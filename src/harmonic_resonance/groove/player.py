"""
player.py - High-fidelity audio playback and real-time spectrum visualization engine for Groove.
Powered by mpv, FFmpeg libavfilter (showcqt, showfreqs, showspectrum, showwaves), and IPC.
"""

import atexit
import hashlib
import json
import math
import os
import shutil
import socket
import struct
import subprocess
import time
import zlib
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class SpectrumMode(str, Enum):
    CQT = "cqt"                 # Musical Constant-Q Transform with piano notes & key guides (default)
    WAVEFORM = "waveform"       # Full song amplitude waveform with moving playhead and highlighted progress
    FREQS = "freqs"             # Animated graphic equalizer frequency bars
    WAVES = "waves"             # Real-time oscilloscope waveform
    SPECTROGRAM = "spectrum"    # Scrolling time-frequency waterfall spectrogram
    NONE = "none"               # Audio-only (no window)


# Ordered list for cycling through modes
SPECTRUM_CYCLE = [
    SpectrumMode.CQT,
    SpectrumMode.WAVEFORM,
    SpectrumMode.FREQS,
    SpectrumMode.WAVES,
    SpectrumMode.SPECTROGRAM,
]

MODE_LABELS: Dict[SpectrumMode, str] = {
    SpectrumMode.CQT: "Musical CQT Notes",
    SpectrumMode.WAVEFORM: "Full Song Waveform",
    SpectrumMode.FREQS: "EQ Frequency Bars",
    SpectrumMode.WAVES: "Oscilloscope Wave",
    SpectrumMode.SPECTROGRAM: "Scrolling Spectrogram",
    SpectrumMode.NONE: "Audio Only",
}


def is_mpv_available() -> bool:
    """Check if mpv executable is installed and available in PATH."""
    return shutil.which("mpv") is not None


def is_ffmpeg_available() -> bool:
    """Check if ffmpeg executable is installed and available in PATH."""
    return shutil.which("ffmpeg") is not None


def ensure_waveform_image(audio_path: Path, width: int = 1920, height: int = 1080) -> Optional[Path]:
    """
    Generate or retrieve a cached high-resolution full-song waveform PNG image using ffmpeg.
    Forces format=rgb24 to guarantee a solid black background without alpha transparency.
    """
    path = Path(audio_path).resolve()
    if not path.exists() or not is_ffmpeg_available():
        return None

    try:
        mtime = int(path.stat().st_mtime)
    except (OSError, FileNotFoundError):
        mtime = 0
    file_hash = hashlib.md5(f"{path}_{mtime}_{width}x{height}_rgb24".encode()).hexdigest()[:12]
    cache_png = Path(f"/tmp/groove-wf-{file_hash}.png")

    try:
        if cache_png.is_file() and cache_png.stat().st_size > 0:
            return cache_png
    except (OSError, FileNotFoundError):
        pass

    try:
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-loglevel", "error",
            "-y",
            "-i", str(path),
            "-filter_complex",
            f"aformat=channel_layouts=mono,showwavespic=s={width}x{height}:colors=0x00e5ff,format=rgb24",
            "-frames:v", "1",
            str(cache_png),
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        if res.returncode == 0 and cache_png.exists():
            return cache_png
    except Exception:
        pass
    return None


PITCH_NAMES: Dict[str, int] = {
    "c": 0, "c#": 1, "db": 1, "d♭": 1,
    "d": 2, "d#": 3, "eb": 3, "e♭": 3,
    "e": 4, "fb": 4, "f♭": 4, "e#": 5,
    "f": 5, "f#": 6, "gb": 6, "g♭": 6,
    "g": 7, "g#": 8, "ab": 8, "a♭": 8,
    "a": 9, "a#": 10, "bb": 10, "b♭": 10,
    "b": 11, "cb": 11, "c♭": 11, "b#": 0,
}

MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10]


def parse_musical_key(key_str: Optional[str]) -> Optional[Tuple[int, Set[int]]]:
    """
    Parse a key string (e.g. 'E♭ minor', 'B major', 'F#m', 'C# minor / E major')
    into (root_pitch_class, set_of_scale_pitch_classes).
    Returns None if key cannot be parsed.
    """
    if not key_str:
        return None

    cleaned = key_str.strip().lower()
    if "/" in cleaned:
        cleaned = cleaned.split("/")[0].strip()

    root_pitch = None
    root_len = 0
    if len(cleaned) >= 2 and cleaned[:2] in PITCH_NAMES:
        root_pitch = PITCH_NAMES[cleaned[:2]]
        root_len = 2
    elif len(cleaned) >= 1 and cleaned[:1] in PITCH_NAMES:
        root_pitch = PITCH_NAMES[cleaned[:1]]
        root_len = 1

    if root_pitch is None:
        return None

    rem = cleaned[root_len:].strip()
    is_minor = "min" in rem or (rem.startswith("m") and not rem.startswith("maj"))
    intervals = MINOR_INTERVALS if is_minor else MAJOR_INTERVALS

    scale_pitches = {(root_pitch + i) % 12 for i in intervals}
    return root_pitch, scale_pitches


def ensure_key_overlay_image(
    musical_key: Optional[str],
    width: int = 1920,
    height: int = 1080,
    basefreq: float = 20.0152,
    endfreq: float = 20495.6,
) -> Optional[Path]:
    """
    Generate or retrieve a cached transparent PNG with subtle vertical column highlights
    for the notes of the given musical key.
    Columns are just a tad lighter than the background (alpha 10-18) so they guide the eye without distracting.
    """
    if not musical_key:
        return None

    parsed = parse_musical_key(musical_key)
    if not parsed:
        return None

    root_pitch, scale_pitches = parsed
    key_slug = hashlib.md5(f"{musical_key}_{root_pitch}_{width}x{height}_{basefreq:.2f}_{endfreq:.2f}".encode()).hexdigest()[:12]
    cache_png = Path(f"/tmp/groove-key-ov-{key_slug}.png")

    try:
        if cache_png.is_file() and cache_png.stat().st_size > 0:
            return cache_png
    except (OSError, FileNotFoundError):
        pass

    try:
        total_octaves = math.log2(endfreq / basefreq)
        semitones_count = int(round(total_octaves * 12))
        px_per_semitone = width / semitones_count

        row = bytearray(width * 4)
        for m in range(16, 16 + semitones_count):
            pitch = m % 12
            if pitch in scale_pitches:
                x_left = int((m - 16) * px_per_semitone)
                x_right = int((m - 15) * px_per_semitone) - 1
                is_root = (pitch == root_pitch)
                r, g, b, a = (200, 230, 255, 18) if is_root else (255, 255, 255, 10)
                for x in range(x_left, min(width, x_right)):
                    idx = x * 4
                    row[idx] = r
                    row[idx + 1] = g
                    row[idx + 2] = b
                    row[idx + 3] = a

        scanline = b'\x00' + bytes(row)
        raw_data = scanline * height
        compressed = zlib.compress(raw_data, level=6)

        def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
            crc = zlib.crc32(chunk_type + data) & 0xffffffff
            return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

        png_bytes = (
            b'\x89PNG\r\n\x1a\n'
            + make_chunk(b'IHDR', struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + make_chunk(b'IDAT', compressed)
            + make_chunk(b'IEND', b'')
        )
        cache_png.write_bytes(png_bytes)
        return cache_png
    except Exception:
        return None


def get_lavfi_filter(
    mode: SpectrumMode,
    audio_path: Path,
    duration: float = 0.0,
    width: int = 1920,
    height: int = 1080,
    musical_key: Optional[str] = None,
) -> Optional[str]:
    """
    Construct the libavfilter complex string for mpv for the given mode rendered at 1080p.
    All visualizer modes:
    1. Route [aid1]asplit[ao][a] so audio is passed directly to the audio sink untouched (no audio cutoff).
    2. Decouple visualizer processing via afifo or anullsink (prevents queue buffer starvation).
    3. Output in format=rgb24 to guarantee a solid black background across all visualizers.
    4. For CQT: note labels and piano keyboard at the very top (bar_h=0, axis_h=60, sono_h=1020)
       to maximize the waterfall timeline, with native FFmpeg pitch labels (C0..C9) and key note highlights.
    5. For WAVEFORM: dynamic overlay progress animation with moving cyan highlight and yellow needle.
    """
    if mode == SpectrumMode.NONE:
        return None

    if mode == SpectrumMode.CQT:
        bar_h = 0
        axis_h = 60
        sono_h = height - bar_h - axis_h  # 1020px dedicated to waterfall timeline

        key_ov = ensure_key_overlay_image(musical_key, width=width, height=height)
        if key_ov and key_ov.exists():
            escaped_ov = str(key_ov.resolve()).replace("\\", "/").replace("'", "'\\''").replace(":", "\\:")
            return (
                f"[aid1]asplit[ao][a];[a]afifo[q];"
                f"[q]showcqt=s={width}x{height}:bar_h={bar_h}:axis_h={axis_h}:sono_h={sono_h}:"
                f"bar_g=2:sono_g=2[cqt];"
                f"movie='{escaped_ov}'[ov];"
                f"[cqt][ov]overlay=shortest=0,format=rgb24[vo]"
            )
        else:
            return (
                f"[aid1]asplit[ao][a];[a]afifo[q];"
                f"[q]showcqt=s={width}x{height}:bar_h={bar_h}:axis_h={axis_h}:sono_h={sono_h}:"
                f"bar_g=2:sono_g=2,format=rgb24[vo]"
            )

    elif mode == SpectrumMode.WAVEFORM:
        img = ensure_waveform_image(audio_path, width=width, height=height)
        dur = max(1.0, duration)
        if img and img.exists():
            escaped_path = str(img.resolve()).replace("\\", "/").replace("'", "'\\''").replace(":", "\\:")
            needle_w = 4
            max_x = max(0, width - needle_w)
            return (
                f"[aid1]asplit[ao][a];[a]anullsink;"
                f"color=c=black:s={width}x{height}:r=25[bg];"
                f"movie='{escaped_path}'[wf];"
                f"[bg][wf]overlay=shortest=0[base];"
                f"color=c=cyan@0.25:s={width}x{height}:r=25[hl];"
                f"[base][hl]overlay=x='min(0,(t/{dur})*{width}-{width})':y=0:shortest=0[with_hl];"
                f"color=c=yellow:s={needle_w}x{height}:r=25[needle];"
                f"[with_hl][needle]overlay=x='min({max_x},max(0,(t/{dur})*{width}))':y=0:shortest=0,format=rgb24[vo]"
            )
        else:
            return f"[aid1]asplit[ao][a];[a]afifo[q];[q]showwaves=s={width}x{height}:mode=line:colors=0x00ffff,format=rgb24[vo]"

    elif mode == SpectrumMode.FREQS:
        return f"[aid1]asplit[ao][a];[a]afifo[q];[q]showfreqs=s={width}x{height}:mode=bar:fscale=log:ascale=log:win_size=2048:colors=cyan|magenta|yellow,format=rgb24[vo]"

    elif mode == SpectrumMode.WAVES:
        return f"[aid1]asplit[ao][a];[a]afifo[q];[q]showwaves=s={width}x{height}:mode=line:colors=0x00ffff,format=rgb24[vo]"

    elif mode == SpectrumMode.SPECTROGRAM:
        return f"[aid1]asplit[ao][a];[a]afifo[q];[q]showspectrum=s={width}x{height}:mode=combined:color=fire:scale=log:fscale=log,format=rgb24[vo]"

    return None


# Cache for waveform envelopes to prevent recomputing on repeated plays
_WAVEFORM_CACHE: Dict[Path, List[float]] = {}


def extract_waveform_envelope(audio_path: Path, num_bars: int = 60) -> List[float]:
    """
    Extract normalized amplitude envelope peaks across the entire audio file using ffmpeg.
    Runs in ~0.05 seconds by downsampling audio to 1 kHz mono.
    Returns a list of float values [0.0, 1.0] representing peak amplitude per bar.
    """
    path = Path(audio_path).resolve()
    if path in _WAVEFORM_CACHE and len(_WAVEFORM_CACHE[path]) == num_bars:
        return _WAVEFORM_CACHE[path]

    if not path.exists() or not is_ffmpeg_available():
        return [0.0] * num_bars

    try:
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-loglevel", "error",
            "-i", str(path),
            "-ac", "1",
            "-ar", "1000",
            "-f", "s16le",
            "pipe:1",
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        raw, _ = proc.communicate(timeout=10)
        if not raw:
            return [0.0] * num_bars

        num_samples = len(raw) // 2
        samples = struct.unpack(f"<{num_samples}h", raw)

        chunk_size = max(1, num_samples // num_bars)
        peaks = []
        for i in range(num_bars):
            start = i * chunk_size
            end = min(num_samples, (i + 1) * chunk_size)
            if start < num_samples:
                peak = max((abs(s) for s in samples[start:end]), default=0)
            else:
                peak = 0
            peaks.append(float(peak))

        max_val = max(peaks) if peaks else 1.0
        if max_val == 0:
            max_val = 1.0

        normalized = [round(p / max_val, 4) for p in peaks]
        _WAVEFORM_CACHE[path] = normalized
        return normalized
    except Exception:
        return [0.0] * num_bars


def render_waveform_ascii(
    peaks: List[float],
    progress_ratio: float = 0.0,
    width: int = 60,
    played_style: str = "bold cyan",
    unplayed_style: str = "dim white",
) -> Tuple[str, str]:
    """
    Render a two-line representation of the full audio wave:
    Line 1: Amplitude envelope bars ( ▂▃▄▅▆▇█) with playhead markup.
    Line 2: Progress track (|████░░░░|) with playhead indicator (▲).
    """
    if not peaks:
        peaks = [0.0] * width
    elif len(peaks) != width:
        # Resample peaks to match requested width
        step = len(peaks) / width
        resampled = [peaks[min(len(peaks) - 1, int(i * step))] for i in range(width)]
        peaks = resampled

    chars = "  ▂▃▄▅▆▇█"
    progress_idx = max(0, min(width - 1, int(progress_ratio * width)))

    wave_chars = [chars[min(8, int(p * 8))] for p in peaks]

    # Line 1: Colored waveform bars
    played_part = "".join(wave_chars[:progress_idx])
    playhead_char = wave_chars[progress_idx] if progress_idx < len(wave_chars) else " "
    unplayed_part = "".join(wave_chars[progress_idx + 1:])

    wave_line = f"[{played_style}]{played_part}[/{played_style}][bold yellow]{playhead_char}[/bold yellow][{unplayed_style}]{unplayed_part}[/{unplayed_style}]"

    # Line 2: Scrubber indicator line
    scrubber_chars = []
    for i in range(width):
        if i == progress_idx:
            scrubber_chars.append("▲")
        elif i < progress_idx:
            scrubber_chars.append("━")
        else:
            scrubber_chars.append("─")
    scrubber_line = f"[{played_style}]{''.join(scrubber_chars[:progress_idx])}[/{played_style}][bold yellow]▲[/bold yellow][{unplayed_style}]{''.join(scrubber_chars[progress_idx+1:])}[/{unplayed_style}]"

    return wave_line, scrubber_line


class MpvPlayer:
    """
    High-level controller for an mpv player instance with real-time spectrum visualization
    and full bidirectional IPC control.
    """

    def __init__(
        self,
        audio_path: Path,
        title: str = "Groove Player",
        mode: SpectrumMode = SpectrumMode.CQT,
        ontop: bool = True,
        geometry: str = "1920x1080",
        loop: bool = False,
        duration: float = 0.0,
        musical_key: Optional[str] = None,
    ) -> None:
        self.audio_path = Path(audio_path).resolve()
        self.title = title
        self.mode = mode
        self.ontop = ontop
        self.geometry = geometry
        self.loop = loop
        self.duration = duration
        self.musical_key = musical_key

        self.ipc_socket_path = f"/tmp/groove-mpv-{os.getpid()}-{int(time.time()*1000)%100000}.sock"
        self.process: Optional[subprocess.Popen] = None
        self._is_active = False

    def _detect_duration(self) -> float:
        """Detect duration of audio using ffprobe or ffmpeg."""
        if not is_ffmpeg_available():
            return 0.0
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(self.audio_path),
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=3)
            return float(res.stdout.decode().strip())
        except Exception:
            return 0.0

    def start(self) -> bool:
        """Launch the mpv playback process."""
        if not is_mpv_available():
            raise RuntimeError("mpv is not installed or not available in PATH.")

        if not self.audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {self.audio_path}")

        if self.duration <= 0.0:
            self.duration = self._detect_duration()

        # Clean old socket if exists
        if os.path.exists(self.ipc_socket_path):
            try:
                os.unlink(self.ipc_socket_path)
            except OSError:
                pass

        cmd = [
            "mpv",
            f"--input-ipc-server={self.ipc_socket_path}",
            f"--title={self.title}",
            "--no-terminal",
            "--keep-open=no",
            "--force-window=yes",
            "--script-opts=osc-visibility=always,osc-layout=bottombar,osc-seekbarstyle=bar",
            f"--geometry={self.geometry}",
            f"--autofit={self.geometry}",
        ]

        if self.loop:
            cmd.append("--loop=inf")

        if self.ontop:
            cmd.append("--ontop")

        if self.mode == SpectrumMode.NONE:
            cmd.extend(["--no-video"])
        else:
            lavfi = get_lavfi_filter(
                self.mode,
                self.audio_path,
                duration=self.duration,
                width=1920,
                height=1080,
                musical_key=self.musical_key,
            )
            if lavfi:
                cmd.append(f"--lavfi-complex={lavfi}")
            else:
                cmd.extend(["--no-video"])

        cmd.append(str(self.audio_path))

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._is_active = True
            return True
        except Exception as e:
            self._is_active = False
            raise RuntimeError(f"Failed to launch mpv: {e}")

    def _send_ipc_command(self, command: List[Any], timeout: float = 0.2) -> Optional[Any]:
        """Send a JSON command to mpv over its IPC unix socket."""
        if not self._is_active or not os.path.exists(self.ipc_socket_path):
            return None

        s = None
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect(self.ipc_socket_path)
            payload = json.dumps({"command": command}).encode("utf-8") + b"\n"
            s.sendall(payload)

            start_t = time.time()
            buffer = ""
            while time.time() - start_t < timeout:
                try:
                    chunk = s.recv(4096).decode("utf-8")
                    if not chunk:
                        break
                    buffer += chunk
                    for line in buffer.split("\n"):
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                if "error" in data:
                                    if data.get("error") == "success":
                                        if data.get("data") is not None:
                                            return data["data"]
                                        return True
                                    return None
                            except json.JSONDecodeError:
                                continue
                except socket.timeout:
                    break

            return None
        except Exception:
            return None
        finally:
            if s:
                try:
                    s.close()
                except Exception:
                    pass

    def get_position(self) -> Tuple[float, float, bool]:
        """
        Get current playback position, total duration, and pause status.
        Returns: (time_pos_seconds, duration_seconds, is_paused)
        """
        if not self.is_running():
            return 0.0, 0.0, False

        pos = self._send_ipc_command(["get_property", "time-pos"])
        dur = self._send_ipc_command(["get_property", "duration"])
        paused = self._send_ipc_command(["get_property", "pause"])

        time_pos = float(pos) if isinstance(pos, (int, float)) else 0.0
        duration = float(dur) if isinstance(dur, (int, float)) else 0.0
        if duration <= 0.0 and self.duration > 0.0:
            duration = self.duration
        is_paused = bool(paused) if isinstance(paused, bool) else False

        return time_pos, duration, is_paused

    def set_mode(self, mode: SpectrumMode) -> bool:
        """Dynamically switch visualization mode on the fly without stopping audio."""
        if not self.is_running():
            return False

        self.mode = mode
        if mode == SpectrumMode.NONE:
            res = self._send_ipc_command(["set_property", "video", "no"])
        else:
            lavfi = get_lavfi_filter(
                mode,
                self.audio_path,
                duration=self.duration,
                width=1920,
                height=1080,
                musical_key=self.musical_key,
            )
            if lavfi:
                self._send_ipc_command(["set_property", "video", "auto"])
                res = self._send_ipc_command(["set_property", "lavfi-complex", lavfi])
            else:
                res = self._send_ipc_command(["set_property", "video", "no"])

        return res is not None

    def cycle_mode(self) -> SpectrumMode:
        """Cycle to the next visualization mode in order."""
        try:
            curr_idx = SPECTRUM_CYCLE.index(self.mode)
            next_mode = SPECTRUM_CYCLE[(curr_idx + 1) % len(SPECTRUM_CYCLE)]
        except ValueError:
            next_mode = SPECTRUM_CYCLE[0]

        self.set_mode(next_mode)
        return next_mode

    def toggle_pause(self) -> bool:
        """Toggle playback pause/resume state."""
        if not self.is_running():
            return False
        return self._send_ipc_command(["cycle", "pause"]) is not None

    def seek(self, seconds: float) -> bool:
        """Seek relative seconds (+/-) or absolute if relative=False."""
        if not self.is_running():
            return False
        return self._send_ipc_command(["seek", seconds, "relative"]) is not None

    def stop(self) -> None:
        """Gracefully stop playback and clean up IPC socket."""
        self._is_active = False
        if self.process:
            try:
                self._send_ipc_command(["quit"])
            except Exception:
                pass

            try:
                self.process.terminate()
                self.process.wait(timeout=0.5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

        if os.path.exists(self.ipc_socket_path):
            try:
                os.unlink(self.ipc_socket_path)
            except OSError:
                pass

    def is_running(self) -> bool:
        """Check if the mpv process is currently alive."""
        if not self._is_active or not self.process:
            return False
        return self.process.poll() is None


class AudioPlayerManager:
    """
    Singleton manager tracking the currently active player process across Groove.
    Ensures only one audio track plays at a time and coordinates graceful transitions.
    """

    _instance: Optional["AudioPlayerManager"] = None

    def __init__(self) -> None:
        self.active_player: Optional[MpvPlayer] = None
        self.active_stem_name: Optional[str] = None
        self.active_file_path: Optional[Path] = None
        self.active_musical_key: Optional[str] = None
        self.current_mode: SpectrumMode = SpectrumMode.CQT
        atexit.register(self.stop)

    @classmethod
    def get_instance(cls) -> "AudioPlayerManager":
        if cls._instance is None:
            cls._instance = AudioPlayerManager()
        return cls._instance

    def play(
        self,
        audio_path: Path,
        stem_name: Optional[str] = None,
        title: Optional[str] = None,
        mode: Optional[SpectrumMode] = None,
        loop: bool = False,
        duration: float = 0.0,
        musical_key: Optional[str] = None,
    ) -> MpvPlayer:
        """Stop any active audio and immediately play the requested track."""
        self.stop()

        target_mode = mode or self.current_mode
        player = MpvPlayer(
            audio_path=audio_path,
            title=title or (f"Groove: {stem_name}" if stem_name else "Groove Player"),
            mode=target_mode,
            loop=loop,
            duration=duration,
            musical_key=musical_key,
        )
        player.start()

        self.active_player = player
        self.active_stem_name = stem_name or Path(audio_path).stem
        self.active_file_path = Path(audio_path)
        self.active_musical_key = musical_key
        self.current_mode = target_mode

        return player

    def toggle_play(
        self,
        audio_path: Path,
        stem_name: Optional[str] = None,
        title: Optional[str] = None,
        musical_key: Optional[str] = None,
    ) -> bool:
        """
        Toggle playback:
        - If the requested audio is already playing: toggles pause/resume.
        - If another track or nothing is playing: starts playing this track.
        """
        if self.is_playing() and self.active_file_path == Path(audio_path).resolve():
            if self.active_player:
                self.active_player.toggle_pause()
                return True
        else:
            self.play(audio_path=audio_path, stem_name=stem_name, title=title, musical_key=musical_key)
            return True

    def stop(self) -> None:
        """Stop active audio playback."""
        if self.active_player:
            self.active_player.stop()
            self.active_player = None
        self.active_stem_name = None
        self.active_file_path = None
        self.active_musical_key = None

    def cycle_mode(self) -> SpectrumMode:
        """Cycle the active visualization mode."""
        if self.active_player and self.active_player.is_running():
            new_mode = self.active_player.cycle_mode()
            self.current_mode = new_mode
            return new_mode
        else:
            curr_idx = SPECTRUM_CYCLE.index(self.current_mode)
            self.current_mode = SPECTRUM_CYCLE[(curr_idx + 1) % len(SPECTRUM_CYCLE)]
            return self.current_mode

    def is_playing(self) -> bool:
        """Check if audio is actively playing."""
        return self.active_player is not None and self.active_player.is_running()

    def get_status(self) -> Dict[str, Any]:
        """Return status dictionary for UI updates."""
        if not self.is_playing() or not self.active_player:
            return {
                "playing": False,
                "paused": False,
                "stem_name": None,
                "file_path": None,
                "musical_key": None,
                "position": 0.0,
                "duration": 0.0,
                "progress_ratio": 0.0,
                "mode": self.current_mode,
                "mode_label": MODE_LABELS.get(self.current_mode, ""),
            }

        pos, dur, paused = self.active_player.get_position()
        ratio = (pos / dur) if dur > 0 else 0.0

        return {
            "playing": True,
            "paused": paused,
            "stem_name": self.active_stem_name,
            "file_path": self.active_file_path,
            "musical_key": self.active_musical_key,
            "position": pos,
            "duration": dur,
            "progress_ratio": min(1.0, max(0.0, ratio)),
            "mode": self.current_mode,
            "mode_label": MODE_LABELS.get(self.current_mode, ""),
        }

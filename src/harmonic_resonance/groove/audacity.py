"""
audacity.py - Audacity 4 multitrack session launcher, project inspector, and offset extractor.
"""

import os
import re
import shutil
import sqlite3
import struct
import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .catalog import Song, Stem
from .downloader import get_song_directory, get_stem_filename


def get_audio_duration(audio_path: Path) -> float:
    """Return the duration of an audio file in seconds using wave or ffprobe."""
    import wave
    p = Path(audio_path)
    try:
        with wave.open(str(p), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(p)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())


def extract_offsets_from_aup4(aup4_path: Path) -> Dict[str, float]:
    """
    Extract track clip start offsets (in seconds) from an Audacity 4 .aup4 project database.

    Returns a dictionary mapping track name (e.g. '00_full_song', '01_drums_tambourine') to its
    start offset in seconds.
    """
    p = Path(aup4_path)
    if not p.exists():
        raise FileNotFoundError(f"Audacity project file not found: {p}")

    con = sqlite3.connect(str(p))
    cur = con.cursor()
    row = cur.execute("SELECT doc FROM project").fetchone()
    con.close()
    if not row or not row[0]:
        return {}

    doc = row[0]
    offsets = {}

    # Tag 51 is waveclip (0x33 0x00), tag 52 is offset (0x34 0x00) with 0x0a double type marker
    pattern = rb"\x33\x00\x0a\x34\x00(.{8})"
    utf32_pattern = rb"(?:0\x00\x00\x00[0-9]\x00\x00\x00_\x00\x00\x00(?:[a-zA-Z0-9_]\x00\x00\x00)+)"

    for m in re.finditer(pattern, doc):
        val = struct.unpack("<d", m.group(1))[0]
        sub = doc[:m.start()]
        names = list(re.finditer(utf32_pattern, sub))
        if names:
            track_name = names[-1].group(0).decode("utf-32-le")
            if track_name not in offsets:
                offsets[track_name] = round(val, 6)

    return offsets


def calculate_relative_offsets(offsets: Dict[str, float], ref_key: str = "00_full_song") -> Dict[str, Dict[str, float]]:
    """
    Calculate lead_in_trim and pad_delay relative to the reference track.
    
    If delta < 0: track has lead-in before song start -> lead_in_trim = -delta
    If delta > 0: track enters after song start -> pad_delay = delta
    """
    ref_offset = offsets.get(ref_key, 0.0)
    relative = {}
    for track_name, offset in offsets.items():
        delta = round(offset - ref_offset, 6)
        if delta < 0:
            relative[track_name] = {"lead_in_trim": abs(delta), "pad_delay": 0.0, "delta": delta}
        else:
            relative[track_name] = {"lead_in_trim": 0.0, "pad_delay": delta, "delta": delta}
    return relative


def pad_track_audio(
    input_file: Path,
    output_file: Optional[Path] = None,
    start_offset: float = 0.0,
    total_duration: Optional[float] = None,
    logger: Optional[Callable[[str], None]] = None,
) -> Path:
    """
    Pad the start of an audio track by start_offset seconds, and optionally
    pad the end to total_duration seconds so that all tracks have identical length.
    """
    in_p = Path(input_file)
    out_p = Path(output_file) if output_file else in_p

    temp_path = in_p.with_name(f"temp_pad_{in_p.name}")
    filters = []

    if start_offset > 0.0005:
        delay_ms = int(round(start_offset * 1000))
        filters.append(f"adelay={delay_ms}|{delay_ms}")

    if total_duration and total_duration > 0:
        filters.append(f"apad=whole_dur={total_duration:.6f}")

    if not filters:
        return in_p

    filter_str = ",".join(filters)
    if logger:
        logger(f"  [cyan]Padding {in_p.name}:[/cyan] start +{start_offset:.4f}s -> target length {total_duration:.3f}s")

    cmd = ["ffmpeg", "-y", "-i", str(in_p), "-af", filter_str, "-c:a", "pcm_s16le", str(temp_path)]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        shutil.move(str(temp_path), str(out_p))
    except Exception as err:
        if temp_path.exists():
            temp_path.unlink()
        raise RuntimeError(f"Failed to pad audio {in_p.name}: {err}")

    return out_p


def pad_song_tracks(
    song_dir: Path,
    start_offsets: Dict[str, float],
    backup_raw: bool = True,
    logger: Optional[Callable[[str], None]] = None,
) -> Dict[str, Path]:
    """
    Given captured start_offsets, pad the start of each track by its offset and pad
    the end so all tracks in song_dir have the exact same duration.
    """
    song_dir = Path(song_dir)
    track_info = {}
    for track_name, offset in start_offsets.items():
        candidates = list(song_dir.glob(f"{track_name}.*"))
        # Exclude temporary or raw files
        valid = [c for c in candidates if not c.name.startswith("temp_") and not c.name.startswith(".")]
        if valid:
            wav_file = valid[0]
            raw_dur = get_audio_duration(wav_file)
            end_time = offset + raw_dur
            track_info[track_name] = {
                "file": wav_file,
                "offset": offset,
                "raw_dur": raw_dur,
                "end_time": end_time,
            }

    if not track_info:
        return {}

    target_duration = max(info["end_time"] for info in track_info.values())

    if logger:
        logger(f"[bold cyan]Equalizing track lengths to {target_duration:.3f}s across {len(track_info)} tracks[/bold cyan]")

    processed = {}
    raw_dir = song_dir / "raw_unpadded"
    if backup_raw:
        raw_dir.mkdir(exist_ok=True)

    for track_name, info in track_info.items():
        wav_file = info["file"]
        offset = info["offset"]

        if backup_raw:
            backup_path = raw_dir / wav_file.name
            if not backup_path.exists():
                shutil.copy2(str(wav_file), str(backup_path))

        pad_track_audio(
            input_file=wav_file,
            output_file=wav_file,
            start_offset=offset,
            total_duration=target_duration,
            logger=logger,
        )
        processed[track_name] = wav_file

    return processed


def generate_launch_script(
    song: Song,
    base_dir: Optional[Path] = None,
) -> Path:
    """
    Generate an executable shell script (launch.sh) to open Audacity 4 with
    all tracks in numeric order, bypassing the need for unsupported .lof files.
    """
    song_dir = get_song_directory(song, base_dir)
    script_path = song_dir / "launch.sh"

    header = f"""#!/usr/bin/env bash
# ==============================================================================
# Launch Audacity 4 with tracks in order for: {song.title}
# Artist: {song.artist} ({song.year})
# Album:  {song.album}
# Tempo:  {song.tempo_bpm} BPM | Key: {song.key}
#
# Usage:
#   ./launch.sh           # Load all tracks (00_full_song.wav, 01_..., ...) in order
#   ./launch.sh --project # Open saved .aup4 project file if present
# ==============================================================================
"""

    body = """
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Locate Audacity binary
if [ -n "${AUDACITY_BIN:-}" ]; then
    AUDACITY="$AUDACITY_BIN"
elif [ -f "$HOME/AppImages/audacity-linux-4.0.0-x86_64.AppImage" ]; then
    AUDACITY="$HOME/AppImages/audacity-linux-4.0.0-x86_64.AppImage"
elif compgen -G "$HOME/AppImages/*audacity*.AppImage" > /dev/null 2>&1; then
    AUDACITY="$(ls -t "$HOME"/AppImages/*audacity*.AppImage | head -n 1)"
elif command -v audacity >/dev/null 2>&1; then
    AUDACITY="$(command -v audacity)"
else
    echo "Error: Audacity executable not found." >&2
    echo "Please set AUDACITY_BIN or install Audacity in ~/AppImages/ or system PATH." >&2
    exit 1
fi

# 2. Check for optional --project flag
if [ "${1:-}" = "--project" ] || [ "${1:-}" = "-p" ]; then
    PROJECT="$(ls -1 *.aup4 2>/dev/null | head -n 1 || true)"
    if [ -n "$PROJECT" ]; then
        echo "Opening Audacity project: $PROJECT"
        exec "$AUDACITY" "$PROJECT"
    else
        echo "No .aup4 project found in $SCRIPT_DIR, falling back to audio tracks..."
    fi
fi

# 3. Collect audio tracks in order (00_full_song.wav, 01_..., etc.)
TRACKS=()
while IFS= read -r file; do
    [ -n "$file" ] && TRACKS+=("$file")
done < <(find . -maxdepth 1 -name "0[0-9]_*.wav" | sort)

if [ ${#TRACKS[@]} -eq 0 ]; then
    while IFS= read -r file; do
        [ -n "$file" ] && TRACKS+=("$file")
    done < <(find . -maxdepth 1 -name "*.wav" | sort)
fi

if [ ${#TRACKS[@]} -eq 0 ]; then
    echo "Error: No audio tracks found in $SCRIPT_DIR" >&2
    exit 1
fi

echo "========================================================"
echo "Launching Audacity with ${#TRACKS[@]} track(s) in order:"
for idx in "${!TRACKS[@]}"; do
    printf "  [%d] %s\\n" "$((idx + 1))" "${TRACKS[$idx]#./}"
done
echo "========================================================"

exec "$AUDACITY" "${TRACKS[@]}"
"""

    script_path.write_text(header + body.lstrip(), encoding="utf-8")
    script_path.chmod(0o755)
    return script_path


def find_audacity_binary() -> str:
    """
    Locate the Audacity binary, prioritizing Audacity 4.x AppImage if available.
    """
    # 1. Environment variable override
    env_bin = os.environ.get("AUDACITY_BIN")
    if env_bin and Path(env_bin).exists():
        return env_bin

    # 2. Known AppImage paths in user home
    home = Path.home()
    appimage_dir = home / "AppImages"
    if appimage_dir.exists():
        # Check for Audacity 4.0.0 specifically
        audacity_4 = appimage_dir / "audacity-linux-4.0.0-x86_64.AppImage"
        if audacity_4.exists():
            return str(audacity_4)
        # Any other audacity AppImage
        for appimg in sorted(appimage_dir.glob("*audacity*.AppImage"), reverse=True):
            return str(appimg)

    # 3. System PATH fallback
    system_audacity = shutil.which("audacity")
    if system_audacity:
        return system_audacity

    raise FileNotFoundError(
        "Audacity executable not found. Set AUDACITY_BIN or place Audacity AppImage in ~/AppImages/."
    )


def launch_audacity(
    target: Optional[Path] = None,
    files: Optional[List[Path]] = None,
    audacity_bin: Optional[str] = None,
) -> subprocess.Popen:
    """
    Launch Audacity with a .lof session, .aup4 project, or list of audio track files.
    
    When passed multiple audio files from the command line, Audacity imports each
    file as a separate track in the project.
    """
    if not audacity_bin:
        audacity_bin = find_audacity_binary()

    cmd = [audacity_bin]
    working_dir = None

    if files:
        for f in files:
            p = Path(f)
            if not p.exists():
                raise FileNotFoundError(f"Audio file not found: {p}")
            cmd.append(str(p.resolve()))
        working_dir = str(Path(files[0]).parent.resolve())
    elif target:
        target_path = Path(target)
        if not target_path.exists():
            raise FileNotFoundError(f"Target project/session file not found: {target_path}")
        cmd.append(str(target_path.resolve()))
        working_dir = str(target_path.parent.resolve())
    else:
        raise ValueError("Must specify either target (e.g. .lof or .aup4) or files list.")

    # Launch Audacity as a detached background process
    proc = subprocess.Popen(
        cmd,
        cwd=working_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return proc


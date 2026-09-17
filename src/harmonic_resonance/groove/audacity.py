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
from typing import Dict, List, Optional

from .catalog import Song, Stem
from .downloader import get_song_directory, get_stem_filename


def extract_offsets_from_aup4(aup4_path: Path) -> Dict[str, float]:
    """
    Extract track clip offsets (in seconds) from an Audacity 4 .aup4 project database.

    Returns a dictionary mapping track name (e.g. '00_full_song', '01_drums') to its
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


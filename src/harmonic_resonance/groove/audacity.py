"""
audacity.py - Audacity multitrack session generator and launcher (.lof format).
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from .catalog import Song, Stem
from .downloader import get_song_directory, get_stem_filename


def generate_audacity_lof(
    song: Song,
    base_dir: Optional[Path] = None,
    audio_format: str = "wav",
    relative_paths: bool = True,
) -> Path:
    """
    Generate an Audacity List of Files (.lof) script for a song.
    
    When opened in Audacity (File -> Open or audacity session.lof), Audacity
    places each stem on its own aligned audio track in a single multitrack window.
    """
    song_dir = get_song_directory(song, base_dir)
    lof_filename = f"{song.id}.lof"
    lof_path = song_dir / lof_filename

    lines: List[str] = [
        f"# ========================================================",
        f"# Audacity Multitrack Session: {song.title}",
        f"# Artist: {song.artist} ({song.year})",
        f"# Album:  {song.album}",
        f"# Tempo:  {song.tempo_bpm} BPM | Key: {song.key} | Time: {song.time_signature}",
        f"# ========================================================",
        f"# Rehearsal Instructions:",
        f"#   - Solo (S) a track to dissect individual performance nuances.",
        f"#   - Mute (M) a track to play your instrument along with the original pocket.",
        f"#   - Select a bar and press Shift+Space (or Transport -> Loop) to loop.",
        f"#   - Use Effect -> Pitch and Tempo -> Change Tempo to practice at slower speeds.",
        f"# ========================================================",
        "",
        "window offset 0",
    ]

    for idx, stem in enumerate(song.stems, start=1):
        filename = get_stem_filename(idx, stem, audio_format)
        target_file = song_dir / filename

        # Add comment with stem details
        lines.append(f"# Track {idx}: {stem.display_name}")
        lines.append(f"# {stem.description}")

        if relative_paths:
            file_entry = f'file "{filename}"'
        else:
            file_entry = f'file "{target_file.resolve()}"'

        lines.append(file_entry)
        lines.append("")

    lof_path.write_text("\n".join(lines), encoding="utf-8")
    return lof_path


def launch_audacity(lof_path: Path) -> subprocess.Popen:
    """
    Launch Audacity with the generated .lof multitrack session.
    """
    audacity_bin = shutil.which("audacity")
    if not audacity_bin:
        raise FileNotFoundError("Audacity executable ('audacity') not found in system PATH.")

    if not lof_path.exists():
        raise FileNotFoundError(f"LOF file not found: {lof_path}")

    # Launch Audacity as a detached background process
    proc = subprocess.Popen(
        [audacity_bin, str(lof_path.resolve())],
        cwd=str(lof_path.parent.resolve()),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc

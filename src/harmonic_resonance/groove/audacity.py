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


"""
downloader.py - Audio extraction and stem management using yt-dlp and ffmpeg.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, List, Optional

from .catalog import Song, Stem


def get_song_directory(song: Song, base_dir: Optional[Path] = None) -> Path:
    """Return the output directory path for a song's stems."""
    if base_dir is None:
        base_dir = Path("tracks")
    artist_slug = song.artist.lower().replace(" ", "-").replace("_", "-")
    song_dir = base_dir / artist_slug / song.id
    song_dir.mkdir(parents=True, exist_ok=True)
    return song_dir


def get_stem_filename(index: int, stem: Stem, audio_format: str = "wav") -> str:
    """Generate a clean, aligned filename for a stem (e.g. 01_drums.wav)."""
    clean_name = stem.name.lower().replace(" ", "_").replace("-", "_")
    return f"{index:02d}_{clean_name}.{audio_format}"


def build_yt_dlp_command(
    source_or_query: str,
    output_template: str,
    audio_format: str = "wav",
) -> List[str]:
    """
    Construct the command line arguments for yt-dlp to download and convert audio.
    """
    # If not a direct URL, treat as a YouTube search query
    target = source_or_query
    if not (source_or_query.startswith("http://") or source_or_query.startswith("https://")):
        target = f"ytsearch1:{source_or_query}"

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--extract-audio",
        "--audio-format", audio_format,
        "--audio-quality", "0",  # Best quality
        "-o", output_template,
        target,
    ]
    return cmd


def download_stem(
    index: int,
    stem: Stem,
    song: Song,
    output_dir: Path,
    audio_format: str = "wav",
    dry_run: bool = False,
    logger: Optional[Callable[[str], None]] = None,
) -> Path:
    """
    Download or extract a single stem for a song.
    
    Returns the Path to the output stem audio file.
    """
    filename = get_stem_filename(index, stem, audio_format)
    target_path = output_dir / filename

    if target_path.exists():
        if logger:
            logger(f"[dim]Stem already exists: {target_path.name} (skipping)[/dim]")
        return target_path

    source = stem.source_url or stem.query or f"{song.artist} {song.title} isolated {stem.name}"
    output_template = str(target_path.with_suffix("")) + ".%(ext)s"

    cmd = build_yt_dlp_command(source, output_template, audio_format)

    if dry_run:
        if logger:
            logger(f"[yellow][DRY RUN][/yellow] Would execute: {' '.join(cmd)}")
        return target_path

    if logger:
        logger(f"[cyan]Downloading stem {index}: {stem.display_name}...[/cyan]")

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise RuntimeError("yt-dlp is not installed or not in PATH. Install with: pip install yt-dlp")
    except subprocess.CalledProcessError as err:
        err_msg = err.stderr.strip() if err.stderr else str(err)
        raise RuntimeError(f"yt-dlp failed to download stem '{stem.name}': {err_msg}")

    # Check if target file was created with the expected extension
    if not target_path.exists():
        # yt-dlp might have produced a slightly different extension before conversion
        possible_matches = list(output_dir.glob(f"{index:02d}_{stem.name}.*"))
        if possible_matches:
            target_path = possible_matches[0]

    # Handle timestamp trimming if specified
    if stem.start_time and target_path.exists():
        trim_stem_audio(target_path, stem.start_time, stem.end_time)

    return target_path


def trim_stem_audio(audio_path: Path, start_time: str, end_time: Optional[str] = None):
    """Trim an audio file in-place or via a temp file using ffmpeg."""
    temp_path = audio_path.with_name(f"temp_{audio_path.name}")
    cmd = ["ffmpeg", "-y", "-ss", start_time]
    if end_time:
        cmd.extend(["-to", end_time])
    cmd.extend(["-i", str(audio_path), "-c", "copy", str(temp_path)])

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    shutil.move(str(temp_path), str(audio_path))


def download_song_stems(
    song: Song,
    base_dir: Optional[Path] = None,
    audio_format: str = "wav",
    dry_run: bool = False,
    logger: Optional[Callable[[str], None]] = None,
) -> List[Path]:
    """
    Download all isolated stems for a given song.
    
    Returns a list of local audio file paths.
    """
    song_dir = get_song_directory(song, base_dir)
    downloaded_paths: List[Path] = []

    if logger:
        logger(f"[bold green]Starting stem retrieval for '{song.title}' by {song.artist}[/bold green]")
        logger(f"Output directory: {song_dir}")

    for idx, stem in enumerate(song.stems, start=1):
        path = download_stem(
            index=idx,
            stem=stem,
            song=song,
            output_dir=song_dir,
            audio_format=audio_format,
            dry_run=dry_run,
            logger=logger,
        )
        downloaded_paths.append(path)

    return downloaded_paths

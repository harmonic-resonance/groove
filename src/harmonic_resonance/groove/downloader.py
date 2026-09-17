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

    # 1. Download full song reference track if available
    if song.full_song_url:
        full_song_path = song_dir / f"00_full_song.{audio_format}"
        if full_song_path.exists():
            if logger:
                logger(f"[dim]Reference track already exists: {full_song_path.name} (skipping)[/dim]")
            downloaded_paths.append(full_song_path)
        else:
            if logger:
                logger(f"[cyan]Downloading Track 0: Full Song Reference ({song.title})...[/cyan]")
            cmd = build_yt_dlp_command(
                song.full_song_url,
                str(full_song_path.with_suffix("")) + ".%(ext)s",
                audio_format=audio_format,
            )
            if dry_run:
                if logger:
                    logger(f"[yellow][DRY RUN][/yellow] Would execute: {' '.join(cmd)}")
                downloaded_paths.append(full_song_path)
            else:
                try:
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    downloaded_paths.append(full_song_path)
                except Exception as err:
                    if logger:
                        logger(f"[yellow]Warning: Could not download full reference track: {err}[/yellow]")

    # 2. Download isolated stems in sequence
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


def detect_silence_segments(
    audio_path: Path,
    noise_db: str = "-30dB",
    min_duration: float = 1.5,
) -> List[dict]:
    """
    Detect silent gaps and return active sound segments in an audio file using ffmpeg.
    """
    cmd = [
        "ffmpeg", "-i", str(audio_path),
        "-af", f"silencedetect=noise={noise_db}:d={min_duration}",
        "-f", "null", "-"
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)

    silences = []
    current_silence_start = None
    import re

    for line in p.stderr.splitlines():
        if "silence_start" in line:
            m = re.search(r"silence_start:\s*([\d\.]+)", line)
            if m:
                current_silence_start = float(m.group(1))
        elif "silence_end" in line:
            m = re.search(r"silence_end:\s*([\d\.]+)", line)
            if m and current_silence_start is not None:
                end = float(m.group(1))
                silences.append((current_silence_start, end))
                current_silence_start = None

    return silences


def slice_audio_file(
    audio_path: Path,
    slices: List[dict],
    output_dir: Path,
    logger: Optional[Callable[[str], None]] = None,
) -> List[Path]:
    """
    Slice an audio file into multiple stem files based on start times and durations.
    Each slice dict should have:
      - 'name': output filename
      - 'start': start time string or seconds (e.g. '00:00:04.283' or 4.283)
      - 'duration': duration string or seconds (e.g. 226.078)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    created: List[Path] = []

    for s in slices:
        out_name = s["name"]
        out_path = output_dir / out_name
        start = str(s["start"])
        dur = str(s["duration"])

        if logger:
            display = s.get("display_name", out_name)
            logger(f"[cyan]Slicing '{display}' ({start} for {dur}s) -> {out_name}[/cyan]")

        cmd = [
            "ffmpeg", "-y",
            "-ss", start,
            "-i", str(audio_path),
            "-t", dur,
            "-c", "copy",
            str(out_path),
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        created.append(out_path)

    return created


def apply_audio_offset(
    audio_path: Path,
    lead_in_trim: float = 0.0,
    pad_delay: float = 0.0,
    logger: Optional[Callable[[str], None]] = None,
) -> Path:
    """
    Apply lead-in trimming and/or delay padding to an audio file so it aligns
    at time 0.0 with the master reference track.
    """
    if lead_in_trim <= 0.0 and pad_delay <= 0.0:
        return audio_path

    temp_path = audio_path.with_name(f"temp_aligned_{audio_path.name}")
    cmd = ["ffmpeg", "-y"]

    if lead_in_trim > 0.0:
        if logger:
            logger(f"  [cyan]Trimming lead-in:[/cyan] {lead_in_trim:.4f}s from {audio_path.name}")
        cmd.extend(["-ss", f"{lead_in_trim:.6f}", "-i", str(audio_path)])
    else:
        cmd.extend(["-i", str(audio_path)])

    if pad_delay > 0.0:
        delay_ms = int(round(pad_delay * 1000))
        if logger:
            logger(f"  [cyan]Padding delay:[/cyan] {pad_delay:.4f}s ({delay_ms}ms) to {audio_path.name}")
        cmd.extend(["-af", f"adelay={delay_ms}|{delay_ms}"])

    cmd.append(str(temp_path))

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        shutil.move(str(temp_path), str(audio_path))
    except Exception as err:
        if temp_path.exists():
            temp_path.unlink()
        raise RuntimeError(f"Failed to align audio file {audio_path.name}: {err}")

    return audio_path


def regenerate_song_from_sources(
    song_id: str,
    base_dir: Optional[Path] = None,
    audio_format: str = "wav",
    dry_run: bool = False,
    force: bool = False,
    logger: Optional[Callable[[str], None]] = None,
) -> List[Path]:
    """
    Regenerate all tracks for a song directly from sources.csv:
    1. Downloads reference track (00_full_song.wav) and isolated stems.
    2. Applies lead_in_trim and pad_delay offsets so all tracks are time-aligned.
    3. Generates the Audacity 4 launch script (launch.sh).
    """
    from .catalog import load_tracks_from_csv, get_song
    from .audacity import get_audio_duration, pad_track_audio

    song_records = load_tracks_from_csv(song_id=song_id)
    if not song_records:
        raise ValueError(f"No tracks recorded in tracks.csv for '{song_id}'.")

    song = get_song(song_id)
    if song:
        song_dir = get_song_directory(song, base_dir)
        title = song.title
    else:
        title = song_records[0].get("title", song_id)
        artist_slug = song_records[0].get("artist", "unknown").lower().replace(" ", "-")
        song_dir = (base_dir or Path("tracks")) / artist_slug / song_id
        song_dir.mkdir(parents=True, exist_ok=True)

    if logger:
        logger(f"[bold green]Regenerating multitrack session for '{title}'[/bold green]")
        logger(f"Target directory: {song_dir}")

    generated_paths: List[Path] = []
    song_records = sorted(song_records, key=lambda r: int(r.get("track_number", 0)))

    # Step 1: Download missing tracks
    tracks_to_pad = []
    for r in song_records:
        trk_num = int(r.get("track_number", 0))
        stem_name = r.get("stem_name", f"track_{trk_num}")
        display_name = r.get("display_name", stem_name)
        url = r.get("url", "")
        start_offset = float(r.get("start_offset", 0.0) or 0.0)

        filename = f"{trk_num:02d}_{stem_name}.{audio_format}"
        target_path = song_dir / filename

        if target_path.exists() and not force:
            if logger:
                logger(f"[dim]Track {trk_num} exists: {filename} (skipping download)[/dim]")
            generated_paths.append(target_path)
            tracks_to_pad.append((target_path, start_offset))
            continue

        if not url:
            if logger:
                logger(f"[yellow]Skipping track {trk_num}: No URL specified[/yellow]")
            continue

        if logger:
            logger(f"[cyan]Downloading Track {trk_num}: {display_name}...[/cyan]")

        output_template = str(target_path.with_suffix("")) + ".%(ext)s"
        cmd = build_yt_dlp_command(url, output_template, audio_format)

        if dry_run:
            if logger:
                logger(f"[yellow][DRY RUN][/yellow] Would download: {url} -> {filename}")
                if start_offset > 0:
                    logger(f"  [yellow][DRY RUN][/yellow] Would pad start offset: +{start_offset:.4f}s")
            generated_paths.append(target_path)
            continue

        # Execute yt-dlp download
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            generated_paths.append(target_path)
            tracks_to_pad.append((target_path, start_offset))
        except Exception as err:
            if logger:
                logger(f"[bold red]Download failed for {display_name}:[/bold red] {err}")
            continue

    # Step 2: Apply start offset padding and equalize all track lengths
    if not dry_run and tracks_to_pad:
        # Calculate end time = start_offset + raw duration for each track
        track_durations = []
        for path, offset in tracks_to_pad:
            if path.exists():
                raw_dur = get_audio_duration(path)
                track_durations.append((path, offset, raw_dur, offset + raw_dur))

        if track_durations:
            max_duration = max(t[3] for t in track_durations)
            has_offsets = any(t[1] > 0.0005 for t in track_durations)

            if has_offsets and logger:
                logger(f"[bold cyan]Aligning start offsets and padding to equal length ({max_duration:.3f}s)...[/bold cyan]")

            for path, offset, raw_dur, end_time in track_durations:
                if offset > 0.0005 or abs(end_time - max_duration) > 0.05:
                    pad_track_audio(
                        input_file=path,
                        output_file=path,
                        start_offset=offset,
                        total_duration=max_duration,
                        logger=logger,
                    )

    return generated_paths


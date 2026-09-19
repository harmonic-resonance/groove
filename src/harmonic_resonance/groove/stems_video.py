"""
stems_video.py - Inspect and parse YouTube videos containing sequential isolated stems.

Handles videos that combine multiple isolated tracks/stems into a single audio timeline,
extracting embedded YouTube chapter markers or parsing description timestamps,
and preparing them for slicing and tracks.csv registration.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .downloader import build_yt_dlp_command


def parse_timestamp_to_seconds(ts_str: str) -> float:
    """
    Convert a timestamp string (e.g. '01:23', '1:23:45', '45.5', '00:03:51.971') to seconds.
    """
    ts_str = ts_str.strip()
    parts = ts_str.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return float(m) * 60 + float(s)
    elif len(parts) == 1:
        return float(parts[0])
    else:
        raise ValueError(f"Invalid timestamp format: '{ts_str}'")


def format_seconds_to_timestamp(seconds: float, include_ms: bool = False) -> str:
    """Convert float seconds to 'MM:SS' or 'HH:MM:SS' format."""
    total_sec = int(seconds)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60

    if include_ms:
        ms = int(round((seconds - total_sec) * 1000))
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"
        return f"{minutes:02d}:{secs:02d}.{ms:03d}"

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def slugify_stem_name(name: str) -> str:
    """Normalize a stem name into a clean filename slug."""
    s = name.lower().strip()
    # Remove track numbering prefixes like "01. ", "1 - ", "Track 1: "
    s = re.sub(r"^(?:track\s*)?\d+[\s.:\-_]+", "", s, flags=re.IGNORECASE)
    # Remove parentheses notes if general, or clean
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s or "stem"


def parse_description_timestamps(description: str, total_duration: float = 0.0) -> List[Dict[str, Any]]:
    """
    Extract chapters/timestamps from video description text.
    Matches lines like:
      0:00 Drums
      00:00 - Isolated Drums
      [03:45] Bass Guitar
      Lead Vocals - 07:12
    """
    if not description:
        return []

    # Regex for timestamp at start of line
    pattern_start = re.compile(
        r"^(?:\[|\()?(\d{1,2}:\d{2}(?::\d{2})?)(?:\]|\))?\s*[-–—:]?\s*(.+)$",
        re.MULTILINE,
    )
    # Regex for timestamp at end of line
    pattern_end = re.compile(
        r"^(.+?)\s*[-–—:]?\s*(?:\[|\()?(\d{1,2}:\d{2}(?::\d{2})?)(?:\]|\))?$",
        re.MULTILINE,
    )

    found: List[Dict[str, Any]] = []

    for line in description.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue

        m = pattern_start.match(line_clean)
        if m:
            ts_str, title = m.group(1), m.group(2).strip()
            # Clean title of markdown or bullets
            title = re.sub(r"^[\s*•\-–—]+", "", title).strip()
            if title and not re.match(r"^https?://", title):
                try:
                    sec = parse_timestamp_to_seconds(ts_str)
                    found.append({"title": title, "start_time": sec})
                    continue
                except ValueError:
                    pass

        m2 = pattern_end.match(line_clean)
        if m2:
            title, ts_str = m2.group(1).strip(), m2.group(2)
            title = re.sub(r"^[\s*•\-–—]+", "", title).strip()
            if title and not re.match(r"^https?://", title):
                try:
                    sec = parse_timestamp_to_seconds(ts_str)
                    found.append({"title": title, "start_time": sec})
                    continue
                except ValueError:
                    pass

    if not found:
        return []

    # Sort by start time and deduplicate
    found.sort(key=lambda x: x["start_time"])
    unique: List[Dict[str, Any]] = []
    for item in found:
        if not unique or abs(item["start_time"] - unique[-1]["start_time"]) > 1.0:
            unique.append(item)

    # Calculate end times and durations
    chapters: List[Dict[str, Any]] = []
    for i, ch in enumerate(unique):
        start = ch["start_time"]
        if i + 1 < len(unique):
            end = unique[i + 1]["start_time"]
        else:
            end = total_duration if total_duration > start else start
        dur = max(0.0, end - start)
        chapters.append({
            "index": i + 1,
            "title": ch["title"],
            "slug": slugify_stem_name(ch["title"]),
            "start_time": start,
            "end_time": end,
            "duration": dur,
            "start_formatted": format_seconds_to_timestamp(start),
            "end_formatted": format_seconds_to_timestamp(end),
            "duration_formatted": format_seconds_to_timestamp(dur),
        })

    return chapters


def inspect_stems_video(
    url_or_id: str,
    logger: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    Inspect a YouTube video containing stems/chapters.
    Fetches video metadata, extracted chapters, and description timestamps using yt-dlp.
    """
    url = url_or_id
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://www.youtube.com/watch?v={url_or_id}"

    if logger:
        logger(f"Inspecting stems video: {url}")

    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-playlist",
        "--no-warnings",
        "--retries", "5",
    ]
    node_path = shutil.which("node") or "/usr/bin/node"
    if Path(node_path).exists():
        cmd.extend(["--js-runtimes", f"node:{node_path}"])
    cmd.append(url)

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"yt-dlp failed to inspect video: {res.stderr.strip()}")

    data = json.loads(res.stdout)

    title = data.get("title", "")
    duration = float(data.get("duration") or 0.0)
    uploader = data.get("uploader", "")
    channel = data.get("channel", "")
    description = data.get("description", "")
    webpage_url = data.get("webpage_url", url)
    video_id = data.get("id", "")

    # 1. Check embedded YouTube chapters
    raw_chapters = data.get("chapters") or []
    chapters: List[Dict[str, Any]] = []

    if raw_chapters:
        for i, ch in enumerate(raw_chapters):
            ch_title = ch.get("title", f"Stem {i+1}")
            start = float(ch.get("start_time", 0.0))
            end = float(ch.get("end_time", duration if duration > start else start))
            dur = max(0.0, end - start)
            chapters.append({
                "index": i + 1,
                "title": ch_title,
                "slug": slugify_stem_name(ch_title),
                "start_time": start,
                "end_time": end,
                "duration": dur,
                "start_formatted": format_seconds_to_timestamp(start),
                "end_formatted": format_seconds_to_timestamp(end),
                "duration_formatted": format_seconds_to_timestamp(dur),
                "source": "youtube_chapters",
            })
    else:
        # 2. Fall back to parsing timestamps from description
        parsed = parse_description_timestamps(description, total_duration=duration)
        for ch in parsed:
            ch["source"] = "description_timestamps"
            chapters.append(ch)

    return {
        "url": webpage_url,
        "video_id": video_id,
        "title": title,
        "duration": duration,
        "duration_formatted": format_seconds_to_timestamp(duration),
        "uploader": uploader or channel,
        "chapter_count": len(chapters),
        "chapters": chapters,
        "description": description,
    }


def format_stems_inspection_report(info: Dict[str, Any]) -> str:
    """Format the inspection results as a markdown / terminal report."""
    lines = [
        f"# Video Stems Inspection: {info['title']}",
        f"- **URL:** {info['url']}",
        f"- **Video ID:** `{info['video_id']}`",
        f"- **Duration:** {info['duration_formatted']} ({info['duration']:.1f}s)",
        f"- **Uploader:** {info['uploader']}",
        f"- **Chapters Found:** {info['chapter_count']}",
        "",
        "| # | Stem Name | Slug | Start | End | Duration | Source |",
        "|---|-----------|------|-------|-----|----------|--------|",
    ]

    for ch in info["chapters"]:
        lines.append(
            f"| {ch['index']:02d} | {ch['title']} | `{ch['slug']}` | {ch['start_formatted']} | "
            f"{ch['end_formatted']} | {ch['duration_formatted']} | {ch.get('source', 'chapters')} |"
        )

    return "\n".join(lines)


def slice_stems_video(
    url_or_id: str,
    output_dir: Path,
    audio_format: str = "webm",
    update_tracks_csv: bool = True,
    keep_source_audio: bool = False,
    logger: Optional[Callable[[str], None]] = None,
) -> List[Path]:
    """
    Download a video containing multiple isolated tracks and slice it into individual stem files
    based on detected chapter markers and timestamps.
    Optionally registers the stems in tracks.csv.
    """
    from .scaffold import add_track_entry

    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    info = inspect_stems_video(url_or_id, logger=logger)
    chapters = info.get("chapters", [])
    if not chapters:
        raise ValueError(f"No chapters or timestamps found in video '{info['title']}' to slice.")

    if logger:
        logger(f"[bold green]Starting stem slicing for '{info['title']}'[/bold green]")
        logger(f"Output directory: {output_dir}")
        logger(f"Detected {len(chapters)} stems/chapters to extract.")

    # 1. Download full video audio once
    temp_source = output_dir / f".source_{info['video_id']}.{audio_format}"
    if not temp_source.exists() or temp_source.stat().st_size == 0:
        if logger:
            logger(f"Downloading source audio ({info['duration_formatted']})...")
        dl_cmd = build_yt_dlp_command(
            info["url"],
            str(temp_source.with_suffix("")) + ".%(ext)s",
            audio_format=audio_format,
        )
        res = subprocess.run(dl_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to download source audio: {res.stderr.decode('utf-8', errors='replace')}")

    # 2. Slice each chapter
    sliced_paths: List[Path] = []
    for ch in chapters:
        idx = ch["index"]
        slug = ch["slug"]
        out_filename = f"{idx:02d}_{slug}.{audio_format}"
        out_path = output_dir / out_filename

        start_sec = ch["start_time"]
        dur_sec = ch["duration"]

        if logger:
            logger(f"  [{idx:02d}/{len(chapters):02d}] Slicing '{ch['title']}' ({ch['start_formatted']} -> {ch['end_formatted']}) -> {out_filename}")

        if audio_format in ("webm", "opus"):
            codec_args = ["-c:a", "libopus", "-b:a", "160k"]
        elif audio_format == "wav":
            codec_args = ["-c:a", "pcm_s16le"]
        else:
            codec_args = ["-c", "copy"]

        ff_cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_sec),
            "-i", str(temp_source),
            "-t", str(dur_sec),
            *codec_args,
            str(out_path),
        ]
        res = subprocess.run(ff_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            err_msg = res.stderr.decode("utf-8", errors="replace")
            if logger:
                logger(f"[red]Error slicing {out_filename}: {err_msg}[/red]")
            continue

        sliced_paths.append(out_path)

        if update_tracks_csv:
            notes = f"Sliced from {info['uploader']} ({ch['start_formatted']} - {ch['end_formatted']})"
            add_track_entry(
                song_dir=output_dir,
                track_number=idx,
                stem_name=slug,
                display_name=ch["title"],
                url=info["url"],
                video_id=info["video_id"],
                duration=ch["duration_formatted"],
                source_type="isolated_tracks_video",
                start_offset=0.0,
                notes=notes,
            )

    # 3. Clean up temporary source file
    if not keep_source_audio and temp_source.exists():
        try:
            temp_source.unlink()
        except OSError:
            pass

    if logger:
        logger(f"[bold green]Successfully sliced {len(sliced_paths)} stems into {output_dir}![/bold green]")

    return sliced_paths


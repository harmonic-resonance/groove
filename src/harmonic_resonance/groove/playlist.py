"""
playlist.py - Ingest official YouTube playlists, parse song credits and descriptions,
maintain album track sequencing, and scaffold full song studies.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .catalog import TRACK_FIELDS, load_song_tracks, save_song_tracks
from .downloader import build_yt_dlp_command


def slugify(text: str) -> str:
    """Convert a title or name to a clean URL/directory slug."""
    s = text.strip().lower()
    # Remove apostrophes without adding spaces
    s = s.replace("'", "").replace("’", "")
    # Replace non-alphanumeric characters with hyphens
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def format_duration(seconds: Optional[int]) -> str:
    """Format seconds into M:SS or H:MM:SS."""
    if not seconds:
        return "0:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def parse_youtube_description(description: str) -> Dict[str, Any]:
    """
    Parse an auto-generated YouTube track description into structured metadata.
    Extracts release date, copyright holder, and personnel/credits roles.
    """
    if not description:
        return {
            "release_date": "",
            "copyright": "",
            "credits": {},
            "raw_description": "",
        }

    lines = [line.strip() for line in description.splitlines() if line.strip()]
    release_date = ""
    copyright_line = ""
    credits: Dict[str, List[str]] = {}

    for line in lines:
        if line.startswith("℗") or line.startswith("(P)") or "UMG Recordings" in line:
            copyright_line = line
        elif line.startswith("Released on:"):
            release_date = line.replace("Released on:", "").strip()
        elif ":" in line and not line.startswith("http") and not line.startswith("Auto-generated") and not line.startswith("Provided to"):
            parts = line.split(":", 1)
            roles_part = parts[0].strip()
            names_part = parts[1].strip()

            # Split roles (often comma-separated e.g. "Recordingarranger, Producer, Composer Lyricist")
            raw_roles = [r.strip() for r in roles_part.split(",") if r.strip()]
            cleaned_roles = []
            for r in raw_roles:
                # Clean up known YouTube concatenations like "Recordingarranger"
                r_clean = re.sub(r"Recordingarranger", "Recording Arranger", r, flags=re.IGNORECASE)
                cleaned_roles.append(r_clean)

            # Split names (comma or slash separated if multiple)
            names = [n.strip() for n in re.split(r"[,/]", names_part) if n.strip()]
            for name in names:
                if name not in credits:
                    credits[name] = []
                for cr in cleaned_roles:
                    if cr not in credits[name]:
                        credits[name].append(cr)

    return {
        "release_date": release_date,
        "copyright": copyright_line,
        "credits": credits,
        "raw_description": description,
    }


def fetch_playlist_details(
    playlist_url: str,
    logger: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    Fetch all video metadata and descriptions for a YouTube playlist using yt-dlp.
    """
    if logger:
        logger(f"[bold cyan]Fetching playlist information:[/bold cyan] {playlist_url}")

    cmd_playlist = ["yt-dlp", "-J", "--flat-playlist", playlist_url]
    try:
        res = subprocess.run(cmd_playlist, capture_output=True, text=True, check=True)
        pl_data = json.loads(res.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to fetch playlist with yt-dlp: {e.stderr or e}")
    except Exception as e:
        raise RuntimeError(f"Failed to parse playlist JSON: {e}")

    playlist_title = pl_data.get("title", "Unknown Album")
    entries_raw = pl_data.get("entries", [])

    if logger:
        logger(f"Found [bold green]{len(entries_raw)}[/bold green] tracks on '{playlist_title}'")

    tracks: List[Dict[str, Any]] = []
    for idx, entry in enumerate(entries_raw, 1):
        vid = entry.get("id")
        title = entry.get("title", f"Track {idx}")
        url = f"https://www.youtube.com/watch?v={vid}"

        if logger:
            logger(f"  [cyan]Inspecting Track {idx:02d}:[/cyan] {title} ({vid})...")

        # Fetch detailed video metadata including full description
        cmd_video = ["yt-dlp", "-j", url]
        try:
            v_res = subprocess.run(cmd_video, capture_output=True, text=True, check=True)
            v_data = json.loads(v_res.stdout)
        except Exception as e:
            if logger:
                logger(f"    [yellow]Warning:[/yellow] Could not fetch detailed metadata for {vid}: {e}")
            v_data = entry

        desc = v_data.get("description", "")
        parsed_desc = parse_youtube_description(desc)
        dur = v_data.get("duration") or entry.get("duration") or 0

        tracks.append({
            "track_number": idx,
            "title": v_data.get("title") or title,
            "slug": slugify(v_data.get("title") or title),
            "video_id": vid,
            "url": url,
            "duration": dur,
            "duration_formatted": format_duration(dur),
            "description": desc,
            "parsed_description": parsed_desc,
            "artist": v_data.get("artist") or pl_data.get("uploader") or "Stevie Wonder",
            "album": v_data.get("album") or playlist_title,
            "release_date": parsed_desc.get("release_date") or v_data.get("release_date") or "",
            "release_year": v_data.get("release_year") or 1973,
        })

    return {
        "title": playlist_title,
        "playlist_url": playlist_url,
        "tracks": tracks,
    }


def download_full_song_reference(
    song_dir: Path,
    url: str,
    audio_format: str = "webm",
    force: bool = False,
    logger: Optional[Callable[[str], None]] = None,
) -> Path:
    """
    Download raw, unpadded full song reference audio directly from YouTube.
    NOTE: Audio is downloaded unpadded without synthetic lead-in delays or silence padding.
    """
    target_file = song_dir / f"00_full_song.{audio_format}"
    if target_file.exists() and not force:
        if logger:
            logger(f"    [dim]Full song reference already exists: {target_file.name} (skipping)[/dim]")
        return target_file

    output_template = str(song_dir / "00_full_song.%(ext)s")
    cmd = build_yt_dlp_command(url, output_template, audio_format=audio_format)

    if logger:
        logger(f"    [green]Downloading full song reference:[/green] {target_file.name}")

    import time
    last_err = None
    for attempt in range(1, 4):
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            last_err = None
            break
        except subprocess.CalledProcessError as e:
            last_err = e
            if attempt < 3:
                if logger:
                    logger(f"    [yellow]Download attempt {attempt} failed, retrying in 2s...[/yellow]")
                time.sleep(2)

    if last_err:
        raise RuntimeError(f"Failed to download audio for {url}: {last_err.stderr or last_err}")

    # Resolve output path in case extension was normalized
    if not target_file.exists():
        candidates = list(song_dir.glob("00_full_song.*"))
        if candidates:
            target_file = candidates[0]

    return target_file


def collect_playlist(
    playlist_url: str,
    base_dir: Optional[Path] = None,
    artist_slug: Optional[str] = None,
    album_slug: Optional[str] = None,
    download_audio: bool = True,
    audio_format: str = "webm",
    force_download: bool = False,
    logger: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    Collect all songs from a YouTube playlist into the Groove library:
    - Maintains strict album track sequence (1..N) in album.yaml and README.md.
    - Captures YouTube descriptions, personnel roles, release date, and copyright in song READMEs.
    - Ensures tracks.csv registers Track 0 (00_full_song).
    - Downloads raw unpadded reference audio files.
    """
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    tracks_dir = (base_dir or (root_dir / "tracks")).resolve()

    pl_info = fetch_playlist_details(playlist_url, logger=logger)
    tracks = pl_info.get("tracks", [])
    if not tracks:
        raise ValueError("Playlist contains no accessible tracks.")

    first_track = tracks[0]
    art_slug = artist_slug or slugify(first_track.get("artist", "stevie-wonder"))
    alb_slug = album_slug or slugify(pl_info.get("title", first_track.get("album", "album")))

    album_dir = tracks_dir / art_slug / alb_slug
    album_dir.mkdir(parents=True, exist_ok=True)

    if logger:
        logger(f"\n[bold green]Ingesting Album:[/bold green] {alb_slug} under artist {art_slug}")
        logger(f"Album directory: {album_dir}")

    # 1. Update or create album.yaml
    album_yaml_path = album_dir / "album.yaml"
    album_data: Dict[str, Any] = {}
    if album_yaml_path.exists():
        try:
            import yaml
            with open(album_yaml_path, "r", encoding="utf-8") as yf:
                album_data = yaml.safe_load(yf) or {}
        except Exception:
            album_data = {}

    album_data.setdefault("title", pl_info.get("title") or first_track.get("album"))
    album_data.setdefault("artist", first_track.get("artist"))
    if first_track.get("release_year"):
        album_data.setdefault("year", int(first_track.get("release_year")))

    # Store ordered track metadata in album.yaml
    tracks_meta = []
    for trk in tracks:
        tracks_meta.append({
            "track_number": trk["track_number"],
            "title": trk["title"],
            "slug": trk["slug"],
            "duration": trk["duration"],
            "duration_formatted": trk["duration_formatted"],
            "url": trk["url"],
            "video_id": trk["video_id"],
        })
    album_data["tracks"] = tracks_meta

    try:
        import yaml
        with open(album_yaml_path, "w", encoding="utf-8") as yf:
            yaml.safe_dump(album_data, yf, sort_keys=False)
    except Exception as e:
        if logger:
            logger(f"[red]Failed writing album.yaml:[/red] {e}")

    # 2. Update album README.md with ordered tracklist
    album_readme_path = album_dir / "README.md"
    _update_album_readme(album_readme_path, album_data, tracks)

    # 3. Process each song study
    processed_songs = []
    for trk in tracks:
        s_slug = trk["slug"]
        s_dir = album_dir / s_slug
        s_dir.mkdir(parents=True, exist_ok=True)

        if logger:
            logger(f"\n[bold cyan]Processing Track {trk['track_number']:02d}:[/bold cyan] {trk['title']} ({s_slug})")

        # Setup tracks.csv (register Track 0)
        _setup_song_tracks_csv(s_dir, trk)

        # Setup or enrich song README.md
        _setup_song_readme(s_dir, trk, album_data)

        # Setup chords.csml if missing
        _setup_song_chords(s_dir, trk, album_data)

        # Download audio
        audio_path = None
        if download_audio:
            audio_path = download_full_song_reference(
                song_dir=s_dir,
                url=trk["url"],
                audio_format=audio_format,
                force=force_download,
                logger=logger,
            )

        processed_songs.append({
            "slug": s_slug,
            "title": trk["title"],
            "track_number": trk["track_number"],
            "song_dir": s_dir,
            "audio_path": audio_path,
        })

    return {
        "artist": art_slug,
        "album": alb_slug,
        "album_dir": album_dir,
        "songs": processed_songs,
    }


def _update_album_readme(readme_path: Path, album_data: Dict[str, Any], tracks: List[Dict[str, Any]]):
    """Ensure album README.md includes the ordered tracklist."""
    title = album_data.get("title", "Album Study")
    artist = album_data.get("artist", "")
    year = album_data.get("year", "")

    track_rows = []
    for t in tracks:
        dur = t.get("duration_formatted", "")
        slug = t.get("slug")
        name = t.get("title")
        track_rows.append(f"{t['track_number']}. **[{name}]({slug}/)** ({dur})")

    tracklist_md = "\n".join(track_rows)

    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        # Replace or append track section
        if "## Track Studies" in content:
            parts = content.split("## Track Studies")
            new_content = parts[0].rstrip() + "\n\n## Track Studies in Album Order\n\n" + tracklist_md + "\n"
        elif "## Tracklist" in content:
            parts = content.split("## Tracklist")
            new_content = parts[0].rstrip() + "\n\n## Track Studies in Album Order\n\n" + tracklist_md + "\n"
        else:
            new_content = content.rstrip() + "\n\n## Track Studies in Album Order\n\n" + tracklist_md + "\n"
    else:
        new_content = f"""# {title} ({year})

**Artist:** {artist}  
**Release Year:** {year}  
**Label:** {album_data.get('label', 'Tamla / Motown')}  

## Overview
{album_data.get('description', f'Complete groove analysis and multitrack study for {title}.')}

## Track Studies in Album Order
{tracklist_md}
"""
    readme_path.write_text(new_content, encoding="utf-8")


def _setup_song_tracks_csv(song_dir: Path, track: Dict[str, Any]):
    """Ensure track 0 is registered with official audio reference in tracks.csv."""
    records = load_song_tracks(song_dir)
    found_track_0 = False

    for r in records:
        if str(r.get("track_number")) == "0":
            found_track_0 = True
            r["stem_name"] = "full_song"
            r["display_name"] = "Full Song Reference"
            r["url"] = track["url"]
            r["video_id"] = track["video_id"]
            r["duration"] = track["duration_formatted"]
            r["source_type"] = "official_audio"
            r["start_offset"] = "0.000000"
            r["notes"] = "Master full stereo mix reference track"
            break

    if not found_track_0:
        records.insert(0, {
            "track_number": "0",
            "stem_name": "full_song",
            "display_name": "Full Song Reference",
            "url": track["url"],
            "video_id": track["video_id"],
            "duration": track["duration_formatted"],
            "source_type": "official_audio",
            "start_offset": "0.000000",
            "notes": "Master full stereo mix reference track",
        })

    # Sort tracks numerically
    records = sorted(records, key=lambda r: int(r.get("track_number", 0)))
    save_song_tracks(song_dir, records)


def _setup_song_readme(song_dir: Path, track: Dict[str, Any], album_data: Dict[str, Any]):
    """Generate or enrich song README.md with YouTube descriptions and personnel credits."""
    readme_path = song_dir / "README.md"
    parsed_desc = track.get("parsed_description", {})
    credits = parsed_desc.get("credits", {})
    raw_desc = parsed_desc.get("raw_description", "").strip()
    year = album_data.get("year", "1973")

    credits_lines = []
    if credits:
        for person, roles in credits.items():
            roles_str = ", ".join(roles)
            credits_lines.append(f"- **{person}**: {roles_str}")
    else:
        credits_lines.append(f"- **{album_data.get('artist', 'Stevie Wonder')}**: All instruments and vocals")

    credits_block = "\n".join(credits_lines)

    quote_desc = "\n".join([f"> {line}" if line else ">" for line in raw_desc.splitlines()])

    # If README exists, preserve custom groove analysis section if already written
    groove_analysis_section = ""
    if readme_path.exists():
        existing_text = readme_path.read_text(encoding="utf-8")
        if "## Groove & Pocket Analysis" in existing_text:
            groove_analysis_section = "\n## Groove & Pocket Analysis" + existing_text.split("## Groove & Pocket Analysis", 1)[1]

    if not groove_analysis_section:
        groove_analysis_section = f"""## Groove & Pocket Analysis

### The Pocket
Detailed breakdown of the kick, snare, bass, and keyboard interplay for {track['title']}.

### Rehearsal Guide
- Solo stems or full mix to study micro-timing and phrasing.
- Play along in the pocket with the original master rhythm track.
"""

    content = f"""# {track['title']}

**Artist:** {album_data.get('artist', 'Stevie Wonder')}  
**Album:** {album_data.get('title', 'Innervisions')} ({year})  
**Track:** {track['track_number']}  
**Duration:** {track['duration_formatted']}  

---

## Personnel & Credits
{credits_block}

## YouTube Official Audio Source
- **URL:** [{track['url']}]({track['url']})
- **Video ID:** `{track['video_id']}`
- **Release Date:** {parsed_desc.get('release_date') or track.get('release_date') or '1973'}
- **Copyright:** {parsed_desc.get('copyright', '')}

<details>
<summary>Original YouTube Description</summary>

{quote_desc}

</details>

---

{groove_analysis_section.strip()}
"""
    readme_path.write_text(content, encoding="utf-8")


def _setup_song_chords(song_dir: Path, track: Dict[str, Any], album_data: Dict[str, Any]):
    """Scaffold chords.csml if not present."""
    csml_path = song_dir / "chords.csml"
    if not csml_path.exists():
        content = f""":title: {track['title']}
:performer: {album_data.get('artist', 'Stevie Wonder')}
:album: {album_data.get('title', 'Innervisions')}
:track: {track['track_number']}

* Intro
| 

* Verse
| 
"""
        csml_path.write_text(content, encoding="utf-8")

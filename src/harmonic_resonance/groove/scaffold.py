"""
scaffold.py - Template generator for artists, songs, tracks.csv, and CSML chord sheets.
"""

from pathlib import Path
from typing import Dict, List, Optional

from .catalog import TRACK_FIELDS, save_song_tracks, load_song_tracks


def create_artist_readme(
    artist_dir: Path,
    artist_name: str,
    overview: Optional[str] = None,
    overwrite: bool = False,
) -> Path:
    """Generate an artist-level README.md describing the rhythm section and study goals."""
    artist_dir = Path(artist_dir)
    artist_dir.mkdir(parents=True, exist_ok=True)
    readme_path = artist_dir / "README.md"

    if readme_path.exists() and not overwrite:
        return readme_path

    display_name = artist_name.replace("-", " ").title()
    content = f"""# {display_name} - Rhythm & Groove Study

{overview or f"Musicological rhythm section breakdown, multitrack isolated stem studies, and pocket analysis for {display_name}."}

## The Rhythm Section & The Pocket
- **Key Musicians & Personnel**: Key rhythm section contributors, drummers, bassists, and keyboard players.
- **Rhythmic Philosophy**: Pocket placement, micro-timing, swing ratio, dynamic phrasing.
- **Pioneering Instruments & Gear**: Signature bass, drum kits, clavinet/Rhodes setups, and synthesizers.

## Song Catalog & Studies
| Song | Album (Year) | Key | Tempo | Stems Status |
|---|---|---|---|---|
"""
    readme_path.write_text(content, encoding="utf-8")
    return readme_path


def create_album_scaffold(
    album_dir: Path,
    title: str,
    artist: str,
    year: Optional[int] = None,
    label: str = "Tamla / Motown",
    studios: Optional[List[str]] = None,
    producers: Optional[List[str]] = None,
    key_gear: Optional[List[str]] = None,
    description: Optional[str] = None,
    overwrite: bool = False,
) -> Dict[str, Path]:
    """Generate album-level folder with README.md and album.yaml."""
    album_dir = Path(album_dir)
    album_dir.mkdir(parents=True, exist_ok=True)
    created: Dict[str, Path] = {}

    readme_path = album_dir / "README.md"
    if not readme_path.exists() or overwrite:
        studios_list = "\n".join(f"- {s}" for s in (studios or ["TBD"]))
        gear_list = "\n".join(f"- {g}" for g in (key_gear or ["TBD"]))
        producers_str = ", ".join(producers) if producers else "TBD"
        content = f"""# {title} ({year or 'TBD'})

**Artist:** {artist}  
**Release Year:** {year or 'TBD'}  
**Label:** {label}  
**Producers:** {producers_str}  

## Overview
{description or f"Album study and multitrack breakdown for {title} by {artist}."}

## Recording Studios
{studios_list}

## Key Gear & Instrumentation
{gear_list}

## Track Studies
"""
        readme_path.write_text(content, encoding="utf-8")
        created["readme"] = readme_path

    yaml_path = album_dir / "album.yaml"
    if not yaml_path.exists() or overwrite:
        import yaml
        data = {
            "title": title,
            "artist": artist,
            "year": year,
            "label": label,
            "studios": studios or [],
            "producers": producers or [],
            "key_gear": key_gear or [],
            "description": description or "",
        }
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)
        created["yaml"] = yaml_path

    return created


def create_song_scaffold(
    song_dir: Path,
    title: str,
    artist: str,
    album: str = "TBD",
    year: str = "TBD",
    tempo_bpm: float = 120.0,
    key: str = "C",
    time_signature: str = "4/4",
    pocket_description: Optional[str] = None,
    microtiming_notes: Optional[str] = None,
    interlocking_rhythm: Optional[str] = None,
    rehearsal_tips: Optional[List[str]] = None,
    overwrite: bool = False,
) -> Dict[str, Path]:
    """
    Scaffold a complete song study folder:
    - README.md: Comprehensive study document with metadata and groove analysis
    - tracks.csv: Isolated stems and reference mix registry
    - chords.csml: Chord Sheet Markup Language file for progressions and lyrics
    """
    song_dir = Path(song_dir)
    song_dir.mkdir(parents=True, exist_ok=True)
    created: Dict[str, Path] = {}

    # 1. README.md
    readme_file = song_dir / "README.md"
    if not readme_file.exists() or overwrite:
        tips_md = "\n".join([f"- {t}" for t in (rehearsal_tips or ["Solo individual tracks to examine micro-timing against the grid.", "Mute your instrument track to practice locking in with the rest of the rhythm section."])])
        readme_content = f"""# {title}

**Artist:** {artist}  
**Album:** {album} ({year})  
**Tempo:** {tempo_bpm} BPM  
**Key:** {key}  
**Time Signature:** {time_signature}  

---

## Groove & Pocket Analysis

### The Pocket
{pocket_description or "Detailed breakdown of the kick, snare, and bass relationship, microtiming accents, and swing feel."}

### Micro-timing & Articulation
{microtiming_notes or "Notes on note length, staccato funk pops, ghost notes, and push/pull against the click."}

### Interlocking Rhythms
{interlocking_rhythm or "How the individual stems combine to form a single cohesive, polyrhythmic groove engine."}

---

## Rehearsal & Play-Along Guide
{tips_md}

---

## Files in this Study
- `tracks.csv`: Registry of isolated tracks, URLs, and alignment offsets.
- `chords.csml`: Chord progressions and lyric sheet (CSML format).
- Run `groove open` from this folder to load the multitrack session directly into Audacity.
"""
        readme_file.write_text(readme_content, encoding="utf-8")
        created["readme"] = readme_file

    # 2. tracks.csv
    tracks_file = song_dir / "tracks.csv"
    if not tracks_file.exists():
        save_song_tracks(song_dir, [])
        created["tracks"] = tracks_file

    # 3. chords.csml
    csml_file = song_dir / "chords.csml"
    if not csml_file.exists():
        csml_content = f""":title: {title}
:performer: {artist}
:album: {album}
:key: {key}
:tempo: {tempo_bpm}
:bpM: 4

* Intro
| 

* Verse 1
| 
- 

* Chorus
| 
- 
"""
        csml_file.write_text(csml_content, encoding="utf-8")
        created["chords"] = csml_file

    return created


def add_track_entry(
    song_dir: Path,
    track_number: int,
    stem_name: str,
    display_name: str,
    url: str = "",
    video_id: str = "",
    duration: str = "",
    source_type: str = "stems",
    start_offset: float = 0.0,
    notes: str = "",
) -> Path:
    """Add or update a track entry in the song's tracks.csv."""
    song_dir = Path(song_dir)
    records = load_song_tracks(song_dir)

    # Check if track_number already exists
    updated = False
    for r in records:
        if int(r.get("track_number", -1)) == track_number:
            r["stem_name"] = stem_name
            r["display_name"] = display_name
            if url:
                r["url"] = url
            if video_id:
                r["video_id"] = video_id
            if duration:
                r["duration"] = duration
            if source_type:
                r["source_type"] = source_type
            if start_offset > 0:
                r["start_offset"] = f"{start_offset:.6f}"
            if notes:
                r["notes"] = notes
            updated = True
            break

    if not updated:
        records.append({
            "track_number": str(track_number),
            "stem_name": stem_name,
            "display_name": display_name,
            "url": url,
            "video_id": video_id,
            "duration": duration,
            "source_type": source_type,
            "start_offset": f"{start_offset:.6f}",
            "notes": notes,
        })

    records = sorted(records, key=lambda r: int(r.get("track_number", 0)))
    return save_song_tracks(song_dir, records)

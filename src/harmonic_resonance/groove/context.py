"""
context.py - Context-aware directory resolution, workspace detection, and summation data for Groove.

Hierarchy levels:
- ROOT: Repository root or top of tracks/
- ARTIST: An artist folder (tracks/<artist>/)
- ALBUM: An album folder (tracks/<artist>/<album>/)
- SONG: A specific song study folder (tracks/<artist>/<album>/<song>/ or tracks/<artist>/<song>/)
- EXTERNAL: Outside of a Groove repository/tracks hierarchy
"""

import csv
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class Scope(Enum):
    ROOT = "root"
    ARTIST = "artist"
    ALBUM = "album"
    SONG = "song"
    EXTERNAL = "external"


def parse_duration_seconds(val: Any) -> float:
    """Parse duration string which may be float seconds or MM:SS / HH:MM:SS."""
    if not val:
        return 0.0
    s = str(val).strip()
    if ":" in s:
        parts = s.split(":")
        try:
            if len(parts) == 2:
                return float(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        except ValueError:
            return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


class GrooveContext:
    def __init__(
        self,
        scope: Scope,
        cwd: Path,
        root_dir: Optional[Path] = None,
        tracks_dir: Optional[Path] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        song: Optional[str] = None,
    ):
        self.scope = scope
        self.cwd = cwd
        self.root_dir = root_dir
        self.tracks_dir = tracks_dir
        self.artist = artist
        self.album = album
        self.song = song

    @property
    def artist_dir(self) -> Optional[Path]:
        if self.tracks_dir and self.artist:
            return self.tracks_dir / self.artist
        return None

    @property
    def album_dir(self) -> Optional[Path]:
        if self.tracks_dir and self.artist and self.album:
            return self.tracks_dir / self.artist / self.album
        return None

    @property
    def song_dir(self) -> Optional[Path]:
        if not self.tracks_dir or not self.artist or not self.song:
            return None
        if self.album:
            candidate = self.tracks_dir / self.artist / self.album / self.song
            if candidate.is_dir():
                return candidate
        # Fallback to direct artist/song
        direct = self.tracks_dir / self.artist / self.song
        if direct.is_dir():
            return direct
        return None

    def list_artists(self) -> List[str]:
        """List all existing artist directory slugs."""
        if not self.tracks_dir or not self.tracks_dir.exists():
            return []
        artists = [
            d.name for d in sorted(self.tracks_dir.iterdir())
            if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_")
        ]
        return artists

    def list_albums(self, artist: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        List all albums as (artist_slug, album_slug) tuples.
        Detects folders containing subdirectories with tracks.csv or album.yaml.
        """
        if not self.tracks_dir or not self.tracks_dir.exists():
            return []

        from .catalog import get_album

        target_artists = [artist] if artist else self.list_artists()
        albums: List[Tuple[str, str]] = []

        for art in target_artists:
            art_dir = self.tracks_dir / art
            if not art_dir.is_dir():
                continue
            for sub in sorted(art_dir.iterdir()):
                if sub.is_dir() and not sub.name.startswith(".") and not sub.name.startswith("_"):
                    has_album_yaml = (sub / "album.yaml").exists()
                    has_sub_songs = any(
                        child.is_dir() and ((child / "tracks.csv").exists() or (child / "chords.csml").exists())
                        for child in sub.iterdir()
                    ) if sub.is_dir() else False
                    is_song = (sub / "tracks.csv").exists() or (sub / "chords.csml").exists()

                    if (has_album_yaml or has_sub_songs or bool(get_album(sub.name))) and not is_song:
                        albums.append((art, sub.name))

        return albums

    def list_songs(
        self,
        artist: Optional[str] = None,
        album: Optional[str] = None,
    ) -> List[Tuple[str, Optional[str], str]]:
        """
        List all songs as (artist_slug, album_slug_or_None, song_slug) tuples.
        Supports both 3-tier (tracks/<artist>/<album>/<song>) and
        legacy 2-tier (tracks/<artist>/<song>).
        """
        if not self.tracks_dir or not self.tracks_dir.exists():
            return []

        from .catalog import get_album

        target_artists = [artist] if artist else self.list_artists()
        results: List[Tuple[str, Optional[str], str]] = []

        for art in target_artists:
            art_dir = self.tracks_dir / art
            if not art_dir.is_dir():
                continue

            for sub in sorted(art_dir.iterdir()):
                if not sub.is_dir() or sub.name.startswith(".") or sub.name.startswith("_"):
                    continue

                is_album = (
                    (sub / "album.yaml").exists()
                    or bool(get_album(sub.name))
                    or any(
                        child.is_dir() and ((child / "tracks.csv").exists() or (child / "chords.csml").exists())
                        for child in sub.iterdir()
                    )
                )

                if is_album:
                    if album is not None and sub.name != album:
                        continue
                    for child in sorted(sub.iterdir()):
                        if child.is_dir() and not child.name.startswith(".") and not child.name.startswith("_"):
                            results.append((art, sub.name, child.name))
                else:
                    # Legacy 2-tier: tracks/<artist>/<song>
                    if album is None:
                        results.append((art, None, sub.name))

        return results

    def find_song_dir(
        self,
        song_id: Union[str, Path],
        artist_id: Optional[str] = None,
        album_id: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Locate the song directory for a given song ID slug.
        Searches across artist and album subfolders.
        """
        if not self.tracks_dir or not self.tracks_dir.exists():
            return None

        if isinstance(song_id, Path):
            if song_id.is_dir() and ((song_id / "tracks.csv").exists() or (song_id / "chords.csml").exists()):
                return song_id
            s_name = song_id.name
        else:
            s_name = str(song_id)

        norm_song = s_name.lower().replace(" ", "-").replace("_", "-")

        # 1. Exact path if artist and album known
        if artist_id and album_id:
            norm_art = artist_id.lower().replace(" ", "-").replace("_", "-")
            norm_alb = album_id.lower().replace(" ", "-").replace("_", "-")
            candidate = self.tracks_dir / norm_art / norm_alb / norm_song
            if candidate.is_dir():
                return candidate

        # 2. Check under artist if specified
        if artist_id:
            norm_art = artist_id.lower().replace(" ", "-").replace("_", "-")
            art_dir = self.tracks_dir / norm_art
            if art_dir.is_dir():
                # Direct check
                if (art_dir / norm_song).is_dir() and ((art_dir / norm_song) / "tracks.csv").exists():
                    return art_dir / norm_song
                # Check within album subfolders
                for sub in art_dir.iterdir():
                    if sub.is_dir() and (sub / norm_song).is_dir():
                        return sub / norm_song

        # 3. Global search
        for art, alb, s_slug in self.list_songs():
            if s_slug == norm_song:
                if alb:
                    return self.tracks_dir / art / alb / s_slug
                else:
                    return self.tracks_dir / art / s_slug

        return None

    def find_album_dir(self, album_id: str, artist_id: Optional[str] = None) -> Optional[Path]:
        """Locate the directory for a given album slug."""
        if not self.tracks_dir or not self.tracks_dir.exists():
            return None

        norm_alb = album_id.lower().replace(" ", "-").replace("_", "-")

        if artist_id:
            norm_art = artist_id.lower().replace(" ", "-").replace("_", "-")
            candidate = self.tracks_dir / norm_art / norm_alb
            if candidate.is_dir():
                return candidate

        for art, alb in self.list_albums():
            if alb == norm_alb:
                return self.tracks_dir / art / alb

        return None

    # =========================================================================
    # SUMMATION DATA PROVIDERS (SEER NAVIGATOR PATTERN)
    # =========================================================================

    def get_catalog_summary(self) -> Dict[str, Any]:
        """Aggregate catalog-wide statistics across all artists, albums, and songs."""
        artists = self.list_artists()
        albums = self.list_albums()
        songs = self.list_songs()

        total_stems = 0
        total_duration_sec = 0.0
        projects_count = 0
        chords_count = 0
        studies_count = 0
        local_files_count = 0

        for art, alb, s_slug in songs:
            s_dir = self.find_song_dir(s_slug, artist_id=art, album_id=alb)
            if not s_dir:
                continue
            t_summary = self._read_song_quick_summary(s_dir)
            total_stems += t_summary["stems_count"]
            total_duration_sec += t_summary["duration"]
            if t_summary["has_project"]:
                projects_count += 1
            if t_summary["has_chords"]:
                chords_count += 1
            if t_summary["has_study"]:
                studies_count += 1
            local_files_count += t_summary["files_present"]

        return {
            "artists_count": len(artists),
            "albums_count": len(albums),
            "songs_count": len(songs),
            "stems_count": total_stems,
            "total_duration_sec": total_duration_sec,
            "projects_count": projects_count,
            "chords_count": chords_count,
            "studies_count": studies_count,
            "local_files_count": local_files_count,
        }

    def get_artist_summary(self, artist_slug: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate statistics for an artist."""
        target_artist = artist_slug or self.artist
        if not target_artist:
            return {}

        albums = [alb for art, alb in self.list_albums(target_artist)]
        songs = self.list_songs(artist=target_artist)

        total_stems = 0
        total_duration_sec = 0.0
        tempos: List[float] = []
        keys: List[str] = []
        projects_count = 0
        chords_count = 0
        studies_count = 0

        for art, alb, s_slug in songs:
            s_dir = self.find_song_dir(s_slug, artist_id=art, album_id=alb)
            if not s_dir:
                continue
            s_sum = self._read_song_quick_summary(s_dir)
            total_stems += s_sum["stems_count"]
            total_duration_sec += s_sum["duration"]
            if s_sum["tempo"] > 0:
                tempos.append(s_sum["tempo"])
            if s_sum["key"]:
                keys.append(s_sum["key"])
            if s_sum["has_project"]:
                projects_count += 1
            if s_sum["has_chords"]:
                chords_count += 1
            if s_sum["has_study"]:
                studies_count += 1

        return {
            "artist": target_artist,
            "albums_count": len(albums),
            "songs_count": len(songs),
            "stems_count": total_stems,
            "total_duration_sec": total_duration_sec,
            "tempo_min": min(tempos) if tempos else 0.0,
            "tempo_max": max(tempos) if tempos else 0.0,
            "tempo_avg": (sum(tempos) / len(tempos)) if tempos else 0.0,
            "keys": sorted(list(set(keys))),
            "projects_count": projects_count,
            "chords_count": chords_count,
            "studies_count": studies_count,
        }

    def get_album_summary(
        self,
        artist_slug: Optional[str] = None,
        album_slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Aggregate statistics for an album."""
        target_art = artist_slug or self.artist
        target_alb = album_slug or self.album
        if not target_art or not target_alb:
            return {}

        songs = self.list_songs(artist=target_art, album=target_alb)
        alb_dir = self.find_album_dir(target_alb, artist_id=target_art)

        total_stems = 0
        total_duration_sec = 0.0
        tempos: List[float] = []
        keys: List[str] = []
        projects_count = 0
        chords_count = 0

        for art, alb, s_slug in songs:
            s_dir = self.find_song_dir(s_slug, artist_id=art, album_id=alb)
            if not s_dir:
                continue
            s_sum = self._read_song_quick_summary(s_dir)
            total_stems += s_sum["stems_count"]
            total_duration_sec += s_sum["duration"]
            if s_sum["tempo"] > 0:
                tempos.append(s_sum["tempo"])
            if s_sum["key"]:
                keys.append(s_sum["key"])
            if s_sum["has_project"]:
                projects_count += 1
            if s_sum["has_chords"]:
                chords_count += 1

        # Load album.yaml if present
        album_meta: Dict[str, Any] = {}
        if alb_dir and (alb_dir / "album.yaml").exists():
            try:
                import yaml
                with open(alb_dir / "album.yaml", "r", encoding="utf-8") as f:
                    album_meta = yaml.safe_load(f) or {}
            except Exception:
                pass

        return {
            "artist": target_art,
            "album": target_alb,
            "title": album_meta.get("title", target_alb.replace("-", " ").title()),
            "year": album_meta.get("year"),
            "label": album_meta.get("label", "Tamla / Motown"),
            "studios": album_meta.get("studios", []),
            "producers": album_meta.get("producers", []),
            "key_gear": album_meta.get("key_gear", []),
            "songs_count": len(songs),
            "stems_count": total_stems,
            "total_duration_sec": total_duration_sec,
            "tempo_min": min(tempos) if tempos else 0.0,
            "tempo_max": max(tempos) if tempos else 0.0,
            "keys": sorted(list(set(keys))),
            "projects_count": projects_count,
            "chords_count": chords_count,
        }

    def get_song_summary(
        self,
        song_slug: Optional[str] = None,
        artist_slug: Optional[str] = None,
        album_slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extract detailed pocket and rehearsal readiness for a specific song."""
        target_song = song_slug or self.song
        target_art = artist_slug or self.artist
        target_alb = album_slug or self.album

        if not target_song:
            return {}

        song_dir = self.find_song_dir(target_song, artist_id=target_art, album_id=target_alb)
        if not song_dir:
            return {}

        return self._read_song_quick_summary(song_dir)

    def _read_song_quick_summary(self, song_dir: Path) -> Dict[str, Any]:
        """Internal helper to extract metrics from a song folder."""
        tracks_csv = song_dir / "tracks.csv"
        stems_count = 0
        ref_duration = 0.0
        max_offset = 0.0
        offsets_padded = False

        if tracks_csv.exists():
            try:
                with open(tracks_csv, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        stems_count += 1
                        dur = parse_duration_seconds(row.get("duration", 0.0))
                        off = float(row.get("start_offset", 0.0) or 0.0)
                        if dur > ref_duration:
                            ref_duration = dur
                        if off > max_offset:
                            max_offset = off
                        if str(row.get("padded", "")).lower() in ("true", "1", "yes"):
                            offsets_padded = True
            except Exception:
                pass

        audio_extensions = {".webm", ".wav", ".opus", ".flac", ".mp3", ".ogg"}
        files_present = sum(
            1 for f in song_dir.iterdir()
            if f.is_file() and f.suffix.lower() in audio_extensions and not f.name.startswith(".")
        )

        has_project = bool(list(song_dir.glob("*.aup4")))
        has_chords = (song_dir / "chords.csml").exists()
        has_study = (song_dir / "README.md").exists()

        from .catalog import get_song
        cat_song = get_song(song_dir.name)

        return {
            "slug": song_dir.name,
            "title": cat_song.title if cat_song else song_dir.name.replace("-", " ").title(),
            "artist": cat_song.artist if cat_song else song_dir.parent.name.replace("-", " ").title(),
            "album": cat_song.album if cat_song else "",
            "year": cat_song.year if cat_song else None,
            "tempo": cat_song.tempo_bpm if cat_song else 0.0,
            "key": cat_song.key if cat_song else "",
            "meter": cat_song.time_signature if cat_song else "4/4",
            "stems_count": stems_count,
            "duration": ref_duration,
            "max_offset": max_offset,
            "offsets_padded": offsets_padded,
            "has_project": has_project,
            "has_chords": has_chords,
            "has_study": has_study,
            "files_present": files_present,
            "song_dir": song_dir,
        }

    def __repr__(self) -> str:
        return (
            f"GrooveContext(scope={self.scope.value}, artist={self.artist}, "
            f"album={self.album}, song={self.song}, tracks_dir={self.tracks_dir})"
        )


def detect_context(start_dir: Optional[Path] = None) -> GrooveContext:
    """
    Inspect the working directory hierarchy to establish GrooveContext.
    Walks upward to locate repository root or tracks directory.
    Identifies ROOT, ARTIST, ALBUM, SONG, or EXTERNAL scopes.
    """
    cwd = (start_dir or Path.cwd()).resolve()

    tracks_dir: Optional[Path] = None
    root_dir: Optional[Path] = None

    curr = cwd
    while curr != curr.parent:
        if (curr / "tracks").is_dir() and (curr / "pyproject.toml").exists():
            root_dir = curr
            tracks_dir = curr / "tracks"
            break
        if curr.name == "tracks" and (curr.parent / "pyproject.toml").exists():
            root_dir = curr.parent
            tracks_dir = curr
            break
        if (curr / "tracks").is_dir():
            tracks_dir = curr / "tracks"
            root_dir = curr
            break
        curr = curr.parent

    if not tracks_dir or not root_dir:
        return GrooveContext(scope=Scope.EXTERNAL, cwd=cwd)

    # Determine position relative to tracks_dir
    try:
        rel = cwd.relative_to(tracks_dir)
        parts = rel.parts
        if len(parts) == 0:
            return GrooveContext(scope=Scope.ROOT, cwd=cwd, root_dir=root_dir, tracks_dir=tracks_dir)
        elif len(parts) == 1:
            return GrooveContext(
                scope=Scope.ARTIST,
                cwd=cwd,
                root_dir=root_dir,
                tracks_dir=tracks_dir,
                artist=parts[0],
            )
        elif len(parts) == 2:
            target_dir = tracks_dir / parts[0] / parts[1]
            from .catalog import get_album, get_song
            if (target_dir / "album.yaml").exists() or bool(get_album(parts[1])):
                return GrooveContext(
                    scope=Scope.ALBUM,
                    cwd=cwd,
                    root_dir=root_dir,
                    tracks_dir=tracks_dir,
                    artist=parts[0],
                    album=parts[1],
                )
            elif (target_dir / "tracks.csv").exists() or (target_dir / "chords.csml").exists() or list(target_dir.glob("*.aup4")):
                return GrooveContext(
                    scope=Scope.SONG,
                    cwd=cwd,
                    root_dir=root_dir,
                    tracks_dir=tracks_dir,
                    artist=parts[0],
                    song=parts[1],
                )
            elif any(
                child.is_dir() and ((child / "tracks.csv").exists() or (child / "album.yaml").exists())
                for child in target_dir.iterdir()
            ):
                return GrooveContext(
                    scope=Scope.ALBUM,
                    cwd=cwd,
                    root_dir=root_dir,
                    tracks_dir=tracks_dir,
                    artist=parts[0],
                    album=parts[1],
                )
            elif get_song(parts[1]):
                return GrooveContext(
                    scope=Scope.SONG,
                    cwd=cwd,
                    root_dir=root_dir,
                    tracks_dir=tracks_dir,
                    artist=parts[0],
                    song=parts[1],
                )
            else:
                return GrooveContext(
                    scope=Scope.ALBUM,
                    cwd=cwd,
                    root_dir=root_dir,
                    tracks_dir=tracks_dir,
                    artist=parts[0],
                    album=parts[1],
                )
        else:
            # len(parts) >= 3
            # Could be:
            # - tracks/<artist>/<album>/<song> (len == 3)
            # - tracks/<artist>/<album>/<song>/<subfolder> (len >= 4)
            # - tracks/<artist>/<song>/<subfolder> (legacy 2-tier with subfolder, len >= 3)
            from .catalog import get_album, get_song
            target_sub = tracks_dir / parts[0] / parts[1]
            is_legacy_song = (
                (target_sub / "tracks.csv").exists()
                or (target_sub / "chords.csml").exists()
                or (bool(get_song(parts[1])) and not bool(get_album(parts[1])))
            )
            if is_legacy_song:
                return GrooveContext(
                    scope=Scope.SONG,
                    cwd=cwd,
                    root_dir=root_dir,
                    tracks_dir=tracks_dir,
                    artist=parts[0],
                    song=parts[1],
                )
            else:
                return GrooveContext(
                    scope=Scope.SONG,
                    cwd=cwd,
                    root_dir=root_dir,
                    tracks_dir=tracks_dir,
                    artist=parts[0],
                    album=parts[1],
                    song=parts[2],
                )
    except ValueError:
        return GrooveContext(scope=Scope.ROOT, cwd=cwd, root_dir=root_dir, tracks_dir=tracks_dir)


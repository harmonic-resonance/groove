"""
context.py - Context-aware directory resolution and workspace detection for Groove.

Determines whether the CLI is being run from:
- ROOT: Repository root or top of tracks/
- ARTIST: An artist folder (tracks/<artist>/)
- SONG: A specific song study folder (tracks/<artist>/<song>/)
- EXTERNAL: Outside of a Groove repository/tracks hierarchy
"""

import sys
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple


class Scope(Enum):
    ROOT = "root"
    ARTIST = "artist"
    SONG = "song"
    EXTERNAL = "external"


class GrooveContext:
    def __init__(
        self,
        scope: Scope,
        cwd: Path,
        root_dir: Optional[Path] = None,
        tracks_dir: Optional[Path] = None,
        artist: Optional[str] = None,
        song: Optional[str] = None,
    ):
        self.scope = scope
        self.cwd = cwd
        self.root_dir = root_dir
        self.tracks_dir = tracks_dir
        self.artist = artist
        self.song = song

    @property
    def artist_dir(self) -> Optional[Path]:
        if self.tracks_dir and self.artist:
            return self.tracks_dir / self.artist
        return None

    @property
    def song_dir(self) -> Optional[Path]:
        if self.tracks_dir and self.artist and self.song:
            return self.tracks_dir / self.artist / self.song
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

    def list_songs(self, artist: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        List all songs as (artist_slug, song_slug) tuples.
        If artist is provided, only lists songs for that artist.
        """
        if not self.tracks_dir or not self.tracks_dir.exists():
            return []
        
        target_artists = [artist] if artist else self.list_artists()
        results = []
        for art in target_artists:
            art_dir = self.tracks_dir / art
            if not art_dir.is_dir():
                continue
            for s_dir in sorted(art_dir.iterdir()):
                if s_dir.is_dir() and not s_dir.name.startswith(".") and not s_dir.name.startswith("_"):
                    results.append((art, s_dir.name))
        return results

    def find_song_dir(self, song_id: str, artist_id: Optional[str] = None) -> Optional[Path]:
        """
        Locate the song directory for a given song ID slug.
        If artist_id is provided, checks tracks/<artist_id>/<song_id>.
        Otherwise searches all artist subfolders for <song_id>.
        """
        if not self.tracks_dir or not self.tracks_dir.exists():
            return None

        normalized_song = song_id.lower().replace(" ", "-").replace("_", "-")

        if artist_id:
            normalized_artist = artist_id.lower().replace(" ", "-").replace("_", "-")
            candidate = self.tracks_dir / normalized_artist / normalized_song
            if candidate.is_dir():
                return candidate

        # Search across all artist folders
        for art_dir in self.tracks_dir.iterdir():
            if art_dir.is_dir() and not art_dir.name.startswith("."):
                candidate = art_dir / normalized_song
                if candidate.is_dir():
                    return candidate

        return None

    def __repr__(self) -> str:
        return (
            f"GrooveContext(scope={self.scope.value}, artist={self.artist}, "
            f"song={self.song}, tracks_dir={self.tracks_dir})"
        )


def detect_context(start_dir: Optional[Path] = None) -> GrooveContext:
    """
    Inspect the working directory hierarchy to establish GrooveContext.
    Walks upward to locate the repository root or tracks directory.
    """
    cwd = (start_dir or Path.cwd()).resolve()

    # Walk upwards looking for tracks/ directory or pyproject.toml
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

    # Determine relative position relative to tracks_dir
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
        else:
            return GrooveContext(
                scope=Scope.SONG,
                cwd=cwd,
                root_dir=root_dir,
                tracks_dir=tracks_dir,
                artist=parts[0],
                song=parts[1],
            )
    except ValueError:
        # cwd is not inside tracks_dir; it is at root_dir or another subfolder
        return GrooveContext(scope=Scope.ROOT, cwd=cwd, root_dir=root_dir, tracks_dir=tracks_dir)

"""
app.py - Main Textual Application class for Groove Navigator.
Directly inspired by Seer Navigator (SessionsNavigator / TasksNavigator).
"""

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container

from ..context import GrooveContext, Scope, detect_context
from .screens.catalog_screen import CatalogScreen
from .screens.artist_screen import ArtistScreen
from .screens.album_screen import AlbumScreen
from .screens.song_screen import SongScreen


class GrooveNavigator(App):
    """Interactive TUI navigator for Groove rhythm studies and multitrack sessions."""

    TITLE = "Groove Navigator"
    SUB_TITLE = "Master Rhythm Studies & Isolated Multitrack Analyzer"

    CSS = """
    Screen {
        background: $surface;
        color: $text;
    }

    Header {
        background: $accent-darken-3;
        color: $text;
        text-style: bold;
    }

    Footer {
        background: $accent-darken-3;
        color: $text-muted;
    }

    DataTable {
        border: solid $accent-darken-2;
        background: $surface;
    }

    DataTable > .datatable--cursor {
        background: $accent;
        color: $text;
        text-style: bold;
    }

    DataTable:focus > .datatable--cursor {
        background: $accent-darken-1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_screen", "Refresh", show=True),
        Binding("s", "sort_table", "Sort Table", show=True),
    ]

    def __init__(self, start_dir: Optional[Path] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.start_dir = Path(start_dir or Path.cwd()).resolve()
        self.ctx = detect_context(self.start_dir)
        self.tracks_dir = self.ctx.tracks_dir or (self.start_dir / "tracks")

    def compose(self) -> ComposeResult:
        yield Container()

    def on_mount(self) -> None:
        """
        Build the initial screen stack based on the directory context where Groove was launched.
        Allows immediate interaction at the current folder level, while enabling 'h' (back)
        to pop all the way back up to the Catalog root.
        """
        tracks = self.tracks_dir

        if self.ctx.scope == Scope.ROOT or self.ctx.scope == Scope.EXTERNAL:
            self.push_screen(CatalogScreen(tracks))

        elif self.ctx.scope == Scope.ARTIST and self.ctx.artist:
            self.push_screen(CatalogScreen(tracks))
            self.push_screen(ArtistScreen(tracks, self.ctx.artist))

        elif self.ctx.scope == Scope.ALBUM and self.ctx.artist and self.ctx.album:
            self.push_screen(CatalogScreen(tracks))
            self.push_screen(ArtistScreen(tracks, self.ctx.artist))
            self.push_screen(AlbumScreen(tracks, self.ctx.artist, self.ctx.album))

        elif self.ctx.scope == Scope.SONG and self.ctx.artist and self.ctx.song:
            self.push_screen(CatalogScreen(tracks))
            self.push_screen(ArtistScreen(tracks, self.ctx.artist))
            if self.ctx.album:
                self.push_screen(AlbumScreen(tracks, self.ctx.artist, self.ctx.album))
            self.push_screen(SongScreen(tracks, self.ctx.artist, self.ctx.album, self.ctx.song))

        else:
            self.push_screen(CatalogScreen(tracks))

    def action_refresh_screen(self) -> None:
        current_screen = self.screen
        if hasattr(current_screen, "action_refresh_content"):
            current_screen.action_refresh_content()
        elif hasattr(current_screen, "refresh_content"):
            current_screen.refresh_content()

    def action_sort_table(self) -> None:
        current_screen = self.screen
        if hasattr(current_screen, "action_sort_table"):
            current_screen.action_sort_table()

    def action_quit(self) -> None:
        self.exit()

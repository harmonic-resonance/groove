"""
album_screen.py - Level 2: Album screen for Groove Navigator.
Displays production metadata, studios, gear, and lists songs on the album.
"""

from pathlib import Path
from typing import Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header
from textual.widgets._data_table import ColumnKey

from ...context import GrooveContext, Scope
from ..sort_modal import SortModal
from ..viewers import ContentModal
from .catalog_screen import _format_time


class AlbumScreen(Screen):
    """Level 2: Album view listing songs and studio/gear production context."""

    CSS = """
    Screen > Vertical {
        grid-size: 2;
        grid-rows: auto 1fr;
    }
    #summary-grid {
        grid-size: 3;
        grid-gutter: 1 2;
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
    }
    .summary-table {
        height: auto;
        border: none;
    }
    .summary-table:focus {
        border: none;
    }
    DataTable {
        height: 1fr;
    }
    Vertical {
        height: 100%;
    }
    """

    BINDINGS = [
        Binding("h", "go_back", "Back to Artist", show=True),
        Binding("j", "move_down", "Cursor down", show=True),
        Binding("k", "move_up", "Cursor up", show=True),
        Binding("l,enter", "select_row", "Select Song", show=True),
        Binding("b", "view_album_notes", "Album Notes", show=True),
        Binding("[", "prev_album", "Prev Album", show=True),
        Binding("]", "next_album", "Next Album", show=True),
        Binding("s", "sort_table", "Sort Table", show=True),
        Binding("r", "refresh_content", "Refresh", show=True),
    ]

    def __init__(self, tracks_dir: Path, artist_slug: str, album_slug: str) -> None:
        super().__init__()
        self.tracks_dir = Path(tracks_dir).absolute()
        self.artist_slug = artist_slug
        self.album_slug = album_slug
        self.ctx = GrooveContext(
            scope=Scope.ALBUM,
            cwd=self.tracks_dir / artist_slug / album_slug,
            tracks_dir=self.tracks_dir,
            artist=artist_slug,
            album=album_slug,
        )
        self.songs = []
        self.all_albums = []
        self.current_sort_key: Optional[ColumnKey] = None
        self.current_sort_reverse: bool = False

    def compose(self) -> ComposeResult:
        self.table = DataTable(id="songs-table")
        self.table.add_columns(
            "SONG",
            "TITLE",
            Text("TEMPO", justify="right"),
            "KEY",
            "METER",
            Text("STEMS", justify="right"),
            Text("AUP4", justify="center"),
            Text("CHORDS", justify="center"),
            Text("STUDY", justify="center"),
        )
        self.table.cursor_type = "row"

        yield Header()
        with Vertical():
            with Grid(id="summary-grid"):
                yield DataTable(id="album-meta-table", show_header=False, cursor_type=None, classes="summary-table")
                yield DataTable(id="production-table", show_header=False, cursor_type=None, classes="summary-table")
                yield DataTable(id="pocket-table", show_header=False, cursor_type=None, classes="summary-table")
            yield self.table
        yield Footer()

    def on_mount(self) -> None:
        self.all_albums = [alb for art, alb in self.ctx.list_albums(self.artist_slug)]
        alb_sum = self.ctx.get_album_summary(self.artist_slug, self.album_slug)
        title = alb_sum.get("title", self.album_slug.replace("-", " ").title())
        year = f"({alb_sum.get('year')})" if alb_sum.get("year") else ""
        art_title = self.artist_slug.replace("-", " ").title()
        self.title = f"GROOVE • {art_title} • {title} {year}"

        # Setup summary tables
        meta_table = self.query_one("#album-meta-table", DataTable)
        meta_table.add_columns("Metric", "Value")

        prod_table = self.query_one("#production-table", DataTable)
        prod_table.add_columns("Metric", "Value")

        pock_table = self.query_one("#pocket-table", DataTable)
        pock_table.add_columns("Metric", "Value")

        self.load_songs()
        self.update_summary()
        self.table.focus()

    def load_songs(self) -> None:
        """Load song rows for this album."""
        songs_raw = self.ctx.list_songs(artist=self.artist_slug, album=self.album_slug)
        self.songs = [s_slug for art, alb, s_slug in songs_raw]
        self.table.clear()

        for s_slug in self.songs:
            s_sum = self.ctx.get_song_summary(s_slug, artist_slug=self.artist_slug, album_slug=self.album_slug)

            tempo_val = s_sum.get("tempo", 0.0)
            tempo_str = f"{tempo_val:.0f} BPM" if tempo_val > 0 else "-"
            stems_cnt = Text(str(s_sum.get("stems_count", 0)), justify="right")
            has_aup4 = Text("✓", style="bold green", justify="center") if s_sum.get("has_project") else Text("-", justify="center")
            has_csml = Text("✓", style="bold blue", justify="center") if s_sum.get("has_chords") else Text("-", justify="center")
            has_study = Text("✓", style="bold magenta", justify="center") if s_sum.get("has_study") else Text("-", justify="center")

            self.table.add_row(
                s_slug,
                s_sum.get("title", s_slug),
                Text(tempo_str, justify="right", style="yellow"),
                s_sum.get("key", "-") or "-",
                s_sum.get("meter", "4/4"),
                stems_cnt,
                has_aup4,
                has_csml,
                has_study,
                key=s_slug,
            )

    def update_summary(self) -> None:
        """Populate the 3 album summary cards."""
        alb_sum = self.ctx.get_album_summary(self.artist_slug, self.album_slug)

        meta_table = self.query_one("#album-meta-table", DataTable)
        meta_table.clear()
        meta_table.add_row(Text("album:", justify="right"), Text(alb_sum.get("title", ""), justify="right", style="bold cyan"))
        meta_table.add_row(Text("year:", justify="right"), Text(str(alb_sum.get("year", "-") or "-"), justify="right"))
        meta_table.add_row(Text("label:", justify="right"), Text(alb_sum.get("label", "-"), justify="right"))
        meta_table.add_row(Text("songs in study:", justify="right"), Text(str(alb_sum.get("songs_count", 0)), justify="right"))

        prod_table = self.query_one("#production-table", DataTable)
        prod_table.clear()
        studios = ", ".join(alb_sum.get("studios", [])[:2]) or "-"
        prod_table.add_row(Text("studios:", justify="right"), Text(studios, justify="right"))
        producers = ", ".join(alb_sum.get("producers", [])[:2]) or "-"
        prod_table.add_row(Text("producers:", justify="right"), Text(producers, justify="right"))
        gear = ", ".join(alb_sum.get("key_gear", [])[:2]) or "-"
        prod_table.add_row(Text("key gear:", justify="right"), Text(gear, justify="right", style="yellow"))

        pock_table = self.query_one("#pocket-table", DataTable)
        pock_table.clear()
        t_min = alb_sum.get("tempo_min", 0.0)
        t_max = alb_sum.get("tempo_max", 0.0)
        tempo_range = f"{t_min:.0f} - {t_max:.0f} BPM" if t_min and t_max and t_min != t_max else (f"{t_min:.0f} BPM" if t_min else "-")
        pock_table.add_row(Text("tempo range:", justify="right"), Text(tempo_range, justify="right", style="yellow"))
        keys_str = ", ".join(alb_sum.get("keys", [])[:3]) or "-"
        pock_table.add_row(Text("key centers:", justify="right"), Text(keys_str, justify="right", style="blue"))
        pock_table.add_row(Text("projects ready:", justify="right"), Text(str(alb_sum.get("projects_count", 0)), justify="right", style="bold green"))

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_move_up(self) -> None:
        row = self.table.cursor_row - 1
        self.table.move_cursor(row=row)

    def action_move_down(self) -> None:
        row = self.table.cursor_row + 1
        self.table.move_cursor(row=row)

    def action_select_row(self) -> None:
        row_idx = self.table.cursor_row
        if row_idx is None or not (0 <= row_idx < len(self.songs)):
            return
        selected_song = self.songs[row_idx]

        from .song_screen import SongScreen
        self.app.push_screen(SongScreen(self.tracks_dir, self.artist_slug, self.album_slug, selected_song))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_select_row()

    def action_view_album_notes(self) -> None:
        alb_dir = self.tracks_dir / self.artist_slug / self.album_slug
        readme = alb_dir / "README.md"
        if readme.exists():
            content = readme.read_text(encoding="utf-8")
        else:
            content = f"# {self.album_slug.replace('-', ' ').title()}\n\nNo README.md notes found."
        self.app.push_screen(ContentModal(f"Album Notes: {self.album_slug.replace('-', ' ').title()}", content, is_markdown=True))

    def action_prev_album(self) -> None:
        if not self.all_albums or len(self.all_albums) <= 1:
            return
        idx = self.all_albums.index(self.album_slug) if self.album_slug in self.all_albums else 0
        new_album = self.all_albums[(idx - 1) % len(self.all_albums)]
        self.app.pop_screen()
        self.app.push_screen(AlbumScreen(self.tracks_dir, self.artist_slug, new_album))

    def action_next_album(self) -> None:
        if not self.all_albums or len(self.all_albums) <= 1:
            return
        idx = self.all_albums.index(self.album_slug) if self.album_slug in self.all_albums else 0
        new_album = self.all_albums[(idx + 1) % len(self.all_albums)]
        self.app.pop_screen()
        self.app.push_screen(AlbumScreen(self.tracks_dir, self.artist_slug, new_album))

    def action_refresh_content(self) -> None:
        curr_row = self.table.cursor_row
        self.load_songs()
        self.update_summary()
        if curr_row is not None and 0 <= curr_row < self.table.row_count:
            self.table.move_cursor(row=curr_row, animate=False)
        self.notify("Album screen refreshed")

    def action_sort_table(self) -> None:
        if not self.table.columns:
            return

        def handle_sort(selected_key: Optional[ColumnKey]) -> None:
            if not selected_key:
                return
            reverse = not self.current_sort_reverse if self.current_sort_key == selected_key else True
            self.current_sort_key = selected_key
            self.current_sort_reverse = reverse

            def get_sort_val(cell):
                plain = cell.plain if hasattr(cell, "plain") else str(cell)
                try:
                    return float(plain.split()[0])
                except ValueError:
                    return plain.lower()

            self.table.sort(selected_key, key=get_sort_val, reverse=reverse)
            col_label = getattr(self.table.columns[selected_key].label, "plain", str(self.table.columns[selected_key].label))
            self.notify(f"Sorted by {col_label} ({'desc' if reverse else 'asc'})")

        self.app.push_screen(SortModal(columns=self.table.columns), handle_sort)

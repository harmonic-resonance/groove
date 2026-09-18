"""
artist_screen.py - Level 1: Artist screen for Groove Navigator.
Displays artist summary cards and lists albums.
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


class ArtistScreen(Screen):
    """Level 1: Artist view listing albums and musical profile."""

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
        Binding("h", "go_back", "Back to Catalog", show=True),
        Binding("j", "move_down", "Cursor down", show=True),
        Binding("k", "move_up", "Cursor up", show=True),
        Binding("l,enter", "select_row", "Select Album", show=True),
        Binding("b", "view_artist_bio", "Artist Bio", show=True),
        Binding("s", "sort_table", "Sort Table", show=True),
        Binding("r", "refresh_content", "Refresh", show=True),
    ]

    def __init__(self, tracks_dir: Path, artist_slug: str) -> None:
        super().__init__()
        self.tracks_dir = Path(tracks_dir).absolute()
        self.artist_slug = artist_slug
        self.ctx = GrooveContext(
            scope=Scope.ARTIST,
            cwd=self.tracks_dir / artist_slug,
            tracks_dir=self.tracks_dir,
            artist=artist_slug,
        )
        self.albums = []
        self.current_sort_key: Optional[ColumnKey] = None
        self.current_sort_reverse: bool = False

    def compose(self) -> ComposeResult:
        self.table = DataTable(id="albums-table")
        self.table.add_columns(
            "YEAR",
            "ALBUM",
            "TITLE",
            Text("SONGS", justify="right"),
            Text("STEMS", justify="right"),
            Text("TEMPO (BPM)", justify="center"),
            Text("PROJECTS", justify="center"),
            "STUDIOS",
        )
        self.table.cursor_type = "row"

        yield Header()
        with Vertical():
            with Grid(id="summary-grid"):
                yield DataTable(id="artist-stats", show_header=False, cursor_type=None, classes="summary-table")
                yield DataTable(id="groove-profile", show_header=False, cursor_type=None, classes="summary-table")
                yield DataTable(id="production-table", show_header=False, cursor_type=None, classes="summary-table")
            yield self.table
        yield Footer()

    def on_mount(self) -> None:
        display_name = self.artist_slug.replace("-", " ").title()
        self.title = f"GROOVE • Artist: {display_name}"

        # Setup summary tables
        ast_table = self.query_one("#artist-stats", DataTable)
        ast_table.add_columns("Metric", "Value")

        groove_table = self.query_one("#groove-profile", DataTable)
        groove_table.add_columns("Metric", "Value")

        prod_table = self.query_one("#production-table", DataTable)
        prod_table.add_columns("Metric", "Value")

        self.load_albums()
        self.update_summary()
        self.table.focus()

    def load_albums(self) -> None:
        """Load album rows into DataTable."""
        self.albums = [alb for art, alb in self.ctx.list_albums(self.artist_slug)]
        self.table.clear()

        for alb in self.albums:
            alb_sum = self.ctx.get_album_summary(self.artist_slug, alb)
            year_str = str(alb_sum.get("year", "-") or "-")
            title = alb_sum.get("title", alb.replace("-", " ").title())
            songs_cnt = Text(str(alb_sum.get("songs_count", 0)), justify="right")
            stems_cnt = Text(str(alb_sum.get("stems_count", 0)), justify="right")

            t_min = alb_sum.get("tempo_min", 0.0)
            t_max = alb_sum.get("tempo_max", 0.0)
            tempo_str = f"{t_min:.0f} - {t_max:.0f}" if t_min and t_max and t_min != t_max else (f"{t_min:.0f}" if t_min else "-")

            prj_cnt = Text(str(alb_sum.get("projects_count", 0)), justify="center", style="bold green" if alb_sum.get("projects_count", 0) > 0 else "")
            studios_list = alb_sum.get("studios", [])
            studios_str = ", ".join(studios_list[:2]) if studios_list else "-"

            self.table.add_row(
                year_str,
                alb,
                title,
                songs_cnt,
                stems_cnt,
                Text(tempo_str, justify="center"),
                prj_cnt,
                studios_str,
                key=alb,
            )

    def update_summary(self) -> None:
        """Populate the 3 artist summary tables."""
        art_sum = self.ctx.get_artist_summary(self.artist_slug)

        ast_table = self.query_one("#artist-stats", DataTable)
        ast_table.clear()
        ast_table.add_row(Text("artist:", justify="right"), Text(self.artist_slug.replace("-", " ").title(), justify="right", style="bold cyan"))
        ast_table.add_row(Text("albums:", justify="right"), Text(str(art_sum.get("albums_count", 0)), justify="right"))
        ast_table.add_row(Text("songs in study:", justify="right"), Text(str(art_sum.get("songs_count", 0)), justify="right"))

        groove_table = self.query_one("#groove-profile", DataTable)
        groove_table.clear()
        t_min = art_sum.get("tempo_min", 0.0)
        t_max = art_sum.get("tempo_max", 0.0)
        t_avg = art_sum.get("tempo_avg", 0.0)
        tempo_range = f"{t_min:.0f} - {t_max:.0f} BPM" if t_min and t_max else "-"
        groove_table.add_row(Text("tempo spectrum:", justify="right"), Text(tempo_range, justify="right", style="yellow"))
        groove_table.add_row(Text("average tempo:", justify="right"), Text(f"{t_avg:.1f} BPM" if t_avg else "-", justify="right"))
        keys_str = ", ".join(art_sum.get("keys", [])[:4]) or "-"
        groove_table.add_row(Text("dominant keys:", justify="right"), Text(keys_str, justify="right", style="blue"))

        prod_table = self.query_one("#production-table", DataTable)
        prod_table.clear()
        prod_table.add_row(Text("total stems:", justify="right"), Text(str(art_sum.get("stems_count", 0)), justify="right"))
        prod_table.add_row(Text("audio duration:", justify="right"), Text(_format_time(art_sum.get("total_duration_sec", 0.0)), justify="right"))
        prod_table.add_row(Text("audacity projects:", justify="right"), Text(str(art_sum.get("projects_count", 0)), justify="right", style="bold green"))

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
        if row_idx is None or not (0 <= row_idx < len(self.albums)):
            return
        selected_album = self.albums[row_idx]

        from .album_screen import AlbumScreen
        self.app.push_screen(AlbumScreen(self.tracks_dir, self.artist_slug, selected_album))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_select_row()

    def action_view_artist_bio(self) -> None:
        artist_dir = self.tracks_dir / self.artist_slug
        readme = artist_dir / "README.md"
        if readme.exists():
            content = readme.read_text(encoding="utf-8")
        else:
            content = f"# {self.artist_slug.replace('-', ' ').title()}\n\nNo README.md profile created yet."
        self.app.push_screen(ContentModal(f"Artist Profile: {self.artist_slug.replace('-', ' ').title()}", content, is_markdown=True))

    def action_refresh_content(self) -> None:
        curr_row = self.table.cursor_row
        self.load_albums()
        self.update_summary()
        if curr_row is not None and 0 <= curr_row < self.table.row_count:
            self.table.move_cursor(row=curr_row, animate=False)
        self.notify("Artist screen refreshed")

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
                    return float(plain)
                except ValueError:
                    return plain.lower()

            self.table.sort(selected_key, key=get_sort_val, reverse=reverse)
            col_label = getattr(self.table.columns[selected_key].label, "plain", str(self.table.columns[selected_key].label))
            self.notify(f"Sorted by {col_label} ({'desc' if reverse else 'asc'})")

        self.app.push_screen(SortModal(columns=self.table.columns), handle_sort)

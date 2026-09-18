"""
catalog_screen.py - Level 0: Catalog Home screen for Groove Navigator.
Directly modeled on Seer Navigator's SessionsScreen.
"""

from pathlib import Path
from typing import Optional

from rich.text import Text
from textual import log
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header
from textual.widgets._data_table import ColumnKey

from ...context import GrooveContext, Scope
from ...study import GROOVE_FOUNDATIONS
from ..sort_modal import SortModal
from ..viewers import ContentModal


def _format_time(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if seconds <= 0:
        return "-"
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    if hours > 0:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class CatalogScreen(Screen):
    """Level 0: Catalog Home screen listing artists with collection summation."""

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
        Binding("j", "move_down", "Cursor down", show=True),
        Binding("k", "move_up", "Cursor up", show=True),
        Binding("l,enter", "select_row", "Select Artist", show=True),
        Binding("f", "view_foundations", "Foundations", show=True),
        Binding("s", "sort_table", "Sort Table", show=True),
        Binding("r", "refresh_content", "Refresh", show=True),
    ]

    def __init__(self, tracks_dir: Path) -> None:
        super().__init__()
        self.tracks_dir = Path(tracks_dir).absolute()
        self.ctx = GrooveContext(scope=Scope.ROOT, cwd=self.tracks_dir, tracks_dir=self.tracks_dir)
        self.artists = []
        self.current_sort_key: Optional[ColumnKey] = None
        self.current_sort_reverse: bool = False

    def compose(self) -> ComposeResult:
        self.table = DataTable(id="catalog-table")
        self.table.add_columns(
            "ARTIST",
            Text("ALBUMS", justify="right"),
            Text("SONGS", justify="right"),
            Text("STEMS", justify="right"),
            Text("TIME", justify="right"),
            Text("PROJECTS", justify="center"),
            Text("CHORDS", justify="center"),
        )
        self.table.cursor_type = "row"

        yield Header()
        with Vertical():
            with Grid(id="summary-grid"):
                yield DataTable(id="collection-table", show_header=False, cursor_type=None, classes="summary-table")
                yield DataTable(id="assets-table", show_header=False, cursor_type=None, classes="summary-table")
                yield DataTable(id="pipeline-table", show_header=False, cursor_type=None, classes="summary-table")
            yield self.table
        yield Footer()

    def on_mount(self) -> None:
        self.title = "GROOVE • Master Rhythm Studies Catalog"

        # Setup summary tables
        col_table = self.query_one("#collection-table", DataTable)
        col_table.add_columns("Metric", "Value")

        ast_table = self.query_one("#assets-table", DataTable)
        ast_table.add_columns("Metric", "Value")

        pip_table = self.query_one("#pipeline-table", DataTable)
        pip_table.add_columns("Metric", "Value")

        self.load_artists()
        self.update_summary()
        self.table.focus()

    def load_artists(self) -> None:
        """Load artist rows into the main DataTable."""
        self.artists = self.ctx.list_artists()
        self.table.clear()

        for art in self.artists:
            summary = self.ctx.get_artist_summary(art)
            display_name = art.replace("-", " ").title()

            alb_cnt = Text(str(summary.get("albums_count", 0)), justify="right")
            sng_cnt = Text(str(summary.get("songs_count", 0)), justify="right")
            stm_cnt = Text(str(summary.get("stems_count", 0)), justify="right")
            dur_str = Text(_format_time(summary.get("total_duration_sec", 0.0)), justify="right")
            prj_cnt = Text(str(summary.get("projects_count", 0)), justify="center", style="bold green" if summary.get("projects_count", 0) > 0 else "")
            crd_cnt = Text(str(summary.get("chords_count", 0)), justify="center", style="bold blue" if summary.get("chords_count", 0) > 0 else "")

            self.table.add_row(
                display_name,
                alb_cnt,
                sng_cnt,
                stm_cnt,
                dur_str,
                prj_cnt,
                crd_cnt,
                key=art,
            )

    def update_summary(self) -> None:
        """Populate the three summary cards."""
        cat_sum = self.ctx.get_catalog_summary()

        col_table = self.query_one("#collection-table", DataTable)
        col_table.clear()
        col_table.add_row(Text("artists:", justify="right"), Text(str(cat_sum.get("artists_count", 0)), justify="right"))
        col_table.add_row(Text("albums:", justify="right"), Text(str(cat_sum.get("albums_count", 0)), justify="right"))
        col_table.add_row(Text("songs:", justify="right"), Text(str(cat_sum.get("songs_count", 0)), justify="right"))

        ast_table = self.query_one("#assets-table", DataTable)
        ast_table.clear()
        ast_table.add_row(Text("total stems:", justify="right"), Text(str(cat_sum.get("stems_count", 0)), justify="right"))
        ast_table.add_row(Text("audio time:", justify="right"), Text(_format_time(cat_sum.get("total_duration_sec", 0.0)), justify="right"))
        ast_table.add_row(Text("groove studies:", justify="right"), Text(str(cat_sum.get("studies_count", 0)), justify="right"))

        pip_table = self.query_one("#pipeline-table", DataTable)
        pip_table.clear()
        pip_table.add_row(Text("audacity projects:", justify="right"), Text(str(cat_sum.get("projects_count", 0)), justify="right", style="bold green"))
        pip_table.add_row(Text("chords (csml):", justify="right"), Text(str(cat_sum.get("chords_count", 0)), justify="right", style="bold blue"))
        pip_table.add_row(Text("local audio files:", justify="right"), Text(str(cat_sum.get("local_files_count", 0)), justify="right"))

    def action_move_up(self) -> None:
        row = self.table.cursor_row - 1
        self.table.move_cursor(row=row)

    def action_move_down(self) -> None:
        row = self.table.cursor_row + 1
        self.table.move_cursor(row=row)

    def action_select_row(self) -> None:
        row_idx = self.table.cursor_row
        if row_idx is None or not (0 <= row_idx < len(self.artists)):
            return
        selected_artist = self.artists[row_idx]

        from .artist_screen import ArtistScreen
        self.app.push_screen(ArtistScreen(self.tracks_dir, selected_artist))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_select_row()

    def action_view_foundations(self) -> None:
        self.app.push_screen(ContentModal("Groove Foundations", GROOVE_FOUNDATIONS, is_markdown=True))

    def action_refresh_content(self) -> None:
        curr_row = self.table.cursor_row
        self.load_artists()
        self.update_summary()
        if curr_row is not None and 0 <= curr_row < self.table.row_count:
            self.table.move_cursor(row=curr_row, animate=False)
        self.notify("Catalog refreshed")

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

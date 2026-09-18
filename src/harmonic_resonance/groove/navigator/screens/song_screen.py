"""
song_screen.py - Level 3: Song screen for Groove Navigator.
Displays pocket summation, stem track breakdown, and context-aware rehearsal actions.
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

from ...audacity import (
    extract_offsets_from_aup4,
    open_song_in_audacity,
    pad_song_tracks,
)
from ...catalog import load_song_tracks, save_song_tracks
from ...context import GrooveContext, Scope, parse_duration_seconds
from ..sort_modal import SortModal
from ..viewers import ContentModal
from .catalog_screen import _format_time


class SongScreen(Screen):
    """Level 3: Song rehearsal cockpit with stem multitrack table and direct action hotkeys."""

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
        Binding("h", "go_back", "Back to Album", show=True),
        Binding("j", "move_down", "Cursor down", show=True),
        Binding("k", "move_up", "Cursor up", show=True),
        Binding("o", "open_audacity", "Open Audacity", show=True),
        Binding("a", "align_offsets", "Extract Align", show=True),
        Binding("p", "pad_stems", "Pad Stems", show=True),
        Binding("c", "view_chords", "Chords (CSML)", show=True),
        Binding("u", "view_study", "Groove Study", show=True),
        Binding("[", "prev_song", "Prev Song", show=True),
        Binding("]", "next_song", "Next Song", show=True),
        Binding("s", "sort_table", "Sort Table", show=True),
        Binding("r", "refresh_content", "Refresh", show=True),
    ]

    def __init__(
        self,
        tracks_dir: Path,
        artist_slug: str,
        album_slug: Optional[str],
        song_slug: str,
    ) -> None:
        super().__init__()
        self.tracks_dir = Path(tracks_dir).absolute()
        self.artist_slug = artist_slug
        self.album_slug = album_slug
        self.song_slug = song_slug

        self.ctx = GrooveContext(
            scope=Scope.SONG,
            cwd=self.tracks_dir / artist_slug / (album_slug or "") / song_slug,
            tracks_dir=self.tracks_dir,
            artist=artist_slug,
            album=album_slug,
            song=song_slug,
        )
        self.song_dir = self.ctx.find_song_dir(song_slug, artist_id=artist_slug, album_id=album_slug)
        self.tracks = []
        self.sibling_songs = []
        self.current_sort_key: Optional[ColumnKey] = None
        self.current_sort_reverse: bool = False

    def compose(self) -> ComposeResult:
        self.table = DataTable(id="stems-table")
        self.table.add_columns(
            "#",
            "STEM",
            "DISPLAY NAME",
            Text("OFFSET", justify="right"),
            Text("DURATION", justify="right"),
            Text("FILE", justify="center"),
            "TYPE",
            "SOURCE URL",
        )
        self.table.cursor_type = "row"

        yield Header()
        with Vertical():
            with Grid(id="summary-grid"):
                yield DataTable(id="song-meta-table", show_header=False, cursor_type=None, classes="summary-table")
                yield DataTable(id="pocket-table", show_header=False, cursor_type=None, classes="summary-table")
                yield DataTable(id="rehearsal-table", show_header=False, cursor_type=None, classes="summary-table")
            yield self.table
        yield Footer()

    def on_mount(self) -> None:
        # Resolve sibling songs for [ and ] navigation
        raw_siblings = self.ctx.list_songs(artist=self.artist_slug, album=self.album_slug)
        self.sibling_songs = [s for art, alb, s in raw_siblings]

        s_sum = self.ctx.get_song_summary(self.song_slug, artist_slug=self.artist_slug, album_slug=self.album_slug)
        title = s_sum.get("title", self.song_slug.replace("-", " ").title())
        alb_title = self.album_slug.replace("-", " ").title() if self.album_slug else ""
        art_title = self.artist_slug.replace("-", " ").title()
        self.title = f"GROOVE • {art_title} • {alb_title} • {title}"

        meta_table = self.query_one("#song-meta-table", DataTable)
        meta_table.add_columns("Metric", "Value")

        pock_table = self.query_one("#pocket-table", DataTable)
        pock_table.add_columns("Metric", "Value")

        reh_table = self.query_one("#rehearsal-table", DataTable)
        reh_table.add_columns("Metric", "Value")

        self.load_stems()
        self.update_summary()
        self.table.focus()

    def load_stems(self) -> None:
        """Load stem tracks from tracks.csv."""
        if not self.song_dir or not self.song_dir.exists():
            return
        self.tracks = load_song_tracks(self.song_dir)
        self.table.clear()

        for t in self.tracks:
            num = str(t.get("track_number", "00")).zfill(2)
            stem_name = t.get("stem_name", "")
            disp_name = t.get("display_name", stem_name)

            off_val = float(t.get("start_offset", 0.0) or 0.0)
            off_str = f"+{off_val:.4f}s" if off_val > 0 else "-"

            dur_val = parse_duration_seconds(t.get("duration", 0.0))
            dur_str = _format_time(dur_val)

            # Check if matching local audio file exists on disk
            has_file = any(
                f.is_file() and f.stem.startswith(num)
                for f in self.song_dir.iterdir()
            )
            file_badge = Text("✓", style="bold green", justify="center") if has_file else Text("missing", style="dim red", justify="center")

            src_url = t.get("source_url", "") or "-"
            if len(src_url) > 35:
                src_url = src_url[:32] + "..."

            self.table.add_row(
                num,
                stem_name,
                disp_name,
                Text(off_str, justify="right", style="cyan" if off_val > 0 else "dim"),
                Text(dur_str, justify="right"),
                file_badge,
                t.get("source_type", "stem"),
                src_url,
                key=num,
            )

    def update_summary(self) -> None:
        """Populate the 3 pocket and rehearsal summary cards."""
        s_sum = self.ctx.get_song_summary(self.song_slug, artist_slug=self.artist_slug, album_slug=self.album_slug)

        meta_table = self.query_one("#song-meta-table", DataTable)
        meta_table.clear()
        meta_table.add_row(Text("song:", justify="right"), Text(s_sum.get("title", ""), justify="right", style="bold white"))
        meta_table.add_row(Text("tempo / meter:", justify="right"), Text(f"{s_sum.get('tempo', 0.0):.0f} BPM  ({s_sum.get('meter', '4/4')})", justify="right", style="yellow"))
        meta_table.add_row(Text("musical key:", justify="right"), Text(s_sum.get("key", "-"), justify="right", style="bold blue"))

        pock_table = self.query_one("#pocket-table", DataTable)
        pock_table.clear()
        pock_table.add_row(Text("stems registered:", justify="right"), Text(str(s_sum.get("stems_count", 0)), justify="right"))
        pock_table.add_row(Text("ref duration:", justify="right"), Text(_format_time(s_sum.get("duration", 0.0)), justify="right"))
        max_off = s_sum.get("max_offset", 0.0)
        pock_table.add_row(Text("max alignment:", justify="right"), Text(f"+{max_off:.4f}s" if max_off > 0 else "locked (0s)", justify="right", style="cyan"))

        reh_table = self.query_one("#rehearsal-table", DataTable)
        reh_table.clear()
        reh_table.add_row(Text("audacity project:", justify="right"), Text("✓ (.aup4 ready)" if s_sum.get("has_project") else "not built", justify="right", style="bold green" if s_sum.get("has_project") else "dim"))
        reh_table.add_row(Text("chords (csml):", justify="right"), Text("✓ (present)" if s_sum.get("has_chords") else "missing", justify="right", style="bold blue" if s_sum.get("has_chords") else "dim"))
        files_cnt = s_sum.get("files_present", 0)
        reh_table.add_row(Text("local audio files:", justify="right"), Text(f"{files_cnt} files", justify="right", style="bold green" if files_cnt > 0 else "red"))

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_move_up(self) -> None:
        row = self.table.cursor_row - 1
        self.table.move_cursor(row=row)

    def action_move_down(self) -> None:
        row = self.table.cursor_row + 1
        self.table.move_cursor(row=row)

    def action_open_audacity(self) -> None:
        """Launch Audacity 4 with this song study."""
        if not self.song_dir:
            self.notify("Song directory not found", severity="error")
            return
        self.notify(f"Launching Audacity 4 for {self.song_slug}...")
        try:
            open_song_in_audacity(self.song_dir)
        except Exception as e:
            self.notify(f"Error opening Audacity: {e}", severity="error")

    def action_align_offsets(self) -> None:
        """Extract offsets from .aup4 and save to tracks.csv."""
        if not self.song_dir:
            return
        aup4_files = list(self.song_dir.glob("*.aup4"))
        if not aup4_files:
            self.notify("No .aup4 project found to extract offsets from", severity="warning")
            return
        aup4_path = aup4_files[0]
        try:
            offsets = extract_offsets_from_aup4(aup4_path)
            if not offsets:
                self.notify("No clips found in .aup4", severity="information")
                return
            # Update tracks.csv
            tracks = load_song_tracks(self.song_dir)
            updated = 0
            for t in tracks:
                s_name = t.get("stem_name", "")
                if s_name in offsets:
                    t["start_offset"] = f"{offsets[s_name]:.6f}"
                    updated += 1
            save_song_tracks(self.song_dir, tracks)
            self.load_stems()
            self.update_summary()
            self.notify(f"Aligned {updated} track offsets into tracks.csv", severity="information")
        except Exception as e:
            self.notify(f"Alignment error: {e}", severity="error")

    def action_pad_stems(self) -> None:
        """Pad audio tracks with silence for locked pocket timeline."""
        if not self.song_dir:
            return
        self.notify(f"Padding tracks in {self.song_slug}...")
        try:
            pad_song_tracks(self.song_dir)
            self.load_stems()
            self.update_summary()
            self.notify("Tracks successfully padded and time-locked", severity="information")
        except Exception as e:
            self.notify(f"Padding error: {e}", severity="error")

    def action_view_chords(self) -> None:
        if not self.song_dir:
            return
        csml_path = self.song_dir / "chords.csml"
        if csml_path.exists():
            content = csml_path.read_text(encoding="utf-8")
        else:
            content = f"# Chords for {self.song_slug}\n\nNo chords.csml sheet created yet."
        self.app.push_screen(ContentModal(f"Chords Sheet (CSML): {self.song_slug}", content, is_markdown=False))

    def action_view_study(self) -> None:
        if not self.song_dir:
            return
        study_path = self.song_dir / "README.md"
        if study_path.exists():
            content = study_path.read_text(encoding="utf-8")
        else:
            content = f"# Groove Study: {self.song_slug}\n\nNo README.md study created yet."
        self.app.push_screen(ContentModal(f"Groove Study: {self.song_slug}", content, is_markdown=True))

    def action_prev_song(self) -> None:
        if not self.sibling_songs or len(self.sibling_songs) <= 1:
            return
        idx = self.sibling_songs.index(self.song_slug) if self.song_slug in self.sibling_songs else 0
        new_song = self.sibling_songs[(idx - 1) % len(self.sibling_songs)]
        self.app.pop_screen()
        self.app.push_screen(SongScreen(self.tracks_dir, self.artist_slug, self.album_slug, new_song))

    def action_next_song(self) -> None:
        if not self.sibling_songs or len(self.sibling_songs) <= 1:
            return
        idx = self.sibling_songs.index(self.song_slug) if self.song_slug in self.sibling_songs else 0
        new_song = self.sibling_songs[(idx + 1) % len(self.sibling_songs)]
        self.app.pop_screen()
        self.app.push_screen(SongScreen(self.tracks_dir, self.artist_slug, self.album_slug, new_song))

    def action_refresh_content(self) -> None:
        curr_row = self.table.cursor_row
        self.load_stems()
        self.update_summary()
        if curr_row is not None and 0 <= curr_row < self.table.row_count:
            self.table.move_cursor(row=curr_row, animate=False)
        self.notify("Song stems refreshed")

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
                    clean = plain.replace("+", "").replace("s", "")
                    return float(clean)
                except ValueError:
                    return plain.lower()

            self.table.sort(selected_key, key=get_sort_val, reverse=reverse)
            col_label = getattr(self.table.columns[selected_key].label, "plain", str(self.table.columns[selected_key].label))
            self.notify(f"Sorted by {col_label} ({'desc' if reverse else 'asc'})")

        self.app.push_screen(SortModal(columns=self.table.columns), handle_sort)

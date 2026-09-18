"""
song_screen.py - Level 3: Song screen for Groove Navigator.
Displays pocket summation, stem track breakdown, and context-aware rehearsal actions.
"""

from pathlib import Path
from typing import Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Grid, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static
from textual.widgets._data_table import ColumnKey

from ...audacity import (
    extract_offsets_from_aup4,
    open_song_in_audacity,
    pad_song_tracks,
)
from ...catalog import load_song_tracks, save_song_tracks
from ...context import GrooveContext, Scope, parse_duration_seconds
from ...player import (
    AudioPlayerManager,
    SpectrumMode,
    MODE_LABELS,
    extract_waveform_envelope,
    render_waveform_ascii,
)
from ..sort_modal import SortModal
from ..viewers import ContentModal
from .catalog_screen import _format_time


class SongScreen(Screen):
    """Level 3: Song rehearsal cockpit with stem multitrack table, audio playback, and real-time spectrum."""

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
    }
    DataTable {
        height: 1fr;
    }
    #player-container {
        height: 5;
        background: $surface-darken-1;
        border: solid $accent-darken-2;
        padding: 0 1;
        margin: 0 1 1 1;
    }
    #player-status {
        height: 1;
        text-style: bold;
    }
    #player-waveform {
        height: 2;
    }
    Vertical {
        height: 100%;
    }
    """

    BINDINGS = [
        Binding("h", "go_back", "Back to Album", show=True),
        Binding("j", "move_down", "Cursor down", show=False),
        Binding("k", "move_up", "Cursor up", show=False),
        Binding("enter", "play_selected", "Play Stem", show=True),
        Binding("space", "toggle_play", "Play/Pause", show=True),
        Binding("x", "stop_play", "Stop Audio", show=True),
        Binding("v", "cycle_visualizer", "Visualizer Mode", show=True),
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

        self.player_mgr = AudioPlayerManager.get_instance()
        self.current_waveform_peaks: list[float] = []
        self.current_playing_file: Optional[Path] = None
        self.current_playing_name: Optional[str] = None

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
            with Container(id="player-container"):
                yield Static(id="player-status")
                yield Static(id="player-waveform")
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
        self.update_player_ui()
        self.set_interval(0.1, self.update_player_ui)
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
            has_file = self._find_stem_audio_file(num, stem_name) is not None
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

    def on_unmount(self) -> None:
        self.player_mgr.stop()

    def _find_stem_audio_file(self, track_num: str, stem_name: str) -> Optional[Path]:
        """Find matching audio file on disk for a given track number or stem name."""
        if not self.song_dir or not self.song_dir.exists():
            return None
        num = str(track_num).zfill(2)
        candidate_dirs = [self.song_dir, self.song_dir / "raw_unpadded"]
        for d in candidate_dirs:
            if not d.is_dir():
                continue
            for ext in [".webm", ".wav", ".flac", ".mp3", ".opus", ".m4a"]:
                for f in d.iterdir():
                    if f.is_file() and f.suffix.lower() == ext:
                        if f.stem.startswith(num) or stem_name in f.stem:
                            return f
        return None

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Play stem track when Enter or clicked on row."""
        self.action_play_selected()

    def action_play_selected(self) -> None:
        """Play the stem track under cursor with real-time spectrum visualization."""
        if not self.tracks or self.table.cursor_row is None:
            return
        row_idx = self.table.cursor_row
        if row_idx < 0 or row_idx >= len(self.tracks):
            return

        t = self.tracks[row_idx]
        num = str(t.get("track_number", "00")).zfill(2)
        stem_name = t.get("stem_name", "")
        disp_name = t.get("display_name", stem_name)

        audio_file = self._find_stem_audio_file(num, stem_name)
        if not audio_file:
            self.notify(f"No local audio file found for {disp_name}. Run 'groove download' first.", severity="warning")
            return

        s_sum = self.ctx.get_song_summary(self.song_slug, artist_slug=self.artist_slug, album_slug=self.album_slug)
        song_key = s_sum.get("key", "")

        try:
            self.current_playing_file = audio_file
            self.current_playing_name = disp_name
            self.current_waveform_peaks = extract_waveform_envelope(audio_file, num_bars=70)
            self.player_mgr.play(
                audio_path=audio_file,
                stem_name=disp_name,
                title=f"Groove: {self.song_slug} - {disp_name}",
                musical_key=song_key,
            )
            mode_lbl = MODE_LABELS.get(self.player_mgr.current_mode, "Musical CQT Notes")
            key_info = f" [Key: {song_key}]" if song_key else ""
            self.notify(f"Playing: {disp_name}  [{mode_lbl}]{key_info}", severity="information")
            self.update_player_ui()
        except Exception as e:
            self.notify(f"Playback error: {e}", severity="error")

    def action_toggle_play(self) -> None:
        """Toggle pause/resume or play current track."""
        if self.player_mgr.is_playing():
            if self.player_mgr.active_player:
                self.player_mgr.active_player.toggle_pause()
            self.update_player_ui()
        else:
            self.action_play_selected()

    def action_stop_play(self) -> None:
        """Stop audio playback."""
        if self.player_mgr.is_playing():
            self.player_mgr.stop()
            self.notify("Audio stopped")
            self.update_player_ui()

    def action_cycle_visualizer(self) -> None:
        """Cycle spectrum visualization mode (CQT -> Waveform -> Freqs -> Waves -> Spectrogram)."""
        new_mode = self.player_mgr.cycle_mode()
        lbl = MODE_LABELS.get(new_mode, new_mode)
        self.notify(f"Visualizer: {lbl}")
        self.update_player_ui()

    def update_player_ui(self) -> None:
        """Update the player status bar and full-track waveform with active playhead."""
        try:
            status_widget = self.query_one("#player-status", Static)
            wave_widget = self.query_one("#player-waveform", Static)
        except Exception:
            return

        status = self.player_mgr.get_status()
        if status["playing"]:
            cur_pos = status["position"]
            dur = status["duration"]
            ratio = status["progress_ratio"]
            pct = int(ratio * 100)
            paused = status["paused"]
            icon = "⏸ PAUSED" if paused else "▶ PLAYING"
            style = "bold yellow" if paused else "bold green"
            mode_lbl = status["mode_label"]
            m_key = status.get("musical_key")
            key_str = f"  • [yellow]Key: {m_key}[/yellow]" if m_key else ""

            pos_str = f"{_format_time(cur_pos)} / {_format_time(dur)}"
            status_text = (
                f"[{style}]{icon}[/{style}] [bold white]{self.current_playing_name or status['stem_name']}[/bold white]  "
                f"[bold cyan]{pos_str}[/bold cyan] ({pct}%)  "
                f"[dim]• Mode: {mode_lbl}{key_str}  • [bold]Space[/bold]: Pause  [bold]v[/bold]: Mode  [bold]x[/bold]: Stop[/dim]"
            )
            status_widget.update(status_text)

            if self.current_waveform_peaks:
                wave_line, scrub_line = render_waveform_ascii(self.current_waveform_peaks, progress_ratio=ratio, width=70)
                wave_widget.update(f"{wave_line}\n{scrub_line}")
            else:
                wave_widget.update("[dim]Rendering waveform...[/dim]")
        else:
            status_widget.update("[dim]⏹ STOPPED  •  [bold]Enter / Space[/bold]: Play Stem  |  [bold]v[/bold]: Visualizer Mode  |  [bold]x[/bold]: Stop[/dim]")
            wave_widget.update("[dim white]──────────────────────────────────────────────────────────────────────[/dim white]")

    def action_go_back(self) -> None:
        self.player_mgr.stop()
        self.app.pop_screen()

    def action_move_up(self) -> None:
        row = self.table.cursor_row - 1
        self.table.move_cursor(row=row)

    def action_move_down(self) -> None:
        row = self.table.cursor_row + 1
        self.table.move_cursor(row=row)

    def action_open_audacity(self) -> None:
        """Launch Audacity 4 with this song study."""
        self.player_mgr.stop()
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
        self.player_mgr.stop()
        if not self.sibling_songs or len(self.sibling_songs) <= 1:
            return
        idx = self.sibling_songs.index(self.song_slug) if self.song_slug in self.sibling_songs else 0
        new_song = self.sibling_songs[(idx - 1) % len(self.sibling_songs)]
        self.app.pop_screen()
        self.app.push_screen(SongScreen(self.tracks_dir, self.artist_slug, self.album_slug, new_song))

    def action_next_song(self) -> None:
        self.player_mgr.stop()
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

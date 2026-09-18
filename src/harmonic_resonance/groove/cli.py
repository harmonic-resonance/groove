"""
cli.py - Rich, context-aware command-line interface for Groove.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    console = Console()
except ImportError:
    console = None


from .context import detect_context, Scope, GrooveContext
from .catalog import (
    CATALOG,
    Song,
    get_song,
    list_songs,
    load_tracks_from_csv,
    load_song_tracks,
    save_song_tracks,
    TRACK_FIELDS,
)
from .downloader import (
    download_song_stems,
    get_song_directory,
    slice_audio_file,
    regenerate_song_from_sources,
)
from .audacity import (
    extract_offsets_from_aup4,
    get_audio_duration,
    pad_track_audio,
    pad_song_tracks,
    launch_audacity,
    open_song_in_audacity,
)
from .scaffold import (
    create_artist_readme,
    create_album_scaffold,
    create_song_scaffold,
    add_track_entry,
)
from .study import get_groove_study, GROOVE_FOUNDATIONS


def print_msg(msg: str):
    if console:
        console.print(msg)
    else:
        import re
        clean = re.sub(r"\[.*?\]", "", msg)
        print(clean)


def resolve_target_song(args, ctx: GrooveContext) -> Tuple[Optional[Song], Path]:
    """
    Resolve targeted song and its directory from CLI args and context.
    Returns (song_object_or_None, song_directory_path).
    """
    song_id = getattr(args, "song", None)
    if not song_id:
        if ctx.scope == Scope.SONG and ctx.song:
            song_id = ctx.song
        else:
            print_msg("[bold red]Error:[/bold red] No song specified. Provide a song name or run from within a song directory.")
            sys.exit(1)

    normalized = song_id.lower().replace(" ", "-").replace("_", "-")
    song = get_song(normalized)

    # Locate directory
    song_dir = ctx.find_song_dir(normalized)
    if not song_dir:
        artist_slug = song.artist.lower().replace(" ", "-") if song else (ctx.artist or "unknown")
        tracks_dir = ctx.tracks_dir or Path("tracks")
        song_dir = tracks_dir / artist_slug / normalized

    return song, song_dir


def cmd_nav(args):
    """Launch the interactive Groove Navigator TUI (Seer style)."""
    try:
        from .navigator import run_navigator
        run_navigator()
    except ImportError as e:
        print_msg(f"[bold red]Error launching navigator:[/bold red] {e}")
        print_msg("[yellow]Ensure textual is installed: uv tool install --editable . --reinstall (or uv pip install -e .)[/yellow]")
        sys.exit(1)


def cmd_list(args):
    """List available groove studies (sensitive to current context)."""
    ctx = detect_context()

    if ctx.scope == Scope.SONG and ctx.song:
        cmd_info(args)
        return

    if ctx.scope == Scope.ALBUM and ctx.album:
        songs = ctx.list_songs(artist=ctx.artist, album=ctx.album)
        alb_sum = ctx.get_album_summary(ctx.artist, ctx.album)
        title = alb_sum.get("title", ctx.album.replace("-", " ").title())
        year = f" ({alb_sum.get('year')})" if alb_sum.get("year") else ""
        art_title = ctx.artist.replace("-", " ").title() if ctx.artist else ""

        if console:
            table = Table(title=f"[bold magenta]Album Study: {art_title} • {title}{year}[/bold magenta]")
            table.add_column("Song Slug", style="cyan")
            table.add_column("Title", style="bold white")
            table.add_column("Tempo", justify="right", style="yellow")
            table.add_column("Key", style="blue")
            table.add_column("Tracks", justify="center", style="green")
            table.add_column("CSML", justify="center", style="blue")
            table.add_column("Project", justify="center", style="magenta")

            for art, alb, s_slug in songs:
                s_sum = ctx.get_song_summary(s_slug, artist_slug=art, album_slug=alb)
                has_csml = "✓" if s_sum.get("has_chords") else "-"
                has_proj = "✓" if s_sum.get("has_project") else "-"
                tempo_str = f"{s_sum.get('tempo', 0.0):.0f} BPM" if s_sum.get("tempo", 0.0) > 0 else "-"
                table.add_row(
                    s_slug,
                    s_sum.get("title", s_slug),
                    tempo_str,
                    s_sum.get("key", "-") or "-",
                    str(s_sum.get("stems_count", 0)),
                    has_csml,
                    has_proj,
                )
            console.print(table)
        else:
            print(f"\nSongs on {title}{year}:")
            for art, alb, s_slug in songs:
                s_sum = ctx.get_song_summary(s_slug, artist_slug=art, album_slug=alb)
                print(f"  - {s_slug:<20} ({s_sum.get('stems_count', 0)} tracks)")
        return

    if ctx.scope == Scope.ARTIST and ctx.artist:
        albums = ctx.list_albums(artist=ctx.artist)
        art_sum = ctx.get_artist_summary(ctx.artist)
        art_title = ctx.artist.replace("-", " ").title()

        if albums and console:
            table = Table(title=f"[bold magenta]Discography & Albums: {art_title}[/bold magenta]")
            table.add_column("Year", style="yellow")
            table.add_column("Album Slug", style="cyan")
            table.add_column("Title", style="bold white")
            table.add_column("Songs", justify="right", style="green")
            table.add_column("Stems", justify="right", style="cyan")
            table.add_column("Tempo Spectrum", justify="center", style="yellow")
            table.add_column("Projects", justify="center", style="magenta")

            for art, alb in albums:
                alb_sum = ctx.get_album_summary(art, alb)
                year_str = str(alb_sum.get("year", "-") or "-")
                title = alb_sum.get("title", alb.replace("-", " ").title())
                t_min = alb_sum.get("tempo_min", 0.0)
                t_max = alb_sum.get("tempo_max", 0.0)
                tempo_str = f"{t_min:.0f}-{t_max:.0f} BPM" if t_min and t_max and t_min != t_max else (f"{t_min:.0f} BPM" if t_min else "-")
                table.add_row(
                    year_str,
                    alb,
                    title,
                    str(alb_sum.get("songs_count", 0)),
                    str(alb_sum.get("stems_count", 0)),
                    tempo_str,
                    str(alb_sum.get("projects_count", 0)),
                )
            console.print(table)
            return

    # Root scope: list artists
    artists = ctx.list_artists()
    if artists and console:
        cat_sum = ctx.get_catalog_summary()
        table = Table(title=f"[bold magenta]Groove Catalog - Master Rhythm Studies ({cat_sum.get('songs_count', 0)} songs across {cat_sum.get('albums_count', 0)} albums)[/bold magenta]")
        table.add_column("Artist", style="green", no_wrap=True)
        table.add_column("Albums", justify="right", style="yellow")
        table.add_column("Songs", justify="right", style="cyan")
        table.add_column("Stems", justify="right", style="white")
        table.add_column("Tempo Range", justify="center", style="yellow")
        table.add_column("Projects", justify="center", style="magenta")

        for art in artists:
            art_sum = ctx.get_artist_summary(art)
            t_min = art_sum.get("tempo_min", 0.0)
            t_max = art_sum.get("tempo_max", 0.0)
            tempo_str = f"{t_min:.0f}-{t_max:.0f} BPM" if t_min and t_max and t_min != t_max else (f"{t_min:.0f} BPM" if t_min else "-")
            table.add_row(
                art.replace("-", " ").title(),
                str(art_sum.get("albums_count", 0)),
                str(art_sum.get("songs_count", 0)),
                str(art_sum.get("stems_count", 0)),
                tempo_str,
                str(art_sum.get("projects_count", 0)),
            )
        console.print(table)
        return

    # Fallback to in-memory catalog
    cat_songs = list_songs()
    if console:
        table = Table(title="[bold magenta]Groove Catalog (Catalog Definitions)[/bold magenta]")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="bold white")
        table.add_column("Artist", style="green")
        table.add_column("Tempo", justify="right", style="yellow")
        table.add_column("Key", style="blue")
        for song in cat_songs:
            table.add_row(song.id, song.title, song.artist, f"{song.tempo_bpm:.0f} BPM", song.key)
        console.print(table)


def cmd_info(args):
    """Show details, stems, and metadata for a song."""
    ctx = detect_context()
    song, song_dir = resolve_target_song(args, ctx)

    title = song.title if song else song_dir.name.replace("-", " ").title()
    artist = song.artist if song else (song_dir.parent.name.replace("-", " ").title() if song_dir else "Unknown")
    album = song.album if song else "TBD"
    year = song.year if song else "TBD"
    tempo = f"{song.tempo_bpm} BPM" if song else "TBD"
    key = song.key if song else "TBD"
    meter = song.time_signature if song else "4/4"

    tracks = load_song_tracks(song_dir) if song_dir.exists() else []

    if console:
        panel_content = (
            f"[bold white]{title}[/bold white] by [green]{artist}[/green]\n"
            f"[dim]Directory:[/dim] {song_dir}\n"
            f"[dim]Album:[/dim] {album} ({year}) | [dim]Tempo:[/dim] [yellow]{tempo}[/yellow] | [dim]Key:[/dim] [blue]{key}[/blue] | [dim]Meter:[/dim] {meter}"
        )
        console.print(Panel(panel_content, title=f"Song Study: {song_dir.name}", border_style="cyan"))

        if tracks:
            table = Table(title=f"Tracks in tracks.csv ({len(tracks)})")
            table.add_column("#", justify="right", style="yellow")
            table.add_column("Stem Name", style="bold green")
            table.add_column("Display Name", style="white")
            table.add_column("Offset", justify="right", style="cyan")
            table.add_column("Dur", justify="center", style="dim")

            for t in tracks:
                off = float(t.get("start_offset", 0.0) or 0.0)
                table.add_row(
                    t.get("track_number", ""),
                    t.get("stem_name", ""),
                    t.get("display_name", ""),
                    f"+{off:.4f}s" if off > 0 else "-",
                    t.get("duration", ""),
                )
            console.print(table)
        print_msg(f"\n[bold green]Commands for this song:[/bold green]")
        print_msg(f"  groove open              # Open in Audacity")
        print_msg(f"  groove chords            # View chord sheet (CSML)")
        print_msg(f"  groove study             # Read groove & pocket breakdown\n")
    else:
        print(f"\nSONG STUDY: {title} by {artist}")
        print(f"Directory: {song_dir}")
        print(f"Tracks: {len(tracks)}")


def cmd_study(args):
    """Display in-depth groove analysis and rehearsal tips."""
    ctx = detect_context()
    song, song_dir = resolve_target_song(args, ctx)

    # First check if README.md exists in song_dir
    readme_path = song_dir / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        if console:
            console.print(Markdown(content))
        else:
            print(content)
        return

    # Fallback to study module text
    if song:
        study_text = get_groove_study(song.id)
        if console:
            console.print(Markdown(study_text))
        else:
            print(study_text)
    else:
        print_msg(f"[bold yellow]No study guide found for '{song_dir.name}'.[/bold yellow]")


def cmd_chords(args):
    """Display CSML chord progressions and lyrics for a song."""
    ctx = detect_context()
    song, song_dir = resolve_target_song(args, ctx)

    csml_path = song_dir / "chords.csml"
    if not csml_path.exists():
        print_msg(f"[bold yellow]No chords.csml found in {song_dir}.[/bold yellow]")
        return

    content = csml_path.read_text(encoding="utf-8")
    title = song.title if song else song_dir.name.replace("-", " ").title()
    if console:
        panel = Panel(content, title=f"[bold cyan]Chord Sheet (CSML): {title}[/bold cyan]", border_style="green")
        console.print(panel)
    else:
        print(f"\n=== CHORD SHEET (CSML): {title} ===")
        print(content)


def cmd_tracks(args):
    """List or inspect track source URLs from tracks.csv."""
    ctx = detect_context()
    song_name = getattr(args, "song", None) or (ctx.song if ctx.scope == Scope.SONG else None)
    artist_name = ctx.artist if ctx.scope == Scope.ARTIST else None

    tracks = load_tracks_from_csv(song_id=song_name, artist_id=artist_name)
    if not tracks:
        print_msg("[bold yellow]No tracks found in tracks.csv.[/bold yellow]")
        return

    title_str = f"Tracks for '{song_name}'" if song_name else "Groove Audio Tracks Registry"
    if console:
        table = Table(title=f"[bold magenta]{title_str}[/bold magenta]")
        if not song_name:
            table.add_column("Song", style="cyan", no_wrap=True)
        table.add_column("#", justify="right", style="yellow")
        table.add_column("Stem Name", style="bold green")
        table.add_column("Display Name", style="white")
        table.add_column("Start Offset", justify="right", style="yellow")
        table.add_column("Dur", justify="center", style="dim")
        table.add_column("Type", style="magenta")
        table.add_column("URL", style="blue")

        for t in tracks:
            offset = float(t.get("start_offset", 0.0) or 0.0)
            row = []
            if not song_name:
                row.append(t.get("song_id", ""))
            row.extend([
                t.get("track_number", ""),
                t.get("stem_name", ""),
                t.get("display_name", ""),
                f"+{offset:.4f}s" if offset > 0 else "-",
                t.get("duration", ""),
                t.get("source_type", ""),
                t.get("url", ""),
            ])
            table.add_row(*row)
        console.print(table)
    else:
        print(f"\n===========================================================================================================")
        print(f" {title_str}")
        print("===========================================================================================================")
        print(f" {'#':<2} | {'STEM':<18} | {'OFFSET':<10} | {'DUR':<5} | {'TYPE':<14} | {'URL'}")
        print("-----------------------------------------------------------------------------------------------------------")
        for t in tracks:
            offset = float(t.get("start_offset", 0.0) or 0.0)
            offset_str = f"+{offset:.4f}s" if offset > 0 else "-"
            print(f" {t.get('track_number',''):<2} | {t.get('stem_name',''):<18} | {offset_str:<10} | {t.get('duration',''):<5} | {t.get('source_type',''):<14} | {t.get('url','')}")
        print("===========================================================================================================\n")


def cmd_open(args):
    """Open Audacity for a song (opens .aup4 project if present, else loads tracks in order)."""
    ctx = detect_context()
    song, song_dir = resolve_target_song(args, ctx)

    if not song_dir.exists():
        print_msg(f"[bold red]Error:[/bold red] Song directory not found: {song_dir}")
        sys.exit(1)

    force_tracks = getattr(args, "tracks", False)
    force_project = getattr(args, "project", False)

    try:
        proc = open_song_in_audacity(
            song_dir=song_dir,
            force_tracks=force_tracks,
            force_project=force_project,
            logger=print_msg,
        )
        print_msg(f"[bold green]Audacity launched for {song.title if song else song_dir.name}![/bold green]")
    except Exception as e:
        print_msg(f"[bold red]Failed to open Audacity:[/bold red] {e}")
        sys.exit(1)


def resolve_playback_audio(target: Optional[str], song_arg: Optional[str], ctx: GrooveContext) -> Tuple[Path, str, str]:
    """
    Resolve target audio file, stem name, and title from CLI arguments and context.
    Returns (audio_path, stem_name, display_title).
    """
    # 1. If target is an existing file path directly
    if target:
        p = Path(target)
        if p.is_file():
            audio_path = p.resolve()
            return audio_path, audio_path.stem, f"Groove: {audio_path.name}"

    # 2. Resolve song and song_dir
    song = None
    song_dir = None
    track_query = target

    if song_arg:
        normalized = song_arg.lower().replace(" ", "-").replace("_", "-")
        song = get_song(normalized)
        song_dir = ctx.find_song_dir(normalized)
        if not song_dir:
            artist_slug = song.artist.lower().replace(" ", "-") if song else (ctx.artist or "unknown")
            tracks_dir = ctx.tracks_dir or Path("tracks")
            song_dir = tracks_dir / artist_slug / normalized
    elif ctx.scope == Scope.SONG and ctx.song:
        song = get_song(ctx.song)
        song_dir = ctx.cwd
    else:
        # Check if target matches a known song
        if target:
            normalized = target.lower().replace(" ", "-").replace("_", "-")
            possible_song = get_song(normalized)
            possible_dir = ctx.find_song_dir(normalized)
            if possible_song or (possible_dir and possible_dir.exists()):
                song = possible_song
                song_dir = possible_dir if (possible_dir and possible_dir.exists()) else (
                    (ctx.tracks_dir or Path("tracks")) / (song.artist.lower().replace(" ", "-") if song else "unknown") / normalized
                )
                track_query = None  # target was the song; play full song / track 0
            else:
                print_msg(f"[bold red]Error:[/bold red] '{target}' does not match a known song, and no song context was detected.")
                print_msg("Usage: groove play [track] [--song SONG] (or run within a song directory)")
                sys.exit(1)
        else:
            print_msg("[bold red]Error:[/bold red] No song or track specified. Provide a song name or run from within a song directory.")
            sys.exit(1)

    if not song_dir.exists():
        print_msg(f"[bold red]Error:[/bold red] Song directory not found: {song_dir}")
        sys.exit(1)

    # 3. Locate audio files in song_dir
    audio_extensions = {".wav", ".webm", ".opus", ".mp3", ".flac", ".m4a", ".ogg"}
    audio_files = [
        f for f in sorted(song_dir.iterdir())
        if f.is_file() and f.suffix.lower() in audio_extensions
        and not f.name.startswith("temp_") and not f.name.startswith(".")
    ]

    if not audio_files:
        print_msg(f"[bold red]Error:[/bold red] No audio files found in {song_dir}")
        print_msg("Run 'groove download' or 'groove regenerate' to download audio stems.")
        sys.exit(1)

    # 4. Find matching audio file
    if not track_query:
        t0 = [f for f in audio_files if f.name.startswith("00_") or f.name.startswith("00.")]
        matched = t0[0] if t0 else audio_files[0]
    else:
        q = track_query.strip().lower()
        matched = None

        if q.isdigit():
            num = int(q)
            for f in audio_files:
                if f.name.startswith(f"{num:02d}_") or f.name.startswith(f"{num:02d}.") or f.name.startswith(f"{num}_"):
                    matched = f
                    break

        if not matched:
            for f in audio_files:
                if q in f.name.lower():
                    matched = f
                    break

        if not matched:
            csv_path = song_dir / "tracks.csv"
            if csv_path.exists():
                tracks_data = load_tracks_from_csv(csv_path)
                for t in tracks_data:
                    t_num = str(t.get("track_number", "")).strip()
                    s_name = str(t.get("stem_name", "")).strip().lower()
                    d_name = str(t.get("display_name", "")).strip().lower()
                    if q in (t_num, s_name) or q in d_name:
                        for f in audio_files:
                            if f.name.startswith(f"{t_num.zfill(2)}_") or s_name in f.name.lower():
                                matched = f
                                break
                        if matched:
                            break

        if not matched:
            print_msg(f"[bold red]Error:[/bold red] No audio file matching '{track_query}' found in {song_dir}")
            print_msg("Available audio files in this directory:")
            for f in audio_files:
                print_msg(f"  • {f.name}")
            sys.exit(1)

    stem_name = matched.stem
    song_title = song.title if song else song_dir.name
    display_title = f"{song_title} — {stem_name}"
    return matched, stem_name, display_title


def cmd_play(args):
    """Play a track or stem with live spectrum visualization and waveform tracking."""
    import time
    from .player import (
        AudioPlayerManager,
        SpectrumMode,
        extract_waveform_envelope,
        render_waveform_ascii,
        is_mpv_available,
    )

    if not is_mpv_available():
        print_msg("[bold red]Error:[/bold red] mpv player not found on system.")
        print_msg("Please install mpv: sudo apt install mpv")
        sys.exit(1)

    ctx = detect_context()
    target = getattr(args, "track", None)
    song_arg = getattr(args, "song", None)
    audio_path, stem_name, title = resolve_playback_audio(target, song_arg, ctx)

    if getattr(args, "no_spectrum", False):
        mode = SpectrumMode.NONE
    else:
        raw_mode = getattr(args, "mode", "cqt")
        try:
            mode = SpectrumMode(raw_mode.lower())
        except ValueError:
            mode = SpectrumMode.CQT

    loop = getattr(args, "loop", False)

    # Detect or extract musical key for CQT column highlighting
    musical_key = getattr(args, "key", None)
    if not musical_key:
        song_slug = song_arg or (ctx.song if ctx else None)
        if song_slug and ctx:
            s_sum = ctx.get_song_summary(song_slug)
            musical_key = s_sum.get("key", "")

    envelope = extract_waveform_envelope(audio_path, num_bars=60)
    manager = AudioPlayerManager.get_instance()
    player = manager.play(
        audio_path=audio_path,
        stem_name=stem_name,
        title=title,
        mode=mode,
        loop=loop,
        musical_key=musical_key,
    )

    wave_str, scrub_str = render_waveform_ascii(envelope, progress_ratio=0.0, width=60)
    key_hdr = f" [yellow](Key: {musical_key})[/yellow]" if musical_key else ""
    print_msg(f"\n[bold cyan]Playing:[/bold cyan] [bold white]{title}[/bold white]{key_hdr}")
    print_msg(f"[dim]File:[/dim] {audio_path}")
    print_msg(f"[dim]Visualizer Mode:[/dim] [magenta]{player.mode.value.upper()}[/magenta] ([dim]Press 'v' to cycle[/dim])")
    print_msg(f"[dim]Controls:[/dim] [yellow]Space[/yellow]=Pause/Resume  [yellow]v[/yellow]=Mode  [yellow]q[/yellow]=Quit  [yellow]←/→[/yellow]=Seek ±5s\n")
    print_msg(wave_str)
    print_msg(scrub_str)

    if not sys.stdin.isatty():
        try:
            if player.process:
                player.process.wait()
        except KeyboardInterrupt:
            manager.stop()
        return

    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        last_wave_render = 0.0

        while player.is_running():
            now = time.time()
            if now - last_wave_render >= 0.15:
                status = manager.get_status()
                pos = status["position"]
                dur = status["duration"]
                ratio = status["progress_ratio"]
                paused_str = " [yellow](PAUSED)[/yellow]" if status["paused"] else ""
                time_str = f"{int(pos//60):02d}:{int(pos%60):02d} / {int(dur//60):02d}:{int(dur%60):02d}"

                w_line, s_line = render_waveform_ascii(envelope, progress_ratio=ratio, width=60)
                if console:
                    with console.capture() as cap1:
                        console.print(f"{w_line}  {time_str}{paused_str}", end="")
                    rendered_w = cap1.get()
                    with console.capture() as cap2:
                        console.print(f"{s_line}  [magenta][{status['mode'].value.upper()}][/magenta]", end="")
                    rendered_s = cap2.get()
                else:
                    rendered_w = f"{w_line}  {time_str}{paused_str}"
                    rendered_s = f"{s_line}  [{status['mode'].value.upper()}]"

                sys.stdout.write(f"\033[2A\r\033[K{rendered_w}\n\033[K{rendered_s}\r")
                sys.stdout.flush()
                last_wave_render = now

            r, _, _ = select.select([sys.stdin], [], [], 0.05)
            if r:
                ch = sys.stdin.read(1)
                if ch == " ":
                    player.toggle_pause()
                elif ch in ("v", "V"):
                    manager.cycle_mode()
                elif ch in ("q", "Q", "\x03"):
                    break
                elif ch == "\x1b":
                    r2, _, _ = select.select([sys.stdin], [], [], 0.02)
                    if r2:
                        seq = sys.stdin.read(2)
                        if seq == "[D":
                            player.seek(-5.0)
                        elif seq == "[C":
                            player.seek(5.0)
                elif ch in ("h", "a"):
                    player.seek(-5.0)
                elif ch in ("l", "d"):
                    player.seek(5.0)

    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        manager.stop()
        print("\n\nPlayback stopped.\n")


def cmd_align(args):
    """Inspect and extract track offsets from an Audacity .aup4 project and update tracks.csv."""
    ctx = detect_context()
    song, song_dir = resolve_target_song(args, ctx)

    aup4_files = [f for f in sorted(song_dir.glob("*.aup4")) if not f.name.endswith(".aup4_")]
    if not aup4_files:
        print_msg(f"[bold red]Error:[/bold red] No .aup4 project file found in {song_dir}")
        print_msg("Run 'groove open' to load tracks, drag clips to align by ear, and save the Audacity project.")
        sys.exit(1)

    project_file = aup4_files[0]
    print_msg(f"[bold cyan]Reading project database:[/bold cyan] {project_file.name}")
    raw_offsets = extract_offsets_from_aup4(project_file)
    if not raw_offsets:
        print_msg("[bold red]No waveclip offsets found in project database.[/bold red]")
        return

    track_details = []
    for track_name, offset in sorted(raw_offsets.items()):
        candidates = list(song_dir.glob(f"{track_name}.*"))
        valid = [
            c for c in candidates
            if not c.name.startswith("temp_") and not c.name.startswith(".") and not c.name.endswith(".aup4") and not c.name.endswith(".aup4_")
        ]
        wav_file = valid[0] if valid else None
        raw_dur = get_audio_duration(wav_file) if (wav_file and wav_file.exists()) else 0.0
        end_time = offset + raw_dur if raw_dur > 0 else 0.0
        track_details.append({
            "name": track_name,
            "file": wav_file,
            "offset": offset,
            "raw_dur": raw_dur,
            "end_time": end_time,
        })

    max_end_time = max((t["end_time"] for t in track_details), default=0.0)

    if console:
        table = Table(title=f"[bold magenta]Audacity 4 Alignment & Offsets ({project_file.name})[/bold magenta]")
        table.add_column("Track", style="cyan")
        table.add_column("Start Offset", justify="right", style="yellow")
        table.add_column("Raw Duration", justify="right", style="white")
        table.add_column("End Time (Offset + Dur)", justify="right", style="green")
        table.add_column("Status", justify="center", style="dim")

        for t in track_details:
            status = "Found" if t["file"] else "Missing"
            table.add_row(
                t["name"],
                f"+{t['offset']:.4f}s" if t["offset"] > 0 else "0.0000s",
                f"{t['raw_dur']:.3f}s" if t["raw_dur"] > 0 else "-",
                f"{t['end_time']:.3f}s" if t["end_time"] > 0 else "-",
                status,
            )
        console.print(table)
        if max_end_time > 0:
            console.print(f"[bold cyan]Equalized target session duration:[/bold cyan] [bold green]{max_end_time:.3f}s[/bold green]")
    else:
        print(f"\nAudacity 4 Alignment & Offsets from {project_file.name}:")
        for t in track_details:
            print(f"  {t['name']:<24} offset=+{t['offset']:.4f}s  raw={t['raw_dur']:.3f}s  end={t['end_time']:.3f}s")
        if max_end_time > 0:
            print(f"Equalized target session duration: {max_end_time:.3f}s")

    # If --save (or default):
    if getattr(args, "save", False):
        records = load_song_tracks(song_dir)
        updated_count = 0
        for r in records:
            trk_num = int(r.get("track_number", 0))
            stem_name = r.get("stem_name", "")
            for tname, offset_val in raw_offsets.items():
                if tname.startswith(f"{trk_num:02d}_") or stem_name in tname:
                    r["start_offset"] = f"{offset_val:.6f}"
                    updated_count += 1
                    break
        save_song_tracks(song_dir, records)
        print_msg(f"\n[bold green]Success![/bold green] Saved {updated_count} track start offset(s) into tracks.csv!")

    # If --pad:
    if getattr(args, "pad", False):
        print_msg(f"\n[bold yellow]Padding track starts and equalizing duration to {max_end_time:.3f}s...[/bold yellow]")
        processed = pad_song_tracks(song_dir, raw_offsets, backup_raw=True, logger=print_msg)
        print_msg(f"[bold green]Success![/bold green] Padded and equalized {len(processed)} audio track(s) on disk!")
        print_msg(f"[dim]Original unpadded tracks preserved in {song_dir / 'raw_unpadded'}[/dim]")


def cmd_pad(args):
    """Pad start silence and equalize all track lengths on disk using captured offsets."""
    ctx = detect_context()
    song, song_dir = resolve_target_song(args, ctx)

    records = load_song_tracks(song_dir)
    offsets = {}
    for r in records:
        trk_num = int(r.get("track_number", 0))
        stem_name = r.get("stem_name", "")
        off = float(r.get("start_offset", 0.0) or 0.0)
        track_key = f"{trk_num:02d}_{stem_name}"
        offsets[track_key] = off

    if not offsets or not any(v > 0 for v in offsets.values()):
        aup4_files = [f for f in sorted(song_dir.glob("*.aup4")) if not f.name.endswith(".aup4_")]
        if aup4_files:
            offsets = extract_offsets_from_aup4(aup4_files[0])

    if not offsets:
        print_msg(f"[bold red]Error:[/bold red] No start offsets found in tracks.csv or .aup4 for {song_dir.name}.")
        print_msg("Run 'groove align' first to inspect and capture offsets.")
        sys.exit(1)

    print_msg(f"[bold cyan]Applying start offsets and equalizing durations for '{song_dir.name}'...[/bold cyan]")
    processed = pad_song_tracks(song_dir, offsets, backup_raw=True, logger=print_msg)
    print_msg(f"[bold green]Success![/bold green] Padded and equalized {len(processed)} audio track(s) on disk!")
    print_msg(f"[dim]Original unpadded tracks preserved in {song_dir / 'raw_unpadded'}[/dim]")


def cmd_regenerate(args):
    """Regenerate multitrack audio stems from tracks.csv."""
    ctx = detect_context()
    song_ids = []

    if args.song:
        song_ids = [args.song.lower().replace(" ", "-")]
    elif args.all:
        tracks = load_tracks_from_csv()
        song_ids = sorted(list({t["song_id"] for t in tracks if "song_id" in t}))
    elif ctx.scope == Scope.SONG and ctx.song:
        song_ids = [ctx.song]
    else:
        print_msg("[bold yellow]Specify a song ID, run inside a song folder, or pass --all to regenerate.[/bold yellow]")
        return

    base_dir = Path(args.output) if args.output else None
    for sid in song_ids:
        print_msg(f"\n[bold cyan]====================================================[/bold cyan]")
        print_msg(f"[bold cyan]Regenerating session for: {sid}[/bold cyan]")
        print_msg(f"[bold cyan]====================================================[/bold cyan]")
        try:
            paths = regenerate_song_from_sources(
                song_id=sid,
                base_dir=base_dir,
                audio_format=args.format,
                dry_run=args.dry_run,
                force=args.force,
                logger=print_msg,
            )
            print_msg(f"[bold green]Done![/bold green] Processed {len(paths)} track(s) for '{sid}'.")
        except Exception as e:
            print_msg(f"[bold red]Error regenerating '{sid}':[/bold red] {e}")


def cmd_download(args):
    """Download isolated audio stems for a song."""
    ctx = detect_context()
    song, song_dir = resolve_target_song(args, ctx)
    if not song:
        print_msg(f"[bold red]Error:[/bold red] Song '{args.song}' not found in catalog. Use 'groove regenerate' for custom tracks.csv songs.")
        sys.exit(1)

    base_dir = Path(args.output) if args.output else None
    audio_format = args.format.lower()

    print_msg(f"[bold cyan]Preparing download for '{song.title}' stems...[/bold cyan]")
    try:
        downloaded = download_song_stems(
            song=song,
            base_dir=base_dir,
            audio_format=audio_format,
            dry_run=args.dry_run,
            logger=print_msg,
        )
        print_msg(f"\n[bold green]Success![/bold green] Processed {len(downloaded)} stems.")
    except Exception as e:
        print_msg(f"[bold red]Download error:[/bold red] {e}")
        sys.exit(1)


def cmd_new_artist(args):
    """Create a new artist folder with an initial README.md."""
    ctx = detect_context()
    name = args.name.strip()
    slug = name.lower().replace(" ", "-")
    tracks_dir = ctx.tracks_dir or Path("tracks")
    artist_dir = tracks_dir / slug

    readme_path = create_artist_readme(artist_dir, name)
    print_msg(f"[bold green]Created artist folder:[/bold green] {artist_dir}")
    print_msg(f"[bold green]Created artist README:[/bold green] {readme_path}")


def cmd_new_album(args):
    """Create a new album folder with README.md and album.yaml."""
    ctx = detect_context()
    tracks_dir = ctx.tracks_dir or Path("tracks")

    artist_name = getattr(args, "artist", None) or ctx.artist
    if not artist_name:
        existing_artists = ctx.list_artists()
        if existing_artists:
            print_msg("[bold cyan]Existing artists:[/bold cyan]")
            for idx, a in enumerate(existing_artists, 1):
                print_msg(f"  [{idx}] {a}")
            choice = input("Select artist number or enter new artist name: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(existing_artists):
                artist_name = existing_artists[int(choice) - 1]
            else:
                artist_name = choice
        else:
            artist_name = input("Enter artist name: ").strip()

    artist_slug = artist_name.lower().replace(" ", "-")
    album_title = args.title.strip()
    album_slug = album_title.lower().replace(" ", "-").replace("'", "")
    album_dir = tracks_dir / artist_slug / album_slug

    created = create_album_scaffold(
        album_dir=album_dir,
        title=album_title,
        artist=artist_name.replace("-", " ").title(),
        year=getattr(args, "year", None),
        label=getattr(args, "label", "Tamla / Motown") or "Tamla / Motown",
    )
    print_msg(f"\n[bold green]Success![/bold green] Created album folder for '{album_title}': {album_dir}")
    for k, p in created.items():
        print_msg(f"  - [cyan]{p.name}[/cyan]")


def cmd_new_song(args):
    """Create a new song study folder with README.md, tracks.csv, and chords.csml."""
    ctx = detect_context()
    tracks_dir = ctx.tracks_dir or Path("tracks")

    # 1. Determine artist
    artist_name = getattr(args, "artist", None)
    if not artist_name:
        if ctx.artist:
            artist_name = ctx.artist
        else:
            existing_artists = ctx.list_artists()
            if existing_artists:
                print_msg("[bold cyan]Existing artists:[/bold cyan]")
                for idx, a in enumerate(existing_artists, 1):
                    print_msg(f"  [{idx}] {a}")
                choice = input("Select artist number or enter new artist name: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(existing_artists):
                    artist_name = existing_artists[int(choice) - 1]
                else:
                    artist_name = choice
            else:
                artist_name = input("Enter artist name: ").strip()

    artist_slug = artist_name.lower().replace(" ", "-")
    artist_dir = tracks_dir / artist_slug
    if not (artist_dir / "README.md").exists():
        create_artist_readme(artist_dir, artist_name)

    # 2. Determine song title
    song_title = getattr(args, "title", None)
    if not song_title:
        song_title = input("Enter song title: ").strip()

    song_slug = song_title.lower().replace(" ", "-").replace("'", "")

    # 3. Determine album and directory
    album = getattr(args, "album", "") or (ctx.album or "")
    album_slug = album.lower().replace(" ", "-") if album and album != "TBD" else ""
    if album_slug:
        album_dir = artist_dir / album_slug
        album_dir.mkdir(parents=True, exist_ok=True)
        song_dir = album_dir / song_slug
    else:
        song_dir = artist_dir / song_slug

    year = getattr(args, "year", "") or "TBD"
    key = getattr(args, "key", "") or "C"
    tempo = float(getattr(args, "tempo", 120.0) or 120.0)

    created = create_song_scaffold(
        song_dir=song_dir,
        title=song_title,
        artist=artist_name.replace("-", " ").title(),
        album=album or "TBD",
        year=year,
        tempo_bpm=tempo,
        key=key,
    )
    print_msg(f"\n[bold green]Success![/bold green] Created song study for '{song_title}': {song_dir}")
    for k, p in created.items():
        print_msg(f"  - [cyan]{p.name}[/cyan]")
    print_msg(f"\nNext steps:")
    print_msg(f"  1. Add stems with 'groove add-track <url>'")
    print_msg(f"  2. Run 'groove download' to fetch stems")
    print_msg(f"  3. Run 'groove open' to align in Audacity\n")


def cmd_add_track(args):
    """Add a track URL to tracks.csv in the song folder."""
    ctx = detect_context()
    song, song_dir = resolve_target_song(args, ctx)

    records = load_song_tracks(song_dir)
    next_num = max([int(r.get("track_number", 0)) for r in records], default=-1) + 1
    track_num = args.number if args.number is not None else next_num

    stem_name = args.stem or f"stem_{track_num}"
    display_name = args.display or stem_name.replace("_", " ").title()
    url = args.url or ""
    source_type = args.type or "stems"
    notes = args.notes or ""

    csv_path = add_track_entry(
        song_dir=song_dir,
        track_number=track_num,
        stem_name=stem_name,
        display_name=display_name,
        url=url,
        source_type=source_type,
        notes=notes,
    )
    print_msg(f"[bold green]Added Track {track_num} ({display_name}) to {csv_path.name}[/bold green]")


def cmd_slice(args):
    """Slice a deconstruction audio file into individual stem tracks based on time marks."""
    ctx = detect_context()
    song, song_dir = resolve_target_song(args, ctx)

    if not song or not song.deconstruction_slices:
        print_msg(f"Error: No deconstruction time marks configured for '{song.title if song else song_dir.name}'.")
        sys.exit(1)

    input_audio = Path(args.input) if args.input else None
    if not input_audio:
        candidates = [
            song_dir / "03_clavinet_left.wav",
            song_dir / f"{song.id}_deconstruction.wav",
            song_dir / "deconstruction.wav",
        ]
        for c in candidates:
            if c.exists():
                input_audio = c
                break

    if not input_audio or not input_audio.exists():
        print_msg(f"Error: Input audio file not found. Specify --input <path>.")
        sys.exit(1)

    out_dir = song_dir / (args.subfolder or "parsed_stems")
    print_msg(f"[bold cyan]Slicing stems from:[/bold cyan] {input_audio.name} ({input_audio.stat().st_size / (1024*1024):.1f} MB)")
    created = slice_audio_file(input_audio, song.deconstruction_slices, out_dir, logger=print_msg)
    print_msg(f"\n[bold green]Success![/bold green] Sliced {len(created)} stems into: {out_dir}")


def cmd_foundations(args):
    """Display the core principles of what makes a good groove."""
    if console:
        console.print(Markdown(GROOVE_FOUNDATIONS))
    else:
        print(GROOVE_FOUNDATIONS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="groove",
        description="Groove - Study of rhythm mechanics and isolated multitrack stem manager for rehearsal and analysis.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list
    p_list = subparsers.add_parser("list", help="List all groove studies in the catalog / current context")
    p_list.set_defaults(func=cmd_list)

    # info
    p_info = subparsers.add_parser("info", help="View song metadata and track breakdown")
    p_info.add_argument("song", nargs="?", default=None, help="Song ID slug (e.g. 'superstition', 'higher-ground')")
    p_info.set_defaults(func=cmd_info)

    # study
    p_study = subparsers.add_parser("study", help="Read groove analysis and rehearsal guide for a song")
    p_study.add_argument("song", nargs="?", default=None, help="Song ID slug (defaults to current directory)")
    p_study.set_defaults(func=cmd_study)

    # chords
    p_chords = subparsers.add_parser("chords", help="View chord progression and lyric sheet (CSML format)")
    p_chords.add_argument("song", nargs="?", default=None, help="Song ID slug (defaults to current directory)")
    p_chords.set_defaults(func=cmd_chords)

    # tracks / sources
    p_tracks = subparsers.add_parser("tracks", aliases=["sources"], help="View track source URLs and alignment offsets")
    p_tracks.add_argument("song", nargs="?", default=None, help="Optional song ID to filter tracks")
    p_tracks.set_defaults(func=cmd_tracks)

    # play
    p_play = subparsers.add_parser("play", help="Play song or stem audio with real-time spectrum visualization")
    p_play.add_argument("track", nargs="?", default=None, help="Track number, stem name, or audio file (defaults to 00_full_song)")
    p_play.add_argument("--song", "-s", default=None, help="Song ID slug (defaults to current directory)")
    p_play.add_argument("--mode", "-m", default="cqt", choices=["cqt", "waveform", "freqs", "waves", "spectrum", "none"], help="Spectrum visualizer mode (default: cqt)")
    p_play.add_argument("--key", "-k", default=None, help="Musical key of track (e.g. 'Eb minor', 'B major') for CQT guide columns")
    p_play.add_argument("--no-spectrum", action="store_true", help="Disable visualizer window (audio playback only)")
    p_play.add_argument("--loop", action="store_true", help="Loop playback indefinitely")
    p_play.set_defaults(func=cmd_play)

    # open / audacity
    p_open = subparsers.add_parser("open", aliases=["audacity"], help="Open song in Audacity 4 (.aup4 project if present, else audio tracks in order)")
    p_open.add_argument("song", nargs="?", default=None, help="Song ID slug (defaults to current directory)")
    p_open.add_argument("--tracks", "-t", action="store_true", help="Force opening audio files as separate tracks")
    p_open.add_argument("--project", "-p", action="store_true", help="Force opening .aup4 project")
    p_open.add_argument("--launch", action="store_true", default=True, help="Launch Audacity immediately")
    p_open.set_defaults(func=cmd_open)

    # align
    p_align = subparsers.add_parser("align", help="Extract clip offsets from an Audacity .aup4 project and save to tracks.csv")
    p_align.add_argument("song", nargs="?", default=None, help="Song ID slug (defaults to current directory)")
    p_align.add_argument("--save", "-s", action="store_true", default=True, help="Save extracted offsets into tracks.csv (default: True)")
    p_align.add_argument("--pad", "-p", action="store_true", help="Pad start offsets and equalize all track lengths on disk")
    p_align.set_defaults(func=cmd_align)

    # pad
    p_pad = subparsers.add_parser("pad", help="Pad start offsets and equalize track lengths to locked pocket duration")
    p_pad.add_argument("song", nargs="?", default=None, help="Song ID slug (defaults to current directory)")
    p_pad.set_defaults(func=cmd_pad)

    # regenerate
    p_regen = subparsers.add_parser("regenerate", help="Regenerate all multitrack audio files from tracks.csv")
    p_regen.add_argument("song", nargs="?", default=None, help="Song ID slug (defaults to current directory)")
    p_regen.add_argument("--all", action="store_true", help="Regenerate all songs")
    p_regen.add_argument("--format", default="webm", choices=["webm", "opus", "wav", "flac", "mp3"], help="Audio output format (default: webm)")
    p_regen.add_argument("--output", "-o", default=None, help="Base output directory (default: tracks/)")
    p_regen.add_argument("--force", "-f", action="store_true", help="Force re-download of existing files")
    p_regen.add_argument("--dry-run", action="store_true", help="Simulate download and alignment without executing commands")
    p_regen.set_defaults(func=cmd_regenerate)

    # download
    p_dl = subparsers.add_parser("download", help="Download isolated audio stems for a catalog song")
    p_dl.add_argument("song", nargs="?", default=None, help="Song ID slug")
    p_dl.add_argument("--format", default="webm", choices=["webm", "opus", "wav", "flac", "mp3"], help="Audio output format (default: webm)")
    p_dl.add_argument("--output", "-o", default=None, help="Base output directory (default: tracks/)")
    p_dl.add_argument("--dry-run", action="store_true", help="Simulate download without invoking yt-dlp")
    p_dl.set_defaults(func=cmd_download)

    # new-song / new
    p_new = subparsers.add_parser("new", aliases=["new-song"], help="Create a new song study folder with README.md, tracks.csv, chords.csml")
    p_new.add_argument("title", nargs="?", default=None, help="Song title (e.g. 'Living for the City')")
    p_new.add_argument("--artist", "-a", default=None, help="Artist name (defaults to current artist context if inside tracks/<artist>)")
    p_new.add_argument("--album", default="", help="Album title")
    p_new.add_argument("--year", default="", help="Release year")
    p_new.add_argument("--key", default="C", help="Musical key (e.g. 'Ebm', 'B')")
    p_new.add_argument("--tempo", default=120.0, type=float, help="Tempo in BPM")
    p_new.set_defaults(func=cmd_new_song)

    # new-artist
    p_nart = subparsers.add_parser("new-artist", help="Create a new artist directory with initial README.md")
    p_nart.add_argument("name", help="Artist name (e.g. 'Stevie Wonder', 'Earth Wind & Fire')")
    p_nart.set_defaults(func=cmd_new_artist)

    # add-track
    p_at = subparsers.add_parser("add-track", help="Register a track or stem URL into tracks.csv")
    p_at.add_argument("url", nargs="?", default="", help="YouTube URL or audio source URL")
    p_at.add_argument("--song", default=None, help="Song slug (defaults to current directory)")
    p_at.add_argument("--number", "-n", type=int, default=None, help="Track number (e.g. 0 for full song, 1..N for stems)")
    p_at.add_argument("--stem", default="", help="Stem identifier name (e.g. 'drums', 'moog_bass')")
    p_at.add_argument("--display", default="", help="Display name (e.g. 'Drums & Tambourine')")
    p_at.add_argument("--type", default="stems", help="Source type ('official_audio', 'stems', 'deconstruction')")
    p_at.add_argument("--notes", default="", help="Notes on this stem or arrangement")
    p_at.set_defaults(func=cmd_add_track)

    # slice
    p_slice = subparsers.add_parser("slice", help="Slice deconstruction audio into isolated stem files")
    p_slice.add_argument("song", nargs="?", default=None, help="Song ID slug (e.g. 'higher-ground')")
    p_slice.add_argument("--input", "-i", default=None, help="Path to input deconstruction audio file")
    p_slice.add_argument("--output", "-o", default=None, help="Base output directory (default: tracks/)")
    p_slice.add_argument("--subfolder", default="parsed_stems", help="Subfolder name for sliced stems")
    p_slice.set_defaults(func=cmd_slice)

    # nav / navigator
    p_nav = subparsers.add_parser("nav", aliases=["navigator", "tui"], help="Launch interactive terminal navigator (Seer style)")
    p_nav.set_defaults(func=cmd_nav)

    # new-album
    p_nalb = subparsers.add_parser("new-album", help="Create a new album directory with README.md and album.yaml")
    p_nalb.add_argument("title", help="Album title (e.g. 'Innervisions')")
    p_nalb.add_argument("--artist", "-a", default=None, help="Artist name (defaults to current artist context)")
    p_nalb.add_argument("--year", "-y", default=None, type=int, help="Release year (e.g. 1973)")
    p_nalb.add_argument("--label", default="Tamla / Motown", help="Record label")
    p_nalb.set_defaults(func=cmd_new_album)

    # foundations
    p_foundations = subparsers.add_parser("foundations", help="Read the core musicological principles of groove")
    p_foundations.set_defaults(func=cmd_foundations)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        if sys.stdin.isatty():
            cmd_nav(args)
        else:
            cmd_list(args)
        return

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()


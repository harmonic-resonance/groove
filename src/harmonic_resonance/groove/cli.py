"""
cli.py - Rich command-line interface for groove.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    console = Console()
except ImportError:
    console = None


from .catalog import CATALOG, get_song, list_songs, load_sources_from_csv, save_sources_to_csv
from .downloader import (
    download_song_stems,
    get_song_directory,
    slice_audio_file,
    regenerate_song_from_sources,
    apply_audio_offset,
)
from .audacity import (
    generate_launch_script,
    extract_offsets_from_aup4,
    calculate_relative_offsets,
    launch_audacity,
)
from .study import get_groove_study, GROOVE_FOUNDATIONS


def print_msg(msg: str):
    if console:
        console.print(msg)
    else:
        # Strip rich tags if rich not present
        import re
        clean = re.sub(r"\[.*?\]", "", msg)
        print(clean)


def cmd_list(args):
    """List all available groove studies in the catalog."""
    songs = list_songs()
    if console:
        table = Table(title="[bold magenta]Groove Catalog - Master Rhythm Studies[/bold magenta]")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="bold white")
        table.add_column("Artist", style="green")
        table.add_column("Album (Year)", style="dim")
        table.add_column("Tempo", justify="right", style="yellow")
        table.add_column("Key", style="blue")
        table.add_column("Stems", justify="center", style="magenta")

        for song in songs:
            table.add_row(
                song.id,
                song.title,
                song.artist,
                f"{song.album} ({song.year})",
                f"{song.tempo_bpm:.0f} BPM",
                song.key,
                str(len(song.stems)),
            )
        console.print(table)
    else:
        print("\n==========================================================================================")
        print(" GROOVE CATALOG - Master Rhythm Studies")
        print("==========================================================================================")
        print(f" {'ID':<20} | {'TITLE':<20} | {'TEMPO':<8} | {'KEY':<12} | {'STEMS':<5}")
        print("------------------------------------------------------------------------------------------")
        for song in songs:
            print(f" {song.id:<20} | {song.title:<20} | {song.tempo_bpm:>5.0f} BPM | {song.key:<12} | {len(song.stems):^5}")
        print("==========================================================================================\n")
        print("Run 'groove info <id>' or 'groove study <id>' for full pocket breakdowns.\n")


def cmd_info(args):
    """Show details and stem breakdown for a song."""
    song = get_song(args.song)
    if not song:
        print_msg(f"Error: Song '{args.song}' not found. Run 'groove list' to see available songs.")
        sys.exit(1)

    if console:
        panel_content = (
            f"[bold white]{song.title}[/bold white] by [green]{song.artist}[/green]\n"
            f"[dim]Album:[/dim] {song.album} ({song.year}) | [dim]Tempo:[/dim] [yellow]{song.tempo_bpm} BPM[/yellow] | [dim]Key:[/dim] [blue]{song.key}[/blue] | [dim]Meter:[/dim] {song.time_signature}"
        )
        console.print(Panel(panel_content, title=f"Song Info: {song.id}", border_style="cyan"))

        table = Table(title=f"Isolated Stems for '{song.title}'")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Stem Name", style="bold cyan")
        table.add_column("Display Name", style="white")
        table.add_column("Description", style="dim")
        table.add_column("Pan", justify="center", style="yellow")

        for idx, stem in enumerate(song.stems, start=1):
            pan_str = f"{stem.pan:+.1f}" if stem.pan != 0 else "C"
            table.add_row(str(idx), stem.name, stem.display_name, stem.description, pan_str)

        console.print(table)
        print_msg(f"\n[bold green]To download stems:[/bold green] groove download {song.id}")
        print_msg(f"[bold green]To generate Audacity multitrack session:[/bold green] groove audacity {song.id} --launch")
        print_msg(f"[bold green]To read pocket study:[/bold green] groove study {song.id}\n")
    else:
        print("\n" + "=" * 70)
        print(f" SONG: {song.title.upper()} - {song.artist}")
        print(f" Album: {song.album} ({song.year}) | Tempo: {song.tempo_bpm} BPM | Key: {song.key} | Meter: {song.time_signature}")
        print("=" * 70)
        print(" ISOLATED STEMS:")
        print("-" * 70)
        for idx, stem in enumerate(song.stems, start=1):
            pan_str = f"pan={stem.pan:+.1f}" if stem.pan != 0 else "center"
            print(f"  [{idx}] {stem.display_name} ({pan_str})")
            print(f"      Role: {stem.description}")
        print("-" * 70)
        print(f" Download stems:     groove download {song.id}")
        print(f" Audacity session:   groove audacity {song.id} --launch")
        print(f" Pocket study:       groove study {song.id}\n")


def cmd_study(args):
    """Display in-depth groove analysis and rehearsal tips."""
    song = get_song(args.song)
    if not song:
        print_msg(f"[bold red]Error:[/bold red] Song '{args.song}' not found.")
        sys.exit(1)

    study_text = get_groove_study(song.id)
    if console:
        console.print(Markdown(study_text))
    else:
        print(study_text)


def cmd_foundations(args):
    """Display the core principles of what makes a good groove."""
    if console:
        console.print(Markdown(GROOVE_FOUNDATIONS))
    else:
        print(GROOVE_FOUNDATIONS)


def cmd_download(args):
    """Download isolated audio stems for a song."""
    song = get_song(args.song)
    if not song:
        print_msg(f"[bold red]Error:[/bold red] Song '{args.song}' not found.")
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
        launch_script = generate_launch_script(song, base_dir=base_dir)
        print_msg(f"[bold green]Audacity launcher generated:[/bold green] {launch_script}")
    except Exception as e:
        print_msg(f"[bold red]Download error:[/bold red] {e}")
        sys.exit(1)


def cmd_slice(args):
    """Slice a deconstruction audio file into individual stem tracks based on time marks."""
    song = get_song(args.song)
    if not song:
        print_msg(f"Error: Song '{args.song}' not found.")
        sys.exit(1)

    if not song.deconstruction_slices:
        print_msg(f"Error: No deconstruction time marks configured for '{song.title}'.")
        sys.exit(1)

    base_dir = Path(args.output) if args.output else None
    song_dir = get_song_directory(song, base_dir)

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


def cmd_audacity(args):
    """Generate Audacity 4 launch script and optionally launch Audacity with tracks in order."""
    song = get_song(args.song)
    if not song:
        print_msg(f"[bold red]Error:[/bold red] Song '{args.song}' not found.")
        sys.exit(1)

    base_dir = Path(args.output) if args.output else None
    song_dir = get_song_directory(song, base_dir)

    # Check if user passed an explicit .aup4 project or parsed stems
    parsed_dir = song_dir / "parsed_stems"
    aup4_files = list(song_dir.glob("*.aup4")) + list(song_dir.glob("*.aup4.aup4"))

    launch_script = generate_launch_script(song, base_dir=base_dir)
    print_msg(f"[bold green]Generated Audacity multitrack launch script:[/bold green]")
    print_msg(f"  [cyan]{launch_script.resolve()}[/cyan]")
    if aup4_files:
        print_msg(f"[dim]Existing .aup4 project found: {aup4_files[0].resolve()}[/dim]")

    if args.launch:
        # Collect track files in order (full song first, then stems)
        tracks_to_open = []
        if parsed_dir.exists() and list(parsed_dir.glob("*.wav")):
            tracks_to_open = sorted(parsed_dir.glob("*.wav"))
        elif list(song_dir.glob("*.wav")):
            tracks_to_open = sorted(song_dir.glob("*.wav"))

        print_msg(f"[bold yellow]Launching Audacity with tracks in order...[/bold yellow]")
        try:
            if args.original:
                orig_candidates = [
                    song_dir / f"{song.id}_original.wav",
                    song_dir / "higher_ground_original.wav",
                    song_dir / "original.wav",
                ]
                orig_file = next((f for f in orig_candidates if f.exists()), None)
                if not orig_file:
                    print_msg(f"[bold red]Original audio file not found in {song_dir}[/bold red]")
                    sys.exit(1)
                print_msg(f"[cyan]Opening original track:[/cyan] {orig_file.name}")
                launch_audacity(files=[orig_file])
            elif args.use_project and aup4_files:
                print_msg(f"[cyan]Opening existing project: {aup4_files[0].name}[/cyan]")
                launch_audacity(target=aup4_files[0])
            elif tracks_to_open:
                print_msg(f"[cyan]Opening {len(tracks_to_open)} track(s) in order on the command line:[/cyan]")
                for idx, t in enumerate(tracks_to_open, 1):
                    print_msg(f"  [{idx}] {t.name}")
                launch_audacity(files=tracks_to_open)
            else:
                print_msg(f"[bold yellow]No audio tracks found to launch in {song_dir}.[/bold yellow]")
            print_msg(f"[bold green]Audacity launched![/bold green]")
        except Exception as e:
            print_msg(f"[bold red]Failed to launch Audacity:[/bold red] {e}")


def cmd_sources(args):
    """List or inspect track source URLs from sources.csv."""
    sources = load_sources_from_csv(getattr(args, "csv", None))
    if not sources:
        print_msg("[bold red]No sources found in sources.csv[/bold red]")
        return

    filter_song = args.song.lower() if getattr(args, "song", None) else None
    if filter_song:
        sources = [
            s for s in sources
            if filter_song in s.get("song_id", "").lower() or filter_song in s.get("title", "").lower()
        ]
        if not sources:
            print_msg(f"[bold yellow]No sources found matching '{args.song}'.[/bold yellow]")
            return

    if console:
        table = Table(title="[bold magenta]Groove Audio Sources (YouTube Stems & References)[/bold magenta]")
        table.add_column("Song ID", style="cyan", no_wrap=True)
        table.add_column("#", justify="right", style="yellow")
        table.add_column("Stem Name", style="bold green")
        table.add_column("Display Name", style="white")
        table.add_column("Trim", justify="right", style="dim cyan")
        table.add_column("Pad", justify="right", style="dim blue")
        table.add_column("Dur", justify="center", style="dim")
        table.add_column("Type", style="magenta")
        table.add_column("URL", style="blue")

        for s in sources:
            trim_val = float(s.get("lead_in_trim", 0.0) or 0.0)
            pad_val = float(s.get("pad_delay", 0.0) or 0.0)
            table.add_row(
                s.get("song_id", ""),
                s.get("track_number", ""),
                s.get("stem_name", ""),
                s.get("display_name", ""),
                f"{trim_val:.4f}s" if trim_val > 0 else "-",
                f"{pad_val:.4f}s" if pad_val > 0 else "-",
                s.get("duration", ""),
                s.get("source_type", ""),
                s.get("url", ""),
            )
        console.print(table)
    else:
        print("\n===========================================================================================================")
        print(" GROOVE AUDIO SOURCES (sources.csv)")
        print("===========================================================================================================")
        print(f" {'SONG':<15} | {'#':<2} | {'STEM':<18} | {'TRIM':<8} | {'PAD':<8} | {'DUR':<5} | {'TYPE':<14} | {'URL'}")
        print("-----------------------------------------------------------------------------------------------------------")
        for s in sources:
            trim_val = float(s.get("lead_in_trim", 0.0) or 0.0)
            pad_val = float(s.get("pad_delay", 0.0) or 0.0)
            trim_str = f"{trim_val:.3f}s" if trim_val > 0 else "-"
            pad_str = f"{pad_val:.3f}s" if pad_val > 0 else "-"
            print(f" {s.get('song_id',''):<15} | {s.get('track_number',''):<2} | {s.get('stem_name',''):<18} | {trim_str:<8} | {pad_str:<8} | {s.get('duration',''):<5} | {s.get('source_type',''):<14} | {s.get('url','')}")
        print("===========================================================================================================\n")


def cmd_regenerate(args):
    """Regenerate multitrack audio stems and launch script from sources.csv."""
    song_ids = []
    if args.song:
        song_ids = [args.song.lower()]
    elif args.all:
        sources = load_sources_from_csv(getattr(args, "csv", None))
        song_ids = sorted(list({s["song_id"] for s in sources}))
    else:
        print_msg("[bold yellow]Specify a song ID or --all to regenerate all songs.[/bold yellow]")
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


def cmd_align(args):
    """Inspect and extract track offsets from an Audacity .aup4 project and update sources.csv."""
    song = get_song(args.song)
    base_dir = Path(args.output) if args.output else None
    song_dir = get_song_directory(song, base_dir) if song else Path("tracks") / "stevie-wonder" / args.song

    aup4_files = list(song_dir.glob("*.aup4"))
    if not aup4_files:
        print_msg(f"[bold red]Error:[/bold red] No .aup4 project file found in {song_dir}")
        sys.exit(1)

    project_file = aup4_files[0]
    print_msg(f"[bold cyan]Reading project database:[/bold cyan] {project_file.name}")
    raw_offsets = extract_offsets_from_aup4(project_file)
    if not raw_offsets:
        print_msg("[bold red]No waveclip offsets found in project database.[/bold red]")
        return

    relative = calculate_relative_offsets(raw_offsets, ref_key="00_full_song")

    if console:
        table = Table(title=f"[bold magenta]Extracted Project Offsets ({project_file.name})[/bold magenta]")
        table.add_column("Track", style="cyan")
        table.add_column("Timeline Offset", justify="right", style="yellow")
        table.add_column("Rel to Full Song", justify="right", style="magenta")
        table.add_column("Lead-in Trim", justify="right", style="green")
        table.add_column("Pad Delay", justify="right", style="blue")

        for track_name, offset in sorted(raw_offsets.items()):
            rel_info = relative.get(track_name, {})
            trim = rel_info.get("lead_in_trim", 0.0)
            pad = rel_info.get("pad_delay", 0.0)
            delta = rel_info.get("delta", 0.0)
            table.add_row(
                track_name,
                f"{offset:.4f}s",
                f"{delta:+.4f}s",
                f"{trim:.4f}s" if trim > 0 else "-",
                f"{pad:.4f}s" if pad > 0 else "-",
            )
        console.print(table)
    else:
        print(f"\nExtracted Offsets from {project_file.name}:")
        for track_name, offset in sorted(raw_offsets.items()):
            rel_info = relative.get(track_name, {})
            print(f"  {track_name:<24} offset={offset:.4f}s (rel={rel_info.get('delta',0.0):+.4f}s, trim={rel_info.get('lead_in_trim',0.0):.4f}s, pad={rel_info.get('pad_delay',0.0):.4f}s)")

    if getattr(args, "save", False):
        sources = load_sources_from_csv(getattr(args, "csv", None))
        updated_count = 0
        for s in sources:
            if s.get("song_id", "").lower() == args.song.lower():
                trk_num = int(s.get("track_number", 0))
                stem_name = s.get("stem_name", "")
                for tname, rel_info in relative.items():
                    if tname.startswith(f"{trk_num:02d}_") or stem_name in tname:
                        s["lead_in_trim"] = f"{rel_info['lead_in_trim']:.6f}"
                        s["pad_delay"] = f"{rel_info['pad_delay']:.6f}"
                        updated_count += 1
                        break
        save_sources_to_csv(sources, getattr(args, "csv", None))
        print_msg(f"\n[bold green]Success![/bold green] Saved {updated_count} track offset(s) into sources.csv!")



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="groove",
        description="Groove - Study of rhythm mechanics and isolated multitrack stem manager for rehearsal and analysis.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # sources
    p_sources = subparsers.add_parser("sources", help="View or search source URLs recorded in sources.csv")
    p_sources.add_argument("song", nargs="?", default=None, help="Optional song ID to filter sources")
    p_sources.add_argument("--csv", default=None, help="Path to custom sources.csv file")
    p_sources.set_defaults(func=cmd_sources)

    # list
    p_list = subparsers.add_parser("list", help="List all groove studies in the catalog")
    p_list.set_defaults(func=cmd_list)

    # info
    p_info = subparsers.add_parser("info", help="View song metadata and stem breakdown")
    p_info.add_argument("song", help="Song ID slug (e.g. 'superstition', 'higher-ground')")
    p_info.set_defaults(func=cmd_info)

    # study
    p_study = subparsers.add_parser("study", help="Read groove analysis and rehearsal guide for a song")
    p_study.add_argument("song", help="Song ID slug (e.g. 'superstition', 'sir-duke')")
    p_study.set_defaults(func=cmd_study)

    # foundations
    p_foundations = subparsers.add_parser("foundations", help="Read the core musicological principles of groove")
    p_foundations.set_defaults(func=cmd_foundations)

    # download
    p_dl = subparsers.add_parser("download", help="Download isolated audio stems for a song")
    p_dl.add_argument("song", help="Song ID slug")
    p_dl.add_argument("--format", default="wav", choices=["wav", "flac", "mp3"], help="Audio output format (default: wav)")
    p_dl.add_argument("--output", "-o", default=None, help="Base output directory (default: tracks/)")
    p_dl.add_argument("--dry-run", action="store_true", help="Simulate download without invoking yt-dlp")
    p_dl.set_defaults(func=cmd_download)

    # slice
    p_slice = subparsers.add_parser("slice", help="Slice deconstruction audio into isolated stem files")
    p_slice.add_argument("song", help="Song ID slug (e.g. 'higher-ground')")
    p_slice.add_argument("--input", "-i", default=None, help="Path to input deconstruction audio file")
    p_slice.add_argument("--output", "-o", default=None, help="Base output directory (default: tracks/)")
    p_slice.add_argument("--subfolder", default="parsed_stems", help="Subfolder name for sliced stems")
    p_slice.set_defaults(func=cmd_slice)

    # regenerate
    p_regen = subparsers.add_parser("regenerate", help="Regenerate all multitrack audio files and launch.sh from sources.csv")
    p_regen.add_argument("song", nargs="?", default=None, help="Song ID slug (e.g. 'higher-ground', 'superstition')")
    p_regen.add_argument("--all", action="store_true", help="Regenerate all songs in sources.csv")
    p_regen.add_argument("--format", default="wav", choices=["wav", "flac", "mp3"], help="Audio output format (default: wav)")
    p_regen.add_argument("--output", "-o", default=None, help="Base output directory (default: tracks/)")
    p_regen.add_argument("--force", "-f", action="store_true", help="Force re-download/re-processing of existing files")
    p_regen.add_argument("--dry-run", action="store_true", help="Simulate download and alignment without executing commands")
    p_regen.add_argument("--csv", default=None, help="Path to custom sources.csv file")
    p_regen.set_defaults(func=cmd_regenerate)

    # align
    p_align = subparsers.add_parser("align", help="Extract clip offsets from an Audacity .aup4 project and save to sources.csv")
    p_align.add_argument("song", help="Song ID slug (e.g. 'higher-ground')")
    p_align.add_argument("--output", "-o", default=None, help="Base output directory (default: tracks/)")
    p_align.add_argument("--save", "-s", action="store_true", help="Save extracted offsets into sources.csv")
    p_align.add_argument("--csv", default=None, help="Path to custom sources.csv file")
    p_align.set_defaults(func=cmd_align)

    # audacity
    p_aud = subparsers.add_parser("audacity", help="Generate an Audacity multitrack launch script (launch.sh)")
    p_aud.add_argument("song", help="Song ID slug")
    p_aud.add_argument("--format", default="wav", choices=["wav", "flac", "mp3"], help="Audio format (default: wav)")
    p_aud.add_argument("--output", "-o", default=None, help="Base output directory (default: tracks/)")
    p_aud.add_argument("--launch", action="store_true", help="Launch Audacity immediately with the generated session")
    p_aud.add_argument("--original", action="store_true", help="Launch Audacity loading the full original track for AI separation")
    p_aud.add_argument("--use-parsed", action="store_true", help="Launch Audacity with sliced/parsed stems directly as separate tracks")
    p_aud.add_argument("--use-project", action="store_true", help="Launch Audacity opening the existing .aup4 project")
    p_aud.set_defaults(func=cmd_audacity)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        # Default to listing catalog
        cmd_list(args)
        return

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

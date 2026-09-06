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


from .catalog import CATALOG, get_song, list_songs
from .downloader import download_song_stems, get_song_directory, slice_audio_file
from .audacity import generate_audacity_lof, launch_audacity
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
        lof_path = generate_audacity_lof(song, base_dir=base_dir, audio_format=audio_format)
        print_msg(f"[bold green]Audacity session generated:[/bold green] {lof_path}")
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

    # Generate LOF file for the parsed stems
    lof_path = out_dir / f"{song.id}-stems.lof"
    lof_lines = [
        f"# Audacity Multitrack Session: {song.title} (Parsed Stems)",
        f"# Artist: {song.artist} ({song.year})",
        "window offset 0",
    ]
    for c in created:
        lof_lines.append(f'file "{c.name}"')
    lof_path.write_text("\n".join(lof_lines), encoding="utf-8")

    print_msg(f"\n[bold green]Success![/bold green] Sliced {len(created)} stems into: {out_dir}")
    print_msg(f"[bold green]LOF session created:[/bold green] {lof_path}")


def cmd_audacity(args):
    """Generate Audacity .lof session and optionally launch Audacity."""
    song = get_song(args.song)
    if not song:
        print_msg(f"[bold red]Error:[/bold red] Song '{args.song}' not found.")
        sys.exit(1)

    base_dir = Path(args.output) if args.output else None
    song_dir = get_song_directory(song, base_dir)
    audio_format = args.format.lower()

    # Check if user passed an explicit .aup4 project or parsed stems
    parsed_dir = song_dir / "parsed_stems"
    aup4_files = list(song_dir.glob("*.aup4")) + list(song_dir.glob("*.aup4.aup4"))

    lof_path = generate_audacity_lof(song, base_dir=base_dir, audio_format=audio_format)
    print_msg(f"[bold green]Generated Audacity multitrack session script:[/bold green]")
    print_msg(f"  [cyan]{lof_path.resolve()}[/cyan]")
    if aup4_files:
        print_msg(f"[dim]Existing .aup4 project found: {aup4_files[0].resolve()}[/dim]")

    if args.launch:
        # Determine launch target: if parsed stems exist, pass them
        parsed_wavs = sorted(parsed_dir.glob("*.wav")) if parsed_dir.exists() else []
        print_msg(f"[bold yellow]Launching Audacity with multitrack session...[/bold yellow]")
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
                print_msg(f"[cyan]Opening original track for stem separation:[/cyan] {orig_file.name}")
                launch_audacity(files=[orig_file])
            elif parsed_wavs and args.use_parsed:
                print_msg(f"[cyan]Importing {len(parsed_wavs)} parsed track(s) from command line into Audacity:[/cyan]")
                for pw in parsed_wavs:
                    print_msg(f"  - {pw.name}")
                launch_audacity(files=parsed_wavs)
            elif aup4_files and args.use_project:
                print_msg(f"[cyan]Opening existing project: {aup4_files[0].name}[/cyan]")
                launch_audacity(target=aup4_files[0])
            else:
                launch_audacity(target=lof_path)
            print_msg(f"[bold green]Audacity launched![/bold green]")
        except Exception as e:
            print_msg(f"[bold red]Failed to launch Audacity:[/bold red] {e}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="groove",
        description="Groove - Study of rhythm mechanics and isolated multitrack stem manager for rehearsal and analysis.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

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

    # audacity
    p_aud = subparsers.add_parser("audacity", help="Generate an Audacity multitrack session file (.lof)")
    p_aud.add_argument("song", help="Song ID slug")
    p_aud.add_argument("--format", default="wav", choices=["wav", "flac", "mp3"], help="Audio format expected in LOF (default: wav)")
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

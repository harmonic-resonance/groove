#!/usr/bin/env python3
"""
scripts/inspect_stems_video.py - Inspect a YouTube video for isolated track stems and chapter markers.

Usage:
    python scripts/inspect_stems_video.py <youtube_url>
    python scripts/inspect_stems_video.py <youtube_url> --json
    python scripts/inspect_stems_video.py <youtube_url> --description
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add src to path so script runs directly without needing pip install
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

try:
    from harmonic_resonance.groove.stems_video import (
        inspect_stems_video,
        slice_stems_video,
        format_stems_inspection_report,
    )
except ImportError as e:
    print(f"Error: Could not import harmonic_resonance.groove.stems_video: {e}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Inspect YouTube video containing isolated stems and extract chapter markers / timestamps."
    )
    parser.add_argument("url", help="YouTube video URL or Video ID")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    parser.add_argument("--description", "-d", action="store_true", help="Print raw video description")
    parser.add_argument("--slice-to", "-s", default=None, help="Directory to slice stems into and update tracks.csv")
    parser.add_argument("--format", "-f", default="webm", choices=["webm", "wav", "opus"], help="Output audio format (default: webm)")
    parser.add_argument("--no-csv", action="store_true", help="Do not update tracks.csv when slicing")
    args = parser.parse_args()

    try:
        info = inspect_stems_video(args.url)
    except Exception as e:
        print(f"Error inspecting video: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(info, indent=2))
        return

    # Try rich formatting if available
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel

        console = Console()
        panel_content = (
            f"[bold cyan]Title:[/bold cyan] {info['title']}\n"
            f"[bold cyan]URL:[/bold cyan] {info['url']} ([green]{info['video_id']}[/green])\n"
            f"[bold cyan]Duration:[/bold cyan] {info['duration_formatted']} ({info['duration']:.1f}s)\n"
            f"[bold cyan]Uploader:[/bold cyan] {info['uploader']}\n"
            f"[bold cyan]Chapters / Stems Found:[/bold cyan] [bold yellow]{info['chapter_count']}[/bold yellow]"
        )
        console.print(Panel(panel_content, title="[bold magenta]Isolated Stems Video Inspection[/bold magenta]"))

        if info["chapters"]:
            table = Table(title="Detected Stem Chapters / Markers")
            table.add_column("#", justify="right", style="cyan", no_wrap=True)
            table.add_column("Stem Name / Chapter", style="green")
            table.add_column("Slug", style="dim")
            table.add_column("Start", justify="right", style="yellow")
            table.add_column("End", justify="right", style="yellow")
            table.add_column("Duration", justify="right", style="magenta")
            table.add_column("Source", style="blue")

            for ch in info["chapters"]:
                table.add_row(
                    f"{ch['index']:02d}",
                    ch["title"],
                    ch["slug"],
                    ch["start_formatted"],
                    ch["end_formatted"],
                    ch["duration_formatted"],
                    ch.get("source", "chapters"),
                )
            console.print(table)
        else:
            console.print("[yellow]No chapters or description timestamps detected in this video.[/yellow]")

        if args.description and info.get("description"):
            console.print("\n[bold]Raw Description:[/bold]")
            console.print(info["description"])

    except ImportError:
        # Fallback to plain markdown output
        print(format_stems_inspection_report(info))
        if args.description and info.get("description"):
            print("\n--- Raw Description ---")
            print(info["description"])

    if args.slice_to:
        out_dir = Path(args.slice_to).resolve()
        print(f"\nSlicing {len(info['chapters'])} stems into {out_dir}...")
        try:
            from rich.console import Console
            logger = Console().print
        except ImportError:
            logger = print

        slice_stems_video(
            url_or_id=args.url,
            output_dir=out_dir,
            audio_format=args.format,
            update_tracks_csv=not args.no_csv,
            logger=logger,
        )


if __name__ == "__main__":
    main()

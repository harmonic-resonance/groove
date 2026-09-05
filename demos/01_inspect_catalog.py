#!/usr/bin/env python3
"""
01_inspect_catalog.py - Inspect the groove catalog programmatically.
"""

import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from harmonic_resonance.groove.catalog import list_songs, get_song


def main():
    print("=== GROOVE CATALOG DEMO ===\n")
    songs = list_songs()
    print(f"Total songs in catalog: {len(songs)}\n")

    for song in songs:
        print(f"Song: {song.title} ({song.year}) - {song.artist}")
        print(f"  Album: {song.album}")
        print(f"  Tempo: {song.tempo_bpm} BPM | Key: {song.key} | Meter: {song.time_signature}")
        print(f"  Available Stems ({len(song.stems)}):")
        for stem in song.stems:
            pan_str = f"pan={stem.pan:+.1f}" if stem.pan != 0 else "center"
            print(f"    - [{stem.name}] {stem.display_name} ({pan_str})")
        print()

    # Detail on Superstition
    superstition = get_song("superstition")
    if superstition:
        print(f"--- Pocket Breakdown for '{superstition.title}' ---")
        print(superstition.analysis.pocket_description)
        print("\n--- Rehearsal Tips ---")
        for tip in superstition.analysis.rehearsal_tips:
            print(f" * {tip}")


if __name__ == "__main__":
    main()

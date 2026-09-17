#!/usr/bin/env python3
"""
02_generate_audacity_session.py - Generate Audacity 4 multitrack launch scripts programmatically.
"""

import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from harmonic_resonance.groove.catalog import get_song
from harmonic_resonance.groove.audacity import generate_launch_script


def main():
    print("=== AUDACITY 4 MULTITRACK LAUNCH SCRIPT GENERATOR DEMO ===\n")
    
    songs_to_generate = ["superstition", "higher-ground", "sir-duke"]
    
    for song_id in songs_to_generate:
        song = get_song(song_id)
        if not song:
            continue
            
        print(f"Generating Audacity 4 launch script for '{song.title}'...")
        script_path = generate_launch_script(song)
        print(f"  -> File created: {script_path}")
        print("  -> Script Preview:")
        content = script_path.read_text().splitlines()
        for line in content[:14]:
            print(f"     {line}")
        print("     ...\n")

    print("Done! You can run ./launch.sh in any song directory to open all tracks in order in Audacity 4.")


if __name__ == "__main__":
    main()

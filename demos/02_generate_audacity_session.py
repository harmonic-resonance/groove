#!/usr/bin/env python3
"""
02_generate_audacity_session.py - Generate Audacity multitrack LOF sessions programmatically.
"""

import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from harmonic_resonance.groove.catalog import get_song
from harmonic_resonance.groove.audacity import generate_audacity_lof


def main():
    print("=== AUDACITY MULTITRACK SESSION GENERATOR DEMO ===\n")
    
    songs_to_generate = ["superstition", "higher-ground", "sir-duke"]
    
    for song_id in songs_to_generate:
        song = get_song(song_id)
        if not song:
            continue
            
        print(f"Generating Audacity LOF session for '{song.title}'...")
        lof_path = generate_audacity_lof(song, audio_format="wav")
        print(f"  -> File created: {lof_path}")
        print("  -> Session Content Preview:")
        content = lof_path.read_text().splitlines()
        for line in content[:16]:
            print(f"     {line}")
        print("     ...\n")

    print("Done! You can open any generated .lof file directly in Audacity.")


if __name__ == "__main__":
    main()

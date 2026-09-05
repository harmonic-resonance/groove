"""
test_downloader.py - Unit tests for downloader logic.
"""

import tempfile
import unittest
from pathlib import Path

from harmonic_resonance.groove.catalog import get_song, Stem
from harmonic_resonance.groove.downloader import (
    build_yt_dlp_command,
    get_stem_filename,
    download_song_stems,
)


class TestDownloader(unittest.TestCase):
    def test_build_yt_dlp_command_with_url(self):
        url = "https://www.youtube.com/watch?v=12345"
        cmd = build_yt_dlp_command(url, "out.%(ext)s", audio_format="wav")
        self.assertIn("yt-dlp", cmd)
        self.assertIn("--extract-audio", cmd)
        self.assertIn("--audio-format", cmd)
        self.assertIn("wav", cmd)
        self.assertIn(url, cmd)

    def test_build_yt_dlp_command_with_query(self):
        query = "Stevie Wonder Superstition isolated drums"
        cmd = build_yt_dlp_command(query, "out.%(ext)s", audio_format="flac")
        self.assertIn(f"ytsearch1:{query}", cmd)
        self.assertIn("flac", cmd)

    def test_get_stem_filename(self):
        stem = Stem(name="moog-bass", display_name="Moog Bass", description="Bass")
        filename = get_stem_filename(2, stem, "wav")
        self.assertEqual(filename, "02_moog_bass.wav")

    def test_download_song_stems_dry_run(self):
        temp_dir = tempfile.TemporaryDirectory()
        base_dir = Path(temp_dir.name)
        try:
            song = get_song("superstition")
            self.assertIsNotNone(song)

            paths = download_song_stems(song, base_dir=base_dir, audio_format="wav", dry_run=True)
            self.assertEqual(len(paths), len(song.stems))
            self.assertEqual(paths[0].name, "01_drums.wav")
        finally:
            temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()

"""
test_catalog.py - Unit tests for the groove catalog.
"""

import unittest
from harmonic_resonance.groove.catalog import CATALOG, get_song, list_songs


class TestCatalog(unittest.TestCase):
    def test_list_songs(self):
        songs = list_songs()
        self.assertGreaterEqual(len(songs), 6)
        song_ids = [s.id for s in songs]
        self.assertIn("superstition", song_ids)
        self.assertIn("higher-ground", song_ids)
        self.assertIn("sir-duke", song_ids)
        self.assertIn("i-wish", song_ids)
        self.assertIn("living-for-the-city", song_ids)
        self.assertIn("isnt-she-lovely", song_ids)

    def test_get_song_case_insensitivity(self):
        song1 = get_song("superstition")
        song2 = get_song("Superstition")
        song3 = get_song("SUPERSTITION")
        self.assertIsNotNone(song1)
        self.assertEqual(song1, song2)
        self.assertEqual(song1, song3)

    def test_superstition_stems_and_analysis(self):
        song = get_song("superstition")
        self.assertIsNotNone(song)
        self.assertEqual(song.artist, "Stevie Wonder")
        self.assertEqual(song.tempo_bpm, 100.0)
        self.assertEqual(song.key, "E♭ minor")
        
        stem_names = [s.name for s in song.stems]
        self.assertIn("drums", stem_names)
        self.assertIn("bass", stem_names)
        self.assertIn("clavinet1", stem_names)
        self.assertIn("clavinet2", stem_names)
        self.assertIn("horns", stem_names)
        self.assertIn("vocals", stem_names)

        self.assertTrue(len(song.analysis.pocket_description) > 0)
        self.assertTrue(len(song.analysis.rehearsal_tips) >= 3)

    def test_higher_ground_stems(self):
        song = get_song("higher-ground")
        self.assertIsNotNone(song)
        self.assertEqual(song.tempo_bpm, 125.0)
        stem_names = [s.name for s in song.stems]
        self.assertIn("drums_tambourine", stem_names)
        self.assertIn("moog_bass", stem_names)
        self.assertIn("clavinets", stem_names)
        self.assertIn("vocals", stem_names)


if __name__ == "__main__":
    unittest.main()

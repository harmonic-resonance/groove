"""
test_catalog.py - Unit tests for the groove catalog.
"""

import unittest
from harmonic_resonance.groove.catalog import CATALOG, get_song, list_songs, load_sources_from_csv


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

    def test_load_sources_from_csv(self):
        sources = load_sources_from_csv()
        self.assertGreater(len(sources), 0)
        song_ids = {s["song_id"] for s in sources}
        self.assertIn("higher-ground", song_ids)
        self.assertIn("superstition", song_ids)
        self.assertIn("sir-duke", song_ids)
        self.assertIn("i-wish", song_ids)

        for s in sources:
            self.assertIn("song_id", s)
            self.assertIn("track_number", s)
            self.assertIn("stem_name", s)
            self.assertIn("url", s)
            self.assertTrue(s["url"].startswith("https://"))

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

    def test_list_albums(self):
        from harmonic_resonance.groove.catalog import list_albums, get_album
        albums = list_albums()
        self.assertGreaterEqual(len(albums), 3)
        album_ids = [a.id for a in albums]
        self.assertIn("talking-book", album_ids)
        self.assertIn("innervisions", album_ids)
        self.assertIn("songs-in-the-key-of-life", album_ids)

    def test_get_album_attributes(self):
        from harmonic_resonance.groove.catalog import get_album
        album = get_album("Innervisions")
        self.assertIsNotNone(album)
        self.assertEqual(album.artist, "Stevie Wonder")
        self.assertEqual(album.year, 1973)
        self.assertTrue(any("Malcolm Cecil" in p for p in album.producers))
        self.assertTrue(any("Robert Margouleff" in p for p in album.producers))
        self.assertTrue(any("Record Plant" in s for s in album.studios))
        self.assertTrue(any("TONTO" in g for g in album.key_gear))

        # Case insensitivity
        self.assertEqual(get_album("innervisions"), get_album("INNERVISIONS"))


if __name__ == "__main__":
    unittest.main()

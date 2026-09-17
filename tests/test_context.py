"""
test_context.py - Unit tests for GrooveContext and scaffolding engine.
"""

import tempfile
import unittest
from pathlib import Path

from harmonic_resonance.groove.context import detect_context, Scope
from harmonic_resonance.groove.scaffold import create_artist_readme, create_song_scaffold, add_track_entry
from harmonic_resonance.groove.catalog import load_song_tracks


class TestContext(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        # Create a mock groove workspace
        (self.root / "pyproject.toml").write_text('[project]\nname = "harmonic-resonance-groove"\n', encoding="utf-8")
        self.tracks_dir = self.root / "tracks"
        self.tracks_dir.mkdir()

        # Artist
        self.artist_dir = self.tracks_dir / "stevie-wonder"
        self.artist_dir.mkdir()

        # Song
        self.song_dir = self.artist_dir / "higher-ground"
        self.song_dir.mkdir()

        # Subfolder
        self.sub_dir = self.song_dir / "raw_unpadded"
        self.sub_dir.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_detect_root_scope(self):
        ctx = detect_context(self.root)
        self.assertEqual(ctx.scope, Scope.ROOT)
        self.assertEqual(ctx.tracks_dir, self.tracks_dir)
        self.assertIsNone(ctx.artist)
        self.assertIsNone(ctx.song)

    def test_detect_artist_scope(self):
        ctx = detect_context(self.artist_dir)
        self.assertEqual(ctx.scope, Scope.ARTIST)
        self.assertEqual(ctx.artist, "stevie-wonder")
        self.assertIsNone(ctx.song)

    def test_detect_song_scope(self):
        ctx = detect_context(self.song_dir)
        self.assertEqual(ctx.scope, Scope.SONG)
        self.assertEqual(ctx.artist, "stevie-wonder")
        self.assertEqual(ctx.song, "higher-ground")

    def test_detect_subfolder_scope(self):
        ctx = detect_context(self.sub_dir)
        self.assertEqual(ctx.scope, Scope.SONG)
        self.assertEqual(ctx.artist, "stevie-wonder")
        self.assertEqual(ctx.song, "higher-ground")

    def test_detect_external_scope(self):
        external_dir = Path("/tmp")
        ctx = detect_context(external_dir)
        self.assertEqual(ctx.scope, Scope.EXTERNAL)

    def test_list_artists_and_songs(self):
        ctx = detect_context(self.root)
        artists = ctx.list_artists()
        self.assertIn("stevie-wonder", artists)

        songs = ctx.list_songs()
        self.assertEqual(len(songs), 1)
        self.assertEqual(songs[0], ("stevie-wonder", "higher-ground"))

    def test_scaffold_song_files(self):
        new_song_dir = self.artist_dir / "living-for-the-city"
        created = create_song_scaffold(
            song_dir=new_song_dir,
            title="Living for the City",
            artist="Stevie Wonder",
            album="Innervisions",
            year="1973",
            tempo_bpm=98.0,
            key="F#m",
        )
        self.assertTrue((new_song_dir / "README.md").exists())
        self.assertTrue((new_song_dir / "tracks.csv").exists())
        self.assertTrue((new_song_dir / "chords.csml").exists())

        csml_text = (new_song_dir / "chords.csml").read_text(encoding="utf-8")
        self.assertIn(":title: Living for the City", csml_text)
        self.assertIn(":tempo: 98.0", csml_text)
        self.assertIn("* Intro", csml_text)

    def test_add_track_entry(self):
        new_song_dir = self.artist_dir / "test-song"
        new_song_dir.mkdir()
        create_song_scaffold(new_song_dir, "Test Song", "Stevie Wonder")

        add_track_entry(
            song_dir=new_song_dir,
            track_number=0,
            stem_name="full_song",
            display_name="Full Reference",
            url="https://youtube.com/watch?v=123",
        )
        tracks = load_song_tracks(new_song_dir)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["stem_name"], "full_song")
        self.assertEqual(tracks[0]["url"], "https://youtube.com/watch?v=123")


if __name__ == "__main__":
    unittest.main()

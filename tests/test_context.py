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

        # Album
        self.album_dir = self.artist_dir / "innervisions"
        self.album_dir.mkdir()
        (self.album_dir / "album.yaml").write_text("title: Innervisions\nyear: 1973\n", encoding="utf-8")

        # Song (in Album)
        self.song_dir = self.album_dir / "higher-ground"
        self.song_dir.mkdir()
        (self.song_dir / "tracks.csv").write_text("track_number,stem_name\n0,full_song\n", encoding="utf-8")

        # Subfolder in Song
        self.sub_dir = self.song_dir / "raw_unpadded"
        self.sub_dir.mkdir()

        # Legacy 2-tier song (direct under artist)
        self.legacy_song_dir = self.artist_dir / "superstition"
        self.legacy_song_dir.mkdir()
        (self.legacy_song_dir / "tracks.csv").write_text("track_number,stem_name\n0,full_song\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_detect_root_scope(self):
        ctx = detect_context(self.root)
        self.assertEqual(ctx.scope, Scope.ROOT)
        self.assertEqual(ctx.tracks_dir, self.tracks_dir)
        self.assertIsNone(ctx.artist)
        self.assertIsNone(ctx.album)
        self.assertIsNone(ctx.song)

    def test_detect_artist_scope(self):
        ctx = detect_context(self.artist_dir)
        self.assertEqual(ctx.scope, Scope.ARTIST)
        self.assertEqual(ctx.artist, "stevie-wonder")
        self.assertIsNone(ctx.album)
        self.assertIsNone(ctx.song)

    def test_detect_album_scope(self):
        ctx = detect_context(self.album_dir)
        self.assertEqual(ctx.scope, Scope.ALBUM)
        self.assertEqual(ctx.artist, "stevie-wonder")
        self.assertEqual(ctx.album, "innervisions")
        self.assertIsNone(ctx.song)

    def test_detect_song_scope(self):
        ctx = detect_context(self.song_dir)
        self.assertEqual(ctx.scope, Scope.SONG)
        self.assertEqual(ctx.artist, "stevie-wonder")
        self.assertEqual(ctx.album, "innervisions")
        self.assertEqual(ctx.song, "higher-ground")

    def test_detect_legacy_song_scope(self):
        ctx = detect_context(self.legacy_song_dir)
        self.assertEqual(ctx.scope, Scope.SONG)
        self.assertEqual(ctx.artist, "stevie-wonder")
        self.assertIsNone(ctx.album)
        self.assertEqual(ctx.song, "superstition")

    def test_detect_subfolder_scope(self):
        ctx = detect_context(self.sub_dir)
        self.assertEqual(ctx.scope, Scope.SONG)
        self.assertEqual(ctx.artist, "stevie-wonder")
        self.assertEqual(ctx.album, "innervisions")
        self.assertEqual(ctx.song, "higher-ground")

    def test_detect_external_scope(self):
        external_dir = Path("/tmp")
        ctx = detect_context(external_dir)
        self.assertEqual(ctx.scope, Scope.EXTERNAL)

    def test_list_artists_albums_and_songs(self):
        ctx = detect_context(self.root)
        artists = ctx.list_artists()
        self.assertIn("stevie-wonder", artists)

        albums = ctx.list_albums()
        self.assertIn(("stevie-wonder", "innervisions"), albums)

        songs = ctx.list_songs()
        self.assertEqual(len(songs), 2)
        self.assertIn(("stevie-wonder", "innervisions", "higher-ground"), songs)
        self.assertIn(("stevie-wonder", None, "superstition"), songs)

    def test_scaffold_song_files(self):
        new_song_dir = self.album_dir / "living-for-the-city"
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
        new_song_dir = self.album_dir / "test-song"
        new_song_dir.mkdir()
        create_song_scaffold(new_song_dir, "Test Song", "Stevie Wonder", album="Innervisions")

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

    def test_scaffold_album_files(self):
        from harmonic_resonance.groove.scaffold import create_album_scaffold
        new_album_dir = self.artist_dir / "talking-book"
        created = create_album_scaffold(
            album_dir=new_album_dir,
            title="Talking Book",
            artist="Stevie Wonder",
            year=1972,
            studios=["Air Studios, London", "Electric Lady, NYC"],
            producers=["Stevie Wonder", "Malcolm Cecil", "Robert Margouleff"],
            key_gear=["TONTO Modular Synthesizer", "Hohner Clavinet D6"],
        )
        self.assertTrue((new_album_dir / "album.yaml").exists())
        self.assertTrue((new_album_dir / "README.md").exists())
        yaml_content = (new_album_dir / "album.yaml").read_text(encoding="utf-8")
        self.assertIn("Talking Book", yaml_content)
        self.assertIn("Air Studios", yaml_content)

    def test_summation_providers(self):
        ctx = detect_context(self.root)
        cat_sum = ctx.get_catalog_summary()
        self.assertGreaterEqual(cat_sum["artists_count"], 1)
        self.assertGreaterEqual(cat_sum["albums_count"], 1)
        self.assertGreaterEqual(cat_sum["songs_count"], 2)

        art_sum = ctx.get_artist_summary("stevie-wonder")
        self.assertEqual(art_sum["artist"], "stevie-wonder")
        self.assertEqual(art_sum["albums_count"], 1)
        self.assertEqual(art_sum["songs_count"], 2)

        alb_sum = ctx.get_album_summary("stevie-wonder", "innervisions")
        self.assertEqual(alb_sum["album"], "innervisions")
        self.assertEqual(alb_sum["songs_count"], 1)

        song_sum = ctx.get_song_summary(self.song_dir)
        self.assertEqual(song_sum["stems_count"], 1)


if __name__ == "__main__":
    unittest.main()

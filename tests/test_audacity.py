"""
test_audacity.py - Unit tests for Audacity LOF generator.
"""

import tempfile
import unittest
from pathlib import Path

from harmonic_resonance.groove.catalog import get_song
from harmonic_resonance.groove.audacity import generate_audacity_lof


class TestAudacity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generate_superstition_lof(self):
        song = get_song("superstition")
        self.assertIsNotNone(song)

        lof_path = generate_audacity_lof(song, base_dir=self.base_dir, audio_format="wav")
        self.assertTrue(lof_path.exists())
        self.assertEqual(lof_path.name, "superstition.lof")

        content = lof_path.read_text(encoding="utf-8")
        self.assertIn("window offset 0", content)
        self.assertIn("Superstition", content)
        self.assertIn('file "01_drums.wav"', content)
        self.assertIn('file "02_bass.wav"', content)
        self.assertIn('file "03_clavinet1.wav"', content)
        self.assertIn('file "04_clavinet2.wav"', content)
        self.assertIn('file "05_horns.wav"', content)
        self.assertIn('file "06_vocals.wav"', content)

    def test_generate_flac_format(self):
        song = get_song("higher-ground")
        self.assertIsNotNone(song)

        lof_path = generate_audacity_lof(song, base_dir=self.base_dir, audio_format="flac")
        self.assertTrue(lof_path.exists())

        content = lof_path.read_text(encoding="utf-8")
        self.assertIn('file "01_drums.flac"', content)
        self.assertIn('file "02_bass.flac"', content)


if __name__ == "__main__":
    unittest.main()

"""
test_audacity.py - Unit tests for Audacity LOF generator.
"""

import tempfile
import unittest
from pathlib import Path

from harmonic_resonance.groove.catalog import get_song
from harmonic_resonance.groove.audacity import generate_audacity_lof, generate_launch_script


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
        self.assertIn('file "03_vocals.wav"', content)
        self.assertIn('file "04_clavinet1.wav"', content)
        self.assertIn('file "05_clavinet2.wav"', content)
        self.assertIn('file "06_horns.wav"', content)

    def test_generate_launch_script(self):
        song = get_song("higher-ground")
        self.assertIsNotNone(song)

        script_path = generate_launch_script(song, base_dir=self.base_dir)
        self.assertTrue(script_path.exists())
        self.assertEqual(script_path.name, "launch.sh")

        content = script_path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("#!/usr/bin/env bash"))
        self.assertIn("Higher Ground", content)
        self.assertIn("AUDACITY_BIN", content)
        self.assertIn("audacity-linux-4.0.0-x86_64.AppImage", content)
        self.assertIn("find . -maxdepth 1", content)
        self.assertIn('exec "$AUDACITY" "${TRACKS[@]}"', content)

    def test_generate_flac_format(self):
        song = get_song("higher-ground")
        self.assertIsNotNone(song)

        lof_path = generate_audacity_lof(song, base_dir=self.base_dir, audio_format="flac")
        self.assertTrue(lof_path.exists())

        content = lof_path.read_text(encoding="utf-8")
        self.assertIn('file "01_drums_tambourine.flac"', content)
        self.assertIn('file "02_moog_bass.flac"', content)


if __name__ == "__main__":
    unittest.main()

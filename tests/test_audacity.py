"""
test_audacity.py - Unit tests for Audacity 4 launcher and offset extractor.
"""

import tempfile
import unittest
from pathlib import Path

from harmonic_resonance.groove.catalog import get_song
from harmonic_resonance.groove.audacity import (
    generate_launch_script,
    extract_offsets_from_aup4,
    calculate_relative_offsets,
)


class TestAudacity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

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

    def test_calculate_relative_offsets(self):
        sample_offsets = {
            "00_full_song": 3.480500,
            "01_drums_tambourine": 4.313854,
            "02_moog_bass": 11.016146,
            "03_clavinets": 0.000000,
            "04_vocals": 4.015187,
        }
        rel = calculate_relative_offsets(sample_offsets, ref_key="00_full_song")
        self.assertIn("00_full_song", rel)
        self.assertAlmostEqual(rel["00_full_song"]["lead_in_trim"], 0.0)
        self.assertAlmostEqual(rel["00_full_song"]["pad_delay"], 0.0)

        # 03_clavinets has delta = -3.4805 -> lead_in_trim = 3.4805
        self.assertAlmostEqual(rel["03_clavinets"]["lead_in_trim"], 3.4805, places=4)
        self.assertAlmostEqual(rel["03_clavinets"]["pad_delay"], 0.0)

        # 01_drums has delta = +0.833354 -> pad_delay = 0.833354
        self.assertAlmostEqual(rel["01_drums_tambourine"]["pad_delay"], 0.833354, places=4)
        self.assertAlmostEqual(rel["01_drums_tambourine"]["lead_in_trim"], 0.0)

    def test_extract_offsets_from_existing_project(self):
        project_file = Path("tracks/stevie-wonder/higher-ground/higher-ground.aup4")
        if project_file.exists():
            offsets = extract_offsets_from_aup4(project_file)
            self.assertIn("00_full_song", offsets)
            self.assertIn("03_clavinets", offsets)
            self.assertAlmostEqual(offsets["00_full_song"], 3.4805, places=4)
            self.assertAlmostEqual(offsets["03_clavinets"], 0.0, places=4)


if __name__ == "__main__":
    unittest.main()

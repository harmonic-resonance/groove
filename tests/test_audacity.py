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
    get_audio_duration,
    pad_track_audio,
    pad_song_tracks,
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

    def test_pad_track_audio(self):
        import wave
        import struct

        # Create a 1.0 second silent WAV file at 44100Hz 16-bit stereo
        wav_path = self.base_dir / "test_tone.wav"
        framerate = 44100
        nchannels = 2
        sampwidth = 2
        nframes = 44100  # exactly 1.0 second

        with wave.open(str(wav_path), "wb") as w:
            w.setnchannels(nchannels)
            w.setsampwidth(sampwidth)
            w.setframerate(framerate)
            # Write 1.0s of silence
            data = struct.pack(f"<{nframes * nchannels}h", *([0] * (nframes * nchannels)))
            w.writeframes(data)

        self.assertAlmostEqual(get_audio_duration(wav_path), 1.0, places=2)

        # Pad with 0.5s start offset and total duration 2.0s
        padded_path = pad_track_audio(
            input_file=wav_path,
            output_file=self.base_dir / "padded.wav",
            start_offset=0.5,
            total_duration=2.0,
        )
        self.assertTrue(padded_path.exists())
        self.assertAlmostEqual(get_audio_duration(padded_path), 2.0, places=2)

    def test_pad_song_tracks(self):
        import wave
        import struct

        song_dir = self.base_dir / "dummy_song"
        song_dir.mkdir()

        framerate = 44100
        # Create 2 dummy tracks with different lengths
        for name, dur in [("00_full_song", 1.0), ("01_drums", 1.5)]:
            p = song_dir / f"{name}.wav"
            nframes = int(dur * framerate)
            with wave.open(str(p), "wb") as w:
                w.setnchannels(2)
                w.setsampwidth(2)
                w.setframerate(framerate)
                w.writeframes(b"\x00" * (nframes * 4))

        offsets = {
            "00_full_song": 0.5,   # end = 0.5 + 1.0 = 1.5s
            "01_drums": 0.2,       # end = 0.2 + 1.5 = 1.7s
        }
        # Equalized duration should be 1.7s
        processed = pad_song_tracks(song_dir, offsets, backup_raw=True)
        self.assertEqual(len(processed), 2)
        for name, p in processed.items():
            dur = get_audio_duration(p)
            self.assertAlmostEqual(dur, 1.7, places=2)

        # Raw backup should exist
        raw_dir = song_dir / "raw_unpadded"
        self.assertTrue((raw_dir / "00_full_song.wav").exists())
        self.assertTrue((raw_dir / "01_drums.wav").exists())

    def test_pad_track_audio_webm(self):
        import wave
        import struct
        import subprocess

        # First make a small 1.0s WAV then convert to WebM
        wav_path = self.base_dir / "sample.wav"
        framerate = 44100
        nframes = 44100
        with wave.open(str(wav_path), "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(framerate)
            w.writeframes(struct.pack(f"<{nframes * 2}h", *([0] * (nframes * 2))))

        webm_path = self.base_dir / "sample.webm"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(wav_path), "-c:a", "libopus", str(webm_path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
        self.assertTrue(webm_path.exists())

        # Pad webm with 0.5s start offset and total duration 2.0s
        padded_webm = pad_track_audio(
            input_file=webm_path,
            output_file=self.base_dir / "padded.webm",
            start_offset=0.5,
            total_duration=2.0,
        )
        self.assertTrue(padded_webm.exists())
        self.assertAlmostEqual(get_audio_duration(padded_webm), 2.0, places=1)


if __name__ == "__main__":
    unittest.main()


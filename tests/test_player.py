"""
test_player.py - Unit tests for Groove audio playback and spectrum visualization engine.
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from harmonic_resonance.groove.player import (
    AudioPlayerManager,
    MpvPlayer,
    SpectrumMode,
    SPECTRUM_CYCLE,
    MODE_LABELS,
    get_lavfi_filter,
    extract_waveform_envelope,
    render_waveform_ascii,
)


class TestPlayer(unittest.TestCase):

    def test_spectrum_modes_and_filters(self):
        self.assertEqual(SpectrumMode.WAVEFORM, "waveform")
        self.assertEqual(SpectrumMode.FREQS, "freqs")
        self.assertEqual(SpectrumMode.WAVES, "waves")
        self.assertEqual(SpectrumMode.SPECTROGRAM, "spectrum")
        self.assertEqual(SpectrumMode.CQT, "cqt")
        self.assertEqual(SpectrumMode.NONE, "none")

        self.assertEqual(SPECTRUM_CYCLE[0], SpectrumMode.CQT)

        for mode in SPECTRUM_CYCLE:
            self.assertIn(mode, MODE_LABELS)
            filt = get_lavfi_filter(mode, Path("/tmp/nonexistent.wav"), duration=100.0)
            self.assertIsNotNone(filt)
            self.assertTrue(len(filt) > 0)
            self.assertIn("asplit[ao]", filt)
            self.assertIn("format=rgb24", filt)

        # Verify CQT filter layout (note labels at top, bar_h=0, axis_h=60, sono_h=1020)
        cqt_filt = get_lavfi_filter(SpectrumMode.CQT, Path("/tmp/audio.wav"), duration=100.0, musical_key="E♭ minor")
        self.assertIsNotNone(cqt_filt)
        self.assertIn("bar_h=0", cqt_filt)
        self.assertIn("axis_h=60", cqt_filt)
        self.assertIn("sono_h=1020", cqt_filt)
        self.assertIn("overlay=", cqt_filt)

        # Verify waveform filter overlay
        with patch("harmonic_resonance.groove.player.ensure_waveform_image", return_value=Path("/tmp/waveform.png")), \
             patch("pathlib.Path.exists", return_value=True):
            wf_filt = get_lavfi_filter(SpectrumMode.WAVEFORM, Path("/tmp/audio.wav"), duration=120.0)
            self.assertIsNotNone(wf_filt)
            self.assertIn("movie=", wf_filt)
            self.assertIn("overlay=", wf_filt)
            self.assertIn("1920x1080", wf_filt)
            self.assertIn("asplit[ao]", wf_filt)
            self.assertIn("format=rgb24", wf_filt)

    def test_render_waveform_ascii_empty(self):
        wave_line, scrub_line = render_waveform_ascii([], progress_ratio=0.0, width=40)
        self.assertIn("▲", scrub_line)
        self.assertIn("bold yellow", wave_line)

    def test_render_waveform_ascii_progress(self):
        peaks = [0.0, 0.2, 0.5, 0.8, 1.0, 0.6, 0.4, 0.2]
        # At start
        w0, s0 = render_waveform_ascii(peaks, progress_ratio=0.0, width=20)
        self.assertIn("▲", s0)

        # At mid
        w_mid, s_mid = render_waveform_ascii(peaks, progress_ratio=0.5, width=20)
        self.assertIn("━", s_mid)
        self.assertIn("─", s_mid)
        self.assertIn("▲", s_mid)

        # At end
        w1, s1 = render_waveform_ascii(peaks, progress_ratio=1.0, width=20)
        self.assertIn("▲", s1)

    def test_extract_waveform_envelope_nonexistent(self):
        peaks = extract_waveform_envelope(Path("/nonexistent/file.wav"), num_bars=30)
        self.assertEqual(len(peaks), 30)
        self.assertEqual(peaks, [0.0] * 30)

    @patch("harmonic_resonance.groove.player.ensure_waveform_image", return_value=Path("/tmp/waveform.png"))
    @patch("harmonic_resonance.groove.player.is_mpv_available", return_value=True)
    @patch("pathlib.Path.exists", return_value=True)
    @patch("subprocess.Popen")
    def test_mpv_player_command_default_waveform(self, mock_popen, mock_exists, mock_mpv, mock_img):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        player = MpvPlayer(
            audio_path=Path("/tmp/test.wav"),
            title="Test Track",
            mode=SpectrumMode.WAVEFORM,
            loop=False,
            duration=120.0,
        )
        started = player.start()
        self.assertTrue(started)
        mock_popen.assert_called_once()
        cmd = mock_popen.call_args[0][0]

        self.assertEqual(cmd[0], "mpv")
        self.assertIn("--title=Test Track", cmd)
        self.assertTrue(any("--lavfi-complex=" in arg for arg in cmd))
        self.assertIn(str(Path("/tmp/test.wav").resolve()), cmd)
        player.stop()

    @patch("harmonic_resonance.groove.player.ensure_waveform_image", return_value=None)
    @patch("harmonic_resonance.groove.player.is_mpv_available", return_value=True)
    @patch("pathlib.Path.exists", return_value=True)
    @patch("subprocess.Popen")
    def test_mpv_player_command_none_and_loop(self, mock_popen, mock_exists, mock_mpv, mock_img):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        player = MpvPlayer(
            audio_path=Path("/tmp/test.wav"),
            title="Test Audio Only",
            mode=SpectrumMode.NONE,
            loop=True,
        )
        started = player.start()
        self.assertTrue(started)
        cmd = mock_popen.call_args[0][0]

        self.assertIn("--no-video", cmd)
        self.assertIn("--loop=inf", cmd)
        self.assertFalse(any("--lavfi-complex=" in arg for arg in cmd))
        player.stop()

    def test_audio_player_manager_singleton(self):
        m1 = AudioPlayerManager.get_instance()
        m2 = AudioPlayerManager.get_instance()
        self.assertIs(m1, m2)

    def test_audio_player_manager_get_status_stopped(self):
        manager = AudioPlayerManager.get_instance()
        manager.stop()
        status = manager.get_status()
        self.assertFalse(status["playing"])
        self.assertFalse(status["paused"])
        self.assertEqual(status["position"], 0.0)
        self.assertEqual(status["duration"], 0.0)

    def test_audio_player_manager_cycle_mode(self):
        manager = AudioPlayerManager.get_instance()
        manager.stop()
        manager.current_mode = SpectrumMode.CQT

        m1 = manager.cycle_mode()
        self.assertEqual(m1, SpectrumMode.WAVEFORM)

        m2 = manager.cycle_mode()
        self.assertEqual(m2, SpectrumMode.FREQS)

        m3 = manager.cycle_mode()
        self.assertEqual(m3, SpectrumMode.WAVES)

        m4 = manager.cycle_mode()
        self.assertEqual(m4, SpectrumMode.SPECTROGRAM)

        m5 = manager.cycle_mode()
        self.assertEqual(m5, SpectrumMode.CQT)

    def test_parse_musical_key(self):
        from harmonic_resonance.groove.player import parse_musical_key
        # Test minor keys
        eb_res = parse_musical_key("E♭ minor")
        self.assertIsNotNone(eb_res)
        root, scale = eb_res
        self.assertEqual(root, 3) # Eb
        self.assertIn(3, scale)
        self.assertIn(10, scale) # Bb (fifth)

        # Test major keys
        b_res = parse_musical_key("B major")
        self.assertIsNotNone(b_res)
        root, scale = b_res
        self.assertEqual(root, 11)

        # Test slash / compound keys
        csharp_res = parse_musical_key("C# minor / E major")
        self.assertIsNotNone(csharp_res)
        self.assertEqual(csharp_res[0], 1)

        # None / invalid
        self.assertIsNone(parse_musical_key(None))
        self.assertIsNone(parse_musical_key(""))
        self.assertIsNone(parse_musical_key("Unknown"))

    def test_ensure_key_overlay_image(self):
        from harmonic_resonance.groove.player import ensure_key_overlay_image
        png = ensure_key_overlay_image("E♭ minor", width=1920, height=1080)
        self.assertIsNotNone(png)
        self.assertTrue(png.exists())
        self.assertTrue(png.stat().st_size > 0)


if __name__ == "__main__":
    unittest.main()

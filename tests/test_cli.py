"""
test_cli.py - Unit tests for CLI parser.
"""

import unittest
from harmonic_resonance.groove.cli import build_parser


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def test_parser_list(self):
        args = self.parser.parse_args(["list"])
        self.assertEqual(args.command, "list")

    def test_parser_info(self):
        args = self.parser.parse_args(["info", "superstition"])
        self.assertEqual(args.command, "info")
        self.assertEqual(args.song, "superstition")

    def test_parser_study(self):
        args = self.parser.parse_args(["study", "higher-ground"])
        self.assertEqual(args.command, "study")
        self.assertEqual(args.song, "higher-ground")

    def test_parser_download_dry_run(self):
        args = self.parser.parse_args(["download", "superstition", "--dry-run", "--format", "flac"])
        self.assertEqual(args.command, "download")
        self.assertEqual(args.song, "superstition")
        self.assertTrue(args.dry_run)
        self.assertEqual(args.format, "flac")

    def test_parser_audacity(self):
        args = self.parser.parse_args(["audacity", "superstition", "--launch"])
        self.assertEqual(args.command, "audacity")
        self.assertEqual(args.song, "superstition")
        self.assertTrue(args.launch)


if __name__ == "__main__":
    unittest.main()

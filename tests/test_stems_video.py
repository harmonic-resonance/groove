"""
Unit tests for stems_video inspection and chapter parsing.
"""

from harmonic_resonance.groove.stems_video import (
    format_seconds_to_timestamp,
    parse_description_timestamps,
    parse_timestamp_to_seconds,
    slugify_stem_name,
)


def test_timestamp_conversions():
    assert parse_timestamp_to_seconds("00:00") == 0.0
    assert parse_timestamp_to_seconds("04:45") == 285.0
    assert parse_timestamp_to_seconds("01:04:45") == 3885.0
    assert parse_timestamp_to_seconds("226.5") == 226.5

    assert format_seconds_to_timestamp(0.0) == "00:00"
    assert format_seconds_to_timestamp(285.0) == "04:45"
    assert format_seconds_to_timestamp(3885.0) == "01:04:45"
    assert format_seconds_to_timestamp(285.5, include_ms=True) == "04:45.500"


def test_slugify_stem_name():
    assert slugify_stem_name("Piano") == "piano"
    assert slugify_stem_name("Drums & Percussion") == "drums-percussion"
    assert slugify_stem_name("01. Isolated Drums") == "isolated-drums"
    assert slugify_stem_name("Track 3: Electric Bass") == "electric-bass"
    assert slugify_stem_name("Lead Vocals (Dry)") == "lead-vocals-dry"


def test_parse_description_timestamps():
    description = """
    Stevie Wonder isolated tracks breakdown.

    Timestamps:
    0:00 - Piano
    04:45 Drums & Percussion
    [09:23] Bass
    14:01 - Backing Vocals
    17:24 Lead Vocals
    22:07 - Instrumental Full Mix

    Check out our other videos!
    """
    total_dur = 1611.0  # 26:51
    chapters = parse_description_timestamps(description, total_duration=total_dur)

    assert len(chapters) == 6
    assert chapters[0]["title"] == "Piano"
    assert chapters[0]["start_time"] == 0.0
    assert chapters[0]["end_time"] == 285.0
    assert chapters[0]["duration_formatted"] == "04:45"

    assert chapters[1]["title"] == "Drums & Percussion"
    assert chapters[1]["slug"] == "drums-percussion"
    assert chapters[1]["start_time"] == 285.0

    assert chapters[5]["title"] == "Instrumental Full Mix"
    assert chapters[5]["end_time"] == 1611.0

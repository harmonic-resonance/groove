"""
harmonic_resonance.groove - Study of groove mechanics and multitrack stem manager.
"""

from .catalog import (
    Song,
    Stem,
    GrooveAnalysis,
    CATALOG,
    get_song,
    list_songs,
    load_sources_from_csv,
    save_sources_to_csv,
)
from .downloader import (
    download_song_stems,
    download_stem,
)
from .audacity import (
    generate_launch_script,
    extract_offsets_from_aup4,
    calculate_relative_offsets,
    launch_audacity,
)
from .study import (
    get_groove_study,
)

__version__ = "0.1.0"

__all__ = [
    "Song",
    "Stem",
    "GrooveAnalysis",
    "CATALOG",
    "get_song",
    "list_songs",
    "load_sources_from_csv",
    "save_sources_to_csv",
    "download_song_stems",
    "download_stem",
    "generate_launch_script",
    "extract_offsets_from_aup4",
    "calculate_relative_offsets",
    "launch_audacity",
    "get_groove_study",
    "__version__",
]

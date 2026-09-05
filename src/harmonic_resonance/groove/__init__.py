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
)
from .downloader import (
    download_song_stems,
    download_stem,
)
from .audacity import (
    generate_audacity_lof,
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
    "download_song_stems",
    "download_stem",
    "generate_audacity_lof",
    "launch_audacity",
    "get_groove_study",
    "__version__",
]

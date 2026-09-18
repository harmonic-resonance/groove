"""
navigator package - Terminal-based interactive hierarchy navigator for Groove.
"""

from pathlib import Path
from typing import Optional

from .app import GrooveNavigator


def run_navigator(start_dir: Optional[Path] = None) -> None:
    """Launch the Groove Navigator application."""
    app = GrooveNavigator(start_dir=start_dir)
    app.run()


__all__ = ["GrooveNavigator", "run_navigator"]

"""
test_navigator.py - Unit and pilot tests for GrooveNavigator TUI.
"""

from pathlib import Path
import pytest

from harmonic_resonance.groove.navigator.app import GrooveNavigator
from harmonic_resonance.groove.navigator.screens.catalog_screen import CatalogScreen
from harmonic_resonance.groove.navigator.screens.artist_screen import ArtistScreen
from harmonic_resonance.groove.navigator.screens.album_screen import AlbumScreen
from harmonic_resonance.groove.navigator.screens.song_screen import SongScreen
from harmonic_resonance.groove.navigator.sort_modal import SortModal
from harmonic_resonance.groove.navigator.viewers import ContentModal


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_navigator_root_mount():
    repo_root = Path(__file__).resolve().parent.parent
    app = GrooveNavigator(start_dir=repo_root)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, CatalogScreen)
        assert app.screen.table.row_count >= 1


@pytest.mark.anyio
async def test_navigator_drilldown_and_popup():
    repo_root = Path(__file__).resolve().parent.parent
    app = GrooveNavigator(start_dir=repo_root)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, CatalogScreen)

        # Drill into ArtistScreen
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ArtistScreen)
        assert app.screen.artist_slug == "stevie-wonder"

        # Drill into AlbumScreen
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, AlbumScreen)

        # Drill into SongScreen
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, SongScreen)

        # Pop back to AlbumScreen with 'h'
        await pilot.press("h")
        await pilot.pause()
        assert isinstance(app.screen, AlbumScreen)

        # Pop back to ArtistScreen with 'h'
        await pilot.press("h")
        await pilot.pause()
        assert isinstance(app.screen, ArtistScreen)

        # Pop back to CatalogScreen with 'h'
        await pilot.press("h")
        await pilot.pause()
        assert isinstance(app.screen, CatalogScreen)


@pytest.mark.anyio
async def test_navigator_launch_from_song_dir():
    repo_root = Path(__file__).resolve().parent.parent
    song_dir = repo_root / "tracks" / "stevie-wonder" / "innervisions" / "higher-ground"
    app = GrooveNavigator(start_dir=song_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        # Direct start at SongScreen
        assert isinstance(app.screen, SongScreen)
        assert app.screen.song_slug == "higher-ground"

        # Pop to AlbumScreen
        await pilot.press("h")
        await pilot.pause()
        assert isinstance(app.screen, AlbumScreen)
        assert app.screen.album_slug == "innervisions"

        # Pop to ArtistScreen
        await pilot.press("h")
        await pilot.pause()
        assert isinstance(app.screen, ArtistScreen)
        assert app.screen.artist_slug == "stevie-wonder"

        # Pop to CatalogScreen
        await pilot.press("h")
        await pilot.pause()
        assert isinstance(app.screen, CatalogScreen)


@pytest.mark.anyio
async def test_navigator_modals():
    repo_root = Path(__file__).resolve().parent.parent
    song_dir = repo_root / "tracks" / "stevie-wonder" / "innervisions" / "higher-ground"
    app = GrooveNavigator(start_dir=song_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, SongScreen)

        # Test Chords Modal ('c')
        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, ContentModal)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SongScreen)

        # Test Study Modal ('u')
        await pilot.press("u")
        await pilot.pause()
        assert isinstance(app.screen, ContentModal)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SongScreen)

        # Test Sort Modal ('s')
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, SortModal)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SongScreen)


@pytest.mark.anyio
async def test_navigator_song_screen_player():
    repo_root = Path(__file__).resolve().parent.parent
    song_dir = repo_root / "tracks" / "stevie-wonder" / "innervisions" / "higher-ground"
    app = GrooveNavigator(start_dir=song_dir)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, SongScreen)
        song_screen: SongScreen = app.screen

        # Verify player widgets exist
        status_w = song_screen.query_one("#player-status")
        wave_w = song_screen.query_one("#player-waveform")
        assert status_w is not None
        assert wave_w is not None

        # Test cycle visualizer mode with 'v'
        initial_mode = song_screen.player_mgr.current_mode
        await pilot.press("v")
        await pilot.pause()
        assert song_screen.player_mgr.current_mode != initial_mode

        # Test stop with 'x'
        await pilot.press("x")
        await pilot.pause()
        assert not song_screen.player_mgr.is_playing()


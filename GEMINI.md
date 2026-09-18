# GEMINI.md - Context for harmonic-resonance / groove

## Purpose

**groove** is a project within the `harmonic-resonance` organization dedicated to studying the mechanics of musical groove, pocket, and rhythm section interplay. The project enables musicians, producers, and researchers to:
1. Catalog and download isolated multitrack audio stems for legendary groove tunes (starting with Stevie Wonder's master recordings).
2. Maintain a persistent per-song `tracks.csv` registry storing source URLs, track numbering, durations, and time alignment offsets so all audio can be regenerated on demand.
3. Automatically launch **Audacity 4** (`groove open`) with pre-aligned multitrack audio files in order (`00_full_song.wav`, `01_drums.wav`, ...) or open an existing `.aup4` project directly, ready to play instantly.
4. Render chord sheets and lyrics in Chord Sheet Markup Language (`chords.csml`), compatible with `harmonic-resonance/chordulator`.
5. Facilitate deep rehearsal and practice by muting/soloing stems, looping sections, and analyzing micro-timing and polyrhythmic syncopations.

## Architecture

- **Namespace Package**: `harmonic_resonance.groove` (under `src/harmonic_resonance/groove/`)
- **Key Modules**:
  - `context.py`: Directory context resolution (`Scope.ROOT`, `Scope.ARTIST`, `Scope.ALBUM`, `Scope.SONG`, `Scope.EXTERNAL`) and multi-level summation data engine (`get_catalog_summary`, `get_artist_summary`, `get_album_summary`, `get_song_summary`).
  - `catalog.py`: Dataclasses (`Song`, `Album`, `Stem`, `GrooveAnalysis`), curated registry of Stevie Wonder albums and songs, and `tracks.csv` loaders/savers.
  - `navigator/`: Textual-based interactive TUI navigator modelled after Seer Navigator:
    - `app.py`: `GrooveNavigator(App)` with context-aware stack building and pop-up handling.
    - `screens/catalog_screen.py`: Level 0 catalog summary grid + artists table.
    - `screens/artist_screen.py`: Level 1 artist summary grid + albums table.
    - `screens/album_screen.py`: Level 2 album summary grid (studios, producers, gear) + songs table.
    - `screens/song_screen.py`: Level 3 song study dashboard + stems table with action keys (`o` audacity, `c` chords, `u` study, `a` align, `p` pad, `[` / `]` siblings).
    - `viewers.py`: Markdown and CSML viewer modals.
    - `sort_modal.py`: Interactive column sort modal.
  - `scaffold.py`: Scaffolding for creating artist profiles (`create_artist_readme`), albums (`create_album_scaffold`), song studies (`create_song_scaffold`), and stem entries (`add_track_entry`).
  - `downloader.py`: Wrapper for `yt-dlp` and `ffmpeg` to download audio, apply offset alignments (lead-in trimming and pad delays), and execute full session regeneration (`regenerate_song_from_sources`).
  - `audacity.py`: Audacity 4 discovery, process launching (`open_song_in_audacity`), and `.aup4` SQLite project inspector (`extract_offsets_from_aup4`, `calculate_relative_offsets`).
  - `study.py`: Musicological breakdowns of pocket, ghost notes, clavinet damping, bass articulations, and rehearsal strategies.
  - `cli.py`: Rich-based command line interface (`nav`, `list`, `info`, `study`, `chords`, `tracks`, `open`, `align`, `pad`, `regenerate`, `download`, `new`, `new-artist`, `new-album`, `new-song`, `add-track`).
  - `__main__.py`: Entry point for `python -m harmonic_resonance.groove`.

## Workflow & Development

- **Context-aware invocation**:
  ```bash
  cd tracks/stevie-wonder/innervisions/higher-ground
  groove info
  groove study
  groove chords
  groove tracks
  groove open
  groove align --save
  groove pad
  ```
- **Interactive TUI Navigator**:
  ```bash
  groove nav       # Explicitly launch navigator
  groove           # Auto-launches navigator in an interactive terminal
  ```
- **Audacity 4 Session Loading**:
  Running `groove open` in the song folder loads `00_full_song.wav` as Track 1 followed by each stem in numeric order at timeline $t=0$, or opens the `<song>.aup4` project directly if present.
- **Audacity Rehearsal**:
  - Solo stems to hear nuances (e.g. kick squeaks, clavinet damping, breath control).
  - Mute an instrument to play that instrument live in the pocket with the original band.
  - Loop sections to build groove muscle memory.

## Conventions
- Code follows PEP 8 standards with type hints throughout.
- Large audio files, temporary stems, and `.aup4` projects are kept in `tracks/` and excluded by `.gitignore`.
- Regeneration is fully deterministic and driven by `tracks.csv`.
- Namespace packaging preserves `harmonic_resonance` identity across all sibling repos in the organization.

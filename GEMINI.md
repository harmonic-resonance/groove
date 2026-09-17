# GEMINI.md - Context for harmonic-resonance / groove

## Purpose

**groove** is a project within the `harmonic-resonance` organization dedicated to studying the mechanics of musical groove, pocket, and rhythm section interplay. The project enables musicians, producers, and researchers to:
1. Catalog and download isolated multitrack audio stems for legendary groove tunes (starting with Stevie Wonder's master recordings).
2. Maintain a persistent `sources.csv` registry storing all source URLs, track numbering, and time alignment offsets (lead-in trims and delays) so all audio can be regenerated on demand.
3. Automatically launch **Audacity 4** with pre-aligned multitrack audio files in order (`00_full_song.wav`, `01_drums.wav`, ...) via `launch.sh`, ready to play instantly.
4. Facilitate deep rehearsal and practice by muting/soloing stems, looping sections, and analyzing micro-timing and polyrhythmic syncopations.

## Architecture

- **Namespace Package**: `harmonic_resonance.groove` (under `src/harmonic_resonance/groove/`)
- **Key Modules**:
  - `catalog.py`: Dataclasses (`Song`, `Stem`, `GrooveAnalysis`), curated registry of Stevie Wonder songs (*Superstition*, *Higher Ground*, *Sir Duke*, *I Wish*), and `sources.csv` loaders/savers.
  - `downloader.py`: Wrapper for `yt-dlp` and `ffmpeg` to download audio, apply offset alignments (lead-in trimming and pad delays), and execute full session regeneration (`regenerate_song_from_sources`).
  - `audacity.py`: Audacity 4 discovery, launch script generator (`launch.sh`), and `.aup4` SQLite project inspector (`extract_offsets_from_aup4`, `calculate_relative_offsets`). Note: `.lof` files are obsolete and not used in Audacity 4.
  - `study.py`: Musicological breakdowns of pocket, ghost notes, clavinet damping, bass articulations, and rehearsal strategies.
  - `cli.py`: Rich-based command line interface (`sources`, `regenerate`, `align`, `list`, `info`, `study`, `download`, `audacity`).
  - `__main__.py`: Entry point for `python -m harmonic_resonance.groove`.

## Workflow & Development

- **CLI invocation**:
  ```bash
  python3 -m harmonic_resonance.groove sources [song]
  python3 -m harmonic_resonance.groove regenerate higher-ground
  python3 -m harmonic_resonance.groove align higher-ground --save
  python3 -m harmonic_resonance.groove audacity higher-ground --launch
  ```
- **Audacity 4 Session Loading**:
  Running `./launch.sh` in the song folder loads `00_full_song.wav` as Track 1 followed by each stem in numeric order. All stems are pre-aligned at $t=0$, ready to play.
- **Audacity Rehearsal**:
  - Solo stems to hear nuances (e.g. kick squeaks, clavinet damping, breath control).
  - Mute an instrument to play that instrument live in the pocket with the original band.
  - Loop sections to build groove muscle memory.

## Conventions
- Code follows PEP 8 standards with type hints throughout.
- Large audio files and temporary stems are kept in `tracks/` and excluded by `.gitignore`.
- Regeneration is fully deterministic and driven by `sources.csv`.
- Namespace packaging preserves `harmonic_resonance` identity across all sibling repos in the organization.

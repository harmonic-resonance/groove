# GEMINI.md - Context for harmonic-resonance / groove

## Purpose

**groove** is a project within the `harmonic-resonance` organization dedicated to studying the mechanics of musical groove, pocket, and rhythm section interplay. The project enables musicians, producers, and researchers to:
1. Catalog and download isolated multitrack audio stems for legendary groove tunes (starting with Stevie Wonder's master recordings).
2. Generate aligned multitrack project sessions for **Audacity** using its native `.lof` (List of Files) specification.
3. Facilitate deep rehearsal and practice by muting/soloing stems, looping sections, and analyzing micro-timing and polyrhythmic syncopations.

## Architecture

- **Namespace Package**: `harmonic_resonance.groove` (under `src/harmonic_resonance/groove/`)
- **Key Modules**:
  - `catalog.py`: Dataclasses (`Song`, `Stem`, `GrooveAnalysis`) and curated registry of Stevie Wonder songs (*Superstition*, *Higher Ground*, *Sir Duke*, *I Wish*, etc.).
  - `downloader.py`: Wrapper for `yt-dlp` and `ffmpeg` to extract audio in high-quality formats (WAV, FLAC, MP3) and organize stems into clean song directories (`tracks/<artist>/<song>/`).
  - `audacity.py`: Generator for Audacity `.lof` session files and launch helper.
  - `study.py`: Musicological breakdowns of pocket, ghost notes, clavinet damping, bass articulations, and rehearsal strategies.
  - `cli.py`: Rich-based command line interface (`list`, `info`, `study`, `download`, `audacity`).
  - `__main__.py`: Entry point for `python -m harmonic_resonance.groove`.

## Workflow & Development

- **CLI invocation**:
  ```bash
  python3 -m harmonic_resonance.groove list
  python3 -m harmonic_resonance.groove info superstition
  python3 -m harmonic_resonance.groove study higher-ground
  python3 -m harmonic_resonance.groove download superstition --format wav
  python3 -m harmonic_resonance.groove audacity superstition --launch
  ```
- **Audacity Session File**:
  The `.lof` file generated in `tracks/<artist>/<song>/<song>.lof` can be opened directly with `audacity <song>.lof`. It immediately constructs a multitrack session where each isolated stem is placed on a separate track.
- **Audacity Rehearsal**:
  - Solo stems to hear nuances (e.g. kick squeaks, clavinet damping, breath control).
  - Mute an instrument to play that instrument live in the pocket with the original band.
  - Loop sections to build groove muscle memory.

## Conventions
- Code follows PEP 8 standards with type hints throughout.
- Audio downloads are cached in `tracks/` and excluded by `.gitignore`.
- Namespace packaging preserves `harmonic_resonance` identity across all sibling repos in the organization.

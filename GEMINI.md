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
  - `context.py`: Directory context resolution (`Scope.ROOT`, `Scope.ARTIST`, `Scope.SONG`, `Scope.EXTERNAL`) enabling seamless CLI execution without repetitive `--artist` and `--song` flags.
  - `catalog.py`: Dataclasses (`Song`, `Track`, `GrooveAnalysis`), curated registry of Stevie Wonder songs (*Superstition*, *Higher Ground*, *Sir Duke*, *I Wish*, *Living for the City*, *Isn't She Lovely*), and `tracks.csv` loaders/savers.
  - `scaffold.py`: Interactive scaffolding for creating artist profiles (`create_artist_readme`), song studies (`create_song_scaffold`), and stem entries (`add_track_entry`).
  - `downloader.py`: Wrapper for `yt-dlp` and `ffmpeg` to download audio, apply offset alignments (lead-in trimming and pad delays), and execute full session regeneration (`regenerate_song_from_sources`).
  - `audacity.py`: Audacity 4 discovery, process launching (`open_song_in_audacity`), and `.aup4` SQLite project inspector (`extract_offsets_from_aup4`, `calculate_relative_offsets`). Note: `.lof` and `launch.sh` files are obsolete.
  - `study.py`: Musicological breakdowns of pocket, ghost notes, clavinet damping, bass articulations, and rehearsal strategies.
  - `cli.py`: Rich-based command line interface (`list`, `info`, `study`, `chords`, `tracks`, `open`, `align`, `pad`, `regenerate`, `download`, `new`, `new-song`, `new-artist`, `add-track`).
  - `__main__.py`: Entry point for `python -m harmonic_resonance.groove`.

## Workflow & Development

- **Context-aware invocation**:
  ```bash
  cd tracks/stevie-wonder/higher-ground
  groove info
  groove study
  groove chords
  groove tracks
  groove open
  groove align --save
  groove pad
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

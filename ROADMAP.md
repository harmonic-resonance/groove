# Groove Roadmap

The vision of **groove** is to build a comprehensive platform for understanding, dissecting, and playing the deepest grooves in modern music, beginning with Stevie Wonder and expanding to the pantheon of funk, soul, and jazz rhythm sections.

---

## Phase 1: Foundation & Stevie Wonder Multitrack Catalog (Current)

- [x] Repository scaffolding under `harmonic-resonance` namespace.
- [x] Curated catalog of Stevie Wonder groove masterpieces:
  - *Superstition* (Drums, Moog Synth Bass, Clavinets, Horns, Vocals)
  - *Higher Ground* (Drums, Moog Bass, Dual Clavinet, Vocals)
  - *Sir Duke* (Drums, Nathan Watts Bass, Rhodes/Keyboards, Brass Section, Vocals)
  - *I Wish* (Drums, Walking Bass, Clavinet/Rhodes, Horns, Vocals)
  - *Living for the City* (Drums, TONTO Moog, Fender Rhodes, Vocals)
  - *Isn't She Lovely* (Drums, Bass, Fender Rhodes, Harmonica, Vocals)
- [x] Audio stem downloader leveraging `yt-dlp` and `ffmpeg` to fetch high-fidelity WAV/FLAC/MP3 audio.
- [x] Audacity 4 multitrack launch script generator (`launch.sh`) and deterministic session regenerator with lead-in offset alignment.
- [x] Groove musicology notes and rehearsal recommendations for musicians.
- [x] CLI commands: `sources`, `regenerate`, `align`, `list`, `info`, `study`, `download`, `audacity`.

---

## Phase 2: Groove Metrics & Micro-timing Analysis

- [ ] **Transient & Beat Tracking**:
  - Integrate onset detection (via `librosa` / `scipy`) to detect exact transient strike times for kick, snare, hi-hat, bass, and clavinet.
- [ ] **Pocket Quantification**:
  - Measure millisecond deviations of each instrument relative to the metronomic grid.
  - Characterize whether an instrument is "on top", "in the pocket", or "laid back / behind the beat".
- [ ] **Swing Ratio Computation**:
  - Calculate exact 16th-note swing percentages (e.g. 50% straight vs. 58-62% funk swing).
- [ ] **Visual Groove Grid**:
  - Visual timeline diagrams in CLI/HTML showing where each instrument's hits fall in the subdivision grid.

---

## Phase 3: Interactive Rehearsal TUI & MIDI Integration

- [x] **Textual TUI Navigator & Rehearsal Workspace (`groove nav`)**:
  - Terminal-based hierarchical navigator across Catalog, Artist, Album, and Song levels.
  - 3-card summation dashboard at every level (counts, durations, projects, chords, studies).
  - In-app chord sheet and musicology viewers, Audacity launcher, and stem offset alignment.
- [ ] **Textual TUI Stem Player**:
  - Terminal-based multitrack mixer allowing live soloing, muting, volume adjustment, and section looping directly in the console.
- [ ] **Cross-Integration with `midiator` & `phi-midi`**:
  - Transcribe isolated bass and clavinet lines into MIDI files.
  - Play back MIDI along with the original isolated audio stems.
  - Record live MIDI performance and compare user timing accuracy to Stevie Wonder's timing.

---

## Phase 4: Expansion of the Master Groove Catalog

- [ ] **James Brown & The J.B.'s**:
  - Clyde Stubblefield & Jabo Starks (drums), Bootsy Collins & "Sweet Charles" Sherrell (bass), Jimmy Nolen ("chicken scratch" guitar).
  - *Cold Sweat*, *Funky Drummer*, *Sex Machine*.
- [ ] **The Meters**:
  - Zigaboo Modeliste (drums), George Porter Jr. (bass), Leo Nocentelli (guitar), Art Neville (organ).
  - *Cissy Strut*, *Look-Ka Py Py*, *Just Kissed My Baby*.
- [ ] **Herbie Hancock / Head Hunters**:
  - Mike Clark & Harvey Mason (drums), Paul Jackson (bass), Bill Summers (percussion), Herbie Hancock (Fender Rhodes & Clavinet).
  - *Chameleon*, *Actual Proof*.
- [ ] **Parliament / Funkadelic**:
  - Bernie Worrell (synthesizers & Clavinet), Bootsy Collins (bass), Jerome "Bigfoot" Brailey (drums).
  - *Flash Light*, *Give Up the Funk*.

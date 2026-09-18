groove
======

**groove** is a command-line environment and musicological toolkit dedicated to the empirical study, deconstruction, and rehearsal of rhythm section mechanics, pocket, and micro-timing.

Part of the `harmonic-resonance <https://github.com/harmonic-resonance>`_ platform, ``groove`` manages isolated multitrack audio stems, captures timeline offsets from Audacity 4 projects, renders chord charts via Chord Sheet Markup Language (CSML), and organizes deep song studies across legendary rhythm sections.

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://github.com/harmonic-resonance/groove/blob/main/LICENSE
   :alt: License

Features
--------

- **Context-Aware Scoping**: The CLI automatically detects where it is being run across a 4-tier hierarchy:
  - **Song scope** (inside ``tracks/<artist>/<album>/<song>/``): commands like ``groove info``, ``groove study``, ``groove chords``, ``groove tracks``, ``groove open``, ``groove align``, and ``groove pad`` run directly on that song without requiring ``--artist``, ``--album``, or ``--song`` flags.
  - **Album scope** (inside ``tracks/<artist>/<album>/``): commands like ``groove list`` and ``groove new-song`` automatically scope to that album, with album studio and gear context.
  - **Artist scope** (inside ``tracks/<artist>/``): commands like ``groove list`` and ``groove new-album`` automatically scope to that artist.
  - **Root scope** (repository root or ``tracks/``): operates across the complete catalog.

- **Interactive Textual TUI Navigator (``groove nav`` / ``groove``)**:
  - Modeled directly on ``geometor/seer-navigator``: delivers clean terminal navigation across the four-tier hierarchy.
  - 3-card summation metric header at each level (Catalog, Artist, Album, Song) displaying stems counts, total duration, projects present, chord charts, and studies.
  - Vim keybindings (``j``/``k`` navigation, ``l``/``Enter`` drill-down, ``h`` pop-up, ``s`` sort table, ``r`` refresh).
  - Quick modal viewers on song level: ``c`` (view chord sheet), ``u`` (view study markdown), ``o`` (launch Audacity), ``a`` (align offsets), ``p`` (pad stems), ``[`` / ``]`` (previous/next song in album).
  - Context launch: running ``groove`` from inside any directory starts at that exact level while maintaining the full back-stack up to Catalog.

- **Native Audacity 4 Integration (``groove open``)**:
  - Intelligently launches Audacity for rehearsal and study.
  - Automatically detects if a saved ``<song>.aup4`` Audacity project exists and opens it directly.
  - If no project file exists, automatically loads all numbered audio tracks (``00_*.wav``, ``01_*.wav``, ...) into Audacity in order at timeline :math:`t=0`.
  - Completely replaces legacy shell launch scripts.

- **Self-Contained Song Studies**: Every song in ``tracks/<artist>/<album>/<song>/`` contains:
  - ``README.md``: In-depth musicological breakdown of tempo, key, meter, pocket feel, micro-timing, interlocking rhythms, and practice tips.
  - ``tracks.csv``: Streamlined stem registry containing track numbers, stem names, display names, source URLs, video IDs, durations, source types, and start offsets.
  - ``chords.csml``: Structured chord progression and lyrics in Chord Sheet Markup Language (CSML), compatible with `harmonic-resonance/chordulator <https://github.com/harmonic-resonance/chordulator>`_.

- **Album Context & Studio Profiles**:
  - Each album in ``tracks/<artist>/<album>/`` contains an ``album.yaml`` and ``README.md`` capturing recording studios, associate producers, recording dates, and signature gear (TONTO, Clavinet D6, Mu-Tron III, Moog Bass).

- **Decoupled Alignment & Track Equalization**:
  - ``groove align``: Inspects the SQLite database inside an Audacity 4 ``.aup4`` project, computes microsecond-accurate clip start offsets, and syncs them to ``tracks.csv``.
  - ``groove pad``: Uses ``ffmpeg`` to insert start silence (``adelay``) and pad the tail (``apad``) so all stems share the exact same duration and sample count. Stems load at :math:`t=0` in locked pocket immediately.

- **Zero Audio in Git & On-Demand Regeneration**:
  - Audio stems (``*.wav``, ``*.mp3``, ``*.flac``) and SQLite projects (``*.aup4*``) are strictly ignored in git.
  - All stems can be downloaded or regenerated from scratch at any time via ``groove download`` or ``groove regenerate``.

- **Interactive Scaffolding**:
  - Quickly scaffold new artists (``groove new-artist``), albums (``groove new-album``), song studies (``groove new-song``), or add stems (``groove add-track``).

Installation
------------

Groove uses `uv <https://github.com/astral-sh/uv>`_ for Python package and tool management.

Install globally as a CLI tool:

.. code-block:: bash

   uv tool install --editable .

Or create and activate a local development virtual environment:

.. code-block:: bash

   uv venv
   source .venv/bin/activate
   uv pip install -e .

External Dependencies
~~~~~~~~~~~~~~~~~~~~~

Ensure you have ``ffmpeg`` and ``audacity`` installed:

.. code-block:: bash

   # On Debian / Ubuntu
   sudo apt install ffmpeg audacity

Directory Structure
-------------------

The catalog is organized hierarchically by artist, album, and song:

.. code-block:: text

   tracks/
   └── stevie-wonder/
       ├── README.md                          # Artist overview & rhythm section philosophy
       ├── talking-book/
       │   ├── album.yaml                     # Studio, gear, and producer metadata
       │   ├── README.md                      # Album overview & gear notes
       │   └── superstition/
       │       ├── README.md                  # Pocket breakdown, micro-timing, practice guide
       │       ├── chords.csml                # CSML chord progression and lyrics
       │       ├── tracks.csv                 # Stem registry, URLs, & alignment offsets
       │       ├── 00_full_song.wav           # Equalized reference mix (generated locally)
       │       ├── 01_drums.wav               # Isolated drums (generated locally)
       │       ├── 02_moog_bass.wav           # Moog synth bass (generated locally)
       │       ├── 03_clavinet1.wav           # Clavinet 1 (generated locally)
       │       ├── 04_clavinet2.wav           # Clavinet 2 (generated locally)
       │       ├── 05_horns.wav               # Horn section (generated locally)
       │       └── 06_vocals.wav              # Lead vocals (generated locally)
       ├── innervisions/
       │   ├── album.yaml
       │   ├── higher-ground/
       │   └── living-for-the-city/
       └── songs-in-the-key-of-life/
           ├── album.yaml
           ├── sir-duke/
           ├── i-wish/
           └── isnt-she-lovely/

CLI Usage & Workflow
---------------------

Interactive Navigator (TUI)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Launch the visual interactive terminal navigator:

.. code-block:: bash

   # Launch interactive TUI at current folder scope
   groove nav

   # Or simply 'groove' in an interactive terminal
   groove

Context-Aware Song Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Navigate into any song directory to execute commands in-context without repetitive arguments:

.. code-block:: bash

   cd tracks/stevie-wonder/higher-ground

   # Inspect metadata and registered stems
   groove info

   # Read the groove pocket analysis and rehearsal guide
   groove study

   # View chord sheet and lyrics (CSML format)
   groove chords

   # View stem registry table with URLs and timing offsets
   groove tracks

   # Open directly in Audacity 4
   groove open

   # Extract alignment offsets from higher-ground.aup4 into tracks.csv
   groove align --save

   # Pad start offsets and equalize all track lengths
   groove pad

Artist Scope Commands
~~~~~~~~~~~~~~~~~~~~~

Navigate into an artist directory:

.. code-block:: bash

   cd tracks/stevie-wonder

   # List all studies for Stevie Wonder
   groove list

   # Scaffold a new song under Stevie Wonder
   groove new-song "living-for-the-city" --title "Living for the City" --bpm 99 --key "F#m"

Repository-Wide Commands
~~~~~~~~~~~~~~~~~~~~~~~~

From the repository root:

.. code-block:: bash

   # List all groove studies across all artists
   groove list

   # Create a new artist
   groove new-artist "marvin-gaye" --name "Marvin Gaye"

   # Create a new song study
   groove new-song "whats-going-on" --artist "marvin-gaye" --title "What's Going On" --bpm 100 --key "E"

   # Register an isolated track URL into tracks.csv
   groove add-track "bass" "James Jamerson Bass" "https://www.youtube.com/watch?v=..." --song whats-going-on --artist marvin-gaye

   # Regenerate audio stems from scratch
   groove regenerate higher-ground --artist stevie-wonder

Rehearsal with Audacity
-----------------------

Running ``groove open`` loads the session directly into Audacity:

- **Mute stems** (``M``) to play that instrument live in the pocket with the original band (e.g., mute bass to rehearse your basslines against Stevie's drums and clavinet).
- **Solo stems** (``S``) to isolate micro-articulations, ghost notes, and subtle phrasing.
- **Loop sections** to build muscle memory around complex licks.
- **Slow down tempo** (via Audacity's *Change Tempo* effect) to dissect intricate 16th-note subdivisions without shifting pitch.

Contributing
------------

Contributions are welcome! Please submit issues or pull requests at https://github.com/harmonic-resonance/groove/issues.

License
-------

``groove`` is released under the MIT License.

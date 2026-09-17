groove
======

**groove** is a command-line environment and musicological toolkit dedicated to the empirical study, deconstruction, and rehearsal of rhythm section mechanics, pocket, and micro-timing.

Part of the `harmonic-resonance <https://github.com/harmonic-resonance>`_ platform, ``groove`` manages isolated multitrack audio stems, captures timeline offsets from Audacity 4 projects, renders chord charts via Chord Sheet Markup Language (CSML), and organizes deep song studies across legendary rhythm sections.

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://github.com/harmonic-resonance/groove/blob/main/LICENSE
   :alt: License

Features
--------

- **Context-Aware Scoping**: The CLI automatically detects where it is being run:
  - **Song scope** (inside ``tracks/<artist>/<song>/``): commands like ``groove info``, ``groove study``, ``groove chords``, ``groove tracks``, ``groove open``, ``groove align``, and ``groove pad`` run directly on that song without requiring ``--artist`` or ``--song`` flags.
  - **Artist scope** (inside ``tracks/<artist>/``): commands like ``groove list`` and ``groove new-song`` automatically scope to that artist.
  - **Root scope** (repository root): operates across the complete catalog.

- **Native Audacity 4 Integration (``groove open``)**:
  - Intelligently launches Audacity for rehearsal and study.
  - Automatically detects if a saved ``<song>.aup4`` Audacity project exists and opens it directly.
  - If no project file exists, automatically loads all numbered audio tracks (``00_*.wav``, ``01_*.wav``, ...) into Audacity in order at timeline :math:`t=0`.
  - Completely replaces legacy shell launch scripts.

- **Self-Contained Song Studies**: Every song in ``tracks/<artist>/<song>/`` contains:
  - ``README.md``: In-depth musicological breakdown of tempo, key, meter, pocket feel, micro-timing, interlocking rhythms, and practice tips.
  - ``tracks.csv``: Streamlined stem registry containing track numbers, stem names, display names, source URLs, video IDs, durations, source types, and start offsets.
  - ``chords.csml``: Structured chord progression and lyrics in Chord Sheet Markup Language (CSML), compatible with `harmonic-resonance/chordulator <https://github.com/harmonic-resonance/chordulator>`_.

- **Decoupled Alignment & Track Equalization**:
  - ``groove align``: Inspects the SQLite database inside an Audacity 4 ``.aup4`` project, computes microsecond-accurate clip start offsets, and syncs them to ``tracks.csv``.
  - ``groove pad``: Uses ``ffmpeg`` to insert start silence (``adelay``) and pad the tail (``apad``) so all stems share the exact same duration and sample count. Stems load at :math:`t=0` in locked pocket immediately.

- **Zero Audio in Git & On-Demand Regeneration**:
  - Audio stems (``*.wav``, ``*.mp3``, ``*.flac``) and SQLite projects (``*.aup4*``) are strictly ignored in git.
  - All stems can be downloaded or regenerated from scratch at any time via ``groove download`` or ``groove regenerate``.

- **Interactive Scaffolding**:
  - Quickly scaffold new artists (``groove new-artist``), song studies (``groove new-song``), or add stems (``groove add-track``).

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

The catalog is organized hierarchically by artist and song:

.. code-block:: text

   tracks/
   └── stevie-wonder/
       ├── README.md                      # Artist overview & rhythm section philosophy
       ├── higher-ground/
       │   ├── README.md                  # Pocket breakdown, micro-timing, practice guide
       │   ├── chords.csml                # CSML chord progression and lyrics
       │   ├── tracks.csv                 # Stem registry, URLs, & alignment offsets
       │   ├── 00_full_song.wav           # Equalized reference mix (generated locally)
       │   ├── 01_drums_tambourine.wav    # Isolated drums & tambourine (generated locally)
       │   ├── 02_moog_bass.wav           # Moog synth bass (generated locally)
       │   ├── 03_clavinets.wav           # Dual clavinets (generated locally)
       │   └── 04_vocals.wav              # Lead & backing vocals (generated locally)
       ├── superstition/
       ├── sir-duke/
       └── i-wish/

CLI Usage & Workflow
---------------------

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
   groove new-artist "d-angelo" --name "D'Angelo"

   # Create a new song study
   groove new-song "spanish-joint" --artist "d-angelo" --title "Spanish Joint" --bpm 108 --key "Dm"

   # Register an isolated track URL into tracks.csv
   groove add-track "drums" "Questlove Drums" "https://www.youtube.com/watch?v=..." --song spanish-joint --artist d-angelo

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

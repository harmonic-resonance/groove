groove
======

**groove** is a project dedicated to the empirical study, deconstruction, and practice of what makes a rhythm section groove.

Focusing initially on the masterworks of **Stevie Wonder**—the quintessential architect of funk, pocket, and polyrhythmic syncopation—``groove`` provides tools to download isolated multitrack stems from YouTube, catalog their arrangement, study their micro-timing, and generate instant **Audacity multitrack rehearsal sessions**.

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://github.com/harmonic-resonance/groove/blob/main/LICENSE
   :alt: License

Features
--------

- **Curated Groove Catalog**: Detailed metadata, tempo (BPM), key, time signatures, and stem breakdown for classic Stevie Wonder recordings:
  - *Superstition* (*Talking Book*, 1972)
  - *Higher Ground* (*Innervisions*, 1973)
  - *Sir Duke* (*Songs in the Key of Life*, 1976)
  - *I Wish* (*Songs in the Key of Life*, 1976)
  - *Living for the City* (*Innervisions*, 1973)
  - *Isn't She Lovely* (*Songs in the Key of Life*, 1976)

- **Stem Downloader & Regeneration**: Automated audio retrieval from YouTube (`sources.csv`) using ``yt-dlp`` and ``ffmpeg`` into clean, uncompressed WAV or lossless formats. Audio files can be regenerated on demand at any time with a single command.

- **Audacity 4 Multitrack Launcher (`launch.sh`)**: Direct multi-file command-line loader tailored for Audacity 4. Automatically passes files in order (master reference mix as Track 1, followed by isolated stems) to create a parallel-track session.

- **Lead-In & Track Offset Alignment**: Solves the alignment problem where isolated tracks have intro lead-ins or count-ins not present in the master song mix. Applies sample-accurate lead-in trimming and delay padding so all tracks start aligned at $t=0$, ready to play.

- **Audacity Project Offset Sync (`groove align`)**: Directly inspects `.aup4` SQLite project databases to extract the precise timeline offsets dialed in by ear, automatically recording them back into `sources.csv`.

- **Rehearsal & Play-Along Workflow**:
  - **Solo stems** to analyze individual parts (e.g. Stevie's isolated Clavinet damping or hi-hat micro-accents).
  - **Mute stems** to play along (e.g., mute drums to rehearse on drum kit; mute bass to lock in with the drums on bass; mute clavinet to practice the funk rhythm keys).
  - **Tempo manipulation**: Slow down tricky passages in Audacity without altering pitch.
  - **Looping**: Rehearse groove loops indefinitely to build muscle memory and internalize the pocket.

- **Groove Musicology & Analysis**: In-depth analysis of interlocking clavinet parts, ghost notes, Moog bass synth dynamics, Nathan Watts' walking basslines, and polyrhythmic counterpoint.

Installation
------------

Clone the repository and install in editable mode:

.. code-block:: bash

   git clone https://github.com/harmonic-resonance/groove.git
   cd groove
   pip install -e .

External Dependencies
~~~~~~~~~~~~~~~~~~~~~

Ensure you have ``ffmpeg`` and ``audacity`` (or the Audacity 4 AppImage in ``~/AppImages/``) installed:

.. code-block:: bash

   # On Debian / Ubuntu
   sudo apt install ffmpeg audacity

CLI Usage
---------

1. View all tracked sources, URLs, and time alignment offsets:

.. code-block:: bash

   groove sources [song_id]

2. Regenerate an entire multitrack session with offsets applied:

.. code-block:: bash

   groove regenerate higher-ground

3. Inspect and extract alignment offsets from a saved Audacity 4 project:

.. code-block:: bash

   groove align higher-ground --save

4. Generate the Audacity 4 launch script:

.. code-block:: bash

   groove audacity higher-ground --launch

5. Rehearse with Audacity:

In the song directory (e.g. ``tracks/stevie-wonder/higher-ground``):

.. code-block:: bash

   ./launch.sh            # Load all tracks in order, pre-aligned and ready to play
   ./launch.sh --project  # Open the saved .aup4 project directly

Rehearsal with Audacity
-----------------------

When launched, Audacity imports ``00_full_song.wav`` as Track 1 followed by each stem track. Because the stems are pre-aligned at $t=0$, hitting Spacebar immediately plays the entire groove in lockstep:
- Hit **Mute** (M) on any track you want to play yourself.
- Hit **Solo** (S) to hear only that instrument.
- Use **Audacity's Transport > Loop** to loop specific sections (like the unison lick in *Sir Duke*).
- Use **Effect > Pitch and Tempo > Change Tempo** to slow down without changing pitch.

Contributing
------------

Contributions are welcome! Please submit issues or pull requests at https://github.com/harmonic-resonance/groove/issues.

License
-------

``groove`` is released under the MIT License.

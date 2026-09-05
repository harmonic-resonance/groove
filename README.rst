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

- **Stem Downloader**: Automated audio extraction using ``yt-dlp`` and ``ffmpeg`` into clean, uncompressed or lossless formats (WAV, FLAC, MP3).

- **Audacity Multitrack Session Generator**: Instant creation of Audacity ``.lof`` (List of Files) session scripts. Opening a ``.lof`` file automatically places each isolated stem on its own aligned track in a single Audacity project window.

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

Ensure you have ``ffmpeg`` and ``audacity`` installed on your system:

.. code-block:: bash

   # On Debian / Ubuntu
   sudo apt install ffmpeg audacity

CLI Usage
---------

1. List available groove studies in the catalog:

.. code-block:: bash

   groove list

2. View details, tempo, key, and stem breakdown for a song:

.. code-block:: bash

   groove info superstition

3. Read the groove analysis, pocket notes, and rehearsal tips:

.. code-block:: bash

   groove study higher-ground

4. Download isolated tracks:

.. code-block:: bash

   groove download superstition --format wav

5. Generate an Audacity multitrack session and optionally open Audacity:

.. code-block:: bash

   groove audacity superstition --launch

Rehearsal with Audacity
-----------------------

Audacity natively supports ``.lof`` files. When you run ``groove audacity <song>``, a file named ``tracks/<artist>/<song>/<song>.lof`` is created containing directives such as:

.. code-block:: text

   window offset 0
   file "01_drums.wav"
   file "02_bass.wav"
   file "03_clavinet1.wav"
   file "04_clavinet2.wav"
   file "05_horns.wav"
   file "06_vocals.wav"

Opening this file in Audacity opens all stems in perfect synchronization. From here, you can:
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

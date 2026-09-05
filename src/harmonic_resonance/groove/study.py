"""
study.py - Musicological groove theory, pocket mechanics, and rehearsal guides.
"""

from typing import Dict
from .catalog import Song, get_song


GROOVE_FOUNDATIONS = """
# What Makes a Good Groove?
## An Empirical and Musicological Guide

Groove is often described as an elusive "feeling", but under the hood it is composed of 
five precise physical and musical principles:

### 1. The Pocket & Micro-Timing (Push vs. Drag)
A mechanical metronome subdivides time into identical, sterile intervals. 
A great human groove creates tension and release through **micro-timing deviations**:
- **Laid Back (Behind the Beat):** The snare backbeat lands 10–25 milliseconds *after* the theoretical grid. This imparts a relaxed, heavy, "stank" feel (characteristic of Stevie Wonder, Questlove, and J Dilla).
- **Driving (On Top of the Beat):** The hi-hat or percussion accents land 5–15 milliseconds *before* or right on the beat, imparting forward momentum and urgency.
- **Dynamic Swing Ratio:** Funk swing is rarely a straight triplet (66.7%) or straight eighth (50%). Master grooves live in the fluid pocket between **54% and 62% swing**, subtly expanding and contracting with musical intensity.

### 2. Interlocking Parts (The Hocket Principle)
The greatest rhythm sections do not compete for sonic or rhythmic space; they interlock:
- In *Superstition*, Clavinet 1, Clavinet 2, and the Moog Bass form a single composite 16th-note stream.
- When one instrument plays a downbeat, the other rests or plays a ghost note.
- Like West African drum ensembles or Balinese Gamelan, each part is simple on its own, but their interlocking creates hypnotic complexity.

### 3. Ghost Notes & Articulation
The groove is defined as much by unaccented notes as by loud hits:
- **Drum Ghost Notes:** Subtle 16th-note snare taps between the 2 and 4 provide the continuous rhythmic train that carries the song.
- **Clavinet Dampening:** Stevie Wonder used the Hohner Clavinet's slider damper and his left palm to produce percussive clicks devoid of pitch, turning the keyboard into a pitched conga drum.

### 4. Note Duration (The Funk of Silence)
Amateur players hold notes too long. Funk masters like bassist Nathan Watts and keyboardist Stevie Wonder release notes abruptly:
- The space between notes allows the drums to speak and gives the bassline its bounce.
- A staccato 16th note has punch; a legato note can turn funk into mud.

### 5. Timbre and Frequency Separation
Groove requires clear frequency lanes:
- **Sub/Low:** Kick drum (~50–80 Hz) and Moog Synth Bass fundamentals (~40–120 Hz).
- **Low-Mid:** Snare body and Rhodes fundamental (~200–500 Hz).
- **Mid:** Clavinet bite through Mu-Tron envelope filters (~1 kHz–3 kHz).
- **High:** Crispy hi-hat and tambourine transient clicks (~5 kHz–12 kHz).
"""


def get_groove_study(song_id: str) -> str:
    """Generate a comprehensive groove study markdown report for a given song."""
    song = get_song(song_id)
    if not song:
        return f"Song '{song_id}' not found in catalog."

    report = [
        f"# Groove Study: {song.title} — {song.artist}",
        f"**Album:** {song.album} ({song.year}) | **Tempo:** {song.tempo_bpm} BPM | **Key:** {song.key} | **Meter:** {song.time_signature}",
        "",
        "---",
        "",
        "## 1. Pocket & Feel Breakdown",
        song.analysis.pocket_description,
        "",
        "## 2. Micro-timing & Articulation",
        song.analysis.microtiming_notes,
        "",
        "## 3. Interlocking Rhythm & Arrangement",
        song.analysis.interlocking_rhythm,
        "",
        "## 4. Key Instrumentation & Sound Design",
    ]

    for inst in song.analysis.key_instruments:
        report.append(f"- **{inst}**")

    report.extend([
        "",
        "## 5. Multitrack Rehearsal & Practice Strategies (Audacity)",
    ])

    for tip in song.analysis.rehearsal_tips:
        report.append(f"- {tip}")

    report.extend([
        "",
        "---",
        "",
        "## 6. Stems in this Study",
    ])

    for idx, stem in enumerate(song.stems, start=1):
        report.append(f"### Stem {idx}: {stem.display_name}")
        report.append(f"- **Role:** {stem.description}")
        report.append(f"- **Default Pan:** {stem.pan:+.1f} | **Gain:** {stem.gain_db:+.1f} dB")
        if stem.query:
            report.append(f"- **Search Reference:** `{stem.query}`")
        report.append("")

    return "\n".join(report)

"""
catalog.py - Curated database of groove masterpieces and isolated stems.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Stem:
    """Represents an isolated audio stem of a song."""
    name: str
    display_name: str
    description: str
    source_url: Optional[str] = None
    query: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    gain_db: float = 0.0
    pan: float = 0.0  # -1.0 (full left) to +1.0 (full right)


@dataclass
class GrooveAnalysis:
    """Detailed musicological and pocket breakdown of a groove."""
    pocket_description: str
    microtiming_notes: str
    interlocking_rhythm: str
    key_instruments: List[str] = field(default_factory=list)
    rehearsal_tips: List[str] = field(default_factory=list)


@dataclass
class Song:
    """Represents a song in the groove catalog."""
    id: str
    title: str
    artist: str
    album: str
    year: int
    tempo_bpm: float
    key: str
    time_signature: str
    stems: List[Stem]
    analysis: GrooveAnalysis
    youtube_playlist_url: Optional[str] = None
    youtube_deconstruction_url: Optional[str] = None


# Curated Registry of Stevie Wonder's Grooviest Masterpieces
CATALOG: Dict[str, Song] = {
    "superstition": Song(
        id="superstition",
        title="Superstition",
        artist="Stevie Wonder",
        album="Talking Book",
        year=1972,
        tempo_bpm=100.0,
        key="E♭ minor",
        time_signature="4/4",
        youtube_deconstruction_url="https://www.youtube.com/watch?v=kYJqD9t9W98",
        stems=[
            Stem(
                name="drums",
                display_name="Drums",
                description="Stevie Wonder on drums. Legendary 16th-note hi-hat groove with subtle open-hat pushes on the '&' of 2 and 4. Kick pedal squeak is audible and iconic.",
                query="Stevie Wonder Superstition isolated drums",
            ),
            Stem(
                name="bass",
                display_name="TONTO Moog Synth Bass",
                description="Stevie playing the TONTO modular synthesizer. Plucky, resonant low-end that glues between the clavinet upbeats and kick downbeats.",
                query="Stevie Wonder Superstition isolated bass",
            ),
            Stem(
                name="clavinet1",
                display_name="Clavinet 1 (Main Rhythm)",
                description="Hohner Clavinet D6 processed through a Mu-Tron III envelope filter. Focuses on the driving 16th-note syncopation and dampened ghost notes.",
                query="Stevie Wonder Superstition isolated clavinet",
                pan=-0.4,
            ),
            Stem(
                name="clavinet2",
                display_name="Clavinet 2 (Counterpoint)",
                description="Secondary overdubbed Clavinet track providing high-register stabs and syncopated rhythmic counterpoint across the stereo field.",
                query="Stevie Wonder Superstition isolated clavinet 2",
                pan=0.4,
            ),
            Stem(
                name="horns",
                display_name="Horns (Sax & Trumpet)",
                description="Trevor Lawrence (tenor sax) and Steve Madaio (trumpet). Punchy, percussive horn stabs on the turnarounds.",
                query="Stevie Wonder Superstition isolated horns",
            ),
            Stem(
                name="vocals",
                display_name="Lead & Backing Vocals",
                description="Stevie Wonder's raw, electrifying lead vocal track with full dynamics, shouts, and spontaneous groove vocables.",
                query="Stevie Wonder Superstition isolated vocals",
            ),
        ],
        analysis=GrooveAnalysis(
            pocket_description=(
                "The pocket is built upon a delicate, loose 16th-note swing (~58% swing ratio). "
                "Stevie's drumming sits slightly behind the beat on the snare (backbeat on 2 and 4), "
                "while his hi-hat pushes the forward momentum with crisp micro-dynamics. "
                "The TONTO synth bass leaves generous space on beat 1, striking on the '1-e-and-A' pickup."
            ),
            microtiming_notes=(
                "Notice the interplay between Stevie's right hand on the hi-hat and his left hand on the snare. "
                "The ghost notes on the snare act as rhythmic connective tissue between the heavy backbeats. "
                "The tempo stays remarkably steady near 100 BPM despite being played completely without a click track."
            ),
            interlocking_rhythm=(
                "Superstition is a textbook study in West African hocket polyrhythm adapted to funk: "
                "no single instrument plays every beat; instead, Clavinet 1, Clavinet 2, and the Moog Bass "
                "weave through each other like three percussionists playing congas, agogô, and talking drum."
            ),
            key_instruments=["Hohner Clavinet D6", "TONTO Moog Modular Synth", "Ludwig Drum Kit", "Mu-Tron III Envelope Filter"],
            rehearsal_tips=[
                "Mute the Drums stem and play the drum groove: practice maintaining an even 16th-note hi-hat pulse while keeping the backbeat relaxed.",
                "Mute the Clavinet stems: practice the two-handed clavinet technique using left-hand muted dampening (palm mute) and right-hand rhythmic chord bites.",
                "Mute the Bass stem: practice locking your bass guitar or synth bass notes strictly with Stevie's kick drum accents.",
                "Solo both Clavinets together to hear how the stereo panning creates a three-dimensional funk texture.",
            ],
        ),
    ),
    "higher-ground": Song(
        id="higher-ground",
        title="Higher Ground",
        artist="Stevie Wonder",
        album="Innervisions",
        year=1973,
        tempo_bpm=125.0,
        key="E♭ minor",
        time_signature="4/4",
        youtube_deconstruction_url="https://www.youtube.com/watch?v=7hR9qQZkLw8",
        stems=[
            Stem(
                name="drums",
                display_name="Drums & Tambourine",
                description="Stevie Wonder playing all percussion. Relentless forward-driving four-on-the-floor hi-hat feel with urgent tambourine pulses.",
                query="Stevie Wonder Higher Ground isolated drums",
            ),
            Stem(
                name="bass",
                display_name="Moog Synth Bass",
                description="Heavy, bouncy analog synth bass with fast decay. Nails the root E♭ and punctuates the clavinet accents.",
                query="Stevie Wonder Higher Ground isolated bass",
            ),
            Stem(
                name="clavinet_left",
                display_name="Clavinet L (Wah / Envelope)",
                description="Left-channel Clavinet pumped through a Mu-Tron III auto-wah, generating the distinctive vocal-like squelch on every accent.",
                query="Stevie Wonder Higher Ground isolated clavinet",
                pan=-0.5,
            ),
            Stem(
                name="clavinet_right",
                display_name="Clavinet R (Chords & Rhythm)",
                description="Right-channel Clavinet playing rhythmic stabs and driving 16th-note percussive scrapes.",
                query="Stevie Wonder Higher Ground isolated clavinet right",
                pan=0.5,
            ),
            Stem(
                name="vocals",
                display_name="Lead & Backing Vocals",
                description="Passionate, spiritual vocal performance recorded in a single continuous take.",
                query="Stevie Wonder Higher Ground isolated vocals",
            ),
        ],
        analysis=GrooveAnalysis(
            pocket_description=(
                "Recorded in a feverish 3-hour burst where Stevie performed every single instrument "
                "sequentially. The groove is fast (125 BPM) and driven by an unstoppable motoric energy. "
                "Because Stevie recorded the drums first based on his internal pulse, the rhythm section "
                "has an organic ebb and flow that humanizes the fast tempo."
            ),
            microtiming_notes=(
                "The tambourine is the secret weapon: placed slightly ahead of the beat, it pulls the listener "
                "forward, while the kick drum grounds each measure with authoritative weight."
            ),
            interlocking_rhythm=(
                "The stereo separation between Clavinet L (wah-wah squelch) and Clavinet R (dry percussive bites) "
                "prevents the busy 16th-note arrangement from cluttering the mix. The bass line mirrors the "
                "clavinet's pentatonic riff during the turnaround."
            ),
            key_instruments=["Hohner Clavinet D6", "Mu-Tron III", "Moog Synthesizer", "Ludwig Drums", "Tambourine"],
            rehearsal_tips=[
                "Loop the main 2-bar riff at 80% tempo in Audacity to lock into the exact 16th-note subdivision before bringing it to 125 BPM.",
                "Mute the Bass stem to practice walking and popping your bass line under the dual clavinet weave.",
                "Mute the Clavinet L stem and try to match Stevie's dynamic envelope-filter phrasing.",
            ],
        ),
    ),
    "sir-duke": Song(
        id="sir-duke",
        title="Sir Duke",
        artist="Stevie Wonder",
        album="Songs in the Key of Life",
        year=1976,
        tempo_bpm=106.0,
        key="B major",
        time_signature="4/4",
        youtube_deconstruction_url="https://www.youtube.com/watch?v=J3PzN3lK0nE",
        stems=[
            Stem(
                name="drums",
                display_name="Drums",
                description="Raymond Pounds on drums. Extremely clean, joyous swing feel with brilliant ride cymbal articulation and snare cracks.",
                query="Stevie Wonder Sir Duke isolated drums",
            ),
            Stem(
                name="bass",
                display_name="Bass (Nathan Watts)",
                description="Nathan Watts on electric bass. One of the most famous bass performances in history; features the legendary lightning-fast unison chromatic breakdown.",
                query="Stevie Wonder Sir Duke isolated bass",
            ),
            Stem(
                name="keyboards",
                display_name="Fender Rhodes & Piano",
                description="Stevie Wonder on Fender Rhodes and acoustic piano, laying down warm jazz-inflected chords and harmonic padding.",
                query="Stevie Wonder Sir Duke isolated keyboards",
            ),
            Stem(
                name="horns",
                display_name="Brass Section",
                description="Hank Redd, Trevor Lawrence (saxophones), Raymond Maldonado, Steve Madaio (trumpets). Iconic hook melodies and unison run.",
                query="Stevie Wonder Sir Duke isolated horns",
            ),
            Stem(
                name="vocals",
                display_name="Vocals",
                description="Stevie's ecstatic vocal ode to Duke Ellington, Ella Fitzgerald, Count Basie, and Glenn Miller.",
                query="Stevie Wonder Sir Duke isolated vocals",
            ),
            Stem(
                name="percussion",
                display_name="Percussion",
                description="Tambourines, handclaps, and Latin percussion accents highlighting the upbeat energy.",
                query="Stevie Wonder Sir Duke isolated percussion",
            ),
        ],
        analysis=GrooveAnalysis(
            pocket_description=(
                "Pure swing-funk celebration. Nathan Watts and Raymond Pounds establish an airtight pocket "
                "where the bass attacks land exactly with the kick drum. The swing is bouncy yet disciplined (~60% swing ratio)."
            ),
            microtiming_notes=(
                "The famous unison breakdown (where bass, brass, and piano play the rapid 16th-note run) "
                "requires absolute synchronization: zero flamming between the bass pick/finger and the horn attacks."
            ),
            interlocking_rhythm=(
                "During the verse, the Rhodes plays syncopated off-beat chords while the bass bounces with octave jumps, "
                "creating a buoyant trampoline feel that lifts the vocal melody."
            ),
            key_instruments=["Fender Jazz Bass", "Fender Rhodes Electric Piano", "Brass Section", "Drum Kit"],
            rehearsal_tips=[
                "Solo the Bass and Horns stems: listen to how Nathan Watts articulates each note in the unison run without muddying the horns.",
                "Mute the Bass stem and practice the unison lick at 60%, 75%, 90%, and finally 100% tempo.",
                "Mute the Drums stem and rehearse keeping the celebratory, danceable swing without rushing.",
            ],
        ),
    ),
    "i-wish": Song(
        id="i-wish",
        title="I Wish",
        artist="Stevie Wonder",
        album="Songs in the Key of Life",
        year=1976,
        tempo_bpm=106.0,
        key="E♭ minor",
        time_signature="4/4",
        youtube_deconstruction_url="https://www.youtube.com/watch?v=wDZFfXn9phg",
        stems=[
            Stem(
                name="drums",
                display_name="Drums",
                description="Raymond Pounds on drums. Straightforward, irresistible four-on-the-floor hi-hat feel with sharp backbeats.",
                query="Stevie Wonder I Wish isolated drums",
            ),
            Stem(
                name="bass",
                display_name="Walking Bass (Nathan Watts)",
                description="Nathan Watts on electric bass playing one of the greatest walking/syncopated bass lines in music history (E♭ minor to A♭7).",
                query="Stevie Wonder I Wish isolated bass",
            ),
            Stem(
                name="keyboards",
                display_name="Fender Rhodes & Clavinet",
                description="Stevie Wonder layering Rhodes comping and sharp Clavinet accents across the chord changes.",
                query="Stevie Wonder I Wish isolated keyboards",
            ),
            Stem(
                name="horns",
                display_name="Horn Section",
                description="Punchy brass hits accentuating the turnaround phrases and nostalgic transitions.",
                query="Stevie Wonder I Wish isolated horns",
            ),
            Stem(
                name="vocals",
                display_name="Vocals",
                description="Stevie's energetic storytelling vocals reflecting on childhood memories.",
                query="Stevie Wonder I Wish isolated vocals",
            ),
        ],
        analysis=GrooveAnalysis(
            pocket_description=(
                "The groove is driven by Nathan Watts' unstoppable 8-bar repeating bass motif. "
                "The drums play an assertive, rock-solid backbeat, giving the bass all the space it needs "
                "to dance between the eighth-note pulses and syncopated chromatic approach notes."
            ),
            microtiming_notes=(
                "Notice how Nathan Watts uses staccato releases on the 8th notes to leave micro-silences. "
                "The groove is defined as much by where the notes end as where they begin."
            ),
            interlocking_rhythm=(
                "Stevie's left-hand keyboard comping doubles key chordal accents while his right hand "
                "fires off conversational fills in between vocal phrases."
            ),
            key_instruments=["Fender Precision / Jazz Bass", "Fender Rhodes", "Hohner Clavinet", "Horn Section"],
            rehearsal_tips=[
                "Mute the Bass stem and practice playing Nathan Watts' walking line: focus on the staccato cutoff of the notes and dynamic consistency.",
                "Mute the Keyboards stem and practice funky rhythm comping over the walking bass groove.",
                "Loop the bridge turnaround in Audacity to master the transitional brass and rhythm section hits.",
            ],
        ),
    ),
    "living-for-the-city": Song(
        id="living-for-the-city",
        title="Living for the City",
        artist="Stevie Wonder",
        album="Innervisions",
        year=1973,
        tempo_bpm=98.0,
        key="F# minor",
        time_signature="4/4",
        youtube_deconstruction_url="https://www.youtube.com/watch?v=W3a4jE9x1sQ",
        stems=[
            Stem(
                name="drums",
                display_name="Drums",
                description="Stevie Wonder on drums. Heavy, gritty slow funk backbeat with deliberate pauses and fills.",
                query="Stevie Wonder Living for the City isolated drums",
            ),
            Stem(
                name="bass",
                display_name="TONTO Moog Synth Bass",
                description="Stevie on TONTO modular synth. Gritty, buzzing analog bass tone carrying the dramatic, gritty urban weight.",
                query="Stevie Wonder Living for the City isolated bass",
            ),
            Stem(
                name="rhodes",
                display_name="Fender Rhodes",
                description="Stevie on electric piano delivering the dark, brooding chord progression and signature arpeggiated riffs.",
                query="Stevie Wonder Living for the City isolated rhodes",
            ),
            Stem(
                name="vocals",
                display_name="Vocals & Street Audio",
                description="Raw, rasping vocal performance with dramatic narration and spoken dialogue from the mid-song street scene.",
                query="Stevie Wonder Living for the City isolated vocals",
            ),
        ],
        analysis=GrooveAnalysis(
            pocket_description=(
                "A dramatic, visceral slow funk groove at 98 BPM. The pocket feels heavy, deliberate, "
                "and soaked in narrative tension. Every snare hit lands with crushing conviction."
            ),
            microtiming_notes=(
                "Stevie plays slightly behind the beat on the drums, reinforcing the struggle and gravity of the lyrical narrative."
            ),
            interlocking_rhythm=(
                "The interaction between the biting Rhodes attack and the fat, fuzzy Moog bass frequencies "
                "fills the entire mid-to-low acoustic spectrum without stepping on the vocal narrative."
            ),
            key_instruments=["TONTO Synthesizer", "Fender Rhodes", "Drums"],
            rehearsal_tips=[
                "Mute the Rhodes and play the dark chord progression, feeling how the heavy snare gives weight to each bar.",
                "Solo the Moog bass and study how analog synthesizer envelope decay shapes the rhythmic punch.",
            ],
        ),
    ),
    "isnt-she-lovely": Song(
        id="isnt-she-lovely",
        title="Isn't She Lovely",
        artist="Stevie Wonder",
        album="Songs in the Key of Life",
        year=1976,
        tempo_bpm=120.0,
        key="C# minor / E major",
        time_signature="4/4",
        youtube_deconstruction_url="https://www.youtube.com/watch?v=9g0HhG0L1pA",
        stems=[
            Stem(
                name="drums",
                display_name="Drums",
                description="Stevie Wonder on drums. Upbeat, bouncing shuffle/swing feel with a joyous ride cymbal pattern.",
                query="Stevie Wonder Isn't She Lovely isolated drums",
            ),
            Stem(
                name="bass",
                display_name="Electric Bass (Nathan Watts)",
                description="Nathan Watts holding down the infectious, bouncing bass line with rhythmic drops and slides.",
                query="Stevie Wonder Isn't She Lovely isolated bass",
            ),
            Stem(
                name="rhodes",
                display_name="Fender Rhodes Piano",
                description="Stevie on Fender Rhodes, laying down shimmering jazz-soul chord voicings.",
                query="Stevie Wonder Isn't She Lovely isolated rhodes",
            ),
            Stem(
                name="harmonica",
                display_name="Chromatic Harmonica Solo",
                description="Stevie's virtuoso chromatic harmonica solo, bending and phrasing with breathtaking lyrical groove.",
                query="Stevie Wonder Isn't She Lovely isolated harmonica",
            ),
            Stem(
                name="vocals",
                display_name="Vocals",
                description="Stevie's loving, joyous vocal track accompanied by the sounds of baby Aisha.",
                query="Stevie Wonder Isn't She Lovely isolated vocals",
            ),
        ],
        analysis=GrooveAnalysis(
            pocket_description=(
                "A swinging soul shuffle at 120 BPM. The groove smiles from start to finish. "
                "The ride cymbal pattern keeps the shuffle lilting while the bass dances on the 1 and the upbeat of 2."
            ),
            microtiming_notes=(
                "The swing ratio is high (~62%), leaning into a bluesy shuffle feel that gives the Rhodes "
                "comping its infectious bounce."
            ),
            interlocking_rhythm=(
                "The chromatic harmonica floats above the tight rhythm section, demonstrating how a solo instrument "
                "can play both rhythmically and melodically over a repeating chord vamp."
            ),
            key_instruments=["Chromatic Harmonica", "Fender Rhodes", "Electric Bass", "Ludwig Drums"],
            rehearsal_tips=[
                "Solo the Harmonica and Rhodes stems to study Stevie's melodic phrasing against his own harmonic comping.",
                "Mute the Harmonica stem and practice improvising your own lead lines (guitar, sax, flute, or keyboard) over the rhythm track.",
            ],
        ),
    ),
}


def get_song(song_id: str) -> Optional[Song]:
    """Retrieve a song from the catalog by its ID slug."""
    normalized = song_id.lower().replace(" ", "-").replace("_", "-")
    return CATALOG.get(normalized)


def list_songs() -> List[Song]:
    """Return all songs in the catalog."""
    return list(CATALOG.values())

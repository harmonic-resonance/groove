"""
catalog.py - Curated database of groove masterpieces and isolated stems.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


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
    deconstruction_slices: Optional[List[Dict]] = None
    full_song_url: Optional[str] = None
    track_number: Optional[int] = None


@dataclass
class Album:
    """Represents an album in the groove catalog."""
    id: str
    title: str
    artist: str
    year: int
    label: str = "Tamla / Motown"
    studios: List[str] = field(default_factory=list)
    producers: List[str] = field(default_factory=list)
    key_gear: List[str] = field(default_factory=list)
    personnel: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    tracks: List[Dict[str, Any]] = field(default_factory=list)


ALBUMS: Dict[str, Album] = {
    "music-of-my-mind": Album(
        id="music-of-my-mind",
        title="Music of My Mind",
        artist="Stevie Wonder",
        year=1972,
        label="Tamla / Motown",
        studios=["Media Sound (New York)"],
        producers=["Stevie Wonder", "Malcolm Cecil (Associate)", "Robert Margouleff (Associate)"],
        key_gear=["TONTO Modular Synthesizer", "Moog Synthesizer", "ARP Synthesizer", "Hohner Clavinet", "Fender Rhodes"],
        description="The breakthrough album launching Stevie Wonder's classic era, featuring groundbreaking one-man synthesizer orchestration with TONTO.",
    ),
    "talking-book": Album(
        id="talking-book",
        title="Talking Book",
        artist="Stevie Wonder",
        year=1972,
        label="Tamla / Motown",
        studios=["Electric Lady Studios (NYC)", "Crystal Sound (Hollywood)", "Record Plant (Los Angeles)"],
        producers=["Stevie Wonder", "Malcolm Cecil (Associate)", "Robert Margouleff (Associate)"],
        key_gear=["TONTO Modular Synthesizer", "Hohner Clavinet D6", "Mu-Tron III Envelope Filter", "Fender Rhodes Mark I", "Moog Bass"],
        description="A turning point in modern music. Stevie gained complete creative control, pioneering polyphonic electronic orchestration with TONTO alongside funk rhythm arrangements.",
    ),
    "innervisions": Album(
        id="innervisions",
        title="Innervisions",
        artist="Stevie Wonder",
        year=1973,
        label="Tamla / Motown",
        studios=["Record Plant (Los Angeles)", "Media Sound (New York)"],
        producers=["Stevie Wonder", "Malcolm Cecil (Associate)", "Robert Margouleff (Associate)"],
        key_gear=["TONTO Modular Synthesizer", "ARP 2600", "Moog Bass", "Hohner Clavinet D6", "Ludwig Drums"],
        description="Peak of the TONTO era. Stevie played virtually all instruments on masterpieces like 'Higher Ground' and 'Living for the City', demonstrating total groove command.",
    ),
    "songs-in-the-key-of-life": Album(
        id="songs-in-the-key-of-life",
        title="Songs in the Key of Life",
        artist="Stevie Wonder",
        year=1976,
        label="Tamla / Motown",
        studios=["Crystal Sound (Hollywood)", "The Hit Factory (New York)", "Record Plant (Sausalito)"],
        producers=["Stevie Wonder"],
        key_gear=["Yamaha GX-1 Polyphonic Synthesizer", "Fender Rhodes", "Hohner Clavinet D6", "Moog Synthesizer"],
        description="Double-album magnum opus. Expanded the rhythm section with elite musicians (Nathan Watts, Raymond Pounds) while integrating the revolutionary Yamaha GX-1 synthesizer.",
    ),
}


def get_album(album_id: str) -> Optional[Album]:
    """Retrieve an album by ID slug or title."""
    norm = album_id.lower().replace(" ", "-").replace("_", "-")
    if norm in ALBUMS:
        return ALBUMS[norm]
    for alb in ALBUMS.values():
        if alb.title.lower() == album_id.lower():
            return alb
    return None


def list_albums(artist: Optional[str] = None) -> List[Album]:
    """List all registered albums, optionally filtered by artist."""
    if artist:
        art_norm = artist.lower().replace(" ", "-")
        return [a for a in ALBUMS.values() if a.artist.lower().replace(" ", "-") == art_norm]
    return list(ALBUMS.values())


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
        track_number=6,
        full_song_url="https://www.youtube.com/watch?v=egqv1mtos6A",
        youtube_playlist_url="https://youtube.com/playlist?list=PL69e4qjLiDmHGIPAfcA0sO_gWD7n4ELzt",
        youtube_deconstruction_url="https://www.youtube.com/watch?v=kYJqD9t9W98",
        stems=[
            Stem(
                name="drums",
                display_name="Drums",
                description="Stevie Wonder on drums. Legendary 16th-note hi-hat groove with subtle open-hat pushes on the '&' of 2 and 4. Kick pedal squeak is audible and iconic.",
                source_url="https://www.youtube.com/watch?v=8ziGOKNAluY",
            ),
            Stem(
                name="bass",
                display_name="TONTO Moog Synth Bass",
                description="Stevie playing the TONTO modular synthesizer. Plucky, resonant low-end that glues between the clavinet upbeats and kick downbeats.",
                source_url="https://www.youtube.com/watch?v=vJS58xWUef8",
            ),
            Stem(
                name="vocals",
                display_name="Lead & Backing Vocals",
                description="Stevie Wonder's raw, electrifying lead vocal track with full dynamics, shouts, and spontaneous groove vocables.",
                source_url="https://www.youtube.com/watch?v=SxqK9DXlKqE",
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
        track_number=5,
        full_song_url="https://www.youtube.com/watch?v=1esf0efHbjM",
        youtube_deconstruction_url="https://www.youtube.com/watch?v=7hR9qQZkLw8",
        stems=[
            Stem(
                name="drums_tambourine",
                display_name="Drums & Tambourine",
                description="Stevie Wonder playing all percussion. Relentless forward-driving four-on-the-floor hi-hat feel with urgent tambourine pulses.",
                query="Stevie Wonder Higher Ground isolated drums",
            ),
            Stem(
                name="moog_bass",
                display_name="Moog Synth Bass",
                description="Heavy, bouncy analog synth bass with fast decay. Nails the root E♭ and punctuates the clavinet accents.",
                query="Stevie Wonder Higher Ground isolated bass",
            ),
            Stem(
                name="clavinets",
                display_name="Clavinets (Wah / Mu-Tron)",
                description="Hohner Clavinet D6 pumped through a Mu-Tron III auto-wah and envelope filter.",
                query="Stevie Wonder Higher Ground isolated clavinet",
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
        deconstruction_slices=[
            {"name": "01_drums_tambourine.wav", "display_name": "Drums & Tambourine", "start": "00:00:04.283", "duration": 226.078},
            {"name": "02_moog_bass.wav", "display_name": "Moog Synth Bass", "start": "00:03:51.971", "duration": 220.065},
            {"name": "03_clavinets.wav", "display_name": "Clavinets", "start": "00:07:33.861", "duration": 230.444},
            {"name": "04_vocals.wav", "display_name": "Lead & Backing Vocals", "start": "00:11:26.163", "duration": 226.376},
        ],
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
        full_song_url="https://www.youtube.com/watch?v=EnNgASBdCeo",
        youtube_playlist_url="https://youtube.com/playlist?list=PL69e4qjLiDmHGIPAfcA0sO_gWD7n4ELzt",
        youtube_deconstruction_url="https://www.youtube.com/watch?v=J3PzN3lK0nE",
        stems=[
            Stem(
                name="drums",
                display_name="Drums",
                description="Raymond Pounds on drums. Extremely clean, joyous swing feel with brilliant ride cymbal articulation and snare cracks.",
                source_url="https://www.youtube.com/watch?v=WwK3O9b5KFY",
            ),
            Stem(
                name="bass",
                display_name="Bass (Nathan Watts)",
                description="Nathan Watts on electric bass. One of the most famous bass performances in history; features the legendary lightning-fast unison chromatic breakdown.",
                source_url="https://www.youtube.com/watch?v=gexmlOgxMso",
            ),
            Stem(
                name="guitars",
                display_name="Guitars",
                description="Crisp funk rhythm guitar comping and unison fills.",
                source_url="https://www.youtube.com/watch?v=IBa9giTu-jI",
            ),
            Stem(
                name="vocals",
                display_name="Vocals",
                description="Stevie's ecstatic vocal ode to Duke Ellington, Ella Fitzgerald, Count Basie, and Glenn Miller.",
                source_url="https://www.youtube.com/watch?v=G9EE05Czn74",
            ),
            Stem(
                name="keyboards",
                display_name="Fender Rhodes & Keyboards",
                description="Stevie Wonder on Fender Rhodes and acoustic piano, laying down warm jazz-inflected chords and harmonic padding.",
                source_url="https://www.youtube.com/watch?v=bOslOGxQX8o",
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
        full_song_url="https://www.youtube.com/watch?v=c7IYSAUj78g",
        youtube_playlist_url="https://youtube.com/playlist?list=PL69e4qjLiDmHGIPAfcA0sO_gWD7n4ELzt",
        youtube_deconstruction_url="https://www.youtube.com/watch?v=wDZFfXn9phg",
        stems=[
            Stem(
                name="drums",
                display_name="Drums",
                description="Raymond Pounds on drums. Straightforward, irresistible four-on-the-floor hi-hat feel with sharp backbeats.",
                source_url="https://www.youtube.com/watch?v=qpnp5BEOcC0",
            ),
            Stem(
                name="bass",
                display_name="Walking Bass (Nathan Watts)",
                description="Nathan Watts on electric bass playing one of the greatest walking/syncopated bass lines in music history (E♭ minor to A♭7).",
                source_url="https://www.youtube.com/watch?v=9PHrzWjPodc",
            ),
            Stem(
                name="guitars",
                display_name="Guitars",
                description="Rhythmic funk guitar strums locking in with the walking bassline.",
                source_url="https://www.youtube.com/watch?v=QYcq9H5sS78",
            ),
            Stem(
                name="keyboards",
                display_name="Fender Rhodes & Clavinet",
                description="Stevie Wonder layering Rhodes comping and sharp Clavinet accents across the chord changes.",
                source_url="https://www.youtube.com/watch?v=6GjOW43QGCY",
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
        track_number=3,
        full_song_url="https://www.youtube.com/watch?v=ghLWjyOOLno",
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


TRACK_FIELDS = [
    "track_number",
    "stem_name",
    "display_name",
    "url",
    "video_id",
    "duration",
    "source_type",
    "start_offset",
    "notes",
]


def get_song_tracks_csv_path(
    song_id: str,
    artist_id: Optional[str] = None,
    album_id: Optional[str] = None,
) -> Optional[Path]:
    """Find the per-song tracks.csv (or legacy sources.csv) path."""
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    tracks_dir = root_dir / "tracks"
    song = get_song(song_id)

    # 1. If artist and album are known from catalog or arguments
    artist_slug = artist_id or (song.artist.lower().replace(" ", "-") if song else None)
    album_slug = album_id or (song.album.lower().replace(" ", "-") if (song and song.album) else None)
    s_id = song.id if song else song_id.lower().replace(" ", "-")

    if artist_slug and album_slug:
        target_dir = tracks_dir / artist_slug / album_slug / s_id
        for candidate_name in ["tracks.csv", "sources.csv"]:
            p = target_dir / candidate_name
            if p.exists():
                return p

    if artist_slug:
        # Check any album under artist
        for candidate_name in ["tracks.csv", "sources.csv"]:
            matches = list(tracks_dir.glob(f"{artist_slug}/*/{s_id}/{candidate_name}"))
            if matches:
                return matches[0]

        # Check direct artist/song (legacy 2-tier)
        target_dir = tracks_dir / artist_slug / s_id
        for candidate_name in ["tracks.csv", "sources.csv"]:
            p = target_dir / candidate_name
            if p.exists():
                return p

    # 2. Search across all artist and album subdirectories
    normalized_song = song_id.lower().replace(" ", "-")
    for candidate_name in ["tracks.csv", "sources.csv"]:
        matches = list(tracks_dir.glob(f"*/*/{normalized_song}/{candidate_name}")) + list(tracks_dir.glob(f"*/{normalized_song}/{candidate_name}"))
        if matches:
            return matches[0]

    # Default fallback target path for new files
    if artist_slug and album_slug:
        return tracks_dir / artist_slug / album_slug / s_id / "tracks.csv"
    elif artist_slug:
        return tracks_dir / artist_slug / s_id / "tracks.csv"

    return None


def get_song_sources_csv_path(song_id: str) -> Optional[Path]:
    """Backwards compatibility alias for get_song_tracks_csv_path."""
    return get_song_tracks_csv_path(song_id)


def load_song_tracks(song_dir: Path) -> List[Dict[str, str]]:
    """Load tracks for a specific song directory."""
    import csv

    p = Path(song_dir)
    csv_file = p / "tracks.csv"
    if not csv_file.exists():
        csv_file = p / "sources.csv"
    if not csv_file.exists():
        return []

    records = []
    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(dict(row))
    return records


def save_song_tracks(song_dir: Path, records: List[Dict[str, str]]) -> Path:
    """Save tracks.csv for a specific song directory without redundant columns."""
    import csv

    p = Path(song_dir)
    p.mkdir(parents=True, exist_ok=True)
    csv_file = p / "tracks.csv"

    if not records:
        with open(csv_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=TRACK_FIELDS)
            writer.writeheader()
        return csv_file

    fieldnames = [k for k in TRACK_FIELDS if any(k in r for r in records)] or TRACK_FIELDS
    # Strip redundant fields
    clean_records = []
    for r in records:
        clean = {k: r.get(k, "") for k in fieldnames}
        clean_records.append(clean)

    with open(csv_file, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_records)

    # Remove old sources.csv if it was present
    old_sources = p / "sources.csv"
    if old_sources.exists():
        old_sources.unlink()

    return csv_file


def load_tracks_from_csv(
    csv_path: Optional[str] = None,
    song_id: Optional[str] = None,
    artist_id: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Load track definitions from tracks.csv (or legacy sources.csv)."""
    import csv

    if csv_path:
        p = Path(csv_path)
        if not p.exists():
            return []
        records = []
        with open(p, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))
        return records

    # If song_id provided, load that song's tracks
    if song_id:
        t_csv = get_song_tracks_csv_path(song_id, artist_id=artist_id)
        if t_csv and t_csv.exists():
            records = []
            with open(t_csv, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    r = dict(row)
                    r.setdefault("song_id", song_id)
                    records.append(r)
            return records

    # Aggregate across all song tracks.csv files
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    tracks_dir = root_dir / "tracks"
    all_records = []

    song_csv_files = sorted(
        list(tracks_dir.glob("*/*/*/tracks.csv")) +
        list(tracks_dir.glob("*/*/tracks.csv")) +
        list(tracks_dir.glob("*/*/*/sources.csv")) +
        list(tracks_dir.glob("*/*/sources.csv"))
    )
    # Deduplicate if both exist
    seen_dirs = set()
    for scsv in song_csv_files:
        song_dir = scsv.parent
        if song_dir in seen_dirs:
            continue
        seen_dirs.add(song_dir)
        try:
            rel_parts = song_dir.relative_to(tracks_dir).parts
        except ValueError:
            continue

        if len(rel_parts) >= 3:
            art_name = rel_parts[0]
            album_name = rel_parts[1]
            song_name = rel_parts[2]
        elif len(rel_parts) == 2:
            art_name = rel_parts[0]
            album_name = None
            song_name = rel_parts[1]
        else:
            continue

        with open(scsv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                r = dict(row)
                r.setdefault("song_id", song_name)
                r.setdefault("artist", art_name)
                if album_name:
                    r.setdefault("album", album_name)
                all_records.append(r)

    if all_records:
        return all_records

    # Fallback to root sources.csv if present
    p = root_dir / "sources.csv"
    if not p.exists():
        p = Path("sources.csv")
    if not p.exists():
        return []

    records = []
    with open(p, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(dict(row))
    return records


def load_sources_from_csv(csv_path: Optional[str] = None, song_id: Optional[str] = None) -> List[Dict[str, str]]:
    """Alias for load_tracks_from_csv."""
    return load_tracks_from_csv(csv_path=csv_path, song_id=song_id)


def save_sources_to_csv(records: List[Dict[str, str]], csv_path: Optional[str] = None) -> Path:
    """Save records back to tracks.csv for affected songs."""
    if csv_path:
        # Save explicitly to given path
        import csv
        p = Path(csv_path)
        fieldnames = list(records[0].keys()) if records else TRACK_FIELDS
        with open(p, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        return p

    # Group by song_id and save per song
    by_song: Dict[str, List[Dict[str, str]]] = {}
    for r in records:
        sid = r.get("song_id")
        if sid:
            by_song.setdefault(sid, []).append(r)

    last_path = None
    for sid, srows in by_song.items():
        t_path = get_song_tracks_csv_path(sid)
        if t_path:
            save_song_tracks(t_path.parent, srows)
            last_path = t_path

    return last_path or Path("tracks.csv")


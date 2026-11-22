"""Instrument pages: which page a part of an arrangement belongs to, and how it is written.

A part (one track of work/<slug>/song.json) is placed on an instrument page by its name first (an arrangement can
give a GM 45 pizzicato program to a cello part) and its GM program second. The page decides the clef, the
transposition of the written part and the order in the full score.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Instrument:
    slug: str          # URL segment: /<country>/<slug>/
    name: str          # English, singular ("Violin")
    plural: str        # "Violins"
    family: str        # woodwinds, brass, percussion, keyboards, voices, strings
    order: int         # score order
    clef: str          # treble, bass, alto, treble8vb, grand, perc
    transpose: int = 0  # semitones written ABOVE sounding (Bb clarinet +2, F horn +7, piccolo -12, bass +12)
    transpose_name: str = ''  # "in Bb", "in F"


INSTRUMENTS = [
    Instrument('piccolo', 'Piccolo', 'Piccolos', 'woodwinds', 10, 'treble', -12),
    Instrument('flute', 'Flute', 'Flutes', 'woodwinds', 11, 'treble'),
    Instrument('oboe', 'Oboe', 'Oboes', 'woodwinds', 12, 'treble'),
    Instrument('clarinet', 'Clarinet', 'Clarinets', 'woodwinds', 13, 'treble', 2, 'in B♭'),
    Instrument('bassoon', 'Bassoon', 'Bassoons', 'woodwinds', 14, 'bass'),
    Instrument('horn', 'French Horn', 'French Horns', 'brass', 20, 'treble', 7, 'in F'),
    Instrument('trumpet', 'Trumpet', 'Trumpets', 'brass', 21, 'treble', 2, 'in B♭'),
    Instrument('trombone', 'Trombone', 'Trombones', 'brass', 22, 'bass'),
    Instrument('tuba', 'Tuba', 'Tubas', 'brass', 23, 'bass'),
    Instrument('timpani', 'Timpani', 'Timpani', 'percussion', 30, 'bass'),
    Instrument('percussion', 'Percussion', 'Percussion', 'percussion', 31, 'perc'),
    Instrument('harp', 'Harp', 'Harps', 'keyboards', 40, 'grand'),
    Instrument('piano', 'Piano', 'Pianos', 'keyboards', 41, 'grand'),
    Instrument('choir', 'Choir', 'Choir', 'voices', 50, 'treble'),
    Instrument('violin', 'Violin', 'Violins', 'strings', 60, 'treble'),
    Instrument('viola', 'Viola', 'Violas', 'strings', 61, 'alto'),
    Instrument('cello', 'Cello', 'Cellos', 'strings', 62, 'bass'),
    Instrument('double-bass', 'Double Bass', 'Double Basses', 'strings', 63, 'bass', 12),
]
BY_SLUG = {i.slug: i for i in INSTRUMENTS}

NAME_RULES = [  # first match wins, on the lower-case track name
    (r'piccolo', 'piccolo'), (r'flute', 'flute'), (r'oboe', 'oboe'), (r'clarinet', 'clarinet'),
    (r'bassoon', 'bassoon'), (r'horn', 'horn'), (r'trumpet|cornet', 'trumpet'), (r'trombone', 'trombone'),
    (r'tuba', 'tuba'), (r'timpani', 'timpani'), (r'harp', 'harp'), (r'piano', 'piano'),
    (r'choir|voices', 'choir'), (r'viola', 'viola'), (r'violin', 'violin'), (r'cello', 'cello'),
    (r'double bass|basses|contrabass', 'double-bass'),
    (r'percussion|snare|drum|tambourine|shaker|cymbal|triangle|gong|castanet|bell', 'percussion'),
]
PROGRAM_RULES = {72: 'piccolo', 73: 'flute', 68: 'oboe', 71: 'clarinet', 70: 'bassoon', 60: 'horn', 56: 'trumpet',
                 57: 'trombone', 58: 'tuba', 47: 'timpani', 46: 'harp', 0: 'piano', 52: 'choir', 53: 'choir',
                 54: 'choir', 40: 'violin', 44: 'violin', 45: 'violin', 41: 'viola', 42: 'cello', 43: 'double-bass'}


def instrument_of(track: dict) -> Instrument:
    if track.get('drums'):
        return BY_SLUG['percussion']
    name = (track.get('name') or '').lower()
    for pat, slug in NAME_RULES:
        if re.search(pat, name):
            return BY_SLUG[slug]
    slug = PROGRAM_RULES.get(track.get('program', -1))
    if slug:
        return BY_SLUG[slug]
    raise ValueError(f"no instrument page for track {track.get('name')!r} (program {track.get('program')})")


def technique_text(track: dict) -> str:
    """The playing instruction written at the start of a part ("pizz.", "trem.")."""
    name = (track.get('name') or '').lower()
    if 'pizz' in name or track.get('program') == 45:
        return 'pizz.'
    if 'spiccato' in name:
        return 'spicc.'
    if 'tremolo' in name or track.get('program') == 44:
        return 'trem.'
    return ''


def is_tremolo(track: dict) -> bool:
    return 'tremolo' in (track.get('name') or '').lower() or track.get('program') == 44


# Percussion keys (GM drum map, as the orchestra app reads them) -> written position on a 5-line staff.
# (display step, octave, notehead, name)
DRUM_POS = {
    35: ('F', 4, 'normal', 'Bass drum'), 36: ('F', 4, 'normal', 'Bass drum'),
    37: ('C', 5, 'x', 'Side stick'), 38: ('C', 5, 'normal', 'Snare drum'), 40: ('C', 5, 'normal', 'Snare drum'),
    39: ('D', 5, 'x', 'Hand clap'),
    41: ('A', 4, 'normal', 'Low tom'), 43: ('A', 4, 'normal', 'Low tom'), 45: ('B', 4, 'normal', 'Mid tom'),
    47: ('D', 5, 'normal', 'Mid tom'), 48: ('E', 5, 'normal', 'High tom'), 50: ('E', 5, 'normal', 'High tom'),
    42: ('G', 5, 'x', 'Hi-hat'), 44: ('D', 4, 'x', 'Hi-hat pedal'), 46: ('G', 5, 'circle-x', 'Open hi-hat'),
    49: ('A', 5, 'x', 'Crash cymbal'), 57: ('A', 5, 'x', 'Crash cymbal'), 52: ('A', 5, 'x', 'Chinese cymbal'),
    51: ('F', 5, 'x', 'Ride cymbal'), 59: ('F', 5, 'x', 'Suspended cymbal'), 53: ('F', 5, 'diamond', 'Ride bell'),
    55: ('B', 5, 'x', 'Splash cymbal'), 30: ('A', 5, 'diamond', 'Cymbal swell'),
    54: ('E', 4, 'x', 'Tambourine'), 56: ('E', 5, 'triangle', 'Cowbell'), 58: ('E', 4, 'triangle', 'Vibraslap'),
    81: ('B', 5, 'triangle', 'Triangle'), 80: ('B', 5, 'triangle', 'Triangle'),
}


def drum_pos(key: int):
    if key in DRUM_POS:
        return DRUM_POS[key]
    # every other small-percussion key is drawn as a triangle-head note above the staff (the app shows a triangle)
    return ('B', 5, 'triangle', 'Small percussion')

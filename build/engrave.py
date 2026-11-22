"""song.json notes -> MusicXML (partwise) for one part, a lead sheet, or the full score.

Times are counted in DIV = 24 divisions per quarter (every meter in the arrangements is x/4), which holds
sixteenths, thirty-seconds and triplets. The arrangement notes sit on the beat grid but are articulation-shortened
(a half note lasts 1.9 beats), so ends are joined to the next onset when the gap is small, then snapped.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

from instruments import Instrument, drum_pos, is_tremolo, technique_text

DIV = 24
TYPES = [(96, 'whole', 0), (72, 'half', 1), (48, 'half', 0), (36, 'quarter', 1), (24, 'quarter', 0),
         (18, 'eighth', 1), (12, 'eighth', 0), (9, '16th', 1), (6, '16th', 0), (3, '32nd', 0)]
TYPE_OF = {d: (t, dots) for d, t, dots in TYPES}

KEY_FIFTHS = {'Cb': -7, 'Gb': -6, 'Db': -5, 'Ab': -4, 'Eb': -3, 'Bb': -2, 'F': -1, 'C': 0, 'G': 1, 'D': 2, 'A': 3,
              'E': 4, 'B': 5, 'F#': 6, 'C#': 7}
MINOR_FIFTHS = {'Abm': -7, 'Ebm': -6, 'Bbm': -5, 'Fm': -4, 'Cm': -3, 'Gm': -2, 'Dm': -1, 'Am': 0, 'Em': 1, 'Bm': 2,
                'F#m': 3, 'C#m': 4, 'G#m': 5, 'D#m': 6, 'A#m': 7}
STEP_PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
SHARP_ORDER = 'FCGDAEB'
FLAT_ORDER = 'BEADGCF'
NATURAL_OF_PC = {0: 'C', 2: 'D', 4: 'E', 5: 'F', 7: 'G', 9: 'A', 11: 'B'}
SHARP_OF_PC = {1: 'C', 3: 'D', 6: 'F', 8: 'G', 10: 'A'}
FLAT_OF_PC = {1: 'D', 3: 'E', 6: 'G', 8: 'A', 10: 'B'}


# ------------------------------------------------------------------------------------------------ keys, spelling
def key_fifths(name: str) -> tuple[int, str]:
    if name in KEY_FIFTHS:
        return KEY_FIFTHS[name], 'major'
    if name in MINOR_FIFTHS:
        return MINOR_FIFTHS[name], 'minor'
    raise ValueError(f'unknown key {name!r}')


def transpose_fifths(fifths: int, semis: int) -> int:
    """The key signature of a part written `semis` semitones above sounding."""
    f = fifths + {0: 0, 2: 2, 7: 1, -12: 0, 12: 0}.get(semis, 0)
    if f > 6:
        f -= 12
    if f < -6:
        f += 12
    return f


class Speller:
    def __init__(self, fifths: int, mode: str = 'major'):
        self.fifths = fifths
        alters = {s: 0 for s in STEP_PC}
        if fifths > 0:
            for s in SHARP_ORDER[:fifths]:
                alters[s] = 1
        elif fifths < 0:
            for s in FLAT_ORDER[:-fifths]:
                alters[s] = -1
        self.scale = {(STEP_PC[s] + a) % 12: (s, a) for s, a in alters.items()}
        if mode == 'minor':  # the raised leading tone: one diatonic step under the tonic, raised
            # relative minor tonic = major tonic - 3 semitones; leading tone = tonic - 1
            maj_pc = (7 * fifths) % 12
            tonic_pc = (maj_pc - 3) % 12
            lt_pc = (tonic_pc - 1) % 12
            if lt_pc not in self.scale:
                tonic_step = self.scale[tonic_pc][0]
                lt_step = 'BCDEFGA'['CDEFGAB'.index(tonic_step)]
                self.scale[lt_pc] = (lt_step, (lt_pc - STEP_PC[lt_step] + 6) % 12 - 6)

    def spell(self, midi: int) -> tuple[str, int, int]:
        pc = midi % 12
        if pc in self.scale:
            step, alter = self.scale[pc]
        elif pc in NATURAL_OF_PC:
            step, alter = NATURAL_OF_PC[pc], 0
        elif self.fifths >= 0:
            step, alter = SHARP_OF_PC[pc], 1
        else:
            step, alter = FLAT_OF_PC[pc], -1
        octave = (midi - alter - STEP_PC[step]) // 12 - 1
        return step, alter, octave


# ------------------------------------------------------------------------------------------------ quantising
def _snap(t: float) -> int:
    """beats -> divisions on the 32nd (3) or triplet-16th (4) grid, whichever is nearer."""
    x = t * DIV
    g3, g4 = round(x / 3) * 3, round(x / 4) * 4
    return g3 if abs(g3 - x) <= abs(g4 - x) + 1e-9 else g4


def quantise(notes: list[dict], drums: bool = False) -> list[tuple[int, int, int]]:
    """[{on, duration, pitch}] in beats -> [(start, end, pitch)] in divisions."""
    ns = sorted(notes, key=lambda n: (n['on'], n['pitch']))
    onsets = sorted({round(n['on'], 4) for n in ns})
    import bisect
    out = []
    for n in ns:
        on, end = n['on'], n['on'] + n['duration']
        i = bisect.bisect_right(onsets, round(on, 4) + 1e-6)
        nxt = onsets[i] if i < len(onsets) else None
        if n.get('roll'):
            pass
        elif drums:
            # a drum stroke's length means nothing: let it ring to the next stroke, at most a beat
            end = min(nxt, on + 1.0) if nxt is not None else on + 1.0
            end = max(end, on + 0.25)
        elif nxt is not None:
            gap = nxt - end
            dur = end - on
            if (0 <= gap <= max(0.2, 0.16 * dur)) or (-0.3 <= gap < 0):
                end = nxt
        s, e = _snap(on), _snap(end)
        if e - s < 3:
            e = s + 3
        out.append((s, e, n['pitch']))
    # one grid per beat: a beat that mixes 32nd-grid and triplet-grid points takes the grid most points sit on
    pts = {}
    for s, e, _ in out:
        for t in (s, e):
            if t % DIV:
                pts.setdefault(t // DIV, []).append(t)
    regrid = {}
    for b, ts in pts.items():
        trip = sum(1 for t in ts if t % 3)
        plain = sum(1 for t in ts if t % 4)
        if trip and plain:
            g = 4 if trip >= plain else 3
            for t in ts:
                regrid[t] = round(t / g) * g
    if regrid:
        out = [(regrid.get(s, s), regrid.get(e, e), p) for s, e, p in out]
        out = [(s, max(e, s + 3), p) for s, e, p in out]
    return out


def find_rolls(notes: list[dict], max_gap: float = 0.26, min_strokes: int = 6) -> list[dict]:
    """Fast repeated strokes on one pitch (a drum or timpani roll) -> one note per roll, flagged 'roll'."""
    by_pitch: dict[int, list[dict]] = {}
    for n in sorted(notes, key=lambda n: n['on']):
        by_pitch.setdefault(n['pitch'], []).append(n)
    out = []
    for p, ns in by_pitch.items():
        i = 0
        while i < len(ns):
            j = i
            while (j + 1 < len(ns) and 0 < ns[j + 1]['on'] - ns[j]['on'] <= max_gap
                   and ns[j + 1]['duration'] <= 2.5 * max(ns[j + 1]['on'] - ns[j]['on'], 0.01)):
                j += 1  # a long last stroke is the roll's resolving hit, written as its own note
            if j - i + 1 >= min_strokes:
                step = ns[j]['on'] - ns[j - 1]['on']
                out.append(dict(on=ns[i]['on'], duration=ns[j]['on'] - ns[i]['on'] + step, pitch=p, roll=True,
                                velocity=ns[j].get('velocity')))
            else:
                out.extend(ns[i:j + 1])
            i = j + 1
    return out


def let_ring(qnotes: list[tuple[int, int, int]], share: float = 0.3) -> list[tuple[int, int, int]]:
    """A harp or piano arpeggio whose notes ring over the next ones: when more than `share` of the notes ring
    past the next onset, cut every note at the next onset (one voice of chords, the way harp parts are written)."""
    ons = sorted({s for s, _e, _p in qnotes})
    import bisect
    nxt = {}
    for s in ons:
        i = bisect.bisect_right(ons, s)
        nxt[s] = ons[i] if i < len(ons) else None
    over = sum(1 for s, e, _p in qnotes if nxt[s] is not None and e > nxt[s])
    if not qnotes or (share and over / len(qnotes) <= share):
        return qnotes
    return [(s, min(e, nxt[s]) if nxt[s] is not None else e, p) for s, e, p in qnotes]


@dataclass
class Event:
    start: int
    end: int
    pitches: list
    lyric: dict | None = None   # {'text', 'syllabic', 'extend'}
    marks: list = field(default_factory=list)  # direction xml strings placed before the note
    trem: bool = False                          # a roll: one held note with tremolo strokes


def voices(qnotes: list[tuple[int, int, int]], max_voices: int = 2) -> list[list[Event]]:
    """Chords (same start and end) into at most `max_voices` non-overlapping voices; voice 1 is filled first.
    Where every voice is still sounding, the earliest-ending one is cut at the new onset."""
    groups: dict[tuple[int, int], list[int]] = {}
    for s, e, p in qnotes:
        groups.setdefault((s, e), [])
        if p not in groups[(s, e)]:
            groups[(s, e)].append(p)
    evs = sorted((Event(s, e, sorted(ps)) for (s, e), ps in groups.items()),
                 key=lambda ev: (ev.start, -max(ev.pitches)))
    vs: list[list[Event]] = [[] for _ in range(max_voices)]
    for ev in evs:
        free = [i for i, v in enumerate(vs) if not v or v[-1].end <= ev.start]
        if free:
            vs[free[0]].append(ev)
            continue
        i = min(range(max_voices), key=lambda k: vs[k][-1].end)
        last = vs[i][-1]
        if last.start == ev.start:  # same onset, different length: join the chord at the shorter length
            last.end = min(last.end, ev.end)
            last.pitches = sorted(set(last.pitches) | set(ev.pitches))
            continue
        last.end = ev.start
        vs[i].append(ev)
    # voice 1 should be the upper one where both sound: swap whole voices if voice 2 is mostly higher
    if max_voices == 2 and vs[1]:
        hi = sum(1 for e in vs[1] if max(e.pitches) > _pitch_at(vs[0], e.start, max(e.pitches)))
        if hi > len(vs[1]) / 2:
            vs = [vs[1], vs[0]]
    return [v for v in vs if v]


def _pitch_at(voice: list[Event], t: int, default: int) -> int:
    for e in voice:
        if e.start <= t < e.end:
            return min(e.pitches)
    return -1


# ------------------------------------------------------------------------------------------------ splitting
def _aligned(p: int, d: int, bar: int, rest: bool) -> bool:
    """Can a note (or rest) of `d` divisions start at `p` (from the barline) without hiding the beat?"""
    beat = DIV
    if d >= 96:
        return p == 0 and bar >= 96
    if d == 72:
        return (p == 0 or (bar == 96 and p == beat and not rest)) and p + d <= bar
    if d == 48:
        if rest:
            return p % 48 == 0
        return p % beat == 0 and not (bar == 96 and p == beat and False)
    if d == 36:
        if rest:
            return False
        return p % beat == 0 or (p % 12 == 0 and (p + d) % beat == 0)
    if d == 24:
        return p % beat == 0 if rest else p % 12 == 0
    # shorter values never cross a beat
    if (p // beat) != ((p + d - 1) // beat):
        return False
    if rest:
        return p % (d if d in (12, 6, 3) else 3) == 0
    return p % 3 == 0


def split_plain(p: int, d: int, bar: int, rest: bool) -> list[int]:
    out = []
    while d > 0:
        for v, _t, _dots in TYPES:
            if v <= d and _aligned(p, v, bar, rest):
                out.append(v)
                p += v
                d -= v
                break
        else:
            out.append(d)  # unnotatable remainder (should not happen on the grid)
            break
    return out


TUP_DISPLAY = {4: 6, 8: 12, 12: 18, 16: 24}  # actual divisions in a 3:2 beat -> written value


def split_tuplet(d: int) -> list[int]:
    out = []
    while d > 0:
        for v in (16, 12, 8, 4):
            if v <= d:
                out.append(v)
                d -= v
                break
        else:
            out.append(d)
            break
    return out


# ------------------------------------------------------------------------------------------------ MusicXML
@dataclass
class PartSpec:
    pid: str
    name: str
    abbr: str
    inst: Instrument
    track: dict
    events_by_staff: list            # [[voice events], ...] per staff (1 or 2)
    written: bool = True             # transposed (part) vs concert (full score, octave transposers kept)
    drums: bool = False
    tremolo: bool = False
    technique: str = ''


def _pitch_xml(sp: Speller, midi: int, drums: bool) -> str:
    if drums:
        step, octv, _head, _name = drum_pos(midi)
        return f'<unpitched><display-step>{step}</display-step><display-octave>{octv}</display-octave></unpitched>'
    step, alter, octv = sp.spell(midi)
    a = f'<alter>{alter}</alter>' if alter else ''
    return f'<pitch><step>{step}</step>{a}<octave>{octv}</octave></pitch>'


def _clef_xml(clef: str, staff: int | None = None) -> str:
    n = f' number="{staff}"' if staff else ''
    return {
        'treble': f'<clef{n}><sign>G</sign><line>2</line></clef>',
        'bass': f'<clef{n}><sign>F</sign><line>4</line></clef>',
        'alto': f'<clef{n}><sign>C</sign><line>3</line></clef>',
        'treble8vb': f'<clef{n}><sign>G</sign><line>2</line><clef-octave-change>-1</clef-octave-change></clef>',
        'perc': f'<clef{n}><sign>percussion</sign></clef>',
    }[clef]


def _measure_segments(voice: list[Event], m0: int, m1: int):
    """(start, end, event | None, tie_start, tie_stop) inside one measure, rests where the voice is silent."""
    segs = []
    t = m0
    for ev in voice:
        if ev.end <= m0 or ev.start >= m1:
            continue
        s, e = max(ev.start, m0), min(ev.end, m1)
        if s > t:
            segs.append((t, s, None, False, False))
        segs.append((s, e, ev, ev.end > m1, ev.start < m0))
        t = e
    if t < m1:
        segs.append((t, m1, None, False, False))
    return segs


def _render_voice(voice: list[Event], m0: int, bar: int, voice_no: int, staff: int | None, sp: Speller,
                  spec: PartSpec, hide_rests: bool) -> tuple[str, int]:
    """One voice of one measure as MusicXML notes. Returns (xml, divisions written)."""
    m1 = m0 + bar
    segs = _measure_segments(voice, m0, m1)
    if hide_rests and all(ev is None for _s, _e, ev, _a, _b in segs):
        return '', 0
    # beats that need a triplet: any boundary off the 32nd grid
    bounds = set()
    for s, e, _ev, _a, _b in segs:
        bounds.add(s - m0)
        bounds.add(e - m0)
    trip_beats = {b // DIV for b in bounds if b % 3 and b % DIV}
    # cut segments at the edges of triplet beats
    cuts = []
    for s, e, ev, ts, tp in segs:
        pts = [s]
        for b in sorted(trip_beats):
            for edge in (m0 + b * DIV, m0 + (b + 1) * DIV):
                if s < edge < e:
                    pts.append(edge)
        pts = sorted(set(pts)) + [e]
        for i in range(len(pts) - 1):
            a, z = pts[i], pts[i + 1]
            cuts.append((a, z, ev, ts or z < e, tp or a > s))
    xml = []
    staff_x = f'<staff>{staff}</staff>' if staff else ''
    total = 0
    in_tuplet_beat = None
    pieces = []
    for a, z, ev, tie_start, tie_stop in cuts:
        rel = a - m0
        beat = rel // DIV
        trip = beat in trip_beats
        durs = split_tuplet(z - a) if trip else split_plain(rel, z - a, bar, ev is None)
        p = a
        for k, d in enumerate(durs):
            first, last = k == 0, k == len(durs) - 1
            pieces.append((p, d, ev, (tie_start or not last) if ev else False,
                           (tie_stop or not first) if ev else False, trip, first and not tie_stop))
            p += d
    # tuplet brackets: start/stop per triplet beat
    beat_of = [((pc[0] - m0) // DIV) if pc[5] else None for pc in pieces]
    beams = _beams(pieces, m0)
    for i, (p, d, ev, t_start, t_stop, trip, onset) in enumerate(pieces):
        tup = ''
        if trip:
            b = beat_of[i]
            if i == 0 or beat_of[i - 1] != b:
                tup += '<tuplet type="start" bracket="yes"/>'
            if i == len(pieces) - 1 or beat_of[i + 1] != b:
                tup += '<tuplet type="stop"/>'
            shown = TUP_DISPLAY.get(d, 12)
            typ, dots = TYPE_OF.get(shown, ('eighth', 0))
            tm = '<time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes></time-modification>'
        else:
            typ, dots = TYPE_OF.get(d, ('32nd', 0))
            tm = ''
        dot_x = '<dot/>' * dots
        if ev is None:
            if d == bar and not trip:
                xml.append(f'<note><rest measure="yes"/><duration>{d}</duration><voice>{voice_no}</voice>{staff_x}</note>')
            else:
                xml.append(f'<note><rest/><duration>{d}</duration><voice>{voice_no}</voice><type>{typ}</type>'
                           f'{dot_x}{tm}{staff_x}{_notations(tup)}</note>')
            total += d
            continue
        if onset:
            xml.extend(ev.marks)
        for j, pitch in enumerate(sorted(ev.pitches)):
            chord = '<chord/>' if j else ''
            ties = ('<tie type="stop"/>' if t_stop else '') + ('<tie type="start"/>' if t_start else '')
            tied = ('<tied type="stop"/>' if t_stop else '') + ('<tied type="start"/>' if t_start else '')
            notations = tied + (tup if j == 0 else '')
            head = ''
            if spec.drums:
                h = drum_pos(pitch)[2]
                if h != 'normal':
                    head = f'<notehead>{h}</notehead>'
            if (spec.tremolo or ev.trem) and j == 0:
                notations += '<ornaments><tremolo type="single">3</tremolo></ornaments>'
            lyr = ''
            if ev.lyric and j == 0 and onset:
                L = ev.lyric
                ext = '<extend/>' if L.get('extend') else ''
                lyr = (f'<lyric number="1"><syllabic>{L["syllabic"]}</syllabic><text>{escape(L["text"])}</text>'
                       f'{ext}</lyric>')
            bm = beams[i] if j == 0 else ''
            xml.append(f'<note>{chord}{_pitch_xml(sp, pitch, spec.drums)}<duration>{d}</duration>{ties}'
                       f'<voice>{voice_no}</voice><type>{typ}</type>{dot_x}{tm}{head}{staff_x}{bm}'
                       f'{_notations(notations)}{lyr}</note>')
        total += d
    return ''.join(xml), total


def _level(d: int, trip: bool) -> int:
    v = TUP_DISPLAY.get(d, 12) if trip else d
    return {12: 1, 18: 1, 6: 2, 9: 2, 3: 3}.get(v, 0)


def _beams(pieces, m0: int) -> list[str]:
    """MusicXML <beam> elements per piece: notes shorter than a quarter beamed within each beat."""
    out = [''] * len(pieces)
    groups, cur, cur_beat = [], [], None
    for i, (p, d, ev, _ts, _tp, trip, _on) in enumerate(pieces):
        lv = _level(d, trip) if ev is not None else 0
        beat = (p - m0) // DIV
        if lv and (not cur or beat == cur_beat):
            cur.append(i)
            cur_beat = beat
            continue
        if cur:
            groups.append(cur)
        cur, cur_beat = ([i], beat) if lv else ([], None)
    if cur:
        groups.append(cur)
    for g in groups:
        if len(g) < 2:
            continue
        lv = {i: _level(pieces[i][1], pieces[i][5]) for i in g}
        for level in (1, 2, 3):
            k = 0
            while k < len(g):
                if lv[g[k]] < level:
                    k += 1
                    continue
                r = k
                while r + 1 < len(g) and lv[g[r + 1]] >= level:
                    r += 1
                run = g[k:r + 1]
                if len(run) == 1:
                    if level > 1:
                        kind = 'forward hook' if k == 0 else 'backward hook'
                        out[run[0]] += f'<beam number="{level}">{kind}</beam>'
                else:
                    for n, i in enumerate(run):
                        kind = 'begin' if n == 0 else ('end' if n == len(run) - 1 else 'continue')
                        out[i] += f'<beam number="{level}">{kind}</beam>'
                k = r + 1
    return out


def _notations(inner: str) -> str:
    if not inner:
        return ''
    # MusicXML wants tied, tuplet, ornaments in that order inside <notations>; keep the given order
    return f'<notations>{inner}</notations>'


def tempo_marks(tempo: list, bar: int, total: int) -> dict[int, int]:
    """Division -> bpm for the metronome marks worth printing: the first tempo and every change that holds at
    least two bars and moves the tempo by 6 BPM or more from the last mark."""
    pts = [(round(b * DIV), bpm) for b, bpm in tempo]
    marks = {}
    last = None
    for i, (t, bpm) in enumerate(pts):
        nxt = pts[i + 1][0] if i + 1 < len(pts) else total
        if last is None:
            marks[0] = round(bpm)
            last = bpm
            continue
        if nxt - t >= 2 * bar and abs(bpm - last) >= 6:
            tb = (t // DIV) * DIV
            marks[tb] = round(bpm)
            last = bpm
    return marks


DYN_BANDS = [(36, 'pp'), (50, 'p'), (64, 'mp'), (80, 'mf'), (96, 'f'), (200, 'ff')]


def dyn_of(vel: int) -> str:
    for top, name in DYN_BANDS:
        if vel < top:
            return name
    return 'ff'


def dynamics_marks(qnotes_vel: list[tuple[int, int, int, int]]) -> dict[int, str]:
    """(start, end, pitch, velocity) -> {division: 'mf'} where the written dynamic changes and stays."""
    by_on: dict[int, list[int]] = {}
    for s, _e, _p, v in qnotes_vel:
        if v:
            by_on.setdefault(s, []).append(v)
    ons = sorted(by_on)
    bands = [dyn_of(round(sum(by_on[o]) / len(by_on[o]))) for o in ons]
    marks = {}
    cur = None
    for i, o in enumerate(ons):
        b = bands[i]
        if b == cur:
            continue
        stays = all(x == b for x in bands[i:i + 3])
        if cur is None or stays:
            marks[o] = b
            cur = b
    return marks


def build_score(*, title: str, subtitle: str, composer: str, lyricist: str, arranger: str, parts: list[PartSpec],
                beats_per_bar: int, total_bars: int, concert_fifths: int, mode: str, tempo: list,
                rehearsal: dict[int, str], dynamics: dict[str, dict[int, str]], multirest: bool,
                header_part_name: str = '', keys: dict[int, tuple[int, str]] | None = None) -> str:
    """keys: key changes after the start, {division at a barline: (concert fifths, mode)}."""
    keys = {k: v for k, v in (keys or {}).items() if k > 0}
    bar = beats_per_bar * DIV
    total = total_bars * bar
    tmarks = tempo_marks(tempo, bar, total)
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
           '"http://www.musicxml.org/dtds/partwise.dtd">',
           '<score-partwise version="4.0">',
           f'<work><work-title>{escape(title)}</work-title></work>',
           f'<movement-title>{escape(title)}</movement-title>',
           '<identification>']
    if composer:
        out.append(f'<creator type="composer">{escape(composer)}</creator>')
    if lyricist:
        out.append(f'<creator type="lyricist">{escape(lyricist)}</creator>')
    if arranger:
        out.append(f'<creator type="arranger">{escape(arranger)}</creator>')
    out.append('<rights>anthem.adjiebrotots.com</rights></identification>')
    # credits: Verovio draws the page header from these
    out.append(f'<credit page="1"><credit-type>title</credit-type><credit-words justify="center" valign="top" '
               f'font-size="22">{escape(title)}</credit-words></credit>')
    if subtitle:
        out.append(f'<credit page="1"><credit-type>subtitle</credit-type><credit-words justify="center" '
                   f'valign="top" font-size="13">{escape(subtitle)}</credit-words></credit>')
    if composer:
        out.append(f'<credit page="1"><credit-type>composer</credit-type><credit-words justify="right" '
                   f'valign="top" font-size="10">{escape(composer)}</credit-words></credit>')
    if header_part_name:
        out.append(f'<credit page="1"><credit-type>part name</credit-type><credit-words justify="left" '
                   f'valign="top" font-size="12">{escape(header_part_name)}</credit-words></credit>')
    out.append('<part-list>')
    for ps in parts:
        out.append(f'<score-part id="{ps.pid}"><part-name>{escape(ps.name)}</part-name>'
                   f'<part-abbreviation>{escape(ps.abbr)}</part-abbreviation></score-part>')
    out.append('</part-list>')

    for ps in parts:
        semis = ps.inst.transpose if ps.written else (ps.inst.transpose if abs(ps.inst.transpose) == 12 else 0)
        fifths = 0 if ps.drums else transpose_fifths(concert_fifths, semis)
        sp = Speller(fifths, mode if semis == 0 else 'major')
        # written pitches
        staves = []
        for staff_voices in ps.events_by_staff:
            vs = []
            for v in staff_voices:
                vs.append([Event(e.start, e.end, [p + (0 if ps.drums else semis) for p in e.pitches], e.lyric,
                                 list(e.marks), e.trem) for e in v])
            staves.append(vs)
        nstaves = len(staves)
        dyn = dynamics.get(ps.pid, {})
        # attach direction marks (dynamics) to the first event at that onset in the top voice of staff 1
        if staves and staves[0]:
            top = staves[0][0]
            for e in top:
                if e.start in dyn:
                    e.marks.append(f'<direction placement="below"><direction-type><dynamics><{dyn[e.start]}/>'
                                   f'</dynamics></direction-type>{"<staff>1</staff>" if nstaves > 1 else ""}</direction>')
        if ps.technique and staves and staves[0] and staves[0][0]:
            first = staves[0][0][0]
            first.marks.insert(0, f'<direction placement="above"><direction-type><words font-style="italic">'
                                  f'{ps.technique}</words></direction-type></direction>')
        out.append(f'<part id="{ps.pid}">')
        # which measures are empty (for multi-measure rests)
        empty = []
        for m in range(total_bars):
            m0, m1 = m * bar, (m + 1) * bar
            has = any(e.start < m1 and e.end > m0 for vs in staves for v in vs for e in v)
            empty.append(not has)
        runs = {}
        if multirest:
            m = 0
            while m < total_bars:
                if empty[m] and m * bar not in rehearsal:
                    k = m
                    while (k + 1 < total_bars and empty[k + 1] and (k + 1) * bar not in tmarks
                           and (k + 1) * bar not in rehearsal and (k + 1) * bar not in keys):
                        k += 1
                    if k > m:
                        runs[m] = k - m + 1
                    m = k + 1
                else:
                    m += 1
        for m in range(total_bars):
            m0 = m * bar
            out.append(f'<measure number="{m + 1}">')
            if m == 0:
                tr = ''
                if semis and not ps.drums:
                    oct_ch = -1 if semis == 12 else (1 if semis == -12 else 0)
                    chrom = -semis if abs(semis) != 12 else 0
                    diat = {2: -1, 7: -4}.get(semis, 0)
                    tr = (f'<transpose><diatonic>{diat}</diatonic><chromatic>{chrom}</chromatic>'
                          f'{"<octave-change>%d</octave-change>" % oct_ch if oct_ch else ""}</transpose>')
                clefs = ''
                if ps.inst.clef == 'grand':
                    clefs = _clef_xml('treble', 1) + _clef_xml('bass', 2)
                else:
                    clefs = _clef_xml(ps.inst.clef if not ps.drums else 'perc')
                key = '' if ps.drums else f'<key><fifths>{fifths}</fifths><mode>{mode if semis == 0 else "major"}</mode></key>'
                stv = f'<staves>{nstaves}</staves>' if nstaves > 1 else ''
                out.append(f'<attributes><divisions>{DIV}</divisions>{key}<time><beats>{beats_per_bar}</beats>'
                           f'<beat-type>4</beat-type></time>{stv}{clefs}{tr}</attributes>')
            if m0 in keys and not ps.drums:
                kf, km = keys[m0]
                fifths = transpose_fifths(kf, semis)
                kmode = km if semis == 0 else 'major'
                sp = Speller(fifths, kmode)
                out.append(f'<attributes><key><fifths>{fifths}</fifths><mode>{kmode}</mode></key></attributes>')
            if m in runs:
                out.append(f'<attributes><measure-style><multiple-rest>{runs[m]}</multiple-rest></measure-style>'
                           f'</attributes>')
            if m0 in rehearsal and (ps is parts[0]):
                out.append(f'<direction placement="above"><direction-type><rehearsal enclosure="square">'
                           f'{escape(rehearsal[m0])}</rehearsal></direction-type></direction>')
            if ps is parts[0]:
                for t, bpm in tmarks.items():
                    if m0 <= t < m0 + bar:
                        off = t - m0
                        fw = f'<offset>{off}</offset>' if off else ''
                        out.append(f'<direction placement="above"><direction-type><metronome parentheses="no">'
                                   f'<beat-unit>quarter</beat-unit><per-minute>{bpm}</per-minute></metronome>'
                                   f'</direction-type>{fw}<sound tempo="{bpm}"/></direction>')
            first_written = True
            for si, vs in enumerate(staves):
                staff_no = si + 1 if nstaves > 1 else None
                rendered = []
                for v in vs:
                    if any(e.start < m0 + bar and e.end > m0 for e in v):
                        rendered.append(v)
                if not rendered:
                    rendered = [[]]
                for vi, v in enumerate(rendered):
                    vno = vi + 1 + 4 * si
                    xml, dur = _render_voice(v, m0, bar, vno, staff_no, sp, ps, False)
                    if not first_written:
                        out.append(f'<backup><duration>{bar}</duration></backup>')
                    out.append(xml)
                    first_written = False
            if m == total_bars - 1:
                out.append('<barline location="right"><bar-style>light-heavy</bar-style></barline>')
            out.append('</measure>')
        out.append('</part>')
    out.append('</score-partwise>')
    return '\n'.join(out)

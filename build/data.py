"""Reads one arrangement from an anthem-orchestra checkout: notes, meter, key, tempo, sections, facts, velocities."""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import mido

from engrave import DIV, Event, PartSpec, _snap, dynamics_marks, find_rolls, key_fifths, let_ring, quantise, voices
from instruments import BY_SLUG, Instrument, instrument_of, is_tremolo, technique_text


def slugify(text: str) -> str:
    t = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')


def load_anthems(orch: Path) -> dict:
    src = (orch / 'work/youtube/anthems.py').read_text(encoding='utf-8')
    env: dict = {}
    exec(compile(src, 'anthems.py', 'exec'), {'__builtins__': {'dict': dict}}, env)  # our own data file
    return env['ANTHEMS']


def load_descriptions(orch: Path) -> dict[str, dict]:
    """Overview row per arrangement from DESCRIPTIONS.md: key, length, parts, character, leading colours."""
    out = {}
    text = (orch / 'output/orchestra/DESCRIPTIONS.md').read_text(encoding='utf-8')
    for line in text.splitlines():
        m = re.match(r'\| \[([^\]]+)\]\(#[^)]*\) \| ([^|]+) \| ([^|]+) \| (\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|', line)
        if m:
            name, keymeter, length, parts, character, leads, left = (g.strip() for g in m.groups())
            out[name] = dict(key_meter=keymeter, length=length, parts=int(parts), character=character,
                             leads=leads, left_out=left)
    # the measured tempo per slug: "about N BPM" lines in the youtube copy are built from these facts
    return out


@dataclass
class Part:
    track: dict
    inst: Instrument
    qnotes: list           # (start, end, pitch) in divisions
    vel: dict              # (start, pitch) -> velocity
    export_index: int      # track index in the exported MIDI (for the part MIDI)
    src: list = field(default_factory=list)    # the notes quantised (rolls merged), in qnotes order
    rolls: set = field(default_factory=set)    # (start division, pitch) of notes that are rolls


@dataclass
class Arrangement:
    slug: str              # anthem-orchestra slug (argentina-anthem)
    country_slug: str      # site slug (argentina)
    meta: dict             # anthems.py entry
    desc: dict             # DESCRIPTIONS overview row
    song: dict
    beats_per_bar: int
    total_bars: int
    key: str
    fifths: int
    mode: str
    tempo: list
    parts: list[Part] = field(default_factory=list)
    rehearsal: dict = field(default_factory=dict)
    keys: dict = field(default_factory=dict)       # key changes: division -> (fifths, mode)
    guide: list = field(default_factory=list)      # (start, end, pitch)
    lyrics: dict = field(default_factory=dict)     # guide note index -> lyric dict
    export_mid: Path | None = None
    chorus_mid: Path | None = None
    srt: Path | None = None


def _export_notes(path: Path) -> tuple[list[str], list[list[tuple[float, int, int]]], int]:
    mf = mido.MidiFile(path)
    ppq = mf.ticks_per_beat
    names, notes = [], []
    for tr in mf.tracks:
        name, t, on, ns = None, 0, {}, []
        for msg in tr:
            t += msg.time
            if msg.type == 'track_name':
                name = msg.name
            elif msg.type == 'note_on' and msg.velocity > 0:
                ns.append((t / ppq, msg.note, msg.velocity))
        names.append(name)
        notes.append(ns)
    return names, notes, ppq


def _match_velocities(track_notes: list[dict], export: list[tuple[float, int, int]]) -> dict:
    pool: dict[int, list] = {}
    for b, p, v in export:
        pool.setdefault(p, []).append([b, v, False])
    out = {}
    for n in track_notes:
        cands = pool.get(n['pitch'], [])
        best = None
        for c in cands:
            if not c[2] and abs(c[0] - n['on']) < 0.4 and (best is None or abs(c[0] - n['on']) < abs(best[0] - n['on'])):
                best = c
        if best:
            best[2] = True
            out[(round(n['on'], 4), n['pitch'])] = best[1]
    return out


def load(orch: Path, slug: str, anthems: dict, descs: dict) -> Arrangement:
    w = orch / 'work' / slug
    song = json.loads((w / 'song.json').read_text())
    ana = json.loads((w / 'analysis.json').read_text())
    meta = anthems[slug]
    c = meta['country']
    plain = re.sub(r'\s*\(.*?\)', '', re.sub(r'^the\s+', '', c, flags=re.I))
    desc = descs.get(c) or descs.get(plain) or next((v for k, v in descs.items() if plain.lower() in k.lower()), {})
    bpb = song['clock']['meter'][0]
    ks = ana.get('key_signatures') or []
    key = ks[0][1] if ks else (desc.get('key_meter', 'C major').split(' ')[0])
    fifths, mode = key_fifths(key)
    arr = Arrangement(slug=slug, country_slug=slugify(meta['country']), meta=meta, desc=desc, song=song,
                      beats_per_bar=bpb, total_bars=0, key=key, fifths=fifths, mode=mode,
                      tempo=song['clock']['tempo'])
    exp = orch / 'output/orchestra' / f'{slug}.mid'
    arr.export_mid = exp
    ch = orch / 'output/orchestra' / f'{slug}-chorus.mid'
    arr.chorus_mid = ch if ch.exists() else None
    srt = orch / 'output/orchestra' / f'{slug}.srt'
    arr.srt = srt if srt.exists() else None
    names, enotes, _ = _export_notes(exp)
    used = set()
    last_end = 0
    for t in song['tracks']:
        if not t['notes']:
            continue
        inst = instrument_of(t)
        idx = next((i for i, n in enumerate(names) if n == t['name'] and i not in used), None)
        if idx is not None:
            used.add(idx)
        vel = _match_velocities(t['notes'], enotes[idx]) if idx is not None else {}
        notes = t['notes']
        if t.get('drums') or inst.slug == 'timpani':
            notes = find_rolls(notes)
        src = sorted(notes, key=lambda n: (n['on'], n['pitch']))
        q = quantise(src, drums=bool(t.get('drums')))
        rolls = {(_snap(n['on']), n['pitch']) for n in src if n.get('roll')}
        arr.parts.append(Part(track=t, inst=inst, qnotes=q, vel=vel, export_index=idx, src=src, rolls=rolls))
        last_end = max(last_end, max(e for _s, e, _p in q))
    bar = bpb * DIV
    arr.total_bars = max(song['clock']['bars'], -(-last_end // bar))
    # rehearsal letters at section starts (not the first)
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    k = 0
    for sec in song['sections']:
        if sec['start_bar'] > 0:
            arr.rehearsal[sec['start_bar'] * bar] = letters[k % 26] + ('' if k < 26 else str(k // 26))
            k += 1
    # guide melody and lyrics
    g = json.loads((w / 'guide.json').read_text())['notes']
    # key changes: a source bar -> the arrangement bar through the tune (the i-th source note is the i-th guide note)
    src_mel = sorted(ana['melody']['notes'], key=lambda n: (n[0], n[2]))
    gsorted = sorted(g, key=lambda n: (n[0], n[2]))
    for kbar, kname in ks[1:]:
        if len(src_mel) != len(gsorted):
            break
        start = (kbar - 1) * bpb
        i = next((k for k, n in enumerate(src_mel) if n[0] >= start - 1e-6), None)
        if i is None:
            continue
        at = gsorted[i][0] - (src_mel[i][0] - start)       # arrangement beat of that source barline
        mbar = round(at / bpb)
        arr.keys[mbar * bar] = key_fifths(kname)
    gnotes = [dict(on=n[0], duration=n[1], pitch=n[2]) for n in g]
    arr.guide = quantise(gnotes)
    lm = w / 'lyrics-map.json'
    if lm.exists():
        order = sorted(range(len(gnotes)), key=lambda i: (gnotes[i]['on'], gnotes[i]['pitch']))
        pos = {orig: k for k, orig in enumerate(order)}  # guide index -> quantised index
        lines = json.loads(lm.read_text())['lines']
        for line in lines:
            sylls = line['syllables']
            for si, s in enumerate(sylls):
                if not s.get('notes'):
                    continue
                prev_end = si == 0 or sylls[si - 1].get('word_end', True)
                if prev_end and s['word_end']:
                    syl = 'single'
                elif prev_end:
                    syl = 'begin'
                elif s['word_end']:
                    syl = 'end'
                else:
                    syl = 'middle'
                first = pos.get(s['notes'][0])
                if first is not None:
                    arr.lyrics[first] = dict(text=s['text'], syllabic=syl, extend=len(s['notes']) > 1)
    return arr


ABBR = {'piccolo': 'Picc.', 'flute': 'Fl.', 'oboe': 'Ob.', 'clarinet': 'Cl.', 'bassoon': 'Bsn.', 'horn': 'Hn.',
        'trumpet': 'Tpt.', 'trombone': 'Tbn.', 'tuba': 'Tba.', 'timpani': 'Timp.', 'percussion': 'Perc.', 'harp': 'Hp.',
        'piano': 'Pno.', 'choir': 'Ch.', 'violin': 'Vln.', 'viola': 'Vla.', 'cello': 'Vc.', 'double-bass': 'Cb.'}


def abbreviation(name: str, inst: Instrument) -> str:
    """The staff name on the second and later systems: 'Violins II' -> 'Vln. II', 'Horns (tune)' -> 'Hn. (tune)',
    'Tambourine' -> 'Tamb.' (a percussion part named after its instrument)."""
    base = ABBR.get(inst.slug, name[:4] + '.')
    m = re.search(r'\b(I{1,3}|IV|\d)$', name)
    extra = m.group(1) if m else ''
    paren = re.search(r'(\([^)]*\))', name)
    if inst.slug == 'percussion' and not re.search(r'percussion', name, re.I):
        base = re.sub(r'\s*\(.*?\)', '', name)
        known = {'snare drum': 'S.D.', 'bass drum': 'B.D.', 'cymbals': 'Cym.', 'cymbal': 'Cym.', 'triangle': 'Tri.',
                 'tambourine': 'Tamb.', 'glockenspiel': 'Glk.', 'tubular bells': 'T.B.', 'bells': 'Bells', 'gong': 'Gong'}
        base = known.get(base.lower(), base if len(base) <= 6 else base[:4] + '.')
    if paren and (len(paren.group(1)) > 12 or (inst.slug == 'piano' and 'solo' in paren.group(1).lower())):
        paren = None
    return ' '.join(x for x in [base, extra, paren.group(1) if paren else ''] if x)


def part_spec(arr: Arrangement, part: Part, pid: str, name: str, written: bool = True) -> PartSpec:
    t = part.track
    drums = bool(t.get('drums'))
    ring = part.inst.slug in ('harp', 'piano', 'timpani')
    if part.inst.clef == 'grand':
        hi = [n for n in part.qnotes if n[2] >= 60]
        lo = [n for n in part.qnotes if n[2] < 60]
        staves = [voices(let_ring(hi, 0)), voices(let_ring(lo, 0))]
    else:
        q = let_ring(part.qnotes, 0) if ring else part.qnotes
        staves = [voices(q, max_voices=2)]
    for st in staves:
        for v in st:
            for ev in v:
                ev.trem = any((ev.start, p) in part.rolls for p in ev.pitches)
    abbr = abbreviation(t['name'], part.inst)
    return PartSpec(pid=pid, name=name, abbr=abbr, inst=part.inst, track=t, events_by_staff=staves,
                    written=written, drums=drums, tremolo=is_tremolo(t), technique=technique_text(t))


def part_dynamics(part: Part) -> dict[int, str]:
    rows = []
    # quantised notes were built in (on, pitch) order; velocities are keyed by the original onset
    for (s, e, p), n in zip(part.qnotes, part.src):
        rows.append((s, e, p, part.vel.get((round(n['on'], 4), n['pitch']), 0)))
    return dynamics_marks(rows)


def guide_spec(arr: Arrangement) -> PartSpec:
    evs = voices(arr.guide, max_voices=1)
    # lyrics: the quantised guide keeps note order, so the k-th note is the k-th event when no chords
    idx = {(s, p): k for k, (s, e, p) in enumerate(arr.guide)}
    for v in evs:
        for ev in v:
            k = idx.get((ev.start, ev.pitches[-1]))
            if k in arr.lyrics:
                ev.lyric = arr.lyrics[k]
    melody = Instrument('melody', 'Melody', 'Melody', 'voices', 0, 'treble')
    return PartSpec(pid='P1', name='Melody', abbr='Mel.', inst=melody, track={'name': 'Melody'},
                    events_by_staff=[evs])

"""Checks the engraving and the site.

    ~/.anthem-venv/bin/python build/check.py notes [--only argentina-anthem ...]   every engraved note vs song.json
    ~/.anthem-venv/bin/python build/check.py site                                 links, assets, JSON-LD, sitemap, PDFs

`notes` engraves each part as the build does, converts it to the MEI the site ships (build.to_mei), lets Verovio play
it back (renderToMIDI, which undoes the written transposition) and compares onset and pitch of every note with the arrangement's quantised notes. Tied continuations
are one note; a roll is one note. Any mismatch is listed.
"""
from __future__ import annotations

import base64
import io
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mido  # noqa: E402
import verovio  # noqa: E402

from build import SKIP, to_mei  # noqa: E402
from data import guide_spec, load, load_anthems, load_descriptions, part_dynamics, part_spec  # noqa: E402
from engrave import DIV, build_score  # noqa: E402

DOCS = HERE.parent / 'docs'


def played(xml: str) -> set[tuple[int, int]]:
    tk = verovio.toolkit()
    tk.setOptions({'font': 'Leland'})
    tk.loadData(xml)
    mf = mido.MidiFile(file=io.BytesIO(base64.b64decode(tk.renderToMIDI())))
    out = set()
    for tr in mf.tracks:
        t = 0
        for msg in tr:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                out.add((round(t * DIV / mf.ticks_per_beat), msg.note))
    return out


def expected(spec) -> set[tuple[int, int]]:
    out = set()
    for staff in spec.events_by_staff:
        for v in staff:
            for ev in v:
                for p in ev.pitches:
                    out.add((ev.start, p))
    return out


def check_notes(orch: Path, only: list[str] | None):
    anthems, descs = load_anthems(orch), load_descriptions(orch)
    bad = 0
    total = 0
    for slug in anthems:
        if slug in SKIP or (only and slug not in only) or not (orch / 'work' / slug / 'song.json').exists():
            continue
        arr = load(orch, slug, anthems, descs)
        common = dict(title='t', subtitle='', composer='', lyricist='', arranger='', beats_per_bar=arr.beats_per_bar,
                      total_bars=arr.total_bars, concert_fifths=arr.fifths, mode=arr.mode, tempo=[[0, 60]],
                      rehearsal={}, keys=arr.keys)
        specs = [('melody', guide_spec(arr), {})] + [(p.track['name'], part_spec(arr, p, 'P1', p.track['name']),
                                                     part_dynamics(p)) for p in arr.parts]
        miss = []
        for name, spec, dyn in specs:
            xml = build_score(parts=[spec], dynamics={'P1': dyn}, multirest=True, **common)
            got, want = played(to_mei(xml, 't', 's', 'l', 'r')), expected(spec)
            # a tremolo (roll) note is played as repeated strokes: strokes inside it are not extra notes
            rolls = [(ev.start, ev.end, set(ev.pitches)) for st in spec.events_by_staff for v in st for ev in v
                     if ev.trem or spec.tremolo]
            if spec.drums:  # Verovio plays unpitched notes at their display position: compare onsets only
                got, want = {t for t, _ in got}, {t for t, _ in want}
                got = {t for t in got if t in want or not any(a < t < b for a, b, _ in rolls)}
            else:
                got = {(t, p) for t, p in got if (t, p) in want or not any(a < t < b and p in ps for a, b, ps in rolls)}
            total += len(want)
            if got != want:
                miss.append(f'  {name}: {len(want - got)} missing, {len(got - want)} extra, e.g. '
                            f'{sorted(want - got)[:3]} / {sorted(got - want)[:3]}')
        print(f'{slug}: {len(specs)} parts', 'ok' if not miss else 'MISMATCH')
        for m in miss:
            print(m)
        bad += len(miss)
    print(f'{total} notes checked, {bad} parts with mismatches')
    return bad == 0


def check_site():
    errs = []
    pages = [p for p in sorted(DOCS.rglob('index.html')) if 'privacy' not in p.parts]
    for p in pages:
        h = p.read_text()
        for ref in re.findall(r'(?:href|src|value)="(/[^"#?]*)"', h):
            f = DOCS / ref.lstrip('/')
            if ref.endswith('/'):
                f = f / 'index.html'
            if not f.exists():
                errs.append(f'{p.relative_to(DOCS)}: broken {ref}')
        for js in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
            try:
                json.loads(js)
            except Exception as ex:
                errs.append(f'{p.relative_to(DOCS)}: JSON-LD {ex}')
        if h.count('rel="canonical"') != 1:
            errs.append(f'{p.relative_to(DOCS)}: canonical count')
        if '—' in re.sub(r'<script.*?</script>', '', h, flags=re.S):
            errs.append(f'{p.relative_to(DOCS)}: em-dash in copy')
    sm = (DOCS / 'sitemap.xml').read_text() if (DOCS / 'sitemap.xml').exists() else ''
    locs = re.findall(r'<loc>(.*?)</loc>', sm)
    n_pages = len([p for p in pages if 'name="robots" content="noindex' not in p.read_text()])
    if len(locs) != n_pages:
        errs.append(f'sitemap has {len(locs)} urls, site has {n_pages} pages')
    # the score files each page draws (and each PDF button prints), the MIDI and SoundFont files the players play
    buttons, players = 0, 0
    for p in pages:
        h = p.read_text()
        for src in set(re.findall(r'data-src="([^"]+)"', h)):
            buttons += 1
            f = DOCS / src.lstrip('/')
            if not f.exists():
                errs.append(f'{p.relative_to(DOCS)}: missing score file {src}')
            elif '<mei' not in f.read_text()[:400]:
                errs.append(f'{p.relative_to(DOCS)}: {src} is not MEI')
        m = re.search(r'<script type="application/json" id="amPlayer">(.*?)</script>', h, re.S)
        if 'id="scoreView"' in h:
            if not m:
                errs.append(f'{p.relative_to(DOCS)}: score without player data')
            else:
                d = json.loads(m.group(1))
                players += 1
                for f in [d.get('midi', '')] + d.get('sf', []):
                    if not f or not (DOCS / f.lstrip('/')).exists():
                        errs.append(f'{p.relative_to(DOCS)}: player file missing: {f!r}')
                if not d.get('sf'):
                    errs.append(f'{p.relative_to(DOCS)}: player without SoundFont files')
                if not d.get('tempo') or d['tempo'][0][:2] != [0, 0]:
                    errs.append(f'{p.relative_to(DOCS)}: tempo map does not start at beat 0')
    import pages as pg  # every anthem's country has a flag file
    for v in json.loads((HERE / 'manifest.json').read_text()).values():
        code = pg.FLAGS.get(v['country_slug'])
        if not code or not (DOCS / 'assets' / 'img' / 'flags' / f'{code}.svg').exists():
            errs.append(f'no flag for {v["country_slug"]} (FLAGS in build/pages.py, docs/assets/img/flags/)')
    if list(DOCS.rglob('*.pdf')):
        errs.append('PDF files in docs/ (they are made in the browser)')
    for f in (DOCS / 'assets' / 'js' / 'vendor' / 'spessasynth.js', DOCS / 'assets' / 'js' / 'vendor' / 'spessasynth_processor.min.js'):
        if not f.exists():
            errs.append(f'missing {f.relative_to(DOCS)} (node build/synth.mjs)')
    if list(DOCS.rglob('*.webp')):
        errs.append('page images (.webp) in docs/ (the score is drawn in the browser)')
    size = sum(f.stat().st_size for f in DOCS.rglob('*') if f.is_file())
    print(f'{len(pages)} pages, {buttons} score files, {players} pages with the player, {len(locs)} sitemap urls, '
          f'docs/ = {size / 1048576:.0f} MB')
    for e in errs:
        print(' ', e)
    print('site ok' if not errs else f'{len(errs)} problems')
    return not errs


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'notes'
    orch = Path(next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--orchestra=')),
                     str(HERE.parent.parent / 'anthem-orchestra')))
    only = sys.argv[sys.argv.index('--only') + 1:] if '--only' in sys.argv else None
    ok = check_notes(orch, only) if what == 'notes' else check_site()
    sys.exit(0 if ok else 1)

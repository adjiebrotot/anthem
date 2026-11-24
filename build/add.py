"""Add (or update) anthems on the site in one command: preflight, note check, build, loudness, site check.

    ~/.anthem-venv/bin/python build/add.py <slug> [<slug> ...] [--orchestra ../anthem-orchestra]
                                           [--soundfont <orchestra checkout>/assets/soundfont/Pawchestra.sf3]
                                           [--no-render] [--preflight]

<slug> is the anthem-orchestra slug (`indonesia-anthem`). The script stops at the first thing it cannot do by
itself and says what to add (a RIGHTS row, a FLAGS row, a flag file ...). `--preflight` only checks.
Steps: preflight -> check.py notes --only -> build.py --only (runs synth.mjs when a MIDI has no loudness yet, then
builds again) -> check.py site. A full rebuild (all pages: home cards, FAQ wording) is `build.py` with no --only.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parent
ROOT = BUILD.parent
sys.path.insert(0, str(BUILD))
PY = sys.executable

REQUIRED = ['country', 'title', 'native', 'music', 'words', 'adopted', 'language', 'about', 'orch', 'region']


def load_anthems(orch: Path) -> dict:
    spec = importlib.util.spec_from_file_location('anthems', orch / 'work' / 'youtube' / 'anthems.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ANTHEMS


def preflight(orch: Path, slugs: list[str]) -> list[str]:
    from build import country_slug
    from i18n import LANG_OF, WORDS
    from pages import FLAGS
    from rights import RIGHTS
    problems, notes = [], []
    anthems = load_anthems(orch)
    descs = (orch / 'output' / 'orchestra' / 'DESCRIPTIONS.md').read_text()
    for s in slugs:
        for f in [f'work/{s}/song.json', f'work/{s}/analysis.json', f'work/{s}/guide.json', f'output/orchestra/{s}.mid']:
            if not (orch / f).exists():
                problems.append(f'{s}: anthem-orchestra has no {f}')
        m = anthems.get(s)
        if not m:
            problems.append(f'{s}: no entry in anthem-orchestra work/youtube/anthems.py')
            continue
        missing = [k for k in REQUIRED if k not in m]
        if missing:
            problems.append(f'{s}: anthems.py entry lacks {", ".join(missing)}')
        plain = re.sub(r'^the\s+', '', m['country'], flags=re.I)
        if f'| [{plain}](' not in descs:
            problems.append(f'{s}: no DESCRIPTIONS.md overview row "| [{plain}](..."')
        if not (orch / 'work' / s / 'lyrics-map.json').exists():
            notes.append(f'{s}: no lyrics-map.json (the melody page will have no words)')
        if s not in RIGHTS:
            problems.append(f'{s}: add a row to RIGHTS in build/rights.py: (PD or CR, holder or None, year of the tune)')
        if s not in LANG_OF:
            notes.append(f'{s}: no LANG_OF row in build/i18n.py (fine for English; else add it, and a WORDS table)')
        elif LANG_OF[s] not in WORDS:
            problems.append(f'{s}: LANG_OF says {LANG_OF[s]!r} but WORDS has no such table')
        c = country_slug(m['country'])
        code = FLAGS.get(c)
        if not code:
            problems.append(f'{s}: add {c!r}: <iso code> to FLAGS in build/pages.py')
        elif not (ROOT / 'docs' / 'assets' / 'img' / 'flags' / f'{code}.svg').exists():
            problems.append(f'{s}: no docs/assets/img/flags/{code}.svg (npm pack flag-icons@7.5.0, flags/4x3/{code}.svg)')
    for n in notes:
        print('note:', n)
    return problems


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    print('$', ' '.join(cmd), flush=True)
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slugs', nargs='+')
    ap.add_argument('--orchestra', default=str(ROOT.parent / 'anthem-orchestra'))
    ap.add_argument('--soundfont', default=str(ROOT.parent / 'orchestra' / 'assets' / 'soundfont' / 'Pawchestra.sf3'))
    ap.add_argument('--no-render', action='store_true')
    ap.add_argument('--preflight', action='store_true', help='only check what is missing')
    a = ap.parse_args()
    orch = Path(a.orchestra).resolve()

    problems = preflight(orch, a.slugs)
    if problems:
        print('\n'.join(['', 'Fix first:'] + [f'  - {p}' for p in problems]))
        sys.exit(1)
    print('preflight ok')
    if a.preflight:
        return

    r = run([PY, 'build/check.py', 'notes', '--orchestra', str(orch), '--only', *a.slugs])
    print(r.stdout[-600:], r.stderr[-600:])
    if r.returncode or ' 0 parts with mismatches' not in r.stdout:
        sys.exit('notes check failed: the engraving does not match the arrangement')

    build = [PY, 'build/build.py', '--orchestra', str(orch), '--only', *a.slugs] + (['--no-render'] if a.no_render else [])
    for attempt in range(2):
        r = run(build)
        out = r.stdout + r.stderr
        if r.returncode == 0:
            break
        if 'no loudness for this MIDI yet' in out and attempt == 0:
            if not Path(a.soundfont).exists():
                sys.exit(f'{a.soundfont} not found: git clone --depth 1 https://github.com/adjiebrotot/orchestra '
                         f'{ROOT.parent / "orchestra"} (or pass --soundfont)')
            s = run(['node', 'build/synth.mjs', '--soundfont', a.soundfont])
            print(s.stdout[-400:], s.stderr[-400:])
            if s.returncode:
                sys.exit('synth.mjs failed (run `cd build && npm install` once)')
            continue
        print(out[-2000:])
        sys.exit('build failed')
    print(r.stdout[-400:])

    r = run([PY, 'build/check.py', 'site'])
    print(r.stdout[-1500:], r.stderr[-800:])
    if r.returncode or 'site ok' not in r.stdout:
        sys.exit('site check failed')
    print('done: open the new pages in a browser (python3 -m http.server -d docs 8765), then commit docs/ and build/')


if __name__ == '__main__':
    main()

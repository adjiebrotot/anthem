"""The orchestra recording the score player plays: one AAC file per anthem, docs/<country>/<title>-orchestra.m4a.

    ~/.anthem-venv/bin/python build/audio.py --orchestra ../anthem-orchestra [--only asean-anthem ...] [--force]

Renders work/<slug>/song.json with anthem-orchestra's music-production skill (the same sampled banks and mix as
every preview it sends; set it up once with `bash scripts/music-setup.sh orchestra` there, plus the vcsl_world bank),
encodes master.flac to 96 kbps AAC and deletes the render and the skill's cache (build/.cache/render/<slug>, 2 to 5 GB;
anthem-orchestra's own work/<slug>/renders is never touched). The render's composition.mid is the
exported MIDI note for note, so the page syncs the recording to the score through that MIDI's tempo map.
An anthem whose file is already in docs/ is skipped unless --force. About 100 s per anthem.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from build import CACHE, DOCS, SKIP, country_slug  # noqa: E402
from data import load_anthems, slugify  # noqa: E402

MUSIC = Path.home() / '.music-skill'


def audio_path(meta: dict) -> Path:
    return DOCS / country_slug(meta['country']) / f"{slugify(meta['title'].split('(')[0])}-orchestra.m4a"


def render(orch: Path, slug: str, out: Path):
    work = CACHE / 'render' / slug       # ours alone: the skill puts its cache beside the output folder
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    folder = work / 'site_audio'
    log = work / 'site_audio.log'
    py = MUSIC / '.venv' / 'bin' / 'python'
    studio = orch / '.claude/skills/music-production/scripts/studio.py'
    with log.open('w') as f:
        r = subprocess.run([str(py), str(studio), 'render', str(orch / 'work' / slug / 'song.json'), '--config',
                            str(MUSIC / 'config.json'), '--output', str(folder)], stdout=f, stderr=subprocess.STDOUT)
    if r.returncode or not (folder / 'master.flac').exists():
        tail = log.read_text()[-300:]
        shutil.rmtree(work)
        raise RuntimeError(f'render failed: {tail}')
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix('.tmp.m4a')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(folder / 'master.flac'), '-c:a', 'aac', '-b:a', '96k',
                    '-movflags', '+faststart', '-map_metadata', '-1', str(tmp)], check=True)
    tmp.replace(out)
    shutil.rmtree(work)      # the render and the skill's cache beside it (renders/cache, several GB)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--orchestra', default=str(HERE.parent.parent / 'anthem-orchestra'))
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    orch = Path(a.orchestra)
    anthems = load_anthems(orch)
    failed = []
    for slug, meta in anthems.items():
        if slug in SKIP or not (orch / 'work' / slug / 'song.json').exists() or (a.only and slug not in a.only):
            continue
        out = audio_path(meta)
        if out.exists() and not a.force:
            continue
        print('rendering', slug, flush=True)
        try:
            render(orch, slug, out)
            print('  ok', out.relative_to(DOCS), f'{out.stat().st_size / 1048576:.1f} MB', flush=True)
        except Exception as ex:  # one failure does not stop the others
            print('  FAILED', slug, ex, flush=True)
            failed.append(slug)
    print('done' if not failed else f'failed: {" ".join(failed)}', flush=True)


if __name__ == '__main__':
    main()

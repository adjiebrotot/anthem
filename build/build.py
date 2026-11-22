"""Builds anthem.adjiebrotots.com (docs/) from an anthem-orchestra checkout.

    ~/.anthem-venv/bin/python build/build.py --orchestra ../anthem-orchestra [--only argentina-anthem ...]

Per arrangement: MusicXML per part (written pitch), the melody with lyrics and the full score (concert pitch);
Verovio SVG pages; page images (WebP) and watermarked PDFs (node build/render.cjs, Playwright Chromium); one-track
MIDI per part; the HTML pages (pages.py). The anthem-orchestra checkout is only read.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mido  # noqa: E402
import verovio  # noqa: E402
from PIL import Image  # noqa: E402

from data import Arrangement, Part, guide_spec, load, load_anthems, load_descriptions, part_dynamics, part_spec, slugify  # noqa: E402
from engrave import build_score  # noqa: E402
from instruments import BY_SLUG, Instrument  # noqa: E402

ROOT = HERE.parent
DOCS = ROOT / 'docs'
CACHE = HERE / '.cache'
SITE = 'https://anthem.adjiebrotots.com'
ARRANGER = 'Arr. Anthem Madness (adjiebrotot)'
SKIP = {'friendly-father'}          # not an anthem


@dataclass
class ScoreFile:
    key: str                 # violin-1, melody, full-score
    label: str               # "Violins I", "Melody", "Full score"
    pages: list = field(default_factory=list)      # site paths of the page images
    pdf: str = ''            # file name the browser saves the PDF as (made on click from the page images)
    footer: str = ''         # the PDF's footer line
    mid: str = ''            # site path
    transpose_name: str = ''


@dataclass
class InstPage:
    inst: Instrument
    parts: list = field(default_factory=list)       # ScoreFile


@dataclass
class Built:
    arr: Arrangement
    country: str             # site slug
    title_slug: str
    melody: ScoreFile | None = None
    full: ScoreFile | None = None
    insts: list = field(default_factory=list)       # InstPage in score order
    orchestra_mid: str = ''
    chorus_mid: str = ''
    pages_total: int = 0


def country_slug(country: str) -> str:
    c = re.sub(r'^the\s+', '', country, flags=re.I)
    c = re.sub(r'\s*\(.*?\)', '', c)
    return slugify(c)


def part_key(inst: Instrument, name: str, taken: set) -> str:
    """'Violins I' -> violin-1, 'Cellos (tune)' -> cello-tune, 'Horns' -> horn."""
    words = slugify(name).split('-')
    roman = {'i': '1', 'ii': '2', 'iii': '3', 'iv': '4'}
    inst_words = set(inst.slug.split('-')) | {inst.slug + 's', 'violins', 'violas', 'cellos', 'basses', 'double',
                                               'flutes', 'oboes', 'clarinets', 'bassoons', 'horns', 'trumpets',
                                               'trombones', 'tubas', 'harps', 'pianos', 'french', 'bass'}
    rest = [roman.get(w, w) for w in words if w not in inst_words]
    key = '-'.join([inst.slug] + rest)
    k, n = key, 2
    while k in taken:
        k = f'{key}-{n}'
        n += 1
    taken.add(k)
    return k


def verovio_pages(xml: str, full: bool = False) -> list[str]:
    tk = verovio.toolkit()
    opts = {'pageWidth': 2100, 'pageHeight': 2970, 'scale': 28 if full else 40, 'font': 'Leland',
            'footer': 'none', 'header': 'auto', 'adjustPageHeight': False, 'svgViewBox': True,
            'svgRemoveXlink': True, 'pageMarginTop': 80, 'pageMarginBottom': 110, 'pageMarginLeft': 90,
            'pageMarginRight': 90, 'spacingSystem': 14 if full else 10}
    if full:
        opts.update({'condense': 'auto', 'condenseFirstPage': False})
    tk.setOptions(opts)
    if not tk.loadData(xml):
        raise RuntimeError('verovio could not read the MusicXML: ' + tk.getLog()[:400])
    return [tk.renderToSVG(i) for i in range(1, tk.getPageCount() + 1)]


def write_part_midi(src: Path, track_index: int, out: Path, name: str):
    """The exported MIDI's conductor track (title, tempo map, meter, key) plus one part's track."""
    mf = mido.MidiFile(src)
    new = mido.MidiFile(type=1, ticks_per_beat=mf.ticks_per_beat)
    new.tracks.append(mido.MidiTrack(msg for msg in mf.tracks[0] if msg.is_meta))
    new.tracks.append(mido.MidiTrack(msg.copy(name=name) if msg.type == 'track_name' else msg
                                     for msg in mf.tracks[track_index]))
    new.save(out)


def build_one(orch: Path, slug: str, anthems: dict, descs: dict, jobs: list) -> Built:
    arr = load(orch, slug, anthems, descs)
    m = arr.meta
    country = country_slug(m['country'])
    title_slug = slugify(m['title'].split('(')[0])
    b = Built(arr=arr, country=country, title_slug=title_slug)
    out = DOCS / country
    cache = CACHE / country
    if cache.exists():
        shutil.rmtree(cache)
    cache.mkdir(parents=True)
    from pages import kind
    # the composer goes on the subtitle line: a long name beside the title collides with it on the page
    common = dict(title=m['title'], subtitle=f"{kind(slug)} of {m['country']} \u00b7 Music: {m['music']}",
                  composer='', lyricist='', arranger=ARRANGER,
                  beats_per_bar=arr.beats_per_bar, total_bars=arr.total_bars, concert_fifths=arr.fifths,
                  mode=arr.mode, tempo=arr.tempo, rehearsal=arr.rehearsal, keys=arr.keys)

    def score(key: str, label: str, xml: str, folder: Path, url: str, footer: str, full: bool = False) -> ScoreFile:
        folder.mkdir(parents=True, exist_ok=True)
        (cache / f'{key}.musicxml').write_text(xml)
        svgs = verovio_pages(xml, full)
        sf = ScoreFile(key=key, label=label)
        svg_paths, pngs = [], []
        for i, s in enumerate(svgs, 1):
            p = cache / f'{key}-{i}.svg'
            p.write_text(s)
            svg_paths.append(str(p))
            pngs.append(str(cache / f'{key}-{i}.png'))
            sf.pages.append(f'{url}img/{key}-{i}.webp')
        sf.pdf = f'{title_slug}-{key}-sheet-music.pdf'
        sf.footer = footer
        jobs.append(dict(svgs=svg_paths, png=pngs,
                         webp=[str(folder / 'img' / f'{key}-{i}.webp') for i in range(1, len(svgs) + 1)]))
        b.pages_total += len(svgs)
        return sf

    # melody (country page)
    murl = f'/{country}/'
    xml = build_score(parts=[guide_spec(arr)], dynamics={}, multirest=True, header_part_name='Melody', **common)
    b.melody = score('melody', 'Melody', xml, out, murl, f'Free download: anthem.adjiebrotots.com/{country}/')
    gm = orch / 'work' / slug / 'guide.mid'
    if gm.exists():
        shutil.copy(gm, out / f'{title_slug}-melody.mid')
        b.melody.mid = f'{murl}{title_slug}-melody.mid'
    shutil.copy(arr.export_mid, out / f'{title_slug}-orchestra.mid')
    b.orchestra_mid = f'{murl}{title_slug}-orchestra.mid'
    if arr.chorus_mid:
        shutil.copy(arr.chorus_mid, out / f'{title_slug}-orchestra-chorus.mid')
        b.chorus_mid = f'{murl}{title_slug}-orchestra-chorus.mid'

    # parts by instrument page, in score order
    groups: dict[str, InstPage] = {}
    taken: set = set()
    specs_full = []
    for i, part in enumerate(arr.parts):
        inst = part.inst
        page = groups.setdefault(inst.slug, InstPage(inst=inst))
        key = part_key(inst, part.track['name'], taken)
        label = part.track['name'] + (f' ({inst.transpose_name})' if inst.transpose_name else '')
        ps = part_spec(arr, part, 'P1', part.track['name'])
        dyn = part_dynamics(part)
        xml = build_score(parts=[ps], dynamics={'P1': dyn}, multirest=True, header_part_name=label, **common)
        url = f'/{country}/{inst.slug}/'
        sf = score(key, part.track['name'], xml, out / inst.slug, url,
                   f'Free download: anthem.adjiebrotots.com/{country}/{inst.slug}/')
        sf.transpose_name = inst.transpose_name
        mid = out / inst.slug / f'{title_slug}-{key}.mid'
        if part.export_index is not None:
            write_part_midi(arr.export_mid, part.export_index, mid, part.track['name'])
            sf.mid = f'{url}{mid.name}'
        page.parts.append(sf)
        fs = part_spec(arr, part, f'P{len(specs_full) + 1}', part.track['name'], written=False)
        specs_full.append((fs, dyn))
    b.insts = sorted(groups.values(), key=lambda g: g.inst.order)
    # full score: every part, concert pitch (octave transposers stay in their octave), in score order
    order = sorted(range(len(specs_full)), key=lambda k: specs_full[k][0].inst.order)
    parts = []
    dyns = {}
    for n, k in enumerate(order, 1):
        ps, dyn = specs_full[k]
        ps.pid = f'P{n}'
        parts.append(ps)
        dyns[ps.pid] = dyn
    xml = build_score(parts=parts, dynamics=dyns, multirest=False, header_part_name='Full score (concert pitch)',
                      **common)
    b.full = score('full-score', 'Full score', xml, out / 'full-score', f'/{country}/full-score/',
                   f'Free download: anthem.adjiebrotots.com/{country}/full-score/', full=True)
    return b


def finish_jobs(jobs: list, render: bool = True):
    if not jobs:
        return
    if not render:  # pages only: the page images must already be there
        missing = [w for job in jobs for w in job['webp'] if not Path(w).exists()]
        if missing:
            raise SystemExit(f'--no-render but {len(missing)} page images are missing, e.g. {missing[0]}')
        return
    jf = CACHE / 'jobs.json'
    jf.write_text(json.dumps(jobs))
    subprocess.run(['node', str(HERE / 'render.cjs'), str(jf)], check=True)
    for job in jobs:
        for png, webp in zip(job['png'], job['webp']):
            Path(webp).parent.mkdir(parents=True, exist_ok=True)
            im = Image.open(png).convert('L')
            im.save(webp, 'WEBP', quality=62, method=6)
            Path(png).unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--orchestra', default=str(ROOT.parent / 'anthem-orchestra'))
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--no-render', action='store_true',
                    help='rewrite the pages only, keeping the page images (Verovio still counts the pages)')
    a = ap.parse_args()
    orch = Path(a.orchestra)
    anthems = load_anthems(orch)
    descs = load_descriptions(orch)
    slugs = [s for s in anthems if s not in SKIP and (orch / 'work' / s / 'song.json').exists()]
    if a.only:
        slugs = [s for s in slugs if s in a.only]
    import pages
    built = []
    for slug in slugs:
        jobs: list = []
        print('building', slug, flush=True)
        b = build_one(orch, slug, anthems, descs, jobs)
        finish_jobs(jobs, render=not a.no_render)
        built.append(b)
    all_built = pages.registry(built, anthems, orch, slugs_all=[s for s in anthems if s not in SKIP])
    pages.write_all(built, all_built)
    import sitefiles  # home, 404, sitemap, robots, llms.txt, ads.txt, CNAME
    sitefiles.main()


if __name__ == '__main__':
    main()

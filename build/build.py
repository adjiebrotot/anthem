"""Builds anthem.adjiebrotots.com (docs/) from an anthem-orchestra checkout.

    ~/.anthem-venv/bin/python build/build.py --orchestra ../anthem-orchestra [--only argentina-anthem ...]

Per arrangement: MusicXML per part (written pitch), the melody with lyrics and the full score (concert pitch), each
converted by Verovio to a compact MEI file that the page draws in the reader's browser (docs/assets/js/score.js,
the same Verovio version) and plays along with the orchestra MIDI in a SoundFont synth (build/synth.mjs); the MIDI's
tempo map that syncs the two and the presets it needs; one-track MIDI per part; one share image per anthem; the HTML
pages (pages.py).
The anthem-orchestra checkout is only read.
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
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mido  # noqa: E402
import verovio  # noqa: E402
from PIL import Image  # noqa: E402

from data import Arrangement, guide_spec, load, load_anthems, load_descriptions, part_dynamics, part_spec, slugify  # noqa: E402
from engrave import build_score  # noqa: E402
from instruments import Instrument  # noqa: E402

ROOT = HERE.parent
DOCS = ROOT / 'docs'
CACHE = HERE / '.cache'
SITE = 'https://anthem.adjiebrotots.com'
ARRANGER = 'Arr. Anthem Madness (adjiebrotot)'
SKIP = {'friendly-father'}          # not an anthem
VEROVIO = verovio.toolkit().getVersion().split('-')[0]   # score.js loads this version of Verovio's toolkit


def print_options(full: bool) -> dict:
    """A4 pages for the PDF (10 units per mm); score.js PRINT uses the same, so the page counts on the buttons hold."""
    o = {'pageWidth': 2100, 'pageHeight': 2970, 'scale': 28 if full else 40, 'font': 'Leland', 'footer': 'none',
         'header': 'auto', 'adjustPageHeight': True, 'svgViewBox': True, 'svgRemoveXlink': True,
         'pageMarginTop': 80, 'pageMarginBottom': 140, 'pageMarginLeft': 90, 'pageMarginRight': 90,
         'spacingSystem': 14 if full else 10}
    if full:
        o.update({'condense': 'auto', 'condenseFirstPage': False})
    return o


@dataclass
class ScoreFile:
    key: str                 # violin-1, melody, full-score
    label: str               # "Violins I", "Melody", "Full score"
    src: str = ''            # site path of the MEI file the page draws
    pages: int = 0           # A4 pages of its PDF
    full: bool = False
    print: dict = field(default_factory=dict)      # print options beyond print_options() (score.js data-print)
    pdf: str = ''            # file name the browser saves the PDF as (made on click, see score.js)
    footer: str = ''         # the PDF's footer line
    mid: str = ''            # site path
    transpose_name: str = ''
    channel: int | None = None    # the part's synth channel in the orchestra MIDI (port * 16 + channel)


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
    melody_mid: str = ''
    player: dict = field(default_factory=dict)     # what score.js plays: midi, sf (preset files), tempo, length
    image: str = ''          # share image (og:image, sitemap)


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


def to_mei(xml: str, title: str, subtitle: str, left: str, right: str, labels: bool = True) -> str:
    """MusicXML -> compact MEI (no ids: Verovio makes them on load) with a page header Verovio sets properly:
    a large title over the subtitle, the part on the left and the arranger on the right, on a line of their own."""
    tk = verovio.toolkit()
    tk.setOptions({'font': 'Leland'})
    if not tk.loadData(xml):
        raise RuntimeError('verovio could not read the MusicXML: ' + tk.getLog()[:400])
    mei = tk.getMEI({'removeIds': True})
    head = ('<pgHead func="first">'
            f'<rend halign="center" valign="top"><rend fontsize="x-large">{escape(title)}</rend>'
            + (f'<lb/><rend fontsize="small">{escape(subtitle)}</rend>' if subtitle else '') + '</rend>'
            f'<rend halign="left" valign="bottom"><rend fontsize="small" fontstyle="italic">{escape(left)}</rend></rend>'
            f'<rend halign="right" valign="bottom"><rend fontsize="small">{escape(right)}</rend></rend></pgHead>')
    mei, n = re.subn(r'<pgHead\b.*?</pgHead>', lambda _m: head, mei, count=1, flags=re.S)
    if n != 1:
        raise RuntimeError('no page header in the MEI')
    mei = re.sub(r'>\s+<', '><', mei)
    if not labels:     # one part: the header names it, so no name before every line
        mei = re.sub(r'<label(Abbr)?\b[^>]*>.*?</label(Abbr)?>', '', mei, flags=re.S)
    return pitched_key_changes(mei)


def pitched_key_changes(mei: str) -> str:
    """Verovio turns a key change of the pitched parts into one for the whole score, percussion staves included:
    name the pitched staves instead (each staffDef with its new keySig)."""
    first = re.search(r'<scoreDef\b.*?</scoreDef>', mei, re.S)
    if not first:
        return mei
    defs = re.findall(r'<staffDef\b[^>]*\bn="(\d+)"[^>]*>(.*?)</staffDef>', first.group(0), re.S)
    perc = {n for n, body in defs if 'shape="perc"' in body}
    if not perc:
        return mei
    pitched = [n for n, _b in defs if n not in perc]

    def change(m):
        ks = m.group(1)
        return ('<scoreDef><staffGrp>' + ''.join(f'<staffDef n="{n}">{ks}</staffDef>' for n in pitched)
                + '</staffGrp></scoreDef>')
    return mei[:first.end()] + re.sub(r'<scoreDef>(<keySig\b[^>]*/>)</scoreDef>', change, mei[first.end():])


def a4_pages(mei: str, full: bool) -> tuple[int, str, dict]:
    """Number of A4 pages, the first page's SVG and the print options that differ from print_options().
    A full score's system (every staff on the first page) can be taller than A4: the staves close up until every
    page fits, and only if even that fails are empty staves hidden on the first page too. A page fits when its
    content and both margins are within A4 (adjustPageHeight: the SVG is as tall as what is on it); the bottom
    margin keeps the PDF footer clear of the notes. Verovio's breaks can still overfill a page: score.js then scales
    that page down to fit."""
    tk = verovio.toolkit()
    if not tk.loadData(mei):
        raise RuntimeError('verovio could not read its own MEI')
    tries = [{}]
    if full:
        tries = [{'spacingStaff': n} for n in (12, 10, 8, 7, 6, 5, 4)] + [{'spacingStaff': 6, 'condenseFirstPage': True}]
    for extra in tries:
        o = print_options(full)
        o.update(extra)
        tk.setOptions(o)
        tk.redoLayout()
        limit = o['pageHeight'] * o['scale'] / 100 + 1
        heights = [float(re.search(r'viewBox="0 0 [\d.]+ ([\d.]+)"', tk.renderToSVG(i)).group(1))
                   for i in range(1, tk.getPageCount() + 1)]
        if max(heights) <= limit:
            break
    return tk.getPageCount(), tk.renderToSVG(1), extra


def tempo_map(mid: Path) -> list:
    """[beat, second, bpm] at the start and at every tempo change of the export MIDI (the timeline the player plays)."""
    mf = mido.MidiFile(mid)
    ppq = mf.ticks_per_beat
    changes = []
    for tr in mf.tracks:
        t = 0
        for msg in tr:
            t += msg.time
            if msg.type == 'set_tempo':
                changes.append((t, msg.tempo))
    changes.sort()
    if not changes or changes[0][0] > 0:
        changes.insert(0, (0, 500000))
    out, sec, last_t, tempo = [], 0.0, 0, changes[0][1]
    for t, new in changes:
        sec += (t - last_t) / ppq * tempo / 1e6
        last_t, tempo = t, new
        if out and out[-1][0] == round(t / ppq, 4):
            out.pop()
        out.append([round(t / ppq, 4), round(sec, 4), round(60e6 / new, 3)])
    return out


def synth_channel(src: Path, track_index: int) -> int | None:
    """The channel a part plays on in the browser synth: spessasynth gives MIDI port p channels p*16 to p*16+15."""
    port, ch = 0, None
    for msg in mido.MidiFile(src).tracks[track_index]:
        if msg.type == 'midi_port':
            port = msg.port
        elif ch is None and hasattr(msg, 'channel'):
            ch = msg.channel
    return None if ch is None else port * 16 + ch


def write_part_midi(src: Path, track_index: int, out: Path, name: str):
    """The exported MIDI's conductor track (title, tempo map, meter, key) plus one part's track."""
    mf = mido.MidiFile(src)
    new = mido.MidiFile(type=1, ticks_per_beat=mf.ticks_per_beat)
    new.tracks.append(mido.MidiTrack(msg for msg in mf.tracks[0] if msg.is_meta))
    new.tracks.append(mido.MidiTrack(msg.copy(name=name) if msg.type == 'track_name' else msg
                                     for msg in mf.tracks[track_index]))
    new.save(out)


SF_INDEX = DOCS / 'assets' / 'sf' / 'index.json'
LOUDNESS = DOCS / 'assets' / 'sf' / 'loudness.json'
TARGET_LUFS = -16          # the orchestra app's level (AES TD1008); the page's limiter catches the peaks above


def gain_db(site_path: str, mid: Path) -> float:
    """The gain that brings the synth's rendering of this MIDI to TARGET_LUFS (loudness.json, build/synth.mjs)."""
    import hashlib
    row = json.loads(LOUDNESS.read_text()).get(site_path)
    if not row or row['hash'] != hashlib.sha256(mid.read_bytes()).hexdigest()[:16]:
        raise SystemExit(f'{site_path}: no loudness for this MIDI yet: run node build/synth.mjs')
    return round(max(0.0, min(20.0, TARGET_LUFS - row['lufs'])), 1)


def presets(mid: Path) -> list[str]:
    """The SoundFont files (build/synth.mjs) the MIDI plays: (bank, program) of every note, bank 128 on channel 10."""
    have = {(e['bank'], e['program']): e['file'] for e in json.loads(SF_INDEX.read_text())}
    need = set()
    for tr in mido.MidiFile(mid).tracks:
        prog, bank = {}, {}
        for msg in tr:
            if msg.type == 'program_change':
                prog[msg.channel] = msg.program
            elif msg.type == 'control_change' and msg.control == 0:
                bank[msg.channel] = msg.value
            elif msg.type == 'note_on' and msg.velocity:
                ch = msg.channel
                need.add((128, prog.get(ch, 0)) if ch == 9 else (bank.get(ch, 0), prog.get(ch, 0)))
    files = []
    for b, p in sorted(need):
        f = have.get((b, p)) or have.get((128, 0) if b == 128 else (0, p))
        if not f:
            raise SystemExit(f'{mid.name}: no SoundFont file for bank {b} program {p}: run node build/synth.mjs')
        files.append(f)
    return sorted(set(files))


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
    for old in list(out.rglob('*.webp')) + list(out.rglob('*.svg')) + list(out.rglob('*.m4a')):   # files of old sites
        old.unlink()
    from pages import kind
    subtitle = f"{kind(slug)} of {m['country']} · Music: {m['music']}"
    common = dict(title=m['title'], subtitle=subtitle, composer='', lyricist='', arranger=ARRANGER,
                  beats_per_bar=arr.beats_per_bar, total_bars=arr.total_bars, concert_fifths=arr.fifths,
                  mode=arr.mode, tempo=arr.tempo, rehearsal=arr.rehearsal, keys=arr.keys)

    def score(key: str, label: str, head_left: str, xml: str, folder: Path, url: str, full: bool = False) -> ScoreFile:
        folder.mkdir(parents=True, exist_ok=True)
        (cache / f'{key}.musicxml').write_text(xml)
        mei = to_mei(xml, m['title'], subtitle, head_left, ARRANGER, labels=full)
        name = f'{title_slug}-{key}.mei.xml'   # .xml: GitHub Pages gzips it (about 20x)
        (folder / name).write_text(mei)
        pages, first, extra = a4_pages(mei, full)
        if full:
            (cache / 'share.svg').write_text(first)
        return ScoreFile(key=key, label=label, src=f'{url}{name}', pages=pages, full=full, print=extra,
                         pdf=f'{title_slug}-{key}-sheet-music.pdf',
                         footer=f'Free download: anthem.adjiebrotots.com{url}')

    # MIDI of the whole arrangement (at the country folder, where they have always been)
    gm = orch / 'work' / slug / 'guide.mid'
    if gm.exists():
        shutil.copy(gm, out / f'{title_slug}-melody.mid')
        b.melody_mid = f'/{country}/{title_slug}-melody.mid'
    shutil.copy(arr.export_mid, out / f'{title_slug}-orchestra.mid')
    b.orchestra_mid = f'/{country}/{title_slug}-orchestra.mid'
    if arr.chorus_mid:
        shutil.copy(arr.chorus_mid, out / f'{title_slug}-orchestra-chorus.mid')
        b.chorus_mid = f'/{country}/{title_slug}-orchestra-chorus.mid'
    b.player = dict(midi=b.orchestra_mid, sf=presets(arr.export_mid), tempo=tempo_map(arr.export_mid),
                    length=round(mido.MidiFile(arr.export_mid).length, 2),
                    gain=gain_db(b.orchestra_mid, out / f'{title_slug}-orchestra.mid'))

    # melody (lead sheet with the words), /<country>/melody/
    xml = build_score(parts=[guide_spec(arr)], dynamics={}, multirest=True, header_part_name='Melody', **common)
    b.melody = score('melody', 'Melody', 'Melody', xml, out / 'melody', f'/{country}/melody/')
    b.melody.mid = b.melody_mid

    # parts by instrument page, in score order
    groups: dict[str, InstPage] = {}
    taken: set = set()
    specs_full = []
    for part in arr.parts:
        inst = part.inst
        page = groups.setdefault(inst.slug, InstPage(inst=inst))
        key = part_key(inst, part.track['name'], taken)
        label = part.track['name'] + (f' ({inst.transpose_name})' if inst.transpose_name else '')
        ps = part_spec(arr, part, 'P1', part.track['name'])
        dyn = part_dynamics(part)
        xml = build_score(parts=[ps], dynamics={'P1': dyn}, multirest=True, header_part_name=label, **common)
        url = f'/{country}/{inst.slug}/'
        sf = score(key, part.track['name'], label, xml, out / inst.slug, url)
        sf.transpose_name = inst.transpose_name
        mid = out / inst.slug / f'{title_slug}-{key}.mid'
        if part.export_index is not None:
            write_part_midi(arr.export_mid, part.export_index, mid, part.track['name'])
            sf.mid = f'{url}{mid.name}'
            sf.channel = synth_channel(arr.export_mid, part.export_index)
        page.parts.append(sf)
        fs = part_spec(arr, part, f'P{len(specs_full) + 1}', part.track['name'], written=False)
        specs_full.append((fs, dyn))
    b.insts = sorted(groups.values(), key=lambda g: g.inst.order)
    # full score: every part, concert pitch (octave transposers stay in their octave), in score order; the country
    # page shows it, so its file sits in the country folder
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
    b.full = score('full-score', 'Full score', 'Full score (concert pitch)', xml, out, f'/{country}/', full=True)
    b.full.mid = b.orchestra_mid
    # share image: the top of the full score's first page
    b.image = f'/{country}/img/{title_slug}-orchestra-score.png'
    jobs.append(dict(svg=str(cache / 'share.svg'), png=str(cache / 'share.png'), out=str(out / 'img' / f'{title_slug}-orchestra-score.png')))
    return b


def finish_jobs(jobs: list, render: bool = True):
    if not jobs:
        return
    if not render:  # pages only: the share images must already be there
        missing = [j['out'] for j in jobs if not Path(j['out']).exists()]
        if missing:
            raise SystemExit(f'--no-render but {len(missing)} share images are missing, e.g. {missing[0]}')
        return
    jf = CACHE / 'jobs.json'
    jf.write_text(json.dumps(jobs))
    subprocess.run(['node', str(HERE / 'render.cjs'), str(jf)], check=True)
    for job in jobs:
        Path(job['out']).parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(job['png']).convert('L').resize((1200, 630), Image.LANCZOS)
        im.save(job['out'], 'PNG', optimize=True)
        Path(job['png']).unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--orchestra', default=str(ROOT.parent / 'anthem-orchestra'))
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--no-render', action='store_true', help='keep the share images (no Chromium)')
    a = ap.parse_args()
    orch = Path(a.orchestra)
    anthems = load_anthems(orch)
    descs = load_descriptions(orch)
    slugs = [s for s in anthems if s not in SKIP and (orch / 'work' / s / 'song.json').exists()]
    if a.only:
        slugs = [s for s in slugs if s in a.only]
    import pages
    built = []
    jobs: list = []
    for slug in slugs:
        print('building', slug, flush=True)
        built.append(build_one(orch, slug, anthems, descs, jobs))
    finish_jobs(jobs, render=not a.no_render)
    all_built = pages.registry(built, anthems, orch, slugs_all=[s for s in anthems if s not in SKIP])
    pages.write_all(built, all_built)
    import sitefiles  # home, 404, sitemap, robots, llms.txt, ads.txt, CNAME
    sitefiles.main()


if __name__ == '__main__':
    main()

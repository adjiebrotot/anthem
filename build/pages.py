"""HTML for anthem.adjiebrotots.com: home; per anthem the full orchestra score (/<country>/), the melody
(/<country>/melody/) and one page per instrument, each with the score drawn in the browser and the orchestra player.

Static pages in the Adjie family design (tokens, theme cookie and dropdowns copied from tool.adjiebrotots.com) with
the Anthem Madness brand. Every page carries its anthem's native title and native instrument words for search.
"""
from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path

from i18n import LANG_OF, native_phrase, words

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
MANIFEST = Path(__file__).resolve().parent / 'manifest.json'
SITE = 'https://anthem.adjiebrotots.com'
BRAND = 'Anthem Madness'
PUB = 'ca-pub-8730116101825381'
GA = 'G-VYTV157ST0'
TODAY = dt.date.today()
PERSON = 'https://www.adjiebrotots.com/#person'

SLOT_TOP = '4716600974'        # Display 1: banner under the title
SLOT_BETWEEN = '4447514374'    # Display 2: under the score
SLOT_MULTI1 = '9720022354'     # Multiplex 1
SLOT_MULTI2 = '4659267360'     # Multiplex 2
SLOT_ARTICLE = '1433722275'    # In-article
SLOT_SIDE = '3134432708'       # Display 4: sticky sidebar

REGION_NAMES = {'asia': 'Asia', 'europe': 'Europe', 'americas': 'The Americas', 'middle-east': 'Middle East',
                'africa': 'Africa', 'oceania': 'Oceania'}

e = html.escape


def kb(n: int) -> str:
    return f'{n / 1024:.0f} KB' if n < 1024 * 1024 else f'{n / 1048576:.1f} MB'


def country_name(c: str) -> str:
    return c  # "the United States" stays as written for running text


def country_title(c: str) -> str:
    return c[4:] if c.lower().startswith('the ') else c


# flag file (docs/assets/img/flags/<code>.svg, from the flag-icons package, MIT) per country slug. An SVG, not an
# emoji: Windows draws flag emoji as two letters.
FLAGS = {
    'argentina': 'ar', 'asean': 'asean', 'australia': 'au', 'bahrain': 'bh', 'belgium': 'be', 'brazil': 'br',
    'brunei': 'bn', 'cambodia': 'kh', 'canada': 'ca', 'china': 'cn', 'colombia': 'co', 'denmark': 'dk',
    'european-union': 'eu', 'finland': 'fi', 'france': 'fr', 'germany': 'de', 'greece': 'gr', 'india': 'in',
    'iran': 'ir', 'ireland': 'ie', 'italy': 'it', 'japan': 'jp', 'laos': 'la', 'malaysia': 'my', 'mexico': 'mx',
    'mongolia': 'mn', 'netherlands': 'nl', 'new-zealand': 'nz', 'north-korea': 'kp', 'norway': 'no', 'peru': 'pe',
    'philippines': 'ph', 'poland': 'pl', 'portugal': 'pt', 'qatar': 'qa', 'romania': 'ro', 'saudi-arabia': 'sa',
    'singapore': 'sg', 'south-africa': 'za', 'south-korea': 'kr', 'spain': 'es', 'sweden': 'se',
    'switzerland': 'ch', 'taiwan': 'tw', 'thailand': 'th', 'turkiye': 'tr', 'uae': 'ae', 'ukraine': 'ua',
    'united-kingdom': 'gb', 'united-states': 'us', 'vatican-city': 'va', 'venezuela': 've', 'vietnam': 'vn',
}


def flag(country_slug: str) -> str:
    """The country's flag as a small image (decorative: the name sits beside it), '' if there is none."""
    code = FLAGS.get(country_slug)
    if not code:
        return ''
    return (f'<img class="flag" src="/assets/img/flags/{code}.svg" alt="" width="24" height="18" '
            f'loading="lazy" decoding="async">')


ORGS = {'asean-anthem', 'european-union-anthem'}   # anthems of a union of nations, not of a nation


def kind(slug: str) -> str:
    """'National Anthem' or, for ASEAN and the EU, 'Anthem'."""
    return 'Anthem' if slug in ORGS else 'National Anthem'


# ------------------------------------------------------------------------------------------------ manifest
def registry(built, anthems, orch, slugs_all):
    """Merge this build into build/manifest.json (what exists on the site) and return it."""
    man = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    for b in built:
        m = b.arr.meta
        man[b.arr.slug] = dict(country=m['country'], country_slug=b.country, title=m['title'],
                               english=m.get('english'), region=m['region'], native=m['native'][:1],
                               insts=[g.inst.slug for g in b.insts], key_meter=b.arr.desc.get('key_meter', ''),
                               length=b.arr.desc.get('length', ''), parts=len(b.arr.parts),
                               image=b.image,
                               updated=TODAY.isoformat())
    MANIFEST.write_text(json.dumps(man, indent=1, ensure_ascii=False, sort_keys=True))
    return man


# ------------------------------------------------------------------------------------------------ pieces
def ad(slot: str, fmt: str = 'auto', cls: str = '', extra: str = '') -> str:
    f = f' data-ad-format="{fmt}"' if fmt else ''
    full = ' data-full-width-responsive="true"' if fmt == 'auto' else ''
    return (f'<div class="ad-slot {cls}"><ins class="adsbygoogle" style="display:block" data-ad-client="{PUB}" '
            f'data-ad-slot="{slot}"{f}{full}{extra}></ins></div>')


def head(*, title: str, desc: str, url: str, image: str, jsonld: dict, keywords: str = '') -> str:
    img = SITE + image if image.startswith('/') else image
    kw = f'\n<meta name="keywords" content="{e(keywords)}"/>' if keywords else ''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}"/>{kw}
<meta name="robots" content="index, follow, max-image-preview:large"/>
<link rel="canonical" href="{SITE}{url}"/>
<link rel="sitemap" type="application/xml" href="/sitemap.xml"/>
<meta property="og:type" content="website"/>
<meta property="og:site_name" content="{BRAND} by adjiebrotot"/>
<meta property="og:title" content="{e(title)}"/>
<meta property="og:description" content="{e(desc)}"/>
<meta property="og:url" content="{SITE}{url}"/>
<meta property="og:image" content="{img}"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{e(title)}"/>
<meta name="twitter:description" content="{e(desc)}"/>
<meta name="twitter:image" content="{img}"/>
<meta name="theme-color" content="#0F1728"/>
<link rel="icon" type="image/svg+xml" href="/assets/img/mark.svg"/>
<link rel="apple-touch-icon" href="/assets/img/anthem-madness-square.png"/>
<link rel="preload" href="/assets/fonts/dm-sans.woff2" as="font" type="font/woff2" crossorigin/>
<link rel="stylesheet" href="/assets/css/fonts.css"/>
<link rel="stylesheet" href="/assets/css/dark.css"/>
<link rel="stylesheet" href="/assets/css/light.css"/>
<link rel="stylesheet" href="/assets/css/dropdown.css"/>
<link rel="stylesheet" href="/assets/css/site.css"/>
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('consent', 'default', {{analytics_storage: 'denied', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied', region: ['AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','GR','HU','IE','IT','LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE','IS','LI','NO','GB','CH']}});
  gtag('consent', 'default', {{analytics_storage: 'granted', ad_storage: 'granted', ad_user_data: 'granted', ad_personalization: 'granted'}});
  try {{ var abtConsent = localStorage.getItem('abt-consent'); if (abtConsent) gtag('consent', 'update', {{analytics_storage: abtConsent}}); }} catch (e) {{}}
  gtag('js', new Date());
  gtag('config', '{GA}');
</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={PUB}" crossorigin="anonymous"></script>
<script src="/consent.js" defer></script>
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False, separators=(',', ':'))}</script>
</head>
'''


def header() -> str:
    return '''<body class="light">
<script src="/assets/js/theme.js"></script>
<header class="family-bar">
  <div class="container family-inner">
    <a class="family-brand" href="/" aria-label="Anthem Madness by adjiebrotot, home">
      <img src="/assets/img/mark.svg" alt="" width="30" height="30"/>
      <span class="brand-words"><span>Anthem <b>Madness</b></span><small>by adjiebrotot</small></span>
    </a>
    <nav class="family-nav" aria-label="Site">
      <a href="/" class="nav-anthems">Anthems</a>
      <a href="https://tool.adjiebrotots.com/" class="nav-hide-sm">Tools</a>
      <a href="https://blog.adjiebrotots.com/" class="nav-hide-sm">Blog</a>
      <button class="family-theme" id="themeToggle" type="button" aria-label="Switch theme"></button>
    </nav>
  </div>
</header>
'''


def footer() -> str:
    return f'''<footer class="container page-footer"><section class="page-footer-info card">
  <p class="footer-links"><a href="/">All anthems</a> · <a href="https://tool.adjiebrotots.com/privacy/">Privacy Policy</a> · <a href="https://tool.adjiebrotots.com/disclaimer/">Disclaimer</a> · <a href="https://www.adjiebrotots.com/">adjiebrotots.com</a> · <span class="footer-updated">Updated <time datetime="{TODAY.isoformat()}">{TODAY.day} {TODAY:%B %Y}</time></span></p>
  <p>The melodies are the official tunes of public national anthems; the orchestral arrangements, sheet music and MIDI files are by Anthem Madness and free to download for practice, school and community performances. Every PDF carries the anthem.adjiebrotots.com watermark, faint and behind the notes.</p>
  <p class="footer-credits">The player plays the MIDI in your browser with <a href="https://github.com/spessasus/spessasynth_lib">spessasynth</a> (<a href="/assets/js/vendor/spessasynth-LICENSE.txt">Apache 2.0</a>) and the SoundFont of the <a href="https://orchestra.adjiebrotots.com/">orchestra app</a>: <a href="http://vis.versilstudios.net/vsco-community.html">VSCO 2 Community Edition</a> and VCSL by Versilian Studios (Sam Gossner) and Ivy Audio (Simon Dalzell), over <a href="https://www.schristiancollins.com">GeneralUser GS</a> by S. Christian Collins (<a href="/assets/sf/GeneralUser-GS-LICENSE.txt">licence</a>). Scores drawn by <a href="https://www.verovio.org/">Verovio</a>.</p>
  <div class="footer-made"><img src="/assets/img/indonesian.png" alt="" width="36" height="36"/><span>Made in Australia by <a href="https://www.adjiebrotots.com/" rel="author">Adjie Brotosukmono</a>, an Indonesian engineer.</span></div>
</section></footer>
<script src="/assets/js/dropdown.js"></script>
<script src="/assets/js/site.js"></script>
<script src="/assets/js/score.js"></script>
</body>
</html>
'''


def crumbs(items: list[tuple[str, str]]) -> str:
    li = []
    for i, (name, url) in enumerate(items):
        if i == len(items) - 1:
            li.append(f'<li aria-current="page">{e(name)}</li>')
        else:
            li.append(f'<li><a href="{url}">{e(name)}</a></li>')
    return f'<nav class="crumbs" aria-label="Breadcrumb"><ol>{"".join(li)}</ol></nav>'


def crumbs_ld(items: list[tuple[str, str]]) -> dict:
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (n, u) in enumerate(items)]}


def faq_block(qas: list[tuple[str, str]]) -> str:
    items = ''.join(f'<div class="faq-item"><h3>{e(q)}</h3><p>{a}</p></div>' for q, a in qas)
    return f'<section class="card faq-card" aria-labelledby="faqTitle"><h2 id="faqTitle">Questions</h2><div class="faq-list">{items}</div></section>'


def faq_ld(qas) -> dict:
    import re
    return {'@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub('<[^>]+>', '', a)}}
        for q, a in qas]}


# ------------------------------------------------------------------------------------------------ anthem pages
class Ctx:
    def __init__(self, b, man):
        self.b = b
        self.arr = b.arr
        self.m = b.arr.meta
        self.man = man
        self.country = self.m['country']
        self.ct = country_title(self.country)
        self.flag = flag(b.country)
        self.title = self.m['title']
        self.base = f'/{b.country}/'
        d = b.arr.desc
        self.key_meter = d.get('key_meter', '')
        self.length = d.get('length', '')
        self.bpm = round(b.arr.tempo[0][1]) if b.arr.tempo else None
        self.native = self.m['native']
        self.ntitle = self.native[0] if self.native else self.title
        self.Kind = kind(b.arr.slug)                     # National Anthem / Anthem
        self.kind = 'the ' + self.Kind.lower()           # the national anthem / the anthem
        self.w = words(b.arr.slug)

    def inst_word(self, slug):
        if not self.w:
            return ''
        if slug == 'full-score':
            return self.w['score']
        if slug == 'melody':
            return self.w['melody']
        return self.w['inst'].get(slug, '')


def composition_ld(c: Ctx) -> dict:
    m = c.m
    alt = [x for x in c.native if x != c.title][:3]
    if m.get('english'):
        alt.insert(0, m['english'])
    d = {'@type': 'MusicComposition', '@id': f'{SITE}{c.base}#anthem', 'name': c.title, 'alternateName': alt,
         'description': f"{c.Kind[0]}{c.Kind[1:].lower()} of {c.country}.", 'url': SITE + c.base,
         'composer': {'@type': 'Person', 'name': m['music']}, 'inLanguage': m['language'],
         'musicArrangement': {'@type': 'MusicComposition', 'name': f'{c.title} (orchestral arrangement)',
                              'creator': {'@id': PERSON}}}
    if m.get('words') and 'instrumental' not in m['language'].lower():
        d['lyricist'] = {'@type': 'Person', 'name': m['words']}
    return d


def doc_ld(name: str, url: str, fmt: str, size: int = 0) -> dict:
    d = {'@type': 'DigitalDocument' if fmt == 'application/pdf' else 'MediaObject', 'name': name, 'url': SITE + url,
         'encodingFormat': fmt, 'isAccessibleForFree': True, 'license': SITE + '/#license'}
    if size:
        d['contentSize'] = kb(size)
    return d


def options(c: Ctx, current: str) -> str:
    opts = [('full-score', 'Full orchestra (all parts)', c.base), ('melody', 'Melody (lead sheet)', f'{c.base}melody/')]
    for g in c.b.insts:
        opts.append((g.inst.slug, g.inst.name if len(g.parts) == 1 else g.inst.plural, f'{c.base}{g.inst.slug}/'))
    return ''.join(f'<option value="{u}"{" selected" if k == current else ""}>{e(n)}</option>' for k, n, u in opts)


ICO_PLAY = ('<svg class="ico-play" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" '
            'd="M8 5.5v13a1 1 0 0 0 1.5.86l10.2-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5z"/></svg>')
ICO_PAUSE = ('<svg class="ico-pause" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" '
             'd="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z"/></svg>')


def player(c: Ctx, what: str, part: bool = False) -> str:
    """The orchestra MIDI played by a SoundFont synth in the browser, synced to the score (score.js)."""
    b = c.b
    data = b.player
    js = json.dumps(data, separators=(',', ':')).replace('</', '<\\/')
    mix = ('<select class="pl-mix" aria-label="What the orchestra plays"><option value="all" selected>Full orchestra</option>'
           '<option value="solo">This part alone</option><option value="minus">Without this part</option></select>') if part else ''
    speeds = ''.join(f'<option value="{v}"{" selected" if v == "1" else ""}>{v}×</option>'
                     for v in ('0.5', '0.75', '1', '1.25'))
    return f'''<div class="player" id="player">
  <button type="button" class="pl-play" aria-label="Play">{ICO_PLAY}{ICO_PAUSE}</button>
  <div class="pl-main"><span class="pl-title">Full orchestra · {e(what)} highlighted</span>
    <div class="pl-line"><span class="pl-time"><span class="pl-cur">0:00</span> / <span class="pl-dur">0:00</span></span>
    <input type="range" class="pl-seek" min="0" max="1000" value="0" step="1" aria-label="Position in the music"/></div></div>
  <div class="pl-tools">
    {mix}<select class="pl-speed" aria-label="Speed">{speeds}</select>
    <button type="button" class="pl-follow" aria-pressed="true" title="Scroll with the music">Follow</button>
    <button type="button" class="pl-zoom" data-zoom="-" aria-label="Smaller notes">−</button>
    <button type="button" class="pl-zoom" data-zoom="+" aria-label="Larger notes">+</button>
  </div>
</div>
<script type="application/json" id="amPlayer">{js}</script>'''


def score_viewer(c: Ctx, parts, current: str, what: str) -> str:
    tabs = ''
    if len(parts) > 1:
        tabs = '<div class="part-tabs" role="tablist" aria-label="Parts">' + ''.join(
            f'<button type="button" role="tab" class="part-tab{" active" if i == 0 else ""}" '
            f'aria-selected="{"true" if i == 0 else "false"}" data-part="{p.key}" data-src="{p.src}"'
            f'{"" if p.channel is None else f" data-channel=\"{p.channel}\""}>{e(p.label)}</button>'
            for i, p in enumerate(parts)) + '</div>'
    notes = ''.join(
        f'<p class="part-note" data-part="{p.key}"{"" if i == 0 else " hidden"}>Written for '
        f'{e(p.transpose_name.replace("in ", "instrument in "))} (transposed part); the orchestra sounds in concert pitch.</p>'
        for i, p in enumerate(parts) if p.transpose_name)
    p0 = parts[0]
    nat = native_phrase(c.arr.slug, current, c.ntitle)
    label = f'{c.title} {what} sheet music' + (f' ({nat})' if nat else '')
    return f'''<section class="card score-card" aria-label="Sheet music and player">
  <div class="score-head">
    <label class="field"><span class="field-label">Instrument</span>
      <select class="sel-input" id="instSel" aria-label="Choose an instrument">{options(c, current)}</select></label>
    {tabs}
  </div>
  {player(c, what, part=p0.channel is not None)}
  {notes}
  <div class="score-view" id="scoreView" data-src="{p0.src}" data-full="{1 if p0.full else 0}"{"" if p0.channel is None else f' data-channel="{p0.channel}"'} role="img" aria-label="{e(label)}" aria-busy="true">
    <div class="score-status"><div class="spinner"></div><span>Loading the score…</span></div>
    <noscript><p class="score-status">The sheet music is drawn in your browser and needs JavaScript. The MIDI files work without it.</p></noscript>
  </div>
</section>
{ad(SLOT_BETWEEN, cls='ad-between')}'''


def pdf_button(p, cls: str = 'btn-primary', label: str = 'PDF') -> str:
    """The PDF is drawn in the reader's browser at A4 from the score file (score.js), watermark and footer added."""
    n = p.pages
    return (f'<button type="button" class="btn {cls}" data-pdf="{e(p.pdf)}" data-src="{p.src}" '
            f'data-full="{1 if p.full else 0}" data-print="{e(json.dumps(p.print, separators=(",", ":")))}" '
            f'data-footer="{e(p.footer)}">{label} '
            f'<small>{n} page{"s" if n != 1 else ""}</small></button>')


def download_card(c: Ctx, parts, extra: list) -> str:
    """extra: (name, url, 'MIDI') links and (name, ScoreFile, 'PDF') buttons for the whole arrangement."""
    rows = []
    for i, p in enumerate(parts):
        mid = f'<a class="btn btn-ghost" href="{p.mid}" download>MIDI</a>' if p.mid else ''
        tr = f' <small>{e(p.transpose_name)}</small>' if p.transpose_name else ''
        rows.append(f'<li class="dl-row{" active" if i == 0 and len(parts) > 1 else ""}" data-part="{p.key}">'
                    f'<span class="dl-name">{e(p.label)}{tr}</span><span class="dl-btns">{pdf_button(p)}{mid}</span></li>')
    more = []
    for n, u, t in extra:
        if not u:
            continue
        btn = pdf_button(u, 'btn-ghost') if t == 'PDF' else f'<a class="btn btn-ghost" href="{u}" download>{e(t)}</a>'
        more.append(f'<li class="dl-row"><span class="dl-name">{e(n)}</span><span class="dl-btns">{btn}</span></li>')
    sub = f'<h3 class="dl-sub">Whole arrangement</h3><ul class="dl-list">{"".join(more)}</ul>' if more else ''
    return f'''<section class="card dl-card" aria-labelledby="dlTitle">
  <h2 id="dlTitle">Download</h2>
  <ul class="dl-list">{''.join(rows)}</ul>
  {sub}
  <p class="dl-note">Free for practice, school and community performance. The PDF is drawn in your browser at A4, with the anthem.adjiebrotots.com watermark faint behind the notes.</p>
</section>'''


def whole_extra(c: Ctx, full_pdf: bool = True, melody: bool = True) -> list:
    b = c.b
    extra = [('Full orchestra', b.orchestra_mid, 'MIDI')]
    if b.chorus_mid:
        extra.append(('Chorus only', b.chorus_mid, 'MIDI'))
    if melody and b.melody_mid:
        extra.append(('Melody only', b.melody_mid, 'MIDI'))
    if full_pdf:
        extra.append(('Full score', b.full, 'PDF'))
    return extra


def facts_card(c: Ctx) -> str:
    m = c.m
    rows = [('Anthem', c.title)]
    if m.get('english'):
        rows.append(('In English', m['english']))
    rows += [('Country', c.ct), ('Music', m['music'])]
    if m.get('words') and 'instrumental' not in m['language'].lower():
        rows.append(('Words', m['words']))
    rows += [('Adopted', m['adopted']), ('Language', m['language'])]
    if c.key_meter:
        rows.append(('Key, meter', c.key_meter))
    if c.bpm:
        rows.append(('Tempo', f'starts at {c.bpm} BPM'))
    if c.length:
        rows.append(('Length', c.length))
    rows.append(('Orchestra', f'{len(c.arr.parts)} parts'))
    dl = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in rows)
    return f'<section class="card facts-card" aria-labelledby="factsTitle"><h2 id="factsTitle">Facts</h2><dl class="facts">{dl}</dl></section>'


def inst_grid(c: Ctx, current: str) -> str:
    cards = []
    items = [('full-score', 'Full orchestra', c.base, f'{len(c.arr.parts)} parts, full score'),
             ('melody', 'Melody', f'{c.base}melody/', 'lead sheet with lyrics' if c.arr.lyrics else 'lead sheet')]
    for g in c.b.insts:
        n = len(g.parts)
        items.append((g.inst.slug, g.inst.name, f'{c.base}{g.inst.slug}/', f'{n} part{"s" if n > 1 else ""}'))
    for slug, name, url, sub in items:
        if slug == current:
            continue
        nat = c.inst_word(slug)
        natx = f'<span class="ig-nat" lang="{LANG_OF.get(c.arr.slug, "und")}">{e(nat)}</span>' if nat else ''
        cards.append(f'<a class="ig-card" href="{url}"><span class="ig-name">{e(name)}</span>{natx}<span class="ig-sub">{e(sub)}</span></a>')
    return f'<section class="card ig-section" aria-labelledby="igTitle"><h2 id="igTitle">Other parts of {e(c.title)}</h2><div class="ig-grid">{"".join(cards)}</div></section>'


def about_sections(c: Ctx) -> str:
    m = c.m
    return f'''<section class="card prose" aria-labelledby="aboutTitle"><h2 id="aboutTitle">About {e(c.title)}</h2>
<p>{e(m['about'])}</p></section>
{ad(SLOT_ARTICLE, fmt='fluid', extra=' data-ad-layout="in-article" style="display:block;text-align:center"')}
<section class="card prose" aria-labelledby="arrTitle"><h2 id="arrTitle">About this orchestral arrangement</h2>
<p>{e(m['orch'])}</p>
<p>The melody is the official tune, note for note; only the orchestration is new. {e(c.key_meter)}{', ' + e(c.length) if c.length else ''}, {len(c.arr.parts)} parts.</p></section>'''


def more_anthems(c: Ctx) -> str:
    same = [v for k, v in sorted(c.man.items(), key=lambda kv: kv[1]['country_slug'])
            if k != c.arr.slug and v['region'] == c.m['region']]
    other = [v for k, v in sorted(c.man.items(), key=lambda kv: kv[1]['country_slug'])
             if k != c.arr.slug and v['region'] != c.m['region']]
    pick = (same + other)[:8]
    if not pick:
        return ''
    cards = ''.join(f'<a class="an-card" href="/{v["country_slug"]}/"><span class="an-country">{flag(v["country_slug"])}{e(country_title(v["country"]))}</span>'
                    f'<span class="an-title">{e(v["title"])}</span></a>' for v in pick)
    return f'<section class="more-anthems" aria-labelledby="moreTitle"><h2 id="moreTitle">More national anthems</h2><div class="an-grid">{cards}</div></section>'


def layout(c: Ctx, *, h1: str, lead: str, crumbs_items, viewer: str, side_dl: str, current: str,
           faq: list) -> str:
    return f'''<main class="container">
{crumbs(crumbs_items)}
<div class="page-title">
  <h1>{h1}</h1>
  <p class="lead">{lead}</p>
</div>
{ad(SLOT_TOP, fmt='horizontal', cls='ad-top')}
<div class="am-layout">
  <div class="am-main">{viewer}</div>
  <div class="am-dl">{side_dl}</div>
  <aside class="am-side">{facts_card(c)}<div class="side-ad">{ad(SLOT_SIDE, fmt='vertical', cls='ad-side')}</div></aside>
</div>
{inst_grid(c, current)}
{about_sections(c)}
{ad(SLOT_MULTI1, fmt='autorelaxed', cls='ad-multi')}
{faq_block(faq)}
{more_anthems(c)}
{ad(SLOT_MULTI2, fmt='autorelaxed', cls='ad-multi')}
</main>
'''


def common_faq(c: Ctx, what: str) -> list[tuple[str, str]]:
    m = c.m
    qa = [(f'Is the {what} of {c.title} free to download?',
           f'Yes. The PDF and the MIDI files on this page are free for practice, school and community performances. '
           f'Each PDF carries the anthem.adjiebrotots.com watermark.'),
          ('Can I listen to it while I read?',
           'Yes. Press play above the score: the full orchestra plays in your browser and the notes light up as they sound, '
           'with the page scrolling along. Click any note to play from there, or slow it down to practise.'),
          (f'Who wrote {c.title}?',
           f'The music is by {e(m["music"])}' + (f' and the words by {e(m["words"])}' if m.get('words') and 'instrumental' not in m['language'].lower() else '')
           + f'. It was adopted {e(m["adopted"])}.'),
          ('Is the melody the official one?',
           'Yes. The tune is the official melody, note for note, checked against published scores; only the orchestration is new.'),
          ('What key and tempo is it in?',
           f'This arrangement is in {e(c.key_meter)}' + (f' and starts at about {c.bpm} beats per minute' if c.bpm else '')
           + (f'; it lasts {e(c.length)}.' if c.length else '.'))]
    return qa


def page_ld(c: Ctx, url: str, title: str, desc: str, items, faq, extra: list) -> dict:
    return {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': SITE + url, 'url': SITE + url, 'name': title, 'description': desc,
         'inLanguage': 'en', 'isPartOf': {'@id': SITE + '/#website'}, 'about': {'@id': f'{SITE}{c.base}#anthem'},
         'primaryImageOfPage': SITE + c.b.image, 'dateModified': TODAY.isoformat(), 'author': {'@id': PERSON}},
        composition_ld(c), *extra, crumbs_ld(items), faq_ld(faq)]}


def inst_page(c: Ctx, g) -> str:
    inst = g.inst
    parts = g.parts
    nat = native_phrase(c.arr.slug, inst.slug, c.ntitle)
    many = len(parts) > 1
    name = inst.name
    url = f'{c.base}{inst.slug}/'
    title = f'{c.title} {name} Sheet Music (PDF) & MIDI | {c.Kind} of {c.ct}'
    desc = (f'Free {name.lower()} sheet music and MIDI of {c.title}, {c.kind} of {c.country}, from a full '
            f'orchestral arrangement: {", ".join(p.label for p in parts)}. Read it along with the orchestra, then '
            f'download the PDF or MIDI.' + (f' {nat[:1].upper() + nat[1:]}.' if nat else ''))
    h1 = f'{e(c.title)}: {e(name)} Sheet Music'
    lead_bits = [f'{c.Kind} of {c.flag}{e(c.ct)}']
    if c.native and c.native[0] != c.title:
        lead_bits.append(f'<span lang="und">{e(c.native[0])}</span>')
    if nat:
        lead_bits.append(e(nat))
    lead = ' · '.join(lead_bits)
    items = [('Anthems', '/'), (c.ct, c.base), (name, url)]
    faq = [(f'Which {name.lower()} parts are in this arrangement?',
            f'{len(parts)} part{"s" if many else ""}: ' + ', '.join(e(p.label) for p in parts)
            + (f'. Parts are written for the {e(inst.name.lower())} {e(inst.transpose_name)}, so they read a transposition above the sounding pitch; the full score is in concert pitch.' if inst.transpose_name else '.'))]
    faq += common_faq(c, f'{name.lower()} sheet music')
    lead_sentence = (f'<p class="geo">{e(c.title)} is {c.kind} of {e(c.country)}. This page has the '
                     f'{e(name.lower())} part{"s" if many else ""} of a full orchestral arrangement as sheet music to '
                     f'read along with the orchestra, with a PDF and a MIDI file for each part.</p>')
    ld = page_ld(c, url, title, desc, items, faq,
                 [doc_ld(f'{c.title} {p.label} (MIDI)', p.mid, 'audio/midi') for p in parts if p.mid])
    viewer = score_viewer(c, parts, inst.slug, name.lower() + (' parts' if many else ' part'))
    body = layout(c, h1=h1, lead=lead + lead_sentence, crumbs_items=items, viewer=viewer,
                  side_dl=download_card(c, parts, whole_extra(c)), current=inst.slug, faq=faq)
    kw = ', '.join(x for x in [f'{c.title} {name.lower()} sheet music', f'{c.title} {name.lower()} pdf',
                              f'{c.title} {name.lower()} midi', f'national anthem of {c.ct} {name.lower()}', nat] if x)
    return head(title=title, desc=desc, url=url, image=c.b.image, jsonld=ld, keywords=kw) + header() + body + footer()


def country_page(c: Ctx) -> str:
    """/<country>/: the full orchestra score with the player."""
    fs = c.b.full
    nat = native_phrase(c.arr.slug, None, c.ntitle)
    url = c.base
    title = f'{c.title} Sheet Music & MIDI: {c.Kind} of {c.ct} (Full Orchestra)'
    desc = (f'{c.title}, {c.kind} of {c.country}, for full orchestra: read the score as the orchestra plays it, '
            f'then download the sheet music of every instrument ({len(c.arr.parts)} parts), the melody'
            + (' with lyrics' if c.arr.lyrics else '') + ' and the MIDI, free.'
            + (f' {nat[:1].upper() + nat[1:]}.' if nat else ''))
    h1 = f'{e(c.title)}: {c.Kind} of <span class="nowrap">{c.flag}{e(c.ct)}</span>'
    bits = []
    if c.m.get('english'):
        bits.append(e(c.m['english']))
    if c.native and c.native[0] != c.title:
        bits.append(f'<span lang="und">{e(c.native[0])}</span>')
    bits.append(f'Full orchestra score, {len(c.arr.parts)} parts')
    lead = ' · '.join(bits)
    play = ': press play and the notes light up as the orchestra plays them'
    lead_sentence = (f'<p class="geo">{e(c.title)} is {c.kind} of {e(c.country)}, with music by '
                     f'{e(c.m["music"])}. Below is the full score of a {len(c.arr.parts)}-part orchestral arrangement in '
                     f'concert pitch{play}. The melody' + (' with the words' if c.arr.lyrics else '')
                     + ' and every instrument have pages of their own.</p>')
    items = [('Anthems', '/'), (c.ct, url)]
    faq = [(f'Can I download {c.title} as MIDI?',
            f'Yes: the full orchestral arrangement ({len(c.arr.parts)} parts, one track per part), the melody alone, a '
            f'short chorus version and a MIDI for every part.'),
           ('Is there sheet music for my instrument?',
            'Pick your instrument in the menu above the score: the melody, '
            + ', '.join(g.inst.name.lower() for g in c.b.insts) + '. This page has the full score with every part in concert pitch.')]
    faq += common_faq(c, 'sheet music')
    ld = page_ld(c, url, title, desc, items, faq,
                 [doc_ld(f'{c.title} full orchestra (MIDI)', c.b.orchestra_mid, 'audio/midi')])
    viewer = score_viewer(c, [fs], 'full-score', 'full score')
    body = layout(c, h1=h1, lead=lead + lead_sentence, crumbs_items=items, viewer=viewer,
                  side_dl=download_card(c, [fs], whole_extra(c, full_pdf=False)), current='full-score', faq=faq)
    kw = ', '.join([f'national anthem of {c.ct}', f'{c.title} sheet music', f'{c.title} midi', f'{c.title} orchestra',
                    f'{c.title} full score', *c.native[:3]] + ([nat] if nat else []))
    return head(title=title, desc=desc, url=url, image=c.b.image, jsonld=ld, keywords=kw) + header() + body + footer()


def melody_page(c: Ctx) -> str:
    """/<country>/melody/: the tune as a lead sheet (with the words where they are sung)."""
    mel = c.b.melody
    nat = native_phrase(c.arr.slug, 'melody', c.ntitle)
    url = f'{c.base}melody/'
    words = ' with lyrics' if c.arr.lyrics else ''
    title = f'{c.title} Melody Sheet Music{" & Lyrics" if c.arr.lyrics else ""} (PDF, MIDI) | {c.Kind} of {c.ct}'
    desc = (f'The melody of {c.title}, {c.kind} of {c.country}, as a lead sheet{words}: read it as the orchestra '
            f'plays, then download the PDF and the MIDI, free.' + (f' {nat[:1].upper() + nat[1:]}.' if nat else ''))
    h1 = f'{e(c.title)}: Melody{" and Lyrics" if c.arr.lyrics else ""}'
    lead = f'{c.Kind} of {c.flag}{e(c.ct)} · lead sheet{words}' + (f' · {e(nat)}' if nat else '')
    play = ' Press play to hear it with the full orchestra and follow the tune as it lights up.'
    lead_sentence = (f'<p class="geo">The official melody of {e(c.title)}, note for note, on one staff'
                     + (' with the words under the notes' if c.arr.lyrics else '') + f'.{play}</p>')
    items = [('Anthems', '/'), (c.ct, c.base), ('Melody', url)]
    faq = common_faq(c, 'melody sheet music')
    ld = page_ld(c, url, title, desc, items, faq,
                 [doc_ld(f'{c.title} melody (MIDI)', mel.mid, 'audio/midi')] if mel.mid else [])
    viewer = score_viewer(c, [mel], 'melody', 'melody')
    body = layout(c, h1=h1, lead=lead + lead_sentence, crumbs_items=items, viewer=viewer,
                  side_dl=download_card(c, [mel], whole_extra(c, melody=False)), current='melody', faq=faq)
    kw = ', '.join(x for x in [f'{c.title} melody', f'{c.title} lyrics sheet music' if c.arr.lyrics else '',
                              f'{c.title} lead sheet', f'national anthem of {c.ct} melody', nat] if x)
    return head(title=title, desc=desc, url=url, image=c.b.image, jsonld=ld, keywords=kw) + header() + body + footer()


def moved_page(to: str, title: str) -> str:
    """An old address that now lives elsewhere (the full score moved to the country page)."""
    u = SITE + to
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><title>{e(title)}</title>
<meta name="robots" content="noindex, follow"/><link rel="canonical" href="{u}"/><meta http-equiv="refresh" content="0; url={to}"/>
<script>location.replace({json.dumps(to)} + location.hash);</script></head>
<body><p>This page has moved to <a href="{to}">{e(u)}</a>.</p></body></html>
'''


def write_all(built, man):
    for b in built:
        c = Ctx(b, man)
        out = DOCS / b.country
        (out / 'index.html').write_text(country_page(c))
        (out / 'melody').mkdir(exist_ok=True)
        (out / 'melody' / 'index.html').write_text(melody_page(c))
        for g in b.insts:
            (out / g.inst.slug / 'index.html').write_text(inst_page(c, g))
        (out / 'full-score').mkdir(exist_ok=True)
        (out / 'full-score' / 'index.html').write_text(moved_page(c.base, f'{c.title} full score | {BRAND}'))

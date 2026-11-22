"""HTML for anthem.adjiebrotots.com: home, one page per anthem (melody), one per instrument, one full score.

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
SLOT_BETWEEN = '4447514374'    # Display 2: between score pages
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
                               image=b.melody.pages[0] if b.melody and b.melody.pages else '',
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
  <p>The melodies are the official tunes of public national anthems; the orchestral arrangements, sheet music and MIDI files are by Anthem Madness and free to download for practice, school and community performances. Every PDF carries the anthem.adjiebrotots.com watermark.</p>
  <div class="footer-made"><img src="/assets/img/indonesian.png" alt="" width="36" height="36"/><span>Made in Australia by <a href="https://www.adjiebrotots.com/" rel="author">Adjie Brotosukmono</a>, an Indonesian engineer.</span></div>
</section></footer>
<script src="/assets/js/dropdown.js"></script>
<script src="/assets/js/site.js"></script>
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
    opts = [('melody', f'Melody (lead sheet)', c.base)]
    for g in c.b.insts:
        opts.append((g.inst.slug, g.inst.name if len(g.parts) == 1 else g.inst.plural, f'{c.base}{g.inst.slug}/'))
    opts.append(('full-score', 'Full score (all parts)', f'{c.base}full-score/'))
    return ''.join(f'<option value="{u}"{" selected" if k == current else ""}>{e(n)}</option>' for k, n, u in opts)


def score_viewer(c: Ctx, parts, current: str, inst_label: str) -> str:
    tabs = ''
    if len(parts) > 1:
        tabs = '<div class="part-tabs" role="tablist" aria-label="Parts">' + ''.join(
            f'<button type="button" role="tab" class="part-tab{" active" if i == 0 else ""}" aria-selected="{"true" if i == 0 else "false"}" '
            f'data-part="{p.key}">{e(p.label)}</button>' for i, p in enumerate(parts)) + '</div>'
    blocks = []
    for i, p in enumerate(parts):
        figs = []
        for k, src in enumerate(p.pages, 1):
            alt = f'{c.title} {p.label} sheet music, page {k} of {len(p.pages)}'
            nat = native_phrase(c.arr.slug, current if current != 'melody' else 'melody', c.ntitle)
            if nat:
                alt += f' ({nat})'
            load = 'eager' if (i == 0 and k == 1) else 'lazy'
            prio = ' fetchpriority="high"' if (i == 0 and k == 1) else ''
            figs.append(f'<figure class="sheet"><img src="{src}" width="1240" height="1754" alt="{e(alt)}" '
                        f'loading="{load}" decoding="async"{prio}/><figcaption>Page {k} of {len(p.pages)}</figcaption></figure>')
            if i == 0 and k < len(p.pages):
                figs.append(ad(SLOT_BETWEEN, cls='ad-between'))
        hidden = '' if i == 0 else ' hidden'
        tr = f'<p class="part-note">Written for {e(p.transpose_name.replace("in ", "instrument in "))} (transposed part).</p>' if p.transpose_name else ''
        blocks.append(f'<div class="score-part" id="part-{p.key}" data-part="{p.key}"{hidden}>{tr}{"".join(figs)}</div>')
    return f'''<section class="card score-card" aria-label="Sheet music">
  <div class="score-head">
    <label class="field"><span class="field-label">Instrument</span>
      <select class="sel-input" id="instSel" aria-label="Choose an instrument">{options(c, current)}</select></label>
    {tabs}
  </div>
  {''.join(blocks)}
</section>'''


def pdf_button(p, cls: str = 'btn-primary', label: str = 'PDF') -> str:
    """The PDF is made in the reader's browser from the page images (site.js), with the big watermark and a footer."""
    n = len(p.pages)
    return (f'<button type="button" class="btn {cls}" data-pdf="{e(p.pdf)}" data-pages="{" ".join(p.pages)}" '
            f'data-footer="{e(p.footer)}">{label} <small>{n} page{"s" if n > 1 else ""}</small></button>')


def download_card(c: Ctx, parts, extra: list) -> str:
    """extra: (name, url, 'MIDI') links and (name, ScoreFile, 'PDF') buttons for the whole arrangement."""
    rows = []
    for i, p in enumerate(parts):
        mid = f'<a class="btn btn-ghost" href="{p.mid}" download>MIDI</a>' if p.mid else ''
        rows.append(f'''<li class="dl-row{" active" if i == 0 else ""}" data-part="{p.key}">
  <span class="dl-name">{e(p.label)}{f' <small>{e(p.transpose_name)}</small>' if p.transpose_name else ''}</span>
  <span class="dl-btns">{pdf_button(p)}{mid}</span></li>''')
    more = []
    for n, u, t in extra:
        btn = pdf_button(u, 'btn-ghost') if t == 'PDF' else f'<a class="btn btn-ghost" href="{u}" download>{e(t)}</a>'
        more.append(f'<li class="dl-row"><span class="dl-name">{e(n)}</span><span class="dl-btns">{btn}</span></li>')
    return f'''<section class="card dl-card" aria-labelledby="dlTitle">
  <h2 id="dlTitle">Download</h2>
  <ul class="dl-list">{''.join(rows)}</ul>
  {f'<h3 class="dl-sub">Whole arrangement</h3><ul class="dl-list">{"".join(more)}</ul>' if more else ''}
  <p class="dl-note">Free for practice, school and community performance. The PDF is made in your browser from the pages above and carries the anthem.adjiebrotots.com watermark.</p>
</section>'''


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
    items = [('melody', 'Melody', c.base, 'lead sheet with lyrics' if c.arr.lyrics else 'lead sheet')]
    for g in c.b.insts:
        n = len(g.parts)
        items.append((g.inst.slug, g.inst.name, f'{c.base}{g.inst.slug}/', f'{n} part{"s" if n > 1 else ""}'))
    items.append(('full-score', 'Full score', f'{c.base}full-score/', f'{len(c.arr.parts)} parts'))
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
    cards = ''.join(f'<a class="an-card" href="/{v["country_slug"]}/"><span class="an-country">{e(country_title(v["country"]))}</span>'
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
          (f'Who wrote {c.title}?',
           f'The music is by {e(m["music"])}' + (f' and the words by {e(m["words"])}' if m.get('words') and 'instrumental' not in m['language'].lower() else '')
           + f'. It was adopted {e(m["adopted"])}.'),
          ('Is the melody the official one?',
           'Yes. The tune is the official melody, note for note, checked against published scores; only the orchestration is new.'),
          ('What key and tempo is it in?',
           f'This arrangement is in {e(c.key_meter)}' + (f' and starts at about {c.bpm} beats per minute' if c.bpm else '')
           + (f'; it lasts {e(c.length)}.' if c.length else '.'))]
    return qa


def inst_page(c: Ctx, g) -> str:
    inst = g.inst
    parts = g.parts
    nat = native_phrase(c.arr.slug, inst.slug, c.ntitle)
    many = len(parts) > 1
    name = inst.name
    url = f'{c.base}{inst.slug}/'
    title = f'{c.title} {name} Sheet Music (PDF) & MIDI | {c.Kind} of {c.ct}'
    desc = (f'Free {name.lower()} sheet music and MIDI of {c.title}, {c.kind} of {c.country}, from a full '
            f'orchestral arrangement: {", ".join(p.label for p in parts)}. Download the PDF or MIDI.'
            + (f' {nat[:1].upper() + nat[1:]}.' if nat else ''))
    h1 = f'{e(c.title)}: {e(name)} Sheet Music'
    lead_bits = [f'{c.Kind} of {e(c.ct)}']
    if c.native and c.native[0] != c.title:
        lead_bits.append(f'<span lang="und">{e(c.native[0])}</span>')
    if nat:
        lead_bits.append(e(nat))
    lead = ' · '.join(lead_bits)
    items = [('Anthems', '/'), (c.ct, c.base), (name, url)]
    extra = [('Full orchestra', c.b.orchestra_mid, 'MIDI')]
    if c.b.chorus_mid:
        extra.append(('Chorus only', c.b.chorus_mid, 'MIDI'))
    extra.append(('Full score', c.b.full, 'PDF'))
    faq = [(f'Which {name.lower()} parts are in this arrangement?',
            f'{len(parts)} part{"s" if many else ""}: ' + ', '.join(e(p.label) for p in parts)
            + (f'. Parts are written for the {e(inst.name.lower())} {e(inst.transpose_name)}, so they read a transposition above the sounding pitch; the full score is in concert pitch.' if inst.transpose_name else '.'))]
    faq += common_faq(c, f'{name.lower()} sheet music')
    lead_sentence = (f'<p class="geo">{e(c.title)} is {c.kind} of {e(c.country)}. This page has the '
                     f'{e(name.lower())} part{"s" if many else ""} of a full orchestral arrangement as sheet music to read and print, '
                     f'with a PDF and a MIDI file for each part.</p>')
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': SITE + url, 'url': SITE + url, 'name': title, 'description': desc,
         'inLanguage': 'en', 'isPartOf': {'@id': SITE + '/#website'}, 'about': {'@id': f'{SITE}{c.base}#anthem'},
         'primaryImageOfPage': SITE + parts[0].pages[0], 'dateModified': TODAY.isoformat(),
         'author': {'@id': PERSON}},
        composition_ld(c),
        *[doc_ld(f'{c.title} {p.label} (MIDI)', p.mid, 'audio/midi') for p in parts if p.mid],
        crumbs_ld(items), faq_ld(faq)]}
    viewer = score_viewer(c, parts, inst.slug, name)
    body = layout(c, h1=h1, lead=lead + lead_sentence, crumbs_items=items, viewer=viewer,
                  side_dl=download_card(c, parts, extra), current=inst.slug, faq=faq)
    kw = ', '.join(x for x in [f'{c.title} {name.lower()} sheet music', f'{c.title} {name.lower()} pdf',
                              f'{c.title} {name.lower()} midi', f'national anthem of {c.ct} {name.lower()}', nat] if x)
    return head(title=title, desc=desc, url=url, image=parts[0].pages[0], jsonld=ld, keywords=kw) + header() + body + footer()


def country_page(c: Ctx) -> str:
    mel = c.b.melody
    nat = native_phrase(c.arr.slug, None, c.ntitle)
    url = c.base
    title = f'{c.title} Sheet Music & MIDI: {c.Kind} of {c.ct} (Orchestra)'
    desc = (f'{c.title}, {c.kind} of {c.country}: free melody sheet music'
            + (' with lyrics' if c.arr.lyrics else '') +
            f', a full orchestral MIDI and the sheet music of every instrument ({len(c.arr.parts)} parts) as PDF.'
            + (f' {nat[:1].upper() + nat[1:]}.' if nat else ''))
    h1 = f'{e(c.title)}: {c.Kind} of {e(c.ct)}'
    bits = []
    if c.m.get('english'):
        bits.append(e(c.m['english']))
    if c.native and c.native[0] != c.title:
        bits.append(f'<span lang="und">{e(c.native[0])}</span>')
    bits.append('Melody, orchestra MIDI and sheet music for every instrument')
    lead = ' · '.join(bits)
    lead_sentence = (f'<p class="geo">{e(c.title)} is {c.kind} of {e(c.country)}, with music by '
                     f'{e(c.m["music"])}. Below is its melody as sheet music'
                     + (' with the words' if c.arr.lyrics else '') +
                     f', a MIDI file of a full {len(c.arr.parts)}-part orchestral arrangement, and the sheet music for each instrument of that orchestra.</p>')
    items = [('Anthems', '/'), (c.ct, url)]
    extra = [('Full orchestra', c.b.orchestra_mid, 'MIDI')]
    if c.b.chorus_mid:
        extra.append(('Chorus only', c.b.chorus_mid, 'MIDI'))
    extra.append(('Full score', c.b.full, 'PDF'))
    faq = [(f'Can I download {c.title} as MIDI?',
            f'Yes: the melody alone, the full orchestral arrangement ({len(c.arr.parts)} parts, one track per part) and a short chorus version.'),
           ('Is there sheet music for my instrument?',
            'Pick your instrument in the menu above the score: ' + ', '.join(g.inst.name.lower() for g in c.b.insts) + ', plus the full score.')]
    faq += common_faq(c, 'sheet music')
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': SITE + url, 'url': SITE + url, 'name': title, 'description': desc,
         'inLanguage': 'en', 'isPartOf': {'@id': SITE + '/#website'}, 'about': {'@id': f'{SITE}{c.base}#anthem'},
         'primaryImageOfPage': SITE + mel.pages[0], 'dateModified': TODAY.isoformat(), 'author': {'@id': PERSON}},
        composition_ld(c),
        doc_ld(f'{c.title} full orchestra (MIDI)', c.b.orchestra_mid, 'audio/midi'),
        crumbs_ld(items), faq_ld(faq)]}
    viewer = score_viewer(c, [mel], 'melody', 'Melody')
    body = layout(c, h1=h1, lead=lead + lead_sentence, crumbs_items=items, viewer=viewer,
                  side_dl=download_card(c, [mel], extra), current='melody', faq=faq)
    kw = ', '.join([f'national anthem of {c.ct}', f'{c.title} sheet music', f'{c.title} midi', f'{c.title} orchestra',
                    *c.native[:3]] + ([nat] if nat else []))
    return head(title=title, desc=desc, url=url, image=mel.pages[0], jsonld=ld, keywords=kw) + header() + body + footer()


def full_page(c: Ctx) -> str:
    fs = c.b.full
    nat = native_phrase(c.arr.slug, 'full-score', c.ntitle)
    url = f'{c.base}full-score/'
    title = f'{c.title} Full Orchestra Score (PDF) | {c.Kind} of {c.ct}'
    desc = (f'The full orchestral score of {c.title}, {c.kind} of {c.country}: all {len(c.arr.parts)} parts '
            f'in concert pitch, free PDF and MIDI.' + (f' {nat[:1].upper() + nat[1:]}.' if nat else ''))
    h1 = f'{e(c.title)}: Full Orchestra Score'
    lead = f'{c.Kind} of {e(c.ct)} · {len(c.arr.parts)} parts in concert pitch' + (f' · {e(nat)}' if nat else '')
    lead_sentence = (f'<p class="geo">The conductor\'s score of an orchestral arrangement of {e(c.title)}, the national '
                     f'anthem of {e(c.country)}: every part on one page, in concert pitch, with empty staves hidden.</p>')
    items = [('Anthems', '/'), (c.ct, c.base), ('Full score', url)]
    extra = [('Full orchestra', c.b.orchestra_mid, 'MIDI')]
    if c.b.chorus_mid:
        extra.append(('Chorus only', c.b.chorus_mid, 'MIDI'))
    faq = common_faq(c, 'full score')
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': SITE + url, 'url': SITE + url, 'name': title, 'description': desc, 'inLanguage': 'en',
         'isPartOf': {'@id': SITE + '/#website'}, 'primaryImageOfPage': SITE + fs.pages[0], 'dateModified': TODAY.isoformat(),
         'author': {'@id': PERSON}},
        composition_ld(c),
        crumbs_ld(items), faq_ld(faq)]}
    viewer = score_viewer(c, [fs], 'full-score', 'Full score')
    body = layout(c, h1=h1, lead=lead + lead_sentence, crumbs_items=items, viewer=viewer,
                  side_dl=download_card(c, [fs], extra), current='full-score', faq=faq)
    return head(title=title, desc=desc, url=url, image=fs.pages[0], jsonld=ld) + header() + body + footer()


def write_all(built, man):
    for b in built:
        c = Ctx(b, man)
        out = DOCS / b.country
        (out / 'index.html').write_text(country_page(c))
        for g in b.insts:
            (out / g.inst.slug / 'index.html').write_text(inst_page(c, g))
        (out / 'full-score' / 'index.html').write_text(full_page(c))

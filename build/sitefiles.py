"""Site-wide files for anthem.adjiebrotots.com, from build/manifest.json and the pages in docs/:
home (/), 404.html, privacy/, sitemap.xml (with each anthem's share image), robots.txt, llms.txt, ads.txt, CNAME, .nojekyll.

    ~/.anthem-venv/bin/python build/sitefiles.py      (build.py runs it at the end)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape as xesc

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from pages import (kind, BRAND, DOCS, MANIFEST, PERSON, PUB, REGION_NAMES, SITE, SLOT_MULTI1, SLOT_MULTI2, SLOT_TOP, TODAY,  # noqa: E402
                   ad, country_title, e, flag, faq_block, faq_ld, footer, head, header)

from rights import CR, RIGHTS  # noqa: E402

REGION_ORDER = ['asia', 'europe', 'americas', 'middle-east', 'africa', 'oceania']


def home(man: dict) -> str:
    items_k = sorted(man.items(), key=lambda kv: country_title(kv[1]['country']).lower())
    items = [v for _k, v in items_k]
    total_parts = sum(v['parts'] for v in items)
    title = 'National Anthem Sheet Music & Orchestra MIDI | Anthem Madness'
    desc = (f'Free sheet music and MIDI of {len(items)} national anthems in full orchestral arrangements: read the full '
            f'score as the orchestra plays, the melody with lyrics and every instrument as a PDF part (violin, flute, trumpet ...).')
    sections = []
    for r in REGION_ORDER:
        group = [v for v in items if v['region'] == r]
        if not group:
            continue
        cards = []
        for v in group:
            nat = v['native'][0] if v.get('native') and v['native'][0] != v['title'] else ''
            search = ' '.join([v['country'], v['title'], nat, v.get('english') or '']).lower()
            cards.append(
                f'<a class="an-card" href="/{v["country_slug"]}/" data-search="{e(search)}">'
                f'<span class="an-country">{flag(v["country_slug"])}{e(country_title(v["country"]))}</span>'
                f'<span class="an-title">{e(v["title"])}</span>'
                + (f'<span class="an-nat" lang="und">{e(nat)}</span>' if nat else '')
                + f'<span class="an-meta">{len(v["insts"])} instruments · {v["parts"]} parts · {e(v.get("length", ""))}</span></a>')
        sections.append(f'<section class="region" aria-labelledby="r-{r}"><h2 id="r-{r}">{REGION_NAMES[r]}</h2>'
                        f'<div class="an-grid">{"".join(cards)}</div></section>')
        if r == 'europe':
            sections.append(ad(SLOT_MULTI1, fmt='autorelaxed', cls='ad-multi'))
    copyrighted = [country_title(v['country']) for k, v in items_k if RIGHTS.get(k, ('',))[0] == CR]
    faq = [('What licence are the arrangements under?',
            'It depends on the melody. Most national anthems are in the public domain: their arrangements here, with '
            'the sheet music and MIDI files, are licensed <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>, '
            'free for any use, commercial too, with credit and adaptations shared alike. Where the melody is still in '
            'copyright, it belongs to its owner and its use follows their rules (usually fine at meetings, education, '
            'ceremonies and community events, never in a defaming context or commercially without their licence); the '
            'arrangement itself asks only for credit (<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>).'),
           ('Which anthems here are still in copyright?',
            ', '.join(copyrighted) + '. Each of their pages names the owner where it is known.'),
           ('How do I credit an arrangement?',
            'Name the anthem, the arranger and the site, and the licence: "Advance Australia Fair", arranged for '
            'orchestra by adjiebrotot (anthem.adjiebrotots.com), CC BY-SA 4.0. In a concert programme, a video '
            'description or the credits of a recording, that one line is enough.')]
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebSite', '@id': SITE + '/#website', 'url': SITE + '/', 'name': BRAND,
         'alternateName': 'Anthem Madness by adjiebrotot', 'inLanguage': 'en', 'publisher': {'@id': PERSON},
         'description': desc},
        {'@type': 'CollectionPage', '@id': SITE + '/', 'url': SITE + '/', 'name': title, 'description': desc,
         'isPartOf': {'@id': SITE + '/#website'}, 'dateModified': TODAY.isoformat(),
         'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(items), 'itemListElement': [
             {'@type': 'ListItem', 'position': i + 1, 'url': f'{SITE}/{v["country_slug"]}/',
              'name': f'{v["title"]} ({kind(k)} of {country_title(v["country"])})'} for i, (k, v) in enumerate(items_k)]}},
        {'@type': 'Person', '@id': PERSON, 'name': 'Adjie Brotosukmono', 'alternateName': 'adjiebrotot',
         'url': 'https://www.adjiebrotots.com/'},
        faq_ld(faq)]}
    body = f'''<main class="container">
<div class="page-title home-title">
  <h1>National anthem sheet music &amp; orchestra MIDI</h1>
  <p class="geo">Sheet music and MIDI of {len(items)} national anthems arranged for full orchestra: the full score, a part for every instrument and the melody with its words. {total_parts} parts in all.</p>
  <label class="search"><span class="field-label">Find an anthem</span>
    <input id="anSearch" type="search" placeholder="Country or anthem, e.g. Brazil, Kimigayo" autocomplete="off"/></label>
</div>
{ad(SLOT_TOP, fmt='horizontal', cls='ad-top')}
{''.join(sections)}
<p class="no-match" id="noMatch" hidden>No anthem matches that search yet.</p>
{faq_block(faq)}
{ad(SLOT_MULTI2, fmt='autorelaxed', cls='ad-multi')}
</main>
'''
    first = next((v['image'] for v in items if v.get('image')), '/assets/img/anthem-madness-square.png')
    return head(title=title, desc=desc, url='/', image=first, jsonld=ld,
                keywords='national anthem sheet music, national anthem midi, national anthem orchestra, '
                         'anthem violin sheet music, anthem pdf') + header() + body + footer()


def not_found() -> str:
    body = '''<main class="container"><div class="page-title"><h1>Page not found</h1>
<p class="geo">That page is not here. Every anthem is listed on the <a href="/">home page</a>; each has a page per instrument at anthem.adjiebrotots.com/&lt;country&gt;/&lt;instrument&gt;/.</p></div></main>
'''
    h = head(title='Page not found | Anthem Madness', desc='Page not found.', url='/404.html',
             image='/assets/img/anthem-madness-square.png', jsonld={'@context': 'https://schema.org', '@type': 'WebPage'})
    return h.replace('<meta name="robots" content="index, follow, max-image-preview:large"/>',
                     '<meta name="robots" content="noindex"/>') + header() + body + footer()


def privacy() -> str:
    url = 'https://tool.adjiebrotots.com/privacy/'
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><title>Privacy Policy | Anthem Madness</title>
<meta name="robots" content="noindex"/><link rel="canonical" href="{url}"/><meta http-equiv="refresh" content="0; url={url}"/></head>
<body><p>Anthem Madness follows the Adjie family privacy policy: <a href="{url}">{url}</a>.</p></body></html>
'''


def sitemap() -> tuple[str, int]:
    rows = []
    for p in sorted(DOCS.rglob('index.html')):
        rel = p.parent.relative_to(DOCS).as_posix()
        if rel.startswith(('privacy', 'assets')):
            continue
        url = '/' if rel == '.' else f'/{rel}/'
        h = p.read_text()
        if 'name="robots" content="noindex' in h:      # moved pages (the old /full-score/) and the 404
            continue
        imgs = [(i[len(SITE):], '') for i in re.findall(r'<meta property="og:image" content="([^"]+\.png)"', h)
                if i.startswith(SITE + '/') and '/assets/' not in i][:1]
        depth = url.count('/') - 1
        prio = {0: '1.0', 1: '0.9'}.get(depth, '0.7')
        img = ''.join(f'<image:image><image:loc>{SITE}{s}</image:loc></image:image>' for s, _a in imgs)
        rows.append(f'<url><loc>{SITE}{url}</loc><lastmod>{TODAY.isoformat()}</lastmod><changefreq>monthly</changefreq>'
                    f'<priority>{prio}</priority>{img}</url>')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + '\n'.join(rows) + '\n</urlset>\n', len(rows))


ROBOTS = '''User-agent: *
# Content signals (contentsignals.org): this site may be shown in search results, quoted in
# AI answers, and used to train AI models.
Content-Signal: search=yes, ai-input=yes, ai-train=yes
Allow: /

User-agent: Googlebot
Allow: /

User-agent: Googlebot-Image
Allow: /

User-agent: bingbot
Allow: /

# AI / LLM crawlers: the pages are meant to be indexed and cited
User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: GPTBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Perplexity-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: meta-externalagent
Allow: /

User-agent: Applebot
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: Amazonbot
Allow: /

User-agent: DuckAssistBot
Allow: /

# LLM-readable site guide: https://anthem.adjiebrotots.com/llms.txt

Sitemap: https://anthem.adjiebrotots.com/sitemap.xml
Host: anthem.adjiebrotots.com
'''


def llms(man: dict) -> str:
    items_k = sorted(man.items(), key=lambda kv: country_title(kv[1]['country']).lower())
    lines = [f'# {BRAND} (Anthem Madness by adjiebrotot)', '',
             '> Free sheet music (PDF) and MIDI files of national anthems in full orchestral arrangements: the official '
             'melody, a part for every instrument and the full score, by Adjie Brotosukmono (adjiebrotot).', '',
             f'Canonical site: {SITE}/', f'Sitemap: {SITE}/sitemap.xml', f'Robots: {SITE}/robots.txt',
             'Creator: Adjie Brotosukmono (adjiebrotot), https://www.adjiebrotots.com/ (profile for LLMs: '
             'https://www.adjiebrotots.com/llms.txt). Sister sites: https://tool.adjiebrotots.com/ (tools), '
             'https://blog.adjiebrotots.com/ (blog).',
             'Access: free, no account. Licence: CC BY-SA 4.0 where the melody is in the public domain; where it is still '
             'in copyright the melody belongs to its owner and the arrangement is CC BY 4.0. Credit: arranged for '
             'orchestra by adjiebrotot (anthem.adjiebrotots.com).', '',
             '## How the site is laid out', '',
             f'- {SITE}/<country>/ : the anthem: the full orchestra score in concert pitch, drawn in the browser and played '
             'along with the orchestra MIDI in a SoundFont synth (the notes light up as they sound); full orchestra MIDI, chorus MIDI, '
             'melody MIDI, full-score PDF, facts (composer, lyricist, adoption, key, tempo, length).',
             f'- {SITE}/<country>/melody/ : the melody as a lead sheet (with lyrics where sung), PDF and MIDI.',
             f'- {SITE}/<country>/<instrument>/ : that instrument\'s parts as sheet music, a PDF and a MIDI per part. '
             'Instruments: violin, viola, cello, double-bass, piccolo, flute, oboe, clarinet (in B flat), bassoon, '
             'horn (French horn in F), trumpet (in B flat), trombone, tuba, timpani, percussion, harp, piano, choir.',
             '- The melodies are the official tunes, note for note; only the orchestration is new.', '',
             '## Anthems', '']
    for k, v in items_k:
        nat = v['native'][0] if v.get('native') and v['native'][0] != v['title'] else ''
        lines.append(f'- [{v["title"]}]({SITE}/{v["country_slug"]}/): {kind(k).lower()} of {country_title(v["country"])}'
                     + (f' ({nat})' if nat else '') + f'; {v.get("key_meter", "")}, {v.get("length", "")}; '
                     f'instruments: {", ".join(v["insts"])}.')
    return '\n'.join(lines) + '\n'


def main():
    man = json.loads(MANIFEST.read_text())
    (DOCS / 'index.html').write_text(home(man))
    (DOCS / '404.html').write_text(not_found())
    (DOCS / 'privacy').mkdir(exist_ok=True)
    (DOCS / 'privacy' / 'index.html').write_text(privacy())
    sm, n = sitemap()
    (DOCS / 'sitemap.xml').write_text(sm)
    (DOCS / 'robots.txt').write_text(ROBOTS)
    (DOCS / 'llms.txt').write_text(llms(man))
    (DOCS / 'ads.txt').write_text(f'google.com, {PUB.replace("ca-", "")}, DIRECT, f08c47fec0942fa0\n')
    (DOCS / 'CNAME').write_text('anthem.adjiebrotots.com\n')
    (DOCS / '.nojekyll').write_text('')
    print(f'home: {len(man)} anthems, sitemap: {n} urls')


if __name__ == '__main__':
    main()

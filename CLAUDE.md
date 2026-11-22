# CLAUDE.md

**Anthem Madness by adjiebrotot**: anthem.adjiebrotots.com, a static GitHub Pages site (folder `docs/`) with free
sheet music (PDF) and MIDI of national anthems in full orchestral arrangements. Every page is generated from an
**adjiebrotot/anthem-orchestra** checkout by `build/`; never edit `docs/` pages by hand (rebuild instead).
**At the end of every run, append new lessons to the log below.**

## What is where

| Path | What |
|---|---|
| `build/build.py` | the build: per arrangement, MusicXML per part, Verovio SVG pages, page images (WebP), per-part MIDI, the HTML pages; then `sitefiles.py`. `--no-render` rewrites the pages and keeps the images |
| `build/data.py` | reads one arrangement from anthem-orchestra (`work/<slug>/song.json`, `analysis.json`, `guide.json`, `lyrics-map.json`, `output/orchestra/<slug>.mid`, `work/youtube/anthems.py`, `DESCRIPTIONS.md`) |
| `build/engrave.py` | song.json notes to MusicXML: quantising (32nd and triplet grids), voices, ties, triplets, beams, rolls, let-ring, keys, dynamics, tempo and rehearsal marks |
| `build/instruments.py` | which instrument page a part goes on, its clef and transposition, the percussion key map |
| `build/i18n.py` | search words in each anthem's language (`LANG_OF`, `WORDS`) |
| `build/pages.py` | HTML of the anthem, instrument and full-score pages (SEO head, JSON-LD, ad slots) |
| `build/sitefiles.py` | home, 404, privacy redirect, sitemap (with images), robots.txt, llms.txt, ads.txt, CNAME, .nojekyll |
| `build/render.cjs` | Playwright Chromium: SVG pages to PNG page images with a light watermark |
| `build/check.py` | `notes`: every engraved note vs the arrangement; `site`: links, JSON-LD, sitemap, PDF buttons, size |
| `build/manifest.json` | what is on the site (one row per anthem); partial builds merge into it |
| `docs/assets/` | design system copied from adjiebrotot/tool (fonts, dark/light tokens, theme.js, dropdown) + `site.css`, `site.js` (PDF in the browser), the logo |

## Commands

```bash
python3 -m venv ~/.anthem-venv && ~/.anthem-venv/bin/pip install verovio mido Pillow   # once
PY=~/.anthem-venv/bin/python
$PY build/check.py notes                         # every note of every arrangement (about 10 min, must say 0 mismatches)
$PY build/build.py --orchestra ../anthem-orchestra            # all anthems (about 25 min); --only <slug> ... for some
$PY build/sitefiles.py                           # home, sitemap ... again (build.py runs it)
$PY build/check.py site                          # must say "site ok"
$PY build/build.py --no-render                   # pages only (HTML change), keeps the page images (about 8 min)
```

**PDFs are not stored.** A PDF button (`data-pdf`, `data-pages`, `data-footer`) makes the PDF in the reader's
browser the way tool.adjiebrotots.com/mdtopdf does: `site.js` lays the page images out on a print-only A4 stage
with the big watermark and a footer, sets the document title to the file name and calls `window.print()` (a
one-time tip says to pick "Save as PDF"). The watermark CSS in `site.css` (`.pdf-wm`) must stay the scaled copy of
the one `render.cjs` draws on the images (88 px, letter-spacing .5 mm on 1240 px, -38deg, centred).

Node with Playwright (pre-installed in cloud sessions) runs `build/render.cjs`; `pdfinfo`/`pdftotext` (poppler)
are used by the site check. Local preview: `python3 -m http.server -d docs 8765`; off the live domain the ad slots
show as labelled boxes.

## A new arrangement in anthem-orchestra

1. It needs `work/<slug>/song.json`, `analysis.json`, `guide.json` and an entry in `work/youtube/anthems.py`
   (country, title, native, music, words, adopted, language, about, orch, region) and a DESCRIPTIONS.md row.
2. Add its language to `LANG_OF` in `build/i18n.py` (and a `WORDS` table if the language is new).
3. `$PY build/check.py notes --only <slug>`, then `$PY build/build.py --only <slug>`, then `check.py site`.
4. Look at a few rendered parts (`docs/<country>/<instrument>/img/*.webp`): beams, rolls, harp, percussion.

## Rules

- **Notes are the arrangement's notes.** `check.py notes` must report 0 mismatches before shipping.
- **URLs are kept.** `/<country>/`, `/<country>/<instrument>/`, `/<country>/full-score/` and the file names are
  indexed by search engines: never rename a country slug, instrument slug or part key once published.
- **No PDF files in `docs/`** (`check.py site` fails on one): PDFs are made in the browser from the page images.
- **Ads:** AdSense `ca-pub-8730116101825381`, slot ids in `build/pages.py`. Never put a unit right beside or under
  a download button (accidental clicks get the account flagged). Auto ads (anchor, vignette) are set in AdSense.
- Brand: "Anthem Madness by adjiebrotot", logo from adjiebrotot/personal-website `logos/anthem-madness*`.
- Page copy: plain English, no em-dashes (`check.py site` flags them).
- Rights: the tunes are public national anthems; the arrangements are adjiebrotot's own. Lyrics are shown under
  the melody only where the anthem's words are sung (from `lyrics-map.json`).

## Lessons Learned log

Append new entries at the top. Format: `YYYY-MM-DD: lesson (context / fix)`.

- 2026-11-22: Stored PDFs were 71 of 170 MB: the PDF is now made in the browser from the page images through the
  print pipeline (mdtopdf's approach; no PDF library, no extra files), so `docs/` is 100 MB and a rebuild changes
  PDFs and pages together. Test it headless: stub `window.print`, click the button, then `page.emulateMedia('print')`
  and `page.pdf({preferCSSPageSize: true})` (A4, one page per image, watermark aligned with the image's own).

- 2026-11-22: DESCRIPTIONS.md names a piece without "the" ("Philippines", "UAE") while anthems.py writes "the
  Philippines": match the overview row on the plain name, or the facts go blank and an anthem with no key signature
  in its source (UAE) falls back to C (it was engraved in C for F). Full build: 53 anthems, 858 pages, 1,062 PDFs,
  170 MB, about 25 minutes.

- 2026-11-22: Engrave from `song.json`, not the exported MIDI: the export is humanised (onsets off the grid), while
  song.json has every onset on the beat grid with articulation-shortened lengths (a half note lasts 1.9 beats):
  join an end to the next onset when the gap is under 0.2 beat or 16 %, then snap to the 32nd or triplet grid.
- 2026-11-22: Verovio does not beam MusicXML by itself: write `<beam>` per beat (levels for 16ths/32nds, hooks).
  Rolls (6+ strokes of one pitch at <= 0.26 beat) become one tremolo note; a long last stroke is its own note.
  Harp, piano and timpani notes ring over the next onsets: cut them at the next onset (one voice of chords).
- 2026-11-22: Verovio's `renderToMIDI` plays a tremolo as repeated strokes and unpitched notes at their display
  position: the note check accepts strokes inside a roll and compares drum onsets only. 98,606 notes, 0 mismatches.
- 2026-11-22: Key changes come from `analysis.json` `key_signatures` (source bars): the i-th note of
  `analysis.melody.notes` is the i-th note of `guide.json`, which maps a source barline to the arrangement bar.
- 2026-11-22: A build module named `site.py` clashes with Python's `site`: it is `sitefiles.py`.

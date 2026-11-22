# CLAUDE.md

**Anthem Madness by adjiebrotot**: anthem.adjiebrotots.com, a static GitHub Pages site (folder `docs/`) with free
sheet music and MIDI of national anthems in full orchestral arrangements. The score is drawn in the reader's browser
by Verovio and plays along with a recording of the orchestra, the notes lighting up as they sound (like MuseScore).
`/<country>/` is the full orchestra score, `/<country>/melody/` the lead sheet, `/<country>/<instrument>/` the parts.
Every page is generated from an **adjiebrotot/anthem-orchestra** checkout by `build/`; never edit `docs/` pages by
hand (rebuild instead). **At the end of every run, append new lessons to the log below.**

## What is where

| Path | What |
|---|---|
| `build/build.py` | the build: per arrangement, MusicXML per part, converted to compact MEI (`*.mei.xml`, the file the page draws), A4 page counts for the PDF buttons, the export MIDI's tempo map, per-part MIDI, one share image, the HTML pages; then `sitefiles.py`. `--no-render` keeps the share images |
| `build/audio.py` | the orchestra recording per anthem (`docs/<country>/<title>-orchestra.m4a`): renders song.json with anthem-orchestra's music-production skill, encodes 96 kbps AAC, deletes the render; skips anthems that have one (`--force`) |
| `build/data.py` | reads one arrangement from anthem-orchestra (`work/<slug>/song.json`, `analysis.json`, `guide.json`, `lyrics-map.json`, `output/orchestra/<slug>.mid`, `work/youtube/anthems.py`, `DESCRIPTIONS.md`); staff abbreviations |
| `build/engrave.py` | song.json notes to MusicXML: quantising (32nd and triplet grids), voices, ties, triplets, beams, rolls, let-ring, keys, dynamics, tempo and rehearsal marks |
| `build/instruments.py` | which instrument page a part goes on, its clef and transposition, the percussion key map |
| `build/i18n.py` | search words in each anthem's language (`LANG_OF`, `WORDS`) |
| `build/pages.py` | HTML of the country (full score), melody and instrument pages, the player bar, the `/full-score/` redirect (SEO head, JSON-LD, ad slots) |
| `build/sitefiles.py` | home, 404, privacy redirect, sitemap (with share images), robots.txt, llms.txt, ads.txt, CNAME, .nojekyll |
| `build/render.cjs` | Playwright Chromium: the share image (top of the full score's first A4 page) |
| `build/check.py` | `notes`: every note of the shipped MEI vs the arrangement; `site`: links, JSON-LD, sitemap, score files, recordings, no PDF or WebP |
| `build/manifest.json` | what is on the site (one row per anthem); partial builds merge into it |
| `docs/assets/` | design system copied from adjiebrotot/tool (fonts, dark/light tokens, theme.js, dropdown) + `site.css`, `site.js` (theme, menus, search, ads), `score.js` (viewer, player, PDF), the logo |

## Commands

```bash
python3 -m venv ~/.anthem-venv && ~/.anthem-venv/bin/pip install verovio==6.4.1 mido Pillow   # once
PY=~/.anthem-venv/bin/python
$PY build/check.py notes                         # every note of every arrangement (about 10 min, must say 0 mismatches)
$PY build/audio.py                               # recordings that are missing (about 2 min each; set-up below)
$PY build/build.py --orchestra ../anthem-orchestra            # all anthems (about 8 min); --only <slug> ... for some
$PY build/sitefiles.py                           # home, sitemap ... again (build.py runs it)
$PY build/check.py site                          # must say "site ok"
$PY build/build.py --no-render                   # no Chromium: keeps the share images
```

**How a page works** (`docs/assets/js/score.js`). Verovio's JS toolkit (jsDelivr, `verovio@6.4.1`, the version the
Python build uses: keep the two equal) loads the page's MEI and lays it out for the screen width (zoom buttons, the
words get more room on a phone). The player plays `<title>-orchestra.m4a`; `#amPlayer` holds the export MIDI's
tempo map ([beat, second, bpm]), which turns the recording's time into beats, and Verovio's timemap gives every note's
start and end in beats: notes sounding get the class `playing`, a band behind the notes follows them (it covers the
measure while the part rests), the page scrolls with the music, a click on a note plays from there, speed 0.5 to 1.25.
Instrument pages play the full orchestra and highlight their part.

**The recording** is the music-production render of song.json, whose `composition.mid` is the exported MIDI note for
note, so the sync holds. Set-up, once per machine, in anthem-orchestra: `bash scripts/music-setup.sh orchestra` and
the `vcsl_world` bank (`fetch_soundbanks.py --only vcsl_world`, see `build/audio.py`). A changed arrangement needs
`audio.py --force --only <slug>`. Test seeking with a server that answers Range requests (GitHub Pages does;
`python3 -m http.server` does not, and the audio then always restarts at 0:00).

**PDFs are not stored.** A PDF button (`data-pdf`, `data-src`, `data-full`, `data-print`, `data-footer`) draws the
score again with Verovio at A4 (`print_options()` in build.py = `printOptions()` in score.js, plus the button's
`data-print` overrides), puts the anthem.adjiebrotots.com watermark faint BEHIND the notes and a footer on each page,
sets the document title to the file name and calls `window.print()` (a one-time tip says to pick "Save as PDF").
Vector pages, nothing over the notes.

Node with Playwright (pre-installed in cloud sessions) runs `build/render.cjs`; ffprobe reads the recording length.
Local preview: any static server on `docs/` that answers Range requests; off the live domain the ad slots show as
labelled boxes. In headless tests route `cdn.jsdelivr.net` to a local copy of the toolkit (`npm pack verovio@6.4.1`).

## A new arrangement in anthem-orchestra

1. It needs `work/<slug>/song.json`, `analysis.json`, `guide.json` and an entry in `work/youtube/anthems.py`
   (country, title, native, music, words, adopted, language, about, orch, region) and a DESCRIPTIONS.md row.
2. Add its language to `LANG_OF` in `build/i18n.py` (and a `WORDS` table if the language is new).
3. `$PY build/check.py notes --only <slug>`, `$PY build/audio.py --only <slug>`, `$PY build/build.py --only <slug>`,
   then `check.py site`.
4. Open a few pages in a browser: beams, rolls, harp, percussion; press play and click a note.

## Rules

- **Notes are the arrangement's notes.** `check.py notes` must report 0 mismatches before shipping.
- **URLs are kept.** `/<country>/`, `/<country>/melody/`, `/<country>/<instrument>/` and the file names are indexed by
  search engines: never rename a country slug, instrument slug or part key once published. `/<country>/full-score/`
  is a redirect to `/<country>/` (the full score moved there): keep it.
- **No PDF or page images in `docs/`** (`check.py site` fails on one): the score is drawn and printed in the browser.
- **Ads:** AdSense `ca-pub-8730116101825381`, slot ids in `build/pages.py` (Display 2 sits under the score card, not
  inside the score, which re-lays itself out). Never put a unit right beside or under a download button (accidental clicks get the account flagged). Auto ads (anchor, vignette) are set in AdSense.
- Brand: "Anthem Madness by adjiebrotot", logo from adjiebrotot/personal-website `logos/anthem-madness*`.
- Page copy: plain English, no em-dashes (`check.py site` flags them).
- Rights: the tunes are public national anthems; the arrangements are adjiebrotot's own. Lyrics are shown under
  the melody only where the anthem's words are sung (from `lyrics-map.json`).

## Lessons Learned log

Append new entries at the top. Format: `YYYY-MM-DD: lesson (context / fix)`.

- 2026-11-22: The score moved from WebP page images (a watermark across the notes, no way to follow playback) to
  Verovio in the browser: the build ships compact MEI (`getMEI({removeIds})` + whitespace closed up: the full score
  is 200 KB, 9 KB gzipped; `.mei.xml` so GitHub Pages gzips it) and the page lays it out per screen width. Verovio
  drops MusicXML credit font sizes, so the title and subtitle collided: build.py writes the MEI `pgHead` itself
  (x-large title, `lb`, small subtitle; part left and arranger right on a line of their own).
- 2026-11-22: Verovio turns one part's key change into a score-wide `scoreDef`, giving percussion staves a key
  signature: `pitched_key_changes()` rewrites it as staffDefs of the pitched staves. A full score's first page (every
  staff) was taller than A4 at scale 28 (the bottom staves fell off the page and under the footer): `a4_pages()`
  closes up `spacingStaff` until every page fits and passes it to the PDF button (`data-print`).
- 2026-11-22: Audio: the music-production render of song.json takes about 100 s and 4 GB per anthem (delete it after
  encoding); its notes equal the export MIDI's exactly and it starts at beat 0, so the export's tempo map (with its
  rubato ramps) syncs recording and score. 101 minutes of music at 96 kbps AAC = about 75 MB, the size of the WebP
  pages it replaced. Arrangements use the `vcsl_world` bank too (not in `music-setup.sh orchestra`).
- 2026-11-22: Clicks rarely hit a note's glyphs (the SVG between head and stem is transparent): the player picks the
  nearest notehead within 30 px. The cursor is a band BEHIND the notes (the SVG has no background), so the red notes
  stay visible. Lyrics at phone width collided until `lyricSize` 3.6 and `spacingLinear` 0.35.

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

# CLAUDE.md

**Anthem Madness by adjiebrotot**: anthem.adjiebrotots.com, a static GitHub Pages site (folder `docs/`) with free
sheet music and MIDI of national anthems in full orchestral arrangements. The score is drawn in the reader's browser
by Verovio and plays along with the orchestra MIDI in a SoundFont synth, the notes lighting up as they sound (like
MuseScore).
`/<country>/` is the full orchestra score, `/<country>/melody/` the lead sheet, `/<country>/<instrument>/` the parts.
Every page is generated from an **adjiebrotot/anthem-orchestra** checkout by `build/`; never edit `docs/` pages by
hand (rebuild instead). **At the end of every run, append new lessons to the log below.**

## What is where

| Path | What |
|---|---|
| `build/build.py` | the build: per arrangement, MusicXML per part, converted to compact MEI (`*.mei.xml`, the file the page draws), A4 page counts for the PDF buttons, the player's data (MIDI, its SoundFont files, tempo map, gain, each part's synth channel), per-part MIDI, one share image, the HTML pages; then `sitefiles.py`. `--no-render` keeps the share images |
| `build/synth.mjs` + `build/package.json` | Node: splits the orchestra app's `Pawchestra.sf3` (adjiebrotot/orchestra `assets/soundfont/`) into `docs/assets/sf/<bank>/<program>.sf3` for the presets the MIDI files use (+ `index.json`), measures each orchestra MIDI's loudness as the synth plays it (`loudness.json`), bundles spessasynth_lib 4.4.5 + core 4.4.7 into `docs/assets/js/vendor/` |
| `build/data.py` | reads one arrangement from anthem-orchestra (`work/<slug>/song.json`, `analysis.json`, `guide.json`, `lyrics-map.json`, `output/orchestra/<slug>.mid`, `work/youtube/anthems.py`, `DESCRIPTIONS.md`); staff abbreviations |
| `build/engrave.py` | song.json notes to MusicXML: quantising (32nd and triplet grids), voices, ties, triplets, beams, rolls, let-ring, keys, dynamics, tempo and rehearsal marks |
| `build/instruments.py` | which instrument page a part goes on, its clef and transposition, the percussion key map |
| `build/i18n.py` | search words in each anthem's language (`LANG_OF`, `WORDS`) |
| `build/pages.py` | HTML of the country (full score), melody and instrument pages, the player bar, the `/full-score/` redirect (SEO head, JSON-LD, ad slots) |
| `build/sitefiles.py` | home, 404, privacy redirect, sitemap (with share images), robots.txt, llms.txt, ads.txt, CNAME, .nojekyll |
| `build/render.cjs` | Playwright Chromium: the share image (top of the full score's first A4 page) |
| `build/check.py` | `notes`: every note of the shipped MEI vs the arrangement; `site`: links, JSON-LD, sitemap, score files, player files, no PDF or WebP |
| `build/manifest.json` | what is on the site (one row per anthem); partial builds merge into it |
| `docs/assets/` | design system copied from adjiebrotot/tool (fonts, dark/light tokens, theme.js, dropdown) + `site.css`, `site.js` (theme, menus, search, ads), `img/flags/` (one SVG flag per country, from the flag-icons npm package, MIT; `FLAGS` in pages.py maps a country slug to its file), `score.js` (viewer, player, PDF), `js/vendor/` (spessasynth), `sf/` (SoundFont per preset), the logo |

## Commands

```bash
python3 -m venv ~/.anthem-venv && ~/.anthem-venv/bin/pip install verovio==6.4.1 mido Pillow   # once
PY=~/.anthem-venv/bin/python
$PY build/check.py notes                         # every note of every arrangement (about 10 min, must say 0 mismatches)
(cd build && npm install)                        # once: spessasynth + esbuild, pinned (Node 24)
node build/synth.mjs --soundfont ../adjiebrotot/orchestra/assets/soundfont/Pawchestra.sf3   # new MIDI or SoundFont (about 3 s per new MIDI)
$PY build/build.py --orchestra ../anthem-orchestra            # all anthems (about 8 min); --only <slug> ... for some
$PY build/sitefiles.py                           # home, sitemap ... again (build.py runs it)
$PY build/check.py site                          # must say "site ok"
$PY build/build.py --no-render                   # no Chromium: keeps the share images
```

**How a page works** (`docs/assets/js/score.js`). Verovio's JS toolkit (jsDelivr, `verovio@6.4.1`, the version the
Python build uses: keep the two equal) loads the page's MEI and lays it out for the screen width (zoom buttons, the
words get more room on a phone). Play loads spessasynth (an AudioWorklet SoundFont synth, the core the orchestra app
runs) with only the presets the page's orchestra MIDI uses, then plays that MIDI through the anthem's gain (to -16
LUFS, as the app does) and a limiter. `#amPlayer` holds the MIDI's tempo map ([beat, second, bpm]), which turns the
sequencer's time into beats, and Verovio's timemap gives every note's start and end in beats: notes sounding get the
class `playing`, a band behind the notes follows them (it covers the measure while the part rests), the page scrolls
with the music, a click on a note plays from there, speed 0.5 to 1.25. Instrument pages highlight their part and
offer the full orchestra, the part alone or the orchestra without it (channel mute; a part's channel is port * 16 +
channel, spessasynth's multi-port numbering).

**PDFs are not stored.** A PDF button (`data-pdf`, `data-src`, `data-full`, `data-print`, `data-footer`) draws the
score again with Verovio at A4 (`print_options()` in build.py = `printOptions()` in score.js, plus the button's
`data-print` overrides), puts the anthem.adjiebrotots.com watermark faint BEHIND the notes and a footer on each page,
sets the document title to the file name and calls `window.print()` (a one-time tip says to pick "Save as PDF").
Vector pages, nothing over the notes.

Node with Playwright (pre-installed in cloud sessions) runs `build/render.cjs`. Local preview:
`python3 -m http.server -d docs 8765`; off the live domain the ad slots show as labelled boxes. In headless tests route `cdn.jsdelivr.net` to a local copy of the toolkit (`npm pack verovio@6.4.1`).

## A new arrangement in anthem-orchestra

1. It needs `work/<slug>/song.json`, `analysis.json`, `guide.json` and an entry in `work/youtube/anthems.py`
   (country, title, native, music, words, adopted, language, about, orch, region) and a DESCRIPTIONS.md row.
2. Add its language to `LANG_OF` in `build/i18n.py` (and a `WORDS` table if the language is new).
3. `$PY build/check.py notes --only <slug>`, `$PY build/build.py --only <slug>` (it asks for `node build/synth.mjs`
   when the MIDI is new: its loudness, or an instrument with no SoundFont file yet), then `check.py site`.
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

- 2026-11-23: PDF footer over the notes: Verovio's auto page breaks can overfill an A4 page (India's full score
  page 6 ran past the paper), and `a4_pages()` let the content reach into the bottom margin. Now print uses
  `adjustPageHeight` (the SVG is as tall as its music), `a4_pages()` fits content plus both margins inside A4, the
  bottom margin is 14 mm, and score.js draws each page from the top with `preserveAspectRatio="xMidYMin meet"`, so an
  overfilled page is scaled down rather than cut or run under the footer. Test with `page.pdf()` + `pdftoppm`.
- 2026-11-23: The sample credits (simple and standard) live in the FAQ answer `#credit`; the download card's note only
  links there. Names come from `composer()` / `lyricist()` in rights.py (anthems.py's music and words text with
  years stripped, `COMPOSER` / `LYRICIST` where it does not read as a name). "More national anthems" is a random
  8 per page, seeded by the page URL (stable across rebuilds). No ads between the about sections and the FAQ.
  site.css, site.js and score.js load as `?v=<content hash>` (`v()` in pages.py): a CSS change once sat behind
  readers' caches. Nav is Home + About.

- 2026-11-23: Licence per anthem (the user's rule): a public-domain melody makes the arrangement CC BY-SA 4.0; a
  melody still in copyright (composer died under 70 years ago, or a state or body holds it, like ASEAN) belongs to
  its owner, used as they permit, and the arrangement asks only for credit (CC BY 4.0). `build/rights.py` holds
  status, owner (None = "its rights holders in <country>") and the tune's year per slug; a new anthem needs a row.
  The FAQ answers real questions (licence and credit, who wrote it, what inspired the orchestration, how it ranks
  among the site's anthems), not "can I play the MIDI". Nav was Home + About me (now About); no watermark talk in page copy.

- 2026-11-23: Rebuilt after the music audit of anthem-orchestra (every arrangement made playable by a symphony
  orchestra and its voicing cleaned: `output/orchestra/AUDIT.md` there): 53 MIDIs, 53 chorus cuts, 356 scores
  changed; `check.py notes` 98,250 notes, 0 mismatches; `check.py site` ok. `build.py` copies a MIDI and then stops
  at its missing loudness, so for a batch of new MIDIs copy them over the old `docs/<country>/*-orchestra.mid` first
  and run `synth.mjs` once (SoundFont: a shallow clone of the public adjiebrotot/orchestra, real file, no LFS). The
  id-only `.mei.xml` rewrites also differ in a generation timestamp: compare with ids and `YYYY-MM-DDT...` stripped
  before `git checkout` (706 of 1,062 were unchanged).

- 2026-11-22: Flags beside country names (home and "more anthems" cards, the country page title, the melody and
  instrument leads) are SVG files, never emoji (Windows draws flag emoji as two letters). Wikimedia answers 429 to
  this container, so they come from the flag-icons npm package (`npm pack flag-icons@7.5.0`, `flags/4x3/`: drawn
  from the Wikipedia SVGs, and it has ASEAN and EU). A new country needs a `FLAGS` row and its file (`check.py site`
  fails without). A rebuild rewrites every `.mei.xml` with new random Verovio ids only: `git checkout -- '*.mei.xml'`
  when the notes did not change.

- 2026-11-22: The score moved from WebP page images (a watermark across the notes, no way to follow playback) to
  Verovio in the browser: the build ships compact MEI (`getMEI({removeIds})` + whitespace closed up: the full score
  is 200 KB, 9 KB gzipped; `.mei.xml` so GitHub Pages gzips it) and the page lays it out per screen width. Verovio
  drops MusicXML credit font sizes, so the title and subtitle collided: build.py writes the MEI `pgHead` itself
  (x-large title, `lb`, small subtitle; part left and arranger right on a line of their own).
- 2026-11-22: Verovio turns one part's key change into a score-wide `scoreDef`, giving percussion staves a key
  signature: `pitched_key_changes()` rewrites it as staffDefs of the pitched staves. A full score's first page (every
  staff) was taller than A4 at scale 28 (the bottom staves fell off the page and under the footer): `a4_pages()`
  closes up `spacingStaff` until every page fits and passes it to the PDF button (`data-print`).
- 2026-11-22: Sound: play the MIDI in the browser, not a rendered recording (the user's call: rendering 53 anthems
  with the music skill took 2 min and 2-5 GB of cache each and filled the disk; 75 MB of audio to store). spessasynth
  with the orchestra app's SoundFont split per preset: 20 presets, 13 MB, a page loads its own (5-9 MB) on the first
  play and the browser caches them across anthems. The export MIDI starts at beat 0 and its tempo map (rubato ramps
  included) syncs sequencer and score. Raw synth output is quiet (-27 to -32 LUFS): synth.mjs renders each MIDI in
  Node with spessasynth_core and BS.1770-measures it; the page gains it to -16 LUFS into a limiter.
- 2026-11-22: spessasynth reports a new channel's settings before the channel (the second MIDI port, parts 17+):
  score.js skips reports for channels the page does not have yet, else every one throws. A part on port 1 is synth
  channel 16 + its channel. When testing a part's level, measure over several seconds: long notes leave gaps.
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

// The browser synth of the score player: the orchestra app's SoundFont split per preset, and spessasynth_lib.
//
//   cd build && npm install                      (once: spessasynth_lib, spessasynth_core, esbuild, pinned)
//   node build/synth.mjs [--soundfont <adjiebrotot/orchestra checkout>/assets/soundfont/Pawchestra.sf3]
//
// 1. docs/assets/sf/<bank>/<program>.sf3: every preset of Pawchestra.sf3 (adjiebrotot/orchestra, the SoundFont the
//    orchestra app plays these MIDI files with: VSCO 2 CE and VCSL by Versilian Studios over GeneralUser GS) that a
//    MIDI file in docs/ plays, one SF3 file each (Ogg samples copied, no new encode), and docs/assets/sf/index.json
//    ([{bank, program, name, file, size}]), which build.py reads to list each page's presets. Bank 128 = drum kits.
// 2. docs/assets/js/vendor/spessasynth.js: spessasynth_lib (+ core) bundled as one ES module, and its AudioWorklet
//    processor beside it. score.js imports them when a reader presses play.
// 3. docs/assets/sf/loudness.json: the integrated loudness (ITU-R BS.1770: K-weighted, gated, LUFS) of every
//    orchestra MIDI as this synth plays it (spessasynth_core rendering in Node, the engine the page runs), keyed by
//    site path with the file's hash; build.py turns it into the page's gain to -16 LUFS, like the orchestra app.
//    Only new or changed MIDI files are rendered (about 5 s each).
// Run it again when the SoundFont changes, an anthem uses an instrument that has no file yet (build.py says so), or a
// MIDI changes.
import { copyFileSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

import { build } from 'esbuild';
import { createHash } from 'node:crypto';

import { BasicMIDI, BasicSoundBank, SoundBankLoader, SpessaSynthProcessor, SpessaSynthSequencer } from 'spessasynth_core';

const HERE = dirname(fileURLToPath(import.meta.url));
const DOCS = join(HERE, '..', 'docs');
const SF = join(DOCS, 'assets', 'sf');
const VENDOR = join(DOCS, 'assets', 'js', 'vendor');
const args = process.argv.slice(2);
const at = args.indexOf('--soundfont');
const SOUNDFONT = at >= 0 ? args[at + 1]
  : join(HERE, '..', '..', 'adjiebrotot', 'orchestra', 'assets', 'soundfont', 'Pawchestra.sf3');

function midiFiles(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) { if (name !== 'assets') out.push(...midiFiles(p)); }
    else if (name.endsWith('.mid')) out.push(p);
  }
  return out;
}
const buf = (p) => { const b = readFileSync(p); return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength); };

await BasicSoundBank.isSF3DecoderReady;
const bank = SoundBankLoader.fromArrayBuffer(buf(SOUNDFONT));
const used = new Map();     // "bank:program" -> preset
for (const f of midiFiles(DOCS)) {
  const midi = BasicMIDI.fromArrayBuffer(buf(f), f);
  for (const preset of midi.getUsedProgramsAndKeys(bank).keys()) {
    const b = preset.isGMGSDrum || preset.isDrum ? 128 : preset.bankMSB;
    used.set(`${b}:${preset.program}`, { preset, bank: b });
  }
}
rmSync(SF, { recursive: true, force: true });
const index = [];
for (const { preset, bank: b } of [...used.values()].sort((x, y) => x.bank - y.bank || x.preset.program - y.preset.program)) {
  const one = new BasicSoundBank();
  one.soundBankInfo = { ...bank.soundBankInfo, name: preset.name };
  one.clonePreset(preset);
  one.flush();
  const data = new Uint8Array(one.writeSF2());
  const file = `${b}/${preset.program}.sf3`;
  mkdirSync(join(SF, String(b)), { recursive: true });
  writeFileSync(join(SF, file), data);
  index.push({ bank: b, program: preset.program, name: preset.name, file: `/assets/sf/${file}`, size: data.byteLength });
}
writeFileSync(join(SF, 'index.json'), JSON.stringify(index) + '\n');
copyFileSync(join(dirname(SOUNDFONT), 'LICENSE.txt'), join(SF, 'GeneralUser-GS-LICENSE.txt'));
const total = index.reduce((s, e) => s + e.size, 0);
console.log(`${index.length} presets, ${(total / 1048576).toFixed(1)} MB in ${relative(process.cwd(), SF)}`);

mkdirSync(VENDOR, { recursive: true });
await build({ entryPoints: [join(HERE, 'node_modules', 'spessasynth_lib', 'dist', 'index.js')], bundle: true,
  format: 'esm', minify: true, target: 'es2020', outfile: join(VENDOR, 'spessasynth.js'), logLevel: 'warning',
  legalComments: 'none' });
copyFileSync(join(HERE, 'node_modules', 'spessasynth_lib', 'dist', 'spessasynth_processor.min.js'),
  join(VENDOR, 'spessasynth_processor.min.js'));
copyFileSync(join(HERE, 'node_modules', 'spessasynth_lib', 'LICENSE'), join(VENDOR, 'spessasynth-LICENSE.txt'));
console.log('spessasynth bundled in', relative(process.cwd(), VENDOR));

// ---------------------------------------------------------------------------------------------- loudness
function biquad(x, [b0, b1, b2, a1, a2]) {
  const y = new Float32Array(x.length);
  let x1 = 0, x2 = 0, y1 = 0, y2 = 0;
  for (let i = 0; i < x.length; i++) {
    const v = b0 * x[i] + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2;
    x2 = x1; x1 = x[i]; y2 = y1; y1 = v; y[i] = v;
  }
  return y;
}
// the K-weighting filters of ITU-R BS.1770-4 at 48 kHz
const SHELF = [1.53512485958697, -2.69169618940638, 1.19839281085285, -1.69065929318241, 0.73248077421585];
const HIGHPASS = [1.0, -2.0, 1.0, -1.99004745483398, 0.99007225036621];
function lufs(left, right, rate) {
  const k = [left, right].map((c) => biquad(biquad(c, SHELF), HIGHPASS));
  const block = Math.round(0.4 * rate), hop = Math.round(0.1 * rate), z = [];
  for (let s = 0; s + block <= left.length; s += hop) {
    let sum = 0;
    for (const c of k) for (let i = s; i < s + block; i++) sum += c[i] * c[i];
    z.push(sum / block);
  }
  const L = (ms) => -0.691 + 10 * Math.log10(ms);
  const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
  const abs = z.filter((m) => L(m) > -70);
  if (!abs.length) return -70;
  const rel = L(mean(abs)) - 10;
  return Math.round(L(mean(abs.filter((m) => L(m) > rel))) * 10) / 10;
}
const LOUD = join(SF, 'loudness.json');
let loud = {};
try { loud = JSON.parse(readFileSync(join(HERE, '.cache', 'loudness.json'), 'utf8')); } catch { /* first run */ }
const RATE = 48000;
let rendered = 0;
for (const f of midiFiles(DOCS).filter((f) => f.endsWith('-orchestra.mid'))) {
  const key = '/' + relative(DOCS, f).split('\\').join('/');
  const hash = createHash('sha256').update(readFileSync(f)).digest('hex').slice(0, 16);
  if (loud[key]?.hash === hash) continue;
  const midi = BasicMIDI.fromArrayBuffer(buf(f), f);
  const synth = new SpessaSynthProcessor(RATE, { eventsEnabled: false });
  synth.soundBankManager.addSoundBank(bank, 'main');
  await synth.ready;
  synth.setSystemParameter?.('autoAllocateVoices', true);
  const seq = new SpessaSynthSequencer(synth);
  seq.loadNewSongList([midi]);
  seq.play();
  const n = Math.ceil(RATE * (midi.duration + 2));
  const left = new Float32Array(n), right = new Float32Array(n);
  for (let done = 0; done < n; done += 128) {
    seq.processTick();
    synth.process(left, right, done, Math.min(128, n - done));
  }
  let peak = 0;
  for (let i = 0; i < n; i++) peak = Math.max(peak, Math.abs(left[i]), Math.abs(right[i]));
  loud[key] = { hash, lufs: lufs(left, right, RATE), peak: Math.round(peak * 1000) / 1000 };
  rendered++;
  console.log('loudness', key, loud[key].lufs, 'LUFS, peak', loud[key].peak);
}
mkdirSync(join(HERE, '.cache'), { recursive: true });
writeFileSync(join(HERE, '.cache', 'loudness.json'), JSON.stringify(loud));
writeFileSync(LOUD, JSON.stringify(Object.fromEntries(Object.entries(loud).sort().map(([k, v]) => [k, { lufs: v.lufs, peak: v.peak, hash: v.hash }]))) + '\n');
console.log(`loudness: ${rendered} rendered, ${Object.keys(loud).length} in ${relative(process.cwd(), LOUD)}`);

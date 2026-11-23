/* Anthem Madness score viewer, player and PDF.

   The score is drawn here, in the reader's browser, by Verovio (the version build.py engraves with) from the page's
   MEI file, laid out for the width of the screen. The player plays the orchestra MIDI in a SoundFont synth and lights
   up the notes it is playing: Verovio's timemap gives every note's start and end in beats, and the MIDI's tempo map
   (in the page, #amPlayer) turns the player's time into beats. Click a note to play from there.
   PDF: the score again at A4 (the options build.py counts the pages with), the watermark behind the notes and a
   footer, through the browser's print dialog ("Save as PDF"). Nothing is stored as PDF. */
(function () {
  'use strict';
  var VEROVIO = 'https://cdn.jsdelivr.net/npm/verovio@6.4.1/dist/verovio-toolkit-wasm.js';
  var body = document.body;

  function printOptions(full) {      // build.py print_options()
    var o = { pageWidth: 2100, pageHeight: 2970, scale: full ? 28 : 40, font: 'Leland', footer: 'none', header: 'auto',
      adjustPageHeight: true, svgViewBox: true, svgRemoveXlink: true, pageMarginTop: 80, pageMarginBottom: 140,
      pageMarginLeft: 90, pageMarginRight: 90, spacingSystem: full ? 14 : 10 };
    if (full) { o.condense = 'auto'; o.condenseFirstPage = false; }
    return o;
  }

  var ready = null;
  function verovioReady() {
    if (ready) return ready;
    ready = new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = VEROVIO; s.async = true; s.crossOrigin = 'anonymous';
      s.onload = function () {
        var m = window.verovio && window.verovio.module;
        if (!m) { reject(new Error('Verovio did not start')); return; }
        if (m.calledRun) { resolve(); return; }
        var prev = m.onRuntimeInitialized;
        m.onRuntimeInitialized = function () { if (prev) prev(); resolve(); };
      };
      s.onerror = function () { ready = null; reject(new Error('Verovio did not load')); };
      document.head.appendChild(s);
    });
    return ready;
  }
  var texts = {};
  function fetchText(url) {
    if (!texts[url]) texts[url] = fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + ': ' + r.status);
      return r.text();
    }).catch(function (e) { delete texts[url]; throw e; });
    return texts[url];
  }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) {} return null; }
  function el(tag, cls, html) { var x = document.createElement(tag); if (cls) x.className = cls; if (html) x.innerHTML = html; return x; }
  function fmt(s) { s = Math.max(0, Math.floor(s || 0)); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }

  /* ------------------------------------------------------------------ timeline: MIDI seconds <-> beats */
  var dataEl = document.getElementById('amPlayer');
  var data = dataEl ? JSON.parse(dataEl.textContent) : null;
  var tempo = data && data.tempo && data.tempo.length ? data.tempo : [[0, 0, 120]];
  function secToBeat(s) {
    var i = tempo.length - 1;
    while (i > 0 && tempo[i][1] > s) i--;
    return tempo[i][0] + (s - tempo[i][1]) * tempo[i][2] / 60;
  }
  function beatToSec(b) {
    var i = tempo.length - 1;
    while (i > 0 && tempo[i][0] > b) i--;
    return tempo[i][1] + (b - tempo[i][0]) * 60 / tempo[i][2];
  }

  /* ------------------------------------------------------------------ the score on screen */
  var view = document.getElementById('scoreView');
  var tk = null, events = [], noteBeat = {}, idx = -1, lastBeat = 0, on = {}, loadedSrc = '', layoutW = 0;
  var full = view && view.getAttribute('data-full') === '1';
  var zoomKey = 'am-zoom-' + (full ? 'full' : 'part');
  var zoom = parseFloat(store(zoomKey)) || 1;
  var cursor = el('div', 'score-cursor'), curSystem = null, follow = store('am-follow') !== '0', namesW = 0, showCursor = false;

  // on screen the score is one continuous line of music that scrolls sideways (the page already has the title)
  function screenOptions(w) {
    var base = full ? (w < 640 ? 24 : 30) : (w < 640 ? 34 : 42);
    var scale = Math.max(12, Math.round(base * zoom));
    return { pageWidth: 60000, pageHeight: 60000, scale: scale, adjustPageHeight: true, adjustPageWidth: true,
      breaks: 'none', font: 'Leland', footer: 'none', header: 'none', svgViewBox: true,
      svgRemoveXlink: true, pageMarginTop: 50, pageMarginBottom: 40, pageMarginLeft: 50, pageMarginRight: 80,
      condense: 'none', lyricSize: 3.6, spacingLinear: !full && w < 640 ? 0.35 : 0.25 };   // room for the words on a phone
  }

  function status(msg, spin) {
    view.innerHTML = '';
    view.appendChild(el('div', 'score-status', (spin ? '<div class="spinner"></div>' : '') + '<span></span>'));
    view.querySelector('.score-status span').textContent = msg;
  }

  function draw() {
    var w = view.clientWidth;
    if (!tk || !w) return;
    layoutW = w;
    namesW = 0;
    tk.setOptions(screenOptions(w));
    tk.redoLayout();
    view.innerHTML = '<div class="score-page"><div class="score-scroll"><div class="score-inner">' + tk.renderToSVG(1) +
      '</div></div></div>';
    var svg = view.querySelector('.score-inner svg'), vb = svg && svg.viewBox && svg.viewBox.baseVal;
    if (vb && vb.width) { svg.setAttribute('width', vb.width); svg.setAttribute('height', vb.height); }   // 1 unit = 1 px
    view.setAttribute('aria-busy', 'false');
    curSystem = null;
    pinNames();
    Object.keys(on).forEach(function (id) { var e = document.getElementById(id); if (e) e.classList.add('playing'); });
    placeCursor(true);
  }

  /* the instrument names (and the brackets joining the staves) stay at the left edge while the music scrolls: a copy
     of the start of the line, cut off where the staff lines begin, laid over the scrolling score */
  function pinNames() {
    var page = view.querySelector('.score-page'), scroll = page && page.querySelector('.score-scroll');
    var svg = scroll && scroll.querySelector('svg');
    if (!svg || !svg.querySelector('.label')) return;
    var left = scroll.querySelector('.score-inner').getBoundingClientRect().left, x = Infinity;
    var m = svg.querySelector('g.measure');
    Array.prototype.forEach.call(m ? m.querySelectorAll('g.staff') : [], function (st) {
      Array.prototype.forEach.call(st.children, function (c) {
        if (c.tagName.toLowerCase() === 'path') x = Math.min(x, c.getBoundingClientRect().left);
      });
    });
    if (x === Infinity) return;
    var w = Math.round(x - left);
    if (w < 8 || w > scroll.clientWidth * 0.6) return;
    var names = el('div', 'score-names');
    names.setAttribute('aria-hidden', 'true');
    names.style.width = w + 'px';
    names.style.height = Math.ceil(svg.getBoundingClientRect().height) + 'px';
    var copy = svg.cloneNode(true);
    Array.prototype.forEach.call(copy.querySelectorAll('[id]'), function (n) { n.removeAttribute('id'); });
    copy.removeAttribute('id');
    names.appendChild(copy);
    page.appendChild(names);
    namesW = w;
    function edge() { page.classList.toggle('is-scrolled', scroll.scrollLeft > 2); }
    scroll.addEventListener('scroll', edge, { passive: true });
    edge();
  }

  function load(src) {
    loadedSrc = src;
    view.setAttribute('aria-busy', 'true');
    if (!tk) status('Loading the score…', true);
    return Promise.all([verovioReady(), fetchText(src)]).then(function (r) {
      if (src !== loadedSrc) return;
      if (!tk) tk = new window.verovio.toolkit();
      tk.setOptions(screenOptions(view.clientWidth || 800));
      if (!tk.loadData(r[1])) throw new Error('the score could not be read');
      events = tk.renderToTimemap({ includeMeasures: true, includeRests: false }) || [];
      noteBeat = {};
      events.forEach(function (e) { (e.on || []).forEach(function (id) { noteBeat[id] = e.qstamp; }); });
      clearAll();
      draw();
      seekTo(lastBeat, true);
    }).catch(function (e) {
      if (src !== loadedSrc) return;
      status('The score could not be drawn here (' + e.message + '). The MIDI downloads still work.', false);
    });
  }

  /* highlight: walk the timemap to the beat being played */
  function clearAll() {
    Object.keys(on).forEach(function (id) { var e = document.getElementById(id); if (e) e.classList.remove('playing'); });
    on = {}; idx = -1;
  }
  function setNote(id, yes) {
    if (yes) on[id] = 1; else delete on[id];
    var e = document.getElementById(id);
    if (e) e.classList.toggle('playing', yes);
  }
  function seekTo(beat, quiet) {
    if (beat < lastBeat - 1e-6) clearAll();
    lastBeat = beat;
    var moved = false;
    while (idx + 1 < events.length && events[idx + 1].qstamp <= beat + 1e-4) {
      idx++;
      var ev = events[idx];
      (ev.off || []).forEach(function (id) { setNote(id, false); });
      (ev.on || []).forEach(function (id) { setNote(id, true); });
      if ((ev.on && ev.on.length) || ev.measureOn) moved = true;
    }
    if (moved || quiet) placeCursor(quiet);
  }
  function lastIndex(test) { for (var i = idx; i >= 0; i--) if (test(events[i])) return i; return -1; }
  function cursorNote() {     // the latest onset at or before the beat
    for (var i = idx; i >= 0; i--) if (events[i].on && events[i].on.length) {
      for (var k = 0; k < events[i].on.length; k++) { var e = document.getElementById(events[i].on[k]); if (e) return e; }
    }
    return null;
  }
  function placeCursor(quiet) {
    // while the part rests (a new measure began after its last note ended), the cursor covers that measure
    var mi = lastIndex(function (e) { return !!e.measureOn; }), ni = lastIndex(function (e) { return e.on && e.on.length; });
    var resting = mi > ni && !Object.keys(on).length;
    var note = idx >= 0 ? (resting ? document.getElementById(events[mi].measureOn) : cursorNote()) : null;
    cursor.classList.toggle('is-measure', !!(note && resting));
    if (!note) { cursor.style.display = 'none'; return; }
    var sys = note.closest('.system'), page = note.closest('.score-inner'), meas = resting ? note : note.closest('.measure');
    if (!sys || !page) return;
    // the cursor spans the staves of the system (not the tempo marks and titles above them)
    var staves = (meas || sys).querySelectorAll('g.staff'), top = Infinity, bottom = -Infinity;
    Array.prototype.forEach.call(staves, function (st) {
      var l = st.querySelector('path, rect') ? st.getBoundingClientRect() : null;
      if (l && l.height) { top = Math.min(top, l.top); bottom = Math.max(bottom, l.bottom); }
    });
    var sr = sys.getBoundingClientRect();
    if (top === Infinity) { top = sr.top; bottom = sr.bottom; }
    var head = resting ? (note.querySelector('.staff') || note) : (note.querySelector('.notehead') || note);
    var hr = head.getBoundingClientRect(), pr = page.getBoundingClientRect();
    if (cursor.parentNode !== page) page.appendChild(cursor);
    cursor.style.display = 'block';
    cursor.style.left = (hr.left - pr.left + hr.width / 2) + 'px';
    cursor.style.width = resting ? Math.max(18, hr.width - 6) + 'px' : '';
    cursor.style.marginLeft = resting ? (-Math.max(18, hr.width - 6) / 2) + 'px' : '';
    cursor.style.top = (top - pr.top - 4) + 'px';
    cursor.style.height = (bottom - top + 8) + 'px';
    if (follow && (playing() || showCursor)) keepInLine(page.parentNode, hr.left + hr.width / 2);
    showCursor = false;
    if (!follow || quiet || !playing()) { curSystem = sys; return; }
    var barEl = document.getElementById('player');
    var minTop = barEl ? barEl.getBoundingClientRect().bottom + 12 : 12, maxBottom = window.innerHeight - 12;
    if (sys !== curSystem && bottom - top <= maxBottom - minTop) {
      // a new line of music: bring the whole system into view if it is not
      curSystem = sys;
      if (top < minTop || bottom > maxBottom) scrollByPx(top - minTop);
      return;
    }
    curSystem = sys;
    // a system taller than the screen (a full score on a phone): keep the notes being played in view
    var a = Infinity, z = -Infinity;
    Object.keys(on).forEach(function (id) {
      var x = document.getElementById(id);
      if (!x) return;
      var r = x.getBoundingClientRect();
      a = Math.min(a, r.top); z = Math.max(z, r.bottom);
    });
    if (a === Infinity) return;
    if (a < minTop || z > maxBottom) scrollByPx(Math.min(a - minTop, z - maxBottom + (maxBottom - minTop) / 3));
  }
  // sideways: the notes being played stay in the left part of the line, clear of the pinned names
  var lastSide = 0;
  function keepInLine(scroll, x) {
    if (!scroll) return;
    var r = scroll.getBoundingClientRect(), from = r.left + namesW + 24, to = r.left + scroll.clientWidth * 0.75;
    if (x >= from && x <= to) return;
    var now = Date.now();
    if (now - lastSide < 300) return;
    lastSide = now;
    var target = scroll.scrollLeft + x - (r.left + namesW + (scroll.clientWidth - namesW) * 0.2);
    scroll.scrollTo({ left: Math.max(0, target), behavior: 'smooth' });
  }
  var lastScroll = 0;
  function scrollByPx(dy) {
    var now = Date.now();
    if (Math.abs(dy) < 2 || now - lastScroll < 350) return;
    lastScroll = now;
    window.scrollTo({ top: window.scrollY + dy, behavior: 'smooth' });
  }

  /* ------------------------------------------------------------------ player
     The orchestra MIDI (the file the orchestra app plays) in spessasynth, a SoundFont synth in an AudioWorklet, with
     the app's SoundFont (Pawchestra: VSCO 2 CE and VCSL over GeneralUser GS), one file per instrument
     (build/synth.mjs): the page loads only the instruments its MIDI plays, on the first press of play. */
  var VENDOR = '/assets/js/vendor/';
  var seq = null, synthRef = null, ctx = null, loading = null, raf = 0, wantPlay = false, pendingSec = 0, rate = 1;
  var mix = 'all', partChannel = view && view.hasAttribute('data-channel') ? +view.getAttribute('data-channel') : -1;
  // instrument pages: the full orchestra, the part alone, or the orchestra without it (to play along)
  function applyMix() {
    if (!synthRef || partChannel < 0) return;
    synthRef.midiChannels.forEach(function (ch, i) {
      var muted = mix === 'solo' ? i !== partChannel : mix === 'minus' ? i === partChannel : false;
      if (ch.systemParameters.isMuted !== muted) ch.setSystemParameter('isMuted', muted);
    });
  }
  var bar = document.getElementById('player');
  var btn = bar && bar.querySelector('.pl-play'), seek = bar && bar.querySelector('.pl-seek');
  var cur = bar && bar.querySelector('.pl-cur'), dur = bar && bar.querySelector('.pl-dur');
  var title = bar && bar.querySelector('.pl-title'), titleText = title ? title.textContent : '';
  var total = data ? data.length || 0 : 0;
  function playing() { return !!(seq && !seq.paused); }
  function now() { return seq ? seq.currentHighResolutionTime : pendingSec; }
  function fetchBuf(url) {
    return fetch(url).then(function (r) { if (!r.ok) throw new Error(url + ': ' + r.status); return r.arrayBuffer(); });
  }
  function say(msg) { if (title) title.textContent = msg || titleText; }
  function ensureSynth() {
    if (loading) return loading;
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC || !window.AudioWorkletNode) return Promise.reject(new Error('this browser cannot play it'));
    ctx = new AC();
    bar.classList.add('pl-wait');
    var files = data.sf || [], done = 0;
    say('Loading the orchestra…');
    function count(p) { return p.then(function (b) { done++; say('Loading the orchestra… ' + done + ' of ' + (files.length + 1)); return b; }); }
    loading = Promise.all([
      ctx.audioWorklet.addModule(VENDOR + 'spessasynth_processor.min.js'),
      import(VENDOR + 'spessasynth.js'),
      count(fetchBuf(data.midi))
    ].concat(files.map(function (f) { return count(fetchBuf(f)); }))).then(function (r) {
      var lib = r[1], midi = r[2], banks = r.slice(3);
      var synth = new lib.WorkletSynthesizer(ctx);
      // the orchestra app's level: the piece's gain to -16 LUFS (build.py, measured by build/synth.mjs), then a limiter
      var gain = ctx.createGain(), limiter = ctx.createDynamicsCompressor();
      gain.gain.value = Math.pow(10, (data.gain || 0) / 20);
      limiter.threshold.value = -2; limiter.knee.value = 0; limiter.ratio.value = 20;
      limiter.attack.value = 0.002; limiter.release.value = 0.15;
      synth.connect(gain); gain.connect(limiter); limiter.connect(ctx.destination);
      // spessasynth reports a new channel's default settings before the channel itself (the orchestra MIDIs open a
      // second port, channels 17 to 32): skip those reports, the channel starts with the defaults anyway
      var receive = synth.receiveEventCallback;
      synth.receiveEventCallback = function (ev) {
        var ch = ev && ev.data && ev.data.channel;
        if (typeof ch === 'number' && !this.midiChannels[ch]) return;
        return receive.call(this, ev);
      };
      return Promise.resolve(synth.isReady).then(function () {
        return banks.reduce(function (p, b, i) {
          return p.then(function () { return synth.soundBankManager.addSoundBank(b, 'am' + i); });
        }, Promise.resolve());
      }).then(function () {
        seq = new lib.Sequencer(synth, { skipToFirstNoteOn: false });
        seq.loopCount = 0;
        seq.playbackRate = rate;
        return new Promise(function (resolve) {
          seq.eventHandler.addEvent('songChange', 'am', function () { resolve(); });
          seq.eventHandler.addEvent('songEnded', 'am', ended);
          seq.loadNewSongList([{ binary: midi, fileName: 'anthem.mid' }]);
        });
      }).then(function () {
        synthRef = synth;
        applyMix();
        if (seq.duration) total = seq.duration;
        seq.currentTime = pendingSec;
        bar.classList.remove('pl-wait');
        say('');
      });
    }).catch(function (e) {
      loading = null;
      bar.classList.remove('pl-wait');
      bar.classList.add('pl-error');
      say('The orchestra could not play here (' + e.message + ')');
      setBtn(false);
      throw e;
    });
    return loading;
  }
  function ended() { setBtn(false); clearAll(); lastBeat = 0; pendingSec = 0; cursor.style.display = 'none'; ui(0); }
  function setBtn(p) {
    if (!btn) return;
    btn.classList.toggle('is-playing', p);
    btn.setAttribute('aria-label', p ? 'Pause' : 'Play');
  }
  function ui(t) {
    if (cur) cur.textContent = fmt(t);
    if (dur) dur.textContent = fmt(total);
    if (seek && total) { seek.value = Math.round(t / total * 1000); seek.style.setProperty('--p', (t / total * 100) + '%'); }
  }
  function loop() {
    cancelAnimationFrame(raf);
    (function tick() {
      if (!seq) return;
      var t = now();
      seekTo(secToBeat(t));
      ui(t);
      if (playing()) raf = requestAnimationFrame(tick);
      else setBtn(false);
    })();
  }
  function jump(sec) {
    sec = Math.max(0, Math.min(sec, (total || 1e9) - 0.05));
    pendingSec = sec;
    if (seq) seq.currentTime = sec;
    curSystem = null;
    showCursor = true;
    seekTo(secToBeat(sec), !playing());
    ui(sec);
  }
  function start() {
    if (ctx && ctx.state !== 'running') ctx.resume();
    seq.play();
    setBtn(true);
    loop();
  }
  function toggle() {
    if (playing()) { seq.pause(); setBtn(false); pendingSec = seq.currentTime; return; }
    try { if (window.gtag && !toggle.sent) { toggle.sent = 1; window.gtag('event', 'play_score', { page_path: location.pathname }); } } catch (e) {}
    if (seq) { start(); return; }
    wantPlay = true;
    setBtn(true);
    ensureSynth().then(function () { if (wantPlay) start(); }, function () {});
    if (ctx && ctx.state !== 'running') ctx.resume();   // inside the click: browsers start audio only on a gesture
  }

  if (bar && data && data.midi) {
    bar.hidden = false;
    ui(0);
    btn.addEventListener('click', function () { if (loading && !seq) { wantPlay = !wantPlay; setBtn(wantPlay); return; } toggle(); });
    seek.addEventListener('input', function () { jump(seek.value / 1000 * total); });
    var sp = bar.querySelector('.pl-speed');
    if (sp) sp.addEventListener('change', function () { rate = parseFloat(sp.value) || 1; if (seq) seq.playbackRate = rate; });
    var mx = bar.querySelector('.pl-mix');
    if (mx) mx.addEventListener('change', function () { mix = mx.value; applyMix(); });
    var fb = bar.querySelector('.pl-follow');
    if (fb) {
      fb.setAttribute('aria-pressed', follow ? 'true' : 'false');
      fb.addEventListener('click', function () {
        follow = !follow; store('am-follow', follow ? '1' : '0');
        fb.setAttribute('aria-pressed', follow ? 'true' : 'false');
        if (follow) { curSystem = null; placeCursor(false); }
      });
    }
    document.addEventListener('keydown', function (e) {
      var t = e.target, tag = t && t.tagName;
      if (e.code !== 'Space' || e.ctrlKey || e.metaKey || e.altKey || /^(INPUT|SELECT|TEXTAREA|BUTTON|A)$/.test(tag || '') || (t && t.isContentEditable)) return;
      if (!view || !view.getBoundingClientRect || view.getBoundingClientRect().bottom < 0) return;
      e.preventDefault(); toggle();
    });
    if (view) view.addEventListener('click', function (e) {    // a note (or the nearest one to the click): play from there
      var n = noteAt(e);
      if (!n) return;
      jump(beatToSec(noteBeat[n.id]) + 0.001);
      if (!playing()) toggle();
    });
  }
  function noteAt(e) {
    var n = e.target.closest && e.target.closest('g.note');
    if (n && noteBeat[n.id] !== undefined) return n;
    var page = e.target.closest && e.target.closest('.score-page');
    if (!page) return null;
    var best = null, bd = 30 * 30;
    Array.prototype.forEach.call(page.querySelectorAll('g.note'), function (x) {
      if (noteBeat[x.id] === undefined) return;
      var h = (x.querySelector('.notehead') || x).getBoundingClientRect();
      var dx = e.clientX - (h.left + h.width / 2), dy = e.clientY - (h.top + h.height / 2), d = dx * dx + dy * dy;
      if (d < bd) { bd = d; best = x; }
    });
    return best;
  }
  if (bar) Array.prototype.forEach.call(bar.querySelectorAll('[data-zoom]'), function (z) {
    z.addEventListener('click', function () {
      zoom = Math.max(0.6, Math.min(2.2, zoom * (z.getAttribute('data-zoom') === '+' ? 1.15 : 1 / 1.15)));
      store(zoomKey, zoom.toFixed(3));
      draw();
    });
  });

  /* ------------------------------------------------------------------ parts (Violins I, Violins II ...) */
  var tabs = document.querySelectorAll('.part-tab');
  function show(key, push) {
    var src = '';
    Array.prototype.forEach.call(tabs, function (b) {
      var yes = b.getAttribute('data-part') === key;
      b.classList.toggle('active', yes);
      b.setAttribute('aria-selected', yes ? 'true' : 'false');
      if (yes) {
        src = b.getAttribute('data-src');
        if (b.hasAttribute('data-channel')) { partChannel = +b.getAttribute('data-channel'); applyMix(); }
      }
    });
    Array.prototype.forEach.call(document.querySelectorAll('.part-note[data-part]'), function (p) {
      p.hidden = p.getAttribute('data-part') !== key;
    });
    Array.prototype.forEach.call(document.querySelectorAll('.dl-row[data-part]'), function (r) {
      r.classList.toggle('active', r.getAttribute('data-part') === key);
    });
    if (push && history.replaceState) history.replaceState(null, '', '#' + key);
    if (src && src !== loadedSrc && view) load(src);
  }
  Array.prototype.forEach.call(tabs, function (b) {
    b.addEventListener('click', function () { show(b.getAttribute('data-part'), true); });
  });

  if (view) {
    var first = view.getAttribute('data-src');
    var k = location.hash.slice(1);
    var tab = k && document.querySelector('.part-tab[data-part="' + k + '"]');
    if (tab) show(k, false); else load(first);
    var rt = 0;
    window.addEventListener('resize', function () {
      clearTimeout(rt);
      rt = setTimeout(function () { if (tk && Math.abs(view.clientWidth - layoutW) > 4) draw(); }, 200);
    });
  }

  /* ------------------------------------------------------------------ PDF */
  var stage = null, tip = null, overlay = null, pending = null, oldTitle = '';
  function ensureUi() {
    if (stage) return;
    stage = el('div'); stage.id = 'pdfStage'; stage.setAttribute('aria-hidden', 'true'); body.appendChild(stage);
    overlay = el('div'); overlay.id = 'pdfOverlay';
    overlay.innerHTML = '<div class="pdf-overlay-card"><div class="spinner"></div><div class="pdf-overlay-msg" id="pdfOverlayMsg">Preparing pages…</div></div>';
    body.appendChild(overlay);
    tip = el('div'); tip.id = 'printTip'; tip.setAttribute('aria-hidden', 'true');
    tip.innerHTML = '<div class="print-tip-card" role="dialog" aria-modal="true" aria-labelledby="printTipTitle">' +
      '<div class="print-tip-title" id="printTipTitle">Save the sheet music as PDF</div>' +
      '<p class="print-tip-text">A print dialog opens next. Set the <strong>Destination</strong> (or printer) to:</p>' +
      '<div class="print-tip-do">“Save as PDF” <span>(Chrome, Edge, Android)</span>, “Save to PDF” in Firefox, or PDF › Save as PDF on a Mac and Share › Save to Files on an iPhone</div>' +
      '<p class="print-tip-text">Or pick your printer to print the parts straight away. Paper: A4, margins: none.</p>' +
      '<label class="print-tip-skip"><input type="checkbox" id="printTipSkip"/> Don’t show this again</label>' +
      '<div class="print-tip-actions"><button class="btn btn-ghost" id="printTipCancel" type="button">Cancel</button>' +
      '<button class="btn btn-primary" id="printTipGo" type="button">Open print dialog</button></div></div>';
    body.appendChild(tip);
    document.getElementById('printTipCancel').addEventListener('click', closeTip);
    tip.addEventListener('click', function (e) { if (e.target === tip) closeTip(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && tip.classList.contains('visible')) closeTip(); });
    document.getElementById('printTipGo').addEventListener('click', function () {
      if (document.getElementById('printTipSkip').checked) store('am-skip-pdf-tip', '1');
      closeTip();
      if (pending) runPrint(pending);
    });
    window.addEventListener('afterprint', cleanup);
  }
  function closeTip() { tip.classList.remove('visible'); tip.setAttribute('aria-hidden', 'true'); }
  function cleanup() {
    if (stage) stage.innerHTML = '';
    if (oldTitle) { document.title = oldTitle; oldTitle = ''; }
  }
  function requestPdf(b) {
    ensureUi();
    pending = b;
    if (store('am-skip-pdf-tip') === '1') { runPrint(b); return; }
    document.getElementById('printTipSkip').checked = false;
    tip.classList.add('visible'); tip.setAttribute('aria-hidden', 'false');
    document.getElementById('printTipGo').focus();
  }
  function runPrint(b) {
    var src = b.getAttribute('data-src');
    var footer = b.getAttribute('data-footer') || 'anthem.adjiebrotots.com';
    var name = (b.getAttribute('data-pdf') || 'sheet-music.pdf').replace(/\.pdf$/, '');
    var isFull = b.getAttribute('data-full') === '1', extra = {};
    try { extra = JSON.parse(b.getAttribute('data-print') || '{}'); } catch (e) {}
    if (!src) return;
    cleanup();
    overlay.classList.add('visible');
    document.getElementById('pdfOverlayMsg').textContent = 'Preparing the pages…';
    Promise.all([verovioReady(), fetchText(src), document.fonts && document.fonts.ready]).then(function (r) {
      var ptk = new window.verovio.toolkit();
      var po = printOptions(isFull);
      Object.keys(extra).forEach(function (k) { po[k] = extra[k]; });   // what build.py counted the pages with
      ptk.setOptions(po);
      if (!ptk.loadData(r[1])) throw new Error('the score could not be read');
      var n = ptk.getPageCount();
      for (var i = 1; i <= n; i++) {
        var pg = el('div', 'pdf-page');
        pg.appendChild(el('div', 'pdf-wm', 'anthem.adjiebrotots.com'));
        pg.insertAdjacentHTML('beforeend', ptk.renderToSVG(i));
        // the SVG is as tall as its music: from the top of the page, scaled down if Verovio overfilled the page
        var svg = pg.querySelector('svg');
        if (svg) svg.setAttribute('preserveAspectRatio', 'xMidYMin meet');
        pg.appendChild(el('div', 'pdf-ft')).textContent = footer + ' · page ' + i + ' of ' + n;
        stage.appendChild(pg);
      }
      if (ptk.destroy) ptk.destroy();
      overlay.classList.remove('visible');
      oldTitle = document.title;
      document.title = name;
      try { if (window.gtag) window.gtag('event', 'file_download', { file_name: name + '.pdf', file_extension: 'pdf', link_text: 'PDF' }); } catch (e) {}
      requestAnimationFrame(function () { requestAnimationFrame(function () { window.print(); }); });
    }).catch(function (e) {
      overlay.classList.remove('visible');
      alert('The PDF could not be made here (' + e.message + ').');
    });
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('button[data-pdf]');
    if (b) { e.preventDefault(); requestPdf(b); }
  });
})();

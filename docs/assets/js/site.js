/* Anthem Madness pages: theme toggle, instrument menu, home search, ad units (the score, player and PDF: score.js). */
(function () {
  'use strict';
  var body = document.body;

  // theme: theme.js sets the starting class and saves a reader's click; the click itself is ours
  var t = document.getElementById('themeToggle');
  if (t) t.addEventListener('click', function () {
    var light = !body.classList.contains('light');
    body.classList.toggle('light', light);
    document.documentElement.setAttribute('data-abt-theme', light ? 'light' : 'dark');
  });

  // instrument menu: each instrument is its own page
  var sel = document.getElementById('instSel');
  if (sel) sel.addEventListener('change', function () { if (sel.value && sel.value !== location.pathname) location.href = sel.value; });

  // home: filter the anthem cards as the reader types
  var q = document.getElementById('anSearch');
  if (q) q.addEventListener('input', function () {
    var v = q.value.trim().toLowerCase(), any = false;
    Array.prototype.forEach.call(document.querySelectorAll('.region'), function (r) {
      var shown = 0;
      Array.prototype.forEach.call(r.querySelectorAll('.an-card'), function (c) {
        var on = !v || c.getAttribute('data-search').indexOf(v) >= 0;
        c.hidden = !on; if (on) shown++;
      });
      r.hidden = !shown; if (shown) any = true;
    });
    var nm = document.getElementById('noMatch'); if (nm) nm.hidden = any;
  });

  /* "More national anthems": whole rows only, about eight cards (7 columns: one row; 3 columns: 3 x 3). */
  function fitMore() {
    document.querySelectorAll('.more-anthems .an-grid').forEach(function (g) {
      var cards = g.querySelectorAll('.an-card');
      cards.forEach(function (a) { a.hidden = false; });
      var cols = getComputedStyle(g).gridTemplateColumns.split(' ').filter(Boolean).length || 1;
      var rows = Math.max(1, Math.round(8 / cols));
      var show = Math.min(cards.length, rows * cols);
      if (show < rows * cols && show > cols) show -= show % cols;
      cards.forEach(function (a, i) { a.hidden = i >= show; });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fitMore); else fitMore();
  window.addEventListener('resize', fitMore);

  // off the live site (a preview), show where each ad unit sits instead of asking Google for one
  if (!/(^|\.)adjiebrotots\.com$/.test(location.hostname)) {
    document.documentElement.classList.add('ad-preview');
    Array.prototype.forEach.call(document.querySelectorAll('ins.adsbygoogle'), function (ins) {
      ins.setAttribute('data-preview', ins.getAttribute('data-ad-format') || 'auto');
    });
    return;
  }

  // ad units: fill every visible one
  function fill() {
    Array.prototype.forEach.call(document.querySelectorAll('ins.adsbygoogle'), function (ins) {
      if (ins.getAttribute('data-adsbygoogle-status') || ins.offsetParent === null) return;
      try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch (e) {}
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fill); else fill();
})();

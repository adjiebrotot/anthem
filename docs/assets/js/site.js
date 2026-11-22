/* Anthem Madness pages: theme toggle, instrument menu, part tabs, ad units. */
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

  // part tabs (Violins I, Violins II ...): show one part's pages and mark its download row
  var tabs = document.querySelectorAll('.part-tab');
  function show(key, push) {
    Array.prototype.forEach.call(tabs, function (b) {
      var on = b.getAttribute('data-part') === key;
      b.classList.toggle('active', on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    Array.prototype.forEach.call(document.querySelectorAll('.score-part'), function (p) {
      p.hidden = p.getAttribute('data-part') !== key;
    });
    Array.prototype.forEach.call(document.querySelectorAll('.dl-row[data-part]'), function (r) {
      r.classList.toggle('active', r.getAttribute('data-part') === key);
    });
    if (push && history.replaceState) history.replaceState(null, '', '#' + key);
  }
  Array.prototype.forEach.call(tabs, function (b) {
    b.addEventListener('click', function () { show(b.getAttribute('data-part'), true); });
  });
  if (tabs.length && location.hash) {
    var k = location.hash.slice(1);
    if (document.querySelector('.score-part[data-part="' + k + '"]')) show(k, false);
  }

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

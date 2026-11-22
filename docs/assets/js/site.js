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

  /* PDF: made on the reader's side from the page images, through the browser's own print pipeline (the way
     tool.adjiebrotots.com/mdtopdf does it): a print-only stage of A4 pages, each the page image with the big
     anthem.adjiebrotots.com watermark (drawn exactly over the image's light one) and a footer line, then
     window.print(); the document title becomes the file name "Save as PDF" suggests. Nothing is stored as PDF. */
  var stage = null, tip = null, overlay = null, pending = null, oldTitle = '';
  function el(tag, cls, html) { var x = document.createElement(tag); if (cls) x.className = cls; if (html) x.innerHTML = html; return x; }
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
      try { if (document.getElementById('printTipSkip').checked) localStorage.setItem('am-skip-pdf-tip', '1'); } catch (e) {}
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
  function requestPdf(btn) {
    ensureUi();
    pending = btn;
    var skip = false;
    try { skip = localStorage.getItem('am-skip-pdf-tip') === '1'; } catch (e) {}
    if (skip) { runPrint(btn); return; }
    document.getElementById('printTipSkip').checked = false;
    tip.classList.add('visible'); tip.setAttribute('aria-hidden', 'false');
    document.getElementById('printTipGo').focus();
  }
  function runPrint(btn) {
    var pages = (btn.getAttribute('data-pages') || '').split(' ').filter(Boolean);
    var footer = btn.getAttribute('data-footer') || 'anthem.adjiebrotots.com';
    var name = (btn.getAttribute('data-pdf') || 'sheet-music.pdf').replace(/\.pdf$/, '');
    if (!pages.length) return;
    cleanup();
    overlay.classList.add('visible');
    document.getElementById('pdfOverlayMsg').textContent = 'Preparing ' + pages.length + ' page' + (pages.length > 1 ? 's' : '') + '…';
    var loads = pages.map(function (src, i) {
      var pg = el('div', 'pdf-page');
      var img = new Image();
      img.alt = '';
      img.src = src;
      pg.appendChild(img);
      pg.appendChild(el('div', 'pdf-wm', 'anthem.adjiebrotots.com'));
      pg.appendChild(el('div', 'pdf-ft')).textContent = footer + ' · page ' + (i + 1) + ' of ' + pages.length;
      stage.appendChild(pg);
      return (img.decode ? img.decode() : new Promise(function (r) { img.onload = r; img.onerror = r; })).catch(function () {});
    });
    Promise.all(loads.concat(document.fonts && document.fonts.ready ? [document.fonts.ready] : [])).then(function () {
      overlay.classList.remove('visible');
      oldTitle = document.title;
      document.title = name;
      try { if (window.gtag) window.gtag('event', 'file_download', { file_name: name + '.pdf', file_extension: 'pdf', link_text: 'PDF' }); } catch (e) {}
      requestAnimationFrame(function () { requestAnimationFrame(function () { window.print(); }); });
    });
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('button[data-pdf]');
    if (b) { e.preventDefault(); requestPdf(b); }
  });

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

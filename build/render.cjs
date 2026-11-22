// Renders Verovio SVG pages to PNG page images (light watermark) and to one watermarked A4 PDF per score.
// node render.cjs jobs.json
// jobs.json: [{ "svgs": ["p1.svg", ...], "png": ["out1.png", ...], "pdf": "out.pdf", "footer": "text" }]
const { chromium } = require('playwright');
const fs = require('fs');

const MARK = 'anthem.adjiebrotots.com';
const W = 1240, H = 1754; // A4 at 150 dpi

function sized(svg) {
  return svg.replace('<svg', '<svg style="position:absolute;inset:0;width:100%;height:100%;display:block"');
}

function pageHtml(svg, opacity, footer) {
  return `<div class="pg">${sized(svg)}
  <div class="wm" style="opacity:${opacity}">${MARK}</div>
  ${footer ? `<div class="ft">${footer}</div>` : ''}</div>`;
}

const CSS = `
@page { size: A4; margin: 0; }
html, body { margin: 0; padding: 0; background: #fff; }
.pg { position: relative; width: 210mm; height: 297mm; overflow: hidden; page-break-after: always; break-after: page; background: #fff; }
.pg:last-child { page-break-after: auto; break-after: auto; }
.wm { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%) rotate(-38deg); white-space: nowrap;
      font: 700 15mm/1 'DM Sans', Arial, sans-serif; color: #000; letter-spacing: .5mm; pointer-events: none; }
.ft { position: absolute; left: 0; right: 0; bottom: 6mm; text-align: center; font: 500 3.2mm/1.2 'DM Sans', Arial, sans-serif; color: #555; }
`;

(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  const shot = await browser.newPage({ viewport: { width: W, height: H } });
  const print = await browser.newPage();
  for (const job of jobs) {
    const svgs = job.svgs.map(f => fs.readFileSync(f, 'utf8'));
    // page images: a light watermark, no footer (the page around them says where they come from)
    for (let i = 0; i < svgs.length; i++) {
      if (!job.png || !job.png[i]) continue;
      await shot.setContent(`<html><head><style>${CSS}.pg{width:${W}px;height:${H}px}.wm{font-size:88px}</style></head>
        <body>${pageHtml(svgs[i], 0.07, '')}</body></html>`);
      await shot.screenshot({ path: job.png[i], clip: { x: 0, y: 0, width: W, height: H } });
    }
    if (job.pdf) {
      const n = svgs.length;
      const body = svgs.map((s, i) => pageHtml(s, 0.13, `${job.footer} · page ${i + 1} of ${n}`)).join('\n');
      await print.setContent(`<html><head><style>${CSS}</style></head><body>${body}</body></html>`);
      await print.pdf({ path: job.pdf, format: 'A4', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
    }
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });

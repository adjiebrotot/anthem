// Share images: the top of each anthem's full score (first A4 page) as a 1240 x 651 PNG (build.py makes it 1200 x 630).
// node render.cjs jobs.json        jobs.json: [{ "svg": "share.svg", "png": "share.png" }]
// The score itself is drawn in the reader's browser (docs/assets/js/score.js); this is only for og:image and the sitemap.
const { chromium } = require('playwright');
const fs = require('fs');

const W = 1240, H = 1754; // A4 at 150 dpi

(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  for (const job of jobs) {
    const svg = fs.readFileSync(job.svg, 'utf8')
      .replace('<svg', '<svg style="position:absolute;inset:0;width:100%;height:100%;display:block"');
    await page.setContent(`<html><head><style>html,body{margin:0;background:#fff}
      .pg{position:relative;width:${W}px;height:${H}px;background:#fff}</style></head><body><div class="pg">${svg}</div></body></html>`);
    await page.screenshot({ path: job.png, clip: { x: 0, y: 0, width: W, height: Math.round(W * 630 / 1200) } });
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });

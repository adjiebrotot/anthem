// node shot.mjs out.png a.svg [b.svg ...] : each SVG page rendered on white at A4 1240x1754
(async () => {
const { chromium } = require('playwright');
const fs = require('fs');
const [out, ...svgs] = process.argv.slice(2);
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1240, height: 1754 } });
let i = 0;
for (const f of svgs) {
  const svg = fs.readFileSync(f, 'utf8');
  await p.setContent(`<html><body style="margin:0;background:#fff">${svg.replace('<svg', '<svg style="width:1240px;height:1754px;display:block"')}</body></html>`);
  await p.screenshot({ path: out.replace('.png', `-${++i}.png`) });
}
await b.close();
})();

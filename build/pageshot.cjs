// node pageshot.cjs url out.png [width] [dark]
const { chromium } = require('playwright');
(async () => {
  const [url, out, w, dark] = process.argv.slice(2);
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: +(w || 1366), height: 900 }, deviceScaleFactor: 1, colorScheme: dark ? 'dark' : 'light' });
  const p = await ctx.newPage();
  p.on('pageerror', e => console.log('PAGEERROR', e.message));
  p.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
  await p.goto(url, { waitUntil: 'networkidle' });
  await p.screenshot({ path: out, fullPage: true });
  await b.close();
})();

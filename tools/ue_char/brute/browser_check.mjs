// Headless load check of the browser brute (uses public/assets/enemies/brute_basecolor.webp on thug.glb). Port 5203 only.
// Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.
//   node tools/ue_char/brute/browser_check.mjs [OUT_DIR]
import { chromium } from 'playwright-core';
import { createServer } from 'vite';
const ROOT = new URL('../../..', import.meta.url).pathname.replace(/\/$/, '');
const SCR = process.env.P2_SCRATCH || ROOT + '/unreal/WebHomage/Saved/P2Build';
const OUT = process.argv[2] || SCR + '/r2/browser';
const server = await createServer({ root: ROOT, server: { port: 5203, strictPort: true, host: '127.0.0.1' }, logLevel: 'error' });
await server.listen();
const ctxB = await chromium.launchPersistentContext(OUT + '/profile', { channel: 'chrome', headless: true, viewport: { width: 1280, height: 720 },
  args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
let code = 0;
try {
  const page = await ctxB.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto('http://127.0.0.1:5203/');
  await page.waitForFunction(() => window.__cmb?.debug && window.__ctx?.player?.object, null, { timeout: 240000 });
  await new Promise(r => setTimeout(r, 3000));
  const types = await page.evaluate(async () => await window.__cmb.debug.fight('b', 5));
  await new Promise(r => setTimeout(r, 3500));
  const info = await page.evaluate(() => {
    const e = window.__cmb.enemies.find(x => x.type === 'brute');
    if (!e) return { brute: false };
    const maps = []; e.root.traverse(o => { if (o.isMesh && o.material?.map) maps.push({ w: o.material.map.image?.width, h: o.material.map.image?.height, src: String(o.material.map.image?.currentSrc || o.material.map.source?.data?.src || '') }); });
    return { brute: true, scale: e.root.scale.toArray().map(v => +v.toFixed(3)), maps };
  });
  await page.screenshot({ path: OUT + '/brute_game.png' });
  console.log('types', types, JSON.stringify(info), errs.length ? 'ERRORS: ' + errs.slice(0, 5).join(' | ') : 'no console errors');
  if (!info.brute || errs.length) code = 1;
} finally { await ctxB.close(); await server.close(); }
process.exit(code);

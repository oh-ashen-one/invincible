import { chromium } from 'playwright-core';
const ctxB = await chromium.launchPersistentContext('/Users/midir/sm2-n1/_scratch/baseline/chrome-profile', { channel: 'chrome', headless: true,
  viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1,
  args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--disable-frame-rate-limit', '--disable-gpu-vsync'] });
const page = ctxB.pages()[0] || await ctxB.newPage();
const logs = [];
page.on('console', m => logs.push(m.type() + ': ' + m.text().slice(0, 300)));
page.on('pageerror', e => logs.push('PAGEERROR: ' + e.message));
const t0 = Date.now();
await page.goto('http://127.0.0.1:5201/?playtest=1');
await page.waitForFunction(() => window.__cmb && window.__sys && window.__ctx?.player, null, { timeout: 300000 });
console.log('ready', (Date.now() - t0) / 1000);
await page.waitForTimeout(3000);
const st = await page.evaluate(() => { const C = __ctx; return { pr: C.renderer.getPixelRatio(), db: C.renderer.getDrawingBufferSize(new C.THREE.Vector2()).toArray(), pos: C.player.position.toArray(), mode: C.player.mode, pt: __ptState(), sys: __sys.debug.state(), gl: C.renderer.getContext().getParameter(C.renderer.getContext().VERSION), rend: (()=>{const gl=C.renderer.getContext();const e=gl.getExtension('WEBGL_debug_renderer_info');return e?gl.getParameter(e.UNMASKED_RENDERER_WEBGL):'?'})(), bootHidden: document.querySelector('#boot, #loading')?.outerHTML?.slice(0,200) }; });
console.log(JSON.stringify(st, null, 1));
await page.screenshot({ path: '/Users/midir/sm2-n1/_scratch/baseline/probe.jpg', quality: 85 });
console.log(logs.join('\n'));
await ctxB.close();

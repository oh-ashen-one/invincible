// Headless load check: wear each AI suit in the running game (default camera), collect console errors, screenshot. Port 5203 only.
import { chromium } from 'playwright-core';
import { createServer } from 'vite';
const ROOT = new URL('../../..', import.meta.url).pathname.replace(/\/$/, '');
const SCR = process.env.P2_SCRATCH || ROOT + '/unreal/WebHomage/Saved/P2Build';
const OUT = process.env.OUT || SCR + '/suits/browser';
const server = await createServer({ root: ROOT, server: { port: 5203, strictPort: true, host: '127.0.0.1' }, logLevel: 'error' });
await server.listen();
const base = 'http://127.0.0.1:5203/';
const ctxB = await chromium.launchPersistentContext(OUT + '/profile', { channel: 'chrome', headless: true, viewport: { width: 1280, height: 720 },
  args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
try {
  for (const s of (process.argv[2] || 'claude,codex,gemini,kimi,qwen').split(',')) {
    const page = await ctxB.newPage();
    const errs = [], warns = [];
    page.on('pageerror', e => errs.push(e.message));
    page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); if (m.type() === 'warning' && /skin|GLTF|texture/i.test(m.text())) warns.push(m.text()); });
    await page.goto(base);   // normal game (the ?shot= harness does not start the game systems that own suits)
    await page.waitForFunction(() => window.__ctx?.sys?.suits && window.__ctx?.player?.object, null, { timeout: 240000 });
    await new Promise(r => setTimeout(r, 3000));
    const r = await page.evaluate(async (id) => {
      const su = window.__ctx.sys.suits; su.apply(id);
      const url = `/assets/skins/${id}.glb`;
      for (let i = 0; i < 200 && su.skins.worn !== url; i++) await new Promise(r => setTimeout(r, 100));
      await new Promise(r => setTimeout(r, 1500));
      let mesh = null; window.__ctx.player.object.traverse(o => { if (o.userData.isSuitSkin) mesh = o; });
      const m = mesh?.material;
      return { worn: su.skins.worn, visible: !!mesh?.visible, tangent: !!mesh?.geometry.attributes.tangent,
        maps: m ? { map: !!m.map, normalMap: !!m.normalMap, roughnessMap: !!m.roughnessMap, metalnessMap: !!m.metalnessMap, aoMap: !!m.aoMap } : null };
    }, s);
    await page.screenshot({ path: `${OUT}/${s}.png` });
    console.log(s, JSON.stringify(r), errs.length ? 'ERRORS: ' + errs.slice(0, 4).join(' | ') : 'no errors', warns.length ? 'WARN: ' + warns.slice(0, 2).join(' | ') : '');
    await page.close();
  }
} finally { await ctxB.close(); await server.close(); }

// (pinata-and-trees) A/B frame-time + GPU-pass probe for the ez-tree trees, park grass and destruction debris.
//   node tools/perf_pat.mjs                      -> headless (indicative only)
//   HEADED=1 W=2560 H=1440 node tools/perf_pat.mjs  -> a real window (use this on the target machine for fps claims)
//   Q=low node tools/perf_pat.mjs                -> the low preset
// Configs: old (eztree / grass / debris off via ?qset) vs new, same build, same camera spots. Per spot: 240 rendered
// frames after a settle: rAF frame time avg / p95 / p99 / max, GPU ms per pass (?prof=1: pipeline.timings()), draw
// calls / triangles (all passes). The 'smash' spot breaks every prop within 8 m three times first (~300 fragments).
// Starts its own Vite server on a free port (5196+), never 5173 / 5191-5193.
import { chromium } from 'playwright-core';
import { createServer } from 'vite';

const Q = process.env.Q || 'high', W = +(process.env.W || 1600), H = +(process.env.H || 900), N = +(process.env.N || 240);
const CONFIGS = (process.env.CONFIGS || 'old,new').split(',');
const QSET = { old: 'eztree:false,grass:0,debris:0', new: '' };
// spot: [name, x, z, height above ground (m), yaw]
const ONLY = process.env.SPOTS ? process.env.SPOTS.split(',') : null;
const SPOTS = [
  ['park-lawn', -70, -730, 1.2, 0.6], ['park-woods', -20, -660, 1.2, 2.4], ['park-swing', 60, -700, 24, 0.3],
  ['street', 250, 150, 1.2, Math.PI], ['street-swing', 247, 180, 16, Math.PI], ['smash', 238.5, 422, 1.2, Math.PI],
];

const server = await createServer({ server: { port: +(process.env.PORT || 5196), strictPort: false, host: '127.0.0.1' }, logLevel: 'error' });
await server.listen();
const base = server.resolvedUrls.local[0];
const browser = await chromium.launch({ channel: 'chrome', headless: !process.env.HEADED,
  args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--disable-frame-rate-limit', '--disable-gpu-vsync'] });
const rows = [];
try {
  for (const cfg of CONFIGS) {
    const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
    const errs = []; page.on('pageerror', e => errs.push(e.message)); page.on('console', m => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
    await page.goto(new URL(`?dev&prof=1&q=${Q}${QSET[cfg] ? '&qset=' + QSET[cfg] : ''}`, base).href);
    await page.waitForFunction(() => window.__destruct && window.__ctx?.combat, null, { timeout: 300000 });
    if (cfg !== 'old') await page.waitForFunction(() => window.__destruct.breakables.ready(), null, { timeout: 120000 });
    for (const [name, x, z, hh, yaw] of SPOTS.filter(s => !ONLY || ONLY.includes(s[0]))) {
      if (name === 'smash' && cfg === 'old') continue;
      await page.evaluate(([x, z, hh, yaw]) => {
        const C = window.__ctx; C.player.teleport(new C.THREE.Vector3(x, C.world.groundHeight(x, z) + hh, z), yaw);
      }, [x, z, hh, yaw]);
      await page.waitForTimeout(250);
      await page.evaluate(() => { window.__ctx.player.frozen = true; }); // a still camera: same view for both configs
      await page.waitForTimeout(3500);
      if (name === 'smash') for (let k = 0; k < 3; k++) { await page.evaluate(() => { const C = window.__ctx, p = C.player.position.clone(); window.__destruct.breakAt(p, 8, { power: 6, up: 4 }); window.__destruct.hitCar(p, 6, {}); }); await page.waitForTimeout(250); }
      await page.evaluate(() => window.__ctx.pipeline.timings(true));
      const r = await page.evaluate((n) => new Promise(res => {
        const t = []; let last = performance.now();
        const f = (now) => { t.push(now - last); last = now; if (t.length < n) requestAnimationFrame(f); else res(t); };
        requestAnimationFrame(f);
      }), N);
      const g = await page.evaluate(() => ({ t: window.__ctx.pipeline.timings(), s: window.__ctx.pipeline.stats, frags: window.__destruct.debris.count }));
      r.sort((a, b) => a - b);
      const avg = r.reduce((a, b) => a + b, 0) / r.length, pct = (p) => r[Math.min(r.length - 1, Math.floor(r.length * p))];
      rows.push({ cfg, spot: name, avg: avg.toFixed(2), p95: pct(0.95).toFixed(1), p99: pct(0.99).toFixed(1), max: r[r.length - 1].toFixed(1),
        gpu: g.t.total, scene: g.t.scene ?? g.t['scene+shadows'], shadows: g.t.shadows, calls: g.s.calls, mtris: (g.s.triangles / 1e6).toFixed(1), frags: g.frags });
      console.log(JSON.stringify(rows[rows.length - 1]));
      if (process.env.PASSES) console.log('  passes', JSON.stringify(g.t));
      await page.evaluate(() => { window.__ctx.player.frozen = false; });
    }
    if (errs.length) console.log(cfg, 'errors:', errs.slice(0, 4).join(' | '));
    await page.close();
  }
} finally {
  console.table(rows);
  await browser.close(); await server.close();
}

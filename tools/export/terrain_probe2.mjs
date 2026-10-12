// probe: tree / prop pool item distribution (how many inside Central Park, where the rest are)
import { chromium } from 'playwright-core';
const ctx = await chromium.launchPersistentContext('/Users/midir/sm2-n1/_scratch/terrain/chrome-profile', { channel: 'chrome', headless: true, viewport: { width: 640, height: 360 },
  args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--js-flags=--max-old-space-size=12000'] });
try {
  const page = await ctx.newPage();
  await page.goto('http://127.0.0.1:5209/?shot=parkHigh');
  await page.waitForFunction(() => window.__shotReady === true, null, { timeout: 600000 });
  const rows = await page.evaluate(async () => {
    const { Pool } = await import('/src/world/pool.js');
    const { G } = await import('/src/world/layout.js');
    window.__pools = new Set();
    for (const k of ['thresh', 'update', 'due', 'upload']) { const f = Pool.prototype[k]; if (!f) continue; Pool.prototype[k] = function (...a) { window.__pools.add(this); return f.apply(this, a); }; }
    const c = window.__ctx;
    for (let i = 0; i < 4; i++) { c.world.update(1 / 60, c.camera); await new Promise(r => setTimeout(r, 50)); }
    await new Promise(r => setTimeout(r, 1500));
    const P = G.PARK, out = [];
    for (const p of window.__pools) {
      const n = p.mesh?.name || ''; if (!/tree|trunk|^ez-|bench|lamp|park|garden|planter|pit/i.test(n)) continue;
      let inPark = 0, mnx = 1e9, mxx = -1e9, mnz = 1e9, mxz = -1e9, hid = 0, hasE = 0, hasC = 0;
      for (const it of p.items) { if (it.hidden) hid++; if (it.x > P.x0 && it.x < P.x1 && it.z > P.z0 && it.z < P.z1) inPark++; mnx = Math.min(mnx, it.x); mxx = Math.max(mxx, it.x); mnz = Math.min(mnz, it.z); mxz = Math.max(mxz, it.z); if (it.extra) hasE++; if (it.color) hasC++; }
      out.push([n, p.items.length, inPark, hid, hasE, hasC, mnx | 0, mxx | 0, mnz | 0, mxz | 0, Object.keys(p.items[0] || {}).join(','), p.items[0]?.extra ? Object.keys(p.items[0].extra).join(',') : '']);
    }
    return out;
  });
  rows.sort((a, b) => a[0] < b[0] ? -1 : 1);
  for (const r of rows) console.log(r.join(' | '));
} finally { await ctx.close(); }

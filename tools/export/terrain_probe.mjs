import { chromium } from 'playwright-core';
import fs from 'node:fs';
const URL0 = 'http://127.0.0.1:5209/';
const ctx = await chromium.launchPersistentContext('/Users/midir/sm2-n1/_scratch/terrain/chrome-profile', { channel: 'chrome', headless: true, viewport: { width: 640, height: 360 },
  args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--js-flags=--max-old-space-size=12000'] });
try {
  const page = await ctx.newPage();
  page.on('pageerror', e => console.log('pageerror:', e.message));
  const t0 = Date.now();
  await page.goto(URL0 + '?shot=parkHigh');
  await page.waitForFunction(() => window.__shotReady === true, null, { timeout: 600000 });
  console.log('ready', (Date.now() - t0) / 1000);
  const rows = await page.evaluate(async () => {
    const { Pool } = await import('/src/world/pool.js');
    window.__pools = new Set();
    for (const k of ['thresh', 'update', 'due', 'upload']) { const f = Pool.prototype[k]; if (!f) continue; Pool.prototype[k] = function (...a) { window.__pools.add(this); return f.apply(this, a); }; }
    const c = window.__ctx;
    for (let i = 0; i < 4; i++) { c.world.update(1 / 60, c.camera); await new Promise(r => setTimeout(r, 50)); }
    await new Promise(r => setTimeout(r, 1500));
    const out = [];
    c.scene.traverse(o => {
      if (!(o.isMesh || o.isPoints || o.isLine)) return;
      const g = o.geometry; if (!g?.attributes?.position) return;
      if (!g.boundingBox) g.computeBoundingBox();
      const bb = g.boundingBox; const m = o.material;
      out.push({ n: o.name, t: o.isInstancedMesh ? 'inst' : o.isSkinnedMesh ? 'skin' : o.isPoints ? 'pts' : o.isLine ? 'line' : 'mesh', c: o.isInstancedMesh ? o.count : 1,
        v: g.attributes.position.count, tri: g.index ? g.index.count / 3 : g.attributes.position.count / 3,
        bb: [bb.min.x, bb.min.y, bb.min.z, bb.max.x, bb.max.y, bb.max.z].map(v => +v.toFixed(0)), mat: Array.isArray(m) ? 'multi' : m?.type, attrs: Object.keys(g.attributes).join(','),
        vis: o.visible, par: o.parent?.name || '' });
    });
    const pools = [...window.__pools].map(P => ({ name: P.mesh?.name, n: P.items?.length, near: P.near, far: P.far, v: P.geo?.attributes?.position?.count }));
    return { rows: out, pools };
  });
  fs.writeFileSync('/Users/midir/sm2-n1/_scratch/terrain/probe/scene_rows.json', JSON.stringify(rows, null, 1));
  console.log(rows.rows.length, 'rows,', rows.pools.length, 'pools');
} finally { await ctx.close(); }

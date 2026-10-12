// Night 1 / F3: drive the hero head-on at the side of the 6 nearest parked cars (both sides) in manual-step mode and print whether he stops dead or slides.
// node docs/night1/baseline/tools/carprobe.mjs   (needs the dev server on :5201)
import { chromium } from 'playwright-core';
const prof = '/Users/midir/sm2-n1/_scratch/baseline/chrome-profile-car-' + process.pid;
const b = await chromium.launchPersistentContext(prof, { channel: 'chrome', headless: true, viewport: { width: 960, height: 540 }, args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
const p = b.pages()[0];
await p.goto('http://127.0.0.1:5201/?playtest=1');
await p.waitForFunction(() => window.__cmb && window.__sys && window.__ctx?.player && window.__ctx.stepFrame, null, { timeout: 300000 });
await p.waitForTimeout(5000);
await p.evaluate(() => { __ctx.manualStep = true; });
const info = await p.evaluate(() => { const C = __ctx, o = C.player.position.clone(); const cars = (C.world.carsNear(o, 80) || []).filter(c => c.parked).slice(0, 6); return cars.map(c => ({ keys: Object.keys(c).join(','), x: c.x, z: c.z, y: c.y, ry: c.ry, wid: c.wid, len: c.len })); });
console.log(JSON.stringify(info.slice(0, 3)));
for (let i = 0; i < Math.min(6, info.length); i++) {
  const c = info[i];
  for (const sd of [1, -1]) {
    const res = await p.evaluate(([c, sd]) => {
      const C = __ctx, V = (x, y, z) => new C.THREE.Vector3(x, y, z);
      const fx = Math.cos(c.ry), fz = -Math.sin(c.ry), sx = -fz, sz = fx;
      const q = V(c.x + sx * sd * (c.wid / 2 + 5), 0, c.z + sz * sd * (c.wid / 2 + 5));
      const gh = C.world.groundHeight(q.x, q.z, (c.y ?? 0) + 1.5); q.y = gh + 1.0;
      C.player.teleport(q, Math.atan2(-sx * sd, -sz * sd));
      return { q: q.toArray().map(x => +x.toFixed(1)), gh };
    }, [c, sd]);
    await p.keyboard.down('KeyW');
    const trace = [];
    for (let f = 0; f < 150; f++) { await p.evaluate(() => __ctx.stepFrame(1 / 60)); if (f % 30 === 29) trace.push(await p.evaluate(() => { const P = __ctx.player; return [+P.position.x.toFixed(1), +P.position.y.toFixed(1), +P.position.z.toFixed(1), +P.velocity.length().toFixed(1), P.mode]; })); }
    await p.keyboard.up('KeyW');
    console.log(`car ${i} sd ${sd} car@(${c.x.toFixed(1)},${c.z.toFixed(1)}) ry ${c.ry.toFixed(2)} start`, JSON.stringify(res), 'trace', JSON.stringify(trace));
  }
}
await b.close(); import('node:fs').then(fs => fs.rmSync(prof, { recursive: true, force: true }));

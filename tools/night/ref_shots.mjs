// Reference captures of the author's night city (~/spiderbench @ 64d957f) at 1920x1080 -> ~/sm2-n1/_scratch/night/ref/
//   node tools/night/ref_shots.mjs            all shots (two browser batches, one page at a time)
// Batch 1: the shots.js compositions (street, wall, swing, swingBack, climb) at full night.
// Batch 2: free cameras (high skyline, Times Square street, waterfront, commercial street with storefront neon).
// Each shot writes <name>.png; ref_shots.json holds camera position / target / fov in browser coords and UE cm = (x, z, y) * 100.
import fs from 'node:fs';
import path from 'node:path';
import { SCRATCH, startServer, launchBrowser, openNight, stepFrames } from './common.mjs';

const OUT = process.env.OUT || path.join(SCRATCH, 'ref');
fs.mkdirSync(OUT, { recursive: true });
const t0 = Date.now();
const log = (...a) => console.log(`[ref_shots ${((Date.now() - t0) / 1000).toFixed(0)}s]`, ...a);
const ue = (v) => [v[0] * 100, v[2] * 100, v[1] * 100].map(x => Math.round(x * 10) / 10);
const infos = [];

const readCam = (page, name) => page.evaluate((name) => {
  const { camera, world } = window.__ctx, f = camera.getWorldDirection(new camera.position.constructor());
  const vp = world.viewpoints?.[name]?.target;
  const r = (v) => [v.x, v.y, v.z].map(x => Math.round(x * 100) / 100);
  return { pos: r(camera.position), forward: r(f), fov: camera.fov, aspect: camera.aspect, viewpoint_target: vp ? r(vp) : null,
    target_fwd20: r({ x: camera.position.x + f.x * 20, y: camera.position.y + f.y * 20, z: camera.position.z + f.z * 20 }) };
}, name);

async function save(page, name, extra = {}) {
  const file = path.join(OUT, name + '.png');
  await page.screenshot({ path: file });
  const cam = await readCam(page, extra.shot ?? name);
  const target = cam.viewpoint_target ?? cam.target_fwd20;
  infos.push({ name, file, size: [1920, 1080], tod: 'night', ...extra, camera: { ...cam, target }, ue_cm: { pos: ue(cam.pos), target: ue(target), fov: cam.fov, note: 'UE cm = (x, z, y) * 100' } });
  log('saved', file);
}

const { server, base } = await startServer({ inject: true });
try {
  // ---------------- batch 1: shots.js
  const b1 = await launchBrowser();
  try {
    for (const shot of ['street', 'wall', 'swing', 'swingBack', 'climb']) {
      const { page, errs } = await openNight(b1, base, { shot });
      await save(page, 'shot_' + shot, { shot, kind: 'shots.js composition', query: `?shot=${shot}&tod=night`, page_errors: errs.length });
      await page.close();
    }
  } finally { await b1.close(); }

  // ---------------- batch 2: free cameras on top of the 'street' harness page
  const b2 = await launchBrowser();
  try {
    const { page, errs } = await openNight(b2, base, { shot: 'street' });
    await page.waitForFunction(() => window.__sm2Neon && (window.__screenLightStats || []).every(s => !s.pending), null, { timeout: 120000 });
    const place = async (name, spec) => {
      await page.evaluate(({ pos, target, fov }) => {
        const { camera, pipeline, player } = window.__ctx;
        try { player.object.visible = false; } catch (e) {}
        camera.position.set(...pos); camera.up.set(0, 1, 0); camera.lookAt(...target); camera.fov = fov; camera.updateProjectionMatrix(); camera.updateMatrixWorld(true); pipeline.resetHistory?.();
      }, spec);
      await stepFrames(page, 90);
      await save(page, name, { kind: 'free camera', requested: spec, page_errors: errs.length });
    };
    const ground = (x, z) => page.evaluate(([x, z]) => window.__ctx.world.groundHeight(x, z), [x, z]);
    await place('view_skyline_high', { pos: [-320, 340, 540], target: [250, 140, -60], fov: 55 });
    let gy = await ground(-22, -80);
    await place('view_times_square_street', { pos: [-22, gy + 1.7, -80], target: [0, 16, -200], fov: 60 });
    // waterfront: the west shore at the latitude of midtown, a little inland, looking out over the river
    const shore = await page.evaluate(async () => { const L = await import('/src/world/layout.js'); const z = -200; let i = 0; while (i < L.SHORE_Z.length - 2 && L.SHORE_Z[i + 1] < z) i++; const t = (z - L.SHORE_Z[i]) / (L.SHORE_Z[i + 1] - L.SHORE_Z[i]); return { z, x: L.SHORE_W[i] + (L.SHORE_W[i + 1] - L.SHORE_W[i]) * t }; });
    log('west shore at z=-200: x', shore.x.toFixed(1));
    await place('view_waterfront', { pos: [shore.x + 30, 9, shore.z], target: [shore.x - 250, 12, shore.z - 60], fov: 62 });
    // commercial street with storefront neon: the densest 40 m cell of neon words outside the Times Square box
    const cluster = await page.evaluate(() => {
      const W = window.__sm2Neon.words, cells = new Map();
      for (let i = 0; i < W.length; i += 12) {
        const x = W[i], z = W[i + 2]; if (x > -112 && x < 112 && z > -352 && z < 22) continue;
        const k = Math.floor(x / 40) + ',' + Math.floor(z / 40), c = cells.get(k) || { n: 0, i0: i, sx: 0, sz: 0 }; c.n++; c.sx += x; c.sz += z; cells.set(k, c);
      }
      let best = null; for (const c of cells.values()) if (!best || c.n > best.n) best = c;
      const i = best.i0, tx = W[i + 3], tz = W[i + 4];
      return { n: best.n, cx: best.sx / best.n, cz: best.sz / best.n, y: W[i + 1], nx: -tz, nz: tx };
    });
    log('neon cluster', JSON.stringify(cluster));
    gy = await ground(cluster.cx + cluster.nx * 16, cluster.cz + cluster.nz * 16);
    await place('view_commercial_neon', { pos: [cluster.cx + cluster.nx * 16, gy + 2.0, cluster.cz + cluster.nz * 16], target: [cluster.cx, Math.max(cluster.y, 3), cluster.cz], fov: 62, neon_cluster: cluster });
    await page.close();
  } finally { await b2.close(); }
  fs.writeFileSync(path.join(OUT, 'ref_shots.json'), JSON.stringify({ source: { repo: '~/spiderbench', commit: '64d957f92f005a1c1870070079351e30b2395661' }, frame: 'browser metres, +x east, +y up, -z north; UE cm = (x, z, y) * 100', shots: infos }, null, 1));
  log('wrote ref_shots.json,', infos.length, 'shots');
} finally {
  await server.close();
}

// Night 1 / F3: close-up stills of every suit (front / 3/4 / back / head+chest) on the street spawn, standing idle, 1920x1080.
// Same harness idea as ?shot=suit (player.setPose + placed camera) but inside the ?playtest=1 game so the real suit-swap code path
// (__sys.debug.suit) runs, and the console is captured per suit (texture-unit warnings, GLB errors).
//   node docs/night1/baseline/tools/skinclose.mjs            -> docs/night1/baseline/stills/skins/<suit>_<view>.jpg + logs/skinclose.json
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
const BASE = process.env.URL || 'http://127.0.0.1:5201/';
const OUT = process.env.OUT || 'docs/night1/baseline/stills/skins';
const SCRATCH = process.env.SCRATCH || '/Users/midir/sm2-n1/_scratch/baseline';
fs.mkdirSync(OUT, { recursive: true });
const profile = path.join(SCRATCH, `chrome-profile-skin-${process.pid}`);
const b = await chromium.launchPersistentContext(profile, { channel: 'chrome', headless: true, viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1,
  args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
const page = b.pages()[0] || await b.newPage();
let cur = 'load'; const con = {};
page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') { const k = m.type() + ': ' + m.text().slice(0, 200); (con[cur] ||= {})[k] = ((con[cur] ||= {})[k] || 0) + 1; } });
page.on('pageerror', e => { const k = 'pageerror: ' + e.message.slice(0, 200); (con[cur] ||= {})[k] = ((con[cur] ||= {})[k] || 0) + 1; });
await page.goto(BASE + '?playtest=1');
await page.waitForFunction(() => window.__cmb && window.__sys && window.__ctx?.player && window.__ctx.stepFrame, null, { timeout: 300000 });
await page.waitForTimeout(6000);
const cdp = await page.context().newCDPSession(page);
const step = n => page.evaluate(n => { for (let i = 0; i < n; i++) __ctx.stepFrame(1 / 60); }, n);
await page.evaluate(async () => {
  const C = __ctx; C.manualStep = true; C.hud.setVisible?.(false);
  const { POSES } = await import('/src/player/rig.js');
  const p = C.player, W = C.world, V = C.THREE.Vector3;
  const sp = W.spawn; const feet = new V(sp.x, W.groundHeight(sp.x, sp.z), sp.z), fwd = new V(0, 0, -1);
  window.__place = () => { p.setPose({ pos: feet, forward: fwd, clip: 'idle', clipTime: 0.25, pose: POSES.idle(0), forceProcedural: !p.rig.hasClip('idle') }); };
  window.__place();
  const orig = C.pipeline.render.bind(C.pipeline);
  window.__cam = null;
  C.pipeline.render = dt => { const v = window.__cam; if (v) { C.camera.position.set(...v.pos); C.camera.lookAt(...v.tgt); C.camera.fov = v.fov; C.camera.updateProjectionMatrix(); C.camera.updateMatrixWorld(true); } orig(dt); };
  window.__views = {
    front: { d: 2.7, side: 0, h: 1.4, th: 1.15, fov: 42 }, threeq: { d: 2.4, side: 1.6, h: 1.35, th: 1.1, fov: 42 },
    back: { d: -2.7, side: 0, h: 1.4, th: 1.15, fov: 42 }, side: { d: 0, side: 2.7, h: 1.3, th: 1.1, fov: 42 }, head: { d: 1.15, side: 0.35, h: 1.6, th: 1.42, fov: 34 },
  };
  window.__setView = name => { const v = window.__views[name], right = new V().crossVectors(fwd, new V(0, 1, 0)).normalize();
    const pos = feet.clone().addScaledVector(fwd, v.d).addScaledVector(right, v.side).add(new V(0, v.h, 0)); pos.y = Math.max(pos.y, feet.y + v.h);
    window.__cam = { pos: pos.toArray(), tgt: feet.clone().add(new V(0, v.th, 0)).toArray(), fov: v.fov }; };
});
const suits = ['advanced', 'iron', 'symbiote', 'claude', 'codex', 'gemini', 'kimi', 'qwen'];
const meta = {};
for (const id of suits) {
  cur = id;
  await page.evaluate(id => __sys.debug.suit(id), id);
  // GLB skins load asynchronously (real time, not frames): wait until the wear() promise has put the mesh on (worn url matches) or 20 s
  const want = await page.evaluate(id => __sys.suits.SUITS.find(s => s.id === id)?.skin || null, id);
  const t0 = Date.now(); let ok = false;
  while (Date.now() - t0 < 20000) { await step(2); ok = await page.evaluate(w => (__sys.suits.skins.worn || null) === w, want); if (ok) break; await page.waitForTimeout(150); }
  meta[id] = { skinLoaded: ok, loadMs: Date.now() - t0 };
  await step(30); await page.evaluate(() => window.__place()); await step(30);
  Object.assign(meta[id], await page.evaluate(() => { const C = __ctx, gl = C.renderer.getContext(); let meshes = 0, tex = new Set(); C.player.object.traverse(o => { if (o.isMesh || o.isSkinnedMesh) { meshes++; const m = o.material; for (const mm of Array.isArray(m) ? m : [m]) for (const k of ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'emissiveMap', 'aoMap']) if (mm?.[k]) tex.add(k); } });
    return { meshes, texKinds: [...tex], state: __sys.debug.state().suit }; }));
  for (const view of Object.keys({ front: 1, threeq: 1, back: 1, side: 1, head: 1 })) {
    await page.evaluate(v => window.__setView(v), view); await step(4);
    const f = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 90 });
    fs.writeFileSync(path.join(OUT, `${id}_${view}.jpg`), Buffer.from(f.data, 'base64'));
  }
  console.log('[skin]', id, JSON.stringify(meta[id]), JSON.stringify(con[id] || {}));
}
fs.writeFileSync('docs/night1/baseline/logs/skinclose.json', JSON.stringify({ meta, console: con }, null, 1));
await b.close(); fs.rmSync(profile, { recursive: true, force: true });

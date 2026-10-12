// Night 1 / F3 browser baseline: scripted playtests driven by REAL input events (CDP Input.dispatchKeyEvent /
// dispatchMouseEvent via Playwright keyboard + mouse) in a headless Chrome (new headless, Metal ANGLE, GPU on).
//
//   MODE=film node docs/night1/baseline/tools/playtest.mjs swingChain fight ...   -> clips (frame-stepped, 60 fps game time)
//   MODE=perf W=3840 H=2160 node docs/night1/baseline/tools/playtest.mjs swingChain street   -> real-time frame times
//
// film: ctx.manualStep = true; every frame = input events for that frame -> ctx.stepFrame(1/60) -> CDP JPEG capture piped
//       to ffmpeg. The video therefore plays back at exactly 60 fps of game time regardless of how long each frame took
//       to render and capture (capture is offline, not real time).
// perf: the normal real-time loop (renderer.setAnimationLoop); the same scripts run on wall-clock time while an in-page
//       rAF logger records every frame delta. Chrome is launched with vsync / frame-rate limit off so frames are not
//       quantised to the display.
// Camera turning uses ctx.input.mouse.dx/dy (the pointer-lock path cannot be entered in headless Chrome); every
// other control is a real key / mouse event.
// Needs a Vite dev server of this worktree (URL, default http://127.0.0.1:5201/). Scratch output: SCRATCH dir.
import { chromium } from 'playwright-core';
import { spawn, execFile } from 'node:child_process';
import { once } from 'node:events';
import fs from 'node:fs';
import path from 'node:path';

const MODE = process.env.MODE || 'film';
const W = +(process.env.W || 1920), H = +(process.env.H || 1080), DPR = +(process.env.DPR || 1);
const BASE = process.env.URL || 'http://127.0.0.1:5201/';
const SCRATCH = process.env.SCRATCH || '/Users/midir/sm2-n1/_scratch/baseline';
const OUTDIR = process.env.OUT || 'docs/night1/baseline';
const Q = process.env.Q ? '&q=' + process.env.Q : '';
const names = process.argv.slice(2);
fs.mkdirSync(path.join(SCRATCH, 'raw'), { recursive: true });
fs.mkdirSync(path.join(OUTDIR, 'clips'), { recursive: true });
fs.mkdirSync(path.join(OUTDIR, 'logs'), { recursive: true });
fs.mkdirSync(path.join(OUTDIR, 'perf'), { recursive: true });

// GPU utilisation (ioreg IOAccelerator "Device Utilization %") -- the GPU is shared with other sessions (Unreal editors, other Chromes), so every
// perf run records it before / during / after and is flagged contaminated when the box was not quiet.
const gpuUtil = () => new Promise(r => execFile('/bin/sh', ['-c', "ioreg -r -d 1 -c IOAccelerator | grep -o '\"Device Utilization %\"=[0-9]*' | head -1 | cut -d= -f2"], (e, out) => r(e ? null : +String(out).trim())));
async function waitQuiet(maxS, thr = 25) { const end = Date.now() + maxS * 1000; let u = await gpuUtil(); while (u != null && u > thr && Date.now() < end) { await new Promise(r => setTimeout(r, 4000)); u = await gpuUtil(); } return u; }
// perf: external GPU load is read BEFORE Chrome is launched (so it excludes this game); QUIET_WAIT=<s> waits for a quiet GPU (<25 %) first
const gpuLaunch = MODE === 'perf' ? await waitQuiet(+(process.env.QUIET_WAIT || 0)) : null;
const profile = path.join(SCRATCH, `chrome-profile-${process.pid}`);
const browser = await chromium.launchPersistentContext(profile, {
  channel: 'chrome', headless: true, viewport: { width: W, height: H }, deviceScaleFactor: DPR,
  args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--disable-frame-rate-limit', '--disable-gpu-vsync',
    '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows'],
});
const page = browser.pages()[0] || await browser.newPage();
const consoleLog = [];
page.on('console', m => consoleLog.push({ t: Date.now(), type: m.type(), text: m.text().slice(0, 400) }));
page.on('pageerror', e => consoleLog.push({ t: Date.now(), type: 'pageerror', text: String(e.message).slice(0, 400) }));

const cdp = await page.context().newCDPSession(page);

const t0 = Date.now();
await page.goto(BASE + '?playtest=1' + Q + (process.env.EXTRA || ''));
await page.waitForFunction(() => window.__cmb && window.__sys && window.__ctx?.player && window.__ctx.stepFrame, null, { timeout: 300000 });
await page.waitForTimeout(6000); // loading screen out, warmup trickle, streaming settle
console.log(`[pt] game ready in ${((Date.now() - t0) / 1000).toFixed(1)} s (${W}x${H}, mode ${MODE})`);
// hide the controls help (H) for clean footage
const helpVisible = await page.evaluate(() => [...document.querySelectorAll('div')].some(d => d.offsetParent && /^CONTROLS/i.test(d.textContent.trim()) && d.textContent.length < 2000));
if (helpVisible) { await page.keyboard.press('KeyH'); }
await page.mouse.move(W / 2, H / 2);
const renderInfo = await page.evaluate(() => { const C = __ctx, dpr = devicePixelRatio, gl = C.renderer.getContext(), e = gl.getExtension('WEBGL_debug_renderer_info');
  return { devicePixelRatio: dpr, pixelRatio: C.renderer.getPixelRatio(), drawingBuffer: C.renderer.getDrawingBufferSize(new C.THREE.Vector2()).toArray(), css: [innerWidth, innerHeight],
    gpu: e ? gl.getParameter(e.UNMASKED_RENDERER_WEBGL) : '?', quality: C.lighting.quality?.name, maxTexUnits: gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS) }; });
console.log('[pt] render', JSON.stringify(renderInfo));

// ------------------------------------------------------------------------------------------------ scenario API
function makeApi(name) {
  const st = { frame: 0, log: [], marks: [], ff: null, done: null, rawPath: null, perFrame: null };
  const api = {
    name, W, H, MODE,
    ev: (fn, arg) => page.evaluate(fn, arg),
    down: k => page.keyboard.down(k), up: k => page.keyboard.up(k),
    tap: async k => { await page.keyboard.down(k); await api.sec(1 / 30); await page.keyboard.up(k); },
    mdown: (b = 'right') => page.mouse.down({ button: b }), mup: (b = 'right') => page.mouse.up({ button: b }),
    click: async (b = 'left') => { await page.mouse.down({ button: b }); await api.sec(1 / 20); await page.mouse.up({ button: b }); },
    look: (dx, dy = 0) => page.evaluate(([dx, dy]) => { __ctx.input.mouse.dx += dx; __ctx.input.mouse.dy += dy; }, [dx, dy]),
    mark: label => { st.marks.push({ t: +(st.frame / 60).toFixed(2), label }); console.log(`  [${name} ${(st.frame / 60).toFixed(2)}s] ${label}`); },
    get t() { return st.frame / 60; },
    state: () => page.evaluate(() => { const C = __ctx, p = C.player, v = p.velocity; const pt = window.__ptState?.() || {};
      return { pos: p.position.toArray().map(x => +x.toFixed(1)), spd: +v.length().toFixed(1), mode: p.mode, sub: pt.sub, trick: pt.trick, node: pt.node, clip: pt.aClip, cmb: pt.cmb ? `${pt.cmb.move} hp${pt.cmb.hp} c${pt.cmb.combo} ${pt.cmb.enemies}` : '', suit: pt.sys?.suit }; }),
    // advance t seconds of game time; fn(i) runs before each frame (film) / each ~16 ms (perf)
    async sec(t, fn = null) {
      const n = Math.max(1, Math.round(t * 60));
      for (let i = 0; i < n; i++) {
        if (fn) await fn(i);
        if (st.perFrame) await st.perFrame(st.frame);
        if (MODE === 'film') {
          await page.evaluate(() => __ctx.stepFrame(1 / 60));
          if (st.ff) {
            const f = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 92 });
            if (!st.ff.stdin.write(Buffer.from(f.data, 'base64'))) await once(st.ff.stdin, 'drain');
          }
        } else await page.waitForTimeout(1000 / 60);
        if (st.frame % 15 === 0) st.log.push({ t: +(st.frame / 60).toFixed(2), ...(await api.state()) });
        st.frame++;
      }
    },
    everyFrame(fn) { st.perFrame = fn; },
    async until(pred, max = 5, fn = null) { const end = st.frame + max * 60; while (st.frame < end) { await api.sec(1 / 60, fn); if (await page.evaluate(pred)) return true; } return false; },
    // steering autopilot (real W key held by the caller; only the CAMERA yaw is steered, through ctx.input.mouse.dx): heads for (x,z), picks the
    // clearest heading among +-offsets (world.raycast at 3 heights), detects being stuck and side-steps. Returns the distance to the target.
    async pilotInit() { await page.evaluate(() => {
      window.__pilot = { hist: [], esc: 0, escDir: 1, prev: 0 };
      window.__steer = (tx, tz, stop = 1.5) => {
        const C = __ctx, P = C.player, p = P.position, V = C.THREE.Vector3, pl = window.__pilot, wrap = a => Math.atan2(Math.sin(a), Math.cos(a));
        const dx = tx - p.x, dz = tz - p.z, dist = Math.hypot(dx, dz), goal = Math.atan2(dx, dz);
        const clear = h => { let m = 10; for (const y of [-0.4, 0.3, 0.9]) { const hit = C.world.raycast(new V(p.x, p.y + y, p.z), new V(Math.sin(h), 0, Math.cos(h)), 10); if (hit) m = Math.min(m, hit.distance); } return m; };
        pl.hist.push([p.x, p.z]); if (pl.hist.length > 50) pl.hist.shift();
        if (pl.esc <= 0 && pl.hist.length >= 50 && dist > stop + 1.5 && Math.hypot(pl.hist[0][0] - p.x, pl.hist[0][1] - p.z) < 1.0) { pl.esc = 50; pl.escDir *= -1; pl.hist.length = 0; }
        let h = goal;
        if (pl.esc > 0) { pl.esc--; h = goal + pl.escDir * 1.5; }
        else { let best = -1e9; for (const off of [0, 0.3, -0.3, 0.6, -0.6, 0.9, -0.9, 1.3, -1.3, 1.8, -1.8]) { const c = clear(goal + off), sc = Math.min(c, dist + 2, 7) - 1.6 * Math.abs(off) + (off * pl.prev > 0 ? 0.4 : 0) - (c < 2.2 ? 6 : 0); if (sc > best) { best = sc; h = goal + off; pl.prev = off; } } }
        const dyaw = Math.max(-0.09, Math.min(0.09, wrap(h - P.heading))); C.input.mouse.dx += -dyaw / 0.0023;
        return dist;
      };
    }); },
    // walk to a point ([x,z] or a JS expression string evaluated in the page returning [x,z]); W is held by the caller. true = arrived
    async goto(target, { stop = 2, max = 10 } = {}) {
      const end = st.frame + Math.round(max * 60);
      while (st.frame < end) {
        const d = await page.evaluate(([t, stop]) => { const [x, z] = typeof t === 'string' ? (0, eval)(t) : t; return window.__steer(x, z, stop); }, [target, stop]);
        if (d <= stop) return true;
        await api.sec(1 / 60);
      }
      return false;
    },
    teleport: (x, z, y = null, yaw = Math.PI) => page.evaluate(([x, z, y, yaw]) => { const C = __ctx; const gy = C.world.groundHeight(x, z, y ?? 999);
      C.player.teleport(new C.THREE.Vector3(x, y ?? gy + 1.0, z), yaw); }, [x, z, y, yaw]),
  };
  return { api, st };
}

// ------------------------------------------------------------------------------------------------ scenarios
const SPAWN = [250, 167.3];
const S = {};
async function reset(a, x = SPAWN[0], z = SPAWN[1], yaw = Math.PI) {
  await page.keyboard.up('KeyW'); await page.mouse.up({ button: 'right' });
  await a.ev(() => { __cmb.debug.end?.(); __ctx.input.releaseAll(); });
  await a.teleport(x, z, null, yaw); await a.sec(1.0);
}
async function swingChain(a, n, { hold = 1.25, gap = 0.3, spaceRel = false, yawFn = null } = {}) {
  for (let k = 0; k < n; k++) {
    await a.mdown('right'); await a.sec(hold, yawFn);
    if (spaceRel) await a.down('Space');
    await a.mup('right'); await a.sec(gap, yawFn);
    if (spaceRel) await a.up('Space');
  }
}

// (a) 20 s street-canyon swing chain at speed down the avenue from the spawn
S.swingChain = async a => {
  await reset(a);
  await a.mark('start: W held, jump, then RMB swing chain down the avenue');
  await a.down('KeyW'); await a.tap('Space'); await a.sec(0.35);
  await swingChain(a, 12, { hold: 1.2, gap: 0.35 });
  await a.mark('chain end');
  await a.sec(1.0); await a.up('KeyW'); await a.sec(1.0);
};
// (b) swing, Space-release (trick), dive (C held), web-zip (E) to a targeted rooftop point
S.trickZip = async a => {
  await reset(a);
  await a.down('KeyW'); await a.tap('Space'); await a.sec(0.35);
  await swingChain(a, 3, { hold: 1.2, gap: 0.35 });
  await a.mark('swing then Space-release');
  await a.mdown('right'); await a.sec(1.2); await a.down('Space'); await a.mup('right'); await a.sec(0.3); await a.up('Space');
  await a.sec(0.9);
  await a.mark('dive (C held)'); await a.down('KeyC'); await a.sec(1.0); await a.up('KeyC');
  await a.mark('look up + E web-zip to a point');
  await a.sec(0.5, () => a.look(0, -18));
  await a.tap('KeyE'); await a.sec(2.5);
  await a.up('KeyW');
  await a.mark('after zip (expect perch)'); await a.sec(2.0);
};
// (c) wall-run up a skyscraper (Shift + W into the facade), wall zips (E), top-out and perch
// Take 1 stood 6 m from a shop shutter (roof 20 m, low) and take 2 stood behind a parked car (the player cannot vault cars), so the
// approach point is now PROVEN with an un-filmed dry run: candidate facades (roof > 90 m) x lateral offsets are tried by holding
// Shift+W for ~1.7 s of un-captured frames; the first candidate whose player.mode becomes 'wall' is the one that is filmed.
S.wallRun = async a => {
  await reset(a);
  const cands = await a.ev(() => {
    const C = __ctx, V = (x, y, z) => new C.THREE.Vector3(x, y, z), out = [];
    for (const [ox, oz] of [[250, 120], [250, 60], [250, 0], [250, -60], [250, -120], [250, 200], [250, -200]]) for (let i = 0; i < 16; i++) {
      const ang = i / 16 * Math.PI * 2, d = V(Math.sin(ang), 0, Math.cos(ang)); const h = C.world.raycast(V(ox, 30, oz), d, 60);
      if (!h || Math.abs(h.normal.y) > 0.2) continue;
      const top = C.world.raycast(V(h.point.x - h.normal.x, 900, h.point.z - h.normal.z), V(0, -1, 0), 900); const roof = top ? top.point.y : 0;
      if (roof > 90) out.push({ p: h.point.toArray(), n: h.normal.clone().setY(0).normalize().toArray(), roof });
    }
    return out.sort((x, y) => y.roof - x.roof);
  });
  let chosen = null, tried = 0;
  outer: for (const c of cands) for (const lat of [0, -4, 4, -8, 8]) for (const dist of [6, 4]) {
    if (++tried > 14) break outer;
    const ok = await a.ev(([c, lat, dist]) => {
      const C = __ctx, n = new C.THREE.Vector3(...c.n), p = new C.THREE.Vector3(...c.p), t = new C.THREE.Vector3(-n.z, 0, n.x);
      const q = p.clone().addScaledVector(n, dist).addScaledVector(t, lat); q.y = C.world.groundHeight(q.x, q.z, 5) + 1.0;
      C.player.teleport(q, Math.atan2(-n.x, -n.z)); return q.toArray();
    }, [c, lat, dist]);
    await page.keyboard.down('ShiftLeft'); await page.keyboard.down('KeyW');
    let hit = false;
    for (let f = 0; f < 110 && !hit; f++) { await page.evaluate(() => __ctx.stepFrame(1 / 60)); hit = await page.evaluate(() => __ctx.player.mode === 'wall'); }
    await page.keyboard.up('ShiftLeft'); await page.keyboard.up('KeyW');
    await a.ev(() => { __ctx.input.releaseAll(); });
    console.log(`  [wallRun] candidate roof ${Math.round(c.roof)} lat ${lat} dist ${dist} -> ${hit ? 'WALL' : 'blocked'}`);
    if (hit) { chosen = { c, lat, dist, ok }; break outer; }
  }
  if (!chosen) { a.mark('NO wall-run approach found (all candidates blocked)'); await a.sec(2); return; }
  await a.ev(([c, lat, dist]) => {
    const C = __ctx, n = new C.THREE.Vector3(...c.n), p = new C.THREE.Vector3(...c.p), t = new C.THREE.Vector3(-n.z, 0, n.x);
    const q = p.clone().addScaledVector(n, dist).addScaledVector(t, lat); q.y = C.world.groundHeight(q.x, q.z, 5) + 1.0;
    C.player.teleport(q, Math.atan2(-n.x, -n.z));
  }, [chosen.c, chosen.lat, chosen.dist]);
  a.mark(`tower facade roof ${Math.round(chosen.c.roof)} m, start ${JSON.stringify(chosen.ok.map(x => +x.toFixed(1)))}`);
  await a.sec(0.8);
  await a.mark('Shift+W into the facade'); await a.down('ShiftLeft'); await a.down('KeyW');
  await a.sec(4.0);
  await a.mark('E: wall zip up'); await a.tap('KeyE'); await a.sec(2.0); await a.tap('KeyE'); await a.sec(2.0); await a.tap('KeyE'); await a.sec(3.0);
  await a.mark('keep running up until the top-out (max 12 s)');
  const top = await a.until(() => __ctx.player.mode !== 'wall', 12);
  a.mark(top ? 'left the wall (top-out / launch)' : 'STILL ON THE WALL after 12 s (no top-out)');
  await a.sec(2.5); await a.up('ShiftLeft'); await a.up('KeyW');
  await a.mark('released: expect perch / top'); await a.sec(3.0);
};
// (d) ground run through a street with crowd / traffic. Take 1 (W held, no steering) ended stuck in a subway-entrance stairwell / behind a
// hot-dog cart, so this take uses the steering autopilot along the east sidewalk of the avenue, then a Shift parkour run.
S.street = async a => {
  await reset(a, 262, 150, Math.PI);
  await a.pilotInit();
  await a.mark('run down the east sidewalk of the avenue (steering autopilot, W held)'); await a.down('KeyW');
  await a.goto([262, 60], { stop: 4, max: 9 });
  await a.mark('Shift parkour run'); await a.down('ShiftLeft');
  await a.goto([262, -40], { stop: 4, max: 9 });
  await a.up('ShiftLeft');
  await a.goto([262, -120], { stop: 4, max: 9 });
  await a.up('KeyW'); await a.sec(1.0);
};
// (e) street fight: spawned thugs, combos, dodge, web shooter, web strike, finisher
S.fight = async a => {
  await reset(a, 250, 120, Math.PI);
  const r = await a.ev(() => __cmb.debug.fight('mmgb', 8)); a.mark('fight spawned: ' + r);
  await a.sec(1.0);
  for (let round = 0; round < 3; round++) {
    await a.mark(`round ${round}: approach + 4-hit combo`);
    await a.down('KeyW'); await a.sec(0.4); await a.up('KeyW');
    for (let k = 0; k < 4; k++) { await a.click('left'); await a.sec(0.28); }
    await a.mark('dodge (Space)'); await a.tap('Space'); await a.sec(0.6);
    await a.mark('web shooter (F) x2'); await a.tap('KeyF'); await a.sec(0.4); await a.tap('KeyF'); await a.sec(0.5);
    await a.mark('launcher (LMB held)'); await a.mdown('left'); await a.sec(0.45); await a.mup('left'); await a.sec(0.4);
    for (let k = 0; k < 3; k++) { await a.click('left'); await a.sec(0.28); }
    await a.mark('web strike (E)'); await a.tap('KeyE'); await a.sec(0.8);
    await a.mark('finisher (Q)'); await a.tap('KeyQ'); await a.sec(1.2);
  }
  await a.sec(2.0);
};
// (f) water: swing out along the Hudson seawall, drop toward / into the river
S.water = async a => {
  const p = await a.ev(() => { const C = __ctx; return null; });
  // Hudson promenade near z = -440 (splash shot), facing south along the shore
  await reset(a, -1, -440, 0);
  const pos = await a.ev(() => { const C = __ctx; let x = -700; for (let xx = -900; xx < 200; xx += 2) if (C.world.groundHeight(xx, -440, 5) > -0.5) { x = xx; break; } return x; });
  await a.teleport(pos + 6, -440, null, -Math.PI / 2); await a.sec(1.0);
  await a.mark(`seawall at x=${pos}: run W west into the river`);
  await a.down('KeyW'); await a.sec(3.5);
  await a.mark('in / over water'); await a.sec(3.0);
  await a.mark('jump + swing attempt over the river'); await a.tap('Space'); await a.mdown('right'); await a.sec(1.5); await a.mup('right'); await a.sec(3.0);
  await a.up('KeyW'); await a.sec(1.0);
};
// (g) each suit worn while swinging (3 s each)
S.skins = async a => {
  await reset(a);
  await a.down('KeyW'); await a.tap('Space'); await a.sec(0.35);
  for (const id of ['advanced', 'iron', 'symbiote', 'claude', 'codex', 'gemini', 'kimi', 'qwen']) {
    await a.ev(id => __sys.debug.suit(id), id); a.mark('suit ' + id);
    await swingChain(a, 2, { hold: 1.15, gap: 0.35 });
  }
  await a.up('KeyW'); await a.sec(1.0);
};
// (h) citizens + animals up close while moving. Take 1 ran into a shop window and the camera collapsed into the hero's head at the end
// (kept as still bugs/camera_inside_hero.jpg); this take follows a dog walker, then walks up to a street critter.
S.crowd = async a => {
  await reset(a, 262.5, 172, Math.PI);
  await a.pilotInit();
  const dog = await a.ev(() => { const A = __ctx.world.life.crowd.agents, p = __ctx.player.position; let best = null, bd = 1e9;
    for (const g of A) if (g.dog && !g.dead) { const d = Math.hypot(g.x - p.x, g.z - p.z); if (d < bd) { bd = d; best = g; } }
    window.__dogA = best; return best ? [+best.x.toFixed(1), +best.z.toFixed(1), +bd.toFixed(1)] : null; });
  await a.mark('walk up to the nearest dog walker ' + JSON.stringify(dog)); await a.down('KeyW');
  await a.goto('[__dogA.x, __dogA.z]', { stop: 3, max: 9 });
  await a.mark('follow the dog walker for 7 s (camera glancing side to side)');
  for (let i = 0; i < 420; i++) {
    const d = await a.ev(() => window.__steer(__dogA.x, __dogA.z, 2.2));
    if (d > 2.6) await a.down('KeyW'); else if (d < 2.0) await a.up('KeyW');
    await a.sec(1 / 60, () => a.look(Math.sin(i / 50) * 2.5, 0));
  }
  const crit = await a.ev(() => { const p = __ctx.player.position; let best = null, bd = 1e9;
    for (const s of __ctx.world.life.critters.sites) for (const c of s.a || []) { const d = Math.hypot(c.x - p.x, c.z - p.z); if (d < bd) { bd = d; best = c; window.__critKind = s.kind; } }
    window.__crit = best; return best ? [window.__critKind, +best.x.toFixed(1), +best.z.toFixed(1), +bd.toFixed(1)] : null; });
  a.mark('walk up to the nearest street critter ' + JSON.stringify(crit));
  if (crit) { await a.down('KeyW'); await a.goto('[__crit.x, __crit.z]', { stop: 2.2, max: 12 }); }
  await a.up('KeyW'); await a.mark('stand next to it'); await a.sec(3.0);
};

// (bug evidence) hero runs straight at the side of a parked car: no vault / step-up, the run cycle plays in place against the door
// (an oblique approach slides along the body). Approach side chosen by an un-filmed dry run (sd = +1 / -1 around each of the nearest parked cars).
S.carBlock = async a => {
  await reset(a);
  const cars = await a.ev(() => { const C = __ctx, o = C.player.position.clone(); return (C.world.carsNear(o, 80) || []).filter(c => c.parked).slice(0, 4).map(c => ({ x: c.x, z: c.z, ry: c.ry, wid: c.wid })); });
  const place = ([c, sd]) => { const C = __ctx, V = (x, y, z) => new C.THREE.Vector3(x, y, z), fx = Math.cos(c.ry), fz = -Math.sin(c.ry), sx = -fz, sz = fx;
    const q = V(c.x + sx * sd * (c.wid / 2 + 5), 0, c.z + sz * sd * (c.wid / 2 + 5)); q.y = C.world.groundHeight(q.x, q.z, 1.5) + 1.0; C.player.teleport(q, Math.atan2(-sx * sd, -sz * sd)); return q.toArray(); };
  let chosen = null;
  outer: for (const c of cars) for (const sd of [-1, 1]) {
    await a.ev(place, [c, sd]); await page.keyboard.down('KeyW');
    let p0 = null; for (let f = 0; f < 120; f++) { await page.evaluate(() => __ctx.stepFrame(1 / 60)); if (f === 89) p0 = await a.ev(() => __ctx.player.position.toArray()); }
    const p1 = await a.ev(() => __ctx.player.position.toArray()); await page.keyboard.up('KeyW'); await a.ev(() => __ctx.input.releaseAll());
    const moved = Math.hypot(p1[0] - p0[0], p1[2] - p0[2]); console.log(`  [carBlock] car (${c.x.toFixed(1)}, ${c.z.toFixed(1)}) sd ${sd}: moved ${moved.toFixed(2)} m in the last 0.5 s of a 2 s run -> ${moved < 0.3 ? 'STUCK' : 'slides / passes'}`);
    if (moved < 0.3) { chosen = [c, sd]; break outer; }
  }
  if (!chosen) { a.mark('no head-on blocked approach found'); await a.sec(2); return; }
  await a.ev(place, chosen); a.mark('parked car at ' + JSON.stringify([+chosen[0].x.toFixed(1), +chosen[0].z.toFixed(1)]) + ': W held straight at its side');
  await a.sec(0.8); await a.down('KeyW'); await a.sec(5.0); await a.up('KeyW'); await a.sec(0.5);
};

// ------------------------------------------------------------------------------------------------ run
const summary = [];
for (const name of names) {
  const fn = S[name]; if (!fn) { console.error('unknown scenario', name); continue; }
  const { api, st } = makeApi(name);
  const tag = `${name}_${W}x${H}${DPR !== 1 ? '_dpr' + DPR : ''}${process.env.TAG ? '_' + process.env.TAG : ''}`;
  let perfHandle = null; const rec0 = {};
  if (MODE === 'film') {
    await page.evaluate(() => { __ctx.manualStep = true; });
    st.rawPath = path.join(SCRATCH, 'raw', `${tag}.mp4`);
    st.ff = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-framerate', '60', '-i', 'pipe:0',
      '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', st.rawPath], { stdio: ['pipe', 'ignore', 'inherit'] });
    st.done = once(st.ff, 'close');
  } else {
    rec0.gpuBefore = gpuLaunch;
    st.gpuSamples = []; st.gpuTimer = setInterval(async () => { const u = await gpuUtil(); if (u != null) st.gpuSamples.push(u); }, 1500);
    // rAF deltas + GPU time per frame from EXT_disjoint_timer_query_webgl2 wrapped around pipeline.render (the whole scene + post chain; excludes
    // the JS world / player update). rAF deltas alone can under-report when the browser does not throttle the page to GPU completion.
    await page.evaluate(() => { __ctx.manualStep = false; window.__ft = []; window.__gq = { pend: [], ms: [], disjoint: 0 }; let last = performance.now();
      const C = __ctx, gl = C.renderer.getContext(), ext = gl.getExtension('EXT_disjoint_timer_query_webgl2');
      if (ext && !C.__gqWrapped) { const orig = C.pipeline.render.bind(C.pipeline); C.__gqWrapped = true;
        C.pipeline.render = dt => { if (window.__gq.pend.length < 60 && !window.__ftStop) { const q = gl.createQuery(); gl.beginQuery(ext.TIME_ELAPSED_EXT, q); orig(dt); gl.endQuery(ext.TIME_ELAPSED_EXT); window.__gq.pend.push(q); } else orig(dt); }; }
      const poll = () => { const Q = window.__gq; while (Q.pend.length && gl.getQueryParameter(Q.pend[0], gl.QUERY_RESULT_AVAILABLE)) { const q = Q.pend.shift();
        if (gl.getParameter(ext.GPU_DISJOINT_EXT)) Q.disjoint++; else Q.ms.push(gl.getQueryParameter(q, gl.QUERY_RESULT) / 1e6); gl.deleteQuery(q); } };
      const f = now => { window.__ft.push(now - last); last = now; if (ext) poll(); if (!window.__ftStop) requestAnimationFrame(f); }; window.__ftStop = false; requestAnimationFrame(f); });
  }
  const c0 = consoleLog.length, w0 = Date.now();
  try { await fn(api); } catch (e) { console.error(`[pt] ${name} failed:`, e.message); api.mark('SCRIPT ERROR ' + e.message); }
  const wall = (Date.now() - w0) / 1000;
  const errs = consoleLog.slice(c0).filter(m => m.type === 'error' || m.type === 'pageerror' || m.type === 'warning');
  const counts = {}; for (const m of errs) { const k = m.type + ': ' + m.text.slice(0, 160); counts[k] = (counts[k] || 0) + 1; }
  const rec = { name, mode: MODE, W, H, render: renderInfo, gameSeconds: +(st.frame / 60).toFixed(2), wallSeconds: +wall.toFixed(1), marks: st.marks, console: counts, log: st.log };
  if (MODE === 'film') {
    st.ff.stdin.end(); await st.done;
    // committed copy: h264, <= ~14 MB (CRF 21 capped by a bitrate that fits the clip length)
    const dur = st.frame / 60, kbps = Math.floor(Math.min(12000, (13.5 * 8 * 1024) / Math.max(dur, 1)));
    const out = path.join(OUTDIR, 'clips', `${name}.mp4`);
    await once(spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', st.rawPath, '-c:v', 'libx264', '-preset', 'slow', '-crf', '21',
      '-maxrate', `${kbps}k`, '-bufsize', `${kbps}k`, '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: 'inherit' }), 'close');
    rec.clip = out; rec.clipMB = +(fs.statSync(out).size / 1048576).toFixed(2); rec.captureFps = '60 (frame-stepped game time, 1/60 s per frame)';
    await page.evaluate(() => { __ctx.manualStep = false; });
    fs.writeFileSync(path.join(OUTDIR, 'logs', `${name}.json`), JSON.stringify(rec, null, 1));
  } else {
    const ft = await page.evaluate(() => { window.__ftStop = true; return window.__ft; });
    await page.waitForTimeout(500); const gq = await page.evaluate(() => { const Q = window.__gq; return Q ? { ms: Q.ms, disjoint: Q.disjoint } : null; });
    clearInterval(st.gpuTimer); rec.gpuUtil = { before: rec0.gpuBefore, during: st.gpuSamples, duringMean: st.gpuSamples.length ? +(st.gpuSamples.reduce((x, y) => x + y, 0) / st.gpuSamples.length).toFixed(1) : null, after: await gpuUtil() };
    rec.contaminated = rec0.gpuBefore == null || rec0.gpuBefore > 25;
    rec.endRender = await page.evaluate(() => { const C = __ctx; return { pixelRatio: C.renderer.getPixelRatio(), drawingBuffer: C.renderer.getDrawingBufferSize(new C.THREE.Vector2()).toArray() }; });
    ft.shift(); const s = [...ft].sort((x, y) => x - y), pc = p => s[Math.min(s.length - 1, Math.floor(s.length * p))];
    const stats = { frames: ft.length, avg: +(ft.reduce((x, y) => x + y, 0) / ft.length).toFixed(2), median: +pc(0.5).toFixed(2), p95: +pc(0.95).toFixed(2), p99: +pc(0.99).toFixed(2), max: +s[s.length - 1].toFixed(1),
      hitches33: ft.filter(x => x > 33.4).length, hitches50: ft.filter(x => x > 50).length, fps: +(1000 / (ft.reduce((x, y) => x + y, 0) / ft.length)).toFixed(1) };
    if (gq && gq.ms.length) { const g = [...gq.ms].sort((x, y) => x - y), gp = p => g[Math.min(g.length - 1, Math.floor(g.length * p))]; stats.gpuMs = { n: g.length, disjoint: gq.disjoint, median: +gp(0.5).toFixed(2), p95: +gp(0.95).toFixed(2), p99: +gp(0.99).toFixed(2), max: +g[g.length - 1].toFixed(1), mean: +(g.reduce((x, y) => x + y, 0) / g.length).toFixed(2) }; rec.rawGpuMs = gq.ms.map(x => +x.toFixed(2)); }
    rec.frameTimes = stats; rec.gpu = await page.evaluate(() => { const i = __ctx.renderer.info.render; return { calls: i.calls, tris: i.triangles }; });
    fs.writeFileSync(path.join(OUTDIR, 'perf', `${tag}.json`), JSON.stringify({ ...rec, log: undefined, rawFrameTimes: ft.map(x => +x.toFixed(2)), rawGpuMs: rec.rawGpuMs }));
    console.log(`[perf] ${tag}: ${JSON.stringify(stats)} gpu before ${rec0.gpuBefore}% during-mean ${rec.gpuUtil.duringMean}% ${rec.contaminated ? 'CONTAMINATED' : 'quiet'}`);
  }
  summary.push({ name, clipMB: rec.clipMB, game: rec.gameSeconds, wall: rec.wallSeconds, errs: Object.keys(counts).length, ...(rec.frameTimes || {}), gpuBefore: rec.gpuUtil?.before, gpuMean: rec.gpuUtil?.duringMean });
  console.log(`[pt] ${name} done: ${rec.gameSeconds}s game / ${rec.wallSeconds}s wall`, Object.keys(counts).length ? 'console: ' + JSON.stringify(counts).slice(0, 600) : '');
}
console.table(summary);
fs.writeFileSync(path.join(SCRATCH, `console_${MODE}_${W}x${H}_${process.pid}.json`), JSON.stringify(consoleLog, null, 0));
await browser.close();
fs.rmSync(profile, { recursive: true, force: true });

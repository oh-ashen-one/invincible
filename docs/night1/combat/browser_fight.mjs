// Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
// P5 combat: the SAME scripted fight in the browser build (reference telemetry for the Unreal port).
//   node docs/night1/combat/browser_fight.mjs <script.json> <out_dir> [--render]
// Own vite on port 5206 (P5's dev port), own headless Chrome profile under <out_dir>/profile, ?playtest (no random crimes,
// in-memory save). The game loop is stepped by hand (ctx.manualStep + ctx.stepFrame(1/60): fixed 60 Hz like -benchmark -fps=60),
// Math.random is seeded, the fight is __cmb.debug.fight(spec, dist) on an open street spot, beats are dispatched as real
// key / mouse events at the same REAL times as in Unreal ('toward' = the stick toward that enemy: c.pickTarget gets that
// direction for 0.5 s). Chrome runs on software GL (SwiftShader: no GPU use, so no GPU slot) unless CMB_GPU=1. Rendering is skipped during the fight unless --render (the sim does not depend on it).
// Writes fight_events.jsonl, fight_beats.jsonl, fight_telemetry.csv, fight_summary.json (same schema as the Unreal director).
import { chromium } from 'playwright-core';
import { createServer } from 'vite';
import fs from 'fs';
const ROOT = new URL('../../..', import.meta.url).pathname.replace(/\/$/, '');
const [scriptPath, OUT] = process.argv.slice(2);
const RENDER = process.argv.includes('--render');
const S = JSON.parse(fs.readFileSync(scriptPath, 'utf8'));
fs.mkdirSync(OUT, { recursive: true });
const server = await createServer({ root: ROOT, server: { port: 5206, strictPort: true, host: '127.0.0.1' }, logLevel: 'error' });
await server.listen();
const ctxB = await chromium.launchPersistentContext(OUT + '/profile', { channel: 'chrome', headless: true, viewport: { width: 960, height: 540 },
  args: process.env.CMB_GPU ? ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] : ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-gpu-compositing'] }); // default: software GL, no GPU use
let code = 0;
try {
  const page = await ctxB.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.addInitScript(seed => { // seeded Math.random (mulberry32)
    let a = seed >>> 0; Math.random = () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  }, S.seed ?? 7);
  await page.goto('http://127.0.0.1:5206/?playtest=1');
  await page.waitForFunction(() => window.__cmb?.debug && window.__ctx?.player?.object && window.__ctx.stepFrame, null, { timeout: 300000 });
  await new Promise(r => setTimeout(r, 4000));
  const res = await page.evaluate(async ({ S, RENDER }) => {
    const ctx = window.__ctx, c = window.__cmb, P = ctx.player, W = ctx.world;
    ctx.manualStep = true;
    if (!RENDER) ctx.pipeline.render = () => {};
    const THREE = ctx.THREE;
    // ---- an open street spot near the spawn: ground within 1 m of the lowest nearby street level, 16 rays clear for 14 m
    const p0 = P.position.clone();
    function openAt(x, z) {
      const gy = W.groundHeight(x, z, p0.y + 60); if (!(gy > -50)) return -1;
      const o = new THREE.Vector3(x, gy + 1.0, z); let minD = 99;
      for (let i = 0; i < 16; i++) { const a = i / 16 * Math.PI * 2; const h = W.raycast(o, new THREE.Vector3(Math.sin(a), 0, Math.cos(a)), 14); if (h) minD = Math.min(minD, h.distance); }
      return { gy, minD };
    }
    let best = null;
    for (let r = 0; r <= 320 && !best; r += 8) for (let k = 0; k < Math.max(1, Math.round(r / 4)); k++) {
      const a = k / Math.max(1, Math.round(r / 4)) * Math.PI * 2, x = p0.x + Math.cos(a) * r, z = p0.z + Math.sin(a) * r;
      const q = openAt(x, z); if (q === -1 || q.minD < 14 || q.gy > 1.5) continue;
      best = { x, z, gy: q.gy }; break;
    }
    if (!best) return { err: 'no open street spot found near ' + p0.toArray() };
    P.teleport(new THREE.Vector3(best.x, best.gy + 0.95 + 0.05, best.z), 0);
    for (let i = 0; i < 60; i++) { ctx.stepFrame(1 / 60); await 0; } // settle on the ground
    // ---- instrumentation (wrap the director's API: every call site uses c.<fn>)
    const EV = [], BEATS = [], TEL = [];
    const tag = e => { const i = c.enemies.indexOf(e); return i >= 0 ? 'e' + (i + 1) : '?'; };
    let t0 = c.rtime;
    const log = s => EV.push({ rt: +(c.rtime - t0).toFixed(3), gt: +c.time.toFixed(3), ts: +(ctx.timeScale ?? 1).toFixed(3), move: c.spidey.moveName(), ev: s });
    const N = { hits: 0, whiffs: 0, kos: 0, launches: 0, air_hits: 0, finishers: 0, dodges: 0, perfect_dodges: 0, web_hits: 0, enemy_melee_hits: 0, shots: 0, shot_hits: 0, hitstops: 0, slowmos: 0 };
    let dmgTaken = 0;
    const wrap = (name, fn) => { const o = c[name]; c[name] = (...a) => fn(o, ...a); };
    wrap('playerHit', (o, e, h) => {
      const hp0 = e?.hp, st0 = e?.state, alive = e?.alive; o(e, h);
      if (!e || !alive) return;
      const hitIt = e.hp !== hp0 || e.state !== st0 || h.kind === 'finisher';
      if (!hitIt) { N.whiffs++; log(`whiff ${h.kind} -> ${tag(e)}`); return; }
      N.hits++; if (h.kind === 'launch' && e.state === 'air') N.launches++; if (h.kind === 'air' || h.kind === 'slam') N.air_hits++; if (h.kind === 'finisher') N.finishers++;
      log(`hit ${h.kind} -> ${tag(e)} dmg ${h.dmg} hp ${Math.max(0, Math.round(e.hp))} state ${e.state} combo ${c.combo.n} focus ${c.spidey.focus.toFixed(2)}`);
    });
    wrap('enemyStrike', (o, e) => { const hp0 = c.spidey.hp; o(e); const d = hp0 - c.spidey.hp; if (d > 0) { N.enemy_melee_hits++; dmgTaken += d; log(`hero hit by ${tag(e)} ${e.atk} dmg ${d} hp ${Math.round(c.spidey.hp)}`); } else log(`enemy swing ${tag(e)} ${e.atk} missed`); });
    wrap('enemyShoot', (o, e) => { const hp0 = c.spidey.hp; o(e); N.shots++; const d = hp0 - c.spidey.hp; if (d > 0) { N.shot_hits++; dmgTaken += d; log(`shot ${tag(e)} HIT hp ${Math.round(c.spidey.hp)}`); } else log(`shot ${tag(e)} missed`); });
    wrap('onDodge', (o, t, perfect) => { o(t, perfect); N.dodges++; if (perfect) N.perfect_dodges++; log(`dodge ${perfect ? 'PERFECT' : 'plain'} threat=${t ? tag(t.e) : 'none'}`); });
    wrap('onEnemyOut', (o, e, how) => { o(e, how); N.kos++; log(`out ${tag(e)} ${how}`); });
    wrap('slowmo', (o, d, s, ea) => { o(d, s, ea); N.slowmos++; log(`slowmo ${(+d).toFixed(2)} s x${(+(s ?? 0.3)).toFixed(2)}`); });
    wrap('hitStop', (o, d, s) => { o(d, s); N.hitstops++; });
    wrap('cine', (o, t, d, k) => { o(t, d, k); log(`cine ${k || 'finisher'} ${tag(t)} ${(+d).toFixed(2)} s`); });
    wrap('threat', (o, e, lead, kind) => { o(e, lead, kind); log(`threat ${tag(e)} ${kind} lead ${(+lead).toFixed(2)}`); });
    let toward = null, towardUntil = -1;
    wrap('pickTarget', (o, dir, ...rest) => {
      if (toward && c.rtime <= towardUntil && toward.alive) { const d = new THREE.Vector3(toward.pos.x - P.position.x, 0, toward.pos.z - P.position.z).normalize(); return o(d, ...rest); }
      return o(dir, ...rest);
    });
    let lastMove = 'free';
    const key = code => { dispatchEvent(new KeyboardEvent('keydown', { code, key: code })); dispatchEvent(new KeyboardEvent('keyup', { code, key: code })); };
    const KEYS = { web: 'KeyF', strike: 'KeyE', finisher: 'KeyQ', heal: 'KeyZ', throw: 'KeyR', dodge: 'KeyC' };
    const beats = S.beats.map(b => ({ ...b, fired: false }));
    let started = false, webSeen = new WeakMap(), lmbUpAt = -1;
    t0 = c.rtime;
    const quit = S.quit ?? 27;
    for (let f = 0; f < Math.round(quit * 60) + 1; f++) {
      const rt = c.rtime - t0;
      if (!started && rt >= (S.start ?? 1)) {
        started = true;
        const types = await c.debug.fight(S.spec, S.dist ?? 7);
        // count web-shot hits (addWeb 0.34 from the web shooter) on the fight's enemies
        const proto = Object.getPrototypeOf(c.enemies[0]); const oAdd = proto.addWeb;
        proto.addWeb = function (amount, dir) { const alive = this.alive; oAdd.call(this, amount, dir); if (alive && Math.abs(amount - 0.34) < 1e-6) { N.web_hits++; log(`web hit ${tag(this)} web ${this.web.toFixed(2)} state ${this.state}`); } };
        log('fight start ' + c.enemies.map((e, i) => `e${i + 1}:${e.type}(${e.pos.x.toFixed(1)},${e.pos.z.toFixed(1)})`).join(' ') + ' types ' + types);
      }
      if (lmbUpAt >= 0 && rt >= lmbUpAt) { dispatchEvent(new MouseEvent('mouseup', { button: 0 })); lmbUpAt = -1; }
      for (const b of beats) {
        if (b.fired || rt < b.t) continue;
        b.fired = true;
        toward = b.toward ? c.enemies[+b.toward.slice(1) - 1] || null : null; towardUntil = c.rtime + 0.5;
        if (b.key === 'attack') { dispatchEvent(new MouseEvent('mousedown', { button: 0 })); if (b.hold > 0) lmbUpAt = rt + b.hold; else dispatchEvent(new MouseEvent('mouseup', { button: 0 })); }
        else if (KEYS[b.key]) key(KEYS[b.key]);
        BEATS.push({ t: b.t, rt: +rt.toFixed(3), gt: +c.time.toFixed(3), key: b.key, hold: b.hold || 0, toward: b.toward || '', label: b.label || '', move_before: c.spidey.moveName() });
      }
      ctx.stepFrame(1 / 60);
      await 0;
      const mv = c.spidey.moveName();
      if (mv !== lastMove) { if (mv !== 'free') log(`move ${mv}${c.spidey.target ? ' -> ' + tag(c.spidey.target) : ''}`); lastMove = mv; }
      const st = c.state;
      TEL.push([f, +(rt).toFixed(4), +c.time.toFixed(4), st.ts, st.move, P.position.x.toFixed(3), P.position.z.toFixed(3), P.position.y.toFixed(3), st.hp, st.focus, st.combo, st.sense, st.cine || '-', P.mode, (c.camW || 0).toFixed(2), JSON.stringify(st.enemies)].join(','));
    }
    const tsArr = TEL.map(r => +r.split(',')[3]);
    const slow = TEL.filter(r => +r.split(',')[3] < 0.999).length / 60;
    const alive = c.enemies.filter(e => e.alive).length;
    const summary = { engine: 'browser', frames: TEL.length, real_s: +(TEL.length / 60).toFixed(3), game_s: +c.time.toFixed(3), enemies: c.enemies.length, enemies_alive: alive, final_states: c.state.enemies,
      hero_hp: Math.round(c.spidey.hp), hero_focus: +c.spidey.focus.toFixed(2), damage_taken: dmgTaken, ...N, min_timescale: Math.min(...tsArr), slowmo_real_s: +slow.toFixed(3),
      beats: beats.length, beats_fired: beats.filter(b => b.fired).length, spot: best };
    return { EV, BEATS, TEL, summary };
  }, { S, RENDER });
  if (res.err) { console.error(res.err); code = 1; }
  else {
    fs.writeFileSync(OUT + '/fight_events.jsonl', res.EV.map(e => JSON.stringify(e)).join('\n') + '\n');
    fs.writeFileSync(OUT + '/fight_beats.jsonl', res.BEATS.map(e => JSON.stringify(e)).join('\n') + '\n');
    fs.writeFileSync(OUT + '/fight_telemetry.csv', 'frame,rt,gt,timescale,move,x_m,z_m,y_m,hp,focus,combo,sense,cine,trav,cam_w,enemies\n' + res.TEL.join('\n') + '\n');
    res.summary.console_errors = errs.slice(0, 10);
    fs.writeFileSync(OUT + '/fight_summary.json', JSON.stringify(res.summary, null, 1));
    console.log(JSON.stringify(res.summary));
  }
} finally { await ctxB.close(); await server.close(); }
process.exit(code);

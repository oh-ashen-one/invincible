// Headless load check after the round-04 / round-05 hero clip edits (round 05 adds runLeap / runLeapB): the game loads, the player rig has the edited `run` (17/30 s), the new
// `runTakeoff`, every other clip, and a few seconds of play raise no console errors. Port 5203 only.
// Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.
//   node tools/ue_char/heroanim/browser_check.mjs [OUT_DIR]
import { chromium } from 'playwright-core';
import { createServer } from 'vite';
const ROOT = new URL('../../..', import.meta.url).pathname.replace(/\/$/, '');
const SCR = process.env.P2_SCRATCH || ROOT + '/unreal/WebHomage/Saved/P2Build';
const OUT = process.argv[2] || SCR + '/r4/browser';
const server = await createServer({ root: ROOT, server: { port: 5203, strictPort: true, host: '127.0.0.1' }, logLevel: 'error' });
await server.listen();
const ctxB = await chromium.launchPersistentContext(OUT + '/profile', { channel: 'chrome', headless: true, viewport: { width: 1280, height: 720 },
  args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
let code = 0;
try {
  const page = await ctxB.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto('http://127.0.0.1:5203/');
  await page.waitForFunction(() => window.__ctx?.player?.object, null, { timeout: 240000 });
  await new Promise(r => setTimeout(r, 4000));
  const info = await page.evaluate(() => {
    const p = window.__ctx.player; const found = {};
    const scan = o => { for (const a of (o.animations || [])) found[a.name] = +a.duration.toFixed(4); };
    p.object.traverse(scan); scan(p.rig || {}); if (p.rig?.clips) for (const [k, c] of (p.rig.clips.entries?.() || Object.entries(p.rig.clips))) found[k] = +(c.duration ?? c.clip?.duration ?? 0).toFixed(4);
    return { n: Object.keys(found).length, run: found.run, runTakeoff: found.runTakeoff, runLeap: found.runLeap, runLeapB: found.runLeapB, jog: found.jog, sprint: found.sprint, hasClip: p.rig?.hasClip?.('run') };
  });
  await page.screenshot({ path: OUT + '/game.png' });
  console.log(JSON.stringify(info), errs.length ? 'ERRORS: ' + errs.slice(0, 5).join(' | ') : 'no console errors');
  if (!info.hasClip || errs.length) code = 1;
} finally { await ctxB.close(); await server.close(); }
process.exit(code);

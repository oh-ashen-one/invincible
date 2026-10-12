// Shared harness for the night-mode exporter / reference shots: a Vite dev server rooted at the author's checkout
// (~/spiderbench, read-only, pinned commit) with serve-time exposure hooks, and a headless Chrome (Metal ANGLE) page.
// Nothing here writes into the checkout: Vite's dep cache goes to a scratch dir and the injections exist only in the
// transformed modules the server hands to the browser.
import { chromium } from 'playwright-core';
import { createServer } from 'vite';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

export const SPIDER = path.join(os.homedir(), 'spiderbench');
export const PINNED = '64d957f92f005a1c1870070079351e30b2395661';
export const SCRATCH = path.join(os.homedir(), 'sm2-n1/_scratch/night');
const FORBIDDEN_PORTS = new Set([5173, 5191, 5192, 5208]);

export function assertPinnedCheckout() {
  const git = (...a) => execFileSync('git', ['-C', SPIDER, ...a], { encoding: 'utf8' }).trim();
  const head = git('rev-parse', 'HEAD');
  if (head !== PINNED) throw new Error(`~/spiderbench is at ${head}, expected ${PINNED}`);
  const dirty = git('status', '--porcelain');
  if (dirty) throw new Error('~/spiderbench tree is not clean:\n' + dirty);
  return head;
}

// ---- serve-time injections. Every anchor is an exact string; a missing anchor aborts (never silently skipped).
// mode 'eof'   : append `code` at the end of the module (after every module-scoped declaration exists)
// mode 'after' : insert `code` right after the anchor, same line (keeps line numbers of the original source)
// mode 'before': insert `code` right before the anchor, same line
const CAT_MAP = `{ 'props.js': 'street_lamp', 'facade.js': 'shop_front', 'neon.js': 'neon', 'screenlights.js': 'screen', 'skyline.js': 'skyline_flood', 'bridges.js': 'bridge_lamp', 'park.js': 'park_lamp' }`;
export const INJECTIONS = [
  { file: 'src/render/citylights.js', mode: 'eof', anchor: 'export { cityLights };', code: `
;{ const __sm2Add = cityLights.add; const __sm2Map = ${CAT_MAP};
  cityLights.add = function (o) {
    const id = __sm2Add.call(this, o); const r = statics[id]; let f = '?', ln = 0;
    try { for (const l of new Error().stack.split('\\n').slice(1)) { const m = /\\/src\\/([^\\s:?)]+)(?:\\?[^\\s:)]*)?:(\\d+):\\d+/.exec(l); if (!m || m[1] === 'render/citylights.js') continue; f = m[1]; ln = +m[2]; break; } } catch (e) {}
    const base = f.split('/').pop(); r.cat = __sm2Map[base] ?? ('other:' + base + ':' + ln); r.file = f; r.line = ln; return id;
  }; }
window.__sm2CL = { statics, providers, cityLights, amb: { AMB_R, AMB_SOFT, AMB_GAIN, CL_CELL, CL_N, CL_SLOTS, CL_TPC, CL_MAXL, CL_LAYER_Y, CL_UN, CL_SH_N, BUCKET } };
` },
  { file: 'src/world/facade.js', mode: 'after', anchor: "if (typeof window !== 'undefined') window.__winLights = WL;",
    code: ' window.__sm2Facade = { WF, WB, WFN, faceBands, WL, SHOP_FRONTS, SHOP_LIGHT, floodU, NFLOOD };' },
  { file: 'src/world/screenlights.js', mode: 'eof', anchor: 'export function screenNightMat(m, key) {',
    code: '\n;window.__sm2Screens = { boards, SL, all, uScrBoost, uScrDesat, uScrKnee, uScrTop };\n' },
  { file: 'src/world/screenlights.js', mode: 'before', anchor: 'e.sync(); E.e = e; all.push(e);',
    code: 'e.panels = (E.list || [E]).map(q => ({ c: q.c, n: q.n, u: q.u, w: q.w, h: q.h, uv: q.uv ?? null, avg: q.avg ?? null, pr: !!q.pr, k: q.k ?? 1 })); ' },
  { file: 'src/world/props.js', mode: 'after', anchor: 'const _bc = new THREE.Color();',
    code: ' (window.__sm2Props ??= {}).bladeBlock = { BL_R, BL_N, rec, WARM };' },
  { file: 'src/world/props.js', mode: 'after', anchor: 'const near = new Array(SIG_N).fill(null), nearD = new Float32Array(SIG_N);',
    code: ' (window.__sm2Props ??= {}).signalBlock = { SIG_R, SIG_N, SIG_COL, rec };' },
  { file: 'src/world/props.js', mode: 'before', anchor: 'const pools = Object.values(P);',
    code: 'Object.assign(window.__sm2Props ??= {}, { P, signals, bladeSignCol }); ' },
  { file: 'src/world/neon.js', mode: 'after', anchor: 'Object.assign(window.__neon, { relight, tubes: tubeMesh, words: wordMesh });',
    code: ' window.__sm2Neon = { tubes, words, lights, stats, NEON, ASPECT, W_, C, VENUES };' },
];

export function injectionPlugin() {
  const applied = new Set();
  const plugin = {
    name: 'sm2-night-hooks', enforce: 'post',
    transform(code, id) {
      const clean = id.split('?')[0].replace(/\\/g, '/');
      const rel = clean.startsWith(SPIDER + '/') ? clean.slice(SPIDER.length + 1) : null;
      if (!rel) return null;
      const mine = INJECTIONS.filter(j => j.file === rel);
      if (!mine.length) return null;
      let out = code;
      for (const j of mine) {
        const n = out.split(j.anchor).length - 1;
        if (n !== 1) throw new Error(`[sm2 night hooks] anchor for ${rel} found ${n} times (need exactly 1): ${j.anchor}`);
        if (j.mode === 'eof') out = out + j.code;
        else if (j.mode === 'after') out = out.replace(j.anchor, () => j.anchor + j.code);
        else out = out.replace(j.anchor, () => j.code + j.anchor);
        applied.add(`${j.file}|${j.anchor}`);
      }
      return { code: out, map: null };
    },
  };
  const missing = () => INJECTIONS.filter(j => !applied.has(`${j.file}|${j.anchor}`)).map(j => `${j.file}: ${j.anchor}`);
  return { plugin, missing };
}

export async function startServer({ inject = true } = {}) {
  assertPinnedCheckout();
  const hooks = injectionPlugin();
  const cacheDir = path.join(SCRATCH, 'vite-cache');
  fs.mkdirSync(cacheDir, { recursive: true });
  const server = await createServer({
    root: SPIDER, cacheDir, logLevel: 'error', plugins: inject ? [hooks.plugin] : [],
    server: { port: 5300 + Math.floor(Math.random() * 400), strictPort: false, host: '127.0.0.1', fs: { strict: true } },
  });
  await server.listen();
  const port = server.config.server.port;
  if (FORBIDDEN_PORTS.has(port)) { await server.close(); throw new Error('picked a reserved port ' + port); }
  return { server, base: server.resolvedUrls.local[0], missing: hooks.missing };
}

export async function launchBrowser() {
  return chromium.launch({ channel: 'chrome', headless: true, args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'] });
}

// one page, loaded to the shot harness' ready flag (the city is built and the frame loop has run its warm-up frames at night)
export async function openNight(browser, base, { shot = 'street', W = 1920, H = 1080, timeout = 480000 } = {}) {
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const errs = [];
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  await page.goto(new URL(`?shot=${shot}&tod=night`, base).href);
  await page.waitForFunction(() => window.__shotReady === true, null, { timeout });
  return { page, errs };
}

// render n more frames of the harness loop (providers, light grid, TAA history) without moving anything
export async function stepFrames(page, n) {
  await page.evaluate(async (n) => {
    const { world, camera, lighting, hud, pipeline } = window.__ctx;
    for (let i = 0; i < n; i++) { world.update(1 / 60, camera); lighting.update(camera); hud.update(1 / 60); pipeline.render(1 / 60); await new Promise(r => requestAnimationFrame(r)); }
  }, n);
}

export function lineOf(file, regex, nLines = 1) {
  const lines = fs.readFileSync(path.join(SPIDER, file), 'utf8').split('\n');
  const i = lines.findIndex(l => regex.test(l));
  if (i < 0) throw new Error(`excerpt anchor not found in ${file}: ${regex}`);
  return { file, line: i + 1, text: lines.slice(i, i + nLines).join('\n') };
}

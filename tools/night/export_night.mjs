// Night-mode data exporter: dumps every light of the original author's night city (browser, ~/spiderbench @ 64d957f) as
// JSON for the Unreal night port. Read-only: exposure hooks are injected at serve time (tools/night/common.mjs).
//   node tools/night/export_night.mjs            -> ~/sm2-n1/_scratch/night/export/night_lights.json (+ night_lights_summary.json)
// Frame: browser metres, +x east, +y up, -z north; UE cm = (x, z, y) * 100 (same as tools/export/export_city.mjs).
import fs from 'node:fs';
import path from 'node:path';
import { SPIDER, PINNED, SCRATCH, startServer, launchBrowser, openNight, stepFrames, lineOf } from './common.mjs';

const OUT = process.env.OUT || path.join(SCRATCH, 'export');
fs.mkdirSync(OUT, { recursive: true });
const t0 = Date.now();
const log = (...a) => console.log(`[export_night ${((Date.now() - t0) / 1000).toFixed(0)}s]`, ...a);

const { server, base, missing } = await startServer({ inject: true });
const browser = await launchBrowser();
let result;
try {
  log('server', base);
  const { page, errs } = await openNight(browser, base, { shot: 'street' });
  log('shot ready; page errors so far:', errs.length);
  const miss = missing();
  if (miss.length) throw new Error('exposure hooks were not applied (modules not served?):\n' + miss.join('\n'));
  await stepFrames(page, 12);
  // atlas-dependent lights (screens, blade colours) register when their images are decoded
  await page.waitForFunction(() => (window.__screenLightStats || []).every(s => !s.pending) && (window.__sm2Props?.bladeSignCol?.length ?? 0) > 0, null, { timeout: 120000 });
  await stepFrames(page, 12);
  const gate = await page.evaluate(() => ({ nightK: window.__ctx.lighting.tod.windows, tod: window.__ctx.lighting.tod.name, statics: window.__sm2CL.statics.filter(Boolean).length,
    frameLights: window.__sm2CL.cityLights.stats.lights, hooks: ['__sm2CL', '__sm2Facade', '__sm2Screens', '__sm2Props', '__sm2Neon'].filter(k => !window[k]) }));
  log('gate', JSON.stringify(gate));
  if (gate.hooks.length) throw new Error('missing page hooks: ' + gate.hooks);
  if (!(gate.nightK > 0.99)) throw new Error('not at full night: ' + gate.nightK);
  if (!gate.statics) throw new Error('no static city lights recorded');

  // ---------------------------------------------------------------- page-side serialisers
  const prelude = () => {
    const r4 = (v) => Math.round(v * 1e4) / 1e4;
    const arr = (a) => Array.from(a, r4);
    const s2l = (c) => (c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
    const l2s = (c) => (c <= 0.0031308 ? c * 12.92 : 1.055 * Math.pow(c, 1 / 2.4) - 0.055);
    const colour = (c) => { // -> { srgb, linear } of an authored colour (hex number | [r,g,b] sRGB 0..1 | THREE.Color (linear working space))
      if (c == null) return { srgb: [1, 1, 1], linear: [1, 1, 1] };
      if (typeof c === 'number') { const s = [(c >> 16 & 255) / 255, (c >> 8 & 255) / 255, (c & 255) / 255]; return { srgb: arr(s), linear: arr(s.map(s2l)), hex: c }; }
      if (Array.isArray(c)) return { srgb: arr(c.slice(0, 3)), linear: arr(c.slice(0, 3).map(s2l)) };
      if (c.isColor) return { srgb: arr([c.r, c.g, c.b].map(l2s)), linear: arr([c.r, c.g, c.b]) };
      return { srgb: null, linear: null, raw: String(c) };
    };
    const plain = (v, depth = 0) => {
      if (v == null || typeof v === 'boolean' || typeof v === 'string') return v;
      if (typeof v === 'number') return Number.isFinite(v) ? r4(v) : null;
      if (v.isColor) return { linear: arr([v.r, v.g, v.b]) };
      if (v.isVector3) return arr([v.x, v.y, v.z]);
      if (Array.isArray(v) || ArrayBuffer.isView(v)) return Array.from(v, x => plain(x, depth + 1));
      if (typeof v === 'object' && depth < 4) { const o = {}; for (const k of Object.keys(v)) if (typeof v[k] !== 'function') o[k] = plain(v[k], depth + 1); return o; }
      return undefined;
    };
    return { r4, arr, colour, plain };
  };
  const P = `(${prelude.toString()})()`;
  const run = (fn, arg) => page.evaluate(`(async () => { const { r4, arr, colour, plain } = ${P}; return (${fn.toString()})(${JSON.stringify(arg ?? null)}, { r4, arr, colour, plain }); })()`);

  // ---- statics
  const statics = await run((_, h) => window.__sm2CL.statics.filter(Boolean).map(r => {
    const s = r.src || {}, col = h.colour(s.color), I = s.intensity ?? 1;
    return {
      id: r.id, cat: r.cat, file: r.file, line: r.line, type: ['point', 'spot', 'rect'][r.type],
      pos: h.arr(r.p), dir: h.arr(r.d), u: h.arr(r.u), width: h.r4(r.hw * 2), height: h.r4(r.hh * 2),
      color_srgb: col.srgb, color_linear: col.linear, intensity: h.r4(I), color_linear_premult: h.arr(r.c),
      range: h.r4(r.range), cosO: h.r4(r.cosO), cosI: h.r4(r.cosI), angle: s.angle ?? null, penumbra: s.penumbra ?? null,
      radius: h.r4(r.radius), volume: h.r4(r.vol), spec: h.r4(r.spec), day: r.day, noShadow: r.noShadow, key: r.key,
      lum: h.r4(r.lum), src: h.plain(s),
    };
  }));
  log('statics', statics.length);

  // ---- windows: every recorded face, bands + runs computed with the facade provider's own code
  const winMeta = await run((_, h) => { const F = window.__sm2Facade; return { faces: F.WF.length / F.WFN, WL: h.plain({ ...F.WL, list: undefined }), WFN: F.WFN }; });
  const faces = [];
  const CH = 1500;
  for (let a = 0; a < winMeta.faces; a += CH) {
    const part = await run(({ a, b }, h) => {
      const F = window.__sm2Facade, A = F.WF.a, out = [];
      for (let fi = a; fi < Math.min(b, F.WF.length / F.WFN); fi++) {
        const o = fi * F.WFN, cx = A[o], cz = A[o + 1], tx = A[o + 2], tz = A[o + 3], nx = -tz, nz = tx;
        const rect = (u0, u1, y, hh, r, g, b) => { // the provider's setRect()
          const uc = (u0 + u1) / 2, w = Math.max(0.3, u1 - u0);
          return { pos: [h.r4(cx + tx * uc + nx * 0.05), h.r4(y), h.r4(cz + tz * uc + nz * 0.05)], dir: [h.r4(nx), 0, h.r4(nz)], u: [h.r4(tx), 0, h.r4(tz)],
            width: h.r4(w), height: h.r4(hh), color_linear: [h.r4(r), h.r4(g), h.r4(b)], intensity: F.WL.K, radius: 1.6, range: h.r4(Math.min(22, F.WL.range + 0.35 * Math.sqrt(w * hh))) };
        };
        const bands = F.faceBands(fi).map(b => {
          const runs = [];
          for (let j = 0; j < b.runs.length; j += 7) { const q = b.runs; runs.push({ u0: h.r4(q[j]), u1: h.r4(q[j + 1]), y: h.r4(q[j + 2]), h: h.r4(q[j + 3]), rgb: [h.r4(q[j + 4]), h.r4(q[j + 5]), h.r4(q[j + 6])], rect: rect(q[j], q[j + 1], q[j + 2], q[j + 3], q[j + 4], q[j + 5], q[j + 6]) }); }
          const q = b.band;
          return { y: h.r4(b.y), band: { u0: h.r4(q[0]), u1: h.r4(q[1]), y: h.r4(q[2]), h: h.r4(q[3]), rgb: [h.r4(q[4]), h.r4(q[5]), h.r4(q[6])], rect: rect(q[0], q[1], q[2], q[3], q[4], q[5], q[6]) }, runs };
        });
        out.push({ i: fi, corner: [h.r4(cx), h.r4(cz)], T: [h.r4(tx), h.r4(tz)], N: [h.r4(nx), h.r4(nz)], W: h.r4(A[o + 4]), y0: h.r4(A[o + 5]), y1: h.r4(A[o + 6]),
          floorH: h.r4(A[o + 7]), bayW: h.r4(A[o + 8]), winW: h.r4(A[o + 9]), winH: h.r4(A[o + 10]), margin: h.r4(A[o + 11]), seed: h.r4(A[o + 12]),
          style: A[o + 13] % 8, resid: A[o + 13] >= 8, gH: h.r4(A[o + 14]), baseY: h.r4(A[o + 15]), bands });
      }
      return out;
    }, { a, b: a + CH });
    faces.push(...part);
    if ((a / CH) % 5 === 0) log('window faces', faces.length, '/', winMeta.faces);
  }
  const winCounts = { faces: faces.length, faces_with_lit: faces.filter(f => f.bands.length).length, bands: faces.reduce((n, f) => n + f.bands.length, 0), runs: faces.reduce((n, f) => n + f.bands.reduce((m, b) => m + b.runs.length, 0), 0) };
  log('windows', JSON.stringify(winCounts));

  // ---- facade extras, screens, props, neon
  const facadeExtra = await run((_, h) => {
    const F = window.__sm2Facade, V = F.floodU.uFl.value, n = F.floodU.uFlY.value.y, floods = [];
    for (let i = 0; i < n; i++) floods.push({ box: { x0: h.r4(V[i * 3].x), z0: h.r4(V[i * 3].y), x1: h.r4(V[i * 3].z), z1: h.r4(V[i * 3].w) }, y0: h.r4(V[i * 3 + 1].x), y1: h.r4(V[i * 3 + 1].y), reach: h.r4(V[i * 3 + 1].z), pad: h.r4(V[i * 3 + 1].w),
      rgb_gain: [h.r4(V[i * 3 + 2].x), h.r4(V[i * 3 + 2].y), h.r4(V[i * 3 + 2].z)], streak: h.r4(V[i * 3 + 2].w) });
    const sl = { ...F.SHOP_LIGHT }; delete sl.pos; delete sl.ids;
    return { shop_fronts: F.SHOP_FRONTS.map(s => h.plain(s)), shop_light: h.plain(sl), crown_floods: floods, flood_bb: h.arr([F.floodU.uFlBB.value.x, F.floodU.uFlBB.value.y, F.floodU.uFlBB.value.z, F.floodU.uFlBB.value.w]), flood_y: h.arr([F.floodU.uFlY.value.x, F.floodU.uFlY.value.y]), NFLOOD: F.NFLOOD };
  });
  const boards = await run((_, h) => {
    const byRec = new Map(window.__sm2Screens.all.filter(e => e.rec).map(e => [e.rec, e]));
    const rec = (r) => { const e = byRec.get(r) || {}; return { pos: h.arr(r.pos), dir: h.arr(r.dir), u: h.arr(r.u), width: h.r4(r.width), height: h.r4(r.height), color_linear_premult: h.arr([r.color.r, r.color.g, r.color.b]),
      range: h.r4(r.range), radius: h.r4(r.radius), volume: h.r4(r.volume), avg_linear: e.avg ? h.arr(e.avg) : null, printed: !!e.pr, tag: e.tag ?? null, gain: e.g ?? null,
      panels: e.panels ? e.panels.map(q => ({ c: h.arr(q.c), n: h.arr(q.n), u: h.arr(q.u), w: h.r4(q.w), h: h.r4(q.h), uv: q.uv ? h.arr(q.uv) : null, avg: q.avg ? h.arr(q.avg) : null, printed: q.pr, k: q.k })) : null }; };
    return window.__sm2Screens.boards.map(b => ({ x: h.r4(b.x), z: h.r4(b.z), R: h.r4(b.R), lod_near: h.r4(b.lod), far: h.r4(b.far), whole: rec(b.whole), tiles: b.tiles ? b.tiles.map(rec) : [] }));
  });
  const screensExtra = await run((_, h) => { const S = window.__sm2Screens; return { SL: h.plain(S.SL), uScrBoost: S.uScrBoost.value, uScrDesat: S.uScrDesat.value, uScrKnee: S.uScrKnee.value, uScrTop: S.uScrTop.value }; });
  const props = await run((_, h) => {
    const Pr = window.__sm2Props, items = (pool) => (pool ? pool.items : []);
    const blades = items(Pr.P.blade).map((it, i) => {
      const bc = Pr.bladeSignCol[i] ?? null, sn = Math.sin(it.ry || 0), cs = Math.cos(it.ry || 0);
      const lc = bc ? [0.35 + 0.65 * bc[0], 0.35 + 0.65 * bc[1], 0.35 + 0.65 * bc[2]] : null;
      const hh = Math.abs(Math.floor(it.x * 3.7) * 73856093 ^ Math.floor(it.z * 5.3) * 19349663) >>> 0; // props.js bladeFaces atlas cell
      return { i, cell: hh % 64, x: h.r4(it.x), y: h.r4(it.y || 0), z: h.r4(it.z), ry: h.r4(it.ry || 0), hidden: !!it.hidden, board_linear: bc ? h.arr(bc) : null,
        light: { type: 'point', pos: [h.r4(it.x + 0.7 * sn), h.r4((it.y || 0) + 4.3), h.r4(it.z + 0.7 * cs)], color_linear: lc ? h.arr(lc) : null, intensity: Pr.bladeBlock.rec.intensity, range: Pr.bladeBlock.rec.range, radius: Pr.bladeBlock.rec.radius, volume: Pr.bladeBlock.rec.volume } };
    });
    const SB = Pr.signalBlock;
    const signals = Pr.signals.map((sg, i) => {
      const it = sg.it, cs = Math.cos(it.ry || 0), sn = Math.sin(it.ry || 0), lx = 0.45, lz = sg.mast ? 5.9 : 0, ly = sg.mast ? 5.1 : 3.4;
      return { i, axis: sg.axis, mast: !!sg.mast, map: !!sg.map, x: h.r4(it.x), y: h.r4(it.y || 0), z: h.r4(it.z), ry: h.r4(it.ry || 0), hidden: !!it.hidden,
        light: { type: 'spot', pos: [h.r4(it.x + lx * cs + lz * sn), h.r4((it.y || 0) + ly), h.r4(it.z - lx * sn + lz * cs)], dir: [h.r4(cs), -0.55, h.r4(-sn)],
          intensity: sg.mast ? 4.5 : 2.5, range: sg.mast ? 13 : 9, angle: SB.rec.angle, penumbra: SB.rec.penumbra, radius: SB.rec.radius, volume: SB.rec.volume, shadow: SB.rec.shadow,
          state_colours_hex: SB.SIG_COL, note: 'colour = SIG_COL[aState]: 0 red, 1 amber, 2 green (phase-driven at run time)' } };
    });
    const lamps = items(Pr.P.lamp).map(it => ({ x: h.r4(it.x), y: h.r4(it.y || 0), z: h.r4(it.z), ry: h.r4(it.ry || 0), s: h.r4(it.s ?? 1), sodium: it.extra?.aState === 1 }));
    return { blades, signals, lamps, blade_provider: h.plain({ BL_R: Pr.bladeBlock.BL_R, BL_N: Pr.bladeBlock.BL_N, rec: { ...Pr.bladeBlock.rec, color: undefined, pos: undefined }, WARM: Pr.bladeBlock.WARM }),
      signal_provider: h.plain({ SIG_R: SB.SIG_R, SIG_N: SB.SIG_N, SIG_COL: SB.SIG_COL, rec: { ...SB.rec, pos: undefined, dir: undefined } }) };
  });
  const neonDump = async (key, stride) => { // flat per-instance arrays, chunked
    const n = await page.evaluate((k) => window.__sm2Neon[k].length, key);
    const data = [];
    for (let a = 0; a < n; a += stride * 4000) data.push(...await page.evaluate(({ k, a, b }) => window.__sm2Neon[k].slice(a, b).map(v => Math.round(v * 1e4) / 1e4), { k: key, a, b: a + stride * 4000 }));
    return { stride, count: n / stride, data };
  };
  const tubes = await neonDump('tubes', 17);
  const words = await neonDump('words', 12);
  const neonExtra = await run((_, h) => { const N = window.__sm2Neon; return { NEON: h.plain(N.NEON), ASPECT: h.plain(N.ASPECT), W_: h.plain(N.W_), C_hex: h.plain(N.C), VENUES: h.plain(N.VENUES), stats: h.plain(N.stats) }; });
  const lighting = await run((_, h) => {
    const L = window.__ctx.lighting, num = (o) => h.plain(Object.fromEntries(Object.entries(o).filter(([, v]) => typeof v === 'number' || (Array.isArray(v) && v.every(x => typeof x === 'number')))));
    const v4 = (v) => (v ? [v.x, v.y, v.z, v.w].filter(x => x !== undefined).map(h.r4) : null);
    const A = L.amb, out = { tod: num(L.tod), tod_name: L.tod.name, nightHaze: { k: L.nightHaze.k, cfg: h.plain(L.nightHaze.cfg) }, city: h.plain(L.city), cityVol: h.plain(L.cityVol),
      fog: h.plain({ density: L.fog?.density, startDistance: L.fog?.startDistance, color: L.fog?.color, tint: L.fog?.tint, keys: Object.keys(L.fog || {}) }),
      sun: h.plain({ color: L.sun?.color, intensity: L.sun?.intensity, position: L.sun?.position }),
      amb: {} };
    for (const k of Object.keys(A)) { const v = A[k]; if (v && v.isVector4 || (v && v.isVector3)) out.amb[k] = v4(v); else if (v && v.value && (v.value.isVector4 || v.value.isVector3)) out.amb[k] = v4(v.value); else if (typeof v === 'number') out.amb[k] = h.r4(v); }
    out.cityLights = { gain: L.cityLights.gain, volume: L.cityLights.volume, ambient_gain: L.cityLights.ambient.gain, stats: h.plain({ lights: L.cityLights.stats.lights, cand: L.cityLights.stats.cand, maxCell: L.cityLights.stats.maxCell }) };
    return out;
  });
  const gate_exposure = lighting.tod.exposure;
  const clAmb = await run((_, h) => h.plain(window.__sm2CL.amb));
  const wlConsts = winMeta.WL;

  // ---------------------------------------------------------------- constants with source file:line (verbatim excerpts)
  const X = (name, file, re, n = 1, extra = {}) => ({ name, ...lineOf(file, re, n), ...extra });
  const constants = {
    NEON: X('NEON', 'src/world/neon.js', /^export const NEON = \{/, 10, { value: neonExtra.NEON }),
    NEON_ASPECT_W_C: [X('ASPECT', 'src/world/neon.js', /^const ASPECT = /), X('W_', 'src/world/neon.js', /^const W_ = /, 3), X('C (neon colours, sRGB hex)', 'src/world/neon.js', /^const C = \{/, 2)],
    SL: X('SL', 'src/world/screenlights.js', /^export const SL = \{/, 18, { value: screensExtra.SL }),
    SL_screen_shading: [X('uScrBoost/uScrDesat', 'src/world/screenlights.js', /^export const uScrBoost/, 1, { value: { uScrBoost: screensExtra.uScrBoost, uScrDesat: screensExtra.uScrDesat } }),
      X('uScrKnee/uScrTop', 'src/world/screenlights.js', /^export const uScrKnee/, 1, { value: { uScrKnee: screensExtra.uScrKnee, uScrTop: screensExtra.uScrTop } }),
      X('lightDrive', 'src/world/screenlights.js', /^const lightDrive/), X('lightColour', 'src/world/screenlights.js', /^function lightColour/, 5)],
    SHOP_LIGHT: X('SHOP_LIGHT', 'src/world/facade.js', /^export const SHOP_LIGHT = /, 1, { value: facadeExtra.shop_light }),
    WL: X('WL', 'src/world/facade.js', /^export const WL = /, 1, { value: wlConsts }),
    NFLOOD: X('NFLOOD', 'src/world/facade.js', /^const NFLOOD = /, 1, { value: facadeExtra.NFLOOD }),
    AMB: X('AMB_R / AMB_SOFT / AMB_GAIN', 'src/render/citylights.js', /^export const AMB_R/, 1, { value: { AMB_R: clAmb.AMB_R, AMB_SOFT: clAmb.AMB_SOFT, AMB_GAIN: clAmb.AMB_GAIN } }),
    CITY_LIGHT_GRID: X('CL_* grid constants', 'src/render/citylights.js', /^export const CL_CELL/, 1, { value: clAmb }),
    lighting_night: [
      X('night preset (elevation / moon / windows / env)', 'src/render/lighting.js', /^  night:\s+\{ elevation/),
      X('city street glow (ambShared.city source)', 'src/render/lighting.js', /^  const city = \{/),
      X('NH night haze', 'src/render/lighting.js', /^  const NH = \{/),
      X('night exposure x4.5', 'src/render/lighting.js', /tod\.exposure = L\.exposure \* lerp\(1, 4\.5, night\)/),
      X('night bloom', 'src/render/lighting.js', /tod\.bloom = 1 \+ 1\.6 \* night/),
      X('moon key colour', 'src/render/lighting.js', /key\.color\.setRGB\(T\[0\] \* E \* 0\.45/),
      X('moon key energy E', 'src/render/lighting.js', /const T = sunTransmittance\(mel, 1\.2\), E = /),
      X('ambient grade at night', 'src/render/lighting.js', /ambShared\.grade\.set\(/),
      X('city street glow applied', 'src/render/lighting.js', /ambShared\.city\.set\(/),
      X('night haze density / start', 'src/render/lighting.js', /fog\.density = fogBase\.density \* lerp\(L\.fog, NH\.fog, night\)/, 2),
      X('night sky zenith', 'src/render/lighting.js', /const nt = \[0\.066 \* moonK/),
      X('screenK', 'src/render/lighting.js', /screenK\.value = Math\.min\(1\.2/),
    ],
    lighting_runtime_at_night: lighting,
    street_lamp: {
      source: [X('street lamp lights (provider in buildProps)', 'src/world/props.js', /cityLights\.add\(\{ type: 'spot', pos: \[it\.x \+ 2\.9/, 3),
        X('sodium / LED mix + Times Square half power', 'src/world/props.js', /const h = Math\.abs\(Math\.sin\(it\.x \* 12\.9898/, 3),
        X('cobra head offset 2.9 m at 8.75 m', 'src/world/props.js', /anchor\(it, 0, 9\.15, 2\.9, 'lampTop'\)/)],
      note: 'light position = prop base + 2.9 m * scale along the prop heading (sin/cos of ry) at 8.75 m * scale; see statics cat street_lamp',
    },
    traffic_lights: {
      source: [X('CL_MAX/CL_R/CL_TAIL/CL_CAP', 'src/world/npc/traffic.js', /const CL_MAX = 50/), X('CL_TWIN/CL_TILT', 'src/world/npc/traffic.js', /const CL_TWIN = 30/),
        X('headlight record clH', 'src/world/npc/traffic.js', /const clH = \{ type: 'spot'/), X('tail light record clT', 'src/world/npc/traffic.js', /const clT = \{ type: 'point'/),
        X('headlight intensity / twin / lamp offsets', 'src/world/npc/traffic.js', /const I = c\.x > -112 && c\.x < 112/, 8),
        X('tail light offsets / brake intensity', 'src/world/npc/traffic.js', /if \(clD\[i\] < CL_TAIL \* CL_TAIL\)/, 7)],
      parameters: { headlight: { type: 'spot', color_hex: '0xffd8b0', intensity_per_lamp: { times_square_box: 14, elsewhere: 38 }, merged_single_lamp_factor: 2, range: 20, angle: 0.5, penumbra: 0.9, radius: 3.5, volume: 0.18, spec: 0, tilt_down_rad: 0.1,
          lamp_local: 'ahead of bumper: len/2 + 0.1 m, 0.72 m up, lateral +-max(0.5, width/2 - 0.25) for the CL_TWIN=30 nearest cars (twin), one centred merged lamp for the rest up to CL_MAX=50', shadow: 'key-based shadow slots (CL_SH_N=4 strongest spots)' },
        taillight: { type: 'point', color_hex: '0xff1c0c', intensity: { normal: 0.75, braking_or_hazard: 2 }, range: 4.5, radius: 0.2, volume: 0.04, shadow: false, local: 'rear: len/2 + 0.2 m behind, 0.85 m up, lateral +-max(0.5, width/2 - 0.2); only for cars within CL_TAIL=45 m' },
        times_square_box_xz: { x: [-112, 112], z: [-352, 22] } },
    },
    street_signals_and_blades: { signal_provider: props.signal_provider, blade_provider: props.blade_provider },
  };
  delete props.signal_provider; delete props.blade_provider;

  // ---------------------------------------------------------------- counts, summary
  const counts = {};
  const sum = {};
  for (const s of statics) {
    counts[s.cat] = (counts[s.cat] || 0) + 1;
    const e = sum[s.cat] ||= { count: 0, bbox: { min: [1e9, 1e9, 1e9], max: [-1e9, -1e9, -1e9] }, total_intensity: 0, total_lum_flux: 0 };
    e.count++; e.total_intensity += s.intensity; e.total_lum_flux += s.lum;
    for (let k = 0; k < 3; k++) { e.bbox.min[k] = Math.min(e.bbox.min[k], s.pos[k]); e.bbox.max[k] = Math.max(e.bbox.max[k], s.pos[k]); }
  }
  const bboxOf = (pts) => { const b = { min: [1e9, 1e9, 1e9], max: [-1e9, -1e9, -1e9] }; for (const p of pts) for (let k = 0; k < 3; k++) { b.min[k] = Math.min(b.min[k], p[k]); b.max[k] = Math.max(b.max[k], p[k]); } return b; };
  const extra = { window_rects: { count: winCounts.runs + winCounts.bands, pts: faces.flatMap(f => f.bands.flatMap(b => [b.band.rect.pos, ...b.runs.map(r => r.rect.pos)])) },
    board_whole: { count: boards.length, pts: boards.map(b => b.whole.pos) }, board_tiles: { count: boards.reduce((n, b) => n + b.tiles.length, 0), pts: boards.flatMap(b => b.tiles.map(t => t.pos)) },
    blades: { count: props.blades.length, pts: props.blades.map(b => b.light.pos) }, signals: { count: props.signals.length, pts: props.signals.map(s => s.light.pos) },
    neon_tubes: { count: tubes.count, pts: Array.from({ length: tubes.count }, (_, i) => tubes.data.slice(i * 17, i * 17 + 3)) },
    neon_words: { count: words.count, pts: Array.from({ length: words.count }, (_, i) => words.data.slice(i * 12, i * 12 + 3)) },
    crown_floods: { count: facadeExtra.crown_floods.length, pts: facadeExtra.crown_floods.map(f => [(f.box.x0 + f.box.x1) / 2, (f.y0 + f.y1) / 2, (f.box.z0 + f.box.z1) / 2]) } };
  for (const [k, v] of Object.entries(extra)) { counts[k] = v.count; sum[k] = { count: v.count, bbox: v.pts.length ? bboxOf(v.pts) : null }; }
  counts.statics_total = statics.length;
  const rnd = (o) => JSON.parse(JSON.stringify(o, (k, v) => (typeof v === 'number' ? Math.round(v * 1e3) / 1e3 : v)));

  result = {
    source: { repo: SPIDER, commit: PINNED, url: new URL('?shot=street&tod=night', base).pathname + '?shot=street&tod=night', exporter: 'tools/night/export_night.mjs', exported_at: new Date().toISOString() },
    frame: 'browser metres, +x east, +y up, -z north; UE cm = (x, z, y) * 100',
    gate, statics, windows: { WL: wlConsts, faces_total: winCounts.faces, counts: winCounts, faces: faces.filter(f => f.bands.length),
      note: 'faces without any lit band are omitted from `faces` (counted in faces_total). rect = the emitted city light of that run / 3-floor band exactly as facade.js rebuildWinCands->setRect computes it (near the camera the provider emits runs, farther away bands).' },
    shop_fronts: facadeExtra.shop_fronts, shop_light: facadeExtra.shop_light, crown_floods: { NFLOOD: facadeExtra.NFLOOD, floods: facadeExtra.crown_floods, bb: facadeExtra.flood_bb, y: facadeExtra.flood_y },
    boards: { SL: screensExtra.SL, boards }, blades: props.blades, signals: props.signals, lamps_props: props.lamps,
    neon: { tubes: { fields: ['ox', 'oy', 'oz', 'tx', 'ty', 'tz', 'vx', 'vy', 'vz', 'w', 'h', 'radius', 'sideMask', 'cr', 'cg', 'cb', 'ledFlag+seed'], ...tubes },
      words: { fields: ['cx', 'cy', 'cz', 'tx', 'tz', 'w', 'h', 'atlasCell', 'cr', 'cg', 'cb', 'seed'], ...words },
      constants: { NEON: neonExtra.NEON, ASPECT: neonExtra.ASPECT, W_: neonExtra.W_, C_hex: neonExtra.C_hex, VENUES: neonExtra.VENUES, stats: neonExtra.stats }, atlas: 'public/assets/city/tex/neon_words.webp' },
    constants, counts,
    screen_k: Math.min(1.2, 0.9 * 0.5 / Math.max(gate_exposure, 0.3)),
  };
  const summary = { source: result.source, counts, per_category: rnd(sum), notes: { total_intensity: 'sum of authored add() intensity (rects: radiance)', total_lum_flux: 'sum of record luminance (rects: radiance x area)' } };
  fs.writeFileSync(path.join(OUT, 'night_lights.json'), JSON.stringify(result));
  fs.writeFileSync(path.join(OUT, 'night_lights_summary.json'), JSON.stringify(summary, null, 1));
  log('wrote', path.join(OUT, 'night_lights.json'), (fs.statSync(path.join(OUT, 'night_lights.json')).size / 1e6).toFixed(1), 'MB');
  console.log(JSON.stringify(counts, null, 1));
  if (errs.length) console.log('page errors:', errs.slice(0, 5));
  await page.close();
} finally {
  await browser.close();
  await server.close();
}

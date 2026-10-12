// Browser-city exporter: builds the procedural city in headless Chrome (the real game code, this worktree's Vite dev
// server) and dumps a region of 256 m tiles as
//   <out>/mesh/<kind>/<name>__t<ix>_<iz>.glb   merged geometry per material class and tile (positions relative to the
//                                               tile centre, glTF frame = browser frame: metres, +x east, +y up, -z north)
//   <out>/proto/<pool>.glb                      instanced prop / tree prototypes (model space)
//   <out>/layout.json                           streets, blocks, footprints, building boxes, zip points, prop + tree
//                                               instances (pool items), browser viewpoints
//   <out>/collision.json                        collision primitives (BOX / CYL / RAMP / HF + height fields)
//   <out>/manifest.json                         every GLB with its tile centre and UV-channel packing
// Vertex-attribute packing (glTF TEXCOORD_n = UE UV channel n, COLOR_0 = UE vertex colour):
//   facade   UV0 uv | UV1 aF.xy | UV2 aF.zw | UV3 aS.xy | UV4 aS.zw | UV5 aW.xy | UV6 aW.zw |
//            UV7 (resid + 2*lintel + 16*glass, depth) | COLOR tint / 2
//   detail   UV0 uv | UV1 (aPart, 0) | COLOR color
//   roofs    UV0 uv | UV1 aM.xy | UV2 aM.zw | UV3 aE.xy | UV4 aE.zw | COLOR color
//   asphalt  UV0 aRoad.xy | UV1 (aRoad.z, 0)
//   sidewalk UV0 aRect.xy | UV1 aRect.zw
//   other    UV0 uv (or 0) | COLOR color (if any) | further attributes packed two floats per UV channel (see manifest)
// UE import (Interchange glTF): UE = (x, z, y) * 100 cm -> X east, Y south (north = -Y), Z up; see docs/night1/city/EXPORT.md
//
// usage: node tools/export/export_city.mjs [--tiles ix0,iz0,ix1,iz1] [--out dir] [--url http://127.0.0.1:<SM2_CITY_PORT, default 5202>/]
//          [--measure] [--nofar] [--lodtiles ix0,iz0,ix1,iz1]
// (island r01) --measure: nothing but <out>/measure.json is written (per tile: meshes, verts, tris, GLB bytes; JSON bytes; timings), so a
//   district / the whole island can be sized without the disk. --nofar: no far field (far shores, land polygons, hinterland, far-ring facadeLod
//   masses, ez-tree LOD1 outside the region) -- a district export that another pass supplies the far layer for.
import { chromium } from 'playwright-core';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const [tx0, tz0, tx1, tz1] = arg('tiles', '-1,-2,1,0').split(',').map(Number); // inclusive tile index range
const SCRATCH = process.env.SM2_CITY_SCRATCH || '/Users/midir/sm2-n1/_scratch/city';   // (r07) parameterised: SM2_CITY_SCRATCH, SM2_CITY_PORT
const OUT = path.resolve(arg('out', process.env.SM2_CITY_EXPORT || path.join(SCRATCH, 'export', 'midtown3x3')));
const URL0 = arg('url', `http://127.0.0.1:${process.env.SM2_CITY_PORT || '5202'}/`);
const PROFILE = arg('profile', path.join(SCRATCH, 'chrome-profile'));
const MEASURE = process.argv.includes('--measure'), NOFAR = process.argv.includes('--nofar');
const T = 256;
const region = { x0: tx0 * T, z0: tz0 * T, x1: (tx1 + 1) * T, z1: (tz1 + 1) * T };
const [lx0, lz0, lx1, lz1] = arg('lodtiles', '-4,-14,3,13').split(',').map(Number); // far ring (facade LOD masses)
const lodRegion = { x0: lx0 * T, z0: lz0 * T, x1: (lx1 + 1) * T, z1: (lz1 + 1) * T };
fs.mkdirSync(OUT, { recursive: true });

// ------------------------------------------------------------------ GLB writer
function packAttrs(kind, A, n) {
  const uv = [], z2 = () => new Float32Array(n * 2);
  const pair = (a, i0, k) => { const o = new Float32Array(n * 2); for (let v = 0; v < n; v++) { o[v * 2] = a[v * k + i0]; o[v * 2 + 1] = i0 + 1 < k ? a[v * k + i0 + 1] : 0; } return o; };
  const one = (a, i, k) => { const o = new Float32Array(n * 2); for (let v = 0; v < n; v++) o[v * 2] = a[v * k + i]; return o; };
  let color = null, colorNote = null; const chan = [];
  const put = (arr, what) => { uv.push(arr); chan.push(what); };
  if (kind === 'facade') {
    put(A.uv?.data ?? z2(), 'uv');
    put(pair(A.aF.data, 0, 4), 'aF.xy'); put(pair(A.aF.data, 2, 4), 'aF.zw');
    put(pair(A.aS.data, 0, 4), 'aS.xy'); put(pair(A.aS.data, 2, 4), 'aS.zw');
    put(pair(A.aW.data, 0, 4), 'aW.xy'); put(pair(A.aW.data, 2, 4), 'aW.zw');
    const x = A.aX.data, o = new Float32Array(n * 2);
    for (let v = 0; v < n; v++) { o[v * 2] = (x[v * 4] > 0.5 ? 1 : 0) + 2 * Math.round(x[v * 4 + 1]) + 16 * Math.round(x[v * 4 + 2]); o[v * 2 + 1] = x[v * 4 + 3]; }
    put(o, 'resid+2*lintel+16*glass, depth');
    const t = A.aTint.data; color = new Float32Array(n * 4);
    for (let v = 0; v < n; v++) { color[v * 4] = t[v * 3] / 2; color[v * 4 + 1] = t[v * 3 + 1] / 2; color[v * 4 + 2] = t[v * 3 + 2] / 2; color[v * 4 + 3] = 1; }
    return { uv, chan, color, colorNote: 'tint/2' };
  }
  if (kind === 'asphalt') { put(pair(A.aRoad.data, 0, 3), 'aRoad.xy'); put(one(A.aRoad.data, 2, 3), 'aRoad.z'); return { uv, chan, color }; }
  if (kind === 'sidewalk') { put(pair(A.aRect.data, 0, 4), 'aRect.xy'); put(pair(A.aRect.data, 2, 4), 'aRect.zw'); return { uv, chan, color }; }
  put(A.uv?.data ?? z2(), A.uv ? 'uv' : 'zero');
  const skip = new Set(['position', 'normal', 'uv', 'color', 'tangent']);
  for (const [k, a] of Object.entries(A)) {
    if (skip.has(k)) continue;
    for (let i = 0; i < a.k; i += 2) { if (uv.length >= 8) break; put(pair(a.data, i, a.k), `${k}.${'xyzw'.slice(i, Math.min(a.k, i + 2))}`); }
  }
  if (A.color) {
    const c = A.color.data, k = A.color.k; color = new Float32Array(n * 4);
    // (r06) farshore.js mass meshes encode a per-vertex window flag in colour.b (+10 window walls, +20 glass towers): the clamp below destroyed it
    // (all far-shore masses came out saturated blue). Decode: flag 0 / 1 / 2 -> vertex alpha 0 / 0.5 / 1, blue restored.
    let flagged = false; for (let v = 0; v < n && !flagged; v++) if (c[v * k + 2] > 5) flagged = true;
    for (let v = 0; v < n; v++) {
      let b = c[v * k + 2], flag = 0; if (flagged) { flag = b > 15 ? 2 : b > 5 ? 1 : 0; b -= flag === 2 ? 20 : flag === 1 ? 10 : 0; }
      color[v * 4] = Math.min(1, Math.max(0, c[v * k])); color[v * 4 + 1] = Math.min(1, Math.max(0, c[v * k + 1])); color[v * 4 + 2] = Math.min(1, Math.max(0, b));
      color[v * 4 + 3] = flagged ? flag / 2 : (k > 3 ? c[v * k + 3] : 1);
    }
    if (flagged) colorNote = 'alpha = window flag (0 none, 0.5 windows, 1 glass)';
  }
  return { uv, chan, color, colorNote };
}

function writeGLB(file, name, kind, A, index, dry = false) {
  const n = A.position.k ? A.position.data.length / 3 : 0;
  const pk = packAttrs(kind, A, n);
  const views = [], accessors = [], chunks = []; let off = 0;
  const addView = (arr, target) => { const b = Buffer.from(arr.buffer, arr.byteOffset, arr.byteLength); const pad = (4 - (b.length % 4)) % 4; views.push({ buffer: 0, byteOffset: off, byteLength: b.length, ...(target ? { target } : {}) }); chunks.push(b); if (pad) chunks.push(Buffer.alloc(pad)); off += b.length + pad; return views.length - 1; };
  const addAcc = (arr, type, comp, count, extra = {}) => { accessors.push({ bufferView: addView(arr, comp === 5125 ? 34963 : 34962), componentType: comp, count, type, ...extra }); return accessors.length - 1; };
  const P = A.position.data, mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < n; i++) for (let j = 0; j < 3; j++) { const v = P[i * 3 + j]; if (v < mn[j]) mn[j] = v; if (v > mx[j]) mx[j] = v; }
  const attributes = { POSITION: addAcc(P, 'VEC3', 5126, n, { min: mn, max: mx }) };
  if (A.normal) {
    const N = A.normal.data; for (let i = 0; i < n; i++) { const x = N[i * 3], y = N[i * 3 + 1], z = N[i * 3 + 2], L = Math.hypot(x, y, z); if (L > 1e-6) { N[i * 3] = x / L; N[i * 3 + 1] = y / L; N[i * 3 + 2] = z / L; } else { N[i * 3 + 1] = 1; } }
    attributes.NORMAL = addAcc(N, 'VEC3', 5126, n);
  }
  pk.uv.forEach((u, i) => { for (let j = 0; j < u.length; j++) if (!Number.isFinite(u[j])) u[j] = 0; attributes['TEXCOORD_' + i] = addAcc(u, 'VEC2', 5126, n); });
  if (pk.color) attributes.COLOR_0 = addAcc(pk.color, 'VEC4', 5126, n);
  const indices = addAcc(index, 'SCALAR', 5125, index.length);
  const json = { asset: { version: '2.0', generator: 'sm2 city exporter (tools/export)' }, scene: 0, scenes: [{ nodes: [0] }],
    nodes: [{ mesh: 0, name }], meshes: [{ name, primitives: [{ attributes, indices, material: 0 }] }],
    materials: [{ name: 'M_' + kind, pbrMetallicRoughness: { baseColorFactor: [1, 1, 1, 1], metallicFactor: 0, roughnessFactor: 0.8 } }],
    accessors, bufferViews: views, buffers: [{ byteLength: off }] };
  const js = Buffer.from(JSON.stringify(json)); const jpad = (4 - (js.length % 4)) % 4;
  const jsonChunk = Buffer.concat([js, Buffer.alloc(jpad, 0x20)]), bin = Buffer.concat(chunks);
  const hdr = Buffer.alloc(12); hdr.writeUInt32LE(0x46546c67, 0); hdr.writeUInt32LE(2, 4); hdr.writeUInt32LE(12 + 8 + jsonChunk.length + 8 + bin.length, 8);
  const ch = (len, type) => { const b = Buffer.alloc(8); b.writeUInt32LE(len, 0); b.writeUInt32LE(type, 4); return b; };
  const bytes = 12 + 8 + jsonChunk.length + 8 + bin.length;
  if (!dry) {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, Buffer.concat([hdr, ch(jsonChunk.length, 0x4e4f534a), jsonChunk, ch(bin.length, 0x004e4942), bin]));
  }
  return { verts: n, tris: index.length / 3, bytes, uv: pk.chan, color: !!pk.color, colorNote: pk.colorNote ?? null };
}

// ------------------------------------------------------------------ receiver
const manifest = { region, tiles: [tx0, tz0, tx1, tz1], created: new Date().toISOString(), transform: 'UE = (x, z, y) * 100', meshes: [], protos: [] };
const USED = new Set();
const JSON_BYTES = {};
const TIMES = { start: Date.now() };
function handle(buf) {
  const hl = buf.readUInt32LE(0), header = JSON.parse(buf.subarray(4, 4 + hl).toString());
  if (header.type === 'json') {
    const js = JSON.stringify(header.data); JSON_BYTES[header.file] = js.length;
    if (header.file === 'collision.json') JSON_BYTES.collision_solids = header.data.solids.length;
    if (!MEASURE) { fs.writeFileSync(path.join(OUT, header.file), js); console.log('wrote', header.file); }
    return;
  }
  let o = 4 + hl; const A = {};
  for (const [k, a] of Object.entries(header.attrs)) { const len = a.n * a.k * 4; const ab = new ArrayBuffer(len); new Uint8Array(ab).set(buf.subarray(o, o + len)); A[k] = { k: a.k, data: new Float32Array(ab) }; o += len; }
  const il = header.nIndex * 4, ib = new ArrayBuffer(il); new Uint8Array(ib).set(buf.subarray(o, o + il)); const index = new Uint32Array(ib);
  let rel = header.proto ? path.join('proto', header.name + '.glb') : path.join('mesh', header.kind, `${header.name}__t${header.tile[0]}_${header.tile[1]}.glb`);
  const rel0 = rel.slice(0, -4); for (let k = 2; USED.has(rel); k++) rel = rel0 + '_n' + k + '.glb'; // same-named meshes in one tile
  USED.add(rel);
  const info = writeGLB(path.join(OUT, rel), path.basename(rel, '.glb'), header.kind, A, index, MEASURE);
  const rec = { file: rel, name: header.name, src: header.src, kind: header.kind, tile: header.tile, center: header.center, mat: header.mat, attrs: Object.keys(header.attrs), ...info };
  (header.proto ? manifest.protos : manifest.meshes).push(rec);
}
const server = http.createServer((req, res) => {
  const bufs = []; req.on('data', d => bufs.push(d));
  req.on('end', () => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    try { if (req.method === 'POST') handle(Buffer.concat(bufs)); res.end('ok'); } catch (e) { console.error(e); res.statusCode = 500; res.end(String(e)); }
  });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const recvURL = `http://127.0.0.1:${server.address().port}/put?x=1`;

// ------------------------------------------------------------------ browser
const ctx = await chromium.launchPersistentContext(PROFILE, { channel: 'chrome', headless: true, viewport: { width: 640, height: 360 },
  args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--js-flags=--max-old-space-size=12000'] });
try {
  const page = await ctx.newPage();
  page.on('pageerror', e => console.log('pageerror:', e.message));
  const t0 = Date.now();
  await page.goto(new URL('?shot=street', URL0).href);
  await page.waitForFunction(() => window.__shotReady === true, null, { timeout: 600000 });
  console.log(`city ready in ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  // register every distance Pool (props, trees): hook the per-frame calls, then advance a few frames
  await page.evaluate(async () => {
    const { Pool } = await import('/src/world/pool.js');
    window.__pools = new Set();
    for (const k of ['thresh', 'update', 'due', 'upload']) { const f = Pool.prototype[k]; if (!f) continue; Pool.prototype[k] = function (...a) { window.__pools.add(this); return f.apply(this, a); }; }
    const c = window.__ctx;
    for (let i = 0; i < 4; i++) { c.world.update(1 / 60, c.camera); await new Promise(r => setTimeout(r, 50)); } // drives props / trees / pools once
    await new Promise(r => setTimeout(r, 1500));
    return window.__pools.size;
  }).then(n => console.log('pools registered:', n));
  await page.addScriptTag({ content: fs.readFileSync(path.join(HERE, 'collect_page.js'), 'utf8') });
  TIMES.ready = Date.now();
  const res = await page.evaluate(o => window.__cityExport(o), { region, lodRegion: NOFAR ? null : lodRegion, farRegion: NOFAR ? null : { x0: -30000, z0: -30000, x1: 30000, z1: 30000 }, url: recvURL });
  TIMES.collected = Date.now();
  console.log(JSON.stringify(res.log), 'pools with instances in region:', res.nInstances);
  manifest.stats = res.stats;
  // (r06) the baked far-land ground map (farshore.js CanvasTexture: land / lot colours, waterfront aprons, parks): far-shore land meshes carry only UV0 into it
  const png = await page.evaluate(() => { let out = null; window.__ctx.scene.traverse(o => { if (!out && o.isMesh && /^farLand-/.test(o.name) && o.material?.map?.image?.toDataURL) out = o.material.map.image.toDataURL('image/png'); }); return out; });
  if (png && !MEASURE) { fs.writeFileSync(path.join(OUT, 'farland_map.png'), Buffer.from(png.split(',')[1], 'base64')); console.log('wrote farland_map.png'); }
  else console.log('WARN: far-land map canvas not found');
} finally {
  await ctx.close();
  if (!MEASURE) fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(manifest, null, 1));
  TIMES.end = Date.now();
  {
    // (island r01) per-tile sizing (also written for a real export): meshes / verts / tris / GLB bytes per tile and kind, JSON bytes, timings
    const per = {}, kinds = {};
    for (const m of manifest.meshes) {
      const k = (m.tile || ['?']).join(','), t = (per[k] ||= { meshes: 0, verts: 0, tris: 0, bytes: 0, lodTris: 0 });
      t.meshes++; t.verts += m.verts; t.tris += m.tris; t.bytes += m.bytes || 0; if (/lod/i.test(m.name) || m.kind === 'far' || m.kind === 'land') t.lodTris += m.tris;
      const q = (kinds[m.kind] ||= { meshes: 0, tris: 0, bytes: 0 }); q.meshes++; q.tris += m.tris; q.bytes += m.bytes || 0;
    }
    const sum = (f) => manifest.meshes.reduce((a, m) => a + (f(m) || 0), 0);
    const meas = { tiles: [tx0, tz0, tx1, tz1], region, measure: MEASURE, nofar: NOFAR, created: manifest.created,
      seconds: { city_ready: (TIMES.ready - TIMES.start) / 1000, collect: (TIMES.collected - TIMES.ready) / 1000, total: (TIMES.end - TIMES.start) / 1000 },
      totals: { meshes: manifest.meshes.length, protos: manifest.protos.length, verts: sum(m => m.verts), tris: sum(m => m.tris), glb_bytes: sum(m => m.bytes),
        proto_bytes: manifest.protos.reduce((a, m) => a + (m.bytes || 0), 0), json_bytes: Object.entries(JSON_BYTES).filter(([k]) => k.endsWith('.json')).reduce((a, [, v]) => a + v, 0) },
      json: JSON_BYTES, kinds, per_tile: per };
    fs.mkdirSync(OUT, { recursive: true }); fs.writeFileSync(path.join(OUT, 'measure.json'), JSON.stringify(meas, null, 1));
    console.log('measure:', JSON.stringify(meas.totals), JSON.stringify(meas.seconds));
  }
  server.close();
}
const tot = manifest.meshes.reduce((a, m) => { a.v += m.verts; a.t += m.tris; return a; }, { v: 0, t: 0 });
console.log(`exported ${manifest.meshes.length} tile meshes (${tot.v} verts, ${tot.t} tris), ${manifest.protos.length} prototypes -> ${OUT}`);

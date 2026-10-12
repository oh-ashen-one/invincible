// Terrain exporter (piece E): builds the procedural browser city in headless Chrome (the real game code, this worktree's Vite dev server) and dumps the
// TERRAIN kinds island-wide (no tile clipping): park ground / lawns / paths / ponds / Reservoir / park furniture / shore details (collect_terrain.js),
//   <out>/mesh/<group>/<name>.glb   world-space meshes (metres, glTF frame = browser frame), UV0 = uv, further attributes packed two floats per UV channel, COLOR_0 = colour
//   <out>/proto/<name>.glb          instanced prop prototypes (model space)
//   <out>/terrain.json              layout / shader parameters (meadows, ponds, GY heights, shoreline polygon, instance lists, stats)
//   <out>/parkmask.rgba             the grass mask (1 m texels RGBA8, size in terrain.json)
//   <out>/manifest.json             every GLB with its group and material info
// Separate from tools/export/export_city.mjs (piece A owns that): this script only ADDS kinds. UE side: unreal/WebHomage/Scripts/build_terrain.py.
// usage: node tools/export/export_terrain.mjs [--out dir] [--url http://127.0.0.1:<SM2_TERRAIN_PORT, default 5209>/]
import { chromium } from 'playwright-core';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const SCRATCH = process.env.SM2_TERRAIN_SCRATCH || '/Users/midir/sm2-n1/_scratch/terrain';
const OUT = path.resolve(arg('out', process.env.SM2_TERRAIN_EXPORT || path.join(SCRATCH, 'export')));
const URL0 = arg('url', `http://127.0.0.1:${process.env.SM2_TERRAIN_PORT || '5209'}/`);
const PROFILE = arg('profile', path.join(SCRATCH, 'chrome-profile'));
fs.mkdirSync(OUT, { recursive: true });
// stale output of an earlier export must not leak into the build: clear only our own mesh / proto folders, and only inside the sm2-n1 sandbox
if (!OUT.startsWith('/Users/midir/sm2-n1/')) throw new Error('refusing to export outside /Users/midir/sm2-n1: ' + OUT);
for (const d of ['mesh', 'proto']) fs.rmSync(path.join(OUT, d), { recursive: true, force: true });

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

function writeGLB(file, name, kind, A, index) {
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
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, Buffer.concat([hdr, ch(jsonChunk.length, 0x4e4f534a), jsonChunk, ch(bin.length, 0x004e4942), bin]));
  return { verts: n, tris: index.length / 3, uv: pk.chan, color: !!pk.color, colorNote: pk.colorNote ?? null };
}

// ------------------------------------------------------------------ receiver
const manifest = { created: new Date().toISOString(), transform: 'UE = (x, z, y) * 100', meshes: [], protos: [] };
const USED = new Set();
function handle(buf) {
  const hl = buf.readUInt32LE(0), header = JSON.parse(buf.subarray(4, 4 + hl).toString());
  if (header.type === 'json') { fs.writeFileSync(path.join(OUT, header.file), JSON.stringify(header.data)); console.log('wrote', header.file); return; }
  if (header.type === 'bin') { fs.writeFileSync(path.join(OUT, header.file), buf.subarray(4 + hl)); console.log('wrote', header.file, buf.length - 4 - hl, 'bytes'); return; }
  let o = 4 + hl; const A = {};
  for (const [k, a] of Object.entries(header.attrs)) { const len = a.n * a.k * 4; const ab = new ArrayBuffer(len); new Uint8Array(ab).set(buf.subarray(o, o + len)); A[k] = { k: a.k, data: new Float32Array(ab) }; o += len; }
  const il = header.nIndex * 4, ib = new ArrayBuffer(il); new Uint8Array(ib).set(buf.subarray(o, o + il)); const index = new Uint32Array(ib);
  let rel = header.proto ? path.join('proto', header.name + '.glb') : path.join('mesh', header.kind, header.name + '.glb');
  const rel0 = rel.slice(0, -4); for (let k = 2; USED.has(rel); k++) rel = rel0 + '_n' + k + '.glb';
  USED.add(rel);
  const info = writeGLB(path.join(OUT, rel), path.basename(rel, '.glb'), header.kind, A, index);
  const rec = { file: rel, name: path.basename(rel, '.glb'), src: header.src, kind: header.kind, mat: header.mat, attrs: Object.keys(header.attrs), ...info };
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
  await page.goto(new URL('?shot=parkHigh', URL0).href);
  await page.waitForFunction(() => window.__shotReady === true, null, { timeout: 600000 });
  console.log(`city ready in ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  // register every distance Pool (props, trees): hook the per-frame calls, then advance a few frames (same trick as export_city.mjs)
  await page.evaluate(async () => {
    const { Pool } = await import('/src/world/pool.js');
    window.__pools = new Set();
    for (const k of ['thresh', 'update', 'due', 'upload']) { const f = Pool.prototype[k]; if (!f) continue; Pool.prototype[k] = function (...a) { window.__pools.add(this); return f.apply(this, a); }; }
    const c = window.__ctx;
    for (let i = 0; i < 4; i++) { c.world.update(1 / 60, c.camera); await new Promise(r => setTimeout(r, 50)); }
    await new Promise(r => setTimeout(r, 1500));
  });
  await page.addScriptTag({ content: fs.readFileSync(path.join(HERE, 'collect_terrain.js'), 'utf8') });
  const res = await page.evaluate(o => window.__terrainExport(o), { url: recvURL });
  console.log(JSON.stringify(res));
  manifest.stats = res.stats;
} finally {
  await ctx.close();
  fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(manifest, null, 1));
  server.close();
}
const tot = manifest.meshes.reduce((a, m) => { a.v += m.verts; a.t += m.tris; return a; }, { v: 0, t: 0 });
console.log(`exported ${manifest.meshes.length} meshes (${tot.v} verts, ${tot.t} tris), ${manifest.protos.length} prototypes -> ${OUT}`);

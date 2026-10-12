// In-page collector for the browser city (runs inside the Vite dev page, after the city is built).
// Installed by tools/export/export_city.mjs via page.addScriptTag; exposes window.__cityExport(opts).
// Everything stays in browser units: metres, +x east, +y up, -z north (three.js / glTF convention).
// Parts are POSTed as binary blobs to the node receiver: [u32 headerLen][header JSON][attr buffers...][index u32].
(() => {
  const SKIP = /(^|\b)(WebStrands|SlingWebs|facadeLod|super|upload|roofAO|roofStreaks|people-|citizen-|SpiderMan|WebRopes|veh-|highwayVeh|pigeons|gulls|boats|boatWakes|waterSpray|steam|coast|far|hinterland|horizon|palisades|riverBed|river|water|Water|sky|Sky|dog-|carContactAO|carHeadlightPools|propContactAO|lampPool|coastLampPools|park-canopy-shade|bridge|reservoir|park-|parkReeds|parkPaths|parkLampPool|mapLawns|wetBands|seawall)/;
  // per-tile building classes (one mesh per 256 m tile, keep whole tiles)
  const TILE_RE = /^(facade|detail|roofs|signage) (\d+)$/;

  const T = 256;
  const FAR_RE = /^(parkPaths$|farCity|farCityRoofs|farCityMass|farBulkheads|farLand-|coast-|horizonSkirt|palisadesCliff|bridge(Stone|Steel|Cables|Deck|Truss)$|seawall|mapLawns)/;
  const tileOf = (x, z) => [Math.floor(x / T), Math.floor(z / T)];

  function kindOf(name, g) {
    if (g.attributes.aF && g.attributes.aS) return 'facade';
    if (/^detail /.test(name) || /^grandCentral$|^metlifeFins$/.test(name)) return 'detail';
    if (/^roofs /.test(name)) return 'roofs';
    if (name === 'asphalt') return 'asphalt';
    if (name === 'sidewalks') return 'sidewalk';
    if (name === 'markings') return 'markings';
    if (/^signage/.test(name)) return 'signage';
    return 'generic';
  }

  // copy one vertex attribute (possibly interleaved / normalized) into a Float32Array
  function attrArray(a) {
    const n = a.count, k = a.itemSize, out = new Float32Array(n * k);
    if (!a.isInterleavedBufferAttribute && a.array instanceof Float32Array && !a.normalized) { out.set(a.array.subarray(0, n * k)); return out; }
    for (let i = 0; i < n; i++) for (let j = 0; j < k; j++) out[i * k + j] = a.getComponent ? a.getComponent(i, j) : [a.getX(i), a.getY(i), a.getZ(i), a.getW(i)][j];
    return out;
  }

  // triangles of mesh m (world space), grouped by the tile of their centroid (or all into `forceTile`)
  function splitMesh(m, region, forceTile, T = 256) {
    const g = m.geometry, pos = g.attributes.position; if (!pos || pos.count === 0) return [];
    m.updateMatrixWorld(true);
    const M = m.matrixWorld.elements, ident = m.matrixWorld.equals(new m.matrixWorld.constructor());
    const idx = g.index ? g.index.array : null;
    const start = g.drawRange.start, cnt = Math.min(g.drawRange.count, (idx ? idx.length : pos.count) - start);
    const P = attrArray(pos);
    const wx = new Float32Array(pos.count), wy = new Float32Array(pos.count), wz = new Float32Array(pos.count);
    for (let i = 0; i < pos.count; i++) {
      const x = P[i * 3], y = P[i * 3 + 1], z = P[i * 3 + 2];
      if (ident) { wx[i] = x; wy[i] = y; wz[i] = z; }
      else { wx[i] = M[0] * x + M[4] * y + M[8] * z + M[12]; wy[i] = M[1] * x + M[5] * y + M[9] * z + M[13]; wz[i] = M[2] * x + M[6] * y + M[10] * z + M[14]; }
    }
    // triangles grouped per tile; big triangles (road / sidewalk strips spanning many tiles) are clipped to each tile
    // square (Sutherland-Hodgman in xz); clipped vertices carry barycentric weights so every attribute interpolates
    const groups = new Map(); // key -> { vk: Map(vertexKey -> out index), vs: [[a,b,c,wa,wb,wc] | a], I: [] }
    const grp = (key) => { let G = groups.get(key); if (!G) groups.set(key, (G = { vk: new Map(), vs: [], I: [] })); return G; };
    const vert = (G, v) => { const k = typeof v === 'number' ? v : v.map(x => (Math.round(x * 1e5) / 1e5)).join(':'); let r = G.vk.get(k); if (r === undefined) { r = G.vs.length; G.vk.set(k, r); G.vs.push(v); } return r; };
    const clipPoly = (poly, axis, val, keepLess) => { // poly: [{x,z,w:[a,b,c,wa,wb,wc]}]
      const out = [];
      for (let i = 0; i < poly.length; i++) {
        const A = poly[i], B = poly[(i + 1) % poly.length], a = A[axis] - val, b = B[axis] - val;
        const inA = keepLess ? a <= 0 : a >= 0, inB = keepLess ? b <= 0 : b >= 0;
        if (inA) out.push(A);
        if (inA !== inB) { const t = a / (a - b); out.push({ x: A.x + (B.x - A.x) * t, z: A.z + (B.z - A.z) * t, w: A.w.map((q, j) => j < 3 ? q : q + (B.w[j] - q) * t) }); }
      }
      return out;
    };
    for (let t = start; t + 2 < start + cnt; t += 3) {
      const a = idx ? idx[t] : t, b = idx ? idx[t + 1] : t + 1, c = idx ? idx[t + 2] : t + 2;
      if (forceTile) { const G = grp(forceTile); G.I.push(vert(G, a), vert(G, b), vert(G, c)); continue; }
      const mnx = Math.min(wx[a], wx[b], wx[c]), mxx = Math.max(wx[a], wx[b], wx[c]), mnz = Math.min(wz[a], wz[b], wz[c]), mxz = Math.max(wz[a], wz[b], wz[c]);
      if (mxx < region.x0 || mnx >= region.x1 || mxz < region.z0 || mnz >= region.z1) continue;
      const i0 = Math.floor(mnx / T), i1 = Math.floor(mxx / T), j0 = Math.floor(mnz / T), j1 = Math.floor(mxz / T);
      if (i0 === i1 && j0 === j1) { // inside one tile: keep as is
        if (mnx < region.x0 || mxx > region.x1 || mnz < region.z0 || mxz > region.z1) continue;
        const G = grp(i0 + ',' + j0); G.I.push(vert(G, a), vert(G, b), vert(G, c)); continue;
      }
      const tri = [{ x: wx[a], z: wz[a], w: [a, b, c, 1, 0, 0] }, { x: wx[b], z: wz[b], w: [a, b, c, 0, 1, 0] }, { x: wx[c], z: wz[c], w: [a, b, c, 0, 0, 1] }];
      for (let i = Math.max(i0, Math.floor(region.x0 / T)); i <= Math.min(i1, Math.floor((region.x1 - 1) / T)); i++)
        for (let j = Math.max(j0, Math.floor(region.z0 / T)); j <= Math.min(j1, Math.floor((region.z1 - 1) / T)); j++) {
          let P = clipPoly(tri, 'x', i * T, false); if (P.length < 3) continue;
          P = clipPoly(P, 'x', (i + 1) * T, true); if (P.length < 3) continue;
          P = clipPoly(P, 'z', j * T, false); if (P.length < 3) continue;
          P = clipPoly(P, 'z', (j + 1) * T, true); if (P.length < 3) continue;
          const G = grp(i + ',' + j), ids = P.map(p => vert(G, p.w[3] === 1 ? a : p.w[4] === 1 ? b : p.w[5] === 1 ? c : p.w));
          for (let k = 1; k + 1 < ids.length; k++) G.I.push(ids[0], ids[k], ids[k + 1]);
        }
    }
    const out = [];
    const names = Object.keys(g.attributes).filter(k => k !== 'position' && !(g.attributes[k].isInstancedBufferAttribute));
    const arrs = Object.fromEntries(names.map(k => [k, attrArray(g.attributes[k])]));
    const nm = new Float32Array(9); nm.set([M[0], M[1], M[2], M[4], M[5], M[6], M[8], M[9], M[10]]);
    const lerpV = (src, s, v, j) => typeof v === 'number' ? src[v * s + j] : src[v[0] * s + j] * v[3] + src[v[1] * s + j] * v[4] + src[v[2] * s + j] * v[5];
    for (const [key, G] of groups) {
      const [ix, iz] = key.split(',').map(Number), cx = (ix + 0.5) * T, cz = (iz + 0.5) * T;
      const order = G.vs, I = Uint32Array.from(G.I);
      const nv = order.length, pos3 = new Float32Array(nv * 3);
      const W = [wx, wy, wz];
      for (let i = 0; i < nv; i++) for (let j = 0; j < 3; j++) { const v = order[i]; pos3[i * 3 + j] = (typeof v === 'number' ? W[j][v] : W[j][v[0]] * v[3] + W[j][v[1]] * v[4] + W[j][v[2]] * v[5]) - (j === 0 ? cx : j === 2 ? cz : 0); }
      const attrs = { position: { k: 3, data: pos3 } };
      for (const k of names) {
        const s = g.attributes[k].itemSize, src = arrs[k], d = new Float32Array(nv * s);
        for (let i = 0; i < nv; i++) for (let j = 0; j < s; j++) d[i * s + j] = lerpV(src, s, order[i], j);
        if (k === 'normal' && !ident) for (let i = 0; i < nv; i++) {
          const x = d[i * 3], y = d[i * 3 + 1], z = d[i * 3 + 2];
          const X = nm[0] * x + nm[3] * y + nm[6] * z, Y = nm[1] * x + nm[4] * y + nm[7] * z, Z = nm[2] * x + nm[5] * y + nm[8] * z, L = Math.hypot(X, Y, Z) || 1;
          d[i * 3] = X / L; d[i * 3 + 1] = Y / L; d[i * 3 + 2] = Z / L;
        }
        attrs[k] = { k: s, data: d };
      }
      out.push({ tile: [ix, iz], center: [cx, 0, cz], attrs, index: I });
    }
    return out;
  }

  async function post(url, header, buffers) {
    const hj = new TextEncoder().encode(JSON.stringify(header));
    const pad = (4 - (hj.length % 4)) % 4;
    let total = 4 + hj.length + pad; for (const b of buffers) total += b.byteLength;
    const out = new Uint8Array(total), dv = new DataView(out.buffer);
    dv.setUint32(0, hj.length + pad, true); out.set(hj, 4); out.fill(32, 4 + hj.length, 4 + hj.length + pad);
    let o = 4 + hj.length + pad; for (const b of buffers) { out.set(new Uint8Array(b.buffer, b.byteOffset, b.byteLength), o); o += b.byteLength; }
    const r = await fetch(url, { method: 'POST', body: out.buffer });
    if (!r.ok) throw new Error('post failed ' + r.status);
  }
  async function postPart(url, name, kind, p, extra = {}) {
    const header = { type: 'mesh', name, kind, tile: p.tile, center: p.center, attrs: {}, nIndex: p.index.length, ...extra };
    const bufs = [];
    for (const [k, a] of Object.entries(p.attrs)) { header.attrs[k] = { k: a.k, n: a.data.length / a.k }; bufs.push(a.data); }
    bufs.push(p.index);
    await post(url, header, bufs);
  }

  window.__cityExport = async (opts) => {
    const { region, url } = opts;
    const ctx = window.__ctx, world = ctx.world, scene = ctx.scene;
    const log = [];
    // ---- 1. static meshes
    const meshes = [];
    scene.traverse(o => { if (o.isMesh && !o.isInstancedMesh && !o.isSkinnedMesh && o.geometry?.attributes?.position) meshes.push(o); });
    const stats = {};
    for (const m of meshes) {
      const name = m.name || '';
      if (!name || (SKIP.test(name) && !/^facadeLod \d+$/.test(name) && !(opts.farRegion && FAR_RE.test(name)))) continue;
      if (opts.farRegion && FAR_RE.test(name)) { // (r02) far shores, waterfront, bridges: whole meshes in 1024 m tiles
        for (const p of splitMesh(m, opts.farRegion, null, /^(farLand-|horizonSkirt|palisadesCliff)/.test(name) ? 60000 : 2048)) await postPart(url, name.replace(/[^A-Za-z0-9_]+/g, '_'), kindOf(name, m.geometry) === 'facade' ? 'facade' : 'far', p,
          { src: name, lod: true, mat: { type: m.material?.type, color: m.material?.color?.toArray?.(), roughness: m.material?.roughness, metalness: m.material?.metalness, vertexColors: !!m.material?.vertexColors, map: m.material?.map?.image?.src ?? null } });
        continue;
      }
      const lm = /^facadeLod (\d+)$/.exec(name);
      if (lm && !opts.lodRegion) continue; // (island r01) --nofar district export: the far ring comes from another pass
      if (lm && opts.lodRegion) { // far ring: bare-mass facade LOD tiles outside the full-detail region (same facade material)
        const g = m.geometry, bb = g.boundingBox ?? (g.computeBoundingBox(), g.boundingBox), cx = (bb.min.x + bb.max.x) / 2, cz = (bb.min.z + bb.max.z) / 2, L = opts.lodRegion;
        if (cx < L.x0 || cx >= L.x1 || cz < L.z0 || cz >= L.z1) continue;
        if (cx >= region.x0 && cx < region.x1 && cz >= region.z0 && cz < region.z1) continue;
        for (const p of splitMesh(m, region, tileOf(cx, cz).join(','))) await postPart(url, 'facadeLod', 'facade', p, { src: name, lod: true });
        continue;
      }
      const tm = TILE_RE.exec(name);
      let parts;
      if (tm) {
        const g = m.geometry; if (!g.boundingBox) g.computeBoundingBox();
        const bb = g.boundingBox, cx = (bb.min.x + bb.max.x) / 2, cz = (bb.min.z + bb.max.z) / 2;
        if (cx < region.x0 || cx >= region.x1 || cz < region.z0 || cz >= region.z1) continue;
        parts = splitMesh(m, region, tileOf(cx, cz).join(','));
      } else parts = splitMesh(m, region, null);
      const base = tm ? (tm[1] === 'signage' ? 'signage' + tm[2] : tm[1]) : name.replace(/[^A-Za-z0-9_]+/g, '_'); // several signage meshes per tile
      const kind = kindOf(name, m.geometry);
      for (const p of parts) {
        await postPart(url, base, kind, p, { src: name, mat: { type: m.material?.type, color: m.material?.color?.toArray?.(), roughness: m.material?.roughness, metalness: m.material?.metalness,
          transparent: !!m.material?.transparent, vertexColors: !!m.material?.vertexColors, map: m.material?.map?.image?.src ?? m.material?.map?.source?.data?.src ?? null,
          emissive: m.material?.emissive?.toArray?.(), emissiveIntensity: m.material?.emissiveIntensity, alphaTest: m.material?.alphaTest, side: m.material?.side } });
        const s = (stats[base.replace(/\d+$/, '#')] ||= { parts: 0, verts: 0, tris: 0 });
        s.parts++; s.verts += p.attrs.position.data.length / 3; s.tris += p.index.length / 3;
      }
    }
    log.push('meshes done');
    if (opts.farRegion) { // (r02) Manhattan land surface (block interiors, parks) from the layout polygon, y = -0.06
      const THREE = window.__ctx.THREE, F0 = world.getMapFeatures();
      for (const [li, poly] of F0.land.entries()) {
        const pts = poly.map(([x, z]) => new THREE.Vector2(x, z));
        const tris = THREE.ShapeUtils.triangulateShape(pts, []);
        const P = new Float32Array(pts.length * 3), N = new Float32Array(pts.length * 3);
        pts.forEach((v, i) => { P[i * 3] = v.x; P[i * 3 + 1] = -0.06; P[i * 3 + 2] = v.y; N[i * 3 + 1] = 1; });
        const I = []; for (const [a, b, c] of tris) { // up-facing winding (three: counter-clockwise seen from +y)
          const cr = (pts[b].y - pts[a].y) * (pts[c].x - pts[a].x) - (pts[b].x - pts[a].x) * (pts[c].y - pts[a].y); if (cr > 0) I.push(a, b, c); else I.push(a, c, b); }
        const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(P, 3)); g.setAttribute('normal', new THREE.BufferAttribute(N, 3)); g.setIndex(I);
        const fake = { geometry: g, matrixWorld: new THREE.Matrix4(), updateMatrixWorld() {} };
        for (const p of splitMesh(fake, opts.farRegion, null, 2048)) await postPart(url, 'land' + li, 'land', p, { src: 'LAND_POLY', lod: true });
      }
      const H = []; scene.traverse(o => { if (o.name === 'hinterland' && o.isInstancedMesh) H.push(o); });
      for (const hm of H) {
        const a = hm.instanceMatrix.array, W = hm.geometry.attributes.aWall.array, R = hm.geometry.attributes.aRoof.array, out = [];
        for (let i = 0; i < hm.count; i++) { const e = a.subarray(i * 16, i * 16 + 16);
          out.push([e[12], e[13], e[14], Math.hypot(e[0], e[1], e[2]), Math.hypot(e[4], e[5], e[6]), Math.hypot(e[8], e[9], e[10]), Math.atan2(e[8], e[10]), ...W.subarray(i * 3, i * 3 + 3), ...R.subarray(i * 3, i * 3 + 3)].map(v => +v.toFixed(3))); }
        await post(url + '&file=hinterland.json', { type: 'json', file: 'hinterland.json', data: { note: '[x,y,z, sx,sy,sz, yaw, wall rgb, roof rgb] unit box, pivot at the bottom', items: out } }, []);
        const fake = { geometry: hm.geometry, matrixWorld: new THREE.Matrix4(), updateMatrixWorld() {} };
        const pp = splitMesh(fake, region, '0,0'); for (const p of pp) { p.center = [0, 0, 0]; for (let i = 0; i < p.attrs.position.data.length; i += 3) { p.attrs.position.data[i] += 128; p.attrs.position.data[i + 2] += 128; } }
        if (pp[0]) await postPart(url, 'hinterland', 'proto', pp[0], { src: 'hinterland', proto: true, mat: {} });
      }
    }
    // ---- 2. instanced pools (props / trees): prototype geometry once + every item inside the region
    const pools = [...(window.__pools ?? [])];
    const instances = {};
    for (const P of pools) {
      const name = P.mesh?.name || ''; if (!name) continue;
      const R0 = opts.farRegion && /^ez-.*-l1-(leaves|bark)$|^trees-(park|elm|conifer)-crownfar$/.test(name) ? opts.farRegion : region; // (r03) real ez-tree LOD1 for every tree outside the detailed block
      const inReg = (it) => it.x >= R0.x0 && it.x < R0.x1 && it.z >= R0.z0 && it.z < R0.z1;
      const inNear = (it) => it.x >= region.x0 && it.x < region.x1 && it.z >= region.z0 && it.z < region.z1;
      const items = P.items.filter(it => !it.hidden && inReg(it) && (R0 === region || !inNear(it) || /crownfar$/.test(name))); // far crowns only outside the detailed block
      if (!items.length) continue;
      instances[name] = { near: P.near, far: P.far, n: items.length, items: items.map(it => {
        const o = { x: +it.x.toFixed(3), y: +it.y.toFixed(3), z: +it.z.toFixed(3), ry: +(it.ry || 0).toFixed(4), s: +(it.s ?? 1).toFixed(4) };
        if (it.rx) o.rx = +it.rx.toFixed(4); if (it.rz) o.rz = +it.rz.toFixed(4); if (it.scale3) o.s3 = it.scale3.map(v => +v.toFixed(4));
        if (it.color) o.c = Array.from(it.color).map(v => +v.toFixed(4));
        if (it.extra) { o.e = {}; for (const k in it.extra) o.e[k] = typeof it.extra[k] === 'number' ? it.extra[k] : Array.from(it.extra[k]); }
        return o; }) };
      // prototype geometry (model space, per-vertex attributes only)
      const g = P.geo, fake = { geometry: g, matrixWorld: new window.__ctx.camera.matrixWorld.constructor(), updateMatrixWorld() {} };
      const parts = splitMesh(fake, region, '0,0');
      for (const p of parts) { p.center = [0, 0, 0]; for (let i = 0; i < p.attrs.position.data.length; i += 3) { p.attrs.position.data[i] += 128; p.attrs.position.data[i + 2] += 128; } } // undo tile-centre shift
      if (parts[0]) await postPart(url, name.replace(/[^A-Za-z0-9_]+/g, '_'), 'proto', parts[0], { src: name, proto: true,
        mat: { type: P.mat?.type, color: P.mat?.color?.toArray?.(), roughness: P.mat?.roughness, metalness: P.mat?.metalness, vertexColors: !!P.mat?.vertexColors,
          map: P.mat?.map?.image?.src ?? null, alphaTest: P.mat?.alphaTest, transparent: !!P.mat?.transparent } });
    }
    log.push('pools done ' + pools.length);
    // ---- 3. collision primitives inside the region
    const C = world.collision, sol = [];
    const usedF = new Set();
    for (let i = 0; i < C.n; i++) {
      if (C.flags[i] & 4) continue; // DEAD
      const j = i * 6, b = C.bb;
      if (b[j + 3] < region.x0 || b[j] > region.x1 || b[j + 5] < region.z0 || b[j + 2] > region.z1) continue;
      const t = C.type[i];
      const r = { t, bb: Array.from(b.subarray(j, j + 6), v => +v.toFixed(3)), p: Array.from(C.par.subarray(j, j + 6), v => +v.toFixed(4)), f: C.flags[i], k: C.kind[i] };
      if (t === 3) usedF.add(r.p[0]);
      sol.push(r);
    }
    const fields = {};
    for (const fid of usedF) { const f = C.fields[fid]; fields[fid] = { nx: f.nx, nz: f.nz, cell: f.cell, hMax: f.hMax, loMin: f.loMin,
      h: Array.from(f.h, v => (Number.isFinite(v) ? +v.toFixed(3) : null)), lo: Array.from(f.lo ?? [], v => (Number.isFinite(v) ? +v.toFixed(3) : null)) }; }
    await post(url + '&file=collision.json', { type: 'json', file: 'collision.json', data: { kinds: ['BOX', 'CYL', 'RAMP', 'HF'], surfaceKinds: KINDS(), solids: sol, fields } }, []);
    log.push('collision ' + sol.length);
    // ---- 4. layout
    const F = world.getMapFeatures();
    const inR = (x0, z0, x1, z1) => x1 >= region.x0 && x0 <= region.x1 && z1 >= region.z0 && z0 <= region.z1;
    const polyIn = (P) => P.some(([x, z]) => x >= region.x0 && x <= region.x1 && z >= region.z0 && z <= region.z1);
    const zips = world.getZipPoints ? world.getZipPoints(new window.__ctx.camera.position.constructor((region.x0 + region.x1) / 2, 0, (region.z0 + region.z1) / 2), Math.hypot(region.x1 - region.x0, region.z1 - region.z0) / 2 + 10) : [];
    const layout = {
      units: 'metres, browser frame: +x east, +y up, -z north (three.js / glTF). UE import: X=x*100, Y=z*100, Z=y*100 (cm, Z-up, left-handed; north = -Y)',
      region, tileSize: T,
      streets: F.streets.filter(s => s.poly ? polyIn(s.poly) : inR(s.x0, s.z0, s.x1, s.z1)),
      blocks: F.blocks.filter(b => inR(b.x0, b.z0, b.x1, b.z1)),
      avenueNames: F.avenueNames,
      footprints: (world.footprints || []).filter(f => f.x0 != null ? inR(f.x0, f.z0, f.x1, f.z1) : true).map(f => ({ ...f })),
      buildingBoxes: (world.buildings || []).filter(b => { const mn = b.min ?? b, mx = b.max ?? b; return inR(mn.x, mn.z, mx.x, mx.z); })
        .map(b => ({ min: [b.min.x, b.min.y, b.min.z], max: [b.max.x, b.max.y, b.max.z] })),
      zipPoints: (zips || []).filter(z => { const p = z.p ?? z.pos ?? z; return p.x >= region.x0 && p.x < region.x1 && p.z >= region.z0 && p.z < region.z1; })
        .map(z => { const p = z.p ?? z.pos ?? z, n = z.n ?? z.normal; return { p: [+p.x.toFixed(3), +p.y.toFixed(3), +p.z.toFixed(3)], n: n ? [+n.x.toFixed(3), +n.y.toFixed(3), +n.z.toFixed(3)] : null, kind: z.kind ?? z.k ?? null }; }),
      instances,
      viewpoints: Object.fromEntries(Object.entries(world.viewpoints || {}).map(([k, v]) => [k, { pos: v.pos?.toArray?.(), target: v.target?.toArray?.() }])),
      stats,
    };
    await post(url + '&file=layout.json', { type: 'json', file: 'layout.json', data: layout }, []);
    log.push('layout');
    return { log, stats, nInstances: Object.keys(instances).length };
  };
  function KINDS() { return ['wall', 'roof', 'parapet', 'coping', 'cornice', 'ledge', 'equipment', 'bulkhead', 'watertower', 'awning', 'fireescape', 'skylight', 'antenna', 'spire', 'hero', 'park', 'pier', 'glass', 'pole', 'trunk']; }
})();

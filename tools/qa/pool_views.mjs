// Headless view check (Studio): loads the game in the Chrome started with --remote-debugging-port=9333, then frames the
// nearest instance of each target pool (props, crowd animals, critters) and saves one JPEG per target.
// usage: node tools/qa/pool_views.mjs "http://localhost:5191/?skipintro" /tmp/v   ->  /tmp/v_<target>.jpg
// Uses the game debug hooks: ctx.manualStep / ctx.stepFrame(dt) and world.life.debugCam = [cx,cy,cz, tx,ty,tz].
const [url, out] = process.argv.slice(2);
const fs = await import('node:fs');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const list = await (await fetch('http://127.0.0.1:9333/json/list')).json();
let page = list.find(t => t.type === 'page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));
let id = 0; const pending = new Map(); const logs = [];
ws.addEventListener('message', ev => { const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === 'Runtime.consoleAPICalled') logs.push(m.params.type + ': ' + m.params.args.map(a => a.value ?? a.description ?? '').join(' ').slice(0, 300));
  if (m.method === 'Runtime.exceptionThrown') logs.push('EXC: ' + (m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text).slice(0, 400)); });
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expr, timeout = 120000) => { const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true, timeout }); return r.result?.result?.value ?? r.result?.exceptionDetails?.exception?.description ?? r; };
await send('Runtime.enable'); await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url });
let ready = false;
for (let i = 0; i < 180 && !ready; i++) { await sleep(1000); ready = await ev('!!window.__sys && !!window.__ctx?.world?.life', 5000) === true; }
console.log('ready', ready);
const shot = async (name) => { const s = await send('Page.captureScreenshot', { format: 'jpeg', quality: 80 }); if (s.result?.data) fs.writeFileSync(`${out}_${name}.jpg`, Buffer.from(s.result.data, 'base64')); };
console.log(JSON.stringify(await ev(`(async () => {
  const ctx = window.__ctx; ctx.manualStep = true;
  for (let i = 0; i < 30; i++) ctx.stepFrame(1 / 60);
  const names = []; ctx.scene.traverse(o => { if (o.isInstancedMesh && /Far|hydrant|trash|bench|cart|planter|mailbox|meter|newsbox|bags|drum|sawhorse|shopcart|parklamp|dogs|rats|squirrels|cats|pigeons|gulls/.test(o.name)) names.push(o.name + ':' + o.count); });
  return { stats: ctx.world.life.stats(), names };
})()`)));
const T = [
  ['squirrels', "L.critters.sites.find(s => s.kind === 'squirrel')", '^squirrels-L', 1.6, 0.8, 0.12],
  ['parklamp', "L.critters.sites.find(s => s.kind === 'squirrel')", '^parklamp$', 6, 2.2, 2.2],
  ['cats', "L.critters.sites.find(s => s.kind === 'cat')", '^cats-L', 1.8, 0.9, 0.2],
  ['gulls', "L.pigeons.flocks.find(f => f.kind === 'gull')", '^gulls-L', 2.2, 1.0, 0.2],
  ['pigeons', "L.pigeons.flocks.find(f => f.kind === 'pigeon' && f.n > 8)", '^pigeons-L', 1.6, 0.8, 0.1],
  ['rats2', "L.critters.sites.filter(s => s.kind === 'rat')[40]", '^rats-L', 1.3, 0.6, 0.08],
  ['cart2', "null", '^cart2$', 4.5, 2.0, 1.0],
  ['dogs', "null", '^dogs-.*-L0$', 2.6, 1.2, 0.3],
];
for (const [label, go, re, dist, h, lh] of T) {
  const r = await ev(`(async () => {
    const ctx = window.__ctx, W = ctx.world, L = W.life, re = new RegExp(${JSON.stringify(re)});
    const find = () => { let m = null; ctx.scene.traverse(o => { if (!m && o.isInstancedMesh && re.test(o.name) && o.count > 0) m = o; }); return m; };
    const site = ${go};
    if (site) { W.life.debugCam = [site.x + 12, 8, site.z + 12, site.x, 0, site.z]; for (let i = 0; i < 60; i++) ctx.stepFrame(1/60); }
    let m = find();
    for (let t = 0; !m && t < 40; t++) { // wander along the avenue until one shows up
      const c = ctx.camera.position; W.life.debugCam = [c.x + 40, 8, c.z + 25, c.x + 40, 0, c.z + 45]; for (let i = 0; i < 20; i++) ctx.stepFrame(1/60); m = find();
    }
    if (!m) return { miss: true };
    const e = m.instanceMatrix.array, cam = ctx.camera.position;
    let best = 0, bd = 1e9; for (let k = 0; k < m.count; k++) { const d = Math.hypot(e[k*16+12]-cam.x, e[k*16+14]-cam.z); if (d < bd) { bd = d; best = k; } }
    const x = e[best*16+12], y = e[best*16+13], z = e[best*16+14], sc = Math.hypot(e[best*16], e[best*16+2]), ry = Math.atan2(e[best*16+8], e[best*16]);
    const a = ry + 0.7;
    W.life.debugCam = [x + Math.sin(a) * ${dist}, y + ${h}, z + Math.cos(a) * ${dist}, x, y + ${lh}, z];
    ctx.stepFrame(1/60);
    return { name: m.name, count: m.count, at: [x.toFixed(1), y.toFixed(2), z.toFixed(1)] };
  })()`);
  console.log(label, JSON.stringify(r));
  if (!r.miss) await shot(label);
}
console.log('console (filtered):', [...new Set(logs.filter(l => /EXC|error|warn|hq/i.test(l)))].slice(0, 20).join('\n'));
ws.close(); process.exit(0);

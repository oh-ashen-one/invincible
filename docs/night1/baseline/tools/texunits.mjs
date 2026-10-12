// Which shader programs declare more sampler uniforms than MAX_TEXTURE_IMAGE_UNITS (the "Trying to use 17 texture units"
// warning)? Loads the game (?playtest=1), lets it run, wears every suit, then lists programs by sampler count.
import { chromium } from 'playwright-core';
const b = await chromium.launchPersistentContext('/Users/midir/sm2-n1/_scratch/baseline/chrome-profile-tex', { channel: 'chrome', headless: true,
  viewport: { width: 1280, height: 720 }, args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
const p = b.pages()[0];
let warnings = 0; p.on('console', m => { if (/texture units/.test(m.text())) warnings++; });
await p.goto((process.env.URL || 'http://127.0.0.1:5201/') + '?playtest=1');
await p.waitForFunction(() => window.__sys && window.__cmb, null, { timeout: 300000 });
await p.waitForTimeout(5000);
const w0 = warnings;
for (const id of ['iron', 'symbiote', 'claude', 'codex', 'gemini', 'kimi', 'qwen', 'advanced']) { await p.evaluate(id => __sys.debug.suit(id), id); await p.waitForTimeout(1500); }
const r = await p.evaluate(() => {
  const C = __ctx, gl = C.renderer.getContext(), max = gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS), out = [];
  for (const pr of C.renderer.info.programs) {
    const prog = pr.program; const n = gl.getProgramParameter(prog, gl.ACTIVE_UNIFORMS); let s = 0; const names = [];
    for (let i = 0; i < n; i++) { const u = gl.getActiveUniform(prog, i); if ([gl.SAMPLER_2D, gl.SAMPLER_CUBE, gl.SAMPLER_2D_SHADOW, gl.SAMPLER_2D_ARRAY, gl.SAMPLER_3D, gl.SAMPLER_2D_ARRAY_SHADOW, gl.UNSIGNED_INT_SAMPLER_2D, gl.INT_SAMPLER_2D].includes(u.type)) { s += u.size; names.push(u.name + (u.size > 1 ? `[${u.size}]` : '')); } }
    out.push({ name: pr.name, samplers: s, names });
  }
  // which scene materials use those programs
  const mats = new Map(); C.scene.traverse(o => { const ms = Array.isArray(o.material) ? o.material : o.material ? [o.material] : []; for (const m of ms) { const pp = C.renderer.properties.get(m); const prg = pp?.currentProgram; if (prg) mats.set(prg.name + '|' + m.name + '|' + m.type + '|' + o.name, prg.id); } });
  return { max, over: out.filter(o => o.samplers > max), top: out.sort((a, b) => b.samplers - a.samplers).slice(0, 6).map(o => ({ name: o.name, s: o.samplers })), mats: [...mats.keys()].filter(k => /17|Spider|suit|skin|hero/i.test(k)).slice(0, 40) };
});
console.log(JSON.stringify({ warningsAtLoad: w0, warningsAfterSuits: warnings, ...r }, null, 1));
await b.close();

// Bit-exactness test of the lit-window integer hash: the author's JS mirror (nhu / nh3 / nh01 in ~/spiderbench/src/world/facade.js, which decides the
// provider's window rects) against the HLSL functions of the generated Shaders/City/Facade.ush, compiled as C (uint -> uint32_t, float(..) casts).
//   node tools/export/facade_hash_parity.mjs        -> prints the mismatch counts, exit 1 if any
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const jsSrc = fs.readFileSync(path.join(os.homedir(), 'spiderbench/src/world/facade.js'), 'utf8');
const ush = fs.readFileSync(path.join(ROOT, 'unreal/WebHomage/Shaders/City/Facade.ush'), 'utf8');
const grab = (text, re, what) => { const m = text.match(re); if (!m) throw new Error('not found: ' + what); return m[0]; };
// ---- JS mirror (verbatim from the author's file)
const jsCode = ['const nhu = ', 'const nh3 = ', 'const nh01 = '].map(p => grab(jsSrc, new RegExp('^' + p + '.*$', 'm'), p)).join('\n') + '\nreturn { nhu, nh3, nh01 };';
const js = new Function(jsCode)();
// ---- HLSL functions of the generated Facade.ush -> C (TEXDECL is added by the translator to every user function: not here, these are hand-kept uint functions)
const hl = ['uint nhu(', 'uint nh3(', 'float nh01('].map(p => grab(ush, new RegExp('^' + p.replace('(', '\\(') + '.*$', 'm'), p)).map(l => l.replace(/TEXDECL, ?/g, '')).join('\n');
const cSrc = `#include <stdint.h>
#include <stdio.h>
#include <math.h>
typedef uint32_t uint;
#define float_(x) ((float)(x))
${hl.replace(/\bfloat\(/g, 'float_(')}
int main(void) {
  uint32_t a, b, c; int n = 0;
  while (scanf("%u %u %u", &a, &b, &c) == 3) { uint h = nh3(a, b, c); printf("%u %u %.9g %u\\n", nhu(a), h, nh01(h), n++); }
  return 0;
}
`;
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sm2-hash-'));
fs.writeFileSync(path.join(dir, 'p.c'), cSrc);
execFileSync('cc', ['-O0', '-ffp-contract=off', '-o', path.join(dir, 'p'), path.join(dir, 'p.c')]);
// ---- inputs: edge cases + random; negatives are int32 values reinterpreted (uint(int(fl)) in the shader == x >>> 0 in JS)
let seed = 12345; const rnd = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed; };
const edge = [0, 1, 2, 11, 23, 57, 91, 0xffffffff, 0x80000000, 0x7fffffff, 1000, 65535];
const triples = [];
for (const a of edge) for (const b of edge.slice(0, 6)) triples.push([a, b, 11]);
while (triples.length < 1000) triples.push([rnd(), rnd(), rnd() >>> (rnd() & 15)]);
for (let i = 0; i < 200; i++) triples.push([(-(rnd() % 400)) >>> 0, rnd() % 100000, (rnd() % 2000) + 23]);   // negative floor / bay indices
const out = execFileSync(path.join(dir, 'p'), { input: triples.map(t => t.join(' ')).join('\n') + '\n', encoding: 'utf8' }).trim().split('\n').map(l => l.split(' '));
let mism = 0, mism01 = 0;
triples.forEach(([a, b, c], i) => {
  const [hu, h3, f01] = out[i];
  const jh = js.nh3(a, b, c), jn = js.nhu(a), j01 = js.nh01(jh);
  if (jn !== +hu || jh !== +h3) { if (mism++ < 5) console.log('MISMATCH hash', a, b, c, 'js', jn, jh, 'hlsl', hu, h3); }
  if (Math.fround(j01) !== Math.fround(+f01)) { if (mism01++ < 5) console.log('MISMATCH nh01', jh, j01, f01); }
});
// ---- (informational) the seed -> uint conversion: shader float32 uint(floor(seed * 1000.0 + 0.5)) vs the mirror's double Math.floor(seed * 1000 + 0.5). The export rounds seeds to
// 4 decimals, which creates exact .5 ties (a test artefact: ~4 % of faces); the real float32 seeds hit a rounding edge on the order of 0.8 % of faces, in the author's browser GPU too.
let sdMism = 0, sdN = 0;
const nj = process.env.SM2_NIGHT_JSON || path.join(os.homedir(), 'sm2-n1/_scratch/night/export/night_lights.json');
if (fs.existsSync(nj)) {
  const faces = JSON.parse(fs.readFileSync(nj, 'utf8')).windows.faces;
  for (const f of faces) {
    const s32 = Math.fround(f.seed);   // (the export rounds seeds to 4 decimals; the browser stores float32)
    const dbl = Math.floor(s32 * 1000 + 0.5);
    const flt = Math.floor(Math.fround(Math.fround(s32 * 1000) + 0.5));
    sdN++; if (dbl !== flt) sdMism++;
  }
}
console.log(JSON.stringify({ hash_samples: triples.length, mismatches_nhu_nh3: mism, mismatches_nh01: mism01, seed_to_uint_faces: sdN, seed_to_uint_mismatches_on_4dp_rounded_seeds: sdMism, note: 'informational (see source comment)' }));
process.exit(mism || mism01 ? 1 : 0);

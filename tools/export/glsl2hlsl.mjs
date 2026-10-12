// Mechanical GLSL (three.js onBeforeCompile snippets) -> HLSL (UE Custom-node include) translator.
// Handles the subset the browser city shaders use: vector types / constructors (scalar broadcast -> cast), mix / fract /
// mod / atan2 / dFdx / textureGrad ..., const arrays, file-scope mutable globals (-> static), uninitialised structs,
// texture sampling with the three.js v-flip (v = 0 at the image bottom) and explicit texture parameters threaded through
// every user function (HLSL functions cannot see material textures as globals): TEXDECL / TEXPASS macros.
//   translate(src, { arrays: Set<textureName>, textures: [names] , renames: {a: b} }) -> string
export function translate(src, opt = {}) {
  const arrays = opt.arrays ?? new Set();
  const textures = opt.textures ?? [];
  let s = src;
  // drop declarations provided by the wrapper
  for (let k = 0; k < 8; k++) s = s.replace(/(^|;|\n)([ \t]*)(flat\s+)?(uniform|varying|attribute|precision)\b[^;]*;/g, '$1$2');
  s = s.replace(/uniform\s+(highp\s+)?sampler2D(Array)?\s+\w+\s*;/g, '');
  // types
  const T = [['vec2', 'float2'], ['vec3', 'float3'], ['vec4', 'float4'], ['ivec2', 'int2'], ['ivec3', 'int3'], ['bvec2', 'bool2'], ['bvec3', 'bool3'], ['mat2', 'float2x2'], ['mat3', 'float3x3'], ['mat4', 'float4x4']];
  for (const [a, b] of T) s = s.replace(new RegExp('\\b' + a + '\\b', 'g'), b);
  // const arrays: const float A[N] = float[N](...);  ->  static const float A[N] = { ... };
  s = s.replace(/const\s+float\s+(\w+)\[(\d+)\]\s*=\s*float\[\d+\]\(([^)]*)\)\s*;/g, 'static const float $1[$2] = { $3 };');
  // simple renames
  const R = { mix: 'lerp', fract: 'frac', dFdx: 'ddx', dFdy: 'ddy', inversesqrt: 'rsqrt', mod: 'gmod', gl_FragCoord: 'gFragCoord', cameraPosition: 'gCamPos', ...(opt.renames ?? {}) };
  for (const [a, b] of Object.entries(R)) s = s.replace(new RegExp('\\b' + a + '\\b(?!\\s*=[^=])', 'g'), b);
  // call-level rewrites that need argument parsing
  s = rewriteCalls(s, 'atan', (args) => args.length === 2 ? `atan2(${args[0]}, ${args[1]})` : `atan(${args[0]})`);
  s = rewriteCalls(s, 'greaterThan', (a) => `((${a[0]}) > (${a[1]}))`);
  s = rewriteCalls(s, 'lessThan', (a) => `((${a[0]}) < (${a[1]}))`);
  s = rewriteCalls(s, 'textureGrad', (a) => { const t = a[0].trim(), arr = arrays.has(t); return `${arr ? 'Texture2DArraySampleGrad' : 'Texture2DSampleGrad'}(${t}, ${t}Sampler, ${arr ? 'fl3' : 'fl2'}(${a[1]}), fd2(${a[2]}), fd2(${a[3]}))`; });
  s = rewriteCalls(s, 'textureLod', (a) => { const t = a[0].trim(), arr = arrays.has(t); return `${arr ? 'Texture2DArraySampleLevel' : 'Texture2DSampleLevel'}(${t}, ${t}Sampler, ${arr ? 'fl3' : 'fl2'}(${a[1]}), ${a[2]})`; });
  s = rewriteCalls(s, 'texture', (a) => { const t = a[0].trim(), arr = arrays.has(t); return a.length > 2 ? `${arr ? 'Texture2DArraySampleBias' : 'Texture2DSampleBias'}(${t}, ${t}Sampler, ${arr ? 'fl3' : 'fl2'}(${a[1]}), ${a[2]})` : `${arr ? 'Texture2DArraySample' : 'Texture2DSample'}(${t}, ${t}Sampler, ${arr ? 'fl3' : 'fl2'}(${a[1]}))`; });
  // scalar-broadcast constructors: floatN(x) -> ((floatN)(x))
  for (const ty of ['float2', 'float3', 'float4', 'int2', 'int3']) s = rewriteCalls(s, ty, (a) => a.length === 1 ? `((${ty})(${a[0]}))` : `${ty}(${a.join(',')})`);
  // uninitialised struct locals
  s = s.replace(/\b(Surf)\s+(\w+)\s*;/g, '$1 $2 = ($1)0;');
  s = s.replace(/\b(Surf)\s+(\w+)\s*,\s*(\w+)\s*;/g, '$1 $2 = ($1)0; $1 $3 = ($1)0;');
  // file-scope mutable globals -> static; thread textures through user functions
  s = scopeFix(s, textures);
  // float literals -> explicit 'f' (DXC types bare literals in ternaries as 'literal float' -> FP64 on Metal)
  s = s.replace(/(^|[^\w.])(\d+\.\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+)(?![\w.])/g, '$1$2f');
  return s;
}

// find NAME( ... ) calls (not preceded by an identifier char or '.') and replace via fn(args[])
export function rewriteCalls(s, name, fn) {
  const re = new RegExp('(^|[^\\w.])' + name + '\\s*\\(', 'g');
  let out = '', i = 0, m;
  while ((m = re.exec(s))) {
    const start = m.index + m[1].length, open = re.lastIndex - 1;
    let d = 0, j = open, args = [], a0 = open + 1;
    for (; j < s.length; j++) {
      const c = s[j];
      if (c === '(' || c === '[' || c === '{') d++;
      else if (c === ')' || c === ']' || c === '}') { d--; if (d === 0) break; }
      else if (c === ',' && d === 1) { args.push(s.slice(a0, j)); a0 = j + 1; }
    }
    args.push(s.slice(a0, j));
    const inner = args.map(x => rewriteCalls(x, name, fn));
    out += s.slice(i, start) + fn(inner.map(x => x.trim()));
    i = j + 1; re.lastIndex = j + 1;
  }
  return out + s.slice(i);
}

const TYPE = '(?:float|float2|float3|float4|int|int2|int3|bool|Surf|float2x2|float3x3)';
function scopeFix(s, textures) {
  // collect user function names (depth-0 definitions)
  const fnames = new Set();
  const defRe = new RegExp('(^|\\n)\\s*' + TYPE + '\\s+(\\w+)\\s*\\(([^)]*)\\)\\s*\\{', 'g');
  let m; while ((m = defRe.exec(s))) fnames.add(m[2]);
  // walk top level: statics for globals, TEXDECL in definitions
  let out = '', depth = 0, i = 0, lineStart = true;
  while (i < s.length) {
    if (depth === 0 && lineStart) {
      const rest = s.slice(i);
      const def = new RegExp('^(\\s*)(' + TYPE + ')\\s+(\\w+)\\s*\\(([^)]*)\\)(\\s*\\{)').exec(rest);
      if (def) {
        const params = def[4].trim();
        out += `${def[1]}${def[2]} ${def[3]}(${textures.length ? 'TEXDECL' + (params ? ', ' : '') : ''}${params})${def[5]}`;
        i += def[0].length; depth++; lineStart = false; continue;
      }
      const glob = new RegExp('^(\\s*)(' + TYPE + ')\\s+(?!\\w+\\s*\\()').exec(rest);
      if (glob && !/^\s*static\b/.test(rest)) { out += glob[1] + 'static ' + rest.slice(glob[1].length, glob[0].length); i += glob[0].length; lineStart = false; continue; }
    }
    const c = s[i];
    if (c === '/' && s[i + 1] === '/') { const e = s.indexOf('\n', i); const k = e < 0 ? s.length : e; out += s.slice(i, k); i = k; continue; }
    if (c === '{') depth++; else if (c === '}') depth--;
    lineStart = c === '\n' || (depth === 0 && (c === ';' || c === '}'));
    out += c; i++;
  }
  // call sites: user functions get TEXPASS as first argument
  if (textures.length) for (const f of fnames) {
    out = out.replace(new RegExp('(^|[^\\w.])(' + f + ')\\s*\\(\\s*(\\))?', 'g'), (all, pre, name, close, off, str) => {
      // skip the definition itself (already has TEXDECL)
      const after = str.slice(off + all.length, off + all.length + 7);
      if (after.startsWith('TEXDECL')) return all;
      return `${pre}${name}(TEXPASS${close ? ')' : ', '}`;
    });
  }
  return out;
}

export const PRELUDE = `
// ---- GLSL compatibility (tools/export/glsl2hlsl.mjs)
float  gmod(float x, float y)   { return x - y * floor(x / y); }
float2 gmod(float2 x, float y)  { return x - y * floor(x / y); }
float3 gmod(float3 x, float y)  { return x - y * floor(x / y); }
float2 gmod(float2 x, float2 y) { return x - y * floor(x / y); }
float3 gmod(float3 x, float3 y) { return x - y * floor(x / y); }
float2 fl2(float2 v) { return float2(v.x, 1.0 - v.y); }   // three.js textures: v = 0 at the image bottom
float3 fl3(float3 v) { return float3(v.x, 1.0 - v.y, v.z); }
float2 fd2(float2 d) { return float2(d.x, -d.y); }
`;

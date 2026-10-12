#!/usr/bin/env python3
"""Offline re-compile of FAILED terrain material permutations with UE's own ShaderCompileWorker (CPU only: no engine, no GPU, no lock; ~0.3 s per permutation).
When a material fails to compile in the game ("Failed to compile Material ... Default Material will be used in game") the engine dumps the exact generated shader of every failing permutation to
  <worktree>/unreal/WebHomage/Saved/ShaderDebugInfo/METAL_SM6/<Material>_<hash>/Default/<VertexFactory>/<Shader>/<perm>/{<Pass>.usf, DebugCompile.in, DebugCompileArgs.txt}
(the .usf is the preprocessed source with `#line` markers; /Engine/Generated/Material.ush holds the Custom-node functions and the macros of the permutation are listed as `// #define X Y` comments
in its header). This tool copies a material's dump tree to scratch, swaps the inlined /Project/Terrain/Foliage.ush section for the CURRENT file on disk (with the permutation's macros re-defined),
and runs  ShaderCompileWorker <dir> 0 DebugCompile DebugCompile.in DebugCompile.out -DebugSourceFiles=...  so a fix to Foliage.ush is verified against UE's real material wrapper (parameter types,
stage rules such as "no derivatives in ray tracing hit shaders", Nanite / shadow / ray tracing permutations) before a GPU-lock turn is spent. Custom-node bodies stay the ones of the dump.
Limits: only permutations that failed once have a dump (run the game once, or `r.DumpShaderDebugInfo=1`); a dump of an older body is not a check of a changed body.
usage: scw_check.py [--no-regen] [material name prefix ...]   (default: every M_Terrain* dump, with the CURRENT Custom-node bodies of terrain_materials.py regenerated into the dumped wrapper;\n       env SM2_FOLIAGE_SRC=<file> tests a candidate Foliage.ush; exit code 1 on any error)"""
import os, sys, re, shutil, subprocess, glob, shlex, json
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
DUMPS = os.path.join(REPO, 'unreal', 'WebHomage', 'Saved', 'ShaderDebugInfo', 'METAL_SM6')
FOLI = os.path.join(REPO, 'unreal', 'WebHomage', 'Shaders', 'Terrain', 'Foliage.ush')
SCW = '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/ShaderCompileWorker'
SCR = os.environ.get('SM2_TERRAIN_SCRATCH', '/Users/midir/sm2-n1/_scratch/terrain'); WORK = os.path.join(SCR, 'scw')
USED = ('SHADOW_DEPTH_SHADER', 'LUMEN_CARD_CAPTURE', 'RAYTRACINGSHADER', 'RAYHITGROUPSHADER')   # macros Foliage.ush tests

FOLI = os.environ.get('SM2_FOLIAGE_SRC', FOLI)    # test a candidate Foliage.ush from scratch before it goes into the worktree

def current_materials():
    """the CURRENT Custom-node definitions (terrain_materials.py) with the float-literal fix of build_terrain.py applied"""
    ns = {}; exec(compile(open(os.path.join(REPO, 'unreal', 'WebHomage', 'Scripts', 'terrain_materials.py')).read(), 'terrain_materials.py', 'exec'), ns)
    src = open(os.path.join(REPO, 'unreal', 'WebHomage', 'Scripts', 'build_terrain.py')).read(); i = src.index('_LIT = '); j = src.index('def sampler_for')
    fx = {'re': re}; exec(src[i:j], fx)
    pm = json.load(open(os.path.join(SCR, 'prep', 'pathmask.json')))
    return {d['name']: dict(d, code=fx['fix_literals'](d['code'])) for d in ns['materials'](pm)}

def regen_custom(usf, mat):
    """replace the dumped Custom-node function by the current material's code: the dump's input parameters stay (inputs must be unchanged), outputs the material has but the dump lacks are appended
    to the signature and to the call site (as fresh locals), so a changed body / a new output pin is compiled inside UE's real wrapper"""
    m = re.search(r'(float3 CustomExpression0\()([^\n]*)(\)\s*\n\{\n)(.*?)(\n\}\n)', usf, re.S)
    if not m: return usf, 'no CustomExpression0 in the dump'
    params = [x.strip() for x in re.split(r',(?![^()]*\))', m.group(2))]
    keep = [x for x in params if not x.startswith('inout ')]; old_out = [x for x in params if x.startswith('inout ')]
    old_names = [x.split()[-1] for x in old_out]
    ty = {1: 'float', 2: 'float2', 3: 'float3'}
    new_out = [(n, k) for n, k, _ in mat['outputs'][1:]]
    extra = [(n, k) for n, k in new_out if n not in old_names]
    gone = [n for n in old_names if n not in [n2 for n2, _ in new_out]]
    if gone: return usf, 'dump has outputs the material no longer has: %s' % gone
    sig = ', '.join(keep + old_out + ['inout %s %s' % (ty[k], n) for n, k in extra])
    body = mat['code'].strip('\n')
    # r03: inputs the material has but the dump lacks (new input pins) become locals of the body with the type UE passes (texture objects cannot be faked: reported)
    pnames = [x.split()[-1] for x in keep]
    tyk = {'wn': 'float3', 'sun': 'float3', 'wpos': 'float3', 'cam': 'float3', 'vector': 'float3', 'vc': 'float3', 'uv': 'float2'}
    for n, k, _ in mat['inputs']:
        if n in pnames: continue
        if k in ('tex', 'texparam'): return usf, 'new texture input %s cannot be checked against this dump' % n
        t_ = tyk.get(k, 'float'); body = '%s %s = (%s)0.5f;\n' % (t_, n, t_) + body
    out = usf[:m.start()] + m.group(1) + sig + m.group(3) + body + m.group(5) + usf[m.end():]
    if extra:    # every call site (Nanite permutations call it in several places): append fresh locals for the new outputs
        pos = 0
        while True:
            i = out.find('= CustomExpression0(', pos)
            if i < 0: break
            j = i + len('= CustomExpression0('); depth = 1
            while depth and j < len(out):
                depth += {'(': 1, ')': -1}.get(out[j], 0); j += 1
            close = j - 1                                        # the matching ')'
            ls = out.rfind('\n', 0, i) + 1                       # start of the statement's line
            decl = ''.join('%s _x%d_%s = (%s)0; ' % (ty[k], i, n, ty[k]) for n, k in extra)
            args = ''.join(', _x%d_%s' % (i, n) for n, k in extra)
            out = out[:ls] + decl + out[ls:close] + args + out[close:]
            pos = close + len(decl) + len(args) + 1
    return out, None

def patch(usf, new_foliage):
    """swap the inlined Foliage.ush section (from its first `#line` marker up to the generated Material.ush `#line` that precedes CustomExpression0) for the current file"""
    ma = re.search(r'#line \d+ "/Project/Terrain/Foliage.ush"', usf)    # the first marker differs per permutation (unused leading functions are stripped)
    if not ma: return usf, False
    a = ma.start()
    m = re.search(r'#line \d+ "/Engine/Generated/Material.ush"\n[^\n]*CustomExpression0\(', usf[a:])
    if not m: return usf, False
    b = a + m.start()
    defs = ''
    for name in USED:    # the dump's header lists the permutation's macros as comments: re-define the ones the new text tests
        mm = re.search(r'^// #define %s (\S+)' % name, usf[:200000], re.M)
        if mm and mm.group(1) != '0': defs += '#define %s %s\n' % (name, mm.group(1))
    body = new_foliage.replace('#pragma once', '')
    # UE strips unused functions from the dumped source: the engine's Texture2DSampleGrad (Common.ush) is missing from dumps of materials that never used it; re-declare it (identical body)
    if 'Texture2DSampleGrad(Texture2D' not in usf:
        body = 'float4 Texture2DSampleGrad(Texture2D Tex, SamplerState Sampler, float2 UV, float2 DDX, float2 DDY) { return Tex.SampleGrad(Sampler, UV, DDX, DDY); }\n' + body
    return usf[:a] + '#line 1 "/Project/Terrain/Foliage.ush"\n' + defs + body + '\n' + usf[b:], True

def check_material(mdir):
    T = os.path.join(WORK, os.path.basename(mdir)); shutil.rmtree(T, ignore_errors=True); shutil.copytree(mdir, T)
    results = []
    for inp in sorted(glob.glob(os.path.join(T, '**', 'DebugCompile.in'), recursive=True)):
        d = os.path.dirname(inp); rel = os.path.relpath(d, T)
        toks = shlex.split(open(os.path.join(d, 'DebugCompileArgs.txt')).read()); toks[0] = d
        srcs = [t.split('=', 1)[1] for t in toks if t.startswith('-DebugSourceFiles=')]
        files = [os.path.normpath(os.path.join(d, f)) for f in (srcs[0].split(',') if srcs else [])]
        did = False; mname = re.sub(r'_[0-9a-f]{12,}$', '', os.path.basename(mdir))
        for f in files:
            if os.path.exists(f):
                text = open(f, encoding='utf8', errors='replace').read(); new, ok = patch(text, open(FOLI).read())
                if ok:
                    note = None
                    if REGEN and mname in CUR: new, note = regen_custom(new, CUR[mname])
                    if note: results.append((rel, False, 'regen: ' + note)); did = None; break
                    open(f, 'w', encoding='utf8').write(new); did = True
        if did is None: continue
        if not did: results.append((rel, None, 'no Foliage.ush section in this dump (permutation does not use it)')); continue
        r = subprocess.run([SCW] + toks, capture_output=True, text=True, cwd=d)
        errs = [l for l in (r.stdout + r.stderr).splitlines() if 'Error' in l or 'error:' in l]
        results.append((rel, not errs, '\n'.join(errs[:10])))
    return results

REGEN = '--no-regen' not in sys.argv
CUR = current_materials() if REGEN else {}
def main():
    pre = [a for a in sys.argv[1:] if not a.startswith('--')] or ['M_Terrain']; bad = 0; n = 0
    mdirs = sorted({d for p in pre for d in glob.glob(os.path.join(DUMPS, p + '*')) if os.path.isdir(d)})
    if not mdirs: print('no shader debug dumps found under', DUMPS); return
    for m in mdirs:
        print('==', os.path.basename(m))
        for rel, ok, msg in check_material(m):
            print('  %-4s %s' % ('OK' if ok else ('SKIP' if ok is None else 'FAIL'), rel))
            if ok is False: print('\n'.join('      ' + l for l in msg.splitlines())); bad += 1
            n += ok is not None
    print('%d permutations compiled, %d failed' % (n, bad))
    sys.exit(1 if bad else 0)
main()

#!/usr/bin/env python3
"""Offline HLSL compile check of the terrain Custom-node bodies (+ the generated Shaders/Terrain/*.ush) with the DXC library that ships with Unreal
(ShaderConductor/Mac/libdxcompiler.dylib), driven through ctypes. UE macros are stubbed; each material body is wrapped as the function UE generates
for a Custom node. Catches syntax / type / undefined-identifier errors in seconds (a wrong shader otherwise costs a GPU-lock turn).
usage: check_hlsl.py [material name ...]   (exit code 1 on any error)"""
import ctypes, os, re, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SCRIPTS = os.path.join(REPO, 'unreal', 'WebHomage', 'Scripts'); SHADERS = os.path.join(REPO, 'unreal', 'WebHomage', 'Shaders')
LIB = '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/ShaderConductor/Mac/libdxcompiler.dylib'
SCR = os.environ.get('SM2_TERRAIN_SCRATCH', '/Users/midir/sm2-n1/_scratch/terrain')

class GUID(ctypes.Structure):
    _fields_ = [('d1', ctypes.c_uint32), ('d2', ctypes.c_uint16), ('d3', ctypes.c_uint16), ('d4', ctypes.c_ubyte * 8)]
def guid(s):
    p = s.split('-'); g = GUID(); g.d1 = int(p[0], 16); g.d2 = int(p[1], 16); g.d3 = int(p[2], 16)
    b = bytes.fromhex(p[3] + p[4]); g.d4 = (ctypes.c_ubyte * 8)(*b); return g
CLSID_Compiler = guid('73e22d93-e6ce-47f3-b5bf-f0664f39c1b0'); IID_Compiler3 = guid('228b4687-5a6a-4730-900c-9702b2203f54')
IID_Result = guid('58346cda-dde7-4497-9461-6f87af5e0659')
class DxcBuffer(ctypes.Structure):
    _fields_ = [('Ptr', ctypes.c_void_p), ('Size', ctypes.c_size_t), ('Encoding', ctypes.c_uint32)]

dxc = ctypes.CDLL(LIB)
dxc.DxcCreateInstance.argtypes = [ctypes.POINTER(GUID), ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)]
dxc.DxcCreateInstance.restype = ctypes.c_long
def vcall(obj, idx, restype, argtypes, *args):
    vt = ctypes.cast(obj, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
    return ctypes.CFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(vt[idx])(obj, *args)

def compile_hlsl(src, profile='ps_6_6'):
    comp = ctypes.c_void_p()
    hr = dxc.DxcCreateInstance(ctypes.byref(CLSID_Compiler), ctypes.byref(IID_Compiler3), ctypes.byref(comp))
    if hr != 0: raise RuntimeError('DxcCreateInstance failed %x' % (hr & 0xffffffff))
    data = src.encode('utf8'); buf = DxcBuffer(ctypes.cast(ctypes.c_char_p(data), ctypes.c_void_p), len(data), 65001)
    args = ['-E', 'main', '-T', profile, '-HV', '2021', '-Wno-ignored-attributes']
    arr = (ctypes.c_wchar_p * len(args))(*args)
    res = ctypes.c_void_p()
    hr = vcall(comp, 3, ctypes.c_long, [ctypes.POINTER(DxcBuffer), ctypes.POINTER(ctypes.c_wchar_p), ctypes.c_uint32, ctypes.c_void_p, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)],
              ctypes.byref(buf), arr, len(args), None, ctypes.byref(IID_Result), ctypes.byref(res))
    if hr != 0: return False, 'Compile() failed %x' % (hr & 0xffffffff)
    status = ctypes.c_long(); vcall(res, 3, ctypes.c_long, [ctypes.POINTER(ctypes.c_long)], ctypes.byref(status))
    err = ctypes.c_void_p(); vcall(res, 5, ctypes.c_long, [ctypes.POINTER(ctypes.c_void_p)], ctypes.byref(err))
    msg = ''
    if err.value:
        p = vcall(err, 3, ctypes.c_void_p, []); n = vcall(err, 4, ctypes.c_size_t, [])
        msg = ctypes.string_at(p, n).decode('utf8', 'replace') if p and n else ''
    return status.value == 0, msg

PRE = '''#define Texture2DSample(T, S, UV) T.Sample(S, UV)
#define Texture2DSampleLevel(T, S, UV, L) T.SampleLevel(S, UV, L)
#define Texture2DSampleBias(T, S, UV, B) T.SampleBias(S, UV, B)
#define Texture2DSampleGrad(T, S, UV, DX, DY) T.SampleGrad(S, UV, DX, DY)
struct FStubParams { float4 SvPosition; };
static FStubParams Parameters = { float4(640.5f, 360.5f, 0.0f, 1.0f) };   // the Custom node body sees UE's FMaterialPixelParameters as `Parameters`
'''
def inline_includes(src, depth=0):
    def rep(m):
        rel = m.group(1)
        assert rel.startswith('/Project/'), rel
        path = os.path.join(SHADERS, rel[len('/Project/'):])
        return '// ---- begin %s\n%s\n// ---- end %s\n' % (rel, inline_includes(open(path).read(), depth + 1), rel)
    return re.sub(r'#include\s+"([^"]+)"', rep, src).replace('#pragma once', '')

def wrap(d):
    """the function UE generates for a Custom node: inputs as parameters (texture objects + samplers), additional outputs as locals"""
    params, args, g = [], [], []
    for n, k, a in d['inputs']:
        if k in ('tex', 'texparam'): params += ['Texture2D %s' % n, 'SamplerState %sSampler' % n]; g.append('Texture2D g_%s; SamplerState g_%sSampler;' % (n, n)); args += ['g_%s' % n, 'g_%sSampler' % n]
        elif k == 'uv': params.append('float2 %s' % n); args.append('float2(0.3, 0.7)')
        elif k == 'wpos': params.append('float3 wpos'); args.append('float3(%s)' % '12345.0, -67890.0, 55.0')
        elif k == 'vc': params.append('float3 vc'); args.append('float3(0.3, 0.4, 0.5)')
        elif k == 'cam': params.append('float3 cam'); args.append('float3(1500.0, -2500.0, 6200.0)')
        elif k == 'wn': params.append('float3 wn'); args.append('float3(0.0, 0.6, 0.8)')
        elif k == 'sun': params.append('float3 %s' % n); args.append('float3(0.3, -0.5, 0.81)')   # r03: SkyAtmosphereLightDirection (float3)
        elif k == 'vector': params.append('float3 %s' % n); args.append('float3(520.0, 3200.0, 0.0)')   # UE passes a VectorParameter to a Custom node as float3 (the r02 warm-up caught float4 vs float3)
        else: params.append('float %s' % n); args.append('0.5')
    ty = {1: 'float', 2: 'float2', 3: 'float3'}
    for n, k, _ in d['outputs'][1:]: params.append('out %s %s' % (ty[k], n)); args.append('o_%s' % n)
    decl = ''.join('  %s o_%s = (%s)0;\n' % (ty[k], n, ty[k]) for n, k, _ in d['outputs'][1:])
    ret = ' + '.join(('o_%s' % n) if k == 1 else ('dot(o_%s, 1.0)' % n) for n, k, _ in d['outputs'][1:]) or '0.0'
    inc = inline_includes('#include "%s"\n' % d['include']) if d['include'] else ''
    return PRE + inc + '\n'.join(g) + '\nfloat3 CustomExpr(%s)\n{\n%s\n}\nfloat4 main() : SV_Target\n{\n%s  float3 c = CustomExpr(%s);\n  return float4(c, %s);\n}\n' % (', '.join(params), d['code'], decl, ', '.join(args), ret), params

def main():
    ns = {}; exec(compile(open(os.path.join(SCRIPTS, 'terrain_materials.py')).read(), 'terrain_materials.py', 'exec'), ns)
    pm = json.load(open(os.path.join(SCR, 'prep', 'pathmask.json')))
    sys.path.insert(0, os.path.join(SCRIPTS))
    # reuse the float-literal fixer of build_terrain.py
    src = open(os.path.join(SCRIPTS, 'build_terrain.py')).read(); i = src.index('_LIT = '); j = src.index('def sampler_for')
    fx = {'re': re}; exec(src[i:j], fx)
    want = set(sys.argv[1:]); bad = 0
    for d in ns['materials'](pm):
        if want and d['name'] not in want: continue
        d = dict(d); d['code'] = fx['fix_literals'](d['code'])
        text, _ = wrap(d)
        ok, msg = compile_hlsl(text)
        print('%-20s %s' % (d['name'], 'OK' if ok else 'FAILED'))
        if msg.strip(): print('\n'.join('    ' + l for l in msg.strip().splitlines()[:40]))
        if not ok:
            bad += 1
            open(os.path.join(SCR, 'hlsl_fail_%s.hlsl' % d['name']), 'w').write(text)
    sys.exit(1 if bad else 0)
main()

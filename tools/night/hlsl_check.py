#!/usr/bin/env python3
"""Offline HLSL compile check (no Unreal needed): compiles every generated Shaders/City/*.ush and every Custom-node body our builders emit
(build_city.py make_material, build_look.py night materials) with UE's bundled DXC (libdxcompiler via tools/night/dxc.py), as a minimal
pixel shader with ps_6_6 / -HV 2021. UE's material-template symbols (Parameters, ResolvedView, Texture2DSample...) are stubbed in PRELUDE; an
error that names one of those stubs is a harness artefact, anything else is a real error in our HLSL.
  python3 tools/night/hlsl_check.py            # everything, JSON summary, exit 1 on any error
  python3 tools/night/hlsl_check.py -v         # print every message
Builders are loaded under a stub `unreal` module (the code that builds the Custom nodes runs unchanged; make_material records them).
Every body is compiled twice: as a pixel shader (ps_6_6) and as a ray-tracing hit shader (lib_6_6 closesthit): UE compiles each material for both (SF_METAL_SM6
with ray tracing), and there ddx / ddy / fwidth / clip are dummies and the implicit-derivative Sample / SampleBias / CalculateLevelOfDetail opcodes are invalid:
the harness turns those three into undefined identifiers, and Texture2DSample() (UE's wrapper) into SampleLevel(..., 0), as the engine does.
Terrain materials (terrain_materials.py) and Shaders/Terrain/*.ush are checked too; a missing generated include (ParkData.ush) is an error."""
import argparse
import json
import os
import sys
import types
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'unreal/WebHomage/Scripts'
SHADERS = ROOT / 'unreal/WebHomage/Shaders'
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(SCRIPTS))
import dxc  # noqa: E402

RT_PRELUDE = r'''
// ---- ray-tracing hit shader stubs (UE: Common.ush RAYTRACINGSHADER / USE_FORCE_TEXTURE_MIP) ----
#define clip(x)
#define ddx(x) 0
#define ddy(x) 0
#define fwidth(x) 0
#define Texture2DSample(T, S, uv) T.SampleLevel(S, uv, 0)
#define Texture2DSampleBias(T, S, uv, b) T.SampleLevel(S, uv, 0)
#define Texture2DArraySample(T, S, uv) T.SampleLevel(S, uv, 0)
#define Sample(...) SM2_ERROR_Sample_is_not_valid_in_a_closesthit_shader(__VA_ARGS__)
#define SampleBias(...) SM2_ERROR_SampleBias_is_not_valid_in_a_closesthit_shader(__VA_ARGS__)
#define CalculateLevelOfDetail(...) SM2_ERROR_CalculateLevelOfDetail_is_not_valid_in_a_closesthit_shader(__VA_ARGS__)
'''
PRELUDE = r'''
// ---- stubs of UE material-template symbols (harness artefacts) ----
#define Texture2DSample(T, S, uv) T.Sample(S, uv)
#define Texture2DSampleLevel(T, S, uv, l) T.SampleLevel(S, uv, l)
#define Texture2DSampleBias(T, S, uv, b) T.SampleBias(S, uv, b)
#define Texture2DSampleGrad(T, S, uv, dx, dy) T.SampleGrad(S, uv, dx, dy)
#define Texture2DArraySample(T, S, uv) T.Sample(S, uv)
#define Texture2DArraySampleLevel(T, S, uv, l) T.SampleLevel(S, uv, l)
#define Texture2DArraySampleGrad(T, S, uv, dx, dy) T.SampleGrad(S, uv, dx, dy)
struct FStubView { float4 DirectionalLightDirection; float4 DirectionalLightColor; float3 WorldCameraOrigin; float3 PreViewTranslation; float PreExposure; float4 BufferSizeAndInvSize; float2 ViewSizeAndInvSize; };
static FStubView ResolvedView;
struct FMaterialPixelParameters { float4 SvPosition; float4 ScreenPosition; float2 ViewBufferUV; float3 WorldPosition_NoOffsets; float3 TangentToWorld0; float4 VertexColor; float3 CameraVector; float3 TranslatedWorldPosition; };
#define SM2_PARAMS_INIT(P, sv) FMaterialPixelParameters P = (FMaterialPixelParameters)0; P.SvPosition = sv;
'''

KIND_TYPE = {'sun': 'float3', 'pir': 'float', 'texparam_': 'float', 'uv': 'float2', 'vc': 'float3', 'vca': 'float', 'wpos': 'float3', 'wn': 'float3', 'cam': 'float3', 'scalar': 'float', 'vector': 'float4', 'mpc': 'float', 'time': 'float',
             'pcd': 'float', 'cd': 'float', 'lp': 'float3', 'param': 'float'}
OUT_TYPE = {1: 'float', 2: 'float2', 3: 'float3'}


def prelude(mode):
    return PRELUDE if mode == 'ps' else PRELUDE + '\n#undef Texture2DSample\n#undef Texture2DArraySample\n' + RT_PRELUDE


def wrap_node(name, code, inputs, outputs, includes_text='', mode='ps'):
    """-> HLSL source: prelude + includes + CustomMain(Parameters, inputs..., out outputs...) { code } + a ps_6_6 entry that calls it"""
    params, decl, call = [], [], []
    for spec in inputs:
        n, kind = spec[0], spec[1]
        if kind in ('tex', 'texparam'):
            ttype = 'Texture2DArray' if (len(spec) > 2 and spec[2] and '/TA_' in str(spec[2])) else 'Texture2D'   # texture arrays (TA_*) are Texture2DArray in the material
            params += ['%s %s' % (ttype, n), 'SamplerState %sSampler' % n]
            decl.append('%s G_%s : register(t%d); SamplerState G_%sSampler : register(s%d);' % (ttype, n, len(decl), n, len(decl)))
            call += ['G_%s' % n, 'G_%sSampler' % n]
        else:
            params.append('%s %s' % (KIND_TYPE[kind], n))
            call.append('(%s)0.5' % KIND_TYPE[kind])
    outs = outputs[1:]
    for n, k in outs:
        params.append('out %s %s' % (OUT_TYPE[k], n))
    ret = OUT_TYPE[outputs[0][1]] if outputs else 'float3'
    out_decl = ''.join('    %s o_%s;\n' % (OUT_TYPE[k], n) for n, k in outs)
    out_call = ''.join(', o_%s' % n for n, k in outs)
    out_sum = ''.join(' + (float3)o_%s' % n for n, k in outs)
    src = prelude(mode) + includes_text + '\n'
    src += '%s CustomMain(FMaterialPixelParameters Parameters%s)\n{\n%s\n}\n' % (ret, ''.join(', ' + p for p in params), code)
    src += '\n'.join(d for d in decl) + '\n'
    if mode == 'ps':
        src += 'float4 main(float4 sv : SV_Position) : SV_Target\n{\n    SM2_PARAMS_INIT(P, sv)\n%s' % out_decl
        src += '    %s r = CustomMain(P%s%s);\n    return float4((float3)r%s, 1.0);\n}\n' % (ret, ''.join(', ' + c for c in call), out_call, out_sum)
    else:
        src += 'struct SM2Payload { float4 c; };\n[shader("closesthit")] void CHS(inout SM2Payload payload, BuiltInTriangleIntersectionAttributes attr)\n{\n    SM2_PARAMS_INIT(P, float4(1, 1, 0, 1))\n%s' % out_decl
        src += '    %s r = CustomMain(P%s%s);\n    payload.c = float4((float3)r%s, 1.0);\n}\n' % (ret, ''.join(', ' + c for c in call), out_call, out_sum)
    return src


class _Meta(type):
    def __getattr__(cls, name):
        if name.startswith('__'):
            raise AttributeError(name)
        v = mock.MagicMock(name='%s.%s' % (cls.__name__, name))
        setattr(cls, name, v)
        return v


class _Stub(metaclass=_Meta):
    def __init__(self, *a, **k):
        pass

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return mock.MagicMock(name='stub.' + name)


class _UnrealStub(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        cls = _Meta(name, (_Stub,), {})
        setattr(self, name, cls)
        return cls


def load_builder(filename, env, job_args=None):
    """exec a builder script under a stub `unreal`; returns its globals"""
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    sys.modules['unreal'] = _UnrealStub('unreal')
    path = str(SCRIPTS / filename)
    ns = {'__file__': path, '__name__': 'sm2_hlsl_check_' + filename}
    if job_args:
        ns['JOB_ARGS'] = job_args
    try:
        exec(compile(open(path).read(), path, 'exec'), ns)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return ns


MISSING_INCLUDES = []


def inline(text, seen=None):
    """expand '#include "/Project/<path>"' from unreal/WebHomage/Shaders (the engine maps <project>/Shaders to /Project); a missing file is recorded"""
    import re
    seen = seen if seen is not None else set()

    def rep(m):
        rel = m.group(1)
        path = SHADERS / rel[len('/Project/'):]
        if not path.is_file():
            MISSING_INCLUDES.append(rel)
            return '// MISSING INCLUDE %s\n' % rel
        if rel in seen:
            return ''
        seen.add(rel)
        return '// ---- begin %s\n%s\n// ---- end %s\n' % (rel, inline(path.read_text(), seen), rel)
    return re.sub(r'#include "(/Project/[^"]+)"', rep, text)


def collect():
    items = []   # dicts: label + ('ush', text) | ('node', name, code, inputs, outputs, include paths)
    for d in ('City', 'Terrain'):
        for p in sorted((SHADERS / d).glob('*.ush')):
            items.append({'label': 'ush/%s/%s' % (d, p.name), 'ush': p.read_text()})
    env_city = {'SM2_CITY_EXPORT': os.environ.get('SM2_CITY_EXPORT', str(Path.home() / 'sm2-n1/_scratch/showcase/manhattan/export/midtown3x3')),
                'SM2_CITY_TEX': os.environ.get('SM2_CITY_TEX', str(Path.home() / 'sm2-n1/_scratch/showcase/manhattan/tex')),
                'SM2_CITY_SCRATCH': os.environ.get('SM2_CITY_SCRATCH', str(Path.home() / 'sm2-n1/_scratch/showcase/manhattan')), 'SM2_STRICT': '0'}
    if not (Path(env_city['SM2_CITY_EXPORT']) / 'manifest.json').is_file() and (Path(env_city['SM2_CITY_EXPORT']) / 'midtown3x3/manifest.json').is_file():
        env_city['SM2_CITY_EXPORT'] = str(Path(env_city['SM2_CITY_EXPORT']) / 'midtown3x3')   # build_city reads <export>/manifest.json at import (emissive instance refresh)
    ns = load_builder('build_city.py', env_city, {'steps': 'mat'})
    for name, code, inputs, outputs, incs in ns['custom_nodes']():
        items.append({'label': 'build_city/' + name, 'node': (name, code, inputs, outputs, incs)})
    ns = load_builder('build_look.py', {'SM2_LOOK_STEPS': 'none', 'SM2_STRICT': '0', 'SM2_CITY_EXPORT': env_city['SM2_CITY_EXPORT']})
    for name, code, inputs, outputs in ns['night_custom_nodes']():
        items.append({'label': 'build_look/' + name, 'node': (name, code, inputs, outputs, [])})
    pm = Path(os.environ.get('SM2_TERRAIN_PREP', str(Path.home() / 'sm2-n1/_scratch/terrain/prep'))) / 'pathmask.json'
    if pm.is_file():
        tns = {}
        exec(compile((SCRIPTS / 'terrain_materials.py').read_text(), 'terrain_materials.py', 'exec'), tns)
        for d in tns['materials'](json.load(open(pm))):
            items.append({'label': 'terrain/' + d['name'], 'node': (d['name'], d['code'], [(n, k, a) for n, k, a in d['inputs']], [(n, kk) for n, kk, _ in d['outputs']], [d['include']] if d.get('include') else [])})
    return items


def source(item, mode):
    if 'ush' in item:
        entry = ('float4 main(float4 sv : SV_Position) : SV_Target { return 0; }\n' if mode == 'ps' else
                 'struct SM2Payload { float4 c; };\n[shader("closesthit")] void CHS(inout SM2Payload payload, BuiltInTriangleIntersectionAttributes attr) { payload.c = 0; }\n')
        return prelude(mode) + '\n' + inline(item['ush']) + '\n' + entry
    name, code, inputs, outputs, incs = item['node']
    text = ''.join('\n// ---- include %s\n%s\n' % (i, inline('#include "%s"' % i)) for i in incs)
    return wrap_node(name, code, inputs, outputs, text, mode)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-v', action='store_true')
    ap.add_argument('--only', help='substring of a label')
    ap.add_argument('--dump', help='write the wrapped sources into this directory')
    a = ap.parse_args()
    items = collect()
    if a.only:
        items = [i for i in items if a.only in i['label']]
    d = dxc.Dxc()
    results, errors = [], 0
    for item in items:
        for mode, args in (('ps', ['-E', 'main', '-T', 'ps_6_6', '-HV', '2021']), ('rt', ['-T', 'lib_6_6', '-HV', '2021'])):
            label = '%s [%s]' % (item['label'], mode)
            src = source(item, mode)
            if a.dump:
                Path(a.dump).mkdir(parents=True, exist_ok=True)
                (Path(a.dump) / (label.replace('/', '__').replace(' ', '') + '.hlsl')).write_text(src)
            ok, msg = d.compile(src, args)
            msgs = [l for l in msg.replace('\x00', '').splitlines() if l.strip() and 'DXIL signing library' not in l]
            errs = [l for l in msgs if ' error:' in l]
            if not ok or errs:
                errors += 1
            results.append({'label': label, 'ok': ok and not errs, 'warnings': sum(1 for l in msgs if ' warning:' in l), 'errors': errs[:8]})
            if a.v or not (ok and not errs):
                print('%-52s %s' % (label, 'OK' if ok and not errs else 'FAIL'))
                for l in (msgs if a.v else errs[:8]):
                    print('    ' + l)
    if MISSING_INCLUDES:
        errors += len(set(MISSING_INCLUDES))
        print('MISSING generated shader includes:', sorted(set(MISSING_INCLUDES)))
    print(json.dumps({'checked': len(results), 'failed': errors, 'failed_labels': [r['label'] for r in results if not r['ok']], 'missing_includes': sorted(set(MISSING_INCLUDES))}))
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()

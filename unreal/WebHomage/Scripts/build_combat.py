# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece P5 (combat): idempotent, headless rebuild of /Game/Combat (FX / street materials) and /Game/Tests/Combat/Combat_Street,
# plus the content it depends on (P3 hero clips in /Game/Traversal/HeroDev, P2 armed street thugs in /Game/Characters).
#
# Two modes in one file (same pattern as build_manhattan.py):
#   * plain python3 (YOUR editor closed):   python3 unreal/WebHomage/Scripts/build_combat.py [--steps cpp,traversal,characters,combat]
#       cpp         Scripts/build_editor.sh
#       traversal   P3 Scripts/build_traversal.py unchanged (HeroDev hero + all 80 GLB clips incl. the combat clips)
#       characters  P2 Scripts/build_characters.py unchanged, steps clean,tex,mat,mesh,citizens,rename,abp (no prep, no map), on a
#                   read-only staged copy of P2's derived inputs (P2_WT art + P2 scratch ueimport) in the combat scratch dir
#       combat      this file inside Unreal: materials + the Combat_Street map
#     Every Unreal process is a headless commandlet (-nullrhi -RenderOffScreen -NoSound, no GPU) of THIS worktree's project and
#     waits while 3+ Unreal instances run (RULES.md).
#   * inside Unreal (-run=pythonscript -script=<this file>): step 'combat'.
#
# Combat_Street: a lit test street (NOT the Manhattan city: see docs/night1/combat/round-01/NOTES.md for why). 30 m avenue along
# +X (building lines y = +-15 m), 4 m sidewalks with a 15 cm curb, 3 blocks of 30-90 m buildings each side, parked-car blocks,
# lamp posts and hydrants on the kerb (all outside the 14 m fight circle around the origin), warm afternoon sun along the street axis.
# Game mode AWHCombatGameMode: AWHCombatHero (the P3 traversal hero + combat) and AWHCombatDirector (fight, script, telemetry).
import os, sys, json, subprocess, time, shutil

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '/Users/midir/sm2-n1/combat/unreal/WebHomage/Scripts'
PROJ = os.path.dirname(HERE)
WT = os.path.dirname(os.path.dirname(PROJ))
UPROJECT = os.path.join(PROJ, 'WebHomage.uproject')
UE = '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor'
SCR = os.environ.get('SM2_COMBAT_SCR', '/Users/midir/sm2-n1/_scratch/combat')
CHAR_STAGE = os.path.join(SCR, 'chars')
P2_WT = os.environ.get('SM2_P2_WT', '/Users/midir/sm2-n1/characters')
P2_SCR = os.environ.get('SM2_P2_SCR', '/Users/midir/sm2-n1/_scratch/characters')
STEPS_ALL = ['cpp', 'traversal', 'characters', 'combat']
GPU_SLOT = '/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh'

try:
    import unreal  # noqa: F401
    IN_UE = hasattr(unreal, 'EditorAssetLibrary')
except ImportError:
    IN_UE = False


def log(*a):
    print('[build_combat %s]' % time.strftime('%H:%M:%S'), *a, flush=True)


# ================================================================================================ orchestrator (plain python3)
def sh(cmd, cwd=WT, log_name=None):
    log('$', cmd if isinstance(cmd, str) else ' '.join(cmd))
    out = open(os.path.join(SCR, 'logs', log_name), 'w') if log_name else None
    r = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), stdout=out or None, stderr=subprocess.STDOUT if out else None)
    if r.returncode != 0:
        raise SystemExit('command failed (%d): %s%s' % (r.returncode, cmd, ('  log: ' + out.name) if out else ''))


def safe_rmtree(p):
    """hard limit (RULES.md): deletes only inside this worktree or this piece's scratch dir"""
    p = os.path.realpath(p)
    if not (p.startswith(WT + '/') or p.startswith(os.path.realpath(SCR) + '/')):
        raise SystemExit('refusing to delete outside the worktree / scratch: ' + p)
    if os.path.isdir(p): shutil.rmtree(p)


def wait_slot():
    if os.environ.get('SM2_COMBAT_NOWAIT'): return   # inside a gpu_slot hold: the lock already enforces the cap
    while True:
        n = subprocess.run("pgrep -f '^/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor( |$)' | wc -l", shell=True, capture_output=True, text=True).stdout.strip()
        if int(n or 0) < 3: return
        log('3+ Unreal instances running, waiting 60 s'); time.sleep(60)


def ue_python(name, code, timeout=3600):
    if subprocess.run(['pgrep', '-f', UPROJECT], capture_output=True).returncode == 0:
        raise SystemExit('an Unreal process of this worktree is running; stop it first with /Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh (never SIGKILL a rendering engine)')
    jobs = os.path.join(SCR, 'jobs'); os.makedirs(jobs, exist_ok=True)
    job = os.path.join(jobs, name + '.py'); open(job, 'w').write(code)
    lg = os.path.join(SCR, 'logs', name + '.log')
    wait_slot()
    log('UE commandlet', name, '-> log', lg)
    t0 = time.time()
    with open(lg + '.stdout', 'w') as so:
        # r02 (RULES): every Unreal launch goes through the GPU slot lock, headless commandlets included
        r = subprocess.run([GPU_SLOT, 'capture', '--label', 'combat', '--timeout', '3600', '--', UE, UPROJECT, '-run=pythonscript', '-script=' + job,
                            '-unattended', '-nullrhi', '-nosplash', '-RenderOffScreen', '-NoSound', '-NoCrashReports', '-abslog=' + lg],
                           stdout=so, stderr=subprocess.STDOUT, timeout=timeout)
    txt = open(lg, errors='replace').read() if os.path.exists(lg) else ''
    bad = [l for l in txt.splitlines() if 'LogPython: Error' in l or 'Traceback' in l]
    log('UE commandlet %s: rc %d, %.0f s, %d python error lines' % (name, r.returncode, time.time() - t0, len(bad)))
    if bad:
        print('\n'.join(bad[:30]))
        raise SystemExit('python error in ' + name + ' (log ' + lg + ')')
    return txt


def exec_wrapper(script, prelude):
    return '%s\n__file__ = %r\nexec(compile(open(__file__).read(), __file__, "exec"))\n' % (prelude, script)


def step_cpp():
    sh([os.path.join(HERE, 'build_editor.sh')], log_name='build_editor.log')


def step_traversal():
    ue_python('traversal', exec_wrapper(os.path.join(HERE, 'build_traversal.py'), ''))


def stage_characters():
    """read-only copy of P2's derived (git-ignored) inputs; P2's own 'prep' is never run here"""
    src_art, src_glb = os.path.join(P2_WT, 'art/night1/characters'), os.path.join(P2_SCR, 'ueimport')
    for p in (src_art, src_glb):
        if not os.path.isdir(p): raise SystemExit('P2 derived inputs missing (P2 runs its prep in its own worktree): ' + p)
    os.makedirs(CHAR_STAGE, exist_ok=True)
    sh(['rsync', '-a', '--delete', src_art + '/', os.path.join(CHAR_STAGE, 'art') + '/'], log_name='chars_stage_art.log')
    sh(['rsync', '-a', '--delete', src_glb + '/', os.path.join(CHAR_STAGE, 'ueimport') + '/'], log_name='chars_stage_glb.log')
    head = subprocess.run(['git', '-C', P2_WT, 'log', '-1', '--format=%h %s'], capture_output=True, text=True).stdout.strip()
    json.dump({'p2_head': head, 'staged_at': time.strftime('%Y-%m-%d %H:%M:%S')}, open(os.path.join(CHAR_STAGE, 'STAGED.json'), 'w'))
    log('staged P2 inputs from', head)


def step_characters():
    stage_characters()
    for d in ('Content/Characters', 'Content/Tests/Characters'):
        safe_rmtree(os.path.join(PROJ, d))
    args = {'steps': 'clean,tex,mat,mesh,citizens,rename,abp', 'art': os.path.join(CHAR_STAGE, 'art'),
            'inputs': os.path.join(CHAR_STAGE, 'ueimport'), 'scratch': CHAR_STAGE}
    ue_python('characters', exec_wrapper(os.path.join(HERE, 'build_characters.py'), 'ARGS = %r' % args))


def step_combat():
    txt = ue_python('combat_map', exec_wrapper(os.path.abspath(__file__), ''))
    for l in txt.splitlines():
        if '[build_combat' in l: print(l.split('LogPython: ')[-1])


def main():
    import argparse
    ap = argparse.ArgumentParser(description='P5 combat: rebuild combat content + dependencies (headless)')
    ap.add_argument('--steps', default=','.join(STEPS_ALL))
    a = ap.parse_args()
    want = a.steps.split(',')
    bad = [s for s in want if s not in STEPS_ALL]
    if bad: raise SystemExit('unknown steps %s (known: %s)' % (bad, STEPS_ALL))
    os.makedirs(os.path.join(SCR, 'logs'), exist_ok=True)
    for s in STEPS_ALL:
        if s in want:
            t0 = time.time(); log('=== step', s)
            globals()['step_' + s]()
            log('=== step %s done in %.0f s' % (s, time.time() - t0))


# ================================================================================================ inside Unreal: step 'combat'
def build_in_unreal():
    EAL = unreal.EditorAssetLibrary
    MEL = unreal.MaterialEditingLibrary
    LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    AT = unreal.AssetToolsHelpers.get_asset_tools()
    MAT_DIR, MAP_DIR = '/Game/Combat/Materials', '/Game/Tests/Combat'
    MAP = MAP_DIR + '/Combat_Street'
    for need in ('/Game/Traversal/HeroDev/punch1', '/Game/Characters/Thug/Anims/A_Thug_thugPunch1', '/Game/Characters/People/SK_Street_Thug_Pistol'):
        if not EAL.does_asset_exist(need): raise RuntimeError('missing dependency %s (run steps traversal, characters first)' % need)

    # map packages are not removed by delete_directory in a commandlet: reuse the map (cleared) when it exists
    if EAL.does_asset_exist(MAP):
        assert LES.load_level(MAP)
        for a in EAS.get_all_level_actors(): EAS.destroy_actor(a)
        LES.save_current_level(); map_exists = True
    else:
        map_exists = False
    if EAL.does_directory_exist('/Game/Combat'): EAL.delete_directory('/Game/Combat')
    EAL.make_directory(MAT_DIR); EAL.make_directory(MAP_DIR)

    def new_material(name):
        return AT.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())

    def custom(mat, code, inputs, out_type, x, y):
        c = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, x, y)
        c.set_editor_property('code', code); c.set_editor_property('output_type', out_type)
        ins = []
        for n in inputs:
            ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
        c.set_editor_property('inputs', ins)
        return c

    def vparam(mat, name, val, x, y):
        p = MEL.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, x, y)
        p.set_editor_property('parameter_name', name); p.set_editor_property('default_value', unreal.LinearColor(*val)); return p

    def sparam(mat, name, val, x, y):
        p = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, x, y)
        p.set_editor_property('parameter_name', name); p.set_editor_property('default_value', val); return p

    # ---- M_CmbFX: unlit additive glow (hit sparks, flashes, tracers, muzzle, spider-sense). Color (HDR) x Opacity x soft edge.
    fx = new_material('M_CmbFX')
    fx.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE)
    fx.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    fx.set_editor_property('two_sided', True)
    c = vparam(fx, 'Color', (4, 3, 2, 1), -700, 0); o = sparam(fx, 'Opacity', 1.0, -700, 200)
    fres = MEL.create_material_expression(fx, unreal.MaterialExpressionFresnel, -700, 350)
    inv = MEL.create_material_expression(fx, unreal.MaterialExpressionOneMinus, -500, 350)
    MEL.connect_material_expressions(fres, '', inv, '')
    m1 = MEL.create_material_expression(fx, unreal.MaterialExpressionMultiply, -400, 100)
    MEL.connect_material_expressions(c, '', m1, 'A'); MEL.connect_material_expressions(o, '', m1, 'B')
    m2 = MEL.create_material_expression(fx, unreal.MaterialExpressionMultiply, -250, 200)
    MEL.connect_material_expressions(m1, '', m2, 'A'); MEL.connect_material_expressions(inv, '', m2, 'B')
    MEL.connect_material_property(m2, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(fx)

    # ---- M_CmbFlare (r03): the blow flare. Unlit additive, single-sided; a radial glow on a sphere: 1 - Fresnel(exponent 0.4, base 0) is ~1 at the
    # centre and falls to 0 at the rim (so the disc has no hard edge and no doubled back face). Color (HDR) x Opacity x falloff.
    fl = new_material('M_CmbFlare')
    fl.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE)
    fl.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    fl.set_editor_property('two_sided', False)
    try: fl.set_editor_property('disable_depth_test', True)   # a screen-space style flare: the same disc in front of or behind the bodies
    except Exception as ex: log('M_CmbFlare: disable_depth_test not settable (%s)' % ex)
    c = vparam(fl, 'Color', (2.0, 0.34, 0.05, 1), -700, 0); o = sparam(fl, 'Opacity', 1.0, -700, 200)
    fres = MEL.create_material_expression(fl, unreal.MaterialExpressionFresnel, -700, 350)
    try:
        fres.set_editor_property('exponent', 0.4); fres.set_editor_property('base_reflect_fraction', 0.0)
    except Exception as ex:
        log('M_CmbFlare: fresnel exponent not settable (%s): the flare falls off like M_CmbFX' % ex)
    inv = MEL.create_material_expression(fl, unreal.MaterialExpressionOneMinus, -500, 350)
    MEL.connect_material_expressions(fres, '', inv, '')
    m1 = MEL.create_material_expression(fl, unreal.MaterialExpressionMultiply, -400, 100)
    MEL.connect_material_expressions(c, '', m1, 'A'); MEL.connect_material_expressions(o, '', m1, 'B')
    m2 = MEL.create_material_expression(fl, unreal.MaterialExpressionMultiply, -250, 200)
    MEL.connect_material_expressions(m1, '', m2, 'A'); MEL.connect_material_expressions(inv, '', m2, 'B')
    MEL.connect_material_property(m2, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(fl)

    # ---- M_CmbTrans: lit translucent (web cocoons / splats, dust puffs). Color, Opacity, Emissive.
    tr = new_material('M_CmbTrans')
    tr.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    tr.set_editor_property('two_sided', True)
    try: tr.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE)
    except Exception: pass
    c = vparam(tr, 'Color', (0.9, 0.9, 0.92, 1), -700, 0); o = sparam(tr, 'Opacity', 0.8, -700, 200); e = sparam(tr, 'Emissive', 0.0, -700, 350)
    MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(o, '', unreal.MaterialProperty.MP_OPACITY)
    me = MEL.create_material_expression(tr, unreal.MaterialExpressionMultiply, -400, 300)
    MEL.connect_material_expressions(c, '', me, 'A'); MEL.connect_material_expressions(e, '', me, 'B')
    MEL.connect_material_property(me, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    r = MEL.create_material_expression(tr, unreal.MaterialExpressionConstant, -400, 450); r.set_editor_property('r', 0.7)
    MEL.connect_material_property(r, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(tr)

    # ---- M_CmbSolid: lit opaque colour (web strand core, props, pistol debris, street furniture). Color, Rough, Emissive.
    so = new_material('M_CmbSolid')
    c = vparam(so, 'Color', (0.5, 0.5, 0.5, 1), -700, 0); rr = sparam(so, 'Rough', 0.6, -700, 200); e = sparam(so, 'Emissive', 0.0, -700, 350)
    mt = sparam(so, 'Metal', 0.0, -700, 500)
    MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rr, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(mt, '', unreal.MaterialProperty.MP_METALLIC)
    me = MEL.create_material_expression(so, unreal.MaterialExpressionMultiply, -400, 300)
    MEL.connect_material_expressions(c, '', me, 'A'); MEL.connect_material_expressions(e, '', me, 'B')
    MEL.connect_material_property(me, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(so)

    # ---- street: facade (procedural windows, storefront band), asphalt (lanes, crosswalk), sidewalk (slabs)
    FACADE = r"""
float3 p = WP / 100.0;
float3 o = floor(OP / 500.0);
float h = frac(sin(dot(o.xy, float2(12.9898, 78.233))) * 43758.5453);
float h2 = frac(h * 91.7);
float ax = abs(N.x) > abs(N.y) ? p.y : p.x;
float u = frac(ax / 3.2), v = frac((p.z - 4.5) / 3.6);
float win = step(0.18, u) * step(u, 0.82) * step(0.28, v) * step(v, 0.86) * step(4.6, p.z);
if (abs(N.z) > 0.5) win = 0.0;
float3 wall = lerp(float3(0.30, 0.17, 0.12), float3(0.52, 0.45, 0.36), h);
wall = lerp(wall, float3(0.20, 0.21, 0.23), step(0.75, h2));
float lit = frac(sin(dot(floor(float2(ax / 3.2, (p.z - 4.5) / 3.6)), float2(3.1, 17.7)) + h * 7.0) * 9173.1);
float3 glass = lerp(float3(0.015, 0.02, 0.03), float3(0.10, 0.12, 0.15), lit);
float3 c = lerp(wall, glass, win);
float cornice = step(abs(frac((p.z - 4.5) / 3.6) - 0.02), 0.02) * step(4.4, p.z);
c *= 1.0 - 0.35 * cornice;
if (p.z < 4.4 && abs(N.z) < 0.5) {
  float bay = frac(ax / 6.0);
  float3 shop = lerp(float3(0.03, 0.035, 0.04), float3(0.22, 0.20, 0.17), step(0.82, bay));
  shop = lerp(shop, wall * 0.6, step(3.5, p.z));
  c = shop;
}
if (N.z > 0.5) c = float3(0.18, 0.17, 0.16);
return c;
"""
    FROUGH = r"""
float3 p = WP / 100.0;
float ax = abs(N.x) > abs(N.y) ? p.y : p.x;
float u = frac(ax / 3.2), v = frac((p.z - 4.5) / 3.6);
float win = step(0.18, u) * step(u, 0.82) * step(0.28, v) * step(v, 0.86) * step(4.6, p.z);
if (p.z < 4.4 && step(0.82, frac(ax / 6.0)) < 0.5 && p.z < 3.5) win = 1.0;
if (abs(N.z) > 0.5) win = 0.0;
return lerp(0.82, 0.08, win);
"""
    fac = new_material('M_CmbFacade')
    wp = MEL.create_material_expression(fac, unreal.MaterialExpressionWorldPosition, -900, 0)
    op = MEL.create_material_expression(fac, unreal.MaterialExpressionObjectPositionWS, -900, 150)
    nn = MEL.create_material_expression(fac, unreal.MaterialExpressionVertexNormalWS, -900, 300)
    fc = custom(fac, FACADE, ['WP', 'OP', 'N'], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, 0)
    fr = custom(fac, FROUGH, ['WP', 'N'], unreal.CustomMaterialOutputType.CMOT_FLOAT1, -500, 250)
    for node in (fc,):
        MEL.connect_material_expressions(wp, '', node, 'WP'); MEL.connect_material_expressions(op, '', node, 'OP'); MEL.connect_material_expressions(nn, '', node, 'N')
    MEL.connect_material_expressions(wp, '', fr, 'WP'); MEL.connect_material_expressions(nn, '', fr, 'N')
    MEL.connect_material_property(fc, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(fr, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(fac)

    ROAD = r"""
float3 p = WP / 100.0;
float n = frac(sin(dot(floor(p.xy * 3.0), float2(12.9898, 78.233))) * 43758.5453);
float n2 = frac(sin(dot(floor(p.xy * 0.37), float2(4.1, 91.7))) * 1731.3);
float3 c = float3(0.055, 0.055, 0.06) * (0.85 + 0.3 * n) * (0.9 + 0.2 * n2);
float ay = abs(p.y);
if (ay < 0.22 && ay > 0.06) c = float3(0.55, 0.42, 0.06);
float dash = step(0.55, frac(p.x / 9.0));
if (abs(ay - 5.5) < 0.07) c = lerp(c, float3(0.62, 0.62, 0.6), dash);
float xw = abs(p.x - 42.0);
if (xw < 2.5 && ay < 11.0 && frac(p.y / 1.2) < 0.55) c = float3(0.6, 0.6, 0.58);
return c;
"""
    road = new_material('M_CmbRoad')
    gwp = MEL.create_material_expression(road, unreal.MaterialExpressionWorldPosition, -700, 0)
    gc = custom(road, ROAD, ['WP'], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -400, 0)
    MEL.connect_material_expressions(gwp, '', gc, 'WP')
    MEL.connect_material_property(gc, '', unreal.MaterialProperty.MP_BASE_COLOR)
    rr = MEL.create_material_expression(road, unreal.MaterialExpressionConstant, -400, 200); rr.set_editor_property('r', 0.78)
    MEL.connect_material_property(rr, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(road)

    WALK = r"""
float3 p = WP / 100.0;
float2 g = frac(p.xy / 1.5);
float joint = step(g.x, 0.02) + step(g.y, 0.02);
float n = frac(sin(dot(floor(p.xy / 1.5), float2(12.9898, 78.233))) * 43758.5453);
float3 c = float3(0.30, 0.29, 0.27) * (0.9 + 0.15 * n);
c *= 1.0 - 0.45 * saturate(joint);
return c;
"""
    walk = new_material('M_CmbSidewalk')
    swp = MEL.create_material_expression(walk, unreal.MaterialExpressionWorldPosition, -700, 0)
    sc_ = custom(walk, WALK, ['WP'], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -400, 0)
    MEL.connect_material_expressions(swp, '', sc_, 'WP')
    MEL.connect_material_property(sc_, '', unreal.MaterialProperty.MP_BASE_COLOR)
    sr = MEL.create_material_expression(walk, unreal.MaterialExpressionConstant, -400, 200); sr.set_editor_property('r', 0.85)
    MEL.connect_material_property(sr, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(walk)

    def mi(name, parent, vec=None, sca=None):
        m = AT.create_asset(name, MAT_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        m.set_editor_property('parent', parent)
        for k, v in (vec or {}).items(): unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(m, k, unreal.LinearColor(*v))
        for k, v in (sca or {}).items(): unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(m, k, v)
        EAL.save_loaded_asset(m); return m

    car_mats = [mi('MI_CmbCar%d' % i, so, {'Color': col}, {'Rough': 0.3, 'Metal': 0.6}) for i, col in enumerate(
        [(0.35, 0.03, 0.03, 1), (0.05, 0.08, 0.14, 1), (0.6, 0.55, 0.45, 1), (0.03, 0.03, 0.035, 1), (0.8, 0.62, 0.05, 1)])]
    metal = mi('MI_CmbPole', so, {'Color': (0.05, 0.06, 0.055, 1)}, {'Rough': 0.45, 'Metal': 0.8})
    hydrant = mi('MI_CmbHydrant', so, {'Color': (0.55, 0.08, 0.04, 1)}, {'Rough': 0.5})
    glass = mi('MI_CmbCarGlass', so, {'Color': (0.02, 0.025, 0.03, 1)}, {'Rough': 0.1, 'Metal': 0.3})
    lamp = mi('MI_CmbLamp', so, {'Color': (1.0, 0.8, 0.55, 1)}, {'Emissive': 6.0})
    curb = mi('MI_CmbCurb', so, {'Color': (0.36, 0.35, 0.33, 1)}, {'Rough': 0.8})
    for m in (fx, tr, so, fac, road, walk): EAL.save_loaded_asset(m)

    # ---------------------------------------------------------------------------------------------- map
    if map_exists: assert LES.load_level(MAP)
    else: assert LES.new_level(MAP)
    CUBE = unreal.load_asset('/Engine/BasicShapes/Cube.Cube'); CYL = unreal.load_asset('/Engine/BasicShapes/Cylinder.Cylinder')
    SPH = unreal.load_asset('/Engine/BasicShapes/Sphere.Sphere')

    def spawn(cls, loc=(0, 0, 0), rot=(0, 0, 0), label=None):
        a = EAS.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(*rot))
        if label: a.set_actor_label(label)
        return a

    LAYOUT = []

    def box(x0, y0, z0, x1, y1, z1, label, mat, mesh=CUBE, folder='Street'):
        """axis-aligned box in METRES (min / max corners)"""
        LAYOUT.append({'label': label, 'min': [round(x0, 2), round(y0, 2), round(z0, 2)], 'max': [round(x1, 2), round(y1, 2), round(z1, 2)]})
        a = spawn(unreal.StaticMeshActor, ((x0 + x1) * 50.0, (y0 + y1) * 50.0, (z0 + z1) * 50.0), label=label)
        c = a.static_mesh_component
        c.set_static_mesh(mesh); c.set_material(0, mat)
        a.set_actor_scale3d(unreal.Vector(x1 - x0, y1 - y0, z1 - z0))
        a.set_folder_path(folder)
        return a

    import random
    rng = random.Random(20260929)
    # ground (road surface top z = 0, WHGround: never holds a web), sidewalks top z = 0.15
    g = box(-400, -200, -1, 400, 200, 0, 'Ground', road); g.tags = [unreal.Name('WHGround')]
    for side in (-1, 1):
        y0, y1 = (-15, -11) if side < 0 else (11, 15)
        w = box(-400, y0, 0, 400, y1, 0.15, 'Sidewalk_%s' % ('S' if side < 0 else 'N'), walk); w.tags = [unreal.Name('WHGround')]
        cy = -11.1 if side < 0 else 11.1
        box(-400, min(cy, cy + 0.2 * side), 0, 400, max(cy, cy + 0.2 * side), 0.16, 'Curb_%s' % ('S' if side < 0 else 'N'), curb).tags = [unreal.Name('WHGround')]
    # buildings: blocks 60 m + 14 m cross streets, building line |y| = 15, depth 30, 2nd row behind a 12 m street
    blk = 0
    x = -200.0
    while x < 200.0:
        for side in (-1, 1):
            n = rng.choice([2, 3, 3])
            cuts = sorted(rng.uniform(0.25, 0.75) * 60 for _ in range(n - 1))
            edges = [0.0] + cuts + [60.0]
            for k in range(n):
                bx0, bx1 = x + edges[k], x + edges[k + 1]
                y0, y1 = (-45.0, -15.0) if side < 0 else (15.0, 45.0)
                h = rng.choice([rng.uniform(22, 40), rng.uniform(35, 70), rng.uniform(55, 95)])
                box(bx0, y0, 0, bx1, y1, h, 'B%02d_%s%d' % (blk, 'S' if side < 0 else 'N', k), fac, folder='Buildings')
                if rng.random() < 0.5:   # rooftop box (water tank / plant room)
                    cx, cyy = (bx0 + bx1) / 2 + rng.uniform(-4, 4), (y0 + y1) / 2 + rng.uniform(-5, 5)
                    box(cx - 2.5, cyy - 2.5, h, cx + 2.5, cyy + 2.5, h + rng.uniform(3, 6), 'B%02d_%s%d_Roof' % (blk, 'S' if side < 0 else 'N', k), fac, CYL if rng.random() < 0.5 else CUBE, 'Buildings')
            y0, y1 = (-87.0, -57.0) if side < 0 else (57.0, 87.0)
            box(x, y0, 0, x + 60, y1, rng.uniform(40, 120), 'R2_%02d_%s' % (blk, 'S' if side < 0 else 'N'), fac, folder='Buildings')
        x += 74.0
        blk += 1

    # street furniture on the kerbs (outside the 14 m fight circle around the origin, x in [-14, 14] kept clear of cars)
    for i, lx in enumerate(range(-120, 121, 24)):
        for side in (-1, 1):
            y = side * 11.6
            box(lx - 0.09, y - 0.09, 0.15, lx + 0.09, y + 0.09, 6.8, 'Lamp%02d_%s_Pole' % (i, 'S' if side < 0 else 'N'), metal, CYL, 'Furniture')
            box(lx - 0.09, y - side * 1.4 - 0.09, 6.7, lx + 0.09, y + 0.09, 6.82, 'Lamp%02d_%s_Arm' % (i, 'S' if side < 0 else 'N'), metal, CUBE, 'Furniture')
            box(lx - 0.25, y - side * 1.4 - 0.18, 6.5, lx + 0.25, y - side * 1.4 + 0.18, 6.7, 'Lamp%02d_%s_Head' % (i, 'S' if side < 0 else 'N'), lamp, CUBE, 'Furniture')
    for i, (hx, side) in enumerate([(-30, -1), (22, 1), (58, -1), (-66, 1)]):
        y = side * 11.8
        box(hx - 0.18, y - 0.18, 0.15, hx + 0.18, y + 0.18, 0.85, 'Hydrant%d' % i, hydrant, CYL, 'Furniture')

    def car(cx, cy, yaw_x, label, mat):
        L, W = 4.6, 1.85
        if yaw_x: x0, x1, y0, y1 = cx - L / 2, cx + L / 2, cy - W / 2, cy + W / 2
        else: x0, x1, y0, y1 = cx - W / 2, cx + W / 2, cy - L / 2, cy + L / 2
        box(x0, y0, 0.25, x1, y1, 0.95, label + '_Body', mat, CUBE, 'Cars')
        sx, sy = (x1 - x0) * 0.22, (y1 - y0) * 0.06
        box(x0 + sx, y0 + sy, 0.95, x1 - sx * 1.2, y1 - sy, 1.45, label + '_Cabin', glass, CUBE, 'Cars')
        for wx in (x0 + 0.8, x1 - 0.8):
            for wy in (y0 + 0.05, y1 - 0.25):
                box(wx - 0.33, wy, 0.0, wx + 0.33, wy + 0.2, 0.66, label + '_Wheel', metal, CUBE, 'Cars')
    for i, (cx, side) in enumerate([(-38, -1), (-26, -1), (24, -1), (36, 1), (-44, 1), (52, 1), (-60, -1), (66, -1)]):
        car(cx, side * 9.6, True, 'Car%02d' % i, car_mats[i % len(car_mats)])

    # ---- lighting (r02, look sweep lk1-lk4 in docs/night1/combat/round-02/NOTES.md). r01: white sky + low contrast flattened the
    # silhouettes; the first r02 dusk (sun 7 deg, sky-lit) went the other way: everything blue-black. Sky-lit shade is blue whatever the
    # sun colour, so the sun has to be the key: a warm afternoon sun 32 deg high, along the street axis (the canyon does not shade the
    # floor), real cast shadows, a dimmed sky light for the shade, thin dark haze (a bright fog luminance washed everything to pale blue-grey: cap2). Lamps stay unlit (daylight).
    sun = spawn(unreal.DirectionalLight, (0, 0, 50000), (0, -32, 180), 'Sun')
    sc = sun.get_component_by_class(unreal.DirectionalLightComponent)
    sc.set_editor_property('intensity', 10.0)
    sc.set_editor_property('light_color', unreal.Color(255, 200, 150, 255))
    sc.set_editor_property('atmosphere_sun_light', True)
    sc.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
    spawn(unreal.SkyAtmosphere, (0, 0, 0), label='SkyAtmosphere')
    sky = spawn(unreal.SkyLight, (0, 0, 1000), label='SkyLight')
    skc = sky.get_component_by_class(unreal.SkyLightComponent)
    skc.set_editor_property('real_time_capture', True); skc.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
    skc.set_editor_property('intensity', 0.6)
    fog = spawn(unreal.ExponentialHeightFog, (0, 0, 0), label='HeightFog')
    fgc = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    fgc.set_editor_property('fog_density', 0.003)
    try: fgc.set_editor_property('fog_inscattering_luminance', unreal.LinearColor(0.08, 0.07, 0.09, 1.0))
    except Exception as ex: log('fog colour not set: %s' % ex)
    spawn(unreal.VolumetricCloud, (0, 0, 0), label='VolumetricCloud')
    ppv = spawn(unreal.PostProcessVolume, (0, 0, 0), label='GlobalPPV'); ppv.set_editor_property('unbound', True)
    try:
        pps = ppv.get_editor_property('settings')
        for k, v in (('override_auto_exposure_bias', True), ('auto_exposure_bias', -0.3), ('override_vignette_intensity', True), ('vignette_intensity', 0.3),
                     ('override_color_contrast', True), ('color_contrast', unreal.Vector4(1.08, 1.08, 1.08, 1.08)),
                     ('override_color_saturation', True), ('color_saturation', unreal.Vector4(1.1, 1.1, 1.1, 1.0))):
            pps.set_editor_property(k, v)
        ppv.set_editor_property('settings', pps)
    except Exception as ex: log('ppv grade not set: %s' % ex)
    # fight fill: a very soft cool fill from the shadow side (low intensity, not a stage light)
    fill = spawn(unreal.RectLight, (0, -900, 900), (0, -30, 90), 'FightFill')
    fc_ = fill.get_component_by_class(unreal.RectLightComponent)
    fc_.set_editor_property('intensity', 5.0); fc_.set_editor_property('attenuation_radius', 3000.0)
    fc_.set_editor_property('source_width', 1200.0); fc_.set_editor_property('source_height', 600.0)
    fc_.set_editor_property('light_color', unreal.Color(200, 215, 255, 255)); fc_.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
    # player start: hero at x = -8 m on the centre line facing +X (the fight spawns ahead of him)
    spawn(unreal.PlayerStart, (-800, 0, 120), (0, 0, 0), 'PlayerStart')

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    gm = unreal.load_class(None, '/Script/WebHomage.WHCombatGameMode')
    assert gm, 'WHCombatGameMode class missing: build the C++ module first'
    world.get_world_settings().set_editor_property('default_game_mode', gm)
    assert LES.save_current_level(), 'save failed'
    out = os.path.normpath(os.path.join(WT, 'docs', 'night1', 'combat', 'combat_street_layout.json'))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({'units': 'm', 'axes': 'UE (X along the street, Z up)', 'boxes': LAYOUT}, open(out, 'w'), indent=0)
    log('COMBAT_STREET_OK actors=%d boxes=%d' % (len(EAS.get_all_level_actors()), len(LAYOUT)))


if IN_UE:
    build_in_unreal()
elif __name__ == '__main__':
    main()

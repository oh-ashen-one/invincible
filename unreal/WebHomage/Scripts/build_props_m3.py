# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Builder PA (final refinement loop, owner brief 2026-10-08): the supplied-GLB integration exception. Idempotent, headless.
# Approved scope (docs/night1/final/assets/PLAN.md, orchestrator decision 2026-10-08): new placements of 7 supplied assets only:
#   blue oil drum, wooden crate (1), pigeon (1), seagull (1), orange tabby cat (1), squirrel (1), rat (1).
#
# Two modes in one file (same pattern as build_life.py / build_manhattan.py):
#   * plain python3 (YOUR editor closed):  python3 unreal/WebHomage/Scripts/build_props_m3.py [--steps prep,content,map,validate]
#       prep       CPU only: tools/final/assets/prep_props_m3.py (Blender background decimation, no render) + place_props_m3.py (placements.json)
#       content    UE commandlet: /Game/PropsM3/{Textures,Meshes,Materials} (textures, LOD0/1 static meshes, M_PropM3 / M_PropM3_Critter + instances)
#       map        UE commandlet: /Game/PropsM3/Maps/PropsM3_Island (THE deliverable level: per-kind per-256 m-tile HISM actors) + PropsM3_Test
#       validate   UE commandlet: asserts every PropsM3 component is a no-collision HISM with 'prop' in its actor/component name, counts = placements.json
#       checkmaps  UE commandlet: temporary verification copies /Game/PropsM3/Maps/PropsM3_IslandCheck_{Golden,Night} of the island showcase maps
#                  + a LevelInstance of PropsM3_Island (what the orchestrator's wiring will do); never touches the originals
#       dropcheck  UE commandlet: deletes the PropsM3_IslandCheck_* maps (+ their external-actor folders)
#     Every Unreal process is a headless commandlet (-nullrhi) of THIS worktree's project launched through tools/gpu/gpu_slot.sh capture on the
#     shared coordinator ~/.cache/gpu-slot (queues behind other holders; never bypasses PAUSED). SM2_STRICT=1: a required asset that was not produced
#     prints SM2_BUILD_FAILED and raises; success prints 'SM2_BUILD_OK: build_props_m3.py' last.
#   * inside Unreal (-run=pythonscript -script=<this file>, env SM2_PROPS_M3_STEPS=clean,content,map,validate,checkmaps,dropcheck)
# Collision / traversal policy (PLAN.md section 5): static meshes without any collision body, HISM components with the NoCollision profile,
# 'prop' in every actor label / component name / mesh name (FWebTravWorld::IsExcludedName tokens '_prop' / 'prop_'), never tagged WHGround.
# FWebTravWorld (SolidMode 2) lists them as 'excluded-ism'; with -WHTravIsmSolid=1 they are still 'excluded' by name.
# Nothing here edits an existing map, build_manhattan.py or C++: the orchestrator adds PropsM3_Island to the island maps.
import os, sys, json, math, time, subprocess, fcntl, glob, shutil

HOME = os.path.expanduser('~')
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.path.join(HOME, 'spider-man-2/unreal/WebHomage/Scripts')
PROJ = os.path.dirname(HERE)
WT = os.path.dirname(os.path.dirname(PROJ))
UPROJECT = os.path.join(PROJ, 'WebHomage.uproject')
sys.path.insert(0, os.environ.get('SM2_SCRIPTS_DIR') or HERE)
import sm2_common  # noqa: E402
_B = sm2_common.Build('build_props_m3.py')
UE = '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor'
SCR = os.environ.get('SM2_PROPS_M3_SCR', os.path.join(HOME, 'sm2-n1/_scratch/final/assets'))
PREP = os.path.join(SCR, 'prep')
GPU_ROOT = os.path.join(HOME, '.cache', 'gpu-slot')
GPU_SLOT = os.path.join(WT, 'tools', 'gpu', 'gpu_slot.sh')
ASSET_PY = os.path.join(HOME, '.local/share/m5-game-tools/asset-python/bin/python3')
STEPS_ALL = ['prep', 'content', 'map', 'validate', 'checkmaps', 'dropcheck']
STEPS_DEFAULT = ['prep', 'content', 'map', 'validate']
ROOT = '/Game/PropsM3'
LEVEL = ROOT + '/Maps/PropsM3_Island'
TEST = ROOT + '/Maps/PropsM3_Test'
CHECK = {'Golden': ('/Game/Showcase/Maps/Manhattan_Island', ROOT + '/Maps/PropsM3_IslandCheck_Golden'),
         'Night': ('/Game/Showcase/Maps/Manhattan_Island_Night', ROOT + '/Maps/PropsM3_IslandCheck_Night')}
KINDS = ['oildrum', 'crate', 'pigeon', 'gull', 'cat', 'squirrel', 'rat']
ANIMALS = ('pigeon', 'gull', 'cat', 'squirrel', 'rat')
# HISM cull (cm): small animals vanish beyond 70 m (a pigeon is ~3 px there at 1080p), larger props later
CULL = {'pigeon': 7000, 'squirrel': 6000, 'rat': 5000, 'cat': 9000, 'gull': 9000, 'crate': 15000, 'oildrum': 15000}
SHADOW = {'pigeon': True, 'squirrel': True, 'rat': True, 'cat': True, 'gull': True, 'crate': True, 'oildrum': True}
ROUGH = {'oildrum': (0.45, 0.35), 'crate': (0.85, 0.0)}   # (roughness, metallic); animals 0.8 / 0
WP_TILE = 256.0

try:
    import unreal  # noqa: F401
    IN_UE = hasattr(unreal, 'EditorAssetLibrary')
except ImportError:
    IN_UE = False


# ================================================================================================ orchestrator (plain python3)
def log(*a):
    print('[build_props_m3 %s]' % time.strftime('%H:%M:%S'), *a, flush=True)


def sh(cmd, log_name):
    os.makedirs(os.path.join(SCR, 'logs'), exist_ok=True)
    lg = os.path.join(SCR, 'logs', log_name)
    log('$', ' '.join(cmd), '->', lg)
    with open(lg, 'w') as out:
        r = subprocess.run(cmd, cwd=WT, stdout=out, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        print(open(lg, errors='replace').read()[-2000:])
        raise SystemExit('command failed (%d): %s (log %s)' % (r.returncode, ' '.join(cmd), lg))


def step_prep():
    py = ASSET_PY if os.path.exists(ASSET_PY) else sys.executable
    sh([py, os.path.join(WT, 'tools/final/assets/prep_props_m3.py'), '--out', PREP], 'prep_meshes.log')
    sh([py, os.path.join(WT, 'tools/final/assets/place_props_m3.py'), '--out', PREP], 'prep_place.log')
    a = json.load(open(os.path.join(PREP, 'audit.json')))
    log('placements', a['counts'], 'checks', a['checks'])


def admission():
    """refusals only (gpu_slot.sh does the queueing): PAUSED, a missing coordinator, a stuck-exiting Unreal"""
    if os.environ.get('GPU_SLOT_DIR') and os.path.realpath(os.environ['GPU_SLOT_DIR']) != os.path.realpath(GPU_ROOT):
        raise SystemExit('refusing GPU_SLOT_DIR=%s: the only shared coordinator root is %s' % (os.environ['GPU_SLOT_DIR'], GPU_ROOT))
    if os.path.exists(os.path.join(GPU_ROOT, 'PAUSED')):
        raise SystemExit('shared GPU PAUSED; this build never clears it')
    if not all(os.path.isdir(os.path.join(GPU_ROOT, d)) for d in ('locks', 'holders', 'queue')):
        raise SystemExit('shared coordinator %s is unavailable; do not create a parallel namespace' % GPU_ROOT)
    for line in subprocess.check_output(['ps', '-axo', 'pid=,stat=,comm='], text=True).splitlines():
        p = line.split(None, 2)
        if len(p) == 3 and 'UnrealEditor' in p[2] and ('E' in p[1] or 'Z' in p[1]):
            raise SystemExit('an UnrealEditor process is stuck exiting; review ownership first: ' + line.strip())


def stop_ours(proc):
    if proc.poll() is not None: return
    proc.terminate(); t = time.monotonic()
    while proc.poll() is None and time.monotonic() - t < 60: time.sleep(0.5)
    if proc.poll() is None: log('child ignored SIGTERM for 60 s: SIGKILL (last resort)'); proc.kill(); proc.wait()


def ue_python(name, steps, timeout=2400):
    admission()
    os.makedirs(os.path.join(SCR, 'logs'), exist_ok=True)
    lock = open(os.path.join(SCR, 'commandlet.lock'), 'a+')
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: raise SystemExit('another build_props_m3 commandlet is already running')
    lg = os.path.join(SCR, 'logs', name + '.log')
    if os.path.exists(lg): os.remove(lg)
    cmd = [GPU_SLOT, 'capture', '--label', 'sm2-propsm3-' + name, '--timeout', '3600', '--', UE, UPROJECT, '-run=pythonscript',
           '-script=' + os.path.abspath(__file__), '-unattended', '-nullrhi', '-nosplash', '-RenderOffScreen', '-NoSound', '-NoCrashReports', '-abslog=' + lg]
    env = {**os.environ, 'GPU_SLOT_DIR': GPU_ROOT, 'GPU_SLOT_CAPTURE_MAX_HOLD': str(timeout), 'SM2_STRICT': '1', 'SM2_SCRIPTS_DIR': HERE,
           'SM2_PROPS_M3_STEPS': steps, 'SM2_PROPS_M3_SCR': SCR}
    log('UE commandlet', name, 'steps', steps, '-> log', lg, '(gpu_slot capture; waits in the shared queue)')
    t0 = time.time(); proc = None
    try:
        with open(lg + '.stdout', 'w') as so:
            proc = subprocess.Popen(cmd, env=env, stdout=so, stderr=subprocess.STDOUT)
            deadline = time.monotonic() + 3600 + timeout + 120
            while proc.poll() is None:
                if time.monotonic() > deadline: stop_ours(proc); raise SystemExit('commandlet %s exceeded its deadline (log %s)' % (name, lg))
                time.sleep(1)
    except BaseException:
        if proc is not None: stop_ours(proc)
        raise
    finally:
        lock.close()
    rc = proc.returncode
    txt = open(lg, errors='replace').read() if os.path.exists(lg) else ''
    for l in txt.splitlines():
        if '[build_props_m3' in l or 'SM2_' in l: print(l.split('LogPython: ')[-1])
    bad = [l for l in txt.splitlines() if 'LogPython: Error' in l or 'Traceback' in l or 'SM2_BUILD_FAILED' in l]
    ok = 'SM2_BUILD_OK: build_props_m3.py' in txt
    log('UE commandlet %s: rc %d, %.0f s, %d error lines, success sentinel %s' % (name, rc, time.time() - t0, len(bad), 'yes' if ok else 'NO'))
    if rc == 75: raise SystemExit('GPU admission timed out (command not run)')
    if bad: print('\n'.join(bad[:30]))
    if rc != 0 or bad or not ok: raise SystemExit('SM2_BUILD_FAILED: commandlet %s (rc %d, log %s)' % (name, rc, lg))


def main():
    import argparse
    ap = argparse.ArgumentParser(description='PA: /Game/PropsM3 (supplied GLB props / animals) headless build')
    ap.add_argument('--steps', default=','.join(STEPS_DEFAULT))
    a = ap.parse_args()
    want = a.steps.split(',')
    bad = [s for s in want if s not in STEPS_ALL]
    if bad: raise SystemExit('unknown steps %s (known: %s)' % (bad, STEPS_ALL))
    t0 = time.time()
    if 'prep' in want: step_prep()
    ue = [s for s in ('content', 'map', 'validate', 'checkmaps', 'dropcheck') if s in want]
    if ue: ue_python('propsm3_' + '_'.join(ue), ','.join((['clean'] if 'content' in ue else []) + ue))
    log('SM2_BUILD_OK: build_props_m3.py (orchestrator, %.0f s)' % (time.time() - t0))


# ================================================================================================ inside Unreal
def build_in_ue():
    STEPS = set(os.environ.get('SM2_PROPS_M3_STEPS', 'clean,content,map,validate').split(','))
    AT = unreal.AssetToolsHelpers.get_asset_tools()
    EAL = unreal.EditorAssetLibrary
    MEL = unreal.MaterialEditingLibrary
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    try: unreal.SystemLibrary.execute_console_command(None, 'Module Load StaticMeshEditor')
    except Exception: pass
    sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    T0 = time.time()
    def L(*a): print('[build_props_m3 %5.0fs]' % (time.time() - T0), *a, flush=True)
    def load(p): return unreal.load_asset(p)
    def world(): return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    meta = json.load(open(os.path.join(PREP, 'meta.json')))
    place = json.load(open(os.path.join(PREP, 'placements.json')))['items']

    def U(x, y, z): return unreal.Vector(x * 100.0, z * 100.0, y * 100.0)   # browser metres (x east, y up, z south) -> UE cm

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    def add_component(actor, cls):
        if hasattr(actor, 'add_component_by_class'):
            return actor.add_component_by_class(cls, False, unreal.Transform(), False)
        root = sds.k2_gather_subobject_data_for_instance(actor)[0]
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=cls, blueprint_context=None))
        return unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h))

    def no_collision(c):
        c.set_collision_profile_name('NoCollision'); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        for k, v in (('generate_overlap_events', False), ('can_ever_affect_navigation', False), ('can_character_step_up_on', unreal.CanBeCharacterBase.ECB_NO)):
            try: c.set_editor_property(k, v)
            except Exception as ex: _B.warn('component property %s' % k, ex)

    KEEP = ('WorldSettings', 'Brush', 'DefaultPhysicsVolume', 'GameplayDebuggerCategoryReplicator', 'WorldDataLayers', 'WorldPartitionMiniMap', 'LevelBounds')
    def open_level(path):
        """idempotent: an existing level is opened and emptied of its own actors, else created (non World Partition)"""
        if EAL.does_asset_exist(path):
            unreal.EditorLoadingAndSavingUtils.load_map(path)
            for a in eas.get_all_level_actors():
                if a.get_class().get_name() not in KEEP and a.get_path_name().startswith(path + '.'): eas.destroy_actor(a)
        else:
            if not les.new_level(path): raise RuntimeError('could not create level ' + path)
        return world()

    # -------------------------------------------------------------------------------------------- clean
    if 'clean' in STEPS:
        unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
        for d in ('Textures', 'Meshes', 'Materials'):
            if EAL.does_directory_exist(ROOT + '/' + d):
                for ap in EAL.list_assets(ROOT + '/' + d, recursive=True, include_folder=False):
                    EAL.delete_asset(ap.split('.')[0])
                if not EAL.delete_directory(ROOT + '/' + d): _B.warn('directory not removed (re-imports replace its assets): ' + ROOT + '/' + d)
        L('cleaned', ROOT, '(Textures, Meshes, Materials; maps are re-opened and emptied by the map step)')

    # -------------------------------------------------------------------------------------------- content
    if 'content' in STEPS:
        TD, MD, XD = ROOT + '/Textures', ROOT + '/Meshes', ROOT + '/Materials'
        # textures
        for k in KINDS:
            f = os.path.join(PREP, 'T_PropM3_%s_D.png' % k)
            t = unreal.AssetImportTask(); t.filename = f; t.destination_path = TD; t.destination_name = 'T_PropM3_%s_D' % k
            t.automated = True; t.replace_existing = True; t.save = False
            AT.import_asset_tasks([t])
            tex = load('%s/T_PropM3_%s_D' % (TD, k))
            if not tex: _B.fail('texture import failed: ' + f); continue
            tex.set_editor_property('srgb', True)
            tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
            EAL.save_asset(tex.get_path_name().split('.')[0])
        L('textures', len(KINDS))

        # materials: one master for props, one with the idle world-position offset for animals
        MP = unreal.MaterialProperty
        def E(m, cls, x, y): return MEL.create_material_expression(m, cls, x, y)
        def master(name, critter):
            path = '%s/%s' % (XD, name)
            m = AT.create_asset(name, XD, unreal.Material, unreal.MaterialFactoryNew())
            m.set_editor_property('two_sided', True)   # Tripo shells / fur cards are open: no see-through holes
            m.set_editor_property('used_with_instanced_static_meshes', True)
            tx = E(m, unreal.MaterialExpressionTextureSampleParameter2D, -800, -200); tx.set_editor_property('parameter_name', 'Tex')
            tx.set_editor_property('texture', load('%s/T_PropM3_crate_D' % TD))
            cd3 = E(m, unreal.MaterialExpressionPerInstanceCustomData, -800, 0); cd3.set_editor_property('data_index', 3)
            mul = E(m, unreal.MaterialExpressionMultiply, -500, -150)
            MEL.connect_material_expressions(tx, 'RGB', mul, 'A'); MEL.connect_material_expressions(cd3, '', mul, 'B')
            MEL.connect_material_property(mul, '', MP.MP_BASE_COLOR)
            r = E(m, unreal.MaterialExpressionScalarParameter, -500, 50); r.set_editor_property('parameter_name', 'Rough'); r.set_editor_property('default_value', 0.8)
            MEL.connect_material_property(r, '', MP.MP_ROUGHNESS)
            me = E(m, unreal.MaterialExpressionScalarParameter, -500, 150); me.set_editor_property('parameter_name', 'Metal'); me.set_editor_property('default_value', 0.0)
            MEL.connect_material_property(me, '', MP.MP_METALLIC)
            if critter:
                c = E(m, unreal.MaterialExpressionCustom, -500, 400)
                c.set_editor_property('description', 'PropsM3Idle'); c.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
                # local space of the imported mesh: +Y forward (glTF +Z), +Z up, X lateral; cm. UV1 = (part id, weight) from critterfit:
                # 0 body, 1 head, 2 tail, 3-6 legs. Birds (kind 0): head peck (pitch) bursts + look-around yaw. Quadrupeds (kind 1): tail sway, head look.
                c.set_editor_property('code', '''
float P = floor(uv1.x + 0.5);
float w = saturate(uv1.y);
float T = t * rate + ph * 37.0;
float3 v = lp;
float3 o = float3(0, 0, 0);
if (P > 0.5 && P < 1.5)
{
    float3 q = lp - hp;
    float yaw, pitch;
    if (kind < 0.5)
    {
        float peck = pow(saturate(sin(T * 2.3)), 6.0) * step(0.35, frac(sin(floor(T * 2.3 / 6.2832) * 12.9898 + ph * 78.233) * 43758.5453)) * act;
        pitch = -0.95 * peck;
        yaw = 0.55 * sin(T * 0.61) * (1.0 - peck);
    }
    else
    {
        pitch = -0.12 + 0.12 * sin(T * 0.37);
        yaw = 0.45 * sin(T * 0.43) * act;
    }
    yaw *= w; pitch *= w;
    float cy = cos(yaw), sy = sin(yaw);
    q = float3(q.x * cy - q.y * sy, q.x * sy + q.y * cy, q.z);
    float cp = cos(pitch), sp = sin(pitch);
    q = float3(q.x, q.y * cp - q.z * sp, q.y * sp + q.z * cp);
    o = (q + hp) - lp;
}
else if (P > 1.5 && P < 2.5 && kind > 0.5)
{
    float3 q = lp - tp;
    float a = (0.30 + 0.25 * act) * sin(T * 1.7) * w;
    float ca = cos(a), sa = sin(a);
    q = float3(q.x * ca - q.y * sa, q.x * sa + q.y * ca, q.z);
    o = (q + tp) - lp;
}
return o * amp;''')
                ins = []
                for n in ('lp', 'uv1', 't', 'ph', 'act', 'rate', 'hp', 'tp', 'kind', 'amp'):
                    ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
                c.set_editor_property('inputs', ins)
                def inp(expr, name, out=''): MEL.connect_material_expressions(expr, out, c, name)
                e = E(m, unreal.MaterialExpressionPreSkinnedPosition, -900, 300); inp(e, 'lp')
                e = E(m, unreal.MaterialExpressionTextureCoordinate, -900, 380); e.set_editor_property('coordinate_index', 1); inp(e, 'uv1')
                e = E(m, unreal.MaterialExpressionTime, -900, 460); inp(e, 't')
                for i, n in enumerate(('ph', 'act', 'rate')):
                    e = E(m, unreal.MaterialExpressionPerInstanceCustomData, -900, 540 + i * 70); e.set_editor_property('data_index', i); inp(e, n)
                for i, n in enumerate(('hp', 'tp')):
                    e = E(m, unreal.MaterialExpressionVectorParameter, -900, 760 + i * 90); e.set_editor_property('parameter_name', {'hp': 'HeadPivot', 'tp': 'TailPivot'}[n])
                    inp(e, n, 'RGB')
                for i, (n, pn, dv) in enumerate((('kind', 'Kind', 0.0), ('amp', 'IdleAmp', 1.0))):
                    e = E(m, unreal.MaterialExpressionScalarParameter, -900, 950 + i * 70); e.set_editor_property('parameter_name', pn); e.set_editor_property('default_value', dv); inp(e, n)
                tr = E(m, unreal.MaterialExpressionTransform, -200, 400)
                tr.set_editor_property('transform_source_type', unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL)
                tr.set_editor_property('transform_type', unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
                MEL.connect_material_expressions(c, '', tr, '')
                MEL.connect_material_property(tr, '', MP.MP_WORLD_POSITION_OFFSET)
            MEL.recompile_material(m)
            EAL.save_asset(path)
            return m
        mprop = master('M_PropM3', False)
        mcrit = master('M_PropM3_Critter', True)
        L('materials M_PropM3, M_PropM3_Critter')

        # meshes: LOD0 + LOD1 GLBs (glTF frame = browser frame: UE = (x, z, y) * 100), materials not imported
        def mesh_pipeline():
            p = unreal.InterchangeGenericAssetsPipeline()
            p.common_meshes_properties.set_editor_properties({'recompute_normals': False, 'recompute_tangents': True, 'use_full_precision_u_vs': True, 'remove_degenerates': False})
            p.mesh_pipeline.set_editor_properties({'generate_lightmap_u_vs': False, 'build_nanite': False})
            p.material_pipeline.set_editor_property('import_materials', False)
            p.material_pipeline.texture_pipeline.set_editor_property('import_textures', False)
            return p
        def do_import(path, dest):
            t = unreal.AssetImportTask(); t.filename = path; t.destination_path = dest; t.automated = True; t.replace_existing = True; t.save = False
            stack = unreal.InterchangePipelineStackOverride(); stack.add_pipeline(mesh_pipeline()); t.options = stack
            AT.import_asset_tasks([t])
            return [g.split('.')[0] for g in t.imported_object_paths if isinstance(load(g.split('.')[0]), unreal.StaticMesh)]
        for k in KINDS:
            got = {}
            for li in (0, 1):
                sm = do_import(os.path.join(PREP, '%s_lod%d.glb' % (k, li)), '%s/_in/%s_lod%d' % (MD, k, li))
                if not sm: _B.fail('mesh import failed: %s lod%d' % (k, li)); continue
                got[li] = sm[0]
            if 0 not in got: continue
            dst = '%s/SM_PropM3_%s' % (MD, k)
            if not EAL.rename_asset(got[0], dst): _B.fail('rename failed ' + dst); continue
            base = load(dst)
            if 1 in got:
                r = sms.set_lod_from_static_mesh(base, 1, load(got[1]), 0, True)
                if r < 0: _B.fail('LOD1 for %s failed (%d)' % (k, r))
            for i in range(len(base.get_editor_property('static_materials'))): base.set_material(i, None)
            mi = AT.create_asset('MI_PropM3_%s' % k, XD, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
            MEL.set_material_instance_parent(mi, mcrit if k in ANIMALS else mprop)
            MEL.set_material_instance_texture_parameter_value(mi, 'Tex', load('%s/T_PropM3_%s_D' % (TD, k)))
            rough, metal = ROUGH.get(k, (0.8, 0.0))
            MEL.set_material_instance_scalar_parameter_value(mi, 'Rough', rough); MEL.set_material_instance_scalar_parameter_value(mi, 'Metal', metal)
            if k in ANIMALS:
                pv = meta[k].get('pivots_m', {})
                def cm(p): return unreal.LinearColor(p[0] * 100.0, p[2] * 100.0, p[1] * 100.0, 0.0)   # glTF (x, y, z) m -> UE local (x, z, y) cm
                MEL.set_material_instance_vector_parameter_value(mi, 'HeadPivot', cm(pv.get('head', [0, 0, 0])))
                MEL.set_material_instance_vector_parameter_value(mi, 'TailPivot', cm(pv.get('tail', [0, 0, 0])))
                MEL.set_material_instance_scalar_parameter_value(mi, 'Kind', 0.0 if meta[k]['rig'] == 'bird' else 1.0)
            EAL.save_asset('%s/MI_PropM3_%s' % (XD, k))
            base.set_material(0, mi)
            ns = base.get_editor_property('nanite_settings')
            if ns.enabled: ns.enabled = False; base.set_editor_property('nanite_settings', ns)
            try: sms.set_lod_screen_sizes(base, [1.0, 0.12 if k in ANIMALS else 0.2])
            except Exception as ex: _B.warn('lod screen sizes ' + k, ex)
            # no collision body at all: no simple shapes, simple-as-complex with nothing simple = nothing to trace
            try: sms.remove_collisions(base)
            except Exception as ex: _B.warn('remove_collisions ' + k, ex)
            bs = base.get_editor_property('body_setup')
            if bs: bs.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
            if k in ANIMALS:   # the idle WPO moves heads / tails up to ~10 cm beyond the rest pose
                try: base.set_editor_property('positive_bounds_extension', unreal.Vector(10, 10, 10)); base.set_editor_property('negative_bounds_extension', unreal.Vector(10, 10, 10))
                except Exception as ex: _B.warn('bounds extension ' + k, ex)
            EAL.save_asset(dst)
            bb = base.get_bounding_box()
            L('mesh %s: LODs %d, bounds cm min %s max %s' % (dst, sms.get_lod_count(base), [round(v) for v in (bb.min.x, bb.min.y, bb.min.z)], [round(v) for v in (bb.max.x, bb.max.y, bb.max.z)]))
        if EAL.does_directory_exist(MD + '/_in'): EAL.delete_directory(MD + '/_in')

    # -------------------------------------------------------------------------------------------- map: the deliverable level + the test map
    def spawn_props(items, path_prefix='PropsM3_prop_'):
        n = 0; actors = 0
        for k in KINDS:
            sm = load('%s/Meshes/SM_PropM3_%s' % (ROOT, k))
            if not sm: _B.fail('missing mesh SM_PropM3_' + k); continue
            by = {}
            for p in items.get(k, []): by.setdefault('%d_%d' % (math.floor(p[0] / WP_TILE), math.floor(p[2] / WP_TILE)), []).append(p)
            for tk, its in sorted(by.items()):
                tx, tz = (int(v) for v in tk.split('_'))
                a = eas.spawn_actor_from_class(unreal.Actor, U((tx + 0.5) * WP_TILE, 0, (tz + 0.5) * WP_TILE), unreal.Rotator(0, 0, 0))
                a.set_actor_label('%s%s__t%s' % (path_prefix, k, tk)); a.set_folder_path('PropsM3/' + k)
                c = add_component(a, unreal.HierarchicalInstancedStaticMeshComponent)
                c.set_static_mesh(sm); c.set_editor_property('num_custom_data_floats', 4)
                c.set_mobility(unreal.ComponentMobility.STATIC)
                no_collision(c)
                c.set_editor_property('cast_shadow', SHADOW[k])
                for prop, v in (('instance_start_cull_distance', int(CULL[k] * 0.8)), ('instance_end_cull_distance', CULL[k])):
                    try: c.set_editor_property(prop, v)
                    except Exception as ex: _B.warn('cull ' + prop, ex)
                xs = []
                for p in its:
                    x, y, z, ry, s = p[:5]
                    xs.append(unreal.Transform(U(x, y, z), unreal.Rotator(roll=0.0, pitch=0.0, yaw=-math.degrees(ry)), unreal.Vector(s, s, s)))
                c.add_instances(xs, False, True)
                for i, p in enumerate(its):
                    for j in range(4): c.set_custom_data_value(i, j, float(p[5 + j]), False)
                n += len(its); actors += 1
        return n, actors

    if 'map' in STEPS:
        w = open_level(LEVEL)
        n, na = spawn_props(place)
        if not unreal.EditorLoadingAndSavingUtils.save_map(w, LEVEL): _B.fail('save_map failed: ' + LEVEL)
        L('level %s: %d instances in %d HISM tile actors' % (LEVEL, n, na))
        # the freshly saved level must not stay loaded as an editor world: AddLevelToWorld pops a modal warning for it (fatal in a commandlet)
        unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
        unreal.SystemLibrary.collect_garbage()

        # test map: 60 x 60 m slab (WHGround), one of each item at real scale beside a 1.8 m reference box, a pigeon flock, the island props as an
        # always-loaded sublevel, the golden look rig, an invisible engine Cube (traversal box: FWebTravWorld runs its island SolidMode 2 here)
        w = open_level(TEST)
        cube = load('/Engine/BasicShapes/Cube'); plane = load('/Engine/BasicShapes/Plane')
        TX, TZ = 300.0, 3000.0   # test origin far from the island props (browser metres)
        g = eas.spawn_actor_from_class(unreal.StaticMeshActor, U(TX, 0.0, TZ), unreal.Rotator(0, 0, 0)); g.set_actor_label('Test_Ground')
        g.static_mesh_component.set_static_mesh(plane); g.set_actor_scale3d(unreal.Vector(60, 60, 1)); g.tags = ['WHGround']
        g.static_mesh_component.set_collision_profile_name('BlockAll')
        mg = load('/Engine/BasicShapes/BasicShapeMaterial')
        if mg: g.static_mesh_component.set_material(0, mg)
        ref = eas.spawn_actor_from_class(unreal.StaticMeshActor, U(TX - 3.0, 0.9, TZ), unreal.Rotator(0, 0, 0)); ref.set_actor_label('Test_Ref_1m80')
        ref.static_mesh_component.set_static_mesh(cube); ref.set_actor_scale3d(unreal.Vector(0.3, 0.3, 1.8))
        tb = eas.spawn_actor_from_class(unreal.StaticMeshActor, U(TX + 25.0, 5.0, TZ + 25.0), unreal.Rotator(0, 0, 0)); tb.set_actor_label('Test_TravBox')
        tb.static_mesh_component.set_static_mesh(cube); tb.static_mesh_component.set_visibility(False); tb.static_mesh_component.set_collision_profile_name('BlockAll')
        tb.set_actor_scale3d(unreal.Vector(2, 2, 10))
        # lineup (plain StaticMeshActors would become traversal solids by FWebTravWorld's rules: use one HISM per kind, like the island level)
        line = {k: [] for k in KINDS}
        for i, k in enumerate(KINDS):
            line[k].append([TX + i * 1.2, 0.0, TZ, math.radians(-90.0 + 35.0), 1.0, 0.25, 1.0, 1.0, 1.0])
        for i in range(9):   # a flock of 9 pigeons
            a = i * 2.39996; r = 0.45 * math.sqrt(i + 0.5)
            line['pigeon'].append([TX + 3.0 + math.cos(a) * r, 0.0, TZ + 3.0 + math.sin(a) * r, a * 1.7, 1.0, (i * 0.137) % 1.0, 0.8, 1.0, 1.0])
        line['crate'] += [[TX + 6.0, 0.0, TZ + 3.0, 0.2, 1.0, 0, 0, 0, 1.0], [TX + 6.62, 0.0, TZ + 3.0, 0.25, 1.0, 0, 0, 0, 0.95], [TX + 6.31, 0.64, TZ + 3.0, 0.5, 1.0, 0, 0, 0, 1.02]]
        n2, _ = spawn_props(line, 'PropsM3_prop_test_')
        ps = eas.spawn_actor_from_class(unreal.PlayerStart, U(TX + 3.0, 1.2, TZ - 6.0), unreal.Rotator(0, 0, 90.0)); ps.set_actor_label('PlayerStart')
        have = {lv.get_path_name().split('.')[0] for lv in unreal.EditorLevelUtils.get_levels(w)}
        for lp in (LEVEL, '/Game/Look/Rigs/Look_Rig_golden'):
            if not EAL.does_asset_exist(lp): _B.fail('missing sublevel ' + lp); continue
            if lp in have: continue   # re-run: already a sublevel (adding it again pops a modal warning)
            lv = unreal.EditorLevelUtils.add_level_to_world(w, lp, unreal.LevelStreamingAlwaysLoaded)
            if not lv: _B.warn('add_level_to_world returned None (already a sublevel?) ' + lp)
        gm = unreal.load_class(None, sm2_common.GAME_MODE_CLASS)
        if gm: w.get_world_settings().set_editor_property('default_game_mode', gm)
        if not unreal.EditorLoadingAndSavingUtils.save_map(w, TEST): _B.fail('save_map failed: ' + TEST)
        L('test map %s: lineup %d instances, sublevels PropsM3_Island + Look_Rig_golden' % (TEST, n2))

    # -------------------------------------------------------------------------------------------- validate
    if 'validate' in STEPS:
        unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
        counts = {k: 0 for k in KINDS}; problems = []
        for a in eas.get_all_level_actors():
            if a.get_class().get_name() in KEEP: continue
            lab = a.get_actor_label()
            comps = a.get_components_by_class(unreal.PrimitiveComponent)
            for c in comps:
                if isinstance(c, unreal.BillboardComponent) and c.get_editor_property('is_editor_only'): continue   # the actor's editor sprite: not in -game
                if not isinstance(c, unreal.HierarchicalInstancedStaticMeshComponent): problems.append('%s/%s not a HISM' % (lab, c.get_name())); continue
                if c.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION or c.get_collision_profile_name() != 'NoCollision':
                    problems.append('%s collision %s %s' % (lab, c.get_collision_enabled(), c.get_collision_profile_name()))
                mesh = c.get_editor_property('static_mesh')
                name = (a.get_name() + '/' + lab + '/' + c.get_name() + '/' + (mesh.get_name() if mesh else '')).lower()
                if '_prop' not in name and 'prop_' not in name: problems.append('%s: no prop token in %s' % (lab, name))
                if 'whground' in [str(t).lower() for t in a.tags]: problems.append(lab + ' tagged WHGround')
                k = lab.split('PropsM3_prop_')[-1].split('__t')[0]
                if k in counts: counts[k] += c.get_instance_count()
                if mesh:
                    bs = mesh.get_editor_property('body_setup')
                    agg = bs.get_editor_property('agg_geom') if bs else None
                    nsimple = sum(len(agg.get_editor_property(f)) for f in ('box_elems', 'sphyl_elems', 'sphere_elems', 'convex_elems')) if agg else 0
                    if nsimple: problems.append('%s has %d simple collision shapes' % (mesh.get_name(), nsimple))
                    if mesh.get_editor_property('nanite_settings').enabled: problems.append(mesh.get_name() + ' Nanite on')
        want = {k: len(place.get(k, [])) for k in KINDS}
        if counts != want: problems.append('instance counts %s != placements %s' % (counts, want))
        for p in problems[:20]: _B.fail('validate: ' + p)
        L('validate %s: counts %s, total %d, problems %d' % (LEVEL, counts, sum(counts.values()), len(problems)))
        json.dump({'level': LEVEL, 'counts': counts, 'problems': problems}, open(os.path.join(SCR, 'validate.json'), 'w'), indent=1)

    # -------------------------------------------------------------------------------------------- verification copies of the island maps (temporary)
    if 'checkmaps' in STEPS:
        for tag, (src, dst) in CHECK.items():
            if not EAL.does_asset_exist(src): _B.fail('missing ' + src); continue
            if not EAL.does_asset_exist(dst):
                unreal.EditorLoadingAndSavingUtils.load_map(src)
                if not unreal.EditorLoadingAndSavingUtils.save_map(world(), dst): _B.fail('save-as failed: ' + dst); continue
                L('copied', src, '->', dst)
            unreal.EditorLoadingAndSavingUtils.load_map(dst)
            w = world()
            for a in list(eas.get_all_level_actors()):
                if a.get_actor_label() == 'LI_PropsM3_Island': eas.destroy_actor(a)
            li = eas.spawn_actor_from_class(unreal.LevelInstance, unreal.Vector(0, 0, 0))
            li.set_actor_label('LI_PropsM3_Island')
            li.set_editor_property('desired_runtime_behavior', unreal.LevelInstanceRuntimeBehavior.LEVEL_STREAMING)
            li.set_world_asset(load(LEVEL))
            try: li.set_editor_property('is_spatially_loaded', False)
            except Exception as ex: _B.warn('is_spatially_loaded', ex)
            if not unreal.EditorLoadingAndSavingUtils.save_map(w, dst): _B.fail('save_map failed: ' + dst)
            L('check map', dst, '+ LI_PropsM3_Island')

    if 'dropcheck' in STEPS:
        unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
        for tag, (src, dst) in CHECK.items():
            if EAL.does_asset_exist(dst):
                ok = EAL.delete_asset(dst); L('deleted', dst, ok)
                if not ok: _B.fail('could not delete ' + dst)
            for sub in ('__ExternalActors__', '__ExternalObjects__'):
                d = os.path.join(PROJ, 'Content', sub, 'PropsM3', 'Maps', dst.split('/')[-1])
                if os.path.isdir(d) and '/Content/' + sub + '/PropsM3/Maps/PropsM3_IslandCheck_' in d:
                    shutil.rmtree(d); L('removed', d)
    _B.finish()


if IN_UE:
    try:
        build_in_ue()
    except Exception as _ex:
        import traceback; traceback.print_exc()
        print('SM2_BUILD_FAILED: build_props_m3.py %s' % str(_ex)[:200], flush=True)
        raise
elif __name__ == '__main__':
    main()

# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# P6 City life: idempotent, headless rebuild of /Game/Life and /Game/Tests/Life (traffic, crowd; water follows in a later round).
#
# Two modes in one file (same pattern as build_manhattan.py):
#   * plain python3 (run from anywhere, YOUR editor closed):
#         python3 unreal/WebHomage/Scripts/build_life.py [--steps prep,cpp,content,map]
#       prep     tools/life/prep_vehicles.py (vehicles.glb -> per-mesh GLBs + IP-clean atlas), tools/life/export_lanes.mjs (lanes / parked cars /
#                pedestrian graph -> Scripts/life_data/*.txt, committed), Blender FBX export of 20 crowd citizens (P2's exporter, redirected)
#       cpp      Scripts/build_editor.sh (Source/WebHomage/Life: AWHLifeTraffic, AWHLifeCrowd, AWHLifeCamRig, AWHLifeProbe)
#       content  headless UE commandlet: clean /Game/Life, atlas + M_LifeVehicle + 15 vehicle static meshes with LODs, citizens + ABP + materials
#       map      headless UE commandlet: /Game/Tests/Life/Life_Midtown (playable) + Life_View_S1 / S2 (P1 shot cameras) + Life_Street_Clip
#     Needs the pieces this one stands on: /Game/Tests/City/City_Midtown_Geo + /Game/Look/Rigs/Look_Rig_golden (python3 tools/life/build_deps.py).
#     Every Unreal process is a headless commandlet (-nullrhi -RenderOffScreen -NoSound) of THIS worktree's project; it waits while the number
#     of running Unreal processes is >= the cap in /Users/midir/sm2-n1/_scratch/gpu/slots (RULES.md, GPU lock).
#   * inside Unreal (-run=pythonscript -script=<this file>, env SM2_LIFE_STEPS=clean,vehicles,citizens,signals,map): builds the content.
# No .uasset / .umap is committed (unreal/WebHomage/CONTENT.md); this script is the source of truth.
import os, sys, json, subprocess, time, shutil, glob, math

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '/Users/midir/sm2-n1/life/unreal/WebHomage/Scripts'
sys.path.insert(0, os.environ.get('SM2_SCRIPTS_DIR') or HERE)
import sm2_common
_B = sm2_common.Build('build_life.py')
COSMETIC_MISS = ('generate_mesh_distance_field', 'lod screen sizes', 'camera rig auto activate')   # perf / camera-default property sets; every other MISS is a required asset or setting
PROJ = os.path.dirname(HERE)
WT = os.path.dirname(os.path.dirname(PROJ))
UPROJECT = os.path.join(PROJ, 'WebHomage.uproject')
UE = '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor'
SCR = os.environ.get('SM2_LIFE_SCR', '/Users/midir/sm2-n1/_scratch/life')
EXPORT = os.environ.get('SM2_LIFE_EXPORT', os.path.join(SCR, 'manhattan/export/midtown3x3'))
VEH = os.path.join(SCR, 'vehicles')
CIT = os.path.join(SCR, 'citizens')
DATA = os.environ.get('SM2_LIFE_DATA_DIR') or os.path.join(HERE, 'life_data')
STEPS_ALL = ['prep', 'cpp', 'content', 'map']
TYPES = ['taxi', 'taxi_hy', 'taxi_mv', 'taxi_gr', 'sedan', 'hatch', 'sedan2', 'cross', 'suv', 'suv2', 'pickup', 'van', 'truck', 'bus', 'tour']
ROOT, TESTS = '/Game/Life', '/Game/Tests/Life'
DENSITY = float(os.environ.get('SM2_LIFE_DENSITY', '2.3'))   # traffic DensityScale (1 = the browser's steady-state cars per km of lane)

try:
    import unreal  # noqa: F401
    IN_UE = hasattr(unreal, 'EditorAssetLibrary')
except ImportError:
    IN_UE = False


# ================================================================================================ orchestrator (plain python3)
def log(*a):
    print('[build_life %s]' % time.strftime('%H:%M:%S'), *a, flush=True)


def sh(cmd, cwd=WT, log_name=None):
    log('$', cmd if isinstance(cmd, str) else ' '.join(cmd))
    out = open(os.path.join(SCR, 'logs', log_name), 'w') if log_name else None
    r = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), stdout=out or None, stderr=subprocess.STDOUT if out else None)
    if r.returncode != 0:
        raise SystemExit('command failed (%d): %s%s' % (r.returncode, cmd, ('  log: ' + out.name) if out else ''))


def slots():
    try: return int(open('/Users/midir/sm2-n1/_scratch/gpu/slots').read().strip())
    except Exception: return 3


def wait_slot():
    while True:
        # real engine processes only (comm == UnrealEditor): the gpu_slot.py wrappers of queued jobs carry the same path in their argv
        n = subprocess.run("pgrep -x UnrealEditor | wc -l", shell=True, capture_output=True, text=True).stdout.strip()
        if int(n or 0) < slots(): return
        log('%s Unreal processes running (cap %d), waiting 60 s' % (n, slots())); time.sleep(60)


def ue_python(name, steps, timeout=7200):
    if subprocess.run(['pgrep', '-f', UPROJECT], capture_output=True).returncode == 0:
        raise SystemExit('an Unreal process of this worktree is running; stop it first: pkill -9 -f "%s"' % UPROJECT)
    lg = os.path.join(SCR, 'logs', name + '.log')
    wait_slot()
    log('UE commandlet', name, 'steps', steps, '-> log', lg)
    t0 = time.time()
    with open(lg + '.stdout', 'w') as so:
        r = subprocess.run([UE, UPROJECT, '-run=pythonscript', '-script=' + os.path.abspath(__file__), '-unattended', '-nullrhi', '-nosplash', '-RenderOffScreen',
                            '-NoSound', '-NoCrashReports', '-abslog=' + lg], env={**os.environ, 'SM2_LIFE_STEPS': steps, 'SM2_LIFE_SCR': SCR, 'SM2_LIFE_EXPORT': EXPORT},
                           stdout=so, stderr=subprocess.STDOUT, timeout=timeout)
    txt = open(lg, errors='replace').read() if os.path.exists(lg) else ''
    for l in txt.splitlines():
        if '[build_life' in l: print(l.split('LogPython: ')[-1])
    bad = [l for l in txt.splitlines() if 'LogPython: Error' in l or 'Traceback' in l]
    log('UE commandlet %s: rc %d, %.0f s, %d python error lines' % (name, r.returncode, time.time() - t0, len(bad)))
    if bad:
        print('\n'.join(bad[:30]))
        raise SystemExit('python error in ' + name + ' (log ' + lg + ')')


def step_prep():
    os.environ.setdefault('SM2_LIFE_CIT', CIT)   # citizens_fbx.py writes where this build reads
    os.makedirs(VEH, exist_ok=True); os.makedirs(CIT, exist_ok=True)
    sh(['python3', 'tools/life/prep_vehicles.py', '--out', VEH], log_name='prep_vehicles.log')
    lay = os.path.join(EXPORT, 'layout.json')
    sh(['node', 'tools/life/export_lanes.mjs'] + (['--layout', lay] if os.path.exists(lay) else []), log_name='export_lanes.log')
    names = [v['name'] for v in json.load(open(os.path.join(WT, 'public/assets/city/npc/citizens.json')))['variants']]
    if not all(os.path.exists(os.path.join(CIT, 'fbx', n + '.fbx')) for n in names):
        sh(['python3', 'tools/ue_char/eval/tiles.py', os.path.join(CIT, 'tiles'), os.path.join(CIT, 'stats_tiles.json')], log_name='citizen_tiles.log')
        sh(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '-P', 'tools/life/citizens_fbx.py', '--'] + names, log_name='citizen_fbx.log')
    sh(['python3', 'tools/life/export_signals.py'] + ([lay] if os.path.exists(lay) else []), log_name='export_signals.log')
    if not glob.glob(os.path.join(CIT, 'fbx', '*_headmask.json')):
        sh(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '-P', 'tools/life/citizen_headmask.py', '--', os.path.join(CIT, 'fbx')], log_name='citizen_headmask.log')
    sh(['python3', 'tools/life/citizen_variants.py', os.path.join(CIT, 'fbx')], log_name='citizen_variants.log')   # two outfit + head recolours per citizen (crowd variety)
    log('prep done: %d vehicle GLBs, %d citizen FBX' % (len(glob.glob(VEH + '/glb/*.glb')), len(glob.glob(CIT + '/fbx/*.fbx'))))


def step_cpp():
    # build_editor.sh fails its manifest check when UBT compiled a new dylib but left UnrealEditor.modules on the old name (it does so while other
    # agents' editors of this engine run); the new dylib is fine, so point the manifest at the newest one and go on
    try:
        sh([os.path.join(HERE, 'build_editor.sh')], log_name='build_editor.log')
    except SystemExit:
        mods = os.path.join(PROJ, 'Binaries/Mac/UnrealEditor.modules')
        dy = sorted(glob.glob(os.path.join(PROJ, 'Binaries/Mac/libUnrealEditor-WebHomage-*.dylib')))
        j = json.load(open(mods))
        if dy and not os.path.exists(os.path.join(PROJ, 'Binaries/Mac', j['Modules']['WebHomage'])):
            j['Modules']['WebHomage'] = os.path.basename(dy[-1]); json.dump(j, open(mods, 'w'), indent='\t'); log('modules manifest re-pointed to', os.path.basename(dy[-1]))
        else:
            raise


def step_content():
    ue_python('life_content', 'clean,vehicles,citizens,signals')


def step_map():
    ue_python('life_map', 'map')


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Piece P6: rebuild /Game/Life + /Game/Tests/Life (headless)')
    ap.add_argument('--steps', default=','.join(STEPS_ALL))
    a = ap.parse_args()
    want = a.steps.split(',')
    bad = [s for s in want if s not in STEPS_ALL]
    if bad: raise SystemExit('unknown steps %s (known: %s)' % (bad, STEPS_ALL))
    os.makedirs(os.path.join(SCR, 'logs'), exist_ok=True)
    t0 = time.time()
    for s in STEPS_ALL:
        if s in want:
            log('=== step', s); t = time.time()
            globals()['step_' + s]()
            log('=== step %s done in %.0f s' % (s, time.time() - t))
    log('all done in %.0f s' % (time.time() - t0))


# ================================================================================================ inside Unreal
def build_in_ue():
    STEPS = set(os.environ.get('SM2_LIFE_STEPS', 'clean,vehicles,citizens,signals,map').split(','))
    AT = unreal.AssetToolsHelpers.get_asset_tools()
    EAL = unreal.EditorAssetLibrary
    MEL = unreal.MaterialEditingLibrary
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    T0 = time.time()
    MISS = []

    def L(*a): print('[build_life %5.0fs]' % (time.time() - T0), *a)
    def load(p): return unreal.load_asset(p)

    def do_import(path, dest, pipeline, name=None):
        """AssetImportTask + InterchangePipelineStackOverride (P2's gotcha: plain pipeline options only work for some imports); returns imported object paths"""
        t = unreal.AssetImportTask(); t.filename = path; t.destination_path = dest; t.automated = True; t.replace_existing = True; t.save = False
        if name: t.destination_name = name
        stack = unreal.InterchangePipelineStackOverride(); stack.add_pipeline(pipeline)
        t.options = stack
        AT.import_asset_tasks([t])
        return list(t.imported_object_paths)

    def E(m, cls, x, y): return MEL.create_material_expression(m, cls, x, y)

    # ------------------------------------------------------------------------------------------------ clean
    if 'clean' in STEPS:
        unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
        if EAL.does_directory_exist(ROOT):
            try: EAL.delete_directory(ROOT)
            except Exception as e: L('clean: delete failed', str(e)[:120])
        L('cleaned')

    # ------------------------------------------------------------------------------------------------ vehicles
    if 'vehicles' in STEPS:
        VD = ROOT + '/Vehicles'
        # atlas (IP-clean copy made by tools/life/prep_vehicles.py)
        t = unreal.AssetImportTask(); t.filename = VEH + '/vehicles_atlas_clean.png'; t.destination_path = VD; t.destination_name = 'T_VehiclesAtlas'
        t.automated = True; t.replace_existing = True; t.save = False
        AT.import_asset_tasks([t])
        atlas = load(VD + '/T_VehiclesAtlas')
        atlas.set_editor_property('srgb', True)
        atlas.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP); atlas.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
        atlas.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
        try: atlas.set_editor_property('never_stream', True)
        except Exception: pass
        EAL.save_asset(VD + '/T_VehiclesAtlas')

        # material: port of partmat.js (part id in UV1.x) + vehicles.js (taxi topper ad tiles, glass, brake lights, night lamps)
        mpath = VD + '/M_LifeVehicle'
        m = AT.create_asset('M_LifeVehicle', VD, unreal.Material, unreal.MaterialFactoryNew())
        for flag in ('used_with_instanced_static_meshes',):
            try: m.set_editor_property(flag, True)
            except Exception as e: MISS.append('material flag %s: %s' % (flag, str(e)[:80]))
        c = E(m, unreal.MaterialExpressionCustom, -400, 0)
        c.set_editor_property('description', 'LifeVehicle'); c.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        c.set_editor_property('code', '''
float3 tint = float3(pc0, pc1, pc2);
float P = floor(part.x + 0.5);
float2 muv = uv0;
if (P > 14.5 && P < 15.5 && uv0.x > 0.499)
{
    // taxi topper: one of the CLEAN ad tiles 0,2,4,6 of the atlas (tiles 1,3,5,7 are IP-excluded and blanked), chosen per instance
    float k = floor(frac(prand * 7.31 + 0.13) * 4.0) * 2.0;
    muv = float2(0.5 + fmod(k, 2.0) * 0.25, floor(k / 2.0) * (170.0 / 2048.0)) + (uv0 - float2(0.5, 0.0));
}
float3 alb = Texture2DSample(tAtlas, tAtlasSampler, muv).rgb;
float nk = saturate(nightk);
float brake = saturate(state);
Rough = 0.7; Metal = 0.0; Emis = float3(0.0, 0.0, 0.0); Spec = 0.5;
if (P > 0.5 && P < 1.5) { alb *= tint; Rough = 0.32; }                                       // paint
else if (P > 1.5 && P < 2.5) { Rough = 0.28; Metal = 1.0; }                                   // metal
else if (P > 2.5 && P < 3.5) { alb = min(alb * float3(0.27, 0.285, 0.30), float3(0.12, 0.12, 0.12)); Rough = 0.05; Spec = 0.6; } // glass over the interior cards
else if (P > 3.5 && P < 4.5) { Rough = 0.2; Emis = alb * 0.4; }
else if (P > 4.5 && P < 5.5) { Rough = 0.92; }                                                // rubber
else if (P > 5.5 && P < 6.5) { Rough = 0.55; }                                                // plastic
else if (P > 6.5 && P < 7.5) { Rough = 0.08; Metal = 0.6; Emis = float3(0.12, 0.12, 0.12) + float3(1.0, 0.93, 0.8) * 5.0 * nk; } // head lamp
else if (P > 7.5 && P < 8.5) { Rough = 0.2; Emis = alb * (0.3 + brake * 5.0 + 1.6 * nk); }    // tail lamp: brake state in custom data 3
else if (P > 8.5 && P < 9.5) { Rough = 0.85; }
else if (P > 13.5 && P < 14.5) { Rough = 0.1; Emis = alb * 2.0 * (1.0 + 1.5 * nk); }        // bus destination screen
else if (P > 14.5 && P < 15.5) { Rough = 0.3; Emis = alb * 0.25 * (1.0 + 1.5 * nk); }       // taxi topper
AO = lerp(1.0, saturate(vc.r), 0.85);
return alb;''')
        ins = []
        for n in ('uv0', 'part', 'vc', 'pc0', 'pc1', 'pc2', 'state', 'prand', 'tAtlas', 'nightk'):
            ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
        c.set_editor_property('inputs', ins)
        outs = []
        for n, k in (('Rough', 1), ('Metal', 1), ('Emis', 3), ('Spec', 1), ('AO', 1)):
            co = unreal.CustomOutput(); co.set_editor_property('output_name', n)
            co.set_editor_property('output_type', [None, unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.CustomMaterialOutputType.CMOT_FLOAT2, unreal.CustomMaterialOutputType.CMOT_FLOAT3][k])
            outs.append(co)
        c.set_editor_property('additional_outputs', outs)
        def inp(expr, name): MEL.connect_material_expressions(expr, '', c, name)
        e = E(m, unreal.MaterialExpressionTextureCoordinate, -900, -300); e.set_editor_property('coordinate_index', 0); inp(e, 'uv0')
        e = E(m, unreal.MaterialExpressionTextureCoordinate, -900, -200); e.set_editor_property('coordinate_index', 1); inp(e, 'part')
        e = E(m, unreal.MaterialExpressionVertexColor, -900, -100); inp(e, 'vc')
        for i, n in enumerate(('pc0', 'pc1', 'pc2', 'state')):
            e = E(m, unreal.MaterialExpressionPerInstanceCustomData, -900, i * 100); e.set_editor_property('data_index', i); inp(e, n)
        e = E(m, unreal.MaterialExpressionPerInstanceRandom, -900, 450); inp(e, 'prand')
        e = E(m, unreal.MaterialExpressionTextureObject, -900, 550); e.set_editor_property('texture', atlas)
        e.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_COLOR); inp(e, 'tAtlas')
        mpc_path = '/Game/City/Materials/MPC_City'
        e = E(m, unreal.MaterialExpressionCollectionParameter, -900, 650)
        if EAL.does_asset_exist(mpc_path): e.set_editor_property('collection', load(mpc_path)); e.set_editor_property('parameter_name', 'NightK')
        else: MISS.append('MPC_City missing: no night lamps')
        inp(e, 'nightk')
        MP = unreal.MaterialProperty
        MEL.connect_material_property(c, '', MP.MP_BASE_COLOR)
        for n, prop in (('Rough', MP.MP_ROUGHNESS), ('Metal', MP.MP_METALLIC), ('Emis', MP.MP_EMISSIVE_COLOR), ('Spec', MP.MP_SPECULAR), ('AO', MP.MP_AMBIENT_OCCLUSION)):
            MEL.connect_material_property(c, n, prop)
        MEL.recompile_material(m)
        EAL.save_asset(mpath)
        L('material M_LifeVehicle')

        # meshes: one GLB per LOD mesh (tools/life/prep_vehicles.py); glTF frame = browser frame, UE = (x, z, y) * 100 (docs/night1/city/EXPORT.md)
        def mesh_pipeline():
            p = unreal.InterchangeGenericAssetsPipeline()
            p.common_meshes_properties.set_editor_properties({'recompute_normals': False, 'recompute_tangents': False, 'use_full_precision_u_vs': True,
                'remove_degenerates': False, 'vertex_color_import_option': unreal.InterchangeVertexColorImportOption.IVCIO_REPLACE})
            p.mesh_pipeline.set_editor_properties({'generate_lightmap_u_vs': False, 'build_nanite': False})
            p.material_pipeline.set_editor_property('import_materials', False)
            p.material_pipeline.texture_pipeline.set_editor_property('import_textures', False)
            return p
        files = sorted(glob.glob(VEH + '/glb/*.glb'))
        imported = {}
        for f in files:
            n = os.path.basename(f)[:-4]
            got = do_import(f, VD + '/_in', mesh_pipeline())
            sm = [g for g in got if isinstance(load(g.split('.')[0]), unreal.StaticMesh)]
            if not sm: MISS.append('import failed: ' + n); continue
            dst = '%s/SM_%s' % (VD, n)
            EAL.rename_asset(sm[0].split('.')[0], dst)
            imported[n] = dst
        L('imported %d of %d vehicle meshes' % (len(imported), len(files)))
        try: unreal.SystemLibrary.execute_console_command(None, 'Module Load StaticMeshEditor')
        except Exception: pass
        sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        mat = load(mpath)
        for ty in TYPES:
            if ty not in imported: MISS.append('no mesh for ' + ty); continue
            base = load(imported[ty])
            for li in (1, 2):
                k = '%s_l%d' % (ty, li)
                if k in imported:
                    r = sms.set_lod_from_static_mesh(base, li, load(imported[k]), 0, True)
                    if r < 0: MISS.append('LOD %s -> %s failed (%d)' % (k, ty, r))
            for i in range(len(base.get_editor_property('static_materials'))): base.set_material(i, mat)
            try: sms.set_lod_screen_sizes(base, [1.0, 0.22, 0.07])
            except Exception as e: MISS.append('lod screen sizes %s: %s' % (ty, str(e)[:80]))
            ns = base.get_editor_property('nanite_settings')
            if ns.enabled: ns.enabled = False; base.set_editor_property('nanite_settings', ns)
            for li in range(sms.get_lod_count(base)):
                bs = sms.get_lod_build_settings(base, li)
                bs.set_editor_property('use_full_precision_u_vs', True); bs.set_editor_property('generate_lightmap_u_vs', False)
                bs.set_editor_property('recompute_normals', False); bs.set_editor_property('recompute_tangents', False)
                sms.set_lod_build_settings(base, li, bs)
            try:
                base.set_editor_property('generate_mesh_distance_field', False)
            except Exception as e:
                MISS.append('generate_mesh_distance_field: ' + str(e)[:80])
            EAL.save_asset(imported[ty])
            bb = base.get_bounds()
            L('vehicle %-8s LODs %d  bounds extent (cm) x %.0f y %.0f z %.0f  origin z %.0f' % (ty, sms.get_lod_count(base), bb.box_extent.x, bb.box_extent.y, bb.box_extent.z, bb.origin.z))
        for n in list(imported):
            if n not in TYPES:  # l1 / l2 sources are now LODs of their base mesh
                try: EAL.delete_asset(imported[n])
                except Exception: pass
        if EAL.does_directory_exist(VD + '/_in'): EAL.delete_directory(VD + '/_in')

    # ------------------------------------------------------------------------------------------------ citizens
    if 'citizens' in STEPS:
        CD = ROOT + '/Citizens'
        names = sorted(os.path.basename(f)[:-4] for f in glob.glob(CIT + '/fbx/*.fbx'))
        if not names: raise RuntimeError('no citizen FBX in ' + CIT + '/fbx (run the prep step)')
        SKEL = CD + '/SK_Citizen_Skeleton'
        def skel_pipeline(skeleton=None, anims=True):
            p = unreal.InterchangeGenericAssetsPipeline()
            mp = p.get_editor_property('mesh_pipeline')
            mp.set_editor_property('build_nanite', False); mp.set_editor_property('create_physics_asset', False)
            mp.set_editor_property('import_static_meshes', False); mp.set_editor_property('use_high_precision_skin_weights', True)
            cm = p.get_editor_property('common_meshes_properties')
            cm.set_editor_property('recompute_normals', False); cm.set_editor_property('recompute_tangents', True); cm.set_editor_property('use_mikk_t_space', True)
            cm.set_editor_property('use_high_precision_tangent_basis', True); cm.set_editor_property('use_full_precision_u_vs', True)
            if skeleton: p.get_editor_property('common_skeletal_meshes_and_animations_properties').set_editor_property('skeleton', load(skeleton))
            ap = p.get_editor_property('animation_pipeline')
            ap.set_editor_property('import_animations', anims); ap.set_editor_property('custom_bone_animation_sample_rate', 30)
            mat_ = p.get_editor_property('material_pipeline'); mat_.set_editor_property('import_materials', False)
            mat_.get_editor_property('texture_pipeline').set_editor_property('import_textures', False)
            return p
        tmp = os.path.join(SCR, 'citizens_import'); os.makedirs(tmp, exist_ok=True)
        for i, n in enumerate(names):
            f = os.path.join(tmp, 'SK_Citizen%s.fbx' % ('' if i == 0 else '_' + n))
            shutil.copyfile('%s/fbx/%s.fbx' % (CIT, n), f)
            do_import(f, CD, skel_pipeline(None if i == 0 else SKEL, anims=(i == 0)))
            if i == 0 or i == len(names) - 1: L('imported citizen', n)
        # flatten: clips -> Anims/A_Citizen_<clip>, meshes / skeleton to CD
        def find(folder, cls):
            return [p.split('.')[0] for p in EAL.list_assets(folder, recursive=True) if '/Anims/' not in p and isinstance(load(p.split('.')[0]), cls)]
        for p in [p.split('.')[0] for p in EAL.list_assets(CD, recursive=True) if isinstance(load(p.split('.')[0]), unreal.AnimSequence)]:
            base = p.split('/')[-1]; clip = base.split('_')[-1]   # 'Armature_walk' / 'SK_Citizen_walk' -> walk | run | idle
            if not p.startswith(CD + '/Anims/'): EAL.rename_asset(p, '%s/Anims/A_Citizen_%s' % (CD, clip))
        for cls in (unreal.SkeletalMesh, unreal.Skeleton):
            for p in find(CD, cls):
                if p.rsplit('/', 1)[0] != CD: EAL.rename_asset(p, CD + '/' + p.split('/')[-1])
        if EAL.does_asset_exist(CD + '/SK_Citizen'): EAL.rename_asset(CD + '/SK_Citizen', CD + '/SK_Citizen_' + names[0])
        # textures + materials: one master (skeletal usage), one instance per citizen
        VARS = ('', '_v1', '_v2', '_v3', '_v4')   # outfit / hair / skin variants (tools/life/citizen_variants.py): same mesh, recoloured atlas tile
        for n in names:
            for v in VARS:
                t = unreal.AssetImportTask(); t.filename = '%s/fbx/%s_basecolor%s.png' % (CIT, n, v); t.destination_path = CD + '/Textures'; t.destination_name = 'T_Cit_%s_BaseColor%s' % (n, v)
                t.automated = True; t.replace_existing = True; t.save = False
                AT.import_asset_tasks([t])
        m = AT.create_asset('M_LifeCitizen', CD + '/Materials', unreal.Material, unreal.MaterialFactoryNew())
        m.set_editor_property('used_with_skeletal_mesh', True)
        tp = E(m, unreal.MaterialExpressionTextureSampleParameter2D, -600, -200)
        tp.set_editor_property('parameter_name', 'BaseColor'); tp.set_editor_property('texture', load('/Engine/EngineResources/WhiteSquareTexture'))
        tp.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
        MEL.connect_material_property(tp, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
        r = E(m, unreal.MaterialExpressionScalarParameter, -600, 0); r.set_editor_property('parameter_name', 'Roughness'); r.set_editor_property('default_value', 0.8)
        MEL.connect_material_property(r, '', unreal.MaterialProperty.MP_ROUGHNESS)
        sp = E(m, unreal.MaterialExpressionScalarParameter, -600, 100); sp.set_editor_property('parameter_name', 'Specular'); sp.set_editor_property('default_value', 0.35)
        MEL.connect_material_property(sp, '', unreal.MaterialProperty.MP_SPECULAR)
        MEL.recompile_material(m); EAL.save_asset(CD + '/Materials/M_LifeCitizen')
        for n in names:
            for v in VARS:
                mv = AT.create_asset('MI_LifeCit_%s%s' % (n, v), CD + '/Materials', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
                MEL.set_material_instance_parent(mv, m)
                MEL.set_material_instance_texture_parameter_value(mv, 'BaseColor', load('%s/Textures/T_Cit_%s_BaseColor%s' % (CD, n, v)))
                MEL.update_material_instance(mv)
                EAL.save_asset('%s/Materials/MI_LifeCit_%s%s' % (CD, n, v))
            mi = load('%s/Materials/MI_LifeCit_%s' % (CD, n))
            sk = load('%s/SK_Citizen_%s' % (CD, n))
            if not sk: MISS.append('no citizen mesh ' + n); continue
            out = []
            for sm_ in sk.get_editor_property('materials'):
                sm_.set_editor_property('material_interface', mi); out.append(sm_)
            sk.set_editor_property('materials', out)
            EAL.save_asset('%s/SK_Citizen_%s' % (CD, n))
        # anim blueprint: child of P2's native UWHCharAnimInstance (idle + walk / run natural speeds: stride 1.1543 m / (32/30 s) = 108 cm/s, run 540 cm/s)
        CA = CD + '/Anims/A_Citizen_'
        f = unreal.AnimBlueprintFactory(); f.set_editor_property('target_skeleton', load(SKEL)); f.set_editor_property('parent_class', unreal.WHCharAnimInstance)
        bp = AT.create_asset('ABP_Life_Citizen', CD, unreal.AnimBlueprint, f)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        cdo = unreal.get_default_object(bp.generated_class())
        samples = []
        for clip, spd in (('walk', 108.0), ('run', 540.0)):
            s = unreal.WHLocoSample(); s.set_editor_property('clip', load(CA + clip)); s.set_editor_property('speed', spd); samples.append(s)
        cdo.set_editor_property('loco', samples); cdo.set_editor_property('idle', load(CA + 'idle'))
        EAL.save_asset(CD + '/ABP_Life_Citizen')
        EAL.save_directory(CD, only_if_is_dirty=True, recursive=True)
        L('citizens', len(names), 'models; clips', sorted(p.split('.')[-1] for p in EAL.list_assets(CD + '/Anims')))

    # ------------------------------------------------------------------------------------------------ signal lenses
    if 'signals' in STEPS:
        SD = ROOT + '/Signals'
        m = AT.create_asset('M_LifeSignal', SD, unreal.Material, unreal.MaterialFactoryNew())
        try: m.set_editor_property('used_with_instanced_static_meshes', True)
        except Exception as e: MISS.append('signal material flag: ' + str(e)[:80])
        c = E(m, unreal.MaterialExpressionCustom, -400, 0)
        c.set_editor_property('description', 'LifeSignal'); c.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        c.set_editor_property('code', '''
float3 rgb = float3(r, g, b);
float on = saturate(st);
Emis = rgb * lerp(0.015, 55.0, on);
Rough = 0.25;
return rgb * lerp(0.02, 0.15, on);''')
        ins = []
        for n in ('r', 'g', 'b', 'st'):
            ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
        c.set_editor_property('inputs', ins)
        outs = []
        for n, k in (('Emis', 3), ('Rough', 1)):
            co = unreal.CustomOutput(); co.set_editor_property('output_name', n)
            co.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3 if k == 3 else unreal.CustomMaterialOutputType.CMOT_FLOAT1)
            outs.append(co)
        c.set_editor_property('additional_outputs', outs)
        for i, n in enumerate(('r', 'g', 'b', 'st')):
            e = E(m, unreal.MaterialExpressionPerInstanceCustomData, -900, i * 100); e.set_editor_property('data_index', i); MEL.connect_material_expressions(e, '', c, n)
        MP = unreal.MaterialProperty
        MEL.connect_material_property(c, '', MP.MP_BASE_COLOR)
        MEL.connect_material_property(c, 'Emis', MP.MP_EMISSIVE_COLOR)
        MEL.connect_material_property(c, 'Rough', MP.MP_ROUGHNESS)
        MEL.recompile_material(m)
        EAL.save_asset(SD + '/M_LifeSignal')
        L('material M_LifeSignal')

    # ------------------------------------------------------------------------------------------------ maps
    if 'map' in STEPS:
        HEREDIR = HERE
        SHOTS = {s['id'].split('_')[0]: s for s in json.load(open(os.path.join(HEREDIR, 'city_shots.json')))}
        CITY_GEO = '/Game/Tests/City/City_Midtown_Geo'
        RIG = '/Game/Look/Rigs/Look_Rig_golden'
        for need in (CITY_GEO, RIG, ROOT + '/Citizens/ABP_Life_Citizen', ROOT + '/Vehicles/M_LifeVehicle'):
            if not EAL.does_asset_exist(need): raise RuntimeError('missing ' + need + ' (run build_deps.py and the content step first)')
        KEEP = ('WorldSettings', 'Brush', 'DefaultPhysicsVolume', 'GameplayDebuggerCategoryReplicator', 'WorldDataLayers', 'WorldPartitionMiniMap')

        def open_level(path):
            if EAL.does_asset_exist(path):
                unreal.EditorLoadingAndSavingUtils.load_map(path)
                for a in eas.get_all_level_actors():
                    if a.get_class().get_name() not in KEEP and a.get_path_name().startswith(path + '.'): eas.destroy_actor(a)
            else:
                les.new_level(path)
            return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

        def Um(x, z, y=0.0): return unreal.Vector(x * 100.0, z * 100.0, y * 100.0)   # browser metres (x east, y up, z south) -> UE cm
        def spawn(cls, loc, yaw=0.0, label=None):
            a = eas.spawn_actor_from_class(cls, loc, unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
            if label: a.set_actor_label(label)
            return a

        ACTORS = TESTS + '/Life_Actors'
        open_level(ACTORS)
        lanes = open(os.path.join(DATA, 'lanes.txt')).read(); parked = open(os.path.join(DATA, 'parked.txt')).read(); walk = open(os.path.join(DATA, 'walk.txt')).read()
        tr = spawn(unreal.WHLifeTraffic, unreal.Vector(0, 0, 0), label='LifeTraffic')
        tr.set_editor_property('lane_data', lanes); tr.set_editor_property('parked_data', parked)
        tr.set_editor_property('vehicle_meshes', [load('%s/Vehicles/SM_%s' % (ROOT, t)) for t in TYPES])
        tr.set_editor_property('vehicle_material', load(ROOT + '/Vehicles/M_LifeVehicle'))
        tr.set_editor_property('seed', 7)
        tr.set_editor_property('max_cars', int(os.environ.get('SM2_LIFE_MAXCARS', '2000')))
        tr.set_editor_property('active_radius_m', float(os.environ.get('SM2_LIFE_ACTIVE_RADIUS', '0')))   # island: cars only within this radius (m) of the camera   # island data: ~10x the lane length of Midtown, raise it with the data set
        tr.set_editor_property('stats_interval', 0.0)
        tr.set_editor_property('density_scale', DENSITY)
        tr.set_editor_property('street_density_factor', float(os.environ.get('SM2_LIFE_STREETF', '0.6')))
        tr.set_editor_property('bus_share', 0.07)
        sigp = os.path.join(DATA, 'signals.txt')
        if os.path.exists(sigp) and EAL.does_asset_exist(ROOT + '/Signals/M_LifeSignal'):
            tr.set_editor_property('signal_data', open(sigp).read())
            tr.set_editor_property('signal_mesh', load('/Engine/BasicShapes/Cylinder'))
            tr.set_editor_property('signal_material', load(ROOT + '/Signals/M_LifeSignal'))
        else: MISS.append('signals.txt / M_LifeSignal missing: no lit signal lenses')
        cits = sorted(p.split('.')[0] for p in EAL.list_assets(ROOT + '/Citizens', recursive=False)
                      if p.split('.')[0].split('/')[-1].startswith('SK_Citizen_') and isinstance(load(p.split('.')[0]), unreal.SkeletalMesh))
        cr = spawn(unreal.WHLifeCrowd, unreal.Vector(0, 0, 0), label='LifeCrowd')
        cr.set_editor_property('walk_data', walk)
        # 20 people x 5 outfits = 100 looks: the same mesh five times, the recoloured material as override (P6 twins fix, tools/life/citizen_variants.py; look = variant * 20 + citizen)
        looks = [(p, v) for v in ('', '_v1', '_v2', '_v3', '_v4') for p in cits]
        cr.set_editor_property('meshes', [load(p) for p, v in looks])
        cr.set_editor_property('material_overrides', [load('%s/Citizens/Materials/MI_LifeCit_%s%s' % (ROOT, p.split('SK_Citizen_')[-1], v)) if v else None for p, v in looks])
        cr.set_editor_property('anim_class', load(ROOT + '/Citizens/ABP_Life_Citizen').generated_class())
        cr.set_editor_property('traffic', tr)
        cr.set_editor_property('seed', 11)
        cr.set_editor_property('per_km_avenue', float(os.environ.get('SM2_LIFE_PERKM_AV', '1600')))     # walkers per km of sidewalk edge (round 03: 1600 / 1100; round 02 1300 / 860; round 01 950 / 640). Keep equal to the C++ default (a value equal to the default is not serialised)
        cr.set_editor_property('per_km_street', float(os.environ.get('SM2_LIFE_PERKM_ST', '1100')))
        cr.set_editor_property('avenue_east_factor', float(os.environ.get('SM2_LIFE_EAST', '1.3')))      # density factor of the east avenue sidewalks (round 03). Keep equal to the C++ default
        cr.set_editor_property('num_variants', 5)
        cr.set_editor_property('pool_per_model', 6)
        pr = spawn(unreal.WHLifeProbe, unreal.Vector(0, 0, 0), label='LifeProbe')
        pr.set_editor_property('traffic', tr); pr.set_editor_property('crowd', cr)
        pr.set_editor_property('report_at', [8.0, 14.0, 20.0, 28.0])
        pr.set_editor_property('foot_from', 10.0); pr.set_editor_property('foot_to', 22.0)
        unreal.EditorLoadingAndSavingUtils.save_map(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(), ACTORS)
        L('actors: traffic (%d vehicle meshes), crowd (%d citizen meshes x 5 outfits)' % (len(TYPES), len(cits)))

        def add_sublevels(world):
            have = [l.get_path_name() for l in unreal.EditorLevelUtils.get_levels(world)]
            for lp in (CITY_GEO, RIG, ACTORS):
                nm = lp.split('/')[-1]
                if not any(('/' + nm + ':') in h or h.endswith(nm) or (nm + '.') in h for h in have):
                    unreal.EditorLevelUtils.add_level_to_world(world, lp, unreal.LevelStreamingAlwaysLoaded)
            les.set_current_level_by_name(str(world.get_name()))

        def make_map(path, cam=None, rig=None, start=False):
            world = open_level(path)
            add_sublevels(world)
            if start:
                ps = SHOTS['S1']['player']
                spawn(unreal.PlayerStart, Um(ps[0], ps[2], ps[1] + 1.0), -90.0, 'PlayerStart')
            if cam:
                b = lambda v: Um(v[0], v[2], v[1])
                p, t = b(cam['pos']), b(cam['target'])
                d = unreal.Vector(t.x - p.x, t.y - p.y, t.z - p.z)
                rot = unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(d.z, math.hypot(d.x, d.y))), yaw=math.degrees(math.atan2(d.y, d.x)))
                ca = eas.spawn_actor_from_class(unreal.CameraActor, p, rot)
                ca.set_actor_label('ShotCam_' + cam['id'])
                ca.camera_component.set_editor_property('field_of_view', cam.get('fov', 70))
                ca.camera_component.set_editor_property('constrain_aspect_ratio', False)
                ca.set_editor_property('auto_activate_for_player', unreal.AutoReceiveInput.PLAYER0)
            if rig:
                sv = lambda v: Um(v[0], v[2], v[1])   # rig points are browser (x, y up, z south) like city_shots.json
                r = eas.spawn_actor_from_class(unreal.WHLifeCamRig, sv(rig['start']), unreal.Rotator(0, 0, 0))
                r.set_actor_label('LifeCamRig')
                try: r.set_editor_property('auto_activate_for_player', unreal.AutoReceiveInput.PLAYER0)
                except Exception as e: MISS.append('camera rig auto activate: ' + str(e)[:80])
                for k, v in (('start', sv(rig['start'])), ('end', sv(rig['end'])), ('duration', rig['duration']), ('eye_height', rig.get('eye', 170.0)),
                             ('look_height_delta', rig.get('lookup', 250.0)), ('yaw_sway_deg', rig.get('sway', 5.0)), ('fov_degrees', rig.get('fov', 68.0)),
                             ('hold_seconds', rig.get('hold', 0.0)), ('loop', rig.get('loop', False))):
                    r.set_editor_property(k, v)
                if 'aim' in rig:
                    r.set_editor_property('aim_at_target', True); r.set_editor_property('aim_target', sv(rig['aim']))
                if 'aim_ahead' in rig:
                    r.set_editor_property('aim_ahead_cm', rig['aim_ahead'][0] * 100.0); r.set_editor_property('aim_ahead_height_cm', rig['aim_ahead'][1] * 100.0)
            ok = unreal.EditorLoadingAndSavingUtils.save_map(world, path)
            L('map', path, 'saved' if ok else 'SAVE FAILED', 'levels', len(unreal.EditorLevelUtils.get_levels(world)))

        make_map(TESTS + '/Life_Midtown', start=True)
        make_map(TESTS + '/Life_View_S1', cam=SHOTS['S1'])
        make_map(TESTS + '/Life_View_S2', cam=SHOTS['S2'])
        # street-level clip: walks north through the free curb lane of the avenue's west side (browser x 241.0; the curb parking is cleared for the walk with -WHLifeClearParked, see
        # capture_round.sh), z 150.5 -> 123.5 (1.5 m/s), eye 1.8 m, aimed 10 deg to the left of north. This is the S1 storefront stretch (P1 thins its street trees out there, so the
        # west sidewalk, 3.5-6.5 m to the left, is open): two-way flow seen obliquely with parallax. The rig holds still for 2.5 s (warm-up, trimmed by the capture script), then walks 18 s.
        make_map(TESTS + '/Life_Street_Clip', rig={'start': (241.0, 0.15, 150.5), 'end': (241.0, 0.15, 123.5), 'duration': 18.0, 'eye': 180.0, 'aim': (223.0, 1.6, 50.0), 'fov': 75.0, 'hold': 2.5})
        # swing-height clip (round 03): 22 m above the avenue centre line, heading north at 25 m/s for 10 s, the camera always aimed at the ground 70 m ahead of itself (constant pitch about 17 deg down,
        # 88 deg lens like the swing camera): both sidewalks and the lanes of the nearest blocks fill the lower half of the frame (round 02: 30 m up, aimed at a fixed point 150-400 m away, the street was a sliver)
        make_map(TESTS + '/Life_Swing_Clip', rig={'start': (250.0, 0.15, 232.0), 'end': (250.0, 0.15, -18.0), 'duration': 10.0, 'eye': 2200.0, 'aim_ahead': (70.0, 0.0), 'fov': 88.0, 'hold': 2.5})
        # signal clip: fixed camera 7.5 m up on the avenue centre line, 18 m behind the tail of the queue of the southbound lanes (links 1201 / 1202) that stops at the signal of street 160
        # (z 155-165); the P1 mast at its far corner (238.1, 165.9) has its heads facing the camera. 10 s after the 2.5 s warm-up: cycle phase 36 -> 46 s (capture_round.sh -WHLifeSignalPhase=33.5), red until 40 s (clip t = 4 s), green after
        make_map(TESTS + '/Life_Signal_Clip', rig={'start': (248.5, 0.15, 106.0), 'end': (248.5, 0.15, 106.0), 'duration': 10.0, 'eye': 750.0, 'aim': (246.0, 3.0, 165.0), 'fov': 52.0, 'hold': 2.5})
        if MISS:
            L('WARNINGS (%d):' % len(MISS))
            for m_ in MISS: print('    ', m_)
    if MISS and 'map' not in STEPS:
        L('WARNINGS (%d):' % len(MISS))
        for m_ in MISS: print('    ', m_)
    L('DONE steps', sorted(STEPS))
    for m_ in MISS:
        if m_.startswith(COSMETIC_MISS): _B.warn(m_)
        else: _B.fail(m_)
    if 'map' in STEPS and not EAL.does_asset_exist(TESTS + '/Life_Actors'): _B.fail('missing ' + TESTS + '/Life_Actors')
    _B.finish()


if IN_UE:
    build_in_ue()
elif __name__ == '__main__':
    main()

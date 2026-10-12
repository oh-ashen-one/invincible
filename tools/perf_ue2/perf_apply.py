# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F: perf transformations of the LOCAL, script-generated city content (never committed; /Content stays out of git). Idempotent.
# Run in a headless commandlet of THIS worktree, editor and game closed (use tools/perf_ue2/perf_content.sh, which backs the touched files up):
#   "<UnrealEditor>" <uproject> -run=pythonscript -script=<abs>/tools/perf_ue2/perf_apply.py -unattended -nullrhi -RenderOffScreen -NoSound
# env SM2_PERF_APPLY = comma list of steps (default: none). Each step is one measured hypothesis (docs/night1/perf/round-01/):
#   static        City/Props + City/Far instanced components Movable -> Static. Movable HISMs put every instance in the GPU-scene
#                 "dynamic" set (SceneCulling/NumDynamicInstances 55 644 vs 450 static) and in the VSM dynamic layer: culled / invalidated every frame.
#   far_rt        hinterland (City/Far, 28 965 instances, 5-30 km out): out of the ray-tracing scene + Lumen scene + distance-field lighting
#   far_plain     hinterland mesh Nanite off (10 triangles per box: Nanite instance culling of 29k instances costs more than it saves)
#   kit_plain     City/streetkit + City/detail tiles Nanite off (masked + two-sided => Nanite programmable raster; ~5 k triangles per tile)
#   tree_lumen    trees (City/Props leaves + bark) out of the Lumen scene / DF lighting (no tree bounce / reflection; keeps direct shadows)
#   tree_rt       trees out of the ray-tracing scene
#   props_far_cull  City/Props components get a max draw distance of SM2_PERF_DRAWDIST cm (default 250000 = 2.5 km)
#   rt_lite       (round 02) City/Far (hinterland), City/Props (trees) and City/far (far ground) out of the hardware ray-tracing scene only
#                 (visible_in_ray_tracing = False; nothing else changes). Makes hardware-RT Lumen reflections cost ~+1.9 ms instead of ~+4.1 ms.
#   cloud         (round 02) VolumetricCloud TracingMaxDistance = SM2_PERF_CLOUD_KM km (default 20 since round 04; round 03 shipped 4) in the look rigs SM2_PERF_RIGS (default golden,midday,night):
#                 /Game/Look/Rigs/Look_Rig_<rig>. The cost is min(TracingMaxDistance, DistanceToSampleMaxCount = 15 km) / 15 km of the full ray-march.
#   rt_lite_trees (round 04) = rt_lite, but the tree LEAVES (City/Props ISM_ez_*_leaves, ISM_trees_*crownfar) stay IN the ray-tracing scene (bark, street furniture,
#                 parked cars, hinterland, far ground out): hardware-RT Lumen GI is occluded by the canopy again (round-03 critic: canopy luma 2x without it).
#                 Sets visible_in_ray_tracing on every City/Props component explicitly, so it also undoes a previous rt_lite run.
#   tree_rt_opaque (round 04) the leaf meshes' sections are flagged force_opaque (ray tracing only: no any-hit shader for the alpha-masked leaf cards; the raster
#                 passes keep the alpha mask). Measured as r.RayTracing.DebugForceOpaque in round-04 session y; this is the per-asset form of it.
#                 Env SM2_PERF_OPAQUE_SKIP (default '' = every leaf mesh opaque): leaf meshes whose ISM label contains it stay alpha-masked; '_l0_' keeps the LOD0
#                 street trees next to the street-level cameras masked (closer S1 canopy, but +0.6 ms p50 / +0.9 ms p95: session z1 ship_a vs ship_op). Not undone by a re-run.
#   rt_proxy_trees (round 05, round-04 critic: merge the ~42 k leaf / crown ray-tracing instances per city tile into <= 1 k ray-tracing proxies)
#                 imports the per-tile proxy GLBs of tools/perf_ue2/tree_proxy_build.py (env SM2_PERF_PROXY_DIR, default _scratch/perf/rtproxy) into
#                 /Game/PerfF/RTProxy (non-Nanite, no distance field: section 'leaf' = M_CityCrown (opaque two-sided foliage), 'bark' = the bark MI of the city),
#                 one static actor per tile in folder City/RTProxy that is visible ONLY to ray tracing (render_in_main_pass / render_in_depth_pass off,
#                 no shadow, no distance-field lighting, not in reflection / sky captures) and takes every tree HISM (leaves, crown masses AND bark) out of
#                 the ray-tracing scene. Raster, shadows and distance fields of the trees are unchanged. Idempotent (old proxy actors + assets are replaced).
#                 Env SM2_PERF_PROXY_LUMEN_ORIG=0 also takes the original tree HISMs out of the Lumen scene (their surface-cache cards are never hit any more).
# `all` = static,far_rt,far_plain,kit_plain.  Output log: env SM2_PERF_APPLY_LOG (default _scratch/perf/apply.json)
import unreal, json, os, time

STEPS = set(x for x in os.environ.get('SM2_PERF_APPLY', '').split(',') if x)
if 'all' in STEPS: STEPS |= {'static', 'far_rt', 'far_plain', 'kit_plain'}
CLOUD_KM = float(os.environ.get('SM2_PERF_CLOUD_KM', '20'))   # round 04: 20 km (round 03: 4)
RIGS = [x for x in os.environ.get('SM2_PERF_RIGS', 'golden,midday,night').split(',') if x]
LOG = os.environ.get('SM2_PERF_APPLY_LOG', '/Users/midir/sm2-n1/_scratch/perf/apply.json')
GEO = os.environ.get('SM2_PERF_GEO', '/Game/Tests/City/City_Midtown_Geo')
DRAW = float(os.environ.get('SM2_PERF_DRAWDIST', '250000'))
OPQ_SKIP = os.environ.get('SM2_PERF_OPAQUE_SKIP', '')   # tree_rt_opaque leaves leaf meshes whose ISM label contains this alpha-masked in ray tracing ('' = none; '_l0_' = the near-LOD street trees: +0.6 / +0.9 ms, session z1)
EAL = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
rep = {'steps': sorted(STEPS), 'geo': GEO, 'changed': {}}
t0 = time.time()
unreal.EditorLoadingAndSavingUtils.load_map(GEO)


def comps(*folders):
    for a in eas.get_all_level_actors():
        f = str(a.get_folder_path())
        if f in folders:
            for c in a.get_components_by_class(unreal.PrimitiveComponent):
                if isinstance(c, (unreal.StaticMeshComponent,)): yield a, c


def bump(k, n=1): rep['changed'][k] = rep['changed'].get(k, 0) + n


def nanite_off(sm, key):
    ns = sm.get_editor_property('nanite_settings')
    if ns.enabled:
        ns.enabled = False; sm.set_editor_property('nanite_settings', ns)
        EAL.save_asset(sm.get_path_name()); bump(key)


def prop(c, name, v, key):
    try:
        if c.get_editor_property(name) != v: c.set_editor_property(name, v); bump(key)
    except Exception as e:
        rep.setdefault('errors', []).append('%s.%s: %s' % (c.get_class().get_name(), name, str(e)[:100]))


if 'static' in STEPS:
    for a, c in comps('City/Props', 'City/Far'):
        if str(c.get_editor_property('mobility')).split('.')[-1].split(':')[0] != 'STATIC':
            c.set_mobility(unreal.ComponentMobility.STATIC); bump('static')
if 'far_rt' in STEPS:
    for a, c in comps('City/Far'):
        prop(c, 'visible_in_ray_tracing', False, 'far_rt_visible_in_ray_tracing')
        prop(c, 'affect_dynamic_indirect_lighting', False, 'far_rt_lumen')
        prop(c, 'affect_distance_field_lighting', False, 'far_rt_df')
        prop(c, 'cast_shadow', False, 'far_rt_cast_shadow')
if 'far_plain' in STEPS:
    for a, c in comps('City/Far'):
        sm = c.get_editor_property('static_mesh')
        if sm: nanite_off(sm, 'far_plain_mesh')
if 'kit_plain' in STEPS:
    for a, c in comps('City/streetkit', 'City/detail'):
        sm = c.get_editor_property('static_mesh')
        if sm: nanite_off(sm, 'kit_plain_mesh')
if 'tree_lumen' in STEPS:
    for a, c in comps('City/Props'):
        sm = c.get_editor_property('static_mesh')
        if sm and ('_leaves' in sm.get_name() or '_bark' in sm.get_name() or 'trees_' in sm.get_name()):
            prop(c, 'affect_dynamic_indirect_lighting', False, 'tree_lumen'); prop(c, 'affect_distance_field_lighting', False, 'tree_df')
if 'tree_rt' in STEPS:
    for a, c in comps('City/Props'):
        sm = c.get_editor_property('static_mesh')
        if sm and ('_leaves' in sm.get_name() or '_bark' in sm.get_name() or 'trees_' in sm.get_name()):
            prop(c, 'visible_in_ray_tracing', False, 'tree_rt')
if 'props_far_cull' in STEPS:
    for a, c in comps('City/Props'):
        prop(c, 'ld_max_draw_distance', DRAW, 'props_far_cull')
if 'rt_lite' in STEPS:
    for a, c in comps('City/Far', 'City/Props', 'City/far'):
        prop(c, 'visible_in_ray_tracing', False, 'rt_lite')

def is_leaves(label): return (label.startswith('ISM_ez_') and label.endswith('_leaves')) or (label.startswith('ISM_trees_') and 'crown' in label)


if 'rt_lite_trees' in STEPS:
    for a, c in comps('City/Far', 'City/far'):
        prop(c, 'visible_in_ray_tracing', False, 'rt_lite_trees_out')
    for a, c in comps('City/Props'):
        want = is_leaves(a.get_actor_label())
        prop(c, 'visible_in_ray_tracing', want, 'rt_lite_trees_in' if want else 'rt_lite_trees_out')
if 'tree_rt_opaque' in STEPS:
    seen = set()
    for a, c in comps('City/Props'):
        if not is_leaves(a.get_actor_label()): continue
        if OPQ_SKIP and OPQ_SKIP in a.get_actor_label(): continue
        sm = c.get_editor_property('static_mesh')
        if not sm or sm.get_path_name() in seen: continue
        seen.add(sm.get_path_name())
        sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem) or unreal.new_object(unreal.StaticMeshEditorSubsystem)   # None in a -nullrhi commandlet; the UFUNCTIONs only touch the mesh passed in
        changed = False
        for lod in range(sm.get_num_lods()):
            for sec in range(sm.get_num_sections(lod)):
                try:
                    if not sms.is_section_force_opaque_enabled(sm, lod, sec):
                        sms.enable_section_force_opaque(sm, True, lod, sec); changed = True
                except Exception as e:
                    rep.setdefault('errors', []).append('force_opaque %s: %s' % (sm.get_name(), str(e)[:120]))
        if changed: EAL.save_asset(sm.get_path_name()); bump('tree_rt_opaque_mesh')
    rep['tree_rt_opaque_meshes'] = sorted(seen)

def is_tree_part(label): return is_leaves(label) or (label.startswith('ISM_ez_') and label.endswith('_bark'))


if 'rt_proxy_trees' in STEPS:
    PDIR = os.environ.get('SM2_PERF_PROXY_DIR', '/Users/midir/sm2-n1/_scratch/perf/rtproxy')
    PROOT = '/Game/PerfF/RTProxy'
    tiles = json.load(open(os.path.join(PDIR, 'tiles.json')))
    # 1. old proxy actors out (their meshes are about to be deleted: a referenced asset would block the delete), then the old assets
    n_old = 0
    for a in eas.get_all_level_actors():
        if str(a.get_folder_path()) == 'City/RTProxy': eas.destroy_actor(a); n_old += 1
    rep['rt_proxy_old_actors'] = n_old
    les.save_current_level()
    reuse = os.environ.get('SM2_PERF_PROXY_REUSE', '0') == '1' and all(EAL.does_asset_exist('%s/SM_%s' % (PROOT, t['name'])) for t in tiles)   # flags-only re-run: keep the imported meshes
    rep['rt_proxy_reused_meshes'] = reuse
    if EAL.does_directory_exist(PROOT) and not reuse: EAL.delete_directory(PROOT)
    # 2. import (Interchange, no Nanite, no materials / textures)
    p = unreal.InterchangeGenericAssetsPipeline()
    p.common_meshes_properties.set_editor_properties({'recompute_normals': False, 'recompute_tangents': False, 'remove_degenerates': False})
    p.mesh_pipeline.set_editor_properties({'generate_lightmap_u_vs': False, 'build_nanite': False})
    try: p.mesh_pipeline.set_editor_property('combine_static_meshes', False)
    except Exception as e: rep.setdefault('warnings', []).append('combine_static_meshes: ' + str(e)[:80])
    p.material_pipeline.set_editor_property('import_materials', False)
    p.material_pipeline.texture_pipeline.set_editor_property('import_textures', False)
    tasks = []
    for f in ([] if reuse else sorted(set(t.get('file', t['name']) for t in tiles))):   # round 05: several tiles per GLB (tree_proxy_build.py packs), one static mesh per glTF mesh
        tk = unreal.AssetImportTask(); tk.filename = os.path.join(PDIR, 'tiles', f + '.glb'); tk.destination_path = PROOT + '/_in'
        tk.automated = True; tk.replace_existing = True; tk.save = False; tk.options = p; tasks.append(tk)
    if tasks: unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    crown = unreal.load_asset('/Game/City/Materials/M_CityCrown')
    bark_mat = None
    for a, c in comps('City/Props'):
        if a.get_actor_label().startswith('ISM_ez_street0_l1_bark'): bark_mat = c.get_materials()[0]
    sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem) or unreal.new_object(unreal.StaticMeshEditorSubsystem)
    n_new, missing, tris = 0, [], 0
    found = {}
    if not reuse and EAL.does_directory_exist(PROOT + '/_in'):
        for ap_ in EAL.list_assets(PROOT + '/_in', recursive=True):
            nm_ = ap_.split('.')[0].split('/')[-1]
            if nm_.startswith('RTP_') and isinstance(unreal.load_asset(ap_.split('.')[0]), unreal.StaticMesh): found[nm_] = ap_.split('.')[0]
    todo_save = []
    for t in tiles:   # phase 1: rename, materials, build settings (the async mesh builds run in parallel)
        dst = '%s/SM_%s' % (PROOT, t['name'])
        if not reuse:
            src = found.get(t['name'])
            if not src: missing.append(t['name']); continue
            EAL.rename_asset(src, dst)
        sm = unreal.load_asset(dst)
        for i, sl in enumerate(sm.get_editor_property('static_materials')):
            nm = str(sl.get_editor_property('material_slot_name'))
            sm.set_material(i, bark_mat if (nm.startswith('bark') and bark_mat) else crown)
        ns = sm.get_editor_property('nanite_settings')
        if ns.enabled: ns.enabled = False; sm.set_editor_property('nanite_settings', ns)
        bs = sms.get_lod_build_settings(sm, 0)
        for k_, v_ in (('recompute_normals', False), ('recompute_tangents', False), ('generate_lightmap_u_vs', False), ('distance_field_resolution_scale', 0.0)):
            try: bs.set_editor_property(k_, v_)
            except Exception as e: rep.setdefault('errors', []).append('build settings %s: %s' % (k_, str(e)[:80]))
        # no collision at all on the proxy meshes (round 05: with the Interchange default complex collision the hidden proxies still blocked the
        # PlayerStart and the origin: 'NO PLAYERSTART with positive rating', no hero, the perf route ran without the swing)
        bset = sm.get_editor_property('body_setup')
        coll_changed = False
        if bset:
            if bset.get_editor_property('collision_trace_flag') != unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX:
                bset.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX); coll_changed = True
            try: sms.remove_collisions(sm)
            except Exception as e: rep.setdefault('warnings', []).append('remove_collisions: ' + str(e)[:80])
        if not reuse:
            sms.set_lod_build_settings(sm, 0, bs); todo_save.append(dst)
        elif coll_changed: todo_save.append(dst)
    for dst in todo_save: EAL.save_asset(dst)   # phase 2: save (waits for each build; most are done by now)
    for t in tiles:   # phase 3: one hidden, ray-tracing-only actor per tile
        dst = '%s/SM_%s' % (PROOT, t['name'])
        if t['name'] in missing: continue
        sm = unreal.load_asset(dst)
        c_ = t['center_cm']
        act = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(c_[0], c_[1], c_[2]), unreal.Rotator(0, 0, 0))
        act.set_actor_label('RTP_' + t['name']); act.set_folder_path('City/RTProxy')
        smc = act.static_mesh_component; smc.set_static_mesh(sm); act.set_mobility(unreal.ComponentMobility.STATIC)
        # ray tracing only = HIDDEN in game + 'affect indirect lighting while hidden' (engine RayTracing.cpp keeps a hidden primitive in the game view's
        # ray-tracing scene only when it retains while hidden; RayTracingInstanceMask.cpp gives it the indirect (Lumen / reflection) mask bits then).
        # render_in_main_pass must stay ON: FRayTracingMeshProcessor and the Lumen card capture skip primitives that do not render in the main pass
        # (round-05 first try: render_in_main_pass off = no occlusion at all, S1 canopy luma 1.93x as found).
        for k_, v_ in (('hidden_in_game', True), ('affect_indirect_lighting_while_hidden', True), ('cast_hidden_shadow', False), ('cast_shadow', False),
                       ('render_in_main_pass', True), ('render_in_depth_pass', True), ('visible_in_ray_tracing', True),
                       ('affect_distance_field_lighting', False), ('affect_dynamic_indirect_lighting', True), ('visible_in_reflection_captures', False),
                       ('visible_in_real_time_sky_captures', False), ('receives_decals', False), ('generate_overlap_events', False)):
            prop(smc, k_, v_, 'rt_proxy_flags')
        smc.set_collision_profile_name('NoCollision'); smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        for k_, v_ in (('can_character_step_up_on', unreal.CanBeCharacterBase.ECB_NO), ('can_ever_affect_navigation', False)):
            try: smc.set_editor_property(k_, v_)
            except Exception as e: rep.setdefault('warnings', []).append('%s: %s' % (k_, str(e)[:60]))
        n_new += 1; tris += sum(t['tris'].values())
    if EAL.does_directory_exist(PROOT + '/_in'): EAL.delete_directory(PROOT + '/_in')
    # 3. the originals leave the ray-tracing scene (raster / shadows / distance fields unchanged)
    lum_orig = os.environ.get('SM2_PERF_PROXY_LUMEN_ORIG', '1') != '0'
    for a, c in comps('City/Props'):
        if is_tree_part(a.get_actor_label()):
            prop(c, 'visible_in_ray_tracing', False, 'rt_proxy_orig_out')
            prop(c, 'affect_dynamic_indirect_lighting', lum_orig, 'rt_proxy_orig_lumen')
    rep['rt_proxy'] = {'tiles': len(tiles), 'actors': n_new, 'missing': missing[:20], 'tris': tris, 'bark_material': bark_mat.get_path_name() if bark_mat else None,
                       'orig_in_lumen_scene': lum_orig, 'report': json.load(open(os.path.join(PDIR, 'report.json'))) if os.path.exists(os.path.join(PDIR, 'report.json')) else None}
    if rep['rt_proxy']['report']: rep['rt_proxy']['report'].pop('meshes', None)
    if missing: rep.setdefault('errors', []).append('rt_proxy: %d tiles not imported' % len(missing))

ok = les.save_current_level()
if 'cloud' in STEPS:  # the rigs are separate levels: load, change, save each (the geometry level above is already saved)
    for rig in RIGS:
        path = '/Game/Look/Rigs/Look_Rig_' + rig
        if not EAL.does_asset_exist(path): rep.setdefault('errors', []).append('rig missing ' + path); continue
        unreal.EditorLoadingAndSavingUtils.load_map(path)
        for a in eas.get_all_level_actors():
            if isinstance(a, unreal.VolumetricCloud):
                vc = a.get_component_by_class(unreal.VolumetricCloudComponent)
                rep['changed']['cloud_' + rig + '_old_km'] = float(vc.get_editor_property('tracing_max_distance'))
                vc.set_editor_property('tracing_max_distance', CLOUD_KM); bump('cloud_' + rig)
        les.save_current_level()
rep['saved'] = bool(ok); rep['secs'] = round(time.time() - t0, 1)
os.makedirs(os.path.dirname(LOG), exist_ok=True)
json.dump(rep, open(LOG, 'w'), indent=1)
print('[perf_apply]', json.dumps(rep))

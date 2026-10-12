# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F (round 03): LOCAL A/B copies of the ray-tracing-scene policy of the city props, made from the SHIPPED (already perf_apply'd) geometry level, so a control and a
# treatment can share one lock session / one still capture. Content is script-generated and never committed. Nothing shared is modified: the copies live in
# /Game/PerfF/RTv<tag>/ and their map copies point at them.
#   RTvA   all of City/Props visible in ray tracing again (trees, street furniture, parked cars)
#   RTvB   trees (ISM_ez_*, ISM_trees_*: 80 k instances) stay OUT; street furniture and parked cars back IN (the shipped RT-lite has all of City/Props out)
#   RTvC   trees IN, street furniture and parked cars OUT (which half of the S1 glass loss is which?)
#   RTvD   shipped RT-lite, but the far ground (City/far, 136 far-LOD tiles) back IN the ray-tracing scene (hardware GI sees the far city, not sky)
#   RTvE   shipped RT-lite, but the hinterland (City/Far, 29 k ten-triangle boxes) back IN
#   RTvF   D + E
#   RTvL   (round 04) tree LEAVES in (ISM_*_leaves + ISM_trees_*crownfar), bark / street furniture / parked cars OUT: half the tree instances of RTvC
#   RTvR   (round 05 control) = the round-04 shipped content on today's build: the tree ray-tracing proxies (City/RTProxy) OUT of the ray-tracing scene,
#          the leaf / crown HISMs (42 k instances, force-opaque sections) back IN, bark out
#   RTvN   (round 05) no tree geometry in the ray-tracing scene at all (proxies out, leaves out)
#   RTvX   (round 05 diagnosis) the shipped level with the proxy ACTORS deleted (everything else as shipped)
# Round 04: env SM2_PERF_RTVAR_CLOUD_KM=<km> also copies the golden look rig with VolumetricCloud TracingMaxDistance = <km> into /Game/PerfF/RTv<tag>k<km>/
#   and swaps it into the map copies (tag suffix k<km>, e.g. RTvCk20 = trees in the ray-tracing scene + cloud 20 km), so trees + cloud share one A/B map.
# Run in a headless commandlet of THIS worktree (editor + game closed, no GPU):
#   SM2_PERF_RTVARS=A,B "<UnrealEditor>" <uproject> -run=pythonscript -script=<abs>/tools/perf_ue2/make_rtvars.py -unattended -nullrhi -RenderOffScreen -NoSound
import unreal, json, os, time

TAGS = [x for x in os.environ.get('SM2_PERF_RTVARS', 'B').split(',') if x]
CLOUD_KM = os.environ.get('SM2_PERF_RTVAR_CLOUD_KM', '')
RIG = '/Game/Look/Rigs/Look_Rig_golden'
GEO = '/Game/Tests/City/City_Midtown_Geo'
MAPS = ['/Game/Maps/Manhattan', '/Game/Maps/Manhattan_View_S1', '/Game/Maps/Manhattan_View_S2', '/Game/PerfF/View_S7']
LOG = os.environ.get('SM2_PERF_VAR_LOG', '/Users/midir/sm2-n1/_scratch/perf/r03/rtvars.json')
EAL = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
rep = {}
t0 = time.time()


def is_tree(label): return label.startswith('ISM_ez_') or label.startswith('ISM_trees_')


def fresh_copy(src, dst):
    if EAL.does_asset_exist(dst): EAL.delete_asset(dst)
    if not EAL.duplicate_asset(src, dst): raise RuntimeError('duplicate failed %s -> %s' % (src, dst))


for t in TAGS:
    tag = 'RTv' + t + ('k' + CLOUD_KM if CLOUD_KM else '')
    base = '/Game/PerfF/' + tag
    geo_dst = base + '/City_Midtown_Geo'
    rig_dst = None
    if CLOUD_KM:
        rig_dst = base + '/Look_Rig_golden'
        fresh_copy(RIG, rig_dst)
        unreal.EditorLoadingAndSavingUtils.load_map(rig_dst)
        rw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        for a in eas.get_all_level_actors():
            if isinstance(a, unreal.VolumetricCloud):
                a.get_component_by_class(unreal.VolumetricCloudComponent).set_editor_property('tracing_max_distance', float(CLOUD_KM))
        unreal.EditorLoadingAndSavingUtils.save_map(rw, rig_dst)
    fresh_copy(GEO, geo_dst)
    unreal.EditorLoadingAndSavingUtils.load_map(geo_dst)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    n_on = n_off = inst_on = 0
    if t in 'DEF':
        for a in eas.get_all_level_actors():
            f = str(a.get_folder_path())
            if (f == 'City/far' and t in 'DF') or (f == 'City/Far' and t in 'EF'):
                for c in a.get_components_by_class(unreal.StaticMeshComponent):
                    c.set_editor_property('visible_in_ray_tracing', True); n_on += 1
                    inst_on += c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
    if t == 'X':
        for a in eas.get_all_level_actors():
            if str(a.get_folder_path()) == 'City/RTProxy': eas.destroy_actor(a); n_off += 1
    if t in 'RN':
        for a in eas.get_all_level_actors():
            if str(a.get_folder_path()) == 'City/RTProxy':
                for c in a.get_components_by_class(unreal.StaticMeshComponent): c.set_editor_property('visible_in_ray_tracing', False); n_off += 1
    for a in eas.get_all_level_actors():
        if t in 'DEFX' or str(a.get_folder_path()) != 'City/Props': continue
        tree = is_tree(a.get_actor_label())
        leaves = tree and not a.get_actor_label().endswith('_bark')
        want = {'A': True, 'B': not tree, 'C': tree, 'L': leaves, 'R': leaves, 'N': False}[t]
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            c.set_editor_property('visible_in_ray_tracing', want)
            n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
            if want: n_on += 1; inst_on += n
            else: n_off += 1
    rep[tag] = {'cloud_km': CLOUD_KM or None, 'props_components_in_rt': n_on, 'props_instances_in_rt': inst_on, 'props_components_out': n_off, 'geo_saved': bool(unreal.EditorLoadingAndSavingUtils.save_map(world, geo_dst)), 'maps': {}}
    for m in MAPS:
        name = m.split('/')[-1]
        dst = base + '/' + name
        if not EAL.does_asset_exist(m): rep[tag]['maps'][name] = 'source missing'; continue
        fresh_copy(m, dst)
        unreal.EditorLoadingAndSavingUtils.load_map(dst)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        for lvl in list(unreal.EditorLevelUtils.get_levels(world)):
            if 'City_Midtown_Geo' in lvl.get_path_name() and tag not in lvl.get_path_name():
                unreal.EditorLevelUtils.remove_level_from_world(lvl)
        unreal.EditorLevelUtils.add_level_to_world(world, geo_dst, unreal.LevelStreamingAlwaysLoaded)
        if rig_dst:
            for lvl in list(unreal.EditorLevelUtils.get_levels(world)):
                if 'Look_Rig_golden' in lvl.get_path_name() and tag not in lvl.get_path_name():
                    unreal.EditorLevelUtils.remove_level_from_world(lvl)
            unreal.EditorLevelUtils.add_level_to_world(world, rig_dst, unreal.LevelStreamingAlwaysLoaded)
        les.set_current_level_by_name(str(world.get_name()))
        ok = unreal.EditorLoadingAndSavingUtils.save_map(world, dst)
        rep[tag]['maps'][name] = {'saved': bool(ok), 'levels': [l.get_path_name().split('.')[0].split('/')[-1] for l in unreal.EditorLevelUtils.get_levels(world)]}
rep['secs'] = round(time.time() - t0, 1)
os.makedirs(os.path.dirname(LOG), exist_ok=True)
json.dump(rep, open(LOG, 'w'), indent=1)
print('[perf_rtvars]', json.dumps(rep))

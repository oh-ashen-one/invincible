# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F: LOCAL map variants for A/B perf runs of ONE look setting, so a control and a treatment share one exclusive lock session
# (session drift is up to 1.6 ms, see docs/night1/perf/round-01/NOTES.md section 2). Nothing shared is modified: the look rig and the maps
# are duplicated under /Game/PerfF/<Tag>/ and the copies point at each other. Content is script-generated and never committed.
#
#   Cl<N>    /Game/PerfF/Cl<N>/  = golden rig copy whose VolumetricCloud component has TracingMaxDistance = N km (2p5 = 2.5)
#            (look_presets.json golden: 50 km) + the maps Manhattan, Manhattan_View_S1, Manhattan_View_S2, PerfF/View_S7 with that rig swapped in.
#   Cl<N>RT[1-3]P the trailing P also removes the street people (skeletal meshes of /Game/Maps/Manhattan_Actors) from the ray-tracing scene; the hero is spawned by code and stays.
#   Cl<N>RT[1-3] the same, plus a copy of /Game/Tests/City/City_Midtown_Geo in which the hinterland (City/Far), the trees (City/Props) and the far
#            ground (City/far) are removed from the hardware ray-tracing scene (visible_in_ray_tracing = False; nothing else changes), for the
#            "hardware-RT reflections, small ray-tracing scene" cost probe.
#
# Run in a headless commandlet of THIS worktree (editor + game closed, no GPU):
#   SM2_PERF_CLOUD_KM=15,10 "<UnrealEditor>" <uproject> -run=pythonscript -script=<abs>/tools/perf_ue2/make_variants.py -unattended -nullrhi -RenderOffScreen -NoSound
# env SM2_PERF_CLOUD_KM (comma list of km, default "15"; a trailing RT makes a Cl<N>RT tag), SM2_PERF_RIG (default golden), SM2_PERF_VAR_LOG (json report)
import unreal, json, os, time

KMS = [x for x in os.environ.get('SM2_PERF_CLOUD_KM', '15').split(',') if x]   # e.g. "15,6,6RT"
GEO = '/Game/Tests/City/City_Midtown_Geo'
RIG = os.environ.get('SM2_PERF_RIG', 'golden')
LOG = os.environ.get('SM2_PERF_VAR_LOG', '/Users/midir/sm2-n1/_scratch/perf/variants.json')
SRC_RIG = '/Game/Look/Rigs/Look_Rig_' + RIG
MAPS = ['/Game/Maps/Manhattan', '/Game/Maps/Manhattan_View_S1', '/Game/Maps/Manhattan_View_S2', '/Game/PerfF/View_S7']
EAL = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
rep = {'rig': RIG, 'variants': {}}
t0 = time.time()


def fresh_copy(src, dst):
    if EAL.does_asset_exist(dst): EAL.delete_asset(dst)
    if not EAL.duplicate_asset(src, dst): raise RuntimeError('duplicate failed %s -> %s' % (src, dst))


import re
for spec in KMS:
    m = re.match(r'^(\d+(?:p\d+)?)(RT[123]?)?(P)?(?:D(\d+))?$', spec)
    if not m: raise RuntimeError('bad variant spec %s (km[RT[1-3]][P][D<metres>])' % spec)
    km, rt, dist, peds = m.group(1), bool(m.group(2)), int(m.group(4) or 0), bool(m.group(3))
    rtlevel = int((m.group(2) or 'RT')[2:] or 1)
    tag = 'Cl' + km + (m.group(2) or '') + ('P' if peds else '') + ('D%d' % dist if dist else '')
    km = km.replace('p', '.')
    base = '/Game/PerfF/' + tag
    v = rep['variants'][tag] = {'km': float(km), 'rt_lite': rt, 'tree_draw_distance_m': dist, 'maps': {}}
    # 1) rig copy with the cloud setting changed
    rig_dst = base + '/Look_Rig_' + RIG
    fresh_copy(SRC_RIG, rig_dst)
    unreal.EditorLoadingAndSavingUtils.load_map(rig_dst)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    n = 0
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.VolumetricCloud):
            c = a.get_component_by_class(unreal.VolumetricCloudComponent)
            v['old_km'] = float(c.get_editor_property('tracing_max_distance'))
            c.set_editor_property('tracing_max_distance', float(km))
            v['new_km'] = float(c.get_editor_property('tracing_max_distance'))
            v['tracing_start_max_distance'] = float(c.get_editor_property('tracing_start_max_distance'))
            n += 1
    v['cloud_actors'] = n
    v['rig_saved'] = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, rig_dst))
    geo_dst = None
    if rt or dist:  # geometry copy with the RT-lite transformation and / or the tree draw distance
        geo_dst = base + '/City_Midtown_Geo'
        fresh_copy(GEO, geo_dst)
        unreal.EditorLoadingAndSavingUtils.load_map(geo_dst)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        cnt = dcnt = 0
        for a in eas.get_all_level_actors():
            if str(a.get_folder_path()) in ('City/Far', 'City/Props', 'City/far'):
                for c in a.get_components_by_class(unreal.PrimitiveComponent):
                    if rt and isinstance(c, unreal.StaticMeshComponent) and c.get_editor_property('visible_in_ray_tracing'):
                        c.set_editor_property('visible_in_ray_tracing', False); cnt += 1
                    if dist and str(a.get_folder_path()) == 'City/Props' and isinstance(c, unreal.HierarchicalInstancedStaticMeshComponent):
                        for prop, val in (('ld_max_draw_distance', float(dist * 100)), ('instance_end_cull_distance', int(dist * 100))):
                            try: c.set_editor_property(prop, val)
                            except Exception as e: v.setdefault('errors', []).append('%s: %s' % (prop, str(e)[:80]))
                        dcnt += 1
        if rt and rtlevel >= 2:   # RT2: also the Nanite street kit + detail tiles; RT3: only facade / roofs / ground stay in the ray-tracing scene
            drop = ('City/streetkit', 'City/detail') if rtlevel == 2 else ('City/streetkit', 'City/detail', 'City/signage', 'City/markings', 'City/generic')
            for a in eas.get_all_level_actors():
                if str(a.get_folder_path()) in drop:
                    for c in a.get_components_by_class(unreal.StaticMeshComponent):
                        if c.get_editor_property('visible_in_ray_tracing'): c.set_editor_property('visible_in_ray_tracing', False); cnt += 1
        v['rt_removed_components'] = cnt; v['draw_distance_components'] = dcnt; v['rt_level'] = rtlevel if rt else 0
        v['geo_saved'] = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, geo_dst))
    actors_dst = None
    if peds:  # street-people sublevel copy: their skeletal meshes out of the ray-tracing scene (the hero stays in)
        actors_dst = base + '/Manhattan_Actors'
        fresh_copy('/Game/Maps/Manhattan_Actors', actors_dst)
        unreal.EditorLoadingAndSavingUtils.load_map(actors_dst)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        n = 0
        for a in eas.get_all_level_actors():
            for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
                if c.get_editor_property('visible_in_ray_tracing'): c.set_editor_property('visible_in_ray_tracing', False); n += 1
        v['peds_rt_removed'] = n; v['actors_saved'] = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, actors_dst))
    # 2) map copies whose golden-rig sublevel is the copy
    for m in MAPS:
        name = m.split('/')[-1]
        dst = base + '/' + name
        if not EAL.does_asset_exist(m): v['maps'][name] = 'source missing'; continue
        fresh_copy(m, dst)
        unreal.EditorLoadingAndSavingUtils.load_map(dst)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        removed = 0
        for lvl in list(unreal.EditorLevelUtils.get_levels(world)):
            pn = lvl.get_path_name()
            if 'Look_Rig_' + RIG in pn and tag not in pn:
                if unreal.EditorLevelUtils.remove_level_from_world(lvl): removed += 1
        unreal.EditorLevelUtils.add_level_to_world(world, rig_dst, unreal.LevelStreamingAlwaysLoaded)
        if actors_dst:
            for lvl in list(unreal.EditorLevelUtils.get_levels(world)):
                if 'Manhattan_Actors' in lvl.get_path_name() and tag not in lvl.get_path_name():
                    unreal.EditorLevelUtils.remove_level_from_world(lvl)
            unreal.EditorLevelUtils.add_level_to_world(world, actors_dst, unreal.LevelStreamingAlwaysLoaded)
        if geo_dst:
            for lvl in list(unreal.EditorLevelUtils.get_levels(world)):
                if 'City_Midtown_Geo' in lvl.get_path_name() and tag not in lvl.get_path_name():
                    unreal.EditorLevelUtils.remove_level_from_world(lvl)
            unreal.EditorLevelUtils.add_level_to_world(world, geo_dst, unreal.LevelStreamingAlwaysLoaded)
        les.set_current_level_by_name(str(world.get_name()))
        ok = unreal.EditorLoadingAndSavingUtils.save_map(world, dst)
        v['maps'][name] = {'saved': bool(ok), 'removed_old_rig': removed, 'levels': [l.get_path_name().split('.')[0].split('/')[-1] for l in unreal.EditorLevelUtils.get_levels(world)]}
rep['secs'] = round(time.time() - t0, 1)
os.makedirs(os.path.dirname(LOG), exist_ok=True)
json.dump(rep, open(LOG, 'w'), indent=1)
print('[perf_variants]', json.dumps(rep))

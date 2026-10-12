# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F (round 03): read the REBUILT, shipped-path content back and record what the perf transformations left in it. Read-only (nothing is saved).
# Run in a headless commandlet of THIS worktree (tools/perf_ue2/build_map.py step perf_audit does it):
#   "<UnrealEditor>" <uproject> -run=pythonscript -script=<abs>/tools/perf_ue2/perf_audit.py -unattended -nullrhi -RenderOffScreen -NoSound
# env SM2_PERF_AUDIT_OUT = json report (default _scratch/perf/audit_r03.json)
# Records: per actor folder of the geometry level (components, instances, how many are visible in the hardware ray-tracing scene), the VolumetricCloud
# TracingMaxDistance of every look rig, the skeletal meshes of the street-people level, and whether the integrated maps exist.
import unreal, json, os, time

OUT = os.environ.get('SM2_PERF_AUDIT_OUT', '/Users/midir/sm2-n1/_scratch/perf/audit_r03.json')
GEO = os.environ.get('SM2_PERF_GEO', '/Game/Tests/City/City_Midtown_Geo')
RIGS = ['golden', 'midday', 'night']
MAPS = ['/Game/Maps/Manhattan', '/Game/Maps/Manhattan_Midday', '/Game/Maps/Manhattan_Night', '/Game/Maps/Manhattan_Actors',
        '/Game/Maps/Manhattan_View_S1', '/Game/Maps/Manhattan_View_S2', '/Game/Maps/Manhattan_View_S4']
EAL = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rep = {'geo': GEO, 'folders': {}, 'rigs': {}, 'maps': {}, 'people': {}, 'summary': {}}
t0 = time.time()

unreal.EditorLoadingAndSavingUtils.load_map(GEO)
tot = {'components': 0, 'instances': 0, 'rt_components': 0, 'rt_instances': 0}
for a in eas.get_all_level_actors():
    f = str(a.get_folder_path()) or '(none)'
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
        rt = bool(c.get_editor_property('visible_in_ray_tracing'))
        d = rep['folders'].setdefault(f, {'components': 0, 'instances': 0, 'rt_components': 0, 'rt_instances': 0})
        d['components'] += 1; d['instances'] += n
        tot['components'] += 1; tot['instances'] += n
        if rt: d['rt_components'] += 1; d['rt_instances'] += n; tot['rt_components'] += 1; tot['rt_instances'] += n
rep['geo_total'] = tot

for rig in RIGS:
    path = '/Game/Look/Rigs/Look_Rig_' + rig
    if not EAL.does_asset_exist(path): rep['rigs'][rig] = 'missing'; continue
    unreal.EditorLoadingAndSavingUtils.load_map(path)
    km = []
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.VolumetricCloud):
            km.append(float(a.get_component_by_class(unreal.VolumetricCloudComponent).get_editor_property('tracing_max_distance')))
    rep['rigs'][rig] = {'cloud_tracing_max_distance_km': km}

for m in MAPS: rep['maps'][m] = EAL.does_asset_exist(m)

ppl = '/Game/Maps/Manhattan_Actors'
if EAL.does_asset_exist(ppl):
    unreal.EditorLoadingAndSavingUtils.load_map(ppl)
    n = rt = 0
    for a in eas.get_all_level_actors():
        for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
            n += 1; rt += 1 if bool(c.get_editor_property('visible_in_ray_tracing')) else 0
    rep['people'] = {'skeletal_components': n, 'visible_in_ray_tracing': rt}

rep['summary'] = {'rt_instances': tot['rt_instances'], 'instances': tot['instances'],
                  'cloud_km': {k: (v['cloud_tracing_max_distance_km'] if isinstance(v, dict) else v) for k, v in rep['rigs'].items()},
                  'maps_missing': [m for m, ok in rep['maps'].items() if not ok], 'people': rep['people'], 'secs': round(time.time() - t0, 1)}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(rep, open(OUT, 'w'), indent=1, sort_keys=True)
print('[perf_audit]', json.dumps(rep['summary']))

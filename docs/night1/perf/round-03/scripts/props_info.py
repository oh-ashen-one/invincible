import unreal, json
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Tests/City/City_Midtown_Geo')
rows = []
for a in eas.get_all_level_actors():
    f = str(a.get_folder_path())
    if f not in ('City/Props', 'City/Traffic'): continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
        sm = c.get_editor_property('static_mesh')
        rows.append((f, a.get_actor_label(), sm.get_name() if sm else None, n, bool(c.get_editor_property('visible_in_ray_tracing')), int(sm.get_num_triangles(0)) if sm and hasattr(sm, 'get_num_triangles') else -1))
rows.sort(key=lambda r: -r[3])
json.dump(rows, open('/Users/midir/sm2-n1/_scratch/perf/r03/props_info.json', 'w'), indent=1)
print('[props_info]', len(rows))

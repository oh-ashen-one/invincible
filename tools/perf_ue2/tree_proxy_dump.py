# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F (round 05): read-only dump of the tree instances of the rebuilt geometry level, input of tools/perf_ue2/tree_proxy_build.py.
# Run in a headless commandlet of THIS worktree (tools/perf_ue2/build_map.py step tree_proxy does it; editor and game closed):
#   "<UnrealEditor>" <uproject> -run=pythonscript -script=<abs>/tools/perf_ue2/tree_proxy_dump.py -unattended -nullrhi -RenderOffScreen -NoSound
# env SM2_PERF_PROXY_DUMP = output json (default _scratch/perf/tree_dump.json)
# For every City/Props HISM whose actor is a tree part (ISM_ez_*_leaves / _bark, ISM_trees_*crown*): the mesh, its local bounds and every instance's
# WORLD transform as a 4x4 row-major matrix (UE convention: row vector * M, translation in the last row, cm). Nothing is saved.
import unreal, json, os, time

OUT = os.environ.get('SM2_PERF_PROXY_DUMP', '/Users/midir/sm2-n1/_scratch/perf/tree_dump.json')
GEO = os.environ.get('SM2_PERF_GEO', '/Game/Tests/City/City_Midtown_Geo')
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
t0 = time.time()
unreal.EditorLoadingAndSavingUtils.load_map(GEO)


def is_tree(label):
    return (label.startswith('ISM_ez_') and (label.endswith('_leaves') or label.endswith('_bark'))) or (label.startswith('ISM_trees_') and 'crown' in label)


def mat4(t):
    m = t.to_matrix()
    return [[m.x_plane.x, m.x_plane.y, m.x_plane.z, m.x_plane.w], [m.y_plane.x, m.y_plane.y, m.y_plane.z, m.y_plane.w],
            [m.z_plane.x, m.z_plane.y, m.z_plane.z, m.z_plane.w], [m.w_plane.x, m.w_plane.y, m.w_plane.z, m.w_plane.w]]


rep = {'geo': GEO, 'components': []}
for a in eas.get_all_level_actors():
    if str(a.get_folder_path()) != 'City/Props' or not is_tree(a.get_actor_label()): continue
    for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
        sm = c.get_editor_property('static_mesh')
        if not sm: continue
        b = sm.get_bounds()
        mats = [str(m.get_path_name()) if m else None for m in c.get_materials()]
        xs = []
        for i in range(c.get_instance_count()):
            r = c.get_instance_transform(i, True)
            t = r[1] if isinstance(r, tuple) else r
            xs.append([round(v, 4) for row in mat4(t) for v in row])
        rep['components'].append({'label': a.get_actor_label(), 'mesh': sm.get_path_name(), 'mesh_name': sm.get_name(),
                                  'bounds_origin': [b.origin.x, b.origin.y, b.origin.z], 'bounds_extent': [b.box_extent.x, b.box_extent.y, b.box_extent.z],
                                  'materials': mats, 'visible_in_ray_tracing': bool(c.get_editor_property('visible_in_ray_tracing')), 'instances': xs})
rep['secs'] = round(time.time() - t0, 1)
rep['n_instances'] = sum(len(c['instances']) for c in rep['components'])
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(rep, open(OUT, 'w'))
print('[tree_proxy_dump]', json.dumps({k: rep[k] for k in ('geo', 'secs', 'n_instances')}), len(rep['components']), 'components')

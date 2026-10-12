# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F: READ-ONLY audit of what /Game/Maps/Manhattan renders (run inside a headless commandlet of THIS worktree, editor closed):
#   "<UnrealEditor>" <uproject> -run=pythonscript -script=tools/perf_ue2/audit_content.py -unattended -nullrhi -RenderOffScreen -NoSound
# Nothing is saved. Output: env SM2_PERF_AUDIT (default /Users/midir/sm2-n1/_scratch/perf/audit.json)
# Per group (actor folder / component kind): actors, components, instances, mobility, Nanite on/off, triangles (LOD0), LOD count,
# UV channels, material count / blend modes (masked / translucent), cast shadow, collision, WPO use.
import unreal, json, os, collections, time

OUT = os.environ.get('SM2_PERF_AUDIT', '/Users/midir/sm2-n1/_scratch/perf/audit.json')
MAP = os.environ.get('SM2_PERF_AUDIT_MAP', '/Game/Maps/Manhattan')
T0 = time.time()
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem) if hasattr(unreal, 'StaticMeshEditorSubsystem') else None
mesh_info = {}


def minfo(sm):
    p = sm.get_path_name()
    if p in mesh_info: return mesh_info[p]
    d = {'path': p}
    try: d['nanite'] = bool(sm.get_editor_property('nanite_settings').enabled)
    except Exception: d['nanite'] = None
    try:
        d['lods'] = sm.get_num_lods()
        d['tris_lod0'] = sm.get_num_triangles(0)
        d['verts_lod0'] = sm.get_num_vertices(0)
    except Exception as e: d['err'] = str(e)[:80]
    try: d['uv_channels'] = sm.get_num_uv_channels(0)
    except Exception: pass
    try: d['sections'] = sm.get_num_sections(0)
    except Exception: pass
    mats = []
    try:
        for sm_mat in sm.get_editor_property('static_materials'):
            mi = sm_mat.get_editor_property('material_interface')
            if not mi: continue
            base = mi.get_base_material() if hasattr(mi, 'get_base_material') else mi
            bm = str(base.get_editor_property('blend_mode')).split('.')[-1] if base else '?'
            wpo = False
            try: wpo = bool(unreal.MaterialEditingLibrary.get_material_property_input_node(base, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET))
            except Exception: pass
            two = False
            try: two = bool(base.get_editor_property('two_sided'))
            except Exception: pass
            mats.append({'mi': mi.get_name(), 'base': base.get_name() if base else None, 'blend': bm, 'wpo': wpo, 'two_sided': two})
    except Exception as e: d['mat_err'] = str(e)[:80]
    d['materials'] = mats
    try: d['df'] = bool(sm.get_editor_property('generate_mesh_distance_field')) if False else None
    except Exception: pass
    mesh_info[p] = d
    return d


groups = collections.OrderedDict()
levels = collections.Counter()
for a in eas.get_all_level_actors():
    lvl = a.get_outer().get_outer().get_name() if a.get_outer() else '?'
    levels[lvl] += 1
    folder = str(a.get_folder_path()) or '(none)'
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        kind = c.get_class().get_name()
        g = groups.setdefault((lvl, folder, kind), {'level': lvl, 'folder': folder, 'component': kind, 'actors': set(), 'components': 0,
                                                    'instances': 0, 'mobility': collections.Counter(), 'nanite': collections.Counter(),
                                                    'tris_total': 0, 'tris_lod0_max': 0, 'uv_max': 0, 'blend': collections.Counter(),
                                                    'wpo_materials': 0, 'cast_shadow': collections.Counter(), 'collision': collections.Counter(),
                                                    'visible': collections.Counter(), 'meshes': collections.Counter(), 'lods': collections.Counter()})
        g['actors'].add(a.get_path_name()); g['components'] += 1
        try: g['mobility'][str(c.get_editor_property('mobility')).split('.')[-1]] += 1
        except Exception: pass
        try: g['cast_shadow'][bool(c.get_editor_property('cast_shadow'))] += 1
        except Exception: pass
        try: g['collision'][str(c.get_collision_enabled()).split('.')[-1]] += 1
        except Exception: pass
        try: g['visible'][bool(c.is_visible())] += 1
        except Exception: pass
        n = 1
        if isinstance(c, unreal.InstancedStaticMeshComponent):
            n = c.get_instance_count()
        g['instances'] += n
        if isinstance(c, unreal.StaticMeshComponent):
            sm = c.get_editor_property('static_mesh')
            if sm:
                mi = minfo(sm)
                g['nanite'][mi.get('nanite')] += n
                g['tris_total'] += (mi.get('tris_lod0') or 0) * n
                g['tris_lod0_max'] = max(g['tris_lod0_max'], mi.get('tris_lod0') or 0)
                g['uv_max'] = max(g['uv_max'], mi.get('uv_channels') or 0)
                g['lods'][mi.get('lods')] += 1
                g['meshes'][sm.get_name()] += n
                for m in mi['materials']:
                    g['blend'][m['blend']] += 1
                    if m['wpo']: g['wpo_materials'] += 1

res = []
for g in groups.values():
    g = dict(g); g['actors'] = len(g['actors'])
    for k in ('mobility', 'nanite', 'blend', 'cast_shadow', 'collision', 'visible', 'lods'):
        g[k] = {str(a): b for a, b in g[k].items()}
    g['distinct_meshes'] = len(g['meshes']); g['top_meshes'] = dict(g['meshes'].most_common(6)); del g['meshes']
    res.append(g)
res.sort(key=lambda g: -g['tris_total'])
lights = collections.Counter()
for a in eas.get_all_level_actors():
    for c in a.get_components_by_class(unreal.LightComponentBase):
        try: lights['%s shadows=%s' % (c.get_class().get_name(), bool(c.get_editor_property('cast_shadows')))] += 1
        except Exception: lights[c.get_class().get_name()] += 1
out = {'map': MAP, 'levels': dict(levels), 'groups': res, 'lights': dict(lights),
       'meshes': sorted(mesh_info.values(), key=lambda m: -(m.get('tris_lod0') or 0))[:60], 'secs': round(time.time() - T0, 1)}
json.dump(out, open(OUT, 'w'), indent=1, default=str)
print('[perf_audit] wrote', OUT, len(res), 'groups', len(mesh_info), 'meshes')

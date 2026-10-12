import unreal, json
out = {}
EAL = unreal.EditorAssetLibrary
paths = ['/Game/Traversal/HeroDev/HeroDev/SkeletalMeshes/SpiderMan', '/Game/Traversal/HeroDev/HeroDev/SkeletalMeshes/Lenses']
import os
# a couple of street people
ppl = [p for p in EAL.list_assets('/Game/Characters', recursive=True, include_folder=False) if '/SK_' in p or '/SKM_' in p][:6]
paths += [p.split('.')[0] for p in ppl]
lib = unreal.EditorSkeletalMeshLibrary
for p in paths:
    if not EAL.does_asset_exist(p): out[p] = 'missing'; continue
    sm = unreal.load_asset(p)
    d = {'class': sm.get_class().get_name()}
    try:
        n = lib.get_lod_count(sm); d['lods'] = n
        d['per_lod'] = [{'verts': lib.get_num_verts(sm, i)} for i in range(n)]
    except Exception as e: d['err'] = str(e)[:200]
    try: d['materials'] = len(sm.get_editor_property('materials'))
    except Exception as e: pass
    try:
        d['allow_cpu'] = bool(sm.get_editor_property('support_ray_tracing')) if 'support_ray_tracing' in [x for x in dir(sm)] else None
    except Exception as e: pass
    out[p] = d
json.dump(out, open('/Users/midir/sm2-n1/_scratch/perf/r03/mesh_info.json', 'w'), indent=1)
print('[mesh_info]', json.dumps(out)[:3000])

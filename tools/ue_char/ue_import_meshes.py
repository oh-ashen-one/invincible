# UE-side (run through tools/ue_char/uebox.py). Imports hero / thug / suits into /Game/Characters via Interchange glTF.
# ARGS: {"which": ["hero","thug","suits"]}. Fan homage project; not official Marvel/Sony/Insomniac.
import unreal, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '.')); from p2paths import WT as _P2WT, scr as _scr  # noqa: E402
SRC = _scr('ueimport')
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
HERO_SKEL = '/Game/Characters/Hero/SKEL_Hero'

def pipeline(skeleton=None, anims=True):
    p = unreal.InterchangeGenericAssetsPipeline()
    mp = p.get_editor_property('mesh_pipeline')
    mp.set_editor_property('build_nanite', False)
    mp.set_editor_property('create_physics_asset', skeleton is None)
    mp.set_editor_property('import_static_meshes', False)
    mp.set_editor_property('use_high_precision_skin_weights', True)
    cm = p.get_editor_property('common_meshes_properties')
    cm.set_editor_property('recompute_normals', False)       # keep authored glTF normals
    cm.set_editor_property('recompute_tangents', True)       # glTF hero has no TANGENT: MikkTSpace in UE
    cm.set_editor_property('use_mikk_t_space', True)
    cm.set_editor_property('use_high_precision_tangent_basis', True)
    cm.set_editor_property('use_full_precision_u_vs', True)
    cs = p.get_editor_property('common_skeletal_meshes_and_animations_properties')
    if skeleton:
        cs.set_editor_property('skeleton', unreal.load_asset(skeleton))
    ap = p.get_editor_property('animation_pipeline')
    ap.set_editor_property('import_animations', anims)
    ap.set_editor_property('custom_bone_animation_sample_rate', 30)   # source keys are exactly 1/30 s
    ap.set_editor_property('use30_hz_to_bake_bone_animation', False)
    mat = p.get_editor_property('material_pipeline')
    mat.set_editor_property('import_materials', False)
    mat.get_editor_property('texture_pipeline').set_editor_property('import_textures', False)
    return p

def do_import(fname, dest, skeleton=None, anims=True):
    src = unreal.InterchangeManager.create_source_data(os.path.join(SRC, fname))
    prm = unreal.ImportAssetParameters()
    prm.is_automated = True
    prm.replace_existing = True
    p = pipeline(skeleton, anims)
    try:
        prm.override_pipelines.append(unreal.SoftObjectPath(p.get_path_name()))
    except Exception:
        prm.override_pipelines.append(p)
    mgr = unreal.InterchangeManager.get_interchange_manager_scripted()
    ok = mgr.import_asset(dest, src, prm)
    unreal.InterchangeManager.get_interchange_manager_scripted().wait_until_all_tasks_done(True)
    got = EAL.list_assets(dest, recursive=True)
    print('import', fname, '->', dest, ok, len(got))
    return got

def mv(old, new):
    if EAL.does_asset_exist(new):
        EAL.delete_asset(new)
    if not EAL.rename_asset(old, new):
        print('RENAME FAIL', old, new)

def organise(tmp, root, prefix, mesh_name, keep_skel=True):
    for p in EAL.list_assets(tmp, recursive=True):
        p = p.split('.')[0]; a = unreal.load_asset(p); base = p.split('/')[-1]
        if isinstance(a, unreal.AnimSequence):
            clip = base[len(prefix):] if base.startswith(prefix) else base
            mv(p, '%s/Anims/A_%s_%s' % (root, mesh_name, clip))
        elif isinstance(a, unreal.SkeletalMesh):
            mv(p, '%s/SK_%s' % (root, mesh_name))
        elif isinstance(a, unreal.Skeleton):
            mv(p, '%s/SKEL_%s' % (root, mesh_name))
        elif isinstance(a, unreal.PhysicsAsset):
            mv(p, '%s/PHYS_%s' % (root, mesh_name))
        else:
            print('left', p, type(a).__name__)
    EAL.delete_directory(tmp)

which = ARGS.get('which', ['hero'])
if 'hero' in which:
    for d in ('/Game/Characters/_ImportTest', '/Game/Characters/Hero', '/Game/Characters/_tmp'):
        if EAL.does_directory_exist(d): EAL.delete_directory(d)
    do_import('Hero.glb', '/Game/Characters/_tmp/Hero')
    organise('/Game/Characters/_tmp/Hero', '/Game/Characters/Hero', 'Hero', 'Hero')
if 'thug' in which:
    if EAL.does_directory_exist('/Game/Characters/Thug'): EAL.delete_directory('/Game/Characters/Thug')
    do_import('Thug.glb', '/Game/Characters/_tmp/Thug', skeleton=HERO_SKEL)
    organise('/Game/Characters/_tmp/Thug', '/Game/Characters/Thug', 'Thug', 'Thug')
if 'suits' in which:
    for s in ARGS.get('suits', ['Claude', 'Codex', 'Gemini', 'Kimi', 'Qwen']):
        root = '/Game/Characters/Suits/' + s
        for p in EAL.list_assets(root, recursive=False) if EAL.does_directory_exist(root) else []:
            if p.split('/')[-1].startswith('SK_'): EAL.delete_asset(p.split('.')[0])
        do_import('Suit_%s.glb' % s, '/Game/Characters/_tmp/Suit_' + s, skeleton=HERO_SKEL, anims=False)
        organise('/Game/Characters/_tmp/Suit_' + s, root, 'Suit_' + s, 'Suit_' + s)
EAL.save_directory('/Game/Characters', only_if_is_dirty=True, recursive=True)
for p in EAL.list_assets('/Game/Characters', recursive=True):
    if '/Anims/' not in p: print(' ', p)
print('anims', len([p for p in EAL.list_assets('/Game/Characters', recursive=True) if '/Anims/' in p]))

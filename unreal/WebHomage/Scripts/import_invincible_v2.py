"""Import the v2 Invincible-homage hero (CustomUse rig, 52 bones) + its animation clips as /Game/Invincible/HeroV2/.

Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation. Source: docs/invincible/character
(CustomUse mesh + rig, Meshy-based / hand-keyed clips, merged by tools/invincible/merge_hero_clips.py into
Saved/P2Build/invincible/SK_InvincibleV2.glb). Unlike v1 this hero keeps its OWN skeleton (owner choice: keep the CustomUse rig);
the game drives it with UWHHeroV2AnimInstance (clip-based flight states). Materials + 4K texture come from the glTF.
Run headless through the GPU guard (build_manhattan.ue_python); prints SM2_BUILD_OK: import_invincible_v2.py and a CLIPS line.
env: WH_INVINCIBLE_V2_GLB (default <project>/Saved/P2Build/invincible/SK_InvincibleV2.glb)
"""
import os
import unreal

DEST = '/Game/Invincible/HeroV2'
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
proj = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
glb = os.environ.get('WH_INVINCIBLE_V2_GLB', os.path.join(proj, 'Saved/P2Build/invincible/SK_InvincibleV2.glb'))
if not os.path.isfile(glb):
    raise FileNotFoundError('run tools/invincible/merge_hero_clips.py first: ' + glb)

p = unreal.InterchangeGenericAssetsPipeline()
mp = p.get_editor_property('mesh_pipeline')
mp.set_editor_property('build_nanite', False)
mp.set_editor_property('create_physics_asset', False)
mp.set_editor_property('import_static_meshes', False)
mp.set_editor_property('use_high_precision_skin_weights', True)
cm = p.get_editor_property('common_meshes_properties')
cm.set_editor_property('recompute_normals', False)
cm.set_editor_property('recompute_tangents', True)
cm.set_editor_property('use_mikk_t_space', True)
ap = p.get_editor_property('animation_pipeline')
ap.set_editor_property('import_animations', True)
mat = p.get_editor_property('material_pipeline')
mat.set_editor_property('import_materials', True)
mat.get_editor_property('texture_pipeline').set_editor_property('import_textures', True)
EAL.make_directory(DEST)
# re-import: Interchange skips animations whose targets were renamed to AS_* by a previous run (only the mesh came back) -- clear this
# script's own clip folder first so every run imports every clip fresh
# (deleting only the clips was not enough: with the mesh present Interchange re-imports the mesh alone) -- the whole folder is this
# script's own output, so clear it and import fresh, exactly like the first run
for x in EAL.list_assets(DEST, recursive=True, include_folder=False): EAL.delete_asset(x)
t = unreal.AssetImportTask(); t.filename = glb; t.destination_path = DEST; t.destination_name = 'SK_InvincibleV2'
t.automated = True; t.replace_existing = True; t.save = False
stack = unreal.InterchangePipelineStackOverride(); stack.add_pipeline(p); t.options = stack
AT.import_asset_tasks([t])
paths = list(t.imported_object_paths)
print('[invincible-v2] imported', len(paths), 'objects')
sk = None; clips = []
for x in paths:
    a = unreal.load_asset(x)
    if isinstance(a, unreal.SkeletalMesh): sk = a
    if isinstance(a, unreal.AnimSequence): clips.append(a)
if not sk:
    raise RuntimeError('no SkeletalMesh imported from ' + glb)
# stable names the C++ looks up: AS_<clip> (A_Hover -> AS_Hover ...)
out = []
for a in clips:
    nm = a.get_name(); key = nm[nm.find('A_') + 2:] if 'A_' in nm else nm
    want = DEST + '/Anims/AS_' + key
    EAL.make_directory(DEST + '/Anims')
    if a.get_path_name().split('.')[0] != want:
        if EAL.does_asset_exist(want): EAL.delete_asset(want)
        EAL.rename_asset(a.get_path_name().split('.')[0], want)
    out.append('AS_' + key)
# -game runs cannot set usage flags on demand ("missing usage flag SkeletalMesh! Default Material will be used" -> plain white hero)
MEL = unreal.MaterialEditingLibrary
for x in EAL.list_assets(DEST, recursive=False, include_folder=False):
    m = unreal.load_asset(x)
    if isinstance(m, unreal.Material):
        ok = m.set_editor_property('used_with_skeletal_mesh', True)
        MEL.recompile_material(m); print('[invincible-v2] material usage SkeletalMesh set on', m.get_name())
for x in EAL.list_assets(DEST, recursive=True, include_folder=False):
    EAL.save_asset(x, only_if_is_dirty=False)
print('CLIPS', sorted(out))
print('MESH', sk.get_path_name(), 'SKELETON', sk.get_editor_property('skeleton').get_path_name())
print('SM2_BUILD_OK: import_invincible_v2.py')

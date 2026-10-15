"""Import the Invincible-homage hero (tools/ue_char/invincible/blender_invincible_hero.py output) as /Game/Invincible/Characters/SK_Invincible.

Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation. Original geometry (this project's own hero rig).
The mesh is bound to the PLAYABLE hero's skeleton (the HeroDev SpiderMan asset's skeleton), so the traversal anim instance plays every existing
clip on it. Flat zone colours: one MaterialInstanceConstant per slot (InvYellow / InvBlue / InvBlack / InvSkin / InvHair / LensFrame / Lens) on
/Game/Combat/Materials/M_CmbSolid's simple lit parent when present, otherwise the glTF importer's own materials. The game picks it up when the
asset exists (AWebTravCharacter: flight mode default; -WHHeroMesh= / -WHHeroLens= override).
Run headless through the GPU guard (build_manhattan.ue_python); prints SM2_BUILD_OK: import_invincible_hero.py.
env: WH_INVINCIBLE_GLB = absolute path of SK_Invincible.glb (default <project>/Saved/P2Build/invincible/SK_Invincible.glb)
"""
import os
import unreal

DEST = '/Game/Invincible/Characters'
MAT_DEST = DEST + '/Materials'
HERO_DEV = '/Game/Traversal/HeroDev/HeroDev/SkeletalMeshes/SpiderMan.SpiderMan'
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
proj = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
glb = os.environ.get('WH_INVINCIBLE_GLB', os.path.join(proj, 'Saved/P2Build/invincible/SK_Invincible.glb'))
if not os.path.isfile(glb):
    raise FileNotFoundError('run tools/ue_char/invincible/blender_invincible_hero.py first: ' + glb)
hero_dev = unreal.load_asset(HERO_DEV)
if not hero_dev:
    raise RuntimeError('playable hero mesh missing: ' + HERO_DEV)
skel = hero_dev.get_editor_property('skeleton')
print('[invincible] skeleton', skel.get_path_name())

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
p.get_editor_property('common_skeletal_meshes_and_animations_properties').set_editor_property('skeleton', skel)
p.get_editor_property('animation_pipeline').set_editor_property('import_animations', False)
mat = p.get_editor_property('material_pipeline')
mat.set_editor_property('import_materials', False)
mat.get_editor_property('texture_pipeline').set_editor_property('import_textures', False)
EAL.make_directory(DEST); EAL.make_directory(MAT_DEST)
t = unreal.AssetImportTask(); t.filename = glb; t.destination_path = DEST; t.destination_name = 'SK_Invincible'
t.automated = True; t.replace_existing = True; t.save = False
stack = unreal.InterchangePipelineStackOverride(); stack.add_pipeline(p); t.options = stack
AT.import_asset_tasks([t])
paths = list(t.imported_object_paths)
print('[invincible] imported', paths)
sk = next((unreal.load_asset(x) for x in paths if isinstance(unreal.load_asset(x), unreal.SkeletalMesh)), None)
if not sk:
    raise RuntimeError('no SkeletalMesh imported from ' + glb)
if sk.get_editor_property('skeleton') != skel:
    raise RuntimeError('SK_Invincible is not bound to the playable hero skeleton')

# flat colours (sRGB -> linear), roughness, metallic: the same palette as the Blender generator
PAL = {'InvYellow': ('f2c21b', 0.62, 0.0), 'InvBlue': ('1f4ea6', 0.66, 0.0), 'InvBlack': ('121317', 0.55, 0.0), 'InvSkin': ('c99a7c', 0.55, 0.0),
       'InvHair': ('17110d', 0.60, 0.0), 'LensFrame': ('0f1013', 0.30, 0.6), 'Lens': ('ffcc33', 0.06, 0.0)}
def lin(h):
    def c(v):
        v = int(v, 16) / 255.0
        return ((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92
    return unreal.LinearColor(c(h[0:2]), c(h[2:4]), c(h[4:6]), 1.0)

# parent: a tiny lit master with BaseColor / Roughness / Metallic parameters (built here once, skeletal usage on)
MASTER = MAT_DEST + '/M_InvFlat'
if not EAL.does_asset_exist(MASTER):
    m = AT.create_asset('M_InvFlat', MAT_DEST, unreal.Material, unreal.MaterialFactoryNew())
    MEL = unreal.MaterialEditingLibrary
    bc = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -400, -100); bc.set_editor_property('parameter_name', 'BaseColor')
    ro = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -400, 100); ro.set_editor_property('parameter_name', 'Roughness'); ro.set_editor_property('default_value', 0.6)
    me = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -400, 200); me.set_editor_property('parameter_name', 'Metallic')
    MEL.connect_material_property(bc, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(ro, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(me, '', unreal.MaterialProperty.MP_METALLIC)
    m.set_editor_property('used_with_skeletal_mesh', True)
    MEL.recompile_material(m)
    EAL.save_asset(MASTER)
master = unreal.load_asset(MASTER)
out = []
for sm in sk.get_editor_property('materials'):
    slot = str(sm.get_editor_property('material_slot_name'))
    if slot in PAL:
        hexc, rough, metal = PAL[slot]
        path = MAT_DEST + '/MI_Inv_' + slot
        mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset('MI_Inv_' + slot, MAT_DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL = unreal.MaterialEditingLibrary
        MEL.set_material_instance_parent(mi, master)
        MEL.set_material_instance_vector_parameter_value(mi, 'BaseColor', lin(hexc))
        MEL.set_material_instance_scalar_parameter_value(mi, 'Roughness', rough)
        MEL.set_material_instance_scalar_parameter_value(mi, 'Metallic', metal)
        EAL.save_asset(path)
        sm.set_editor_property('material_interface', mi)
    out.append(sm)
sk.set_editor_property('materials', out)
EAL.save_asset(sk.get_path_name())
slots = [(str(m.get_editor_property('material_slot_name')), m.get_editor_property('material_interface').get_name() if m.get_editor_property('material_interface') else None)
         for m in unreal.load_asset(sk.get_path_name()).get_editor_property('materials')]
print('[invincible] slots', slots)
missing = [s for s, mi in slots if s in PAL and not (mi or '').startswith('MI_Inv_')]
if missing:
    raise RuntimeError('slots without a material: %s' % missing)
print('SM2_BUILD_OK: import_invincible_hero.py')

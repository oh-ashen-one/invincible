import bpy, sys
GLB, OUT = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=GLB, bone_heuristic='TEMPERANCE')
sc = bpy.context.scene; sc.render.fps = 24
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
for o in list(sc.objects):
    if o.type == 'MESH' and o.name.lower().startswith('icosphere'): bpy.data.objects.remove(o, do_unlink=True)
for tr in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(tr)
act = bpy.data.actions['A_Hover']; act.name = 'hover_testfit'
for x in list(bpy.data.actions):
    if x is not act: bpy.data.actions.remove(x)
arm.animation_data.action = act
try: arm.animation_data.action_slot = act.slots[0]
except Exception: pass
arm.scale = (0.01,) * 3
bpy.ops.wm.save_as_mainfile(filepath=OUT); print('TESTFIT saved', OUT)

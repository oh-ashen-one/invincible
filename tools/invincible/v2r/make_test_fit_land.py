# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.
# Test fixture for refine_hero.py: one game clip of the merged GLB on the project rig (bone_heuristic TEMPERANCE, armature scaled
# 0.01, scene 24 fps, one action), like make_test_fit.py, but for a GROUNDED one-shot: the armature object is shifted in z so the
# lowest mesh vertex at the LAST key is on z = 0 (the project floor), so the clip's feet-on-floor end pose stands on the floor.
#   Blender -b --factory-startup -P make_test_fit_land.py -- <SK.glb> <out.blend> [--action A_LandHero] [--name landhero_testfit]
import argparse, os, sys
import bpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import v2r_rig as R  # noqa: E402
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('out')
ap.add_argument('--action', default='A_LandHero'); ap.add_argument('--name', default='landhero_testfit')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a.glb, bone_heuristic='TEMPERANCE')
sc = bpy.context.scene; sc.render.fps = 24
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
for o in list(sc.objects):
    if o.type == 'MESH' and o.name.lower().startswith('icosphere'): bpy.data.objects.remove(o, do_unlink=True)
for tr in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(tr)
act = bpy.data.actions[a.action]; act.name = a.name
for x in list(bpy.data.actions):
    if x is not act: bpy.data.actions.remove(x)
R.assign_action(arm, act)
arm.scale = (0.01,) * 3
k0, k1 = R.key_range(act)
body = max((o for o in sc.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers)), key=lambda o: len(o.data.vertices))
R.set_frame(k1); bpy.context.view_layer.update()
z_end = float(R.mesh_world(body)[:, 2].min())
arm.location.z -= z_end
bpy.context.view_layer.update()
R.set_frame(k1); z_after = float(R.mesh_world(body)[:, 2].min())
R.set_frame(k0); z0 = float(R.mesh_world(body)[:, 2].min())
sc.frame_start, sc.frame_end = int(k0), int(round(k1 + 0.4999))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out))
print('TESTFIT saved %s action %s keys %.3f..%.3f (%.3f s at 24 fps) shift_z %.4f m lowest_vertex_last %.5f m lowest_vertex_first %.4f m'
      % (a.out, act.name, k0, k1, (k1 - k0) / 24.0, -z_end, z_after, z0))

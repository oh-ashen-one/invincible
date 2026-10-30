# Probe the game's merged clips: facing (left_foot - left_ankle, horizontal), pelvis and lowest-vertex heights at the first and
# last frame, object parenting and units. Blender -b --factory-startup -P clip_probe.py -- <merged.glb>
import bpy, sys, json
from mathutils import Vector
GLB = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB, bone_heuristic='TEMPERANCE')
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); body = next(o for o in sc.objects if o.type == 'MESH')
print('PARENT', body.parent.name if body.parent else None, 'arm scale', tuple(arm.scale), 'body scale', tuple(body.scale), 'arm rot', tuple(round(x, 3) for x in arm.rotation_euler), 'fps', sc.render.fps)
if arm.animation_data is None: arm.animation_data_create()
for tr in arm.animation_data.nla_tracks: tr.mute = True
def facts():
    bpy.context.view_layer.update()
    AW = arm.matrix_world; h = lambda n: AW @ arm.pose.bones[n].head
    deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps)
    zs = [(ev.matrix_world @ v.co).z for v in ev.data.vertices]
    f = h('left_foot') - h('left_ankle'); f.z = 0; f.normalize()
    return dict(fwd=[round(f.x, 2), round(f.y, 2)], pelvis_z=round(h('pelvis').z, 1), head_z=round(h('head').z, 1), low_z=round(min(zs), 1), high_z=round(max(zs), 1))
# rest pose first
arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
print('REST', json.dumps(facts()))
for act in bpy.data.actions:
    arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    f0, f1 = act.frame_range
    out = {}
    for tag, fr in (('first', f0), ('last', f1)):
        sc.frame_set(int(round(fr))); out[tag] = facts()
    print('CLIP', act.name, 'frames', int(f0), int(f1), json.dumps(out))

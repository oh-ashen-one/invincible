# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.
# video2rig project model for the Invincible-homage hero v2: the game's own merged GLB (SK_InvincibleV2.glb: rig + the 12 game
# clips) imported with child-pointing bone tails (TEMPERANCE), posed on ONE frame of ONE clip, every action stripped, feet (or the
# hover height) put on z = 0 -> model.blend for export_rig.py / render_start.py / reader.prepare.
#   Blender -b --factory-startup -P build_model.py -- <merged.glb> <out.blend> <action> <frame> <lowest_z_m> <facts.json>
import bpy, sys, json
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT, ACT, FRAME, LOW_Z, FACTS = a[0], a[1], a[2], float(a[3]), float(a[4]), a[5]
SCALE = float(a[6]) if len(a) > 6 else 1.0          # armature object scale (0.01: the merged GLB is in cm-like units, 200 per hero)
MATCH_YAW = '--match-rest-yaw' in a                # yaw the pelvis so the feet-forward matches the REST pose's (one facing for every picture)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB, bone_heuristic='TEMPERANCE')
sc = bpy.context.scene; sc.render.fps = 30
for o in list(sc.objects):
    if o.type == 'MESH' and o.name.lower().startswith('icosphere'): bpy.data.objects.remove(o, do_unlink=True)
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
body = next(o for o in sc.objects if o.type == 'MESH')
act = bpy.data.actions.get(ACT)
if act is None: raise SystemExit('no action %s; have %s' % (ACT, [x.name for x in bpy.data.actions]))
if arm.animation_data is None: arm.animation_data_create()
# the importer may have put the clips on NLA tracks: mute them and evaluate the chosen action alone
for tr in arm.animation_data.nla_tracks: tr.mute = True
arm.animation_data.action = act
try: arm.animation_data.action_slot = act.slots[0]
except Exception: pass
bpy.context.view_layer.update()
def feet_fwd():
    AW = arm.matrix_world; h = lambda n: AW @ arm.pose.bones[n].head
    f = h('left_foot') - h('left_ankle'); f.z = 0; f.normalize(); return f
arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update(); rest_fwd = feet_fwd()
arm.animation_data.action = act
try: arm.animation_data.action_slot = act.slots[0]
except Exception: pass
sc.frame_set(int(round(FRAME)))
bpy.context.view_layer.update()
if MATCH_YAW:
    from mathutils import Matrix
    import math
    f = feet_fwd(); yaw = math.atan2(rest_fwd.y, rest_fwd.x) - math.atan2(f.y, f.x)
    pel = arm.pose.bones['pelvis']; M = pel.matrix.copy(); t = M.to_translation()
    pel.matrix = Matrix.Translation(t) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation(-t) @ M
    bpy.context.view_layer.update(); print('MATCH_YAW rotated pelvis by %.1f deg; feet fwd now %s' % (math.degrees(yaw), tuple(round(x, 3) for x in feet_fwd())))
basis = {pb.name: pb.matrix_basis.copy() for pb in arm.pose.bones}
arm.animation_data.action = None
for tr in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(tr)
arm.animation_data_clear()
for x in list(bpy.data.actions): bpy.data.actions.remove(x)
for pb in arm.pose.bones: pb.matrix_basis = basis[pb.name]
bpy.context.view_layer.update()
def bounds():
    deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps)
    co = [ev.matrix_world @ v.co for v in ev.data.vertices]
    lo = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
    hi = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
    return lo, hi
arm.scale = (SCALE, SCALE, SCALE)
bpy.context.view_layer.update()
lo, hi = bounds()
arm.location.z += LOW_Z - lo.z
bpy.context.view_layer.update()
lo, hi = bounds()
AW = arm.matrix_world
def head(n): return AW @ arm.pose.bones[n].head
fwd = head('left_foot') - head('left_ankle'); fwd.z = 0; fwd.normalize()
left = head('left_hip') - head('right_hip'); left.z = 0; left.normalize()
fwd2 = Vector((0, 0, 1)).cross(left)   # facing from the hips: up x left = forward
bpy.ops.wm.save_as_mainfile(filepath=OUT)
facts = dict(floor_units=(0.0 - arm.location.z) / arm.scale.z, rest_fwd=list(rest_fwd), glb=GLB, action=ACT, frame=FRAME, bounds_lo=list(lo), bounds_hi=list(hi), height_m=hi.z - lo.z,
             fwd_feet=list(fwd), fwd_hips=list(fwd2), armature_location=list(arm.location), armature_scale=list(arm.scale),
             bones=len(arm.data.bones), verts=len(body.data.vertices), actions_left=len(bpy.data.actions),
             pelvis=list(head('pelvis')), head=list(head('head')), left_foot=list(head('left_foot')),
             tails_cos=[round(float(((arm.data.bones[n].tail_local - arm.data.bones[n].head_local).normalized()).dot(
                 (arm.data.bones[c].head_local - arm.data.bones[n].head_local).normalized())), 3)
                 for n, c in (('left_hip', 'left_knee'), ('left_knee', 'left_ankle'), ('left_shoulder', 'left_elbow'), ('left_elbow', 'left_wrist'), ('spine1', 'spine2'))])
json.dump(facts, open(FACTS, 'w'), indent=1)
print('BUILD_MODEL', json.dumps({k: facts[k] for k in ('floor_units', 'rest_fwd', 'height_m', 'fwd_feet', 'fwd_hips', 'bones', 'verts', 'actions_left', 'tails_cos')}))

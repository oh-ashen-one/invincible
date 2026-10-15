# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.
# Retarget Meshy preset clips (24-bone Meshy rig) onto the hero's 52-bone CustomUse/Cartwheel rig. Both rigs were built on the SAME
# v2 mesh, so rest poses nearly coincide: per frame, each mapped target bone gets the source bone's world-space rotation change from
# rest (delta * target rest); the pelvis also gets the hips translation change, scaled by the hip-height ratio. Fingers keep rest.
# usage: Blender -b --factory-startup -P tools/invincible/retarget_meshy.py -- <target_rigged.glb> <out.glb> <clips.glb> [<clips2.glb> ...]
import bpy, sys
from mathutils import Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
TGT, OUT, SRCS = argv[0], argv[1], argv[2:]
MAP = {'Hips': 'pelvis', 'Spine02': 'spine1', 'Spine01': 'spine2', 'Spine': 'spine3', 'neck': 'neck', 'Head': 'head',
       'LeftShoulder': 'left_collar', 'LeftArm': 'left_shoulder', 'LeftForeArm': 'left_elbow', 'LeftHand': 'left_wrist',
       'RightShoulder': 'right_collar', 'RightArm': 'right_shoulder', 'RightForeArm': 'right_elbow', 'RightHand': 'right_wrist',
       'LeftUpLeg': 'left_hip', 'LeftLeg': 'left_knee', 'LeftFoot': 'left_ankle', 'LeftToeBase': 'left_foot',
       'RightUpLeg': 'right_hip', 'RightLeg': 'right_knee', 'RightFoot': 'right_ankle', 'RightToeBase': 'right_foot'}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=TGT)
tgt = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE'); tgt.name = 'Hero'
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH' and o.name.lower().startswith('icosphere'): bpy.data.objects.remove(o)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
sc = bpy.context.scene; sc.render.fps = 30
done = []
for src_path in SRCS:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=src_path)
    new = [o for o in bpy.data.objects if o not in before]
    src = next(o for o in new if o.type == 'ARMATURE')
    acts = [a for a in bpy.data.actions if a.name not in done and not a.name.startswith('HERO_')]
    # rest world matrices
    def rest_w(arm, n): return arm.matrix_world @ arm.data.bones[n].matrix_local
    s_hip_h = (src.matrix_world @ src.data.bones['Hips'].head_local).z
    t_hip_h = (tgt.matrix_world @ tgt.data.bones['pelvis'].head_local).z
    k = t_hip_h / max(1e-6, s_hip_h)
    order = [b.name for b in tgt.data.bones]                          # parents before children
    inv_map = {v: k_ for k_, v in MAP.items()}
    for act in acts:
        src.animation_data_create(); src.animation_data.action = act
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        out = bpy.data.actions.new('HERO_' + act.name); tgt.animation_data_create(); tgt.animation_data.action = out
        for pb in tgt.pose.bones: pb.rotation_mode = 'QUATERNION'
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            for pb in tgt.pose.bones: pb.matrix_basis = Matrix.Identity(4)
            bpy.context.view_layer.update()
            for tn in order:
                sn = inv_map.get(tn)
                if not sn or sn not in src.pose.bones: continue
                spb, tpb = src.pose.bones[sn], tgt.pose.bones[tn]
                s_pose = src.matrix_world @ spb.matrix
                delta = s_pose.to_quaternion() @ rest_w(src, sn).to_quaternion().inverted()
                want = delta @ rest_w(tgt, tn).to_quaternion()
                tw = tgt.matrix_world @ tpb.matrix                     # current (parent-driven) world
                m = Matrix.LocRotScale(tw.to_translation(), want, tw.to_scale())
                if tn == 'pelvis':
                    d = (s_pose.to_translation() - rest_w(src, sn).to_translation()) * k
                    m = Matrix.LocRotScale(rest_w(tgt, tn).to_translation() + d, want, tw.to_scale())
                tpb.matrix = tgt.matrix_world.inverted() @ m
                bpy.context.view_layer.update()
                tpb.keyframe_insert('rotation_quaternion', frame=f)
                if tn == 'pelvis': tpb.keyframe_insert('location', frame=f)
        tr = tgt.animation_data.nla_tracks.new(); tr.name = out.name; tr.strips.new(out.name, f0, out)
        tgt.animation_data.action = None
        done.append(act.name); print('RETARGET', act.name, f1 - f0 + 1, 'frames')
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
for a in list(bpy.data.actions):
    if not a.name.startswith('HERO_'): bpy.data.actions.remove(a)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animation_mode='NLA_TRACKS', export_force_sampling=True)
print('RETARGET_OK', len(done), OUT)

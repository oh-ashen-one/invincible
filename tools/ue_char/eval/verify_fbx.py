"""Re-import exported citizen FBX files and check the shared skeleton (Blender 5.2 headless).
Fan homage, not official Marvel/Sony/Insomniac; no affiliation.

  blender -b -P tools/ue_char/eval/verify_fbx.py -- OUT_JSON FBX [FBX ...]
Reports per file: objects, bone names, rest heads (armature space, metres), actions + frame ranges, mesh height,
and whether every file's bone list/rest matches the first file (max head delta).
"""
import bpy, sys, json
args = sys.argv[sys.argv.index('--') + 1:]
out, files = args[0], args[1:]
res, ref = {}, None
for f in files:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    bpy.ops.import_scene.fbx(filepath=f, automatic_bone_orientation=False)
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    me = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    heads = {b.name: list(arm.matrix_world @ b.head_local) for b in arm.data.bones}
    zs = [(me.matrix_world @ v.co).z for v in me.data.vertices]
    r = dict(objects=[(o.name, o.type, [round(x, 4) for x in o.scale]) for o in bpy.context.scene.objects],
             bones=list(heads), root=[b.name for b in arm.data.bones if not b.parent],
             actions={a.name: [round(x, 2) for x in a.frame_range] for a in bpy.data.actions},
             mesh_height_m=round(max(zs) - min(zs), 4), fps=bpy.context.scene.render.fps,
             vertex_groups=len(me.vertex_groups), materials=[m.name for m in me.data.materials])
    if ref is None:
        ref = heads
    r['same_bones_as_first'] = list(heads) == list(ref)
    r['max_head_delta_m_vs_first'] = max(max(abs(a - b) for a, b in zip(heads[k], ref[k])) for k in heads) if r['same_bones_as_first'] else None
    res[f] = r
    print('VERIFY', f, json.dumps(r))
json.dump(res, open(out, 'w'), indent=1)

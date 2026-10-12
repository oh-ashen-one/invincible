"""Round 09: swing-foot lift of every walk take in an exported citizen FBX (Blender 5.2 headless).  Fan homage project; no affiliation.
  blender -b -P tools/ue_char/eval/fbx_lift.py -- out.json a.fbx [b.fbx ...]
Per take: the highest the ankle (foot bone head) rises above its lowest point, in metres and as a fraction of the standing height (mesh top - mesh bottom)."""
import bpy, sys, json, os
import numpy as np
args = sys.argv[sys.argv.index('--') + 1:]
out, files = args[0], args[1:]
res = {}
for f in files:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    mesh = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    z = np.array([(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]); stature = float(z.max() - z.min())
    r = {'stature_m': round(stature, 3)}
    for act in bpy.data.actions:
        name = act.name.split('|')[-1].replace('Armature_', '')
        arm.animation_data_create(); arm.animation_data.action = act
        if hasattr(arm.animation_data, 'action_slot') and len(act.slots): arm.animation_data.action_slot = act.slots[0]
        fr = act.frame_range; n = int(fr[1] - fr[0]) + 1
        zs = {'footL': [], 'footR': []}
        for k in range(n):
            bpy.context.scene.frame_set(int(fr[0]) + k); bpy.context.view_layer.update()
            for b in zs: zs[b].append((arm.matrix_world @ arm.pose.bones[b].head).z)
        lift = max(max(v) - min(min(w) for w in zs.values()) for v in zs.values())
        r[name] = {'frames': n, 'ankle_lift_m': round(float(lift), 3), 'ankle_lift_frac_stature': round(float(lift) / stature, 3)}
    res[os.path.basename(f)] = r
json.dump(res, open(out, 'w'), indent=1)
for k, v in res.items():
    print(k, {n: (d['ankle_lift_m'], d['ankle_lift_frac_stature']) for n, d in v.items() if isinstance(d, dict) and n.startswith('walk')})

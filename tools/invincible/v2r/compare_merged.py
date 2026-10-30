# Does the action survive merge_hero_clips onto the game rig? Import the original merged GLB and the test-merged one (both with the default
# bone heuristic, as the game import path does), play A_Hover on both, compare deformed world vertices on N frames (mm of the 200-unit rig / 100).
import bpy, sys, numpy as np
A, B = sys.argv[sys.argv.index('--') + 1:][:2]
def load(path):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path); new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == 'ARMATURE'); body = max((o for o in new if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
    acts = [x for x in bpy.data.actions if x.name.startswith('A_Hover')]
    act = acts[-1]
    if arm.animation_data is None: arm.animation_data_create()
    for tr in arm.animation_data.nla_tracks: tr.mute = True
    arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    return arm, body, act
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 30
a1, b1, act1 = load(A); a2, b2, act2 = load(B)
print('actions', act1.name, act1.frame_range[:], act2.name, act2.frame_range[:], 'verts', len(b1.data.vertices), len(b2.data.vertices))
def wv(o):
    deps = bpy.context.evaluated_depsgraph_get(); ev = o.evaluated_get(deps); M = np.array(ev.matrix_world)
    co = np.empty(len(ev.data.vertices) * 3); ev.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3); return co @ M[:3, :3].T + M[:3, 3]
# both actions were imported at the scene's 30 fps (121 frames over 4 s): same frame = same time
worst = []
for t in np.linspace(0, 4.0, 7):
    sc.frame_set(int(round(t * 30))); bpy.context.view_layer.update(); v1 = wv(b1)
    sc.frame_set(int(round(t * 30))); bpy.context.view_layer.update(); v2 = wv(b2)
    d = np.linalg.norm(v1 - v2, axis=1); worst.append((round(t, 2), round(float(d.max()) * 10, 2), round(float(np.median(d)) * 10, 3)))
print('COMPARE t, max_mm, median_mm (200-unit rig, 1 unit = 1 cm):', worst)

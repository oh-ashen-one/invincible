# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.
# A video2rig fit / refined .blend of the hero (project rig: the game's merged GLB imported with child-pointing bone tails,
# TEMPERANCE, armature scaled 0.01) -> one GLB on the GAME rig (rigged_hunyuanTex.glb imported the default way, exactly as
# tools/invincible/merge_hero_clips.py imports it) carrying the Action under the name the merge spec expects (`<glb>:<ACTION>=A_<Clip>`).
#
# Why the retarget: the two imports give the same bones, heads and hierarchy but different REST orientations (bone tails), so an
# action keyed on the project rig plays wrong when merge copies it by bone name (measured 2026-10-30: median 4.9 cm, max 39 cm at frame 0).
# The pose is moved in ARMATURE space (v2r_rig.retarget_basis, shared with the Hulk tools): same deformation, new basis keys.
#
#   Blender -b --factory-startup <fit.blend> -P export_hero_clip.py -- --out <file.glb> --name <ACTION NAME> [--action <src action>]
#        [--game-rig <rigged.glb>] [--fps 30] [--gate-frames 6] [--gate-mm 1.0]
# Output frames are sampled at --fps by TIME from the fit's keys (import_motion keys at the fit scene's fps, 24).
# Prints: EXPORT <name> wrote <glb> (<MB>) frames <n> seconds <s>
#         EXPORT_GATE <name> max_vertex_delta_mm <x> frames <n> PASS|FAIL   (fit mesh vs the game rig's mesh under the new keys,
#         both in the fit scene's world, mm; FAIL over --gate-mm, exit 3)
import argparse, os, sys
import bpy, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import v2r_rig as R  # noqa: E402
GAME_RIG = '/Users/midir/spider-man-2-invincible/docs/invincible/character/customuse/v2/rigged_hunyuanTex.glb'
argv = sys.argv[sys.argv.index('--') + 1:]
ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--name', required=True); ap.add_argument('--action', default='')
ap.add_argument('--game-rig', default=GAME_RIG); ap.add_argument('--fps', type=int, default=30)
ap.add_argument('--gate-frames', type=int, default=6); ap.add_argument('--gate-mm', type=float, default=1.0)
a = ap.parse_args(argv)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
body = next(o for o in sc.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers))
act = bpy.data.actions.get(a.action) if a.action else (arm.animation_data.action if arm.animation_data else None)
if act is None:
    # refine scripts may leave the action on an NLA track
    if arm.animation_data and arm.animation_data.nla_tracks:
        act = arm.animation_data.nla_tracks[-1].strips[0].action
if act is None: raise SystemExit('no action (have %s)' % [x.name for x in bpy.data.actions])
if arm.animation_data is None: arm.animation_data_create()
for tr in arm.animation_data.nla_tracks: tr.mute = True
R.assign_action(arm, act)
src_fps = sc.render.fps
k0, k1 = R.key_range(act)
seconds = (k1 - k0) / src_fps
n_out = int(round(seconds * a.fps)) + 1
src_frames = [k0 + i * src_fps / a.fps for i in range(n_out)]        # fit-scene frames sampled at the output rate
# ---- sample the fit's armature-space poses
P_src = []
for f in src_frames:
    R.set_frame(f); bpy.context.view_layer.update(); P_src.append(R.sample_pose(arm))
R_src, PAR_src = R.rest(arm), R.parents(arm)
# ---- the game rig
new = R.import_glb(a.game_rig)
garm = next(o for o in new if o.type == 'ARMATURE'); gbody = max((o for o in new if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
for o in new:
    if o.type == 'MESH' and o is not gbody: bpy.data.objects.remove(o, do_unlink=True)
for x in [x for x in bpy.data.actions if x is not act and x.users == 0]: bpy.data.actions.remove(x)
ok, lines = R.check_match(arm, garm, tol=1e-3)
for l in lines: print('RIG', l)
if not ok: print('EXPORT_GATE %s max_vertex_delta_mm nan frames 0 FAIL (rig mismatch)' % a.name); sys.exit(3)
R_dst, PAR_dst = R.rest(garm), R.parents(garm)
bases = [R.retarget_basis(P, R_src, R_dst, PAR_dst) for P in P_src]
out_frames = list(range(n_out))
gact = bpy.data.actions.new(a.name); gact.use_fake_user = True
sc.render.fps = a.fps
loc_bones = R.write_basis_frames(garm, gact, out_frames, bases, loc_bones=[next(n for n, p in PAR_dst.items() if p is None)])   # location keys on the root only
garm.matrix_world = arm.matrix_world.copy()
# ---- gate: fit rig vs the game rig under the new keys, same world: every bone's head and tail (mm), plus the deformed meshes when
# the two meshes have the same vertex count (the game GLB and the merged GLB differ by one stray vertex)
R.assign_action(garm, gact)
def joints(ar):
    M = ar.matrix_world; return np.array([list(M @ ar.pose.bones[n].head) for n in NAMES])   # heads only, by NAME: the two rigs' tails and bone order differ
NAMES = sorted(PAR_dst)
same_mesh = len(body.data.vertices) == len(gbody.data.vertices)
worst = 0.0; worst_v = 0.0
for i in np.linspace(0, n_out - 1, a.gate_frames).round().astype(int):
    sc.render.fps = src_fps; R.set_frame(src_frames[i]); bpy.context.view_layer.update(); j1 = joints(arm); v1 = R.mesh_world(body) if same_mesh else None
    sc.render.fps = a.fps; sc.frame_set(int(i)); bpy.context.view_layer.update(); j2 = joints(garm); v2 = R.mesh_world(gbody) if same_mesh else None
    dj = np.sqrt(((j1 - j2) ** 2).sum(1)) * 1000.0
    if dj.max() > worst:
        names = NAMES; top = np.argsort(dj)[::-1][:4]
        print('GATE_WORST frame %d: %s' % (i, ', '.join('%s %.1f mm' % (names[k], dj[k]) for k in top)))
    worst = max(worst, float(dj.max()))
    if same_mesh: worst_v = max(worst_v, float(np.linalg.norm(v1 - v2, axis=1).max()) * 1000.0)
print('EXPORT_GATE_DETAIL %s max_joint_delta_mm %.4f max_vertex_delta_mm %s' % (a.name, worst, ('%.4f' % worst_v) if same_mesh else 'n/a (vertex counts differ)'))
worst = max(worst, worst_v)
# the game rig is exported where the fit lives (object transform is not part of the clip; merge copies the action only)
garm.matrix_world = arm.matrix_world.copy()
# ---- export: NLA track named like the action (merge_hero_clips reads the animation by that name)
garm.animation_data.action = None
for tr in list(garm.animation_data.nla_tracks): garm.animation_data.nla_tracks.remove(tr)
tr = garm.animation_data.nla_tracks.new(); tr.name = a.name; tr.strips.new(a.name, 0, gact); tr.mute = False
sc.frame_start, sc.frame_end = 0, n_out - 1
for o in list(sc.objects): o.select_set(False)
garm.select_set(True); gbody.select_set(True); bpy.context.view_layer.objects.active = garm
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=a.out, export_format='GLB', use_selection=True, export_animation_mode='NLA_TRACKS', export_force_sampling=True,
                          export_frame_range=True, export_skins=True, export_morph=False, export_apply=False, export_yup=True)
print('EXPORT %s wrote %s (%.1f MB) frames %d seconds %.3f' % (a.name, a.out, os.path.getsize(a.out) / 1e6, n_out, seconds))
ok = worst <= a.gate_mm
print('EXPORT_GATE %s max_vertex_delta_mm %.4f frames %d %s' % (a.name, worst, a.gate_frames, 'PASS' if ok else 'FAIL'))
sys.exit(0 if ok else 3)

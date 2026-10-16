# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.
# Game-ready boost clips from the owner-confirmed boost v3 + flight loop:
#   HERO_boost_game : boost v3 time-warped so the burst (arms snapping forward out of the coil) lands at 0.42 s = the flight code's
#                     charge hang + sonic boom; after the burst the take plays at normal speed
#   HERO_boost_hold : super-speed hold while Shift is held = the approved flight loop sampled 1.6x faster (2.5 s seamless) with the
#                     arms locked in the boost's parallel fists-forward line (untwisted swings) and verified fists
# usage: Blender -b --factory-startup -P boost_game_clips.py -- <hero_boost_v3.glb> <hero_fly_keyed.glb> <out.glb>
import bpy, sys, math
from mathutils import Vector, Matrix, Quaternion
BOOST, FLY, OUT = sys.argv[sys.argv.index('--') + 1:][:3]
sys.argv = [sys.argv[0], '--', FLY, '/dev/null', 'X']          # reuse post_take helpers without running its main section
src = open(__file__.replace('boost_game_clips.py', 'post_take.py')).read()
helpers = src[:src.index('# sample the take')]
helpers = helpers.replace("A = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])", "A = ap.parse_args(['x', 'x', 'x', 'x'])")
helpers = helpers.replace("bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=A.src)",
                          "bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=r'%s')" % BOOST)
exec(helpers)
def sample(action, frames):
    arm.animation_data_create(); arm.animation_data.action = action; out = []
    for f in frames:
        sc.frame_set(int(f)); a0 = {p.name: p.matrix_basis.copy() for p in pb}
        if f != int(f):                                   # sub-frame: blend to the next frame
            sc.frame_set(int(f) + 1); a1 = {p.name: p.matrix_basis.copy() for p in pb}; k = f - int(f)
            a0 = {n: Matrix.LocRotScale(a0[n].to_translation().lerp(a1[n].to_translation(), k), a0[n].to_quaternion().slerp(a1[n].to_quaternion(), k), Vector((1, 1, 1))) for n in a0}
        out.append(a0)
    arm.animation_data.action = None; return out
boost = bpy.data.actions['HERO_boost_v3']; nb = int(boost.frame_range[1])
# find the burst: arms come from behind (coil) to pointing forward along the flight line
arm.animation_data_create(); arm.animation_data.action = boost; fwd_by_f = []
for f in range(0, nb + 1):
    sc.frame_set(f); fwd_by_f.append(((limb('left_shoulder') + limb('right_shoulder')) / 2).dot(FWD))   # UPPER arm: back in the coil, forward after the burst
coil_f = min(range(len(fwd_by_f)), key=lambda i: fwd_by_f[i])
burst_f = next(i for i in range(coil_f, len(fwd_by_f)) if fwd_by_f[i] > 0.85)
print('BOOST coil frame', coil_f, 'burst frame', burst_f)
B_AT = 13                                                   # 0.42 s at 30 fps
warp = [burst_f * (j / B_AT) for j in range(B_AT)] + list(range(burst_f, nb + 1))
game = sample(boost, warp)
# hold: the fly loop at 1.6x (120 frames -> 75), arms overridden to the parallel boost line
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=FLY)
new = [o for o in bpy.data.objects if o not in before]; arm2 = next(o for o in new if o.type == 'ARMATURE'); fly_act = arm2.animation_data.action or bpy.data.actions['HERO_fly_keyed']
arm2.animation_data_create(); arm2.animation_data.action = bpy.data.actions['HERO_fly_keyed']
hold = []
for j in range(75):
    f = j * 1.6; sc.frame_set(int(f)); a0 = {p.name: p.matrix_basis.copy() for p in arm2.pose.bones}
    sc.frame_set(int(f) + 1); a1 = {p.name: p.matrix_basis.copy() for p in arm2.pose.bones}; k = f - int(f)
    hold.append({n: Matrix.LocRotScale(a0[n].to_translation().lerp(a1[n].to_translation(), k), a0[n].to_quaternion().slerp(a1[n].to_quaternion(), k), Vector((1, 1, 1))) for n in a0})
for o in new: bpy.data.objects.remove(o, do_unlink=True)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)

def write(name, frames, arms_line=False):
    act = bpy.data.actions.new(name); arm.animation_data_create(); arm.animation_data.action = act
    for p in pb: p.rotation_mode = 'QUATERNION'
    for i, basis in enumerate(frames):
        for p in pb: p.matrix_basis = basis[p.name]
        bpy.context.view_layer.update()
        if arms_line:                                       # arms = the owner-confirmed boost stretch (last game frame), riding on the fly loop's chest
            for n in ARM_CHAIN + HAND: pb[n].matrix_basis = game[-1][n]
            bpy.context.view_layer.update()
        for p in pb:
            p.keyframe_insert('rotation_quaternion', frame=i)
            if p.name == 'pelvis': p.keyframe_insert('location', frame=i)
    tr = arm.animation_data.nla_tracks.new(); tr.name = name; tr.strips.new(name, 0, act); arm.animation_data.action = None
    print('CLIP', name, len(frames))
for tr in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(tr)
write('HERO_boost_game', game)
write('HERO_boost_hold', hold, arms_line=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animation_mode='NLA_TRACKS', export_force_sampling=True)
print('BOOSTGAME_OK', OUT)

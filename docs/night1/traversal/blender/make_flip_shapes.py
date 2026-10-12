# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 11 (owner brief FLIPS_BRIEF.md): gymnast shape clips keyed on the hero rig in Blender (headless).
#   blender -b -P make_flip_shapes.py -- <hero.glb> <out.glb> [<report.json>]
# Imports the hero GLB (public/assets/spiderman.glb, 58 bones), keys one action per held gymnastic shape (tuck, pike, layout,
# swan, pencil, straddle, throne, twist, reach) by aiming every limb / spine bone at a direction given in the BODY frame
# (F forward, U up, O outward for the bone's side), parent first, and exports ONLY these actions (+ the untouched 'airApex'
# action as a round-trip check) to <out.glb>. build_traversal.py splices the flip actions into Saved/HeroDev.glb
# (rotation channels only, matched by node name) after checking that 'airApex' survived the Blender round trip unchanged.
# Each clip is 1 s: key 0 = the shape, key 1 s = the same shape "breathing" (limbs 6-8 % further out) so a held shape is never
# frozen. Clip names: flipTuck, flipPike, flipLayout, flipSwan, flipPencil, flipStraddle, flipThrone, flipTwist, flipReach.
import bpy
import json
import sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = argv[0] if len(argv) > 0 else "public/assets/spiderman.glb"
OUT = argv[1] if len(argv) > 1 else "HeroFlips.glb"
REPORT = argv[2] if len(argv) > 2 else None

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30  # BEFORE the import: the importer maps glTF seconds to frames at the scene fps
bpy.ops.import_scene.gltf(filepath=SRC)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
bpy.context.view_layer.objects.active = arm
scene = bpy.context.scene

# body frame of the imported rig (glTF +Z forward -> Blender -Y; the rig's .L side is +X)
F = Vector((0.0, -1.0, 0.0))
U = Vector((0.0, 0.0, 1.0))


def d(f, u, o, side):
    """Direction from body-frame components: f forward, u up, o outward (toward the bone's own side)."""
    s = 1.0 if side == "L" else -1.0
    v = F * f + U * u + Vector((s * o, 0.0, 0.0))
    return v.normalized()


CHAIN = ["hips", "spine", "spine1", "spine2", "neck", "head",
         "shoulder.L", "upperArm.L", "forearm.L", "hand.L", "shoulder.R", "upperArm.R", "forearm.R", "hand.R",
         "thigh.L", "shin.L", "foot.L", "toe.L", "thigh.R", "shin.R", "foot.R", "toe.R"]

# ---- shapes: bone -> (f, u, o). Side-less entries apply to both sides (o mirrored). None = keep the rest direction.
#   arms: upperArm / forearm; hand follows the forearm; legs: thigh / shin / foot (pointed toes follow the shin) / toe
POINT = "point"  # foot / toe along the shin (pointed toes)


def legs(thigh, shin, foot=POINT):
    return {"thigh": thigh, "shin": shin, "foot": foot, "toe": POINT}


SHAPES = {
    # tight tuck: knees to the chest, hands on the shins, back rounded, chin down
    # round 17 (critic r16 "limbs symmetric"): asymmetric grab -- left hand low on the shin, right hand high on the knee; knees unevenly apart
    "flipTuck": dict(spine=(0.35, 1, 0), spine1=(0.6, 1, 0), spine2=(0.8, 1, 0), neck=(1.0, 0.9, 0), head=(1.0, 0.55, 0),
                     upperArm_L=(1.0, -0.45, 0.32), forearm_L=(0.2, -1.0, 0.04), upperArm_R=(1.0, -0.15, 0.5), forearm_R=(0.55, -0.85, -0.05),
                     hand="follow", foot=POINT, toe=POINT,
                     thigh_L=(1.0, 0.95, 0.08), shin_L=(-0.4, -1.0, 0.04), thigh_R=(1.0, 0.8, 0.2), shin_R=(-0.2, -1.0, 0.08)),
    # pike: legs straight and together, folded forward at the hips, hands reaching to the ankles
    # round 17 (critic r16 "the pike is a lump from 3/4 behind"): left hand reaches the ankles, right arm sweeps wide and back
    "flipPike": dict(spine=(0.3, 1, 0), spine1=(0.6, 1, 0), spine2=(0.95, 1, 0), neck=(1.0, 0.7, 0), head=(1.0, 0.4, 0),
                     upperArm_L=(1.0, 0.1, 0.12), forearm_L=(1.0, 0.35, 0.05), upperArm_R=(0.15, 0.35, 1.0), forearm_R=(-0.25, 0.45, 1.0),
                     hand="follow", **legs((1.0, 0.55, 0.03), (1.0, 0.6, 0.02))),
    # layout: one straight line, slight hollow, arms along the sides a hand-width out
    "flipLayout": dict(spine=(0.04, 1, 0), spine1=(0.02, 1, 0), spine2=(0.0, 1, 0), neck=(0.02, 1, 0), head=(0.05, 1, 0),
                       upperArm=(0.05, -1.0, 0.33), forearm=(0.05, -1.0, 0.22), hand="follow",
                       **legs((0.03, -1.0, 0.03), (0.0, -1.0, 0.02))),
    # swan: arched back, chest proud, arms spread wide and a little back, legs together extended behind
    # round 17 (critic r16 "swan arms even"): left arm high and forward, right arm low and back; right knee bent, foot trailing (stag line)
    "flipSwan": dict(spine=(-0.18, 1, 0), spine1=(-0.32, 1, 0), spine2=(-0.4, 1, 0), neck=(-0.25, 1, 0), head=(-0.15, 1, 0),
                     upperArm_L=(0.05, 0.6, 1.0), forearm_L=(0.2, 0.85, 0.75), upperArm_R=(-0.55, -0.15, 1.0), forearm_R=(-0.7, -0.05, 0.8),
                     hand="follow", foot=POINT, toe=POINT,
                     thigh_L=(-0.3, -1.0, 0.03), shin_L=(-0.42, -1.0, 0.02), thigh_R=(-0.05, -1.0, 0.1), shin_R=(-0.85, -0.6, 0.05)),
    # pencil: straight, legs glued together, arms out low on the diagonal (the reference's inverted pencil)
    "flipPencil": dict(spine=(0.0, 1, 0), spine1=(0.0, 1, 0), spine2=(0.0, 1, 0), neck=(0.0, 1, 0), head=(0.03, 1, 0),
                       upperArm=(0.12, -0.5, 1.0), forearm=(0.12, -0.35, 1.0), hand="follow",
                       **legs((0.0, -1.0, 0.012), (0.0, -1.0, 0.0))),
    # straddle: straight legs split wide to the sides, arms spread level
    "flipStraddle": dict(spine=(0.12, 1, 0), spine1=(0.12, 1, 0), spine2=(0.1, 1, 0), neck=(0.1, 1, 0), head=(0.12, 1, 0),
                         upperArm=(0.15, 0.08, 1.0), forearm=(0.15, 0.18, 1.0), hand="follow",
                         **legs((0.3, -0.62, 1.0), (0.3, -0.6, 1.0))),
    # throne: upright "seated" spread (reference 23.0-23.4 s): knees up and apart, shins hanging, arms in a wide V
    "flipThrone": dict(spine=(-0.08, 1, 0), spine1=(-0.1, 1, 0), spine2=(-0.1, 1, 0), neck=(-0.05, 1, 0), head=(0.0, 1, 0),
                       upperArm=(0.05, 0.75, 1.0), forearm=(0.02, 1.0, 0.65), hand="follow",
                       **legs((1.0, 0.12, 0.45), (0.12, -1.0, 0.12))),
    # twist (corkscrew): legs straight and crossed tight, arms folded across the chest (small inertia about the long axis)
    "flipTwist": dict(spine=(0.02, 1, 0), spine1=(0.02, 1, 0), spine2=(0.02, 1, 0), neck=(0.02, 1, 0), head=(0.06, 1, 0),
                      upperArm=(0.75, -0.55, -0.1), forearm=(0.25, 0.3, -1.0), hand="follow",
                      **legs((0.0, -1.0, -0.03), (0.0, -1.0, -0.05))),
    # reach (catch prep): web arm (right) reaching up and forward, left arm out, knees lightly bent
    "flipReach": dict(spine=(0.05, 1, 0), spine1=(0.02, 1, 0), spine2=(0.0, 1, 0), neck=(0.0, 1, 0), head=(0.1, 1, 0),
                      upperArm_R=(0.45, 1.0, 0.25), forearm_R=(0.45, 1.0, 0.18), upperArm_L=(0.25, 0.05, 1.0), forearm_L=(0.35, 0.15, 1.0),
                      hand="follow", **legs((0.55, -0.85, 0.1), (-0.25, -1.0, 0.05))),
}
# breathing key: how much further out the limbs go at 1 s (blend toward a slightly more open copy)
BREATH = 0.07

# round 13 (critic r12: "Layout is a rigid, identical plank"; "backDouble uses 5 shapes"): KEYED shapes -- a list of (u, shape) keys
# (u = 0..1 of the 1 s clip, which the anim instance plays over the shape's hold) instead of one held pose + breathing.
# round 18 (critic r17 single gap: "every trick holds a frozen inverted split"; test: in every trick window one limb_z component moves
# >= 0.10 per 0.1 s sample): the keys are interpolated HERE, per bone (normalised lerp of the aim directions, linear in u) and keyed on
# EVERY frame, so the motion runs at a steady speed between keys (r13-r17 keyed 4-5 frames and let Blender's auto-Bezier ease every key
# to a standstill: the limbs stopped at each key). Each key moves at least one hand or foot >= ~0.25 m (body frame) from the previous one,
# and the limbs are staggered so no two keys are reached by every limb at once.
def _lay(ua, fa, th_l, sh_l, th_r, sh_r, sp=(0.04, 0.02, 0.0)):
    d = dict(spine=(sp[0], 1, 0), spine1=(sp[1], 1, 0), spine2=(sp[2], 1, 0), neck=(0.02, 1, 0), head=(0.05, 1, 0),
             upperArm=ua, forearm=fa, hand="follow", foot=POINT, toe=POINT)
    d["thigh_L"], d["shin_L"], d["thigh_R"], d["shin_R"] = th_l, sh_l, th_r, sh_r
    return d


def _pose(sp, arm_l, arm_r, leg_l, leg_r, neck=(0.02, 1, 0), head=(0.05, 1, 0)):
    """Full body key: sp = (spine, spine1, spine2) forward leans; arm_* = (upperArm, forearm); leg_* = (thigh, shin)."""
    return dict(spine=(sp[0], 1, 0), spine1=(sp[1], 1, 0), spine2=(sp[2], 1, 0), neck=neck, head=head,
                upperArm_L=arm_l[0], forearm_L=arm_l[1], upperArm_R=arm_r[0], forearm_R=arm_r[1], hand="follow",
                thigh_L=leg_l[0], shin_L=leg_l[1], thigh_R=leg_r[0], shin_R=leg_r[1], foot=POINT, toe=POINT)


# the tuck grab (start of the kick-out, = flipTuck) and the catch reach (end of the kick-out, = flipReach) as keys
_TUCK = _pose((0.35, 0.6, 0.8), ((1.0, -0.45, 0.32), (0.2, -1.0, 0.04)), ((1.0, -0.15, 0.5), (0.55, -0.85, -0.05)),
              ((1.0, 0.95, 0.08), (-0.4, -1.0, 0.04)), ((1.0, 0.8, 0.2), (-0.2, -1.0, 0.08)), neck=(1.0, 0.9, 0), head=(1.0, 0.55, 0))
# r01 resume: marching leg phases (thigh, shin) -- A low and straight, B knee half up, C knee up (thigh ~horizontal), D lowering forward
_LEG_A = ((0.05, -1.0, 0.08), (-0.05, -1.0, 0.04))
_LEG_B = ((0.75, -0.65, 0.09), (-0.2, -1.0, 0.04))
_LEG_C = ((1.0, -0.2, 0.1), (0.0, -1.0, 0.05))
_LEG_D = ((0.75, -0.65, 0.09), (0.35, -1.0, 0.04))
# (foot height below the hips ~ A .90, B .73, C .53, D .71 m: even steps, so a quarter cycle always moves a foot ~0.17-0.2 m)


_REACH = _pose((0.05, 0.02, 0.0), ((0.25, 0.05, 1.0), (0.35, 0.15, 1.0)), ((0.45, 1.0, 0.25), (0.45, 1.0, 0.18)),
               _LEG_A, _LEG_B, head=(0.1, 1, 0))   # r01 resume: legs = the reach's first march phase (was a static lunge)

def _tuck(th, sh, sp=(0.35, 0.6, 0.8)):
    """Tricks C r01: tuck key with the thighs / shins pulled in by th / sh (the r17 asymmetric grab otherwise)"""
    t = dict(SHAPES["flipTuck"])
    t.update(spine=(sp[0], 1, 0), spine1=(sp[1], 1, 0), spine2=(sp[2], 1, 0),
             thigh_L=(1.0, 0.95 + th, 0.08), shin_L=(-0.4 - sh, -1.0, 0.04), thigh_R=(1.0, 0.8 + th, 0.2), shin_R=(-0.2 - sh, -1.0, 0.08))
    return t


KEYED = {
    # Tricks C r01 (critic pose.py rule: 2 slow limb samples in r23's held 1.2 s double tuck): the tuck SQUEEZES instead of holding -- the
    # knees come up into it, pull hard to the chest at ~40 % (the spin's fastest part), then ease off toward the kick-out; the anim
    # instance's tuck IK keeps the wrists on the shins and the knees together throughout (tight tuck numbers unchanged)
    "flipTuck": [
        (0.0, _tuck(-0.3, -0.25, (0.25, 0.45, 0.65))),
        (0.4, _tuck(0.2, 0.2, (0.42, 0.7, 0.9))),
        (0.72, _tuck(-0.05, 0.0)),
        (1.0, _tuck(-0.5, -0.5, (0.25, 0.45, 0.62))),
    ],
    # Tricks C r01 reach (catch prep; critic pose.py rule: the r23 reach was a held pose -> slow limb samples when the body turns slowly):
    # the web arm (right) is already up out of the kick-out; the head SPOTS (chin down, eyes on the next anchor's swing line), then the
    # legs scissor through (left knee up, right leg long, then swapped) while the web arm climbs higher and forward, the free arm sweeps
    # down and out, and the head lifts to the web
    # r01 resume (L: 0.1 s samples of slowly turning reaches moved < .10 m): a bigger scissor -- out of the kick-out the left knee DRIVES up
    # while the right leg sweeps long behind and the free (left) arm swings down past the hip; then the legs swap (right knee up, left leg
    # long) and the free arm swings forward and up. Every half moves a hand and a foot >= ~0.35 m in BOTH body forward and up, so some
    # limb height changes whatever the body's pitch. (Past the program's end WebFlips::Sample plays the reach back and forth from u .45.)
    "flipReach": [
        # r01 resume (L, critic pose.py rule: synchronous keys put every limb's turnaround at the same instant -> 0.03-0.09 m samples): the
        # legs MARCH -- alternating knee drives, the two legs a quarter cycle apart (one foot is always mid-stroke) -- and the free (left) arm
        # counter-swings; the web arm stays up; the head spots, then lifts to the web. Leg phases: A low, B knee half up, C knee up, D lowering.
        (0.0, dict(_pose((0.05, 0.02, 0.0), ((0.25, 0.05, 1.0), (0.35, 0.15, 1.0)), ((0.45, 1.0, 0.25), (0.45, 1.0, 0.18)), _LEG_A, _LEG_B), neck=(0.35, 1, 0), head=(0.7, 0.72, 0))),
        (0.25, _pose((0.07, 0.04, 0.01), ((0.05, -0.6, 0.8), (0.15, -0.6, 0.7)), ((0.5, 1.0, 0.28), (0.5, 1.0, 0.2)), _LEG_B, _LEG_C, neck=(0.2, 1, 0), head=(0.42, 0.9, 0))),
        (0.5, _pose((0.08, 0.05, 0.02), ((-0.15, -1.0, 0.4), (0.05, -1.0, 0.3)), ((0.55, 1.0, 0.25), (0.55, 1.0, 0.18)), _LEG_C, _LEG_D, neck=(0.1, 1, 0), head=(0.22, 1, 0))),
        (0.75, _pose((0.05, 0.02, -0.01), ((0.45, -0.3, 0.8), (0.55, -0.15, 0.7)), ((0.6, 1.0, 0.22), (0.6, 1.0, 0.15)), _LEG_D, _LEG_A, neck=(0.02, 1, 0), head=(0.0, 1, 0))),
        (1.0, _pose((0.02, -0.02, -0.04), ((0.7, 0.45, 0.6), (0.8, 0.5, 0.45)), ((0.6, 1.0, 0.2), (0.7, 1.0, 0.12)), _LEG_A, _LEG_B, neck=(-0.05, 1, 0), head=(-0.22, 1, 0))),
    ],
    # Tricks C r01 pencil (backSingle's inverted hold): straight and glued legs throughout, the arms travel from low diagonals through
    # level to a high V (the body stays a line; the arms keep the hold alive)
    "flipPencil": [
        # r01 resume (L: the low-diagonal start left 0.06 m per 0.1 s): the arms start by the thighs and sweep out through level to the V
        (0.0, dict(SHAPES["flipPencil"], upperArm=(0.12, -0.95, 0.4), forearm=(0.15, -1.0, 0.25))),
        # r01 resume (L: the arms' turn into the next tuck met still legs -> 0.03-0.06 m samples): the glued legs fold from the hips and
        # knees through the hold (the tuck-up), so the feet travel while the arms turn back
        (0.5, dict(SHAPES["flipPencil"], upperArm=(0.1, 0.12, 1.0), forearm=(0.1, 0.25, 1.0), thigh=(0.4, -0.92, 0.012), shin=(-0.2, -1.0, 0.0))),
        (1.0, dict(SHAPES["flipPencil"], upperArm=(0.1, 0.9, 0.55), forearm=(0.05, 1.0, 0.42),
                   thigh=(0.9, -0.45, 0.012), shin=(-0.5, -0.85, 0.0))),
    ],
    # r01 resume twist (L: a held chest wrap turning about the long axis moved no limb height -- fullTwist 0.07 m per 0.1 s): the legs stay
    # straight and crossed; out of the chest wrap the LEFT arm drives straight up over the head (one arm in, one arm up: a real twisting
    # entry), then the right arm follows it up so the twist ends long, both arms overhead, ready to fling out into the straddle / layout
    "flipTwist": [
        (0.0, dict(SHAPES["flipTwist"])),
        (0.45, dict(SHAPES["flipTwist"], upperArm_L=(0.05, 1.0, 0.12), forearm_L=(0.02, 1.0, 0.05))),
        (1.0, dict(SHAPES["flipTwist"], upperArm_L=(0.05, 1.0, 0.12), forearm_L=(0.02, 1.0, 0.05), upperArm_R=(0.05, 1.0, 0.1), forearm_R=(0.02, 1.0, 0.04))),
    ],
    # round 18 pike: it STARTS at the release (frontPikeSwan) with the arms raised and the body long, and folds through the hold -- the arms
    # reach forward and down while the straight legs lift -- into the r17 pike (left hand at the ankles, right arm swept wide and back)
    "flipPike": [
        (0.0, _pose((0.0, 0.0, 0.0), ((0.3, 1.0, 0.25), (0.25, 1.0, 0.18)), ((0.4, 1.0, 0.15), (0.35, 1.0, 0.1)),
                    ((0.1, -1.0, 0.03), (0.05, -1.0, 0.02)), ((0.05, -1.0, 0.03), (0.0, -1.0, 0.02)))),
        (0.45, _pose((0.15, 0.3, 0.5), ((1.0, 0.3, 0.15), (1.0, 0.1, 0.08)), ((0.6, 0.6, 0.6), (0.3, 0.5, 0.8)),
                     ((1.0, -0.4, 0.03), (1.0, -0.3, 0.02)), ((0.8, -0.6, 0.03), (0.9, -0.5, 0.02)), neck=(0.6, 1, 0), head=(0.6, 0.8, 0))),
        (1.0, SHAPES["flipPike"]),
    ],
    # layout: the straight line breathes with overlapping limbs -- the arms float out and forward, the legs part a little behind them
    "flipLayout": [
        # round 18: it opens from the release with the arms still raised (the swing's web arm) and sweeps them down to the sides through
        # the first ~40 % of the hold, then the r17 breathing (left arm higher / further forward, legs part), then the arms gather in across
        # the chest (into the corkscrew's twist wrap)
        (0.0, dict(_lay((0.25, 0.9, 0.4), (0.2, 1.0, 0.3), (0.03, -1.0, 0.03), (0.0, -1.0, 0.02), (0.03, -1.0, 0.03), (0.0, -1.0, 0.02)),
                   upperArm_R=(0.35, 1.0, 0.2), forearm_R=(0.3, 1.0, 0.15))),
        (0.4, _lay((0.05, -1.0, 0.33), (0.05, -1.0, 0.22), (0.03, -1.0, 0.03), (0.0, -1.0, 0.02), (0.03, -1.0, 0.03), (0.0, -1.0, 0.02))),
        # Tricks C r01 (gymnast layout: hips / knees >= 170 deg): the scissor is halved and the hollow eased (r18: thighs +0.2 / -0.15,
        # shins +0.08 / -0.25, spine -0.02 / -0.06 / -0.08 -> hip angle ~165 deg)
        (0.62, dict(_lay((0.35, -0.6, 0.6), (0.4, -0.45, 0.5), (0.1, -1.0, 0.04), (0.06, -1.0, 0.02), (-0.07, -1.0, 0.04), (-0.1, -1.0, 0.02),
                         sp=(-0.01, -0.03, -0.04)), upperArm_L=(0.5, -0.25, 0.65), forearm_L=(0.6, -0.05, 0.55),
                    upperArm_R=(0.1, -0.9, 0.5), forearm_R=(0.12, -0.85, 0.4))),
        (1.0, dict(_lay((0.5, -0.6, 0.1), (0.4, 0.2, -0.6), (0.08, -1.0, 0.0), (0.03, -1.0, -0.02), (-0.05, -1.0, 0.0), (-0.1, -1.0, -0.02),
                        sp=(0.02, 0.0, -0.03)))),
    ],
    # round 18 kick-out (backDouble's open finish; critic r17 "kickouts freeze", "make the kickout a moving extension, not a held pose"):
    # out of the tuck grab the legs SHOOT out (left forward, right back: a scissor), the left arm swings up overhead while the right opens
    # wide, the body arches, then the web arm (right) swings up for the catch while the left sweeps down and out, the right knee folds and
    # the scissor swaps -- it ends in the catch reach. No two keys hold every limb.
    "flipKickout": [
        (0.0, _TUCK),
        # Tricks C r01: the head SPOTS the catch -- out of the tuck's chin-down it stays forward-down (eyes on where he is going) while the
        # legs shoot out, then lifts through the open-out to the neutral reach (r18: neutral at 0.22, thrown back at 0.42)
        (0.22, _pose((0.12, 0.16, 0.2), ((0.9, 0.5, 0.3), (0.7, 0.8, 0.25)), ((0.5, -0.3, 1.0), (0.3, -0.2, 1.0)),
                     _LEG_A, _LEG_B, neck=(0.3, 1, 0), head=(0.6, 0.8, 0))),
        (0.42, _pose((-0.1, -0.2, -0.25), ((0.25, 1.0, 0.35), (0.1, 1.0, 0.3)), ((-0.1, 0.2, 1.0), (-0.2, 0.35, 1.0)),
                     _LEG_B, _LEG_C, neck=(0.12, 1, 0), head=(0.42, 0.95, 0))),
        (0.62, _pose((-0.05, -0.1, -0.12), ((0.1, -0.1, 1.0), (0.15, 0.05, 1.0)), ((0.45, 1.0, 0.25), (0.45, 1.0, 0.18)),
                     _LEG_C, _LEG_D, head=(0.28, 1, 0))),
        # r01 resume (L): out of the tuck the legs shoot down into a MARCH, a quarter cycle per key (A / B, B / C, C / D, D / A, then the
        # reach's A / B), so one foot is always mid-stroke while the arms sweep and turn
        (0.82, _pose((0.05, 0.03, 0.0), ((0.2, -0.65, 0.8), (0.35, -0.45, 0.8)), ((0.5, 1.0, 0.3), (0.5, 1.0, 0.2)),
                     _LEG_D, _LEG_A, head=(0.1, 1, 0))),
        (1.0, _REACH),
    ],
    # round 18 swan (frontPikeSwan's inverted shape; critic r17: "replace the frozen inverted split with a continuous unwind -- arms sweep from
    # overhead to the sides, one knee bends, the body extends toward the catch"): out of the pike both arms reach overhead and the legs extend;
    # the LEFT arm sweeps out to the side first, the right follows 0.15 later while the back arches and the right knee folds (stag); then the
    # knee re-extends, the arms sweep on down past the hips and forward and the hips flex -- the body gathers into the tuck that follows.
    "flipSwan": [
        # r01 resume (L: near inverted the r18 sweeps ran along constant height -> 0.02-0.07 m samples): the right arm windmills (forward,
        # down and back, forward and up) while the left sweeps as before, so a hand height changes in every 0.1 s of the hold
        (0.0, _pose((0.0, -0.05, -0.08), ((0.3, 1.0, 0.2), (0.25, 1.0, 0.12)), ((0.35, 1.0, 0.25), (0.3, 1.0, 0.18)),
                    ((0.05, -1.0, 0.03), (0.0, -1.0, 0.02)), ((0.05, -1.0, 0.03), (0.0, -1.0, 0.02)))),
        (0.3, _pose((-0.15, -0.28, -0.35), ((0.0, 0.25, 1.0), (-0.05, 0.3, 1.0)), ((0.55, -0.2, 0.8), (0.6, -0.1, 0.7)),
                    ((-0.2, -1.0, 0.04), (-0.25, -1.0, 0.02)), ((0.0, -1.0, 0.06), (-0.5, -1.0, 0.03)), head=(-0.15, 1, 0))),
        (0.55, _pose((-0.2, -0.35, -0.42), ((-0.35, -0.3, 1.0), (-0.4, -0.2, 0.9)), ((-0.3, -0.7, 0.6), (-0.35, -0.6, 0.5)),
                     ((-0.25, -1.0, 0.04), (-0.35, -1.0, 0.02)), ((0.05, -1.0, 0.08), (-0.95, -0.35, 0.04)), head=(-0.2, 1, 0))),
        (0.8, _pose((-0.05, -0.08, -0.1), ((0.4, -0.6, 0.7), (0.55, -0.4, 0.6)), ((0.5, 0.3, 0.7), (0.5, 0.4, 0.6)),
                    ((-0.1, -1.0, 0.04), (-0.9, -0.45, 0.02)), ((0.1, -1.0, 0.06), (-0.4, -1.0, 0.03)))),   # r01 resume: left stag follows the right (L)
        (1.0, _pose((0.15, 0.3, 0.4), ((0.85, -0.5, 0.3), (0.6, -0.7, 0.2)), ((0.8, -0.35, 0.45), (0.5, -0.75, 0.15)),
                    ((0.55, -0.8, 0.05), (-0.2, -1.0, 0.03)), ((0.45, -0.9, 0.1), (-0.35, -1.0, 0.05)), neck=(0.5, 1, 0), head=(0.5, 0.9, 0))),
    ],
    # round 18 straddle (corkscrew's OWN inverted shape, distinct from the swan; critic r17 "f2, f3 and f4 share one inverted split"): out of
    # the twist's chest wrap the arms fling out level and the straight legs split WIDE to the sides (an X, body straight, not arched), the
    # arms rise on into a V over the head (left first), then the legs scissor shut -- right first -- and the knees bend while the arms come
    # forward: into the tuck that follows.
    "flipStraddle": [
        (0.0, _pose((0.02, 0.02, 0.02), ((0.75, -0.55, -0.1), (0.25, 0.3, -1.0)), ((0.75, -0.55, -0.1), (0.25, 0.3, -1.0)),
                    ((0.0, -1.0, -0.03), (0.0, -1.0, -0.05)), ((0.0, -1.0, -0.03), (0.0, -1.0, -0.05)), head=(0.06, 1, 0))),
        (0.3, _pose((0.05, 0.05, 0.05), ((0.1, 0.35, 1.0), (0.05, 0.45, 1.0)), ((0.15, 0.05, 1.0), (0.1, 0.15, 1.0)),
                    ((0.2, -0.65, 1.0), (0.2, -0.6, 1.0)), ((0.15, -0.75, 0.85), (0.15, -0.7, 0.85)))),
        (0.58, _pose((0.08, 0.06, 0.04), ((0.15, 1.0, 0.65), (0.1, 1.0, 0.55)), ((0.05, 0.6, 1.0), (0.0, 0.75, 0.9)),
                     ((0.25, -0.6, 1.0), (0.3, -0.55, 1.0)), ((0.3, -0.9, 0.35), (0.0, -1.0, 0.25)))),
        (0.8, _pose((0.15, 0.2, 0.25), ((0.7, 0.4, 0.5), (0.65, 0.1, 0.4)), ((0.5, 0.75, 0.6), (0.4, 0.8, 0.5)),
                    ((0.45, -0.85, 0.3), (-0.2, -1.0, 0.2)), ((0.55, -0.7, 0.12), (-0.3, -1.0, 0.08)))),
        (1.0, _pose((0.3, 0.5, 0.7), ((1.0, -0.2, 0.35), (0.45, -0.85, 0.1)), ((0.95, 0.1, 0.45), (0.6, -0.7, 0.0)),
                    ((0.85, 0.35, 0.1), (-0.35, -1.0, 0.05)), ((0.9, 0.25, 0.18), (-0.25, -1.0, 0.08)), neck=(0.7, 1, 0), head=(0.8, 0.7, 0))),
    ],
}


def reset_pose():
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def aim(pb, want):
    """Rotate pose bone pb (armature space, about its head) so head->tail points along want (minimal arc)."""
    bpy.context.view_layer.update()
    cur = (pb.tail - pb.head)
    if cur.length < 1e-6 or want.length < 1e-6:
        return
    q = cur.normalized().rotation_difference(want.normalized())
    h = pb.head.copy()
    M = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ pb.matrix
    pb.matrix = M
    bpy.context.view_layer.update()


def spec_for(shape, bone):
    base, side = (bone.split(".")[0], bone.split(".")[1]) if "." in bone else (bone, "C")
    key_side = base + "_" + side
    if key_side in shape:
        return shape[key_side], side
    return shape.get(base), side


def apply_shape(shape, open_k=0.0):
    reset_pose()
    for bone in CHAIN:
        if bone == "hips" or bone.startswith("shoulder"):
            continue
        pb = arm.pose.bones[bone]
        sp, side = spec_for(shape, bone)
        if sp is None:
            continue
        if sp == "follow":  # hand along the forearm
            par = arm.pose.bones[bone.replace("hand", "forearm")]
            aim(pb, (par.tail - par.head))
            continue
        if sp == POINT:  # pointed foot / toe: along the shin
            src = "shin" if bone.startswith("foot") else "foot"
            par = arm.pose.bones[src + "." + side]
            aim(pb, (par.tail - par.head))
            continue
        f, u, o = sp
        if open_k and (bone.startswith("upperArm") or bone.startswith("forearm") or bone.startswith("thigh")):
            o = o + open_k * (1.0 if o >= 0 else -1.0) * 0.6
        aim(pb, d(f, u, o, side if side in ("L", "R") else "L"))


def key_all(frame):
    for bone in CHAIN + [b.name for b in arm.pose.bones if b.name not in CHAIN]:
        pb = arm.pose.bones[bone]
        pb.keyframe_insert("rotation_quaternion", frame=frame)


report = {}
keep = {"airApex"}
arm.animation_data_create()
def _clean(shape):
    return {k: v for k, v in shape.items() if v is not None}


def resolve(shape):
    """bone -> aim direction (Vector), 'follow', 'point' or None (rest) for every CHAIN bone of a shape dict."""
    out = {}
    for bone in CHAIN:
        if bone == "hips" or bone.startswith("shoulder"):
            continue
        sp, side = spec_for(shape, bone)
        if sp is None or sp == "follow" or sp == POINT:
            out[bone] = sp
        else:
            f, u, o = sp
            out[bone] = d(f, u, o, side if side in ("L", "R") else "L")
    return out


def apply_resolved(res):
    reset_pose()
    for bone in CHAIN:
        if bone not in res or res[bone] is None:
            continue
        pb = arm.pose.bones[bone]
        sp = res[bone]
        side = bone.split(".")[1] if "." in bone else "C"
        if sp == "follow":
            par = arm.pose.bones[bone.replace("hand", "forearm")]
            aim(pb, (par.tail - par.head))
        elif sp == POINT:
            src = "shin" if bone.startswith("foot") else "foot"
            par = arm.pose.bones[src + "." + side]
            aim(pb, (par.tail - par.head))
        else:
            aim(pb, sp)


def lerp_resolved(r0, r1, t):
    out = {}
    for bone in set(r0) | set(r1):
        a, b = r0.get(bone), r1.get(bone)
        if hasattr(a, "lerp") and hasattr(b, "lerp"):
            v = a.lerp(b, t)
            out[bone] = v.normalized() if v.length > 1e-6 else (b if t > 0.5 else a)
        else:
            out[bone] = b if t > 0.5 else a
    return out


NFR = 30  # clip frames (1 s at 30 fps)
for name, keys in KEYED.items():
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    rk = [(u, resolve(_clean(shape))) for u, shape in keys]
    for fr in range(NFR + 1):
        u = fr / NFR
        k = 0
        while k + 1 < len(rk) - 1 and u > rk[k + 1][0]:
            k += 1
        u0, r0 = rk[k]; u1, r1 = rk[min(k + 1, len(rk) - 1)]
        t = 0.0 if u1 <= u0 else min(1.0, max(0.0, (u - u0) / (u1 - u0)))
        apply_resolved(lerp_resolved(r0, r1, t))
        key_all(fr)
    try:  # every frame is keyed: the interpolation only matters between frames (UE resamples at 30 fps anyway)
        fcs = list(act.fcurves) if hasattr(act, "fcurves") else [fc for ly in act.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
        for fc in fcs:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    except Exception as e:  # noqa: BLE001
        print("FLIPSHAPE interpolation not set:", e)
    keep.add(name)
    print("FLIPSHAPE", name, "keyed dense", [u for u, _ in keys])

for name, shape in SHAPES.items():
    if name in KEYED:
        continue
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    apply_shape(shape)
    key_all(0)
    # body-frame check of the key joints (feet, hands, head) relative to the hips
    hip = arm.pose.bones["hips"].head
    rep = {}
    for j in ("head", "hand.L", "hand.R", "foot.L", "foot.R", "shin.L"):
        p = arm.pose.bones[j].head - hip
        rep[j] = [round(p.dot(F), 3), round(p.dot(U), 3), round(p.x, 3)]  # forward, up, x(+L)
    rep["bones"] = {pb.name: [[round(x, 3) for x in (pb.head - hip)], [round(x, 3) for x in (pb.tail - hip)]] for pb in arm.pose.bones
                    if not any(k in pb.name for k in ("index", "middle", "ring", "pinky", "thumb"))}
    report[name] = rep
    apply_shape(shape, BREATH)
    key_all(30)
    keep.add(name)
    print("FLIPSHAPE", name, json.dumps({k: v for k, v in rep.items() if k != "bones"}))

# round 18: per-frame joint dump for the offline limb-motion estimator (flip_motion_sim.py): every bone head relative to the hips in the
# BODY frame [forward, up, x(+L)] at frames 0..30 of every flip clip
frames = {}
for name in sorted(k for k in keep if k.startswith("flip")):
    act = bpy.data.actions[name]
    arm.animation_data.action = act
    try:
        if hasattr(arm.animation_data, "action_slot") and act.slots:
            arm.animation_data.action_slot = act.slots[0]
    except Exception:  # noqa: BLE001
        pass
    seq = []
    for fr in range(0, 31):
        scene.frame_set(fr)
        bpy.context.view_layer.update()
        hip = arm.pose.bones["hips"].head.copy()
        seq.append({pb.name: [round((pb.head - hip).dot(F), 4), round((pb.head - hip).dot(U), 4), round((pb.head - hip).x, 4)]
                    for pb in arm.pose.bones})
    frames[name] = seq
report["frames"] = frames

# export only the flip actions + airApex (round-trip check)
for a in list(bpy.data.actions):
    if a.name not in keep:
        bpy.data.actions.remove(a)
arm.animation_data.action = bpy.data.actions["airApex"]
reset_pose()
kw = dict(filepath=OUT, export_format="GLB", export_animations=True, export_force_sampling=True, export_materials="NONE",
          export_animation_mode="ACTIONS")
try:
    bpy.ops.export_scene.gltf(**kw, export_optimize_animation_size=False)
except TypeError:
    bpy.ops.export_scene.gltf(**kw)
if REPORT:
    json.dump(report, open(REPORT, "w"), indent=1)
print("FLIPSHAPES_OK", OUT, sorted(keep))

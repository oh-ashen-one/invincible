# Tricks (piece C) — spec

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.

Owner (2026-09-29 / 2026-10-01): "I want the flips to look like a fucking gymnast. They need to look beautiful" and "different skins and
tricks possible, with really really high-quality well-done animations when he's flipping around in the air".
Sources: `docs/night1/director/PLAN-firstpass.md` §1 / §4 Tricks, `docs/night1/traversal/FLIPS_BRIEF.md`, `FLIPS_SPEC.md` (F1-F12, measured
from the owner's reference clip — local only, never committed).

## Acceptance (PLAN §4 Tricks) and how each line is measured

| Id | Line | Tool / column |
|---|---|---|
| P | >= 10 distinct programs in ONE 60 s clip (front / back single + double, pike, layout, twists 180 / 360 / 540, corkscrew, chains) | `tools/tricks/tricks_check.py` P (telemetry `flip_prog`) |
| V1 | same-type tricks differ >= 40 deg/s in a 0.1 s sample | V1: program rate (`flip_rate_dps`) and rendered body-axis rate (`body_pitch_deg`, 0.1 s) at the same flip time |
| V2 | durations vary +-10-20 % | V2: `flip_scale` per instance (instances below 0.90 and above 1.10, none beyond +-22 %) |
| K | tight tuck: wrists <= .15 m from the shins, knees <= .25 m apart, held >= .25 s | K: `tuck_w`, `tuck_wrist_shin_m`, `tuck_knee_gap_m` |
| L | 0 slow limb samples (critic pose.py rule) | L: `limb_z` every 0.1 s inside a trick, some component moves >= .10 m |
| G1 | straight-line layout: hip and knee angles >= 170 deg | G1: rendered bones (`-WHTrickPose` log), held layout rows |
| G2 | pointed toes | G2: foot within 35 deg of the shin line in >= 90 % of trick samples |
| G3 | spot-the-landing head motion | G3: head-vs-chest angle moves >= 15 deg in the open-out (last 45 % of the trick) |
| G4 | clean open-out before the catch | G4: last 0.15 s of every trick is an open shape turning <= 300 deg/s |
| A/B | flips >= 8 vs the owner clip (blind critic); contact sheets of ours vs the owner clip at matched phases | `tools/tricks/ab_sheet.py` |
| R | no regression on traversal's merged r23 axes (swing 7, camera 6, body 6, flips 7) | blind critic; traversal-owned code untouched |

Offline: `tools/tricks/flip_sim.py` (momentum timeline of every program: peak / mean rate, held open shape, F5 easing, twist rate) and
`tools/tricks/clip_check.py` (keyed clip geometry from the Blender report).

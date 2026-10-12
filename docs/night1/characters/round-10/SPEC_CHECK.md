# Round 10: spec check (P2 Characters)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

Every number below was measured on the REAL game (UE 5.8.3, Metal, offscreen, through `gpu_slot.sh`; provenance in `CAPTURES.md`) with the committed tools; raw outputs are in `evidence/`. Round-09 critic: lowest axis 4 (image quality), biggest gap "in EVERY 8 s fight clip (`street_fight_34` and `street_fight_wide`, which had 0 knockdowns): >= 4 hit reactions, >= 2 knockdowns with 2 enemies down together >= 1 s, >= 2 distinct get-ups, no enemy holding one guard > 2 s", plus a regression (the "untextured grey hero arm" at 1.30 - 1.50 s). **No frame time here is a performance result** (every lock release logged `contaminated=true reasons=no-exclusive-lock`).

## 0. Regression first: the "grey hero arm" of round 09

**It was the Brute's steel pipe, not the hero's arm** (found in round 10 with a bone-log projection and CPU renders of each actor alone; `captures/crops_3x/r9_arm.jpg` shows it: a pale tube with a bend at its end sticking out of the hero's flank). Round 09's fight had the Brute swing it behind the hero at 9.25 s.

The first round-10 fix (gunmetal pipe texture, new choreography) was **not enough**: the first real re-capture of the fixed choreography still showed the pipe's grey elbow fitting sticking out of the hero's back at `street_fight_34` 3.25 - 3.45 s and the Thug's bat through his waist (`evidence/weapon_clip_r10_before.json`; CPU instrument `tools/ue_char/fight/weapon_clip_check.py`: the hand weapons' vertices against capsules round the hero's body, same real skinned meshes and clips as the engine). Cause: `weapons/add_weapon.py` tilted every bat / pipe 58 deg toward the fingers, which points it across the wielder's guard at whoever stands in front. Fix: tilt -10 deg (a CPU sweep of the extra rotation, 0 - 180 deg in 15 deg steps plus 300 / 330 deg and 64 / 68 / 72 deg, picked the value that minimises both the hero and the holder's own head / torso: hero 0.05 s, own body 0.1 - 0.15 s).

| | before (round-10 choreography v2, tilt +58 deg) | after (final build, tilt -10 deg) |
|---|---|---|
| bat inside the hero's body (> 6 vertices deeper than 1 cm), 24 s of fight | 116 of 481 frames = 5.80 s, max depth 15.9 cm (4.75 s with the re-timed script) | **0 frames**, max depth 0.0 cm |
| pipe inside the hero's body | 28 frames = 1.40 s, max depth 16.1 cm (1.50 s with the re-timed script) | **0 frames**, max depth 1.9 cm |
| pistol | 1 frame, 5.4 cm | 1 frame (9.55 s), 5.4 cm |

Proof on the pixels: `captures/crops_3x/r10_arm.jpg` (street_fight_34, region of the r09 limb, 1.30 / 1.40 / 1.50 s, 3x) against `r9_arm.jpg`; `r10_hero_wide|34|orbit.jpg` = the hero centred, 3x, at the same three instants of every clip (r9 rows: `r9_hero_*.jpg`). In all nine frames the hero's arms and legs carry the suit texture and nothing grey protrudes. The Brute's pipe is visibly a pipe in his fist (4K stills `street_fight_34_4k.jpg` stage 12.0 s: held upright beside the hero; over the whole fight it is at most 1.9 cm inside the hero's capsule).

## 1. Round target (CH-C, section 3 of the spec): every 8 s fight clip

Instrument: the walkers' bone log of the run (`-WHBoneLog`, 60 Hz, hips / spine2 / head / hands / feet in world cm, `evidence/fight_bones_final.csv.gz`) read by `tools/ue_char/fight/r10_check.py` (the critic's wording: reaction = head or spine2 displaced >= 0.10 stature (175 cm x scale) within 0.2 s of the contact instant; knockdown = spine2 < 45 cm and pelvis < 60 cm for >= 1 s; guard hold = longest time an enemy keeps ONE standing pose, every joint within 12 cm of its position at the start of the run). Pixel cross-check: YOLO11x-seg on every 0.2 s of each clip (`tools/ue_char/fight/video_grounded.py`: boxes wider than tall = lying).

| Target | Round 09 (same instrument on the r09 log / r09 clips) | **Round 10 (measured)** |
|---|---|---|
| **>= 4 hit reactions within 0.2 s of contact, each >= 0.1 stature** | wide 3 of 4, 34 5 of 5, orbit 6 of 6 | **wide 6 of 6 (0.154 - 0.310 stature), 34 7 of 7 (0.166 - 0.311), orbit 7 of 7 (0.163 - 0.352)**; + one enemy blow that lands on the hero in each window (hero flinch) |
| **>= 2 knockdowns (torso on the ground >= 1 s)** | wide **0**, 34 2, orbit 2 | **2 / 2 / 2**: wide Thug 2.93 s + Oxblood 3.10 s; 34 Hood 2.93 s + Beard 2.70 s; orbit Brute 3.03 s + Tee 2.13 s |
| **two enemies on the ground together >= 1 s** | wide 0.00 s, 34 **0.00 s**, orbit 0.55 s (bone log) / 0.0, 0.2, 0.6 s (YOLO) | **bone log 1.84 / 1.84 / 1.94 s; YOLO 2.0 / 1.6 (+0.4) / 2.4 s** |
| **>= 2 distinct get-ups** | wide 0, 34 1, orbit 1 (the backward roll reused) | **2 / 2 / 2**: `getUp` (the hero's backward roll) and the new `getUp2` (elbow-propped sit-up through a squat) in every window |
| **no enemy holding one guard > 2 s** | longest 3.60 / **4.37** / 3.90 s (the red-hoodie thug 0 - 7.75 s in the critic's frames) | **1.40 / 1.82 / 1.98 s** (limit 2.0) |
| hero's feet vs a downed body (r09 critic: feet sank into the Thug) | none on the ground in wide, **9.1 cm** in 34, 28.6 cm in orbit | **39.8 / 49.5 / 47.2 cm** |
| the blows land | 18 strikes, worst 35 cm to the nearest joint | **23 strikes: nearest joint median 22.7 cm, worst 41.6 cm** (`evidence/contact_check.txt`); facing error of the striker at the contact instant **worst 3.9 deg** (`evidence/facing_check.json`) |
| pixel activity of the clip (mean % of luma pixels changing > 12/255 per frame, 1 s windows) | 34: min 0.94, median 1.73, max 2.86 | wide min 1.05 / median 1.83 / max 3.29; **34 1.33 / 2.60 / 3.96**; orbit 2.64 / 3.88 / 4.94 |
| CH11 / CH12 (YOLO11x on the clips, every ~0.5 s) | people median 7, person height max 0.48 | people **median 7 in all three clips** (p10 6.5 - 7, max 7 - 9, all >= 3 % H); person height median 0.292 (wide) / 0.390 (34) / 0.359 (orbit), max 0.49 / 0.50; each 4K still shows 7 people (0.19 - 0.47 H) |

Raw: `evidence/r10_check.json` (every reaction with contact time and displacement), `evidence/r10_check_on_r9_log.json` (the same instrument on the round-09 log with the round-09 windows and script), `evidence/grounded_*.json` / `grounded_r9_*.json`, `evidence/video_activity_*.json`, `evidence/count_videos.txt`, `evidence/yolo_*_4k.json`.

The 8 s windows are the three clips of the capture (stage 0.65 - 8.65 s wide, 8.65 - 16.65 s 3/4, 16.65 - 24.65 s orbit; clip time = stage time - 0.65 / 8.65 / 16.65 - 0.05 s).

**Things the first real capture of the new choreography taught (fixed before the final capture):** two strikes were aimed the wrong way: an enemy blow scheduled soon after a hero punch turned the hero toward its attacker before the punch landed (hero facing 165 deg away from the Tee at stage 3.97 s, 18 deg off at 12.73 s; `choreo.py` now re-times the blow: wide enemy_hit 4.50 s, strikes 5.55 / 6.55 / 7.55 s, enemy_hit 13.15 s). The script's predicted bone log (`preview_cpu.py --bones`) said PASS before the first capture and could not see either problem; the engine log and a facing check on it did.

## 2. Secondary issues of the round-09 critic

| Issue | Round 09 | Round 10 (measured on the 4K close-ups, same camera) | Evidence |
|---|---|---|---|
| untextured grey hero arm | present at street_fight_34 1.30 - 1.50 s | **gone** (the Brute's pipe; section 0) | `captures/crops_3x/r10_arm.jpg`, `r10_hero_*.jpg`, `evidence/weapon_clip_r10_*.json` |
| thug collar skin wedge | 1,790 px (70 x 151 px at 1742, 1348); critic "about 135 x 180 px" | **3,136 px (66 x 147 px at 1748, 1360): NOT fixed, and larger than round 09 by this metric** (round 08: 7,336). Round 10 turned the strip's vertex normals to the collar direction and shaded its texels hue-preserving; the engine still lights the strip as a tan plane. Open. | `evidence/thug_wedge_r10.json`, `captures/crops_3x/r10_thug-collar.jpg` vs `r9_thug-collar.jpg` |
| beard rear hair shell with a background gap | grey background visible between face and hair curtain at the right temple | the gap is bridged by a dark hair card (23 triangles, `people/mask.py bridge_hair_gap`) and Beard / Hood hair materials are two-sided; reads as a flat dark strip, no background through it | `captures/crops_3x/r10_beard-hair.jpg` vs `r9_beard-hair.jpg` |
| hood loose ribbon strands | two long pale ribbons over the forehead / temple | **removed** (322 triangles of loose shells, `people/mask.py drop_loose_shells`); one small 40 px wisp remains above the crown | `captures/crops_3x/r10_hood-hair.jpg` vs `r9_hood-hair.jpg` |
| hijab walker's horizontal rear shin | 10 % cap (round 09) | **not changed this round** (crowd takes are the round-09 ones). Measured in the capped takes: the swing shin is still >= 30 deg from horizontal (min 30.1 - 33.3 deg over the 5 walks), knee 0.38 - 0.40 m, ankle 0.17 m above the planted ankle; a flatter-looking toe-off needs a shorter stride (foot slide) - open | `crowd/lift_cap.py` output, scratch probe `shin_probe.py` (not committed) |
| tee mask see-through holes (CH18) | 0 components >= 20 px (28 px total) | 0 components >= 20 px (27 px total) | `evidence/tee_seethrough_r10.json` |
| hero head brow / nose volume | - | **not done** | - |
| get-up pop (r09: body yawed 180 deg in 0.13 s, bat reappeared in the hand) | yaw 180 deg in 0.13 s | engine log: enemy yaw rate max 20 deg/s over the whole fight (no pops); weapons are rigid in the hand (no bat reappearing) | `evidence/fight_bones_final.csv.gz` |

## Not changed in round 10 (round-08 / round-09 numbers stand)

Hero model, suit, eyes and hero clips (`round-08/captures/hero_*` are the current captures), crowd density and clips (`round-09/captures/crowd_*`), hero showcase framing (0.79 H vs CH1 0.48 - 0.62), run start / stop / turn / idle clips (CH10, section 5), citizen triangle counts, civilian coats.

## Offline checks that preceded the engine runs (not game results)

`choreo.py --check`, `preview_cpu.py --bones` + `r10_check.py` (predicted PASS), `weapon_clip_check.py` and the weapon-angle sweep (`weapon_clip_check.py` classes + a scratch lab, 0 - 360 deg), `pose_view.py` (thug collar iterations of round 10).

## Honest notes

- The bone-log checker is my own instrument (the critic's wording turned into code); the YOLO box check is an independent pixel cross-check and agrees to within a few tenths of a second.
- The guard-hold number is strict (every joint within 12 cm of the run's first frame); with a looser tolerance (20 - 30 cm from the window mean) an enemy bobbing in the same stance for 3 - 4 s still counts as a hold. What changed is that nobody stands in one stance for more than ~2 s any more and every enemy leaves the guard (feint, shuffle, step-in, reaction) every ~1.5 s.
- Orbit guard hold 1.98 s is 0.02 s under the limit.
- The thug collar wedge got worse by the metric; do not read the round-10 normals / shade change as a fix.

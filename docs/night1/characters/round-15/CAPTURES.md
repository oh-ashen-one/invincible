# Round 15: captures (P2 hero skins: rim behind the brow, sharp brow trim, net on seam cords, the pawn on the merged ground blend)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Round target (director, after the r14 critic [hero 6, anim 5, enemies 5, civilians 5, IQ 5; IP PASS]):** first merge `origin/Opus-5.5-Loop-Night-1` (P3 r22: `GroundBlendS` 0.18 s in `WebTravAnimInstance.cpp`) and re-shoot the pawn swap movie; then the P2-owned lines:
(R1) on all 8 4K headside stills the front-most pixel of the lens RIM lies >= 1 % of the head height (>= 16 px) BEHIND the front-most pixel of the brow (critic r14: Verdant rim 18 px proud); (Q5) the accent pipe joins the Ash sash end (no cord pixel > 5 px off the end);
(net) every net / groove line terminates on a seam cord; (Q7) no texture stretch under the brow shelf; (Q6) the Verdant armpit piping is not pinched. Gate: no axis below r14 [6,5,5,5,5], enemy pack / crowd unchanged, swatch sheet regenerated for the owner.
The pawn's run CADENCE is P3's (routed to traversal, not a P2 gate). Numbers: `SPEC_CHECK.md` (every number is read from `evidence/` by `tools/ue_char/suits/spec_check_r15.py`).
**The OWNER must approve the suits before any merge: `SWATCH_SHEET.jpg` (8 suits, front + back + chest + head; new since r14: yoke seam cords across the chest and back, a deeper brow / eye socket, a thin accent pipe on the sash end).**

**Source.** The REAL game: UE 5.8.3 `-game`, Metal, offscreen (`Scripts/run_game.sh`), through the GPU lock (`gpu_slot.sh capture`), driven by `tools/ue_char/suits/chain_r15.sh` (`STEPS="build stills lineup pawn orbit hero chase fight crowd"`, `EV=10.0`, `P2_FIRST_EXTRA=9`, run from the snapshot `.chain_r15_run.sh` by `hold_r15.sh`).
**One hold: 2026-10-02 09:06:44 - 09:33:36, 1612 s of hold after 6460 s in the queue, 0 engine crashes, one engine of mine at a time, the engine stopped by the script's own `-quit` (never killed, no `stop_ue.sh` needed); the lock reported `contaminated=true` (no exclusive lock: other agents' engines rendered nearby; GPU 0 % before 16 of 18 runs, 74 % before two,
`evidence/gpu_util_before_runs.txt`), so no frame time here is a performance number.** The content was rebuilt from the committed scripts first inside the hold (`build_fight.sh clean,tex,mat,mesh,citizens,rename,fightclips,abp,map,maps5,skins,skinsmap`, 230 s, 8 suits OK; `/Content` is not committed); the hero GLB and the suit maps are prepared on the CPU beforehand
(`tools/ue_char/suits/prep_hero_r15.sh`, `gen_suits.py --n 4096 --n-color 8192`, `hero_suit_r8.py --n 8192`).
**Resolution (disclosed).** 4K stills: output 3840x2160, internal 3840x2160 (`r.ScreenPercentage 100`, `evidence/stills_perf.json`, `lineup_perf.json`), committed as 4K JPEG (q2) (front, chest, head, head34, headside, headfront, lineups) or 1920 px (back); the measures ran on the lossless PNG originals (scratch dir `$P2_SCRATCH/r15/chain1/run/stills`).
Movies: 1920x1080 output = 1920x1080 internal, `-movie` = every frame dumped at a fixed 1/60 s step, H.264 crf 18-20, each <= 7.3 MB (largest `swap_pawn_T_key.mp4`). The first 0.1 s of the engine's pawn movie are camera-binding frames (a far default camera, a sky frame, a rear view), trimmed away exactly as in r14 (`post_r15.sh`: `-ss 0.1`).
The base colour maps of the 7 generated suits are 8192 px now (normal / ORM 4096; Tessera 8192 for all three): the first still waits 12 s of stage time instead of 3.7 s so the 24 textures can compile (`textures_resident=4/4` at every swap but the first of each run, which logs 2/4 resp. 3/4 while the compile finishes; no white mannequin in any still: the hero's mean luma is 148 - 164 in all 8 front stills).

| file | map / shot | what |
|---|---|---|
| `stills/skin_<suit>_headside_4k.jpg` (8) | Char_Skins, view `headside`: profile, 1.25 m, aim 166.5 | **R1** rim behind the brow, **Q7** brow trim sharpness, G1 / G2 |
| `stills/skin_<suit>_head_4k.jpg`, `..._headfront_4k.jpg`, `..._head34_4k.jpg` (8 + 8 + 8) | views head (12 deg), headfront (0 deg), head34 (25 deg) | G3 cheek lines, H1 - H6 |
| `stills/skin_<suit>_front_4k.jpg`, `..._chest_4k.jpg` (8 + 8) | views front (7.85 m, CH1) and chest (1.5 m) | CH1 0.542 - 0.544; **Q5** Ash sash end, **Q6** Verdant armpit, the yoke seam cords |
| `stills/skin_<suit>_back_1080p.jpg` (8) | view back | |
| `SWATCH_SHEET.jpg` | composed from the 4K stills (front + back + chest + head of all 8 suits) | **the owner's sheet** (sign-off still required before any merge) |
| `swap_pawn_T_key.mp4` (11.4 s) | Char_SkinsPlay, the PLAYABLE pawn (spawned on the ground since r15), 7 injected real T presses, P3 r22 ground blend | **pawn test P1 / P2**, swap movie: 7 / 7 presses on the pixels, worst 33 ms |
| `orbit_all_suits.mp4` (11.4 s) | Char_Skins orbit shots | the stage hero orbiting through every suit |
| `hero_run_side.mp4`, `hero_run_34.mp4`, `hero_run_leap_side.mp4`, `hero_run_chase.mp4`, `hero_run_toward.mp4` | Char_Hero shots 1-3 / 6-7 (as round 08) | the stage hero (Tessera): CH6 / CH7 / CH2 instruments |
| `street_fight_wide.mp4` (8.0 s), `crowd_tracking.mp4` (8.0 s) | Char_Fight shot 0 / Char_Crowd shot 0, unchanged | `evidence/fight_unchanged_since_r10.txt` (identical script, choreography, weapon fit) |
| `enemy_lineup_4k.jpg`, `enemy_lineup_34_4k.jpg` | Char_Lineup shots 5 / 6 | 7 enemies, wall luma 139 as in r13 / r14 |

## Results at a glance (details and every other line: `SPEC_CHECK.md`)
| line | r14 | r15 (real game) | verdict |
|---|---|---|---|
| **R1** rim behind the brow, % of head height (gate >= 1 % = >= 16 px) | Verdant -14 px (critic -18); all 8 suits proud of the brow or < 11 px behind | **34 - 49 px = 2.3 - 3.3 %** on all 8 | **PASS 8 / 8** |
| **Q5** Ash sash-end pipe: pixels between the pipe and the border cord (p90 / max; gate <= 5 px) | 33 / 80 | **2 / 10** (pipe 4 px wide, on the end line) | **PASS** |
| **net ends** (the paint itself, 4096): dead-end blobs in open fabric, all 8 suits (torso net) | 434 (105) | **83 (1)**; armpit crease zone 116 -> 95 (not counted) | torso PASS; **limbs not finished** (see problems) |
| **Q7** brow trim edge rise, r15 / r14 (smaller = sharper) | smeared by eye | Verdant 0.67, Cinder 0.73, Saffron 0.59, Sage 0.61; Tessera 1.01 (it was 8192 already), Plum 0.95, Glacier 1.07, **Ash 1.55**; by eye (crops `evidence/measures/iq/q7_brow_*.jpg`) the trim is sharp on every suit I looked at | by eye PASS, the instrument is noisy |
| **Q6** Verdant armpit cord: thickness min / median (gate >= 0.5), gap columns | 0.0, 13 gap columns | **0.46, 0 gap columns** (the cord ends on the cap edge instead of crossing the crease) | **FAIL by my own gate** (0.04 short), pinch / break fixed by eye |
| pawn: luma pops 0 - 1.5 s (whole frame / hero blob) | 1 / 1 (9.5 at 0.133 s) | **0 / 0** (max 5.2) | **PASS** |
| pawn: `anim_weight` step <= dt / 0.18 | 0 | 0 (vacuous: `anim_weight` is the TOTAL weight, always 1.0) | PASS (vacuous) |
| G1 recess / G2 brow over lens top / G3 cheek lines (3 views) | 8 / 8 | **8 / 8** (G1 7.8 - 8.0 %, G2 6.0 - 7.0 %, G3 13/13 lines on every suit and view) | PASS |
| H4 own gate: ONE closed raised rim >= 6 px on >= 90 % of the angles | 2 / 8 | **2 / 8** (Glacier, Sage) | unchanged FAIL |
| IP guard / seams / OCR / swap latency / regression | PASS, min palette distance 38.4 | PASS, **49.6**, worst seam 3.3 px, 0 OCR hits, 7 / 7 presses, 33 ms, `REGRESSION PASS` | PASS |
| enemy pack lineup / fight / crowd | unchanged since r13 / r10 | unchanged (wall luma 139, fight script identical to r10) | unchanged |

## What changed in the content this round (all committed, all script-generated)
- **Head** (`tools/ue_char/suit8/hero_head_r14.py` PARAMS, `tools/ue_char/hero_lens_r14.py`): brow shelf 11 -> 13.5 mm, eye socket -5.2 -> -8.8 mm, inner corner -5.0 -> -7.5 mm, lenses centred 41.0 -> 43.5 mm from the midline, rim crest 3.1 -> 2.6 mm: the lens + rim sit 3.6 mm deeper under a stronger brow. Mesh numbers (CPU): recess 7.2 % HH, brow over the lens top 6.95 %, over every rim vertex 5.3 % (r14: 1.4 %).
  **The head is posed in the stills (idle clip: pitched back ~6 - 7 deg, camera ~86 deg off the face axis); a rest-pose model reproduced the r14 silhouette to 2.9 px rms and the r14 rim / glass offsets to 1 px at pitch -7 / yaw -88 (`tools/ue_char/suits/dev_r15/cpu_rim2.py`, `cpu_fit.py`); at that pose the r15 mesh predicted the rim 39 px behind the brow, the real stills measure 34 - 49 px.** r14's geometry had passed the rest-pose test (T2b 1.4 % HH) and failed in the real posed frame: the head tilt costs ~34 px.
- **Texel density** (`gen_suits.py --n-color 8192`, `hero_suit_r8.py` as before): the browser atlas has 0.7 - 1.0 mm per texel on the brow / forehead at 4096 (chin 0.22, torso 0.42), so the hood trim smeared under the brow in the profile stills while Tessera (8192) was sharp. The base colours of the other 7 suits are 8192 now (normal / ORM from the 2 x 2 average of the 8192 paint at 4096).
- **Net / seams** (`design.py`): the torso net is a YOKE PANEL with hard edges (y 1.31 - 1.43, outside the shoulder caps, inside the side wedge) and a raised seam cord (the face-seam tone) on the top and bottom edge, front and back; the wedge edge is its side seam from the yoke's bottom to its top; the arm nets stop at the cap's inner ring cord (no net on the shoulder top);
  the limb nets end hard on a cord that is already there: the wrist bands, the ankle bands, the knee / elbow slab rings, the hip-wrap cut piping (the right thigh and the left thigh net now run down to the knee ring).
- **Sash end** (`design.py`): the accent pipe lies ON the end line (1 mm wide, inner edge touching the DEEP border cord) instead of 5.8 mm outside it.
- **Armpit** (`design.py`, `cap.r_in`): on the torso side the shoulder cap ends 7.5 cm from the arm axis (r14: 10.8 cm all around), so its ring cords and INK edge no longer run over the armpit crease; the raglan edge across the chest and the shoulder is unchanged.
- **Pawn** (`tools/ue_char/suits/pawn_run.json`): the pawn spawned 25 cm in the air since r11 (z 1.2): a 12-frame fall, `airRise` clip at 0.15 s, `idle` at 0.3 s = the "pose pop at frame 7 - 8" of r14, an artefact of MY script, not of P3's blend. It spawns on the ground now (z 0.95). With the merged `GroundBlendS` the start is idle -> jog @0.90 s -> run @1.00 s with no walk step.
- Instruments (committed): `rim_depth_r15.py`, `iq_check_r15.py` (Q5 / Q6 / Q7), `net_end_check_r15.py` (the paint's own net zones vs cords), `pawn_check_r15.py`, `chain_r15.sh`, `hold_r15.sh`, `post_r15.sh`, `spec_check_r15.py`, `make_pairs_r15.py`, `test_regression.py` EXPECT_R15.

## Known problems (honest list)
- **Q6 is 0.46, not >= 0.5** and the cord now simply ENDS at the cap edge near the crease (a short dark stub remains, crop `evidence/measures/iq/q6_verdant_armpit.jpg`). A smaller `cap.r_in` (6.5 cm) would end it earlier, on the arm.
- **A step in the yoke bottom seam cord at the armpit side** (Verdant chest still, x ~1300 y ~1320; ~17 px = 3.5 mm): the browser mesh has a discontinuity at the torso / arm island seam; r14's rib lines had the same jog (it is just more visible on a long cord). Not fixed.
- **Net ends on the LIMBS are not finished**: 83 open-fabric dead-end blobs remain (left upper arm 33, thighs 40, forearm / shin 12, torso 1); the cause is skin-weight ramps and island seams, not the hard cuts. A lenient weight made it worse (231). The 95 in the armpit crease zone are folded away under the arm in the idle pose.
- **H4 (my own strict rim criterion) is still 2 / 8** (Glacier, Sage); the rim is a clear closed band by eye on all 8 (a lower crest of 2.6 mm did not change it). Next experiment: a dark non-metallic rim with a bright inner lip.
- **Q7 is a noisy instrument** (a glint or a flash can enter its window; `windows_sane` is False for Sage / Saffron): read the crops. Ash's edge-rise ratio is 1.55 (r15 / r14) but its trim reads sharp in the crop; I did not chase it.
- **The cheek panel seams still read as "tear tracks" from the lower eye frame** in the profile and front stills (critic r14 hero axis); not touched this round.
- **CH2 chase framing 0.373** (gate 0.39 - 0.53; the round-08 clip read 0.372, r13 0.389, r14 0.392): an edge line that flips with the mask, unrelated to this round; the chase shot distance of `Char_Hero` shot 6 needs ~5 % less.
- **Cinder shoulders** (faceted, r13 critic): unchanged since r14, not in this round's brief.
- The pawn's run CADENCE (4.0 steps/s) is P3's; `anim_weight` cannot show the ground blend (it is the total weight): the test P2 is vacuous, the real evidence is P1 (luma) and the pose-signature steps (largest / median 3.0 -> 1.7).
- Hold contaminated (other agents' engines rendered nearby); the lineup / fight / crowd are re-captures of unchanged content.

## Evidence (`evidence/`)
`rim_depth.json` / `.txt` (+ r14 baseline, `measures/rim_overlays/*.jpg`), `iq_check.json` + `measures/iq/*.jpg` (Q5 / Q6 / Q7 crops r14 | r15), `net_end.json` + `net_end_r14.json` (+ `measures/net_end/*.jpg`: dead ends in red over the base colour), `pawn_check.json`, `pawn_telemetry.csv`, `head_check.json` / `.txt` + `measures/head_overlays/*.jpg`, `head_profile_mesh.json`,
`measures/` (relief / sash / jog of the chest stills, CH1, CH2 / CH6 / CH7 of the clips), `ipguard.json`, `seams.json`, `ocr_stills.json`, `regression.txt`, `swap_latency.json`, `lineup_exposure.json`, `fight_unchanged_since_r10.txt`, `characters_build.log`, `chain.log`, `pawn_*`.
Critic pairs: `critic_pairs.json` (42 pairs); the pack is in `/Users/midir/sm2-n1/_scratch/critic-P2-r15/pack` (key outside it).

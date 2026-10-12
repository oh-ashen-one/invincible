# Round 16: captures (P2 hero skins: no front emblem / sash on the backs, no stair-step cord jogs, a straight face seam, every limb net line ends on a cord)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Round target (director, after the r15 critic [hero 6, anim 5, enemies 5, civilians 5, IQ 5; IP PASS]; the owner approved the suits at 11:31 and r14 is merged as the skins baseline):** raise Image quality to >= 6 by closing the r15 critic's four 4K defects without adding one:
(1) all 8 back stills committed at 4K and no cluster >= 20 px of the front emblem / sash palette inside the back torso mask; (2) where a groove cord meets a panel border on the 8 chest stills the step is <= 4 px; (3) on the 8 headfront stills the face centre seam deviates <= 10 px laterally per 100 px;
(4) net_end_check open-fabric dead ends 83 -> 0, Verdant armpit Q6 >= 0.5, the Ash notch smear (~1480, 1170) gone; (5) a no-new-defect crop pass, r16-vs-r14 progress pairs win or tie blind, enemy pack and crowd unchanged, IP guard + OCR PASS.
First: `origin/Opus-5.5-Loop-Night-1` merged into `night1/characters` (85683fa6; the C++ module rebuilt). The pawn's run cadence (4.07 Hz) is P3's; `Traversal/` was not edited.
Numbers: `SPEC_CHECK.md` (every number read from `evidence/` by `tools/ue_char/suits/spec_check_r16.py`).

## Source, holds and resolution (disclosed)

The REAL game: UE 5.8.3 `-game`, Metal, offscreen (`Scripts/run_game.sh`), every engine run through the GPU lock (`gpu_slot.sh capture --label characters`), driven by `tools/ue_char/suits/chain_r16.sh` from a snapshot (`hold_r16.sh`, READY gate). One engine of mine at a time, 0 engine crashes, no OS dialog, every stop by the script's own quit or by `stop_ue.sh` (SIGTERM, never SIGKILL).
The content was rebuilt from the committed scripts inside each hold (`build_fight.sh clean,...,skins,skinsmap`, `/Content` not committed); the hero GLB (`prep_hero_r16.sh`) and the suit maps (`gen_suits.py --n 4096 --n-color 8192`, `hero_suit_r8.py --n 8192`) were prepared on the CPU first.
The lock admitted 4 - 6 holders at once this afternoon (its status read "6/2 in use"; `contaminated=true` on every hold): the 4K stills rendered at **1.4 - 1.5 fps** (`evidence/stills_perf.json`), so **no frame time here is a performance number**.

| hold | when | what it gave | used |
|---|---|---|---|
| 1 | 12:21 - 12:32 | build + 23 of 56 stills: the process-time `-quit` cut the stills because the stage clock ran at ~1/3 of real time; with 6 holders on the lock I stopped it myself (`stop_ue.sh`, "stopped cleanly") | no (diagnosis only) |
| 2 | 12:55 - 13:33 (2267 s) | build + 56/56 stills (the director now quits 3 s after the last stage shot, `-WHStageShotQuit`) + both lineups + the pawn movie; the orbit was stopped by me at 527 / 756 frames before the 40 min max hold (the lock SIGKILLs 10 s after its SIGTERM) | **lineups, pawn movie**; its stills not used: Tessera's first views caught its 8192 px maps at a low mip, and Saffron's maps changed after it |
| 3 | 14:04 - 14:32 (1676 s) | build + 56/56 stills + the orbit, 0 crashes | **every still, the swatch sheet, the orbit** |

- **4K stills:** output 3840x2160 = internal 3840x2160 (`r.ScreenPercentage 100`), committed as 4K JPEG (q2) for EVERY view now, the backs included (`stills/skin_<suit>_<view>_4k.jpg`, 56 files); every measure ran on the lossless PNG originals (`$P2_SCRATCH/r16/chain3/run/stills`). Combined run dir for `post_r16.sh`: `tools/ue_char/suits/combine_r16.sh` (symlinks: stills / orbit from hold 3, pawn / lineups from hold 2).
- **Movies:** 1920x1080 output = internal, `-movie` = every frame at a fixed 1/60 s step, H.264 crf 18 - 20: `swap_pawn_T_key.mp4` 7.2 MB (11.4 s, the first 0.1 s of camera binding trimmed as in r14 / r15), `orbit_all_suits.mp4` 4.9 MB (11.4 s). Both <= 15 MB.
- **Not re-shot this round** (content unchanged; the hold budget went to the stills): the stage-hero run / chase clips, the fight and the crowd clips. The critic pack uses the round-15 files for them (`make_pairs_r16.py` falls back to `round-15/`); `evidence/fight_unchanged_since_r10.txt` holds. The stage hero wears Tessera, whose BACK changed this round (no sash / accent mark): the r15 chase clip still shows the old back.

## Results (details: `SPEC_CHECK.md`)

| line | r15 | **r16** (real game, hold 3 stills) | verdict |
|---|---|---|---|
| (1) back bleed: accent clusters >= 20 px in the back torso mask, 8 backs (`back_bleed_r16.py`) | 1 - 8 per suit, largest 297 - 10 276 px (every suit) | **0 on all 8** (Saffron: 113 scattered px, no cluster) | **PASS 8 / 8** |
| (2) cord jog where the yoke seam cord crosses the torso side under the arm, 8 chests (`cord_jog_r16.py`, gate <= 4 px) | 8.0 - 36.2 px (Ash 36.2, Sage 32.0, Cinder 18.6, Tessera 17.1, Verdant 14.0) | **0.5 - 0.9 px** | **PASS 8 / 8** |
| (3) face centre seam dev100 on the 8 headfront stills (`seam_track_r16.py`, gate <= 10 px / 100 px) | Cinder 15.9 (range 52.8), Glacier 13.8, others 2.9 - 7.7 | Tessera 4.5, Plum 4.7, Ash 6.7, Saffron 2.6, Sage 8.4; **Cinder 10.9 (range 33.8), Glacier 10.6**; Verdant not tracked (the tracker lost the seed; straight by eye) | **5 / 8 measured PASS** (hold 2, same content: 8 / 8 <= 8.8) |
| (4a) net_end_check open-fabric dead ends, 4096 px | 83 | **0** (crease zone 95 -> 45) | **PASS** |
| (4b) Q6 Verdant armpit cord pinch (gate >= 0.5) | 0.46 | **0.54** | **PASS** |
| (4c) Ash notch smear (~1480, 1170) | weave-flip notch patches | gone (`evidence/measures/ash_notch_r15_r16.jpg`, r15 left / r16 right) | **PASS by eye** |
| R1 rim behind the brow / G1 - G3 / H4 (own) | 8/8 / 8/8 / 2/8 | 8/8 (33 - 48 px) / 8/8 / **3/8** (Plum new) | kept |
| IP guard / OCR / seams / regression / swap | PASS (49.6) / 0 / PASS / PASS / 7 of 7, 33 ms | PASS (min palette distance 49.3) / 1 hit = Glacier chest "MIRA", tesseract noise on the hex net (`evidence/ocr_review.txt`) / worst 2.4 px / PASS (`EXPECT_R16`) / 7 of 7 presses | PASS |
| pawn start (P1 luma pops 0 - 1.5 s) | 0 | 0 (largest 5.17) | PASS; cadence 4.13 Hz is P3's |
| enemy pack / crowd | unchanged | lineups re-shot (unchanged content), fight / crowd not re-shot (r15 files) | unchanged |

## What changed (all committed, all script-generated)

- **The stair-step jogs were a skin-weight bug, found on the CPU.** A posed CPU render of the prepped GLB in the idle clip (`tools/ue_char/suits/dev_r16/posed_render.py`) reproduced the r15 jog exactly; the edge strain (`dev_r16/strain.py`) peaked at 2.6 (median 0.22) at |x| 0.16 - 0.18 m, y 1.30 - 1.34 m: the round-12 weight smoothing leaves FIVE bones there (spine2, spine1, shoulder, deltoid, upperArm) and the plain top-4 truncation dropped spine1 on one vertex and upperArm (0.14 - 0.18) on its neighbour, so the hanging arm pulled them ~0.15 x its motion apart.
  `tools/ue_char/suit8/hero_weights_r16.py` merges bones that move alike (spine1 into spine2, spine into spine1, hips, glute, neck) before truncating, never an arm bone: max strain 2.6 -> 0.97 on three idle poses; the in-game jogs went from 8 - 36 px to <= 0.9 px and the Ash notch smear (folded faces) disappeared. `prep_hero_r16.sh` runs it.
- **Backs** (`design.py`): the sash is a FRONT panel (it also ends on the coronal plane z = -0.012 m, finished like every end; the end finishing of the other ends is gated to the front: hold 1 showed short accent pipes floating on the Plum back); the back mark is a tone-on-tone emboss (`glyph.back = 'tone'`), not the accent; the wedge edge pipe is accent on the front and the seam tone on the back.
- **Limb nets** (`design.py`, `net.geo`): the limb net zones are bounded by geometry, not by the soft skin weights: planes that carry a cord (the cap's lower ring, the elbow / knee slab rings, the wrist / ankle bands, the hip-wrap cut piping) and a radius around the limb axis; on the sleeveless suit (Saffron) the bounding planes get ring cords of their own (directional radius, so they stay on the arm) and the yoke panel a side seam; where the hip-wrap cut lies above the crotch an inseam cord closes the two thigh nets.
- **Headfront portrait** (C++ `WHShot.bHeadLock`, `WHCharShowDirector.cpp`; `build_characters.py` sets it on `headfront`): the camera is moved into the head's midsagittal plane (normal = the actor's right axis turned with the head bone) with its up axis in that plane, so the idle head yaw / roll no longer swings the seam off the camera axis (a nod is not followed; the stage framing is kept). Disclosed: this is a framing change of the headfront still. It removes most of the zig-zag (Cinder range 52.8 -> 33.8 px) but not all: the lower face is partly neck-weighted, so the residual depends on the idle phase (hold 2: Cinder 7.4, hold 3: 10.9).
- **Capture robustness** (`WHCharShowDirector.cpp`, `chain_r16.sh`): `-WHStageShotQuit` (the stills run quits 3 s of stage time after its last shot instead of at a process-time deadline) and `-WHStageWaitTextures` (holds the stage clock while the target's suit textures are not fully streamed in). Honest note: in hold 3 the wait never triggered (0 `WH_STAGE_WAIT_TEX` lines) although the suit log still reports `textures_resident=0/4` at the first swap, so `IsFullyStreamedIn` may not see what the 1.4 fps hold 2 showed; hold 3's Tessera stills are sharp (checked by eye on the 4K crops).
- **Instruments** (committed): `back_bleed_r16.py`, `cord_jog_r16.py`, `seam_track_r16.py`, `crop_sheets_r16.py`, `post_r16.sh`, `spec_check_r16.py`, `make_pairs_r16.py`, `combine_r16.sh`, `test_regression.py` `EXPECT_R16`; CPU dev aids in `tools/ue_char/suits/dev_r16/`.

## No-new-defect crop pass (8 suits x chest / back / headfront / front; `evidence/measures/crops/crops_<suit>.jpg`, r15 row over r16 row) - every residual I saw

- **Fixed**: the yoke-seam stair-steps on all 8 chests; the Ash notch smear; the front sash / emblem on every back; the floating sash-end pipes of hold 1; the Saffron arm-ring stub of hold 2; the Tessera low-mip stills of hold 2.
- **Residual, seam**: Cinder's headfront seam still drifts (33.8 px over the face, dev100 10.9) and Glacier's measures 10.6; Verdant's seam is not tracked by the instrument in the committed still (straight by eye).
- **Residual, present in r15 too**: a thin dark net line hangs below the yoke seam at the armpit edge on Saffron and Sage (the left upper-arm net reaches the torso side under the arm; it ends in the armpit crease zone); the yoke bottom seam cord bends gently (a shallow V, a few px) at the sternum on several suits; the cheek panel seams still read as tracks from the lower lens frame; H4 (my strict rim criterion) 3 / 8.
- **Changed look the critic will see**: the backs are plainer (no sash, a dark tone-on-tone mark, the spine stripe and the yoke seams remain); the headfront portraits are centred on the face (head-locked).
- Q5 (Ash sash-end pipe): p90 gap 2 px as in r15; the max rose 10 -> 80 px at the panel's top corner where the end line meets the upper edge (by eye the pipe is attached along the end: `evidence/measures/iq/Q5_ash_sash_end.jpg`). Verdant sash longest dark run 11 px (r15 9, target 10).

## Critic pack

`/Users/midir/sm2-n1/_scratch/critic-P2-r16/pack` (56 pairs, key `pack.key.json` outside it; `critic_pairs.json` here): suit fronts / backs / chests / heads / profiles vs references, the swatch sheet, the pawn swap movie, the orbit, the lineups, the r15 stage-hero / fight / crowd clips; **progress pairs against the MERGED round 14** (lossless 4K PNG vs PNG): 8 backs, 4 chests, 4 headfronts, the head, the Verdant profile, the Sage head34, the pawn movie, the lineup; and **r15 -> r16** pairs on the four named defects (Tessera back, Verdant chest, Cinder headfront, Ash chest).

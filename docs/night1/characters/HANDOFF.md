# P2 Characters: handoff (round 17, first-pass piece G: hero skins)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

Branch `night1/characters`, worktree `~/sm2-n1/characters`, UE MCP port 8772, browser dev port 5203. Round 17 author: Sonnet 5.5 xhigh via Devin (2026-10-02 20:35 - 22:50 EDT), resuming the WIP of an interrupted Claude Code session (d2df6f7d, 9b71fc21, 65366270); round 16: Opus 5.5; round 15: Sonnet 5.5.
Everything described here is committed and pushed (`origin/night1/characters`); `/Content` is NOT committed (script-generated). No engine of mine is running; the C++ editor module is built (`Scripts/build_editor.sh`, ~25 s). `origin/Opus-5.5-Loop-Night-1` was NOT merged this round (it only added docs since the r16 merge).

## STATE AT THE END OF ROUND 17 (read this first)

Round target (director, after the r16 critic [hero 6, anim 5, enemies 4, civilians 5, IQ 4]): remove the enemy lineup corruption (blotches, halos, ghost weapons) with a settle-frames capture protocol and PROVE its cause; keep every r16 gain; sash / groove edges within 4 px; face seam through the chin, cord ends finished; crowd cut; Verdant away from a known green-and-yellow costume.
**No blind critic verdict yet**: the pack is `/Users/midir/sm2-n1/_scratch/critic-P2-r17/pack` (key `pack.key.json` outside it, `round-17/critic_pairs.json`). Captures / holds / the cause measurement / honest limits: `round-17/CAPTURES.md`; every number: `round-17/SPEC_CHECK.md`.

Results (real game, 4K PNG originals; every number in `round-17/SPEC_CHECK.md`, honest limits in `round-17/CAPTURES.md`):

| line | r16 | **r17** (real game, 4K PNG originals) | verdict |
|---|---|---|---|
| (1) `enemy_lineup_4k.jpg` > 20 luma vs the previous clean lineup (gate <= 2 %) | 13.664 % / band 26.623 % | **0.453 % / band 1.497 %** (vs r15 0.436 % / band 1.441 %) | PASS |
| (1) `enemy_lineup_34_4k.jpg` (3/4) | 3.027 % / band 9.313 % | **0.309 % / band 1.019 %** | PASS |
| (2) back bleed: accent clusters >= 20 px in the back torso | 0 on 8 | **0 on 8** | PASS |
| (2) yoke-seam cord jog under the arm, gate <= 4 px | 0.5 - 0.9 | **0.5 - 5.3** (max over 8: 5.3; under-arm run only: Ash 1.0) | **7 / 8** by the instrument (Ash: 5.3 px at x 1665 = the cord's end cap at the sash border, see below) |
| (2) face centre seam dev100 <= 10 px | 5 / 8 measured (Cinder 10.9, Glacier 10.6, Verdant untracked) | tessera 4.3, verdant 4.3, plum 4.0, cinder 5.2, glacier 11.2, ash 5.8, saffron 2.6, sage 8.7 | **7 / 8** (Glacier: tracker reading, see below) |
| (2) net-end dead ends in open fabric (paint, 4096 px) | 0 | **0** | PASS |
| (2) IP guard (P1 - P7) / OCR hits | PASS (49.3) / 1 reviewed noise hit | **PASS** (min palette distance 43.5) / 1 reviewed noise hit (`evidence/ocr_review.txt`) | PASS |
| (2) swap: presses visible / latency | 7 of 7, 33 ms | **6 of 7**, [33.3] ms | 6 of 7 by the histogram matcher; the 7th press (Tessera -> Verdant, engine set at 8.717 s frame 522, swap_done 4/4 textures resident) is visible between 8.55 s and 8.9 s (`evidence/measures/swap7_tessera_to_verdant.jpg`) but the matcher found no step |
| (2) pawn luma pops 0 - 1.5 s | 0 | **0** (largest 5.183) | PASS |
| (2) Q6 Verdant armpit piping pinch ratio (own gate >= 0.5) | 0.54 | **0.27** (min 3 px, median 11.0 px; the copper cord is intact and tapers into the crease like r16, `evidence/measures/q6_pair.jpg`) | FAIL by the instrument |
| (2) R1 lens rim behind the brow (>= 1 pct of head height = 16 px) | 8 / 8 (33 - 48 px) | tes 33.0 px, ver 41.7 px, plu 50.0 px, cin 36.0 px, gla 22.0 px, ash 46.7 px, saf 42.7 px, sag 62.3 px | PASS 8 / 8 |
| (2) G1 / G2 / G3 (head sculpt) | 8 / 8 each | G1 8 / G2 8 / G3 12 deg 8, 0 deg 8, 25 deg 8 of 8 | PASS |
| (3) sash / groove edge steps > 4 px on long edges (both runs >= 100 px), 8 chests (`line_step_r17.py`) | 20 (largest per suit: tes 29.6, ver 13.7, plu 29.4, cin 5.3, gla 9.8, ash 26.9, saf 9.3, sag 14.8) | **13** | the named defects are gone (Ash shelf 26.9 px, Verdant step 13.7 px); 13 long-edge jogs of 4.5 - 10 px remain: NOT met |
| (3) pawn clip step at 9.933 s | 15.49 vs neighbours 3.48 (a director shot end) | **5.1** vs neighbours 3.79; cuts in the clip: 0 | PASS |
| (3) crowd clip step at 7.483 s | 55.6 vs neighbours 1.89 (a director shot end) | **2.27** vs neighbours 2.02; cuts in the clip: 0 | PASS |
| (3) face seam through the chin / cheek-cord ends | Cinder seam broke and jogged at the chin; cheek cords cut square | seam continuous through the chin on all 8 (`evidence/measures/chin_crops.jpg`, r16 row over r17 row); the four cheek cords close in a rounded tip (`design.py`, EXPECT_R17) | by eye |
| (4) Verdant | brass yellow accent, yellow forearm / shin blocks, yellow crown stripes | forest green + dark pine + copper, no yellow, plain crown; IP guard PASS, nearest suits tessera 43.5, ash 44.2 | `SWATCH_SHEET.jpg`, `VERDANT_BEFORE_AFTER.jpg` |

### What changed (details in `round-17/CAPTURES.md`)
- **THE KEY FINDING: the r16 lineup was captured while the engine was still compiling assets and while everything still moved.** The r16 command (`-shots 3.0`) fires at engine frame 12 on today's lock (the first frames of a 4K run take 0.15 - 6 s): 12 of 27 assets still compiling, 0 textures non-resident, the characters' idle animations and 31 lane walkers running. Dose-response (`-WHShotFrames`, one run): the > 20 luma share falls 7.1 % (27 compiling) -> 4.5 % (12) -> 1.5 % at 0 compiling; the residual at 0 compiling is the running animation (E1: frozen animations, 1 static frame, same compile state: 0.06 %). Not streaming (0 textures non-resident at every bad shot, `-NoTextureStreaming` changes nothing), not content (the same content renders clean the moment the capture waits). `evidence/lineup_cause.json` has the E0 / E1 / E2 / dose-response numbers; `lineup_cause_r17.py` reproduces them.
- **Capture protocol** (`Source/WebHomage/Characters/WHCharShowDirector.*`): `-WHSettleFrames=N -WHSettleSeconds=S` (+ `-WHStageShotRel` for shots that start mid-sequence, the lineup): at a stage shot's time freeze the stage clock, every skeletal animation, every `AWHCharLoopWalker` Tick and the camera; wait for 0 compiling assets / shaders and every visible texture resident; count N RENDERED frames with no camera / frustum-pose movement; screenshot. `-WHPreload` (movies), `-WHProbeFrames=N` (per-frame residency probe), `-WHSettleDump=1,2,4,...` (convergence curve), `-WHShotFrames=3,5,...` (plain screenshots at engine frame numbers). Bugs found by the probe and fixed: the player pawn (falls from the off-stage PlayerStart) and the lane walkers kept resetting the count; the timeout is checked before the reset branch.
- **Skin weights** (`tools/ue_char/suit8/hero_weights_r17.py`, from the interrupted session): the torso front's raw spine1 / spine2 weights jumped across the sternum strip |x| 0.03 - 0.05 (every sash edge / groove cord crossing it stepped sideways: Ash shelf 27 px, Verdant step 13.7 px); now a Gaussian 3D-neighbour average over the strip and a smooth head <-> neck blend over y 1.40 - 1.56 (the Cinder chin seam break). Long-edge jogs over the 8 chests 20 -> 13 (`line_step_r17.py`), Ash 4 -> 1, Plum 5 -> 0, Cinder / Glacier -> 0.
- `design.py`: the four cheek panel seams close in a rounded tip (circular cap over the last 6 / 4.8 mm) instead of a square cut (`face.cord_tip`, EXPECT_R17).
- `suits.json`: **Verdant re-blocked**: forest green + dark pine + copper accent (was brass yellow), no accent forearm / shin blocks (`arm.fore: deep`, `greave: none`), plain crown (the yellow racing stripes also hid the face seam from the tracker). The r16 pawn clip shows how close the old one came to the green-and-yellow wetsuit (frames in `evidence/measures/cuts/r16_director_cuts.jpg`).
- `build_characters.py`: pawn map shot 0 = 16 s, crowd shot 0 = 12 s: **the r16 pawn 'yaw snap' at 9.933 s and the r15 / r16 crowd cut at 7.483 s were DIRECTOR SHOT ENDS** (the director cut to the next shot; frames in `evidence/measures/cuts/r16_director_cuts.jpg`), not animation blends: not a P2 animation bug.
- Instruments (all CPU): `lineup_diff_r17.py`, `lineup_cause_r17.py`, `lineup_crops_r17.py`, `cut_check_r17.py`, `line_step_r17.py` (colour regions -> polygon edges -> run / connector / run jogs), `chin_crops_r17.py`, `seam_track_r16.py` (+ `step20`, `dev100_med31`), `cord_jog_r16.py` (+ `max_jump_under_arm_px`), `cord_jog_r17.py` (every cord, both sides; its crossing-step part is not calibrated), `post_r17.sh`, `spec_check_r17.py`, `fill_captures_r17.py`, `make_pairs_r17.py`, `combine_r17.sh`, `chain_r17.sh` / `hold_r17.sh`.

### What to know before touching anything
- **The lock**: cap 3, renders at background priority; with 2 other holders a 1080p fixed-step movie runs at 0.5 - 1.4 fps (the 756-frame orbit takes ~20 - 25 min, the crowd ~12 min). Plan one hold per movie group, keep every hold under the 40 min max hold (the lock SIGKILLs 10 s after its SIGTERM: stop your own run with `stop_ue.sh` first), and DO NOT run a CPU-heavy post script while a movie renders (it halves the frame rate).
- The settle protocol is for stills and lineups; movies cannot wait (fixed 1/60 s steps) and use `-WHPreload`.
- Hold inputs: `prep_hero_r17.sh` after any head / lens / shoulder / weights change; regenerate ALL maps after any `design.py` / `suits.json` change (`gen_suits.py --n 4096 --n-color 8192 --only <id> --out <scratch>` per suit in parallel + `hero_suit_r8.py --n 8192`, ~4 min on 8 cores), copy into `art/night1/characters/hero/{suits,tex}`, `test_regression.py` (EXPECT_R17).
- My instruments have limits (headers): the seam tracker follows the BRIGHT centroid of the cord, so a pale cord on a pale hood (Glacier) reads a 12 px shift across the crown / face luma transition that a 1.6x crop shows is not there; the yoke-cord tracker reads the cord's end cap at a sash border as a 5 px step (Ash); the Q6 pinch ratio uses colour thresholds tuned on brass (Verdant copper reads 0.27 with the cord intact); `line_step_r17.py` counts design corners where a panel boundary legitimately steps.
- LESSONS: (1) a corrupted render is first a capture-moment question: log what the engine is doing at the shot frame (assets compiling, textures resident) before touching content; (2) a settle gate needs a signature restricted to what the camera sees (the pawn fell for 30 frames off-stage); (3) `-shots t1,t2,...` are process-time seconds: at 4K the first frames take seconds, so several shots fire in one frame - use frame numbers; (4) the harness backgrounds a command after 10 s without output and `sleep N; cmd` chains: poll files; (5) the macOS bash is 3.2 (`${x^^}` is a fatal substitution error that aborts the whole command line).

### Next steps (priority order)
1. Read the round-17 critic verdict (`critic/round-17-CRITIC.md` once written) and fix its biggest gap.
2. The remaining sash / groove jogs (13 long-edge jogs of 4.5 - 10 px, `evidence/line_step_*.json`; the yoke-seam cord steps ~8 px where it crosses the sash's top-left corner (Tessera (1765, 1300)), the ring-net line wobble at the image-right armpit (Verdant (2539, 854)), Saffron's collar line (y ~ 700)): the sternum strip is done; next the trapezius / collar band (y > 1.38) and the pec <-> arm boundary.
3. The seam tracker (Glacier) and cord-jog tracker (Ash end cap) artefacts: centre the cord by its lit + shadow flank pair instead of the bright centroid, stop the yoke-cord track at the sash border.
4. Re-shoot the stage-hero run / chase / fight clips when the lock is quiet (not re-shot in r17: content unchanged except r17 weights; the r15 / r16 files are in the pack).
5. P3: the pawn's run cadence (WebTravAnimInstance) is theirs.

### Commands (round 17)
```
export P2_SCRATCH=/Users/midir/sm2-n1/_scratch/characters UE_WAIT_SKIP=1
unreal/WebHomage/Scripts/build_editor.sh                                                     # C++ (close your own editor first; 13 - 25 s)
bash tools/ue_char/suits/prep_hero_r17.sh                                                    # hero GLB (CPU, ~10 s), r17 weights
# maps: 7 x  python3 tools/ue_char/suits/gen_suits.py --n 4096 --n-color 8192 --only <id> --out $P2_SCRATCH/r17/tex_new/suits   +   python3 tools/ue_char/hero_suit_r8.py --n 8192 --out $P2_SCRATCH/r17/tex_new/hero   (parallel, ~4 min), then cp into art/night1/characters/hero/{suits,tex}
python3 tools/ue_char/suits/test_regression.py                                              # legacy r8 texel for texel + EXPECT_R17
python3 tools/ue_char/suits/ip_guard.py palette art/night1/characters/hero/suits OUT.json
# stills hold (build + both lineups + 56 stills, ~23 min on the cap-3 lock); movies in separate holds (pawn + orbit ~25 min, crowd ~9 min): the lock SIGKILLs a hold at 40 min
OUT=$P2_SCRATCH/r17/chainX; mkdir -p $OUT; cp tools/ue_char/suits/chain_r17.sh tools/ue_char/suits/.chain_r17x_run.sh; cp tools/ue_char/suits/hold_r17.sh tools/ue_char/suits/.hold_r17x_run.sh; touch $OUT/READY_R17
CHAIN_SNAPSHOT=.chain_r17x_run.sh STEPS="build lineup stills" nohup /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters --timeout 28800 -- bash tools/ue_char/suits/.hold_r17x_run.sh $OUT > $OUT/gpu_wrapper.log 2>&1 < /dev/null &
#   other steps: STEPS="pawn orbit" | "crowd" | "hero chase fight" | "lineupx" (E0 / E1 / E2 experiment) | "lineupx0" (frame dose-response); EV=10.0 default; one engine of yours at a time
bash tools/ue_char/suits/combine_r17.sh <stills hold>/run <pawn+orbit hold>/run <crowd hold>/run $P2_SCRATCH/r17/final
bash tools/ue_char/suits/post_r17.sh $P2_SCRATCH/r17/final $P2_SCRATCH/r17/final               # CPU ~25 min with a quiet machine: round-17 dir + evidence + crop sheets (NOT while a movie renders)
python3 tools/ue_char/suits/lineup_cause_r17.py --e0 <E0 dir> --e1 <E1 dir> --e2 <E2 dir> --x0 <lineupx0 dir> --ref docs/night1/characters/round-14/enemy_lineup_4k.jpg --out docs/night1/characters/round-17/evidence/lineup_cause.json --md docs/night1/characters/round-17/evidence/lineup_cause.md
python3 tools/ue_char/suits/spec_check_r17.py docs/night1/characters/round-17 > docs/night1/characters/round-17/SPEC_CHECK.md
python3 tools/ue_char/suits/fill_captures_r17.py docs/night1/characters/round-17                # fills the @@placeholders@@ of CAPTURES.md from the evidence
STILLS_4K=$P2_SCRATCH/r17/final/stills LINEUP34=1 python3 tools/ue_char/suits/make_pairs_r17.py docs/night1/characters/round-17 /Users/midir/sm2-n1/_scratch/critic-P2-r17/pairs.json
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py /Users/midir/sm2-n1/_scratch/critic-P2-r17/pack /Users/midir/sm2-n1/_scratch/critic-P2-r17/pairs.json
```
Stop an engine only with `/Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh "/Users/midir/sm2-n1/characters"`.

## Round 16 state (history)


Round 16 author: Opus 5.5 (2026-10-02 11:50 - 15:00 EDT). Everything is committed and pushed (`origin/night1/characters`, which carries the merge of `origin/Opus-5.5-Loop-Night-1` at 85683fa6); `/Content` is NOT committed. **No engine of mine is running; nothing of mine is queued on the lock.**
Round target (director, after the r15 critic [6,5,5,5,5]; owner approved the suits 11:31, r14 merged as the baseline): IQ >= 6 by closing the r15 critic's four 4K defects without a new one. No blind critic verdict yet: the pack is `/Users/midir/sm2-n1/_scratch/critic-P2-r16/pack` (56 pairs, key `pack.key.json` outside it, `round-16/critic_pairs.json`). Captures / holds / honest residual list: `round-16/CAPTURES.md`; every number: `round-16/SPEC_CHECK.md`.

| line | r15 -> r16 (real game, 4K PNG originals of hold 3, 14:04 - 14:32, 0 crashes) | verdict |
|---|---|---|
| (1) back bleed: accent clusters >= 20 px in the back torso (`back_bleed_r16.py`), all 8 backs committed at 4K | 1 - 8 per suit -> **0 on 8** | PASS |
| (2) yoke cord jog under the arm (`cord_jog_r16.py`, <= 4 px) | 8 - 36 px -> **0.5 - 0.9 px** | PASS 8 / 8 |
| (3) face seam dev100 (`seam_track_r16.py`, <= 10 px / 100 px) | Cinder 15.9, Glacier 13.8 -> **Cinder 10.9, Glacier 10.6**, 5 others 2.6 - 8.4, Verdant not tracked | **5 / 8 measured** (hold 2: 8 / 8 <= 8.8) |
| (4) net_end open fabric / Q6 / Ash notch | 83 -> **0** / 0.46 -> **0.54** / gone | PASS |
| kept: R1 8/8, G1 - G3 8/8, H4 2/8 -> 3/8, IP guard 49.3, OCR 1 reviewed noise hit, regression `EXPECT_R16`, swap 7/7, pawn 0 pops | | PASS |

### What changed (details in `round-16/CAPTURES.md`)
- **The stair-step jogs were skin weights**: five bones under the armpit + a plain top-4 truncation (spine1 dropped on one vertex, upperArm on its neighbour). `tools/ue_char/suit8/hero_weights_r16.py` merges spine-chain bones before truncating (`prep_hero_r16.sh`); CPU edge strain 2.6 -> 0.97. The CPU posed render that found it (`tools/ue_char/suits/dev_r16/posed_render.py`, `strain.py`: the prepped GLB skinned in its own idle clip, textured with a suit map, 4 s) reproduces in-game jogs: use it before any weight / prep change.
- `design.py`: front-only sash (+ its end finishing gated to the front), tone-on-tone back mark (`glyph.back`), seam-tone back wedge pipe, GEO limb net zones (`net.geo`: ring-cord planes + limb radius; ring cords + yoke side seam for sleeveless suits with a directional radius; an inseam cord). Maps regenerated, `EXPECT_R16`.
- C++ (`Source/WebHomage/Characters/WHCharShowDirector.*`): `WHShot.bHeadLock` (headfront camera in the head's midsagittal plane), `-WHStageShotQuit`, `-WHStageWaitTextures` (did not trigger in hold 3: `IsFullyStreamedIn` may not see the streaming - check before relying on it).

### What to know before touching anything
- **The lock was over-subscribed all afternoon (4 - 6 holders, "6/2 in use"), stills ran at 1.4 fps.** A process-time `-quit` then cuts the stills run (hold 1: 23 of 56) - the chain now quits after the last stage shot. A movie at ~1 fps takes ~12 min: the full chain no longer fits the 40 min max hold; split it (`STEPS=...`, `CHAIN_SNAPSHOT=` for a second snapshot name while one runs) and stop your own run with `stop_ue.sh` before the max hold (the lock SIGKILLs 10 s after its SIGTERM).
- At 1.4 fps the first suit's 8192 maps were still a low mip in hold 2's Tessera stills: LOOK at the first suit's chest crop of every hold.
- Hold inputs: `prep_hero_r16.sh` after any head / lens / shoulder / weights change; regenerate the maps after any `design.py` / `suits.json` change (`gen_suits.py --n 4096 --n-color 8192 --only <id>` in parallel + `hero_suit_r8.py --n 8192`, ~4 min), copy into `art/night1/characters/hero/{suits,tex}`, `test_regression.py`.
- The seam / cord / back instruments are mine and have limits (written in their headers): the seam tracker drops rows under accent pieces (vent) and can lose the seed on Verdant's striped crown; the cord tracker follows ONE cord (the yoke bottom seam) on the image-left side; the back mask is +-0.13 m, 6 px inside the silhouette, above the belt.

### Next steps (priority order)
1. Read the round-16 critic verdict (`critic/round-16-CRITIC.md` once written) and fix its biggest gap.
2. The face seam residual (Cinder / Glacier ~10.5 px, idle-phase dependent): either make the lower face follow the head bone (the jaw / chin neck weights in `hero_weights_*`) or measure the head plane from skinned seam vertices instead of the head bone.
3. Seen myself, not fixed: the thin dark net line under the arm on Saffron / Sage (the left upper-arm net reaches the torso side; a directional radius like the ring cords' would end it on the arm but raised the crease-zone dead ends 42 -> 81 at 2048: needs a cord there), the shallow V of the yoke seam at the sternum, the cheek seams reading as tracks, H4, CH2 chase framing, the enemy axis / crowd cut (paused scope). P3: the pawn cadence 4.13 Hz.
4. Re-shoot the stage-hero run / chase clips (Tessera's back changed; the r15 clips are in the pack) when the lock is less busy.

### Commands (round 16)
```
export P2_SCRATCH=/Users/midir/sm2-n1/_scratch/characters UE_WAIT_SKIP=1
bash tools/ue_char/suits/prep_hero_r16.sh                                                    # hero GLB (CPU, ~10 s), r16 weights
python3 tools/ue_char/suits/dev_r16/posed_render.py $P2_SCRATCH/ueimport/SK_Hero.glb verdant OUT.jpg -25 0.5     # CPU posed chest view (MAPS=, DIST=, W=, REST=1)
python3 tools/ue_char/suits/net_end_check_r15.py --n 2048                                   # dead net ends of the paint (CPU, 20 s at 2048)
OUT=$P2_SCRATCH/r16/chainN; mkdir -p $OUT; cp tools/ue_char/suits/chain_r16.sh tools/ue_char/suits/.chain_r16b_run.sh; cp tools/ue_char/suits/hold_r16.sh tools/ue_char/suits/.hold_r16b_run.sh; touch $OUT/READY_R16
CHAIN_SNAPSHOT=.chain_r16b_run.sh STEPS="build stills orbit" nohup /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters --timeout 28800 -- bash tools/ue_char/suits/.hold_r16b_run.sh $OUT > $OUT/gpu_wrapper.log 2>&1 < /dev/null &
bash tools/ue_char/suits/combine_r16.sh <hold with pawn/lineups>/run <hold with stills/orbit>/run $P2_SCRATCH/r16/final
bash tools/ue_char/suits/post_r16.sh $P2_SCRATCH/r16/final $P2_SCRATCH/r16/final               # CPU ~12 min: round-16 dir + evidence + crop sheets
python3 tools/ue_char/suits/spec_check_r16.py docs/night1/characters/round-16 > docs/night1/characters/round-16/SPEC_CHECK.md
STILLS_4K=$P2_SCRATCH/r16/final/stills LINEUP34=1 python3 tools/ue_char/suits/make_pairs_r16.py docs/night1/characters/round-16 /Users/midir/sm2-n1/_scratch/critic-P2-r16/pairs.json
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py /Users/midir/sm2-n1/_scratch/critic-P2-r16/pack /Users/midir/sm2-n1/_scratch/critic-P2-r16/pairs.json
```
Stop an engine only with `/Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh "/Users/midir/sm2-n1/characters"`.

## Round 15 state (history)

Round target (director, after the r14 critic [hero 6, anim 5, enemies 5, civilians 5, IQ 5; IP PASS]): merge P3 r22's ground blend and re-shoot the pawn movie; R1 the lens RIM >= 1 % of the head height behind the brow on all 8 4K headside stills; Q5 the accent pipe joins the Ash sash end; every net / groove line ends on a seam cord; no texture stretch under the brow; Q6 the Verdant armpit piping unpinched.
Gate: no axis below r14 [6,5,5,5,5], enemy pack / crowd unchanged, swatch sheet regenerated. **The OWNER must approve the suits before any merge: `docs/night1/characters/round-15/SWATCH_SHEET.jpg`.**
No blind critic verdict yet: the pack is `/Users/midir/sm2-n1/_scratch/critic-P2-r15/pack` (42 pairs, key `pack.key.json` outside it, `round-15/critic_pairs.json`). Resolution / hold / file table / honest problem list: `round-15/CAPTURES.md`; every number: `round-15/SPEC_CHECK.md`.

| line | r14 -> r15 (real game, 4K stills unless noted; one hold 2026-10-02 09:06 - 09:33, 0 crashes) | verdict |
|---|---|---|
| **R1** rim behind the brow (gate >= 1 % HH = 16 px) | all 8 proud / < 11 px behind -> **34 - 49 px = 2.3 - 3.3 %** | **PASS 8 / 8** |
| **Q5** Ash pipe joins the sash end (<= 5 px) | p90 gap 33 -> **2 px** | **PASS** |
| net / groove ends on cords (the paint itself) | open-fabric dead-end blobs 434 -> **83** (torso net 105 -> **1**); limbs not finished | torso PASS, limbs open |
| **Q7** brow trim sharpness | smeared (4096 colour, 0.7 - 1.0 mm / texel) -> sharp (8192 colour) by eye on every crop I read; edge-rise r15 / r14 0.59 - 0.73 on four suits, ~1.0 on three, **1.55 on Ash** (noisy instrument) | by eye PASS |
| **Q6** Verdant armpit cord | broken (13 gap columns, min 0) -> **0.46** (no gap, ends on the cap edge) | **FAIL by my own 0.5 gate** |
| pawn luma pops 0 - 1.5 s / `anim_weight` step | 1 pop (9.5 at 0.133 s) -> **0 pops** (max 5.2); `anim_weight` is the total weight (always 1) -> vacuous | PASS / vacuous |
| G1 / G2 / G3 (3 views) / H1 - H3 / H5 / H6 | 8 / 8 -> **8 / 8** (G1 7.8 - 8.0 %, G2 6.0 - 7.0 %) | PASS |
| H4 (my own: ONE closed raised rim >= 6 px on >= 90 % of the angles) | 2 / 8 -> **2 / 8** (Glacier, Sage) | unchanged FAIL |
| IP guard / seams / OCR / swap latency / regression | PASS (min palette distance 38.4 -> **49.6**), 0 OCR hits, 7 / 7 presses 33 ms, REGRESSION PASS | PASS |
| CH1 / CH6 / CH7 / CH2 | 0.542 - 0.544 / 3.54 Hz / 32.6 deg / **0.373 (gate 0.39, edge FAIL; the r08 clip reads 0.372)** | CH2 edge FAIL, not this round |
| enemy pack lineup / fight / crowd | unchanged (wall luma 139, fight script identical to r10) | unchanged |

### What changed (all committed; details in `round-15/CAPTURES.md`)
- **THE KEY LESSON: the head is POSED in the stills.** The idle clip pitches it back ~6 - 7 deg and the profile camera sits ~86 deg off the face axis. r14's mesh passed the rest-pose test (rim behind the brow by 1.4 % HH) and failed in the real frame (rim 18 px proud): the tilt costs ~34 px. A rest-pose CPU model with the fitted pose (`$P2_SCRATCH/r15/cpu_rim2.py`: persp_render of the head GLB with a pitch about (0, 1.60, -0.02) and yaw, `cpu_fit.py`: silhouette fit, rms 2.9 px;
  in `tools/ue_char/suits/dev_r15/`, README there) predicted -39 px (the real stills: 34 - 49 px). Use it before any head change: it costs 2 s, a hold costs ~2 h of queue.
- Head: brow 13.5 mm, socket -8.8, inner corner -7.5, lenses 43.5 mm from the midline, rim crest 2.6 mm (`hero_head_r14.py` PARAMS, `hero_lens_r14.py`; the paint's baked face tone reads the same PARAMS: regenerate the maps after any change).
- Maps: base colour 8192 px for all 8 suits (`gen_suits.py --n 4096 --n-color 8192`: colour 8192, normal / ORM 4096; Tessera 8192 x 3). `build_characters.py`: `P2_FIRST_EXTRA` (the chain sets 9): the first still waits 12 s so the 24 textures compile.
- `design.py`: the torso net is a yoke panel (hard edges, seam cords top / bottom / sides, no net on the shoulder top), the limb nets end on bands / rings / the hip-wrap piping, the Ash-style sash-end pipe lies on the end line (`sash.pipe_join`), the shoulder cap ends 7.5 cm from the arm axis on the torso side (`cap.r_in`: no cord over the armpit crease); `terminate` / `pipe_join` / `cap.r_in` switch back to r14 (`net_end_check_r15.py --r14`).
- Pawn: MY `pawn_run.json` spawned the pawn 25 cm in the air since r11 (the "pop at frame 7 - 8" was the landing + airRise clip, not P3's blend); it spawns on the ground now.
- Instruments: `rim_depth_r15.py`, `iq_check_r15.py` (Q5 / Q6 / Q7), `net_end_check_r15.py` (design-level dead ends: design.paint(..., dbg=...) hands out the net zones and the cord mask), `pawn_check_r15.py`, `chain_r15.sh`, `hold_r15.sh`, `post_r15.sh`, `spec_check_r15.py`, `make_pairs_r15.py`, `prep_hero_r15.sh`, `test_regression.py` EXPECT_R15.

### What to know before touching anything
- Hold inputs: the engine imports `$P2_SCRATCH/ueimport/SK_Hero.glb` AS IT STANDS (the chain's build does NOT run the 'prep' step): rerun `tools/ue_char/suits/prep_hero_r15.sh` after any change to the head / lens / shoulder / weights scripts, regenerate ALL maps after any `design.py` / `suits.json` / PARAMS change
  (`gen_suits.py --n 4096 --n-color 8192 --only <id> --out <scratch dir>` per suit in parallel, ~3 min each; `hero_suit_r8.py --n 8192 --out <scratch dir>` for Tessera; then copy into `art/night1/characters/hero/{suits,tex}` (git-ignored); the 8 maps take 4 min on 8 cores), rerun `test_regression.py` (update EXPECT_R15 deliberately).
  A queued hold is gated by `<chain dir>/READY_R15` (the launcher waits 4 min for it, then releases the slot); never edit the snapshot scripts `.chain_r15_run.sh` / `.hold_r15_run.sh` while a hold uses them. Files read by the build (maps, scripts, GLB) can still change while you wait in the queue, as long as they are consistent when your turn comes: I changed the sculpt twice that way.
- This round's queue wait was 6460 s (four other agents' holds, one of 100 min): queue EARLY, with READY in place, and keep working.
- The mesh stretch of the sculpt under the brow is 1.34 (p90) / 1.45 (max) in area root; the 8192 colour hides it. The pose / camera of the stills moves the hero ~100 - 150 px sideways between rounds: never test a fixed pixel box (the critic's Ash box 1490-1540 x 760-1150 contains no accent pixel in r15 because the pipe moved to x 1655 - 1672); the r15 instruments search for the feature.
- LESSONS: (1) the real posed frame, not the rest pose, decides silhouette tests; (2) a thin cord (1 mm = 4 px at 4800 px/m) is destroyed by a 3 x 3 opening: do not open masks of cords; (3) a rest-pose island seam in the browser mesh shifts cords by a few mm (yoke seam jog at the armpit); (4) `sleep N; cmd` chains are blocked by the harness: use `until`-loops;
  (5) look at the frames before the numbers (the Sage rim failure was a segmentation overreach on a pale hood: an opening + a 34 px ring fixed it, the overlay showed it at once).

### Next steps (priority order)
1. The owner's IP / suit sign-off on `round-15/SWATCH_SHEET.jpg` (the yoke seams across the chest and back are a design change on every suit); no merge before it. 2. Read the round-15 critic verdict (`critic/round-15-CRITIC.md` once written) and fix its biggest gap.
Candidates I saw myself: (a) Q6: `cap.r_in` 6.5 cm so the ring cord ends on the arm, or smooth the armpit crease in `hero_shoulder_r14.py`; the yoke bottom seam jog at the armpit (x ~1300, y ~1320 of the Verdant chest still); (b) the limb net ends (83 blobs: left upper arm 33, thighs 40): the skin-weight ramp and island seams, use `net_end_check_r15.py` + the per-layer overlays (`tools/ue_char/suits/dev_r15/dbg_layer.py`),
(c) H4: a dark non-metallic rim with a bright inner lip, (d) the cheek seams read as tear tracks from the eye frame (critic hero axis): end them on a jaw cord or move their start away from the lens, (e) Cinder's faceted shoulder (unchanged since r13), (f) CH2 chase framing 0.373: `Char_Hero` shot 6 camera ~5 % closer, (g) the enemy axis / the crowd cut at 7.48 s (paused P2 work).
3. P3 items: the pawn's run cadence (4.0 steps/s) belongs to the traversal brief (`round-15/SPEC_CHECK.md`, unchanged: clip switches now A_Hero_idle -> jog @0.90 s -> run @1.00 s).

### Commands (round 15)
```
export P2_SCRATCH=/Users/midir/sm2-n1/_scratch/characters UE_WAIT_SKIP=1
bash tools/ue_char/suits/prep_hero_r15.sh                                                    # hero GLB (CPU, ~10 s) + mesh profile numbers
# maps: 7 x  python3 tools/ue_char/suits/gen_suits.py --n 4096 --n-color 8192 --only <id> --out $P2_SCRATCH/r15/tex_new/suits   +   python3 tools/ue_char/hero_suit_r8.py --n 8192 --out $P2_SCRATCH/r15/tex_new/hero   (in parallel, nohup, ~4 min), then cp into art/night1/characters/hero/{suits,tex}
python3 tools/ue_char/suits/test_regression.py                                              # r8 legacy texel for texel + r15 default hashes
python3 tools/ue_char/suits/net_end_check_r15.py --n 2048 [--r14] [--png DIR]               # dead net ends of the paint (CPU, ~2 min)
OUT=$P2_SCRATCH/r15/chainN; mkdir -p $OUT; cp tools/ue_char/suits/chain_r15.sh tools/ue_char/suits/.chain_r15_run.sh; cp tools/ue_char/suits/hold_r15.sh tools/ue_char/suits/.hold_r15_run.sh; touch $OUT/READY_R15
nohup /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters --timeout 28800 -- bash tools/ue_char/suits/.hold_r15_run.sh $OUT > $OUT/gpu_wrapper.log 2>&1 < /dev/null &     # STEPS="build stills" for a short re-shoot (1612 s for everything)
bash tools/ue_char/suits/post_r15.sh $OUT/run $OUT/run                                       # CPU ~10 min: fills docs/night1/characters/round-15 + evidence (then re-run iq_check_r15.py if it fails on a moved feature)
python3 tools/ue_char/suits/spec_check_r15.py docs/night1/characters/round-15 > docs/night1/characters/round-15/SPEC_CHECK.md
STILLS_4K=$OUT/run/stills LINEUP34=1 python3 tools/ue_char/suits/make_pairs_r15.py docs/night1/characters/round-15 /Users/midir/sm2-n1/_scratch/critic-P2-r15/pairs.json
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py /Users/midir/sm2-n1/_scratch/critic-P2-r15/pack /Users/midir/sm2-n1/_scratch/critic-P2-r15/pairs.json
```
Stop an engine only with `/Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh "/Users/midir/sm2-n1/characters"`.

## Round 14 state (history)

Round target (director, after the r13 critic [hero 6, anim 5, enemies 5, civilians 5, IQ 5; IP PASS]): FINISH the shared mask sculpt on all 8 suits - G1 headside recess >= 1.5 % of the head height, G2 brow >= 1 % in front of the lens top (lens + rim seated in an eye socket under the brow ridge, rim one closed raised band >= 6 px, lens >= 1.6x r12),
G3 Tessera AND Cinder 4K front stills: a luma line through the cheek bones with >= 3 extrema, swing >= 20 - plus the two-round-old IQ repeats (pipe every sash end, no armpit stitch zigzag, no torn Sage trapezius groove, no faceted Cinder shoulders). Gate: no axis below r13 [6,5,5,5,5]; enemy pack / crowd unchanged; the pawn's 4.0 steps/s and the frame 7-8 start pop are P3's.
**The OWNER must approve the suits before any merge: `docs/night1/characters/round-14/SWATCH_SHEET.jpg` (8 suits, front + back + chest + head; the cheek panel seams are new on all of them).** No blind critic verdict yet: the pack is `/Users/midir/sm2-n1/_scratch/critic-P2-r14/pack` (38 pairs, key outside it, `round-14/critic_pairs.json`).
Everything is committed and pushed (`origin/night1/characters`); `/Content` is NOT committed. No engine of mine is running. Resolution / hold / file table / honest problem list: `round-14/CAPTURES.md`; every number: `round-14/SPEC_CHECK.md`.

| line | r13 -> r14 (real game, lossless 4K stills, one hold 2026-10-02 05:32 - 05:57, 0 crashes, lock `contaminated=true`) | verdict |
|---|---|---|
| G1 headside recess behind the brow -> nose-tip chord (gate 1.5 % of head height) | r13 Tessera 1.11 %, Cinder 1.44 % (my instrument on the r13 stills) -> **6.5 - 6.8 %** on all 8 (mesh: 6.05 %) | PASS 8 / 8 |
| G2 brow in front of the lens top (gate 1 %); with a 3.1 mm rim allowance | r13 -0.2 % (Tessera), -1.3 % (Cinder) -> **3.45 - 4.29 %**; with rim **2.08 - 2.93 %** | PASS 8 / 8 |
| G3 cheek luma lines (>= 3 extrema, prominence >= 20 luma, 13 lines per still) at 12 / 0 / 25 deg | r13 Tessera 0/13, Cinder 1/13 -> **13/13 on every suit and view** (min swing 111 - 182) | PASS 8 / 8, 3 views |
| H3 lens vs r12 (gate 1.6x) near / mean | 1.73 - 1.88x / 1.73 - 1.88x -> **1.73 - 1.83x / 1.65 - 1.81x** (Saffron 1.651 is the closest) | PASS 8 / 8 |
| H1 nose-bridge luma / H2 nose bump / H5 seam cord / H6 inside the outline | 6/8, 8.6 - 10.3 %, 49 - 148, 8/8 -> **8/8, 9.6 - 13.3 %, 82 - 171, 8/8** | PASS 8 / 8 |
| **H4 ONE closed raised rim >= 6 px on >= 90 % of the angles (my strict luma definition)** | 4 / 8 -> **2 / 8** (Glacier, Sage): the silver rims on the lifted hoods cross the mask's luma (Tessera 0.85 -> 0.35); the rim is a clear closed band by eye on all 8 | **FAIL 6 / 8 (own gate)** |
| Ash armpit stitches (critic box 1120-1200 x 1530-1600): stitch-dash blobs in the armpit box | 7 -> **0** (the wedge pipe + stitches end 3.5 cm below the crease) | fixed |
| Sage trapezius groove (head34): dark thin-line pixels in the critic's box | 10.3 % -> **0.07 %** (the net stops at the neck base) | fixed (one short crease remains) |
| Ash sash end (critic box 1410-1440 x 700-1050) | raw, no border / stitches -> a straight plane at |x| = 0.118 m with a DEEP border cord, 2 stitch rows and an accent pipe on every end of all 8 suits; stitch dashes beyond the end 1 -> 8; end line rms 7.2 -> 6.7 px (skinning bends the plane) | fixed by eye |
| Cinder shoulders faceted | one Phong refinement level + an unchanged silhouette contour measure (12.2 -> 10.9 vertices / 1000 px) | **NOT fixed / no visible change** |
| CH1 front framing 0.48 - 0.62 / CH6 side + chase 3.2 - 3.8 / CH7 lean >= 15 / CH2 chase 0.39 - 0.53 | 0.543 - 0.544 / 3.542, 3.542 Hz / 33.5 deg / 0.392 | PASS |
| keep: raised-piping cells share (r13 0.35 - 0.66) | Tessera 0.588 -> 0.485, the other seven -0.05 .. +0.07 | kept (Tessera lower) |
| IP guard P1 - P7 / seams / OCR / swap on the pixels | min palette distance 45.0 -> 38.4 no fails; seams worst 4.3 px; OCR 1 hit = Sage chest "SONY" noise (reviewed); 7 / 7 presses, 33 ms | PASS |
| enemy pack: lineup / fight / crowd | unchanged since r13 (wall luma 140, fight script identical to r10) | unchanged |

### What changed (all committed; details in `round-14/CAPTURES.md`)
- `tools/ue_char/suit8/hero_head_r14.py` (sculpt: brow shelf +11 mm, nasion notch, 22 mm nose, cheek planes +9 / hollows -5, mouth, chin; `PARAMS` dict, in-process `main(path, dump, params, widen)` for experiments), `tools/ue_char/hero_lens_r14.py` (`setup(a_half, cx, rim_h ...)`: 61 x 28 mm lenses at 40.5 mm, rim 3.1 mm),
  `hero_shoulder_r14.py` (one Phong-tessellation level on the shoulder / upper arm, +20k faces), `hero_weights_r14.py` (r12 armpit pass + trapezius smoothing; `--check`), `design.py` (`face` style: hood lift + baked face tone from the sculpt field + cheek panel seams; straight piped sash ends `sash.end_x` 0.118;
  torso net stops at the neck base; wedge pipe / stitch end below the armpit; lighter seam cord), `suits.json` (Cinder hood = body; per-suit `face.lift`), `build_characters.py` (r14 prep chain, `headfront` view, silver rim up to hood luma 0.36).
- Instruments: `head_check_r14.py` (G1 / G2 / G3 on the stills + r13's H1 - H6), `head_profile_r14.py` (the mesh silhouette, relief shading, perspective lens-to-outline clearance: the CPU design aid that told the sculpt where to go, 2 s per iteration), `iq_check_r14.py` (the four IQ defects), `prep_hero_r14.sh`, `chain_r14.sh`, `hold_r14.sh` (READY_R14 gate), `post_r14.sh`, `spec_check_r14.py`, `make_pairs_r14.py`; `test_regression.py` EXPECT_R14.
- CPU design loop that worked: edit the field -> `prep_hero_r14.sh` -> `head_profile_r14.py --png --relief --h6` (seconds) -> a softrender head with the real maps (`_scratch/characters/r14/cpu/head_render.py`, not committed). A CPU render over-predicts luma extrema (the r13 baseline gave 3 where the engine gave 1 - 2): trust relative changes only.

### What to know before touching anything
- Hold inputs: the engine imports `$P2_SCRATCH/ueimport/SK_Hero.glb` AS IT STANDS (the chain's build does NOT run build_characters 'prep'): rerun `tools/ue_char/suits/prep_hero_r14.sh` after any change to the head / lens / shoulder / weights scripts, regenerate the maps (`hero_suit_r8.py` for Tessera 8192, `gen_suits.py` for the others 4096; write them to a scratch dir and copy over) after any `design.py` / `suits.json` change, rerun `test_regression.py` (update EXPECT_R14 deliberately).
  A queued hold is gated by `<chain dir>/READY_R14` (the launcher waits 4 min for it, then releases); never edit the snapshot scripts `.chain_r14_run.sh` / `.hold_r14_run.sh` while a hold uses them.
- The sculpt is `z`-only displacement windowed by n_z; the paint (design.py, evaluated on the ORIGINAL browser mesh at each texel's rest-pose x, y) uses the same field for the baked tone, so changing `field_mm` changes the tone too (regenerate the maps).
- The lens + rim sit on the sculpted surface through r8's height field (`hero_lens_r8.head_height_field`, a 2 mm envelope): a deeper socket lowers the rim automatically; the nose-end rim vertex (x ~ 8 mm, y 1.664) is the front-most one (T2b 1.4 % HH of margin).
- LESSONS: (1) the G3 luma line cannot be won by relief alone on a dark hood (the stage key's large-scale gradient dominates and the sun only gives 10 - 20 luma of relief) - lighten the albedo AND put contrast in the albedo (cords, tone); (2) a polished silver rim is a bad rim on a mid-luma hood: its reflections sit at the hood's luma; (3) the first line of defence against wasted holds is the CPU instruments + a full prep dry run (`prep_hero_r14.sh` and the regression test), then queue EARLY with the READY gate and keep working while the lock is busy (4 other agents' holds = 55 min);
  (4) `sleep N; cmd` chains are blocked by the harness: use `until`-loops with a timeout; (5) grep every `replace` for its occurrence count; LOOK at the frames before the numbers.

### Next steps (priority order)
1. The owner's IP / suit sign-off on `round-14/SWATCH_SHEET.jpg` (cheek panel seams on every suit; Plum apricot as in r13); no merge before it. 2. Read the round-14 critic verdict (`critic/round-14-CRITIC.md` once written) and fix its biggest gap.
Candidates I saw myself: (a) H4: a rim that contrasts at every angle (try a dark non-metallic rim with a bright inner lip, or an accent-lit rim edge) - needs one hold (`STEPS="build stills"`, ~7 min), (b) Cinder's faceted shoulder: find the real cause (the DEEP panel edge is cut by skin weights; look at the panel boundary and the weight ramp at the deltoid before refining more),
(c) the remaining creases (left trapezius of Sage, Glacier / Ash armpit: the arm panel folds under the arm; `hero_weights_r14.py --check` counts them), (d) the seams' look (the outer cheek seam reads as a track in profile), (e) the enemy axis (r13 list: closed fingers on the grips, >= 1.5 m spacing and turn-taking in the fight, hit FX; P2's paused enemy work), (f) the crowd cut at 7.48 s.
3. P3 items (the playable pawn's cadence 4.0 steps/s and the frame 7 - 8 start pop) belong to the traversal brief (numbers in `round-14/SPEC_CHECK.md`, unchanged: clip switches A_Hero_idle -> A_Hero_walk @0.817 s -> jog @0.867 s -> run @0.983 s).

### Commands (round 14)
```
export P2_SCRATCH=/Users/midir/sm2-n1/_scratch/characters UE_WAIT_SKIP=1
bash tools/ue_char/suits/prep_hero_r14.sh                                                    # hero GLB (CPU, ~8 s) + mesh profile numbers
python3 tools/ue_char/hero_suit_r8.py --out $P2_SCRATCH/r14/tex_new/hero && python3 tools/ue_char/suits/gen_suits.py --out $P2_SCRATCH/r14/tex_new/suits   # maps (CPU ~6 min, parallel), then copy into art/night1/characters/hero/{tex,suits} (git-ignored)
python3 tools/ue_char/suits/test_regression.py                                              # r8 legacy texel for texel + r14 default hashes
OUT=$P2_SCRATCH/r14/chainN; mkdir -p $OUT; cp tools/ue_char/suits/chain_r14.sh tools/ue_char/suits/.chain_r14_run.sh; cp tools/ue_char/suits/hold_r14.sh tools/ue_char/suits/.hold_r14_run.sh; touch $OUT/READY_R14
nohup /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters --timeout 28800 -- bash tools/ue_char/suits/.hold_r14_run.sh $OUT > $OUT/gpu_wrapper.log 2>&1 < /dev/null &     # STEPS="build stills" for a short re-shoot
bash tools/ue_char/suits/post_r14.sh $OUT/run $OUT/run                                       # CPU ~10 min: fills docs/night1/characters/round-14 + evidence
python3 tools/ue_char/suits/spec_check_r14.py docs/night1/characters/round-14 > docs/night1/characters/round-14/SPEC_CHECK.md
STILLS_4K=$OUT/run/stills LINEUP34=1 python3 tools/ue_char/suits/make_pairs_r14.py docs/night1/characters/round-14 /Users/midir/sm2-n1/_scratch/critic-P2-r14/pairs.json
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py /Users/midir/sm2-n1/_scratch/critic-P2-r14/pack /Users/midir/sm2-n1/_scratch/critic-P2-r14/pairs.json
```
Stop an engine only with `/Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh "/Users/midir/sm2-n1/characters"`.

## Round 13 and earlier (history)

### Round 13 state (history)

Round target (director, after the r12 critic [hero 5, anim 5, enemies 4, civilians 5, IQ 5; IP PASS]): sculpt the shared mask head; lenses >= 1.6x r12 with one closed raised rim each; the black face seam as raised piping; merge gate: enemy pack at the r10 content, keep r12's passing lines,
Verdant / Saffron / Plum without IP watch items. **The OWNER must approve the suits before any merge: `docs/night1/characters/round-13/SWATCH_SHEET.jpg` (8 suits, front + back + chest + head).** No blind critic verdict yet; the pack is `/Users/midir/sm2-n1/_scratch/critic-P2-r13/pack` (28 pairs, key outside it).
Details, resolution, file table, what the first hold got wrong, known problems: `round-13/CAPTURES.md`; every number: `round-13/SPEC_CHECK.md`.

| line | r12 -> r13 (real game, 4K stills unless noted; second hold 2026-10-02 03:21 - 03:44) | verdict |
|---|---|---|
| sculpted head (brow, nose, cheek bones, mouth, chin, profile) on all 8 suits | egg / sock -> sculpted; nose bump **8.6 - 10.3 %** of the head height (gate 2 %) | PASS 8 / 8 (H2) |
| lens width vs r12 (head-width ratio, near lens in the r12 framing / mean in the 12 deg still) | 38.5 mm -> 63 mm model; **1.88 - 1.95x** near, **1.73 - 1.88x** mean (gate 1.6x) | PASS 8 / 8 (H3) |
| face seam: 12 px black ink -> raised cord | lit / shadow pair **49 - 148** luma (gate 20), no black run | PASS 8 / 8 (H5) |
| nose-bridge luma profile (>= 3 extrema, swing >= 20) | 6 of 8 suits | PASS 6 / 8 (H1: Cinder near-black hood, Saffron cord-dominated profile fail) |
| ONE closed raised dark rim >= 6 px, closed on >= 90 % of the angles | rim 11 - 43 px wide; closed: Plum, Cinder, Glacier, Sage pass, Tessera 0.85, Verdant 0.85 / 0.73, Ash 0.60 / 0.52, Saffron 0.75 / 0.56 | **4 / 8** (H4); visible by eye on all 8 |
| lenses inside the outline | the far lens lies against it (>= 3 px) | PASS 8 / 8 (H6, weak) |
| suits passing every gate | | **3 of 8** (Plum, Glacier, Sage) |
| raised piping (64 px cells with a lit / shadow pair >= 20 luma), chest stills, 8 suits | r12 0.34 - 0.61 -> **r13 0.35 - 0.66** | kept |
| CH1 front framing 0.48 - 0.62 | 0.541 - 0.545 -> **0.542 - 0.544** | PASS |
| CH6 run cadence (side / chase) 3.2 - 3.8 | 3.542 / 3.542 Hz -> **3.542 / 3.542** | PASS |
| CH7 lean >= 15 deg | 20.6 -> **33.0 deg** (r8 clip 25.5) | PASS |
| CH2 chase framing 0.39 - 0.53 | 0.389 (edge FAIL) -> **0.391** | PASS |
| IP guard P1 - P7 (Plum recoloured apricot) | min palette distance 52.3 -> **45.0**, no fails; OCR 0 hits; seams worst 4.3 px | PASS |
| swap on the pixels | 7 / 7 presses, 33 ms | PASS |
| enemy pack: lineup | 6 enemies, wall luma 208 -> **7 enemies, wall 140**; fight / crowd / hero maps at the r12 exposure (same pixels), fight script + choreography + weapon fit identical to r10 | restored / improved |
| Verdant chevron jog at the critic's columns | 1.24 -> **14.4 px**: pose-dependent measure, the ~20 px step at the upper edge near the armpit is visible in BOTH r12 and r13 | NOT fixed |

### What to know before touching anything
- The tools: `tools/ue_char/suit8/hero_head_r13.py` (head sculpt: `field_mm` amplitudes, `ZONE`, 6 mm widening), `tools/ue_char/hero_lens_r13.py` (`A_HALF` 31.5 / `B_HALF` 13.8 / `CENTER_X` / `BEZEL`), `design.py` (`seam`, `rough_hood`, hood colour), `build_characters.py` 'skins' (per-suit rim: silver on near-black hoods, graphite on the rest), C++ `WHHeroSuit.{h,cpp}` (`FrameMaterial`, built with `Scripts/build_editor.sh`, 13 s).
  Prep order on CPU: `prep_glbs.py` -> `hero_head_r13.py` -> `hero_lens_r13.py` -> `hero_weights_r12.py` (build_characters 'prep' does the same). A GLB change needs no hold to build, only to be seen.
- The lenses are very wide for the face (the mask wraps: 60 deg off the view axis at 70 mm from the midline): 63 mm is the compromise (66 / 72 mm touched or left the outline; 6 mm of temple widening was added). The far lens of a 25 deg view is foreshortened (1.05 - 1.56x r12).
- `head_check_r13.py` definitions are mine (the critic is blind and visual): H4 uses luma only, so a reflective rim that crosses the mask's luma at some angles counts as open although it reads; the nose profile H1 runs along the midline = on the seam cord (a flank profile is in `head_check.json` as info only).
- The first hold's mistakes (all fixed, all in CAPTURES.md): a `replace` that hit two identical lines (the lineup's -0.6 EV also darkened `new_stage()`), the first still taken while the 8192 px maps streamed in (3.7 s now), `-quit` counted from process start (+40 s now), one silver rim for every suit.
  LESSONS: grep every `replace` for its occurrence count; LOOK at every clip frame and still before the numbers; the stage clock starts ~35 s after the process (`-quit` is process time); never append to a running script except at its end.
- The GPU lock: both holds waited 48 min and 127 min behind other agents' hours-long holds (`--timeout 28800`); the chain is ONE hold of ~1410 s (limit 2400 s). Hold 2 was started by a launcher (`reshoot_r13.sh`) that needs a `READY_V2` marker, so a premature grant could not waste it.

### Next steps (priority order)
1. The owner's IP / suit sign-off on `round-13/SWATCH_SHEET.jpg` (Plum is apricot now); no merge before it. 2. Read the round-13 critic verdict (`critic/round-13-CRITIC.md` once written) and fix its biggest gap. Candidates I saw myself: (a) H4 / dark rim: a per-suit rim colour from the suit's own palette
(a dark tint of the accent) instead of two neutral metals, or a thin lit edge; (b) Cinder / Saffron relief (a lighter hood for Cinder: `hood: body`), (c) the Verdant chevron upper-edge step and the Ash armpit smear (the arm skin weights near the armpit), the unpiped sash ends (design.py: a cord along `zone_s`'s ends),
(d) the lens size against the face (a wider cranium / flatter cheek plane would let a 63 mm lens sit further from the outline), (e) the enemy axis: the lineup stands in the hero idle (open hands), a fist-closed idle for the armed ones would grip the weapons visibly; fight spacing is r10's choreography (the r12 critic asked for >= 1.5 m spacing and turn-taking: P2's paused enemy work).
3. P3 items (cadence 4.0 steps/s of the playable pawn, hard clip switches) belong to the traversal brief (numbers in `round-13/SPEC_CHECK.md`).

### Commands (round 13)
```
export P2_SCRATCH=/Users/midir/sm2-n1/_scratch/characters UE_WAIT_SKIP=1
G=$P2_SCRATCH/ueimport
python3 tools/ue_char/prep_glbs.py && python3 tools/ue_char/suit8/hero_head_r13.py $G/SK_Hero.glb && python3 tools/ue_char/hero_lens_r13.py $G/SK_Hero.glb && python3 tools/ue_char/suit8/hero_weights_r12.py $G/SK_Hero.glb   # hero GLB (CPU, seconds)
python3 tools/ue_char/hero_suit_r8.py && python3 tools/ue_char/suits/gen_suits.py                       # Tessera 8192 (~2.5 min) + the 7 others at 4096 (~5 min), in parallel: art/.../suits (git-ignored)
python3 tools/ue_char/suits/test_regression.py                                                           # r8 legacy texel for texel + the r13 default hashes
unreal/WebHomage/Scripts/build_editor.sh                                                                 # C++ (only if WHHeroSuit changes; close your own editor first)
OUT=$P2_SCRATCH/r13/chainN; mkdir -p $OUT; cp tools/ue_char/suits/chain_r13.sh tools/ue_char/suits/.chain_r13_run.sh      # run a SNAPSHOT, never edit a running script
EV=10.0 STEPS="build stills lineup pawn orbit hero chase fight crowd" nohup /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters --timeout 28800 -- bash tools/ue_char/suits/.chain_r13_run.sh $OUT > $OUT/gpu_wrapper.log 2>&1 < /dev/null &
bash tools/ue_char/suits/post_r13.sh $OUT $OUT                                                           # CPU ~8 min: fills docs/night1/characters/round-13 + evidence + head_check.json
python3 tools/ue_char/suits/spec_check_r13.py docs/night1/characters/round-13 > docs/night1/characters/round-13/SPEC_CHECK.md
TESSERA_FRONT_OK=1 LINEUP34=1 STILLS_4K=$OUT/stills python3 tools/ue_char/suits/make_pairs_r13.py docs/night1/characters/round-13 /Users/midir/sm2-n1/_scratch/critic-P2-r13/pairs.json
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py /Users/midir/sm2-n1/_scratch/critic-P2-r13/pack /Users/midir/sm2-n1/_scratch/critic-P2-r13/pairs.json
```
Stop an engine only with `/Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh "/Users/midir/sm2-n1/characters"`.

## Round 12 and earlier (history)

## STATE AT THE END OF ROUND 12 (read this first)

Round 12 author: Opus 5.5 (2026-10-01 17:40 - 23:30). Everything committed and pushed on `night1/characters`; `/Content` is NOT committed (rebuilt by the scripts).
Round target (critic r11, single biggest gap): raised piping + net / panel lines UNDER the sash and chevron; same round: no faceted patches / weave flip / armpit stair-step, the Verdant jog
<= 2 px, Verdant + Saffron re-blocked, CH1-framed fronts, every r8 axis re-proven (stage-hero run / chase, enemy lineup 4K, fight clip, crowd clip, swap movie).
Numbers: `round-12/SPEC_CHECK.md`; captures and how: `round-12/CAPTURES.md`; the fold diagnosis: `round-12/FOLD.md`. Critic pack: `/Users/midir/sm2-n1/_scratch/critic-P2-r12/pack`
(21 pairs, key in `pack.key.json` outside it; `pairs.json` also as `round-12/critic_pairs.json`). No critic verdict yet.

| line | r11 -> r12 (real game, 4K chest stills unless noted) | verdict |
|---|---|---|
| net / panel lines through the sash: critic probe Tessera (1412, 1240) | luma 85 vs panel 109 -> **110 vs 107** | fixed |
| sash / chevron: longest dark run inside the panel (<= 10 px) | Tessera 20 -> **11**, Ash 70 -> **3**, Cinder 108 -> **10**, Saffron 98 -> **6**, Verdant 9 -> 8, Plum 4 -> 9 (Glacier / Sage: no sash panel found) | Tessera 1 px over |
| raised piping: 64 px line cells with a lit / shadow pair >= 20 luma | Tessera 32 -> **59 %**, Ash 32 -> 58, Glacier 35 -> 58, Sage 32 -> 62, Plum 53 -> 60, Cinder 51 -> 59, Saffron 40 -> 52, **Verdant 41 -> 35** | NOT "every line": about 6 in 10; Verdant's horizontal rib rings read flat |
| Verdant chevron jog at the critic's columns (x 1320-1400) | **68.6 px -> 1.2 px** (whole tracked edge 4.1 px at (1528, 1821), stitch / twill noise) | fixed at the jog |
| armpit fold (CPU skinning, folded faces in the region) | run 62 -> 18, sprint 85 -> 37, fight idle 34 -> 7, idle 4 -> 2 | `FOLD.md` |
| normal map vs mesh tangent basis per UV island | all large islands cos >= 0.98, no island flipped (Tessera / Verdant / Ash) | PASS |
| CH1 front framing 0.48 - 0.62 | 0.77 -> **0.541 - 0.545** | PASS |
| CH6 / CH7 / CH2 stage hero (r8 instruments, r8 clips measured alongside) | side head bob 3.542 Hz (r8 3.542), chase 3.542 Hz, lean 20.6 deg (r8 25.5), chase height 0.389 (r8 0.372; target 0.39) | PASS / PASS / CH2 at the edge |
| IP guard palette, seams, OCR, regression | min palette distance 52.3, worst seam run 4.6 px, 0 OCR hits, r8 legacy + r12 default md5 PASS | PASS |
| swap on the pixels | 7 / 7 T presses, 33 ms | PASS |

**Cross-piece numbers for the orchestrator -> traversal brief (P3 owns `Traversal/`, P2 did not edit it):** the playable pawn (`AWebTravCharacter` + `WebTravAnimInstance`) runs at
**4.0 steps/s** (head-top bob period 15.0 frames, FFT 4.13 Hz; target 3.2 - 3.8), and its start switches `A_Hero_idle -> A_Hero_walk @0.817 s -> A_Hero_jog @0.867 s -> A_Hero_run @0.983 s`
with blend weight 1.000 on every switch (telemetry `round-12/evidence/pawn_telemetry.csv`, `loco_r12.py tpop`); the 10-number pose signature spreads its change over 28 frames, so the visible
pop the critic saw (0.733 -> 0.750 s of the trimmed r11 clip) is the hard clip switch at 0.817 s untrimmed.

### What changed in round 12 (all committed)
- `tools/ue_char/suit8/hero_weights_r12.py` (run by `build_characters.py` 'prep' after `hero_lens_r8.py`): `strip_arm` (no shoulder / upperArm weight on the chest side below the armpit, ramp
  y 1.25 -> 1.36 m) + Gaussian weight smoothing in the 1650-vertex torso-side region. `--check` prints / writes the fold counts. THE cause of the jog / weave flip / facets (`FOLD.md`).
- `tools/ue_char/suit8/design.py`: style `relief` (default `piping`: cords pipe 1.8 mm, net 1.3, ring 1.8, glyph 1.4, sash plateau 0.6, border 1.6, rough 0.34 / 0.40, cavity AO 0.35,
  `net_tone` 0.38 = mid-tone net cords); every line laid after the sash is masked UNDER it (`sash_cov`); crisp sash / chevron ends. `relief.kind = 'r8'` reproduces round 08 exactly.
- `tools/ue_char/hero_suit_r8.py`: `--legacy-r8`, cavity AO pass, smoothed metres-per-texel, normal sigma 0.6 for relief maps; `gen_suits.py` the same.
- `M_Char_Suit` (`build_characters.py`): the weave is laid out from the PRE-SKINNED local position (triplanar whiteout, rotated onto the skinned normal, World -> Tangent; static switch
  `WeaveFromPosition`, default on). Compiles and renders in -game (weave continuous across the armpit seam in the 4K chest stills).
- Stage: fills 0.8 -> 0.5 (`skin_fill`), front / back views 7.85 m (CH1).
- `suits.json`: Verdant deep #4b4a22 olive-bronze, upper arm body, glyph `gate` (no black raglans, no chest ring); Saffron deep / crown #2f3a36 slate, upper arm body, `sleeves: false`
  (no tan / brown raglan pair).
- Tools: `tangent_check.py`, `relief_check_r12.py relief|sash|jog`, `loco_r12.py ch1|bob|pop|tpop`, `chain_r12.sh` (one hold: build + captures), `post_r12.sh`, `spec_check_r12.py`,
  `make_pairs_r12.py`; `test_regression.py` checks the r8 legacy AND the r12 default hashes (update EXPECT_R12 with any deliberate design change).

#### Round-11 next steps (history; round 12's list is at the top)
1. Read the round-12 critic verdict (`critic/round-12-CRITIC.md` once written) and fix its biggest gap. Known open items: (a) relief is ~60 % of line cells, not every line: Verdant's
   horizontal rib rings and lines parallel to the key light read flat (raise `relief.net` for `rib`, or give the stage key a side component); (b) Tessera sash dark run 11 px at (1349, 1164)
   (the remains of the armpit crease at the sash's upper-left corner); (c) CH2 chase framing 0.389 (target 0.39-0.53: camera 5 % closer in `maps5`); (d) head sculpt (egg head, shared
   decal grille) is round 13 per the brief.
2. The owner's IP sign-off (PLAN-firstpass section 5): show `round-12/SWATCH_SHEET.jpg` (Verdant and Saffron re-blocked); no merge before it.
3. P3 items above (cadence 4.0 steps/s, hard clip switches) belong to the traversal brief.

### Lessons of this round
- NEVER edit a shell script while bash runs it (bash reads it incrementally: the r12 first chain re-ran a step and died on a syntax error). `chain_r12.sh` is run from a snapshot copy.
- The GPU lock's default capture wait timeout is 3600 s: with 6+ waiters pass `gpu_slot.sh capture --timeout 14400`. An auto-PAUSE (20:43 - 22:38 tonight) blocks every launch; wait.
- `run_game.sh` has an uncommitted change from another session (18:12, frame cap for non-perf captures): not P2's, left alone.

## Round 11 (history)

Round 11 is DONE except the blind critic's verdict: all acceptance numbers are in `round-11/SPEC_CHECK.md`, what was captured (and how, at which resolution) in `round-11/CAPTURES.md`, the suits in `round-11/SUITS.md`, the owner's swatch sheet is `round-11/SWATCH_SHEET.jpg`.

| acceptance line (PLAN-firstpass section 4) | result |
|---|---|
| >= 6 ORIGINAL suits from the parameterised Tessera generator | **8** (tessera, verdant, plum, cinder, glacier, ash, saffron, sage); IP guard P1 - P7 pass, min palette distance 47.1, atlases OCR 0 hits |
| in-game swap: key cycle + `wh.Suit`, persisted in WHSettings, <= 0.5 s | T / Shift+T, D-pad Up, console, settings-menu row; real-time 4K swaps 64 - 68 ms (3 frames), 7 of 7 injected T presses visible 2 frames (33 ms) later on the movie pixels; the pawn run ended in verdant, the relaunch and the menu both read verdant from `GameUserSettings.ini` |
| swatch sheet for the owner | `round-11/SWATCH_SHEET.jpg` (front + back + chest of every suit) |
| no seam > 40 px, 4K stills | texture-level seam runs <= 4.6 px; a small stair-step at the left-chest sash end is visible in the 4K chest close-ups (UV island boundary, see CAPTURES) |
| critic pack | `/Users/midir/sm2-n1/_scratch/critic-P2-r11/pack` (17 pairs: 4 full-body, 4 back, 3 chest, 2 head, swatch sheet, swap clip, orbit clip, round-08 Tessera vs round-11 Tessera; key in `pack.key.json` outside it), built from `pairs.json` by `make_pairs_r11.py` + `abpack.py`; no critic verdict yet: IQ >= 6 is the critic's line |

What happened in the resume (2026-10-01 14:40 - 16:00): the owner's GTA V reservation blocked the lock twice (by design, never worked around); the manual-exposure stills of the interrupted chain were BLACK (AEM_Manual = camera EV100 9.9 minus the bias, stage sun 8 lux): measured bias +9 -> floor luma 121, +10 -> 172 (auto exposure's 170). The stage default is now **+10.0** (`build_characters.py`, `skin_ev`) and every run passes `-WHExposure=10.0` (`evidence/exposure_calib.txt`).
`tools/ue_char/suits/chain_r11_final2.sh` is the ONE hold that produces all the evidence (build skins + skinsmap -> [EV calibration] -> 4K stills -> pawn swap movie -> persistence relaunch -> settings-menu shot -> orbit movie; stops after 2 engine crashes; 600 s of lock hold). `tools/ue_char/suits/post_r11.sh <chain dir>` then fills `round-11/` (stills, sheet, clips trimmed, evidence, swap analysis, OCR, `SPEC_CHECK.md`).
The orbit movie of the main chain showed the default pawn of `Char_Skins` as a small dark post on the horizon (its off-stage PlayerStart was 60 m away). **Fixed and re-shot (second hold, 2026-10-01 17:09 - 17:13, 223 s, 0 crashes, instances of mine = 1)**: the start is now 1.8 km away (`build_characters.py`), `STEPS="build orbit" EV=10.0 chain_r11_final2.sh .../r11/chain5`, and the COMMITTED `round-11/orbit_all_suits.mp4` is that re-shot movie (checked on 23 frames by hand, before/after crop in `evidence/orbit_post_removed_before_after.png`; details in `CAPTURES.md` "Orbit note"). The owner's GTA V reservation (15:41 pause) was lifted at 17:05; the lock then granted the hold after a 150 s queue behind other agents.
Round-11 resume checklist (all done): orbit re-shot, `post_r11.sh` re-run (swatch sheet, OCR 1 reviewed hit, swap analysis: unchanged numbers, `SPEC_CHECK.md` regenerated identical), critic pack rebuilt from the final files (17 pairs, `/Users/midir/sm2-n1/_scratch/critic-P2-r11/pack`, key outside it in `pack.key.json`), everything committed and pushed.

### What exists (all verified in the real game this round)

| piece | file |
|---|---|
| generator: Tessera's `paint(..., style)` (DEFAULT_STYLE = Tessera, bit-identical to round 08 at 1024 px: max diff 0, `test_regression.py`) | `tools/ue_char/suit8/design.py` |
| suit list, 8 original styles | `tools/ue_char/suits/suits.json` |
| maps per suit (4096 px, ~45 s each; Tessera 8192 from `hero_suit_r8.py`) | `python3 tools/ue_char/suits/gen_suits.py [--only id] [--hero] [--n 4096]` -> `art/night1/characters/hero/suits/<id>_{basecolor,normal,orm}.png` (git-ignored) |
| IP guard: colour-blocking rules P1-P5, structural + palette uniqueness P6, glyph whitelist P7; OCR of atlases / stills | `tools/ue_char/suits/ip_guard.py palette|ocr` (numbers in `round-11/SPEC_CHECK.md`) |
| UV seam check (spec CH18) | `tools/ue_char/eval/suit_seams.py` |
| CPU design-aid renders / swatch | `tools/ue_char/suits/swatch_cpu.py` (not evidence); engine sheet: `swatch_sheet.py` |
| engine content steps `skins` (textures NeverStream, `MI_HeroSuit_<id>`, `MI_HeroLens_<id>`, data asset `/Game/Characters/Hero/Suits/DA_HeroSuits`) and `skinsmap` (`Char_Skins`, `Char_SkinsPlay`) | `unreal/WebHomage/Scripts/build_characters.py` (end of file) |
| the swap | `Source/WebHomage/Characters/WHHeroSuit.{h,cpp}`: `UWHHeroSuitSubsystem` (UTickableWorldSubsystem): T / Shift+T, gamepad D-pad Up (LB + D-pad Up = back), console `wh.Suit <n|id>` / `wh.SuitNext` / `wh.SuitPrev`, applies to the player pawn's `SpiderSuit` slot (+ `Lens`) and to every other mesh wearing a hero suit |
| persistence | `Core/WHSettings.{h,cpp}`: `SuitIndex`, `SuitId`, `LoadSuit()`, `SaveSuit()`; keys `HeroSuit`, `HeroSuitId` in `GameUserSettings.ini [WebHomage.Settings]`; the in-play swap saves at once; "Reset defaults" keeps the suit |
| settings menu row "Suit" (section HERO) | `Core/WHSettingsMenu.cpp` |
| capture director: `FWHShot.Suit`, `FWHShot.bTargetPlayer`, `-WHExposure=<EV bias>` | `Characters/WHCharShowDirector.*` |
| automation flags | `-WHSuit=<n|id>`, `-WHSuitScript=t:n,...`, `-WHSuitKeyScript=t,...` (real T key through the player controller; a scripted run ignores the GLOBAL macOS Shift state, which leaked in from the owner's other game), `-WHSuitPersist` (see the header of `WHHeroSuit.h`) |
| swap latency on pixels | `tools/ue_char/suits/analyze_swap.py` (colour histogram of the hero's pixels; matches each logged key injection with the first swap step) |
| exposure calibration helper | `tools/ue_char/suits/ev_calib.py` (bare-floor luma, secant search for 170) |

The playable pawn (`AWebTravCharacter`, P3) is NOT edited: its `SetupHeroMesh` still loads `MI_Hero_Suit`; the subsystem re-applies the chosen suit to the player's mesh every frame and scans the world every 0.5 s.
Integration note for the integrator: the module needs no new Build.cs dependency (the suit list is a data asset, not an asset-registry scan). `Core/WHSettingsMenu.cpp` got one section (a `ChoiceRow`); `Core/WHSettings.*` got the two fields + two methods.

## Next steps (priority order)

1. Read the critic verdict for round 11 (`critic/round-11-CRITIC.md` once written) and fix its single biggest gap. Candidates I saw myself: (a) the stair-step at the left-chest sash end of every suit (a UV island boundary of the shared atlas, visible in the 4K chest close-ups: fix by making the sash / net layout continuous across that boundary in `design.py` or by padding the atlas islands). Looked at in the resume (crops of `stills/skin_saffron_chest_4k.jpg` x 1100-1900 / y 1500-2160 and `skin_cinder_chest_4k.jpg` x 1000-2000 / y 1200-2160, the hero's right armpit seen from the front): the cloth weave direction flips across a jagged island edge, the black sash border jumps by ~15 px (3 mm) and there are faint polygon-shaped shade patches in the flat colour (cinder cyan sash); the texture-level seam check cannot see the weave flip or the patches, so the next fix needs (i) the weave UV direction made island-independent (derive the weave coordinates from the 3D position in `M_Char_Suit`, or from a per-island rotation table) and (ii) a check of the normal map (derived from the height map) against the mesh normals at that armpit, (b) the back views are dim (the key sun is in front: add a rim / back fill on the stage), (c) the first suit's 8192 px Tessera maps stream in visibly for ~0.4 s at game start (consider 4096 for Tessera, or touching the textures at subsystem init), (d) `glacier` / `sage` are close to the white end at the fixed exposure.
2. Whole-mesh suits (PLAN: "whole-mesh suits later"): a style can already change colours / patterns only; a different silhouette (cape, collar, gauntlets) needs Blender geometry on the hero rig.
3. Per-suit emissive trim (glow lines) needs an emissive input in `M_Char_Suit` (not built).
4. Hero model / animation items from rounds 08 - 10 (head brow / nose volume, run start / stop / turn) are untouched; the hero-only first pass also owes P3 the section-5 clips of `SPEC.md`.

## Rules that still hold

- ORIGINAL suits only (never an official suit, emblem, web-line pattern or recognisable colour blocking; no image generation for suit art; never write "Spider-Man" or "spider" in a generation prompt). The guard + critic read it every round.
- Every Unreal launch through `gpu_slot.sh` (cap 1), `stop_ue.sh` only, never kill -9 an engine, no listeners, one engine at a time. The lock waits while the owner plays a game: that is by design, not a bug to work around.
- Content is script-generated (`/Content` never committed, no LFS).

## Commands

```
export P2_SCRATCH=/Users/midir/sm2-n1/_scratch/characters UE_WAIT_SKIP=1
python3 tools/ue_char/suits/gen_suits.py --hero --n 4096                    # all suits (CPU, ~6 min); --only cinder for one
python3 tools/ue_char/suits/ip_guard.py palette art/night1/characters/hero/suits OUT.json
python3 tools/ue_char/eval/suit_seams.py art/night1/characters/hero/suits OUT.json
python3 tools/ue_char/suits/swatch_cpu.py art/night1/characters/hero/suits OUT.jpg --views front,three,back   # design aid
unreal/WebHomage/Scripts/build_editor.sh                                    # C++ (close your own editor first)
bash tools/ue_char/fight/build_fight.sh clean,tex,mat,mesh,citizens,rename,fightclips,abp,skins,skinsmap      # content (needs the lock)
python3 tools/ue_char/suits/make_pairs_r11.py docs/night1/characters/round-11 $P2_SCRATCH/../critic-P2-r11/pairs.json
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py /Users/midir/sm2-n1/_scratch/critic-P2-r11/pack /Users/midir/sm2-n1/_scratch/critic-P2-r11/pairs.json
```
Stop an engine only with `/Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh "/Users/midir/sm2-n1/characters"`; count engines with `pgrep -x UnrealEditor`.

## Re-running the evidence (round 12: ONE lock hold of ~23 min does build + every capture)

```
export P2_SCRATCH=/Users/midir/sm2-n1/_scratch/characters; G=$P2_SCRATCH/ueimport
python3 tools/ue_char/prep_glbs.py && python3 tools/ue_char/hero_lens_r8.py $G/SK_Hero.glb && python3 tools/ue_char/suit8/hero_weights_r12.py $G/SK_Hero.glb   # hero GLB (CPU, seconds)
python3 tools/ue_char/hero_suit_r8.py && python3 tools/ue_char/suits/gen_suits.py      # Tessera 8192 (~2.5 min) + the 7 others at 4096 (~5 min); art/.../suits/tessera_* are symlinks to hero/tex
cp tools/ue_char/suits/chain_r12.sh tools/ue_char/suits/.chain_r12_run.sh            # run a SNAPSHOT (never edit a running script)
OUT=$P2_SCRATCH/r12/chainN; mkdir -p $OUT
EV=10.0 STEPS="build stills pawn orbit hero chase fight crowd lineup" nohup /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters --timeout 14400 -- bash tools/ue_char/suits/.chain_r12_run.sh $OUT > $OUT/gpu_wrapper.log 2>&1 < /dev/null &
bash tools/ue_char/suits/post_r12.sh $OUT $OUT        # CPU: fills round-12/ + measures (~4 min)
python3 tools/ue_char/suits/spec_check_r12.py docs/night1/characters/round-12 > docs/night1/characters/round-12/SPEC_CHECK.md
STILLS_4K=$OUT/stills python3 tools/ue_char/suits/make_pairs_r12.py docs/night1/characters/round-12 /Users/midir/sm2-n1/_scratch/critic-P2-r12/pairs.json
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py /Users/midir/sm2-n1/_scratch/critic-P2-r12/pack /Users/midir/sm2-n1/_scratch/critic-P2-r12/pairs.json
```

## Re-running the round-11 evidence (history)

```
export P2_SCRATCH=/Users/midir/sm2-n1/_scratch/characters
OUT=$P2_SCRATCH/r11/chain4; mkdir -p $OUT      # a short re-shoot of one part: STEPS="build orbit" (or "stills", "pawn" ...) with EV=10.0 and its own out dir (the orbit used chain5)
EV=10.0 nohup /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters -- bash tools/ue_char/suits/chain_r11_final2.sh $OUT > $OUT/gpu_wrapper.log 2>&1 < /dev/null &     # record the PID; STEPS="build orbit" runs a subset; without EV= the chain calibrates the exposure first
# then (CPU): ORBIT_OUT=<dir whose orbit3/ is committed> STILLS=stills_a bash tools/ue_char/suits/post_r11.sh $OUT
python3 tools/ue_char/suits/make_pairs_r11.py docs/night1/characters/round-11 /Users/midir/sm2-n1/_scratch/critic-P2-r11/pairs.json
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py /Users/midir/sm2-n1/_scratch/critic-P2-r11/pack /Users/midir/sm2-n1/_scratch/critic-P2-r11/pairs.json
```
`round-11/evidence/ocr_review.txt` is hand-written (the one OCR false positive); re-check it after a new OCR run.

## Older rounds (hero / enemies / crowd, now paused)

Round 10 numbers (fight clips, hit reactions, knockdowns) and the open items (thug collar wedge, hijab walker shin, hero brow / nose volume, orbit guard hold, hood wisp) are in `round-10/SPEC_CHECK.md` and `critic/round-10-CRITIC.md`. The round-11 hair work of an earlier session
(`tools/ue_char/people/hair.py`, `eval/hair_4k.py`, `crops_r11.py`, `make_pairs_r11.py`... that interim round was superseded by the first-pass plan) is committed but was never rebuilt or captured.
How the fight script works (`tools/ue_char/fight/choreo.py`, `fight_script.json`, `r10_check.py`) is unchanged; commands for it: `git show 69afb4b:docs/night1/characters/HANDOFF.md`.

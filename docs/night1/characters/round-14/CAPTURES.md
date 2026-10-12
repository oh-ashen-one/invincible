# Round 14: captures (P2 hero skins, the finished mask sculpt)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Round target (critic r13, single biggest gap):** finish the shared mask sculpt on all 8 suits - (G1) the 4K headside profile edge dips >= 1.5 % of the head height behind the brow -> nose-tip chord; (G2) the brow's front-most point is >= 1 % of the head height in front of the top of the lens, with each lens + rim
seated in its eye socket under the brow ridge (the rim stays ONE closed raised band >= 6 px, the lens >= 1.6x its r12 width, nose bump >= 2 %, face seam a raised cord); (G3) on the Tessera AND Cinder 4K front stills a horizontal luma line through the cheek bones shows >= 3 extrema with swing >= 20 (Cinder: lighten / satin the hood).
Same round, other files (design.py / hero_weights): pipe every sash end (Ash), no armpit stitch zigzag (Ash), no torn Sage trapezius groove, no faceted Cinder shoulders. Gate: no axis below r13 [6,5,5,5,5]; enemy pack and crowd unchanged; P3's pawn cadence / start pop untouched.
Numbers: `SPEC_CHECK.md` (every number is read from `evidence/` by `tools/ue_char/suits/spec_check_r14.py`).

**Source.** The REAL game: UE 5.8.3 `-game`, Metal, offscreen (`Scripts/run_game.sh`), through the GPU lock (`gpu_slot.sh capture`), driven by `tools/ue_char/suits/chain_r14.sh` (`STEPS="build stills lineup pawn orbit hero chase fight crowd"`, `EV=10.0`, run from the snapshot `.chain_r14_run.sh` by `hold_r14.sh`).
**One hold: 2026-10-02 05:32:47 - 05:57:47, 1500 s of hold after 3257 s in the queue, 0 engine crashes, one engine of mine at a time, the engine stopped by the script's own `-quit` (never killed); the lock reported `contaminated=true` (no exclusive lock: other agents' engines rendered during the hold, GPU 0 - 69 % before each of my runs,
`evidence/gpu_util_before_runs.txt`), so no frame time here is a performance number.** The content was rebuilt from the committed scripts first inside the hold (`build_fight.sh clean,tex,mat,mesh,citizens,rename,fightclips,abp,map,maps5,skins,skinsmap`, 114 s; `/Content` is not committed); the hero GLB and the suit maps are prepared on the CPU beforehand
(`tools/ue_char/suits/prep_hero_r14.sh`, `gen_suits.py`, `hero_suit_r8.py`; the chain's build does not run the 'prep' step).
**Resolution (disclosed).** 4K stills: output 3840x2160, internal 3840x2160 (`r.ScreenPercentage 100`, `evidence/stills_perf.json`, `evidence/lineup_perf.json`), committed as 4K JPEG (q2) (front, chest, head, head34, headside, headfront, lineups) or 1920 px (back); the measures ran on the lossless PNG originals
(scratch dir `$P2_SCRATCH/r14/chain1/run/stills`). Movies: 1920x1080 output = 1920x1080 internal, `-movie` = every frame dumped at a fixed 1/60 s step, H.264 crf 18-20, each <= 7.3 MB (largest `swap_pawn_T_key.mp4`).
`run_game.sh` carries another session's uncommitted frame-cap change (stills <= 8 fps, movies <= 30 fps wall clock; fixed-step movies give the same frames): not mine, left alone.

| file | map / shot | what |
|---|---|---|
| `stills/skin_<suit>_headfront_4k.jpg` (8) | Char_Skins, view `headfront`: 0 deg off the face axis, 1.0 m, FOV 26, aim 164, EV bias +10 | **new**: the head straight on: G3 (cheek luma lines) |
| `stills/skin_<suit>_head_4k.jpg` (8) | view `head`: 12 deg off the face axis | G3, H1, H4, H5, H6 |
| `stills/skin_<suit>_head34_4k.jpg` (8) | view `head34`: the round-12 head framing (25 deg, 1.0 m, aim 160) | H3 against r12, G3 at 25 deg, the Sage trapezius |
| `stills/skin_<suit>_headside_4k.jpg` (8) | view `headside`: profile, 1.25 m, aim 166.5, whole head in frame | G1, G2, H2 |
| `stills/skin_<suit>_front_4k.jpg`, `..._chest_4k.jpg` (8 + 8) | views front (7.85 m, CH1) and chest (1.5 m) | CH1 0.543 - 0.544; sash ends, armpit, shoulders, trapezius |
| `stills/skin_<suit>_back_1080p.jpg` (8) | view back | |
| `SWATCH_SHEET.jpg` | composed from the 4K stills (front + back + chest + head of all 8 suits) | **the owner's sheet** (sign-off still required before any merge) |
| `swap_pawn_T_key.mp4` (11.4 s) | Char_SkinsPlay, the PLAYABLE pawn, 7 injected real T presses | swap movie: 7 / 7 presses on the pixels, worst 33 ms |
| `orbit_all_suits.mp4` (11.4 s) | Char_Skins orbit shots | the stage hero orbiting through every suit |
| `hero_run_side.mp4`, `hero_run_34.mp4`, `hero_run_leap_side.mp4`, `hero_run_chase.mp4`, `hero_run_toward.mp4` | Char_Hero shots 1-3 / 6-7 (as round 08) | the stage hero (Tessera, finished head): CH6 / CH7 / CH2 instruments |
| `street_fight_wide.mp4` (8.0 s), `crowd_tracking.mp4` (8.0 s) | Char_Fight shot 0 / Char_Crowd shot 0, unchanged | `evidence/fight_unchanged_since_r10.txt` (identical script, choreography, weapon fit) |
| `enemy_lineup_4k.jpg`, `enemy_lineup_34_4k.jpg` | Char_Lineup shots 5 / 6 | 7 enemies, wall luma 140 as in r13 (same pixels within 1 level) |

## What changed in the content this round (all committed, all script-generated)
- **Head** (`tools/ue_char/suit8/hero_head_r14.py`, run on the hero GLB so all 8 suits inherit it): the r13 features were smaller than the egg's own curvature (the browser face is a vertical plane at z ~ 100 mm from chin to brow), so the profile was a straight slope. r14: a **brow shelf** (+11 mm, arching down toward the temple),
  a **nasion notch** (the nose ridge now starts BELOW the brow and climbs to a 22 mm tip), deep **eye sockets** with a canthus pit next to the bridge (-5 mm), **cheek-bone planes** (+9 mm) over hollows (-5 mm) and nasolabial folds, a **mouth bulge** + groove (6.9 mm), a **chin plane** (+9 mm), 7.5 mm temple widening.
  Mesh silhouette (CPU, the GLB the engine imports): recess 6.05 % HH, brow over the lens top 4.3 % HH, over every rim vertex 1.4 % HH.
- **Eyes** (`tools/ue_char/hero_lens_r14.py`): 61 x 28 mm lenses (r13 63), centred 40.5 mm from the midline, rim crest 3.1 mm (r13 3.6) - the lens + rim lie IN the socket under the brow ridge (the surface under them comes from the sculpted mask).
- **Hood / relief tone** (`design.py`): near-black hoods hid the relief (r13 cheek lines: 1 - 2 extrema, swing 30 - 55): a 'deep' hood is lifted to the body colour (`face.lift`, Tessera / Plum; Ash 0.6; Cinder `hood: body`), and a **baked face tone** from the sculpt field (convex lighter up to +34 %, hollows darker up to -42 %).
  Two raised **cheek panel seams** per side (light cords like the face seam: from the eye frame down the cheek-bone plane to the jaw, and from the nose-bridge flank toward the mouth piece): a cord's luma contrast does not depend on the sun, which gives a dark hood only a 10 - 20 luma swing.
- **IQ** (`design.py`, `hero_shoulder_r14.py`, `hero_weights_r14.py`): every sash end is a **straight plane at |x| = 0.118 m** finished like the long edges (DEEP border cord, two stitch rows, an accent pipe 5.8 mm outside); the wedge pipe + stitch rows **end 3.5 cm below the armpit crease**; the **torso net stops at the neck base** (on the oblique trapezius slope the cords stretched into torn creases);
  the shoulders / upper arms are refined once with **Phong tessellation** (+20k faces, original vertices unchanged); the **trapezius skin weights** are smoothed like r12's armpit (CPU skinning, folded faces in the trapezius region, original -> r14 weights: sprint 14 -> 5, fight idle 7 -> 0, run 4 -> 1; the idle had none).
- **Rims**: silver up to a hood luma of 0.36 (r13: 0.20), graphite on the pale hoods (Glacier, Sage). See "Known problems".
- Unchanged: the enemy pack, the crowd, the fight, the hero clips, the pawn (P3).

## Known problems (honest list)
- **H4 (my own strict rim criterion: the luma of the rim band differs from the mask by >= 15 on >= 90 % of 48 angles) passes on 2 of 8 suits (Glacier, Sage; r13: 4 of 8)**: closed fractions Tessera 0.35 / 0.35, Verdant 0.54 / 0.71, Plum 0.90 / 0.81, Cinder 0.54 / 0.60, Ash 0.79 / 0.77, Saffron 0.58 / 0.63. The rim is a clear closed raised gunmetal band by eye on all 8 (crops
  in `evidence/measures/head_overlays/`; the rim is 3.4 mm wide = 28 px at the 4K head still, 10 - 43 px median by the measure), but a polished silver rim reflects sky / floor values that cross the lifted hoods' luma at some angles; the lifted hoods made the silver rim worse than r13's near-black hoods did (Tessera 0.85 -> 0.35). A dark-rim variant, or an accent-lit rim edge, is the next experiment.
- **Cinder shoulders: no measurable or visible change** (`evidence/measures/iq/q4_cinder_shoulder.jpg`): the silhouette contour measure is 12.2 -> 10.9 vertices per 1000 px with a corner at the panel edge; the stored normals match the geometry (mean 1.7 deg, p90 2.7 deg), so the "facets" are not a normal fault, and the CPU render of the shoulder silhouette looks the same before and after the one Phong level. Not fixed; this needs the real cause (the DEEP panel edge is cut by skin weights).
- Ash sash end: straight in the rest pose and finished by eye, but the end line still has an rms deviation of 6.7 px in the posed frame (r13 7.2): the shoulder skinning bends the plane. A small crease remains at the shoulder / sash junction (`q1_ash_sash_end.jpg`). The Verdant chevron step of r13 is gone because the V now ends at |x| = 0.118 m; the instrument finds no edge in its ROI, so it is reported as n/a, not 0 px.
- Sage trapezius: the net no longer reaches the neck (dark thin-line pixels 10.3 % -> 0.07 % of the critic's box); one short skin crease remains left of the neck (visible in `skin_sage_chest_4k.jpg`). Armpit creases of Glacier / Ash (the arm panel folds under the arm) are not touched.
- The raised-piping share of the Tessera chest dropped 0.588 -> 0.485 of the 64 px cells (median pair 23.8 -> 19.5, still inside the 0.34 - 0.66 band of r12 / r13): the other seven suits moved -0.05 .. +0.07. Not investigated further.
- The cheek panel seams are a design change (shared by all 8 suits): the outer ones can read as "tracks" from the eye frame; they are what makes the cheek luma line robust on dark hoods. The owner decides whether they stay.
- IP guard: min palette distance 45.0 (r13) -> 38.4 (the shared seams / tone are in the structural comparison); no fails, OCR 1 hit (Sage chest "SONY": noise on the hexagon net, reviewed by eye in `evidence/ocr_review.txt`).
- Hold contaminated (other agents' engines rendered alongside); the lineup / fight / crowd are re-captures of unchanged content.

## Evidence (`evidence/`)
`head_check.json` / `head_check.txt` + `measures/head_overlays/*.jpg` (lens masks, profile chord, cheek lines on every still), `head_profile_mesh.json` (+ `measures/head_profile_mesh.png`, `head_relief_cpu.png`), `iq_check.json` + `measures/iq/*.jpg` (round-13 / round-14 crops of the four defects and of the other suits' sash ends),
`trapezius_fold_check.json`, `fold_check.json`, `measures/` (relief / sash / jog of the chest stills, CH1, CH2 / CH6 / CH7 of the clips), `ipguard.json`, `seams.json`, `ocr_stills.json` + `ocr_review.txt`, `regression.txt`, `swap_latency.json`, `lineup_exposure.json`, `fight_unchanged_since_r10.txt`, `characters_build.log`, `chain.log`, `pawn_*`.
Critic pairs: `critic_pairs.json` (38 pairs); the pack is in `/Users/midir/sm2-n1/_scratch/critic-P2-r14/pack` (key outside it).

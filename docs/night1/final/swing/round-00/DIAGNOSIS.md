# Round 00 diagnosis (builder SW): why swing presses look awkward

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Build = tag `final-before` (16d24911) behaviour + telemetry-only columns (proved identical: 1229 rows x 164 existing columns, 0 differing cells, `s1_swing_chain` nullrhi, before vs after). Clips and numbers:
`docs/night1/final/swing/round-00/` (`CHECK.txt`, `*_telemetry.csv`, `*_check.json`). Per-press table: `python3 tools/final/swing/diagnose.py <telemetry.csv> --case <case>`
(its camera model reproduces the logged `rope_ax/ay` to a median of 1.0 px, p90 4.0 px, so the px values below are real 1080p offsets).
Status words: **confirmed** = measured in telemetry (and the code path read); **hypothesis** = plausible from code, not measured. I looked at numbers, not at the pictures; items that need the eye are marked.
Ranked by how visible each is on screen.

## 1. Strand starts about a body-length behind the hand (confirmed, every press, every clip)
- Strand start vs the hand as rendered in the same frame: **0 % of web-on frames within 8 cm** in all 5 clips; error p50 60.1 / p95 61.4 / max 62.6 cm at median hero speed 37 m/s (s1) = speed/60 s, i.e. exactly one frame of travel. In px at 1080p (press frame, s1): 21 / 15 / 7 / 10 / 21 / 3 px at +0 frames, 20-28 px 3 frames later; worst case `s2_c1_roof_jump` 124 cm = 112 px at +3 frames.
- Cause (code): `UpdateWebs` (`WebTravCharacter.cpp` ~1225) reads `HandWorldCm` = `GetMesh()->GetBoneLocation("hand_R"/"hand_L")` during the actor tick; the mesh's anim tick runs after the actor (`M->PrimaryComponentTick.AddPrerequisite(this, PrimaryActorTick)`, line 383), so the bone is last frame's pose in world space while the actor has already moved. The strand start equals that stale read exactly (same-row bone read max 0.0 cm in s1/s4/s5).
- Also: the strand uses the bone origin, no palm offset.

## 2. The firing arm is not aimed at the anchor when the strand appears (confirmed)
- Arm (shoulder -> hand) vs shoulder -> anchor, at the press / at tip arrival: s1 31-62 deg / 33-63 deg (median arrival 48 deg, 0/6 within 20 deg); s2 median arrival 37 deg (1/9); s3 42 deg (2/7); s4 50 deg (0/6).
- Worst cases: `c3_wallrun` press out of a wall run 114 / 102 deg (arm never reaches); `c5_repress` second press 155 / 170 deg (arm points away from the anchor); `c1_roof_jump` 148 / 43 deg.
- Cause (code): `ArmAimWeight` ramps 0 -> 1 over 0.15 s (`WebTravAnimInstance.cpp` ~514) while the tip arrives in 0.05-0.13 s (shot 0.08 s median), so the arm is at roughly half weight on arrival; the aim also starts from whatever pose the previous node left. Motion start (angle drops 5 deg) median 0.0-0.13 s (s3 0.133 s, s4 0.100 s).

## 3. Swing starts and tension builds before the tip lands; attach pop (confirmed)
- Chest angular rate within -3..+5 frames of an attach: **0 % <= 400 deg/s** in every clip, > 700 deg/s on 6/6 (s1), 7/7 (s3, s4), worst 2241 deg/s (`c3_wallrun`), 2155 (s1 first attach), `c1` 1113. Hand speed ratio at the attach frame is fine (max 2.0x).
- Mode becomes `swing` on the press frame and rope tension > 0.05 starts 0.02-0.13 s BEFORE the tip reaches the anchor (s1 -0.08 s median, s3 -0.13 s): the body is yanked while the web is still in flight (W3 0/6, 0/7, 0/7). Cause (code, hypothesis for the exact pop): `WebAttach` and `SetMode(Swing)` happen together at the press; the pose changes node (`air_*` -> `swing` clip blend, 0.2 s `BodyAlignW` ramp) while the pendulum already pulls.
- `shoot` duration: 0.050-0.160 s (median 0.08-0.14), tip speed median 371-378 m/s: inside W3's numeric band except 0.050/0.055 s shots on close anchors (14-18 m, `c8`, `c9`).

## 4. Press with no anchor gives no visible response (confirmed)
- `s2_c7_no_anchor`: presses at 0.30 s and 1.40 s (330 m up): no strand, `anim_node` stays `air_rise` / `air_dive`, no reach pose. The only response is `Emit(N_noAnchor)` (`WebTraversalComponent.cpp` ~806) plus a comment "no held reach pose while searching for a web" in `WebTravAnimInstance.cpp` ~225 (the r09 decision). W10: 8/11 presses resolve.

## 5. Press right after a jump from a roof: strand 100 ms late, on the wrong pose (confirmed)
- `s2_c1_roof_jump`: swing pressed 0.1 s after the jump; `LaunchJump` sets `SwingCooldown` 0.12 s (`WebTraversalComponent.cpp` ~379), the strand shows 6 frames (100 ms) after the press; at the press frame the anim is still `ground/perchLand` (landing crouch) with the arm 148 deg from the anchor; strand start 124 cm / 112 px from the hand 3 frames later.

## 6. Press right after a release: strand out while the body is still in the release tuck (confirmed)
- `s2_c5_repress` second press 0.15 s after the release: a strand exists at the press frame (the "web pending" path: shot on the rise, pendulum starts later, `S.bWebPending`), mode `air/release`, anim `releaseTuck`, arm 155 -> 170 deg from the anchor, hand chosen L while the anchor is on the right (W9). The swing proper starts 0.5 s later (t=1.95 s in the probe).

## 7. Wrong hand for the anchor side (confirmed in 2 of 9 s2 presses; 0 of 20 in s1/s3/s4)
- W9: s1 6/6, s3 7/7, s4 7/7, s5 6/6, but s2 7/9: `c6_side_anchor` (stick held left, hero hugging the east facade: right hand, anchor on the left) and `c5` second press (left hand, anchor right). Hypothesis: the hand is chosen from the blended steering direction `Dir = Lerp(Fwd, Turn, 0.6)` (`WebTraversalComponent.cpp` ~820) while the test uses the travel line.

- Anchor behind the hero: 1 of 7 attaches in `s4_release_float` (W10 'anchor behind the hero' count; the anchor rule drops anchors behind the body only above 6 m/s, `bBehind` in `WebTraversalComponent.cpp` ~790; this one is not identified further).

## 8. Strand passes through collision geometry (confirmed by world raycast hand -> anchor; trees not measured)
- Drawn frames with the hand->anchor line blocked (clear fraction < 0.995): s2 `c9_trees` 100/130 (min 0.01, i.e. blocked at the hand), `c4_flip_cancel` 59/121 (min 0.55), `c1` 7/121, `c8_close_facade` 4/124; s3 `c1`, `c5` 27/76, 31/76 (min 0.47); s4 50/559 (min 0.25 at t = 4.3 s); s1/s5: 0/515. The object hit is not identified; tree crowns have no collision so crown clearance is unmeasured (needs the frames).
- Hypothesis: anchors are searched and ray-confirmed from the body position (`Anchors->Find(S.Pos, ...)`), the strand is drawn from the (displaced) hand.

## 9. Readability (confirmed on frames, rope_r25_check at 10 fps)
- W5: s1 75/75, s5 75/75 (width 3.0 / 4.0 px), s4 81/84, s2 114/130 (88 %), s3 45/57 (79 %). Failures: width 4.5-5.5 px at close range (s2 c9/c8, s3 all 12) and contrast (`c4` t=0.95 s: contrast 17/255, pass 0.18; s4 t=4.1-4.4 s contrast 34-43). Cause hypothesis: the screen-space width clamp (`RopePxMax`) is looser than 4 px for near segments; contrast failures are against bright facade (needs the frames).

## 10. Strand shape: wave does not straighten fast enough (confirmed, model value before the screen clamp)
- Wave in flight median 14.9 cm (max 24.8); 0.10 s after landing median 2.1 cm (max 3.7) in s1/s4/s5 (W6 limit 2.0), 3.5 / max 5.8 cm in s2. Segments: 12 cylinders per strand (`SEGS_PER_STRAND`); joint kink at 25 cm wave over 40 m is about 2.6 deg (computed): segmenting is a hypothesis, not seen (needs the eye).

## 11. Release (measured: not a vanish)
- Drawn after release 0.15-0.17 s (10 frames): the strand shortens from the hand end toward the anchor (16.1 m -> 0.1 m), then is hidden when under 5 cm; W8 passes at the lower edge of 0.15-0.40 s. The release strand is not at the hand (start moves along the line), by design (`UpdateWebs` retract branch).

## 12. Body / air (A lines) and flips
- A1 (pose signature change >= 0.15 per 0.3 s inside swings): s1 43 %, s2 56 %, s3 83 %, s4 36 %: swings read static in s1/s4 (median 0.12-0.14). A2-A4 pass (s1: 4 styles in 6 swings, longest held air pose 0.28 s).
- A5: catch out of a trick 0.72 s median after the last shape (s3, 0/7 <= 0.25 s), chest rate through the catch 1316 deg/s median (0/7 <= 400).
- F with stick (s3, each from the same 110 m start): forward -> frontSingle, back -> backSingle, right -> barani, left -> barani, neutral -> backSingle, forward-right -> frontSingle, back-left -> barani (the owner's always-backSingle bug is gone; every case starts the pool at K=0, so these are the first program of each pool). Note: `heading` in a script overrides the stick.
- A6/A7 n/a or partial: only 2-7 tricks per clip; pike hip angle and pencil straightness are not measurable from the current telemetry (no hip-angle column).

## Checker limits (so the table is read correctly)
- W1 uses the hand bone, no palm offset. W2 uses shoulder = `upperArm_L/R` bones. Chest = bone `spine2`. W7 = collision raycast only. W6 reports the model wave, not the on-screen shape. W4 "body leads into the swing within 0.15-0.35 s" is not scored (no defined column). A1 signature = rms of the 10 `pose_sig` values.

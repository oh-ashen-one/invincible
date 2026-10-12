# TRICK_CAMERA_SPEC — reconciled trick camera (director, Fable 5.1, 2026-09-30, after round 15)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.

## Why the Camera axis is stuck at 5 (rounds 12–15)
Each round satisfied the previous critic's single camera demand by turning one knob (tilt up for sky → orbit side-on → cap the pitch → face
away from the sun) on top of an architecture the reference does not have: a **fresh side-on orbit searched every 0.15 s at 3.3 m**. Round 15
telemetry (trick windows = `flip_t >= 0` + 0.5 s): camera yaw **85–107°** off the travel heading, yaw rate p90 **216°/s** (max 2717), distance
p50 **3.3 m**, hero height p50 .25–.37 / p90 .48–.52, hero x p5–p95 .10–.83, camera level with the hero (camZ−heroZ p50 0.0–0.1 m).
The owner clip (sheets 01–04, F9 in FLIPS_SPEC) shows the opposite: a **3/4-behind chase that holds its yaw**, hero **0.18–0.30** of frame
height, hero centre x .35–.60 and y .30–.45, camera **slightly below** the hero, and sky behind him **only when he is above the skyline**
(sheet 4 row 2, sheet 1 row 2); during the roof vault (sheet 2) and the facade run (sheet 1 rows 3–4) the reference itself frames him
against glass and roof. Roughly 33 of 73 sheet frames (~45 %) have sky behind the hero. Nothing below is a new knob: it replaces the
search-and-orbit with a held 3/4 chase, and moves sky from the camera to the hero's altitude.

## Lines (trick window = `flip_t >= 0` through 0.5 s after the program ends; every clip with a trick: a, b, f1–f5)
| id | line | from | supersedes |
|---|---|---|---|
| TC1 | **Yaw at release: ONE offset of 35–55° from the travel-behind direction** (3/4 behind, hero's travel leads into the frame). Chosen once, at the release frame, never re-searched during the trick. | sheets 1/3/4: rope and travel lead into the frame at ~20–50° from the view axis; the hero is never seen full side-on with travel across the frame | r13 "≥ 60° off the flip axis" and r14/r15 "orbit ±90°". r13's unreadable rotation came from a camera 51–56° **under** the hero, not from being behind him; at 45° 3/4 the tuck axis still turns ≥ 300° on screen (TC-J keeps r13's test) |
| TC2 | **Side rule, in order:** (1) obstruction: the spot at TC4 distance must be sweep-reachable with 1.5 m free beyond it and a clear path 0.5 s along the travel (r14 clearance); (2) sun: view ≥ 100° from the sun (r14); (3) tie → the side with more open space (r11). If only one side passes (1) it wins even if it fails (2); if neither passes (1), pull in along the same yaw (TC11), then fall back to the plain chase (yaw 0°) — **never** to a full side-on orbit. | r15 gap ("flies through trees", "finds the sun") | r15's "side-on yaw clear of trees" (side-on is the cause of the tree passes: side spots sit over the sidewalk canopy) |
| TC3 | **Hold:** yaw drift ≤ ±10° over the trick (world yaw, not hero-relative); yaw rate ≤ 40°/s once `flipcam_k ≥ 0.9`. Blend-in ≤ 150°/s. | sheets: the background parallax is a slow pan, never a swing round the hero | r15 "±30°" (tightened: the reference holds) |
| TC4 | **Distance 5.0–6.5 m** at the swing FOV (hFOV 100–110, T14; no widen, no narrow) → hero height p50 **.18–.28**, p10 ≥ .12, **p90 ≤ .36**. Pull-in for obstruction allowed to 4.0 m only (TC11). | F9 .18–.36; T8 p90 .38; T15 4–7 m; r15 at 3.3 m gave p90 .50 | r15 "distance so hero is .15–.38" kept, made concrete: `FlipDist` 3.3 → 5.5 |
| TC5 | **Pitch band during the trick: 8° up .. 8° down**, p50 within ±5°. Within 0.5 s of the catch: 4–12° down (settle band). Cap `MaxLookUpDeg` stays 10. | sheet 4 row 2 / sheet 1 row 2: horizon at ~0.55–0.62 of the frame height ≈ 4–8° up at vFOV 70; roof vaults ~20° down are attach/land frames, not trick frames | r13 "≤ 30° up" (r14's 8° cap stands); r11 tilt-up for sky (void: sky comes from TC7/TC8) |
| TC6 | **Height: camera 0.5–2.0 m below the hero's hips** during the airborne shapes (heroZ − camZ p50 in 0.5–2.0, p10 ≥ 0.2). He is placed above the view centre so the skyline falls below him. | F9 "camera level with or below the hero"; at 5.5 m and pitch +5° up, hero y .35 ⇒ hero ~1.5 m above the lens | r15's level camera (camZ−heroZ ≈ 0) |
| TC7 | **Hero placement:** centre x p5–p95 inside **.35–.60**; centre y p5–p95 inside **.28–.48** (above centre, sky room above him). | sheets: hero x .30–.60, y .30–.45 during tricks | r15 "x .44–.56" (that is the swing-camera T9; the reference does not centre tricks) |
| TC8 | **Sky by altitude, not tilt:** a flow/release flip fires from an apex whose hips are ≥ 3 m over the lower roofline within 30 m when a rise of ≤ 14 m gets there (`FlowRoof*`, r15), else it fires anyway. Target: **≥ 35 % of trick frames (pooled f1–f5) have a 40 px ring ≥ 50 % sky**; a canyon flip against a facade is legal. No pitch above TC5 to buy sky. | sheets: ~45 % of trick frames have sky behind him, the rest glass/roof; r15 suncam per-flip roofline table | r11 "≥ 70 % of trick frames ≥ 50 % sky" and r12's 95–100 % ring (bought with a 51–56° look-up: cause of r13) |
| TC9 | **Sun/glare:** view ≥ 100° from the sun in every trick frame (r14 S1); glare cost term kept. Blow-out measured on the **suit mask**, not the box: no trick frame with > 5 % suit pixels at luma ≥ 245. Mirrored-sun hot-spots in glass behind the hero are logged to P4 (exposure/bloom), not scored on the camera. | r14/r15 L1; r15 f4 9.85 s = curtain-wall mirror of the sun | r14 box test (the box counts sky/glass behind him) |
| TC10 | **Blends:** in 0.30–0.35 s from the release frame (ease-in-out; ≤ 150°/s yaw); out ≥ 0.40 s starting at the web attach (r12), reaching the settle band by attach + 0.5 s (r13 P2). No cut: per frame pitch ≤ 3°, yaw ≤ 4°, position ≤ 1.2 m (r12). | r12/r13 tests | — |
| TC11 | **Obstruction during the trick:** a sweep hit dollies the camera **in along the held view axis** (to ≥ 4.0 m), never yaws or re-picks the side; lens sphere 0.25 m clear of geometry and foliage every frame (T19); the hero is fully in frame every frame. If the pull-in would go under 4.0 m, blend to the plain chase (TC2 fallback) over ≥ 0.3 s. | r15: hero lost 0.2 s at f4 5.62–5.82, tree pass | r13-era "hold the view" and the r12 3 m cut (already deleted) |
| TC12 | **Roll ≤ 2°** (no roll with the body). FOV, kick, punch and shake untouched by the trick camera. | F9 roll ≤ 5°, T13 | — |

## Tests — the builder runs them on telemetry (`trickcam_check.py` v2), the critic on the rendered mp4 (`px_check.py` hero mask + `vp_cam.py`); thresholds identical
Window per test: `flip_t >= 0` through +0.5 s after the program's last segment; pooled per clip unless stated. All must pass on f4 and on f1–f5; a and b are informative.
- **TC-A yaw offset:** |`pcm_yaw` − hero horizontal velocity heading at release| p5–p95 in **30–60°**; per-trick range (max−min of world `pcm_yaw`) ≤ **20°**.
- **TC-B yaw rate:** with `flipcam_k ≥ 0.9`: p95 ≤ **40°/s**, max ≤ **60°/s**; whole window incl. blends max ≤ **150°/s**.
- **TC-C hero height** (`hero_bbox_h` / mask): p10 ≥ .12, p50 .18–.28, p90 ≤ .36.
- **TC-D placement:** `hero_cx` p5–p95 inside .35–.60; `hero_cy` p5–p95 inside .28–.48.
- **TC-E pitch:** `pcm_pitch` p5 ≥ −8 (up) and p95 ≤ +8 (down) inside the trick; median at attach + 0.5..1.0 s in 4–12° down.
- **TC-F height:** (`z_m` − `pcm_z`) p50 in 0.5–2.0 m, p10 ≥ 0.2 m.
- **TC-G safety:** `hero_in_frame` = 1 on 100 % of window frames; `cam_in_geometry` = 0; `hero_occl` = 0; foliage: lens sphere clear (probe log).
- **TC-H sun/glare:** `view_sun_deg` min ≥ 100; suit-mask luma ≥ 245 share ≤ 5 % on every window frame.
- **TC-I sky:** `sky_check.py` ring ≥ 50 % sky on ≥ 35 % of trick samples pooled over f1–f5 (10 fps), with hero h ≥ .15 on those frames.
- **TC-J readability:** tuck head–hip axis turns ≥ 300° on screen per backDouble (r13 A1, unchanged) — proves 3/4 still reads.
- **TC-K continuity:** r12 per-frame slew limits (3° / 4° / 1.2 m) on every frame of the clip; blend-out ≥ 0.40 s measured from the attach.

## Builder notes (not lines)
- Implementation is a removal, not an addition: `SearchSkyView` runs **once** at release over yaw offsets 35–55° on the two sides (TC2 order),
  elevation so the lens is 0.5–2.0 m under the hips at 5.5 m; delete the 0.15 s re-search and the 70–115° candidate band; `FlipDist` 3.3 → 5.5;
  `FlipInT` 0.30–0.35, `FlipOutT` ≥ 0.40 (r12), `FlipPitchUpMax` 8 stays. Frame target (`FlipSFrame`) → hero centre y 0.38.
- Sky is the flow-flip apex's job (`FlowRoof*`), plus TC6/TC7 placing him above the view centre. Do not touch pitch to chase TC-I.
- Round closes on Camera ≥ 7 only with TC-A..TC-K passing on the 1080p render AND the blind A/B no longer citing camera on any pair.

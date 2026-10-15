# Invincible flight suite r2: independent blind critique

Evidence used: the 17 mp4s (frames pulled with ffmpeg at the times quoted), the `_sheet.jpg` contact sheets, the `_telemetry.csv` files, the `_luma.txt` files and CHECK.json. I read no builder notes and no source code. Times are clip seconds (60 fps, so frame = t×60). The 60 fps capture rate is not evidence of real-time performance.

## 1. Verdict: FAILS TARGET

| axis | score /10 |
|---|---|
| silhouette & poses | 3 |
| suit / character read | 5 |
| camera | 3 |
| speed & impact | 3 |
| destruction / FX | 2 |
| glitches (10 = none) | 2 |

**Lowest scores: destruction/FX and glitches, both 2.**

How the scores were measured:
- **Hero size.** I masked the blue and yellow suit pixels in each frame. In cruise and boost frames the hero is only 0.10–0.16 of frame height:
  - fl04: 106–117 px during boost.
  - fl03: 155–196 px.
  - Telemetry `hero_bbox_h` reports 0.19–0.29 for the same frames. That is about 1.8× too big, so the framing gates are judging a hero larger than the one on screen.
- **Character.** Close views show the suit colours correctly: yellow torso, blue limbs, black belt and short dark hair (fl11 3.6–6.9, fl13 3.3/9.6). But:
  - The hair is a smooth black cap with a dark band around it.
  - Yellow-tinted goggle lenses never appear in any clip, because the camera is always behind the hero.
  - The suit is flat plastic with blue bare-looking hands.
  - The glutes are oversized. In every flight view they are the largest shape in the silhouette.

## 2. Per case

| case | verdict | defects (pixels / measurements) |
|---|---|---|
| fl01 takeoff_hover | FAIL | 0.00–0.10: opens in a wide frog crouch that pops to standing by 0.20. 1.25: takeoff arms flail with hands on top of the head. Hover is a stiff standing mannequin with arms hanging. The "gentle touchdown" is not gentle: z falls at a constant vz −10.0 m/s down to 1.41 m, then vz is 0 one frame later (10.82→10.85). |
| fl02 takeoff_to_fly | MINOR | Takes off from the yellow centre line of a live avenue. Climb and level-out work (z 0.9→53.9). From 4.0 on the hero reads as a blue egg seen from behind and below: the head is barely visible and the arms are hidden. |
| fl03 cruise_hands_off | MINOR | Altitude held at exactly 60.0 m. Same egg silhouette, hero 0.14–0.18 of frame height. There are no wind or speed cues. |
| fl04 boost_sonic | FAIL | No sonic boom is visible. At 1.67 (frame 102) mean luma goes from only 101.4 to 103.1. Frames 98–112 show no ring, cone, flash or vapour. At 160 m/s and 120 m altitude the city barely moves, so the speed does not read. Boost pose at 1.55–2.0: rear view of the hips and boots, with no visible head or forward fist. |
| fl05 bank_turns | MINOR | Banking reads: about 45–60° of body tilt at 2.4–4.0 and 5.6–7.2 (telemetry `fl_bank_deg` up to ±70). The camera never rolls, and the silhouette is still the egg. |
| fl06 look_steer | MINOR | Steering works: yaw −93°→−3°, z 80→106→94. The hero stays small and seen from behind for the whole clip. |
| fl07 climb_dive_keys | MINOR | Climb works (z 70→125) and so does the dive (→83.75). In the dive, 6.0–6.6, the camera looks down onto the hero's backside and the head is not visible. |
| fl08 brake | MINOR | 55→0 m/s at 3.5–3.8, and the upright flare reads. There is no air-burst or brake effect. The hover after the brake is a dead mannequin stance. |
| fl09 dash | FAIL | The dashes (1.5, 3.0, 4.5) have no effect: no streaks or afterimage, and the peak speed is 46 m/s. The camera swings 58° in yaw on the right dash, so it reads as a turn rather than a lateral burst. 2.5–3.15: a billboard fills about two-thirds of the frame. At 7.9 the camera ends nose-to-wall. |
| fl10 slow_flight | FAIL | Instead of a controlled slow glide over the avenue, the hero bumps facades at 4.6 and 7.95. Beige untextured cubes spawn and the HUD shows COLLATERAL $32K. The pose is a limp dangle with one arm raised. |
| fl11 slam_crater | FAIL | 1.5–2.1: the slam is an upright, feet-first drop with one arm raised, not a dive. 2.3: a dark van fills about 30% of the left of the frame. 2.4: a flat white smoke wall covers the lower half. 3.0: frog-squat landing, not a superhero three-point landing. The crater is a flat dark decal disc. Debris is plain beige cubes, one hanging in the air above the van hood at 2.8–3.3. From 3.6 to 7.0 the hero stands in the identical idle pose. |
| fl12 fast_land | FAIL | Dive 1.0–2.4: hero pushed high in frame (`hero_cy` down to 0.22), arms at the sides and legs fused into one blob. Landing has the same flat crater, transparent bubble "smoke" (2.8), a cube floating in front of the hero (3.0) and a frog squat. Traffic keeps driving over the crater rim (4.5). |
| fl13 soft_land_walk | FAIL | Touchdown hits at 10 m/s and stops dead in one frame (3.07→3.10). The hero lands about 2 m in front of a moving van (3.15–3.3). The "walk" is a 9.8 m/s run after 3.8 s of idle standing. |
| fl14 breach_cruise | FAIL | 2.2–2.54: the breach hole is a flat brown disc covering about 25% of the frame, with transparent glass-like bubbles and paper-card debris. 2.53: camera teleports 74 m relative to the hero, with a 39° yaw and 48° pitch jump. 2.62–3.15: 33 near-black frames (luma 27–39). From 2.66 to the end at 8.08 the hero is stuck at (339.52, 384.28) at 0.000 m/s, pinned against a glass tower in the fly state. |
| fl15 breach_boost | FAIL | Same flat disc hole and bubble smoke at 3.42 and 9.95. Camera jumps 26 m at 3.58. The hero is hidden through both breaches, and the clip ends mid-breach. The booms at 0.77 and 4.14 are invisible: luma stays at about 100 in frames 44–51. Hero about 0.10 of frame height. |
| fl16 slow_facade_slide | FAIL | 3.55 and 7.25: fire-escape stairs pass through the hero's head and arm. 3.85: the raised hand sinks into the window plane. `hero_occl` is 0.617 at 7.33. The slide pose is a limp one-arm reach. |
| fl17 rescue_crane | FAIL | 12.62: an unintended breach through a glass facade, with a tan disc filling about 40% of the frame and COLLATERAL $2.9M. 13.0: camera jumps 38 m. 16.36–16.46: the crane's yellow slab blocks the frame. 17.0: the "catch" is the hero standing or sitting on top of an untextured grey box, with no grip. 18.4–20.4: the load is nowhere in frame during the carry dive, and the hero is jammed at the top edge (`hero_cy` 0.14–0.21, `px_top` 0–88, 17.7–20.1). Pose then pops from head-down (20.4) to prone (20.8) to upright (21.2). 21.4–21.8: hero intersects a glass wall. 21.91–22.58: touchdown hidden behind a rooftop wall (0.67 s). |

## 3. Top 8 defects (ranked)

1. **Breach destruction is fake.**
   - Evidence: every hole is a flat untextured brown or tan disc with transparent bubble spheres and paper-card debris (fl14 2.2–2.54, fl15 3.42/9.95, fl17 12.62).
   - *Test:* in every breach frame the hole shows jagged geometry with the interior visible through it, at least 20 textured debris chunks fall, the dust is opaque, and no single flat disc covers more than 5% of the frame.
2. **fl14: camera cut, blackout and hero stuck after the breach.**
   - Evidence: camera jump of 74 m / 39° yaw / 48° pitch at 2.53; 33 frames with luma under 40; hero at 0.000 m/s from 2.66 to 8.08.
   - *Test:* after the exit, speed stays above 40 m/s, no frame has luma under 40, and camera movement relative to the hero stays under 1.5 m per frame.
3. **Flight silhouette is an egg seen from behind.**
   - Evidence: the glutes dominate, the head and arms are hidden, and the pixel-masked height is only 0.10–0.16 of the frame (fl03, fl04, fl15).
   - *Test:* in cruise and boost the head, both arms reaching forward and both legs are separately readable, and the hero is at least 0.18 of frame height by pixel mask. Telemetry `hero_bbox_h` matches the pixel mask within 15%.
4. **Sonic boom is invisible.**
   - Evidence: fl04 frame 102 luma moves only +1.7; no shock shape in frames 98–112; fl15 frames 44–51 the same.
   - *Test:* a vapour cone or ring at least 25% of frame width stays visible for at least 0.3 s.
5. **Slam and landings lack impact.**
   - Evidence: feet-first slam, frog squat, flat crater decal and floating cubes (fl11 1.5–3.3, fl12 2.67–3.0).
   - *Test:* head- or fist-first slam pose, a three-point landing, a crater with 3D displaced chunks, and no debris motionless in the air for more than 3 frames.
6. **The rescue doesn't show a rescue.**
   - Evidence: no grip on the load, the load is out of frame during the carry, the touchdown is hidden for 0.67 s, and there is an unintended breach (fl17).
   - *Test:* hands contact the load and both hero and load are in frame for every frame from catch to set-down, with 0 breaches and a hidden run of 6 frames or fewer.
7. **Geometry clipping.**
   - Evidence: fl16 3.55/7.25 (fire escape through head and arm) and 3.85 (hand into window); fl17 21.4–21.8 (glass wall).
   - *Test:* zero body-into-geometry intersections in any frame of fl16/fl17, and a standoff of at least 0.3 m while sliding.
8. **"Gentle" touchdowns are 10 m/s impacts, and there are off-model pose pops.**
   - Evidence: fl01 10.82→10.85 and fl13 3.07→3.10 go from vz −10 to 0 in one frame; frog crouch at fl01/fl17 0.0; hands-on-head flail at fl01 1.25.
   - *Test:* |vz| is 2 m/s or less over the final 2 m, and no crouch or flail frames appear.

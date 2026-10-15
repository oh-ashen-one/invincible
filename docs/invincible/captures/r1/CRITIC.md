# CRITIC — Invincible flight suite r1 (blind, pixels + raw telemetry only)

Evidence: 17 clips (1920x1080/60), contact sheets, my own ffmpeg extractions (bursts, crops, per-frame
`signalstats` luminance), and per-frame telemetry columns (positions, `hero_occl`, `hero_bbox_h`,
`anim_node`, `pose_sig`, `body_pitch_deg`). I recomputed actual speed from x/y/z deltas rather than trusting
`speed_mps`. CHECK.json marks all 17 cases PASS; the pixels contradict that in 11 cases. The gates miss
occlusion (`hero_occl`=1.0 counted as "in frame"), dark/inside-geometry frames, and frozen positions.

## 1. Overall verdict: **FAILS TARGET**

| Axis | Score /10 |
|---|---|
| Silhouette & poses | 3 |
| Suit / character read | 5 |
| Camera | 2 |
| Speed & impact | 3 |
| Destruction / FX | 2 |
| Glitches (10 = none) | 2 |

Lowest: **2** (camera, destruction/FX, glitches).

What this is today: a smooth, unmuscled mannequin seen mostly from behind and below (a blue bean with a yellow
yoke). It flies in rigid poses, freezes against walls, vanishes inside geometry, and smashes into untextured
cubes, flat black decals and opaque discs. Colour blocking is the only part that is on target: yellow torso,
blue limbs, black belt, dark hair, no cape. The goggles are never readable because no clip shows the face; only
a thin side strap is visible (fl12 5.5 s). An unproven read fails.

## 2. Per case

**fl01 takeoff_hover — FAIL**
- 0.00 s: bind A-pose frame (`anim_node`=None, frame 0). This happens in all 17 clips.
- 0.47–0.98 s: the hero starts in a Spider-Man frog crouch (`perchIdle`) and is hidden behind pedestrians
  (`hero_occl` ≥0.9 for 16 frames).
- 1.5–10.5 s: the hover is a stiff upright stand. Legs are straight and together and the arms are held a little
  away from the body. The strafes show no lean in the pixels.
- **11.15–12.05 s: the touchdown, which is the point of the shot, is invisible.** The camera sits low behind the
  red TKTS steps, which fill the bottom 60% of the frame (frame at 11.6 s). `hero_occl`=1.0 for 52
  consecutive frames, yet the gate reports "off-screen 0".

**fl02 takeoff_to_fly — FAIL**
- 0.47–0.98 s: frog crouch, then the hero is occluded by pedestrians.
- 4.58–9.87 s: there are **7 breaches in 5.3 s** at a constant z=35 m. The shot asks for a climbing fly line
  that levels out. What it shows is a chain of building impacts, with speed spiking to 141–145 m/s on each one.
- Mean luma YAVG falls below 30/255 (near-black) at 4.62, 5.98–6.08, 8.88 and 9.73 s. At 8.79 s
  `cam_in_geometry`=1 and `hero_bbox_h`=0.90, which means the camera is inside the hero or the wall.
- 5.90 s: a large dark disc fills the upper-left third of the frame.
- 9.17 s: the camera is buried in a fire escape and the frame is a black smear.
- 5.85–6.0 s: `height_above_floor` drops from 34 m to 12.8 m while z stays fixed. The hero is inside a building.

**fl03 cruise_hands_off — MINOR**
- The altitude hold works: z is 60.0→60.0 m and the actual speed is 55 m/s.
- 0.0–0.2 s: A-pose at frame 0, then the camera pops back. `cam_hero_dist` goes 3.07→5.41 m and the hero's
  height in frame drops from 0.51 to 0.24 of the screen.
- 2–10 s: the pose never changes. Every `pose_sig` limb component moves by ≤0.134 m over 8 s. The camera sits
  about 3 m behind and below the feet, so the frame is dominated by buttocks and legs. The head is a small black
  dome and there is no readable "superman line" (crop at 3/6/9.5 s).

**fl04 boost_sonic — FAIL**
- 1.7–2.3 s: telemetry logs the boom (`fl_boom_k` 0.78 at 1.80 s, booms=1). **There is no visible boom in any
  frame**: no shock ring, no vapour cone, no flash or distortion (8-frame burst across 1.6–2.4 s plus 5 hero
  crops).
- The only speed cues are FOV going 60→72° and full motion blur.
- 3–8 s: rear view of a static butt-and-legs bean (`pose_sig` range ≤0.135 m). The head is not visible at all in
  the 1.65–2.1 s crops.

**fl05 bank_turns — FAIL**
- 2.0–7.6 s: the bank does reach ±70°. The body rolls as one rigid block, and the arm and leg poses are
  identical between 3.2, 4.4 and 6.0 s.
- At 7.2→7.6 s the bank snaps from -70° to -8° (62° in 0.4 s).
- 8.6–9.3 s: an unrequested breach through a rooftop structure at 70 m (`height_above_floor` 6.2 m). Then the
  camera whips through four viewpoints in about 0.6 s: inside the bulkhead (8.6), a high top-down shot with the
  hero about 40 px tall (8.8), a ~45° rolled dark frame (9.0), and a far wide shot (9.1).

**fl06 look_steer — MINOR**
- The heading change works (90°).
- The pose is identical and rigid throughout, the hero reads as a rear-view bean, and the 70° bank looks like a
  rotated statue (2.8–3.6 s).

**fl07 climb_dive_keys — MINOR**
- The climb works: z 70→125 m between 2.0 and 4.5 s, then a dive back to 84 m.
- The body barely visibly pitches into the line; the hero stays near-upright in the 2.5–4.0 s frames. Rigid
  pose throughout.

**fl08 brake — MINOR**
- 3.45–3.75 s: the stop reads well. Speed goes 55→0 in about 0.25 s and the arms fling out.
- 4–8 s: the hover is the same stiff stand with the arms slightly out. It is a mannequin, not a hero holding
  station.

**fl09 dash — FAIL**
- 1.5 s: the dash-right pose is a good horizontal line.
- **2.15–3.05 s (about 54 frames): the hero is gone.** The dash ends inside a billboard or building. The camera
  stares at a dark blurred wall filling about 70% of the frame, and debris cubes spawn with breaches=0.
- 3.1 s: the hero reappears through the wall on the dash left.
- The gate reports 0 off-screen frames, although `hero_occl` is ≥0.9 from 2.18 to 2.55 s and ≥0.5 until 2.95 s.

**fl10 slow_flight — FAIL**
- 1.0–2.4 s: slow flight runs straight into a facade.
- **2.42–7.10 s: the hero is frozen in place.** Displacement is 0.08 m in 4.7 s, while `speed_mps` keeps
  reporting 19.24.
- During the freeze, body pitch swings between 50° and 75° on a ~1.2 s cycle. The pixels flip between a
  horizontal sprawl against the brick and an upright reach, which reads as a Spider-Man wall cling.

**fl11 slam_crater — FAIL**
- 1.6–2.2 s: the "slam" is an upright falling stand with one arm raised, not a fist-first dive (2.25 s).
- 2.25–2.75 s: a black pole and two pedestrians sit between the camera and the impact. The hero is a few dozen
  pixels tall behind them.
- 2.35 s: the impact flash is a flat opaque white disc, and the pedestrians stand inside it with no reaction.
- 2.45–2.75 s: the hero's legs render as washed-out, see-through white (they look submerged in dust).
- 2.75–3.3 s: a one-knee landing pose shows briefly. It then pops into the frog crouch (`perchIdle`, from
  3.4 s), which is held to the end of the clip at 7.05 s.
- **No crater is visible**: in the 4.0 s crop the asphalt is uniformly dark, with no rim, cracks or depression.
- A large unlit black panel fills the right third of the frame.

**fl12 fast_land — FAIL**
- 1.0–3.5 s: the "steep fast dive" happens at cruise speed (actual max 55 m/s), so it is no faster than flight.
  The hero is pinned near the top edge (`hero_cy` 0.20–0.21) and seen legs-first.
- 3.6–3.75 s: the impact is an opaque beige hemisphere with visibly stamped, repeating smoke-puff sprites.
- 5.5 s: the crater is a flat, uniform dark-grey disc decal with no depth, rim or cracks. The debris is a pile of
  identical off-white untextured cubes.
- 5.0–8.0 s: frog crouch held for 3 s.
- 4.4–5.8 s: a van and a box truck drive past the impact zone and over the debris without reacting.

**fl13 soft_land_walk — MINOR**
- The touchdown, walk (about 6.9–9 s) and re-takeoff (from 9.6 s) all work.
- 3.4–6.2 s: the hero rests for 2.8 s in an off-model Spider-Man frog squat with the knees splayed flat (4.5 s).
- 2.0–2.8 s: a lamppost occludes the hero.
- 6.2–6.9 s: a pedestrian walking into the camera covers about 25% of the frame.

**fl14 breach_cruise — FAIL**
- 2.2 s: the hero lies prone, scraping along a cornice, before the "breach".
- 2.35–2.5 s: the camera is pressed against or inside the facade.
- **2.65 s: an untextured salmon-coloured cube fills the entire frame.**
- 3.04 s: the breach hole is a perfect black dome or sphere. It reads as a black ball, not broken masonry.
- 2.8–3.25 s: the hero stands upright on a roof among cubes and dust sprites instead of flying through.
- At 2.99 s the hero is dead-stopped mid-air (v=0.005) after the breach.
- **5.6–8.1 s: frozen on a glass curtain wall** (v=0.007, position constant) in a one-arm-up wall-cling pose. The
  clip ends stuck there.

**fl15 breach_boost — FAIL**
- 3.2–3.9 s: the hero skids crouched across a dark rooftop instead of punching through.
- At 5.22 s `hero_bbox_h`=1.85, so the hero fills the frame.
- 6.49–6.68 s: dead stop on a brick facade (v=0.007) in a Spider-Man climbing pose, with huge flesh-coloured
  cubes floating next to the camera.
- **6.86 s: the "breach hole" is a flat black ellipse decal stamped on an intact brick wall.**
- 7.05 s: hard camera jump to a top-down view about 30 m out (`cam_hero_dist` 5.5→9.2 m), with the hero about
  40 px tall at the bottom of the frame.
- Five breaches, but none reads as a hole torn through a building.

**fl16 slow_facade_slide — FAIL**
- **2.48–7.32 s: there is no slide.** The hero is frozen: y moves 519.578→519.656 m (0.08 m) while `speed_mps`
  reads 19.24.
- The body oscillates between 50° and 75° pitch on a ~1.2 s cycle against the brick. In the pixels this flips
  between a sprawl and an upright reach.
- This is the same stuck behaviour as fl10, with the same pitch sequence.

**fl17 rescue_crane — FAIL**
- **0.00–4.38 s (264 frames, 22% of the clip): the screen is a near-black interior** (YAVG about 31/255
  throughout) and the hero cannot be seen. Telemetry says in-frame and not in geometry; `hero_occl`=1.0.
- 7.7 and 11.6 s: "climb over roofs" turns into two breaches.
- 12.9 and 14.1 s: the crane boom is a flat untextured yellow slab cutting across the camera.
- 14.4–15.3 s: the load is an untextured grey box. The hero hovers above it in the standard stand, hands at his
  sides, and never grabs it.
- The `lives_saved` counter jumps 0→5 at 14.63 s with no catch shown.
- 15.2 s: the HUD prompts "SET IT DOWN". The hero then holds z=134.30 m from 15.4 s to the end at 20.2 s, so the
  load is never set down.
- From 16.3 s the box has disappeared from frame. Neither the carry nor the set-down happens.

**HUD (all clips):** the top-left HUD text is about 12 px tall at 1080p, with a grey-on-dark low-contrast
"COLLATERAL" bar. It cannot be read at normal viewing distance.

## 3. TOP 8 defects (most damaging first)

1. **The hero disappears into geometry or darkness, and the gates are blind to it.**
   - Evidence: fl17 0–4.38 s, fl01 11.15–12.05 s, fl09 2.15–3.05 s, fl02 YAVG<30 at 4.62/5.98–6.08/8.88/9.73 s,
     fl05 8.6–9.3 s.
   - *Acceptance test:* in every clip, no run of more than 6 frames with `hero_occl` ≥0.9, and no frame with
     mean luma below 40/255 except inside a ≤0.25 s breach window. fl17 at 1.0 s must show the hero standing on
     a lit street at ≥15% of frame height.
   - The gate must count `hero_occl` ≥0.9 as off-screen.
2. **Touching a facade freezes the hero while telemetry keeps reporting speed.**
   - Evidence: fl10 2.42–7.10 s and fl16 2.48–7.32 s (0.08 m moved, `speed_mps` 19.24); fl14 5.6–8.1 s and fl15
     6.5 s (v=0.007).
   - *Acceptance test:* in fl16, displacement along the facade is ≥0.5× the commanded speed for every 0.5 s
     window. Body pitch varies by ≤10° while the hero is in contact. Background windows visibly scroll between
     the 3.0 and 5.0 s frames.
3. **Destruction is built from primitives.** It shows untextured flat-colour cubes and spheres, a flat black
   ellipse "hole" on an intact wall (fl15 6.86 s), a black dome hole (fl14 3.04 s) and a cube filling the camera
   (fl14 2.65 s).
   - *Acceptance test:* 0.3 s after a breach, the frame shows a jagged opening with lit interior or floor slabs
     visible through it. Debris chunks carry the facade's own texture, and no single debris piece covers more
     than 15% of the frame.
4. **The rescue is not shown** (fl17 14.4–20.2 s): no grab, no carry, no set-down, and the load vanishes at
   16.3 s.
   - *Acceptance test:* between the catch and the end, the hero's hands touch the textured load in every frame,
     with the arms under or around it. z then descends to a roof or street, and the last frame shows the load
     resting on that surface with the hero beside it.
5. **The sonic boom is invisible** (fl04 1.7–2.3 s; telemetry `fl_boom_k` 0.78).
   - *Acceptance test:* the frames at boom ±0.1 s show a ring or cone ≥25% of frame width centred on the hero,
     plus a visible flash or air distortion, clearly different from the frame at boom −0.5 s.
6. **The flight silhouette is a rear-view blob, and poses are static and rigid.**
   - Evidence: fl03 and fl04 rear crops; `pose_sig` range ≤0.134 m over 8 s; banks are a rotated statue (fl05
     3.2/4.4/6.0 s); a stiff hover stand in all hover clips.
   - *Acceptance test:* at cruise, the camera sits ≥15° above and offset to the side of the hero's spine, and the
     head plus both arms are readable in ≥90% of frames. Limb `pose_sig` varies by ≥0.25 m over any 4 s of
     cruise. Banks show the outer arm and leg spread differently from level flight.
7. **Landings are off-model and the impact is fake.**
   - Evidence: Spider-Man frog squat held for 3–4 s (fl11 3.4–7.05 s, fl12 5.0–8.0 s, fl13 3.4–6.2 s); the
     crater is a flat dark disc or invisible (fl12 5.5 s, fl11 4.0 s); opaque white or beige flash discs (fl11
     2.35 s, fl12 3.6 s); pedestrians and traffic ignore the impact (fl11 2.35 s, fl12 4.8–5.8 s); the slam is an
     upright fall (fl11 2.25 s).
   - *Acceptance test:* the frame 1.0 s after impact shows a one-knee-and-fist superhero landing, then an upright
     heroic stand, never the knees-splayed squat. The crater has a raised cracked rim and visible depth (shading
     gradient), with no opaque disc covering more than 5% of the frame. Pedestrians within 10 m flee or fall.
8. **Start-of-clip and scripting glitches.**
   - Bind A-pose at frame 0 in all 17 clips, followed by a camera pop (fl03: `cam_hero_dist` 3.07→5.41 m in
     0.2 s).
   - Unrequested breaches in non-breach shots: fl02 has 7, fl05 one at 8.79 s, fl17 two.
   - The fast-land dive is no faster than cruise (fl12, 55 m/s).
   - *Acceptance test:* frame 0 has a valid animation pose, and the hero's height in frame changes by <15%
     across the first 0.5 s. fl02, fl05 and fl17 log breaches=0. The fl12 dive reaches ≥90 m/s before impact.

Single biggest gap (builder instruction): make visibility and occlusion a hard pixel gate and fix the cases it
exposes. Count any frame with `hero_occl` ≥0.9 or mean luma below 40/255 as off-screen. Fail the case on any run
over 6 frames outside a ≤0.25 s breach window. Then re-capture so that fl17 0–4.38 s, fl01 11.15–12.05 s and fl09
2.15–3.05 s show the hero lit and unoccluded at ≥15% of frame height.

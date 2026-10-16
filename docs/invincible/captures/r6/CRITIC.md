# r6 flight suite: blind critic report

What I used: only the 17 clips, the contact sheets, the per-frame telemetry CSVs and the ffmpeg frame extracts I pulled myself at the times quoted below. Times are clip seconds. Pixel positions are in the 1920x1080 source frame. I read no builder text.

## 1. Verdict: **FAILS TARGET**

| axis | score |
|---|---|
| silhouette & poses | 5 |
| animation quality | 3 |
| suit / character read | 6 |
| camera | 3 |
| speed & impact | 5 |
| destruction / FX | 3 |
| glitches (10 = none) | 2 |

What works: the cruise and fly line read well, with a horizontal superman pose, one fist forward and ~280 px tall in fl03. The fl11 slam (head-first dive, flip to feet, three-point landing, cracked crater, dust) is the best shot in the set. Banking and climbing read clearly.

What fails: every breach is a camera freeze followed by a teleport jump cut. The rescue clips the hero through the container and a taxi. The hover is lifeless. The boost "ring" in fl04 is a haze disc, and the hero snaps from the charge pose into flight in one frame. The camera passes through a truck and is blocked by pedestrians.

## 2. Per case

- **fl01 MINOR.** At takeoff the camera loses the hero off the bottom of the frame for 4 frames (1.017–1.067, telemetry `hero_in_frame=0`; at 1.083 the crouch is cut off at the bottom edge). The arms-overhead takeoff pose comes back mid-climb at 3.5 s, long after takeoff ended at 1.40. Touchdown has no knee absorption: he goes from a dangling hover at 10.9 straight to a locked stand at 11.05.
- **fl02 MINOR.** Same 4-frame takeoff loss (1.017–1.067). The climbing fist-forward pose is good. The dark squiggle at 2.5 s is a fire escape, not an artifact.
- **fl03 PASS.** Cruise pose holds from 2.5 to 9.8 s with small leg variation. The framing is dominated by the butt and boot soles (head ~40 px out of ~280 px).
- **fl04 FAIL.**
  - One-frame pose pop at the boom: upright charge pose at 1.450, full horizontal flight at 1.467.
  - The "ring" is a soft filled disc, not a ring. On column x=980–1020 at 1.517, luma is lifted uniformly from 58–127 (at 1.40) to 131–173, with no edge peak.
  - The charge (1.38–1.45) is just a hunched hover, with no build-up effect.
  - The speed lines are flat, uniform grey bars.
- **fl05 MINOR.** The camera rolls hard in the banks (horizon visibly tilted in sheet tiles 3 and 5). In the profile bank the knees are bent ~90°, which breaks the streamlined superman line.
- **fl06 MINOR.** The top-left HUD text is smeared or doubled (sheet tile 2). Otherwise fine.
- **fl07 PASS.**
- **fl08 FAIL (hover).** The brake is quick (horizontal at 3.45, upright by 3.75), but there is no braking flare. In the hover from 5.4 to 8.0 the torso's yellow-pixel centroid moves 2.0 px in total (244.0→242.7→244.1) on a ~520 px hero: no bob and no breathing. The capsule z is a constant 60.000. The hands are open blue paddles, not fists, and the legs dangle with toes pointed (crop at 5.5, x 780–1140).
- **fl09 MINOR.** The dash has a lean pose but no effect. A billboard fills the whole background from 2.95 to 3.05.
- **fl10 MINOR.** The camera looks straight into a brick facade that fills the frame around 1.0 s (`wall_frac` 0.38 at 1.5 s).
- **fl11 MINOR.** Good dive and landing (impact at 2.25 s). The rubble is uniform grey cubes. He then stands static for ~2.5 s (4.5–7.0).
- **fl12 FAIL.**
  - The camera slices through a white box truck from 2.700 to 2.733 (truck body cut open, pole through the frame).
  - The landing at 2.75–2.80 is a spread-eagle splat, not a three-point landing.
  - A grey debris cube floats in or clips through the pickup bed at 3.1–3.4.
  - The pickup, ~1 m from the crater, does not react.
  - From 4 to 8 s a box truck fills ~40% of the frame on the right.
- **fl13 MINOR.** He moves at 9.8 m/s on the ground (telemetry 7.33–8.93) with a walk-style stride. Takeoff loses the hero for 4 frames (9.517–9.567). Traffic passes within about 1 m of the camera.
- **fl14 FAIL.** Five breaches in 8 s. On each one the camera freezes while the hero jumps 17–26 m through the building in 3–4 frames, then the camera teleports 24–31 m.
  - At 4.946→4.962 the camera yaw jumps from −14.5° to 79.7° in one frame.
  - The building interior is never shown; the breach reads as a black crack decal plus a hard cut (5.00→5.04).
  - He flies belly-down on roof gravel at 5.28.
  - At 8.1 he is cut off at the top of the frame, with only a leg visible.
- **fl15 FAIL.**
  - The camera steps 77.9 m in one frame (3.853→3.870).
  - At 4.00 the hero bbox height is 2.66 frame heights, i.e. the camera is inside the hero.
  - The camera clips through a round tower at 4.43–4.48.
  - The boost overshoots the city, crosses the river and ends at 10.15 on a small hole in a bridge girder with the hero absent. No city block is visibly breached.
- **fl16 MINOR.** He skims ~0.5 m over roof gravel at 5.6–5.9, which reads as lying on the roof. The roof boxes are untextured black.
- **fl17 FAIL.**
  - Two pedestrians hide the hero for 29 frames (0.650–1.117).
  - The takeoff is a jump cut: the hero moves from x≈260 to x≈785 of the 640 px thumbnail between 3.30 and 3.35.
  - He breaches a glass tower he wasn't aiming at (12.88), and it spits brick debris (12.9).
  - The catch at 17.35–17.65: legs inside the container, arms in a T.
  - The hold reads as hanging limp, not lifting.
  - The container passes through the tree canopy at 31.2.
  - From 32.9 to 36.2 the hero's side merges into the taxi door (`hero_occl` 0.33–0.38 from 31.95 to the end).

## 3. Top 8 defects (ranked)

1. **Breach is a jump cut** (fl14 4.91–4.96, 6.16–6.23; fl15 3.79–3.87; fl17 12.88–12.92): the camera freezes, then steps 24–78 m and up to 94° of yaw in one frame. *Test:* in every breach, camera step ≤ 3 m and ≤ 6° per frame; hero visible in ≥ 80% of breach frames; both the entry and exit holes appear on screen.
2. **Rescue interpenetration** (fl17 17.35–17.65 container, 32.9–36.2 taxi). *Test:* zero mesh overlap between the hero and the container or any vehicle; hands touch the container's underside; `hero_occl` ≤ 0.10 for the last 2 s.
3. **Lifeless hover** (fl08: 2 px over 2.6 s, open hands). *Test:* torso centroid oscillates 8–20 px at 0.3–0.6 Hz, and both fists are visibly clenched in a crop.
4. **Boost pop and haze disc** (fl04: 1.450→1.467 pose pop; flat luma at 1.517). *Test:* hero bbox aspect changes ≤ 25% per frame; within boom +2 to +10 frames, a radial luma profile shows an annulus edge ≥ 40 above the interior.
5. **Camera inside geometry** (fl12 2.700–2.733 box truck; fl15 4.43–4.48 tower and 4.00 inside the hero). *Test:* camera never inside a vehicle, building or hero bounds; hero bbox ≤ 1.0 frame height.
6. **fl12 splat landing and no vehicle reaction** (2.75–2.80; pickup at 3.1). *Test:* a three-point pose (knee plus fist on the ground) held ≥ 0.4 s; vehicles within 10 m are displaced or damaged; no floating debris.
7. **Occlusion and framing**: pedestrians at fl17 0.65–1.12, truck covering 40% in fl12 4–8 s, 4-frame takeoff loss in fl01/02/13, takeoff cut at fl17 3.30→3.35. *Test:* hero hidden ≤ 6 consecutive frames; no foreground object > 25% of the frame for > 1 s; no camera step > 1 m per frame at takeoff.
8. **Destruction fidelity**: a glass tower spawns bricks (fl17 12.9); breach holes are crack decals with no interior (fl14 4.98, fl15 10.15); fl15 never hits a block. *Test:* debris material matches the surface it came from; the hole is ≥ the hero's silhouette with interior visible; fl15 visibly breaches a building inside the city.

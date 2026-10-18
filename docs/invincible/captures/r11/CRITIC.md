# r11 flight suite — independent blind critique

Evidence used: 18 clips (1080p60), the contact sheets, ffmpeg frame/burst extracts and crops, `*_telemetry.csv` (camera yaw/pitch/distance, hero bbox, occlusion, sub-state), `*_luma.txt`. I read no builder text. Times are clip seconds; px values are in 1920x1080 frame space unless noted.

## 1. Verdict: **FAILS TARGET**

| axis | score |
|---|---|
| Silhouette & poses | 4 |
| Animation quality | 4 |
| Suit / character read | 6 |
| Camera | 2 |
| Speed & impact | 5 |
| Destruction / FX | 4 |
| Glitches (10 = none) | 3 |

What works: the sonic boost charge bubble, bright ring and speed lines (fl04 1.0–1.6 s); the instant brake (fl08: 55 → 0.83 m/s between 3.483 and 3.633 s); the ~0.45 m float gap after landings (fl11/fl13/fl17 height_above_floor 0.45); steady chase-camera yaw in straight cruise (≤1.5°/frame in fl01–fl08 and fl11/fl13/fl18).

What fails: the camera breaks down in landings and close-to-geometry moments, the poses are not heroic (A-pose open-hand hover, kneeling bent-knee flight, curled-ball boost), the superhero landings are hidden or are not three-point, and the destruction reads as flat decals and plain cubes.

## 2. Per-case

- **fl01 takeoff_hover — MINOR.** Hover pose is a rigid A-pose: arms straight down and slightly out, hands open, legs locked together (sheet tiles 1, 7, 8). There are no fists. The bob is animation only: px_top moves 328–352 (24 px on a ~450 px figure) while z is frozen.
- **fl02 takeoff_to_fly — MINOR.** In the fly phase, camera yaw sits a median 16° (p90 17°) off the velocity heading. The hero crabs diagonally across the frame instead of reading from behind. The flight pose has knees bent about 90°.
- **fl03 cruise_hands_off — MINOR.** Same 17° heading offset and the same kneeling flight pose. The silhouette never becomes a straight superman line.
- **fl04 boost_sonic — MINOR.** Charge bubble → ring → speed lines all read well at 1.0–1.6 s. Luma jumps 9.6/frame at the boom. After the boost (sheet tiles 6–8) the legs fold back into the kneel. At ~6 s the camera skims a glass facade.
- **fl05 bank_turns — MINOR.** The banks read. At ~4 s the hero shrinks to about 0.20 of frame height in sun glare.
- **fl06 look_steer — MINOR.** At the end (sheet tile 8) a building wall covers the left third of the frame and the hero is pushed to the right edge.
- **fl07 climb_dive_keys — MINOR.** The climb and dive read. The pose problems are the same as fl02.
- **fl08 brake — MINOR.** The brake is instant and good. The hover after it is the A-pose; px_top moves 180–196 with z fixed at 60.000.
- **fl09 dash — MINOR.** Hero centre x jumps 124 px in one frame at 1.55 s, and camera yaw steps 3.0°/frame at 1.517 s. Around 3.4 s a billboard fills about half the frame (sheet tile 4).
- **fl10 slow_flight — FAIL.** Camera yaw swings from −97° to +9° (106°) in 0.8–1.0 s. At 1.00 s a brick facade fills 100% of the frame with the camera square to the wall. The hero kneels sideways across it, knees about 90°. Hero centre x jumps 132 px at 0.367 s.
- **fl11 slam_crater — MINOR.** Speed goes from 94 m/s to 0 in one sample (2.17 → 2.42 s), so impact is there. The landing (2.45 s crop) is a kneel with the right fist raised overhead and no hand planted, so it is not a three-point landing. The crater is a flat black decal with crack lines: no rim, depth or displaced asphalt. Debris is a few uniform cuboids.
- **fl12 fast_land — FAIL.** Camera pinballs during landHero (2.65–3.95 s). 102 frames turn faster than 3°/frame. Yaw moves −52 → +98° between 2.77 and 2.92 s, jumps +73 → −73° at 3.27 s, and cuts 126° in one frame at 3.587 s. At 3.57 s pitch snaps to −80°, a straight-down view (6-frame burst from 3.55 s). The box truck fills about 60% of the frame at 2.75 and 3.05 s. Hero centre jumps 448 px at 3.287 s. The mechanical gate also fails: 41 frames off-screen, longest run 13. Fly-out at 4.25 s is at 0.9 m height among parked trucks. The truck takes no damage.
- **fl18 roof_hero_land — FAIL.** The hero is more than 50% occluded for 54 frames (2.167–3.433 s), which is the whole landHero window (2.15–3.45 s). At the 2.5 s crop the parapet hides the legs and planted hand; only the torso and raised fist show. The roof crater is mostly hidden, and the debris is beige cubes.
- **fl13 soft_land_walk — MINOR.** Float 0.45 m, heading offset 3°, smooth. The glide along the street is the stiff upright A-pose with no lean into the travel direction.
- **fl14 breach_cruise — FAIL.** The object breached at 4.333 s is a giant lipstick billboard, not a facade (burst from 4.1 s). The billboard fills about 60% of the frame at 4.37 s. After an 8-frame breach (4.333–4.466 s, one dust card and about 5 brown chunks) it is simply gone: no hole, no remains. The camera is inside geometry at 4.40 and 4.48 s. Luma dips to 45.0 at 5.03 s, a 47.2/frame swing.
- **fl15 breach_boost — FAIL.** While boosting at about 300 m/s (sheet tiles 6–8, 7.5 s) the hero is curled into a knees-to-chest ball, not superman-straight. The camera is inside geometry for 5 frames (4.22, 4.44, 5.25 … 8.45 s). At about 8.45 s glass mullions are drawn across the hero. A near-black frame shows at 4.03 s (YAVG 32.2). The breaches are again a dust card plus black slab debris.
- **fl16 slow_facade_slide — MINOR.** Camera yaw steps 24.9° in one frame at 0.383 s, and the hero is off-frame on that frame. Hero centre jumps 128 px at 0.333 s. The slide along the facade itself is acceptable.
- **fl17 rescue_crane — FAIL.** During the carry and descent (28.5–32.5 s, 1 fps burst) the crane load is cut off by the top frame edge: only its underside occupies y≈0–40 px, while the hero's px_top is about 256–268. The object being rescued is never framed. Hero centre jumps 342 px at 12.95 s, and camera yaw steps 4.4° at 12.93 s, through the breach. Luma drops to 38.8 at 13.27 s, a 52.8/frame swing. The load is set down tight between parked cars. Positives: float 0.45 m at the start and end, and a readable overhead hold.

## 3. Top 8 defects (ranked)

1. **Landing camera pinball (fl12 2.65–3.95 s).** Yaw cuts 126° in one frame at 3.587 s, pitch snaps to −80° at 3.57 s, and 102 frames exceed 3°/frame. *Test:* in fl12, no frame-to-frame yaw change above 3°, pitch stays within −45°, and hero centre moves less than 60 px per frame across the whole landHero.
2. **Superhero landings unseen or wrong (fl18 2.17–3.43 s at ≥50% occlusion; fl11 2.45 s arm-up kneel).** *Test:* during landHero, hero_occl stays at or below 0.2 on every frame. A crop at impact +0.2 s shows one knee down, one foot planted and one hand flat on the ground, all inside the frame.
3. **Camera pressed into or square to walls (fl10 1.00 s facade fills 100%; fl14 4.40 s and fl15 8.45 s camera in geometry; fl09 ~3.4 s billboard).** *Test:* cam_in_geometry is 0 on all frames. No frame has more than 50% of its pixels covered by one surface within 2 m of the camera. Yaw changes less than 40° in any 0.5 s window in fl10.
4. **Flight and boost poses not heroic (knees about 90° in fl02/03/10; curled ball in fl15 7.5 s).** *Test:* at 2 s, 5 s and 8 s in fl03 and at 7.5 s in fl15, a crop shows knees within 20° of straight and the body within 25° of the velocity line, with fists leading.
5. **Rescue load cropped out of frame (fl17 28.5–32.5 s).** *Test:* the entire load bbox sits at y ≥ 40 px and at least 80 px inside all edges on every carry and descent frame.
6. **Breach target vanishes with no hole (fl14 billboard 4.37 → 4.47 s; fl15 slabs).** *Test:* fl14 hits a facade. A frame 1 s after the breach, looking back, shows a hole with jagged edges and interior lighting, and the struck object still exists.
7. **Crater is a flat decal (fl11 2.45 s, fl12 3.05 s).** *Test:* a grazing-angle frame shows a raised rim and depth shading, with at least 12 debris pieces of varied shape (not cubes). The parked truck in fl12 shows a visible dent or displacement.
8. **Hover is a stiff open-hand A-pose (fl01, fl08, fl13; bob only ±8 px with z frozen).** *Test:* crops at three hover times show closed fists, bent elbows and staggered knees. The body bob is at least 20 px peak-to-peak on a ~450 px figure, with a visible 2–4 s breathing cycle.

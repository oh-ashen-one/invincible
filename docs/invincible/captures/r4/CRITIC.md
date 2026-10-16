# r4 flight suite: independent blind critique

What I looked at: the 17 contact sheets, about 60 frame bursts and crops pulled from the mp4s with ffmpeg, OpenCV per-frame luma, luma standard deviation (sd) and hero-colour pixel counts inside the telemetry bounding box, telemetry CSVs, and CHECK.json values.
What I did not read: builder notes, the README, RUN.json, source code and other critiques.
Times are clip seconds. Pixel figures are at 1920x1080.

## 1. Verdict: **FAILS TARGET**

| axis | score |
|---|---|
| silhouette & poses | 4 |
| animation quality | 3 |
| suit/character read | 6 |
| camera | 4 |
| speed & impact | 4 |
| destruction/FX | 3 |
| glitches (10 = none) | 3 |

**Lowest score: 3** (animation quality, destruction/FX, glitches).

The colours of the suit read as Invincible. From behind, the cruise pose with both fists forward reads as a superman line (fl06 9.3 s). The rest falls short of AAA:
- Every hover-to-fly transition passes through a T-pose.
- The brake ends lying horizontal in mid-air.
- The slam dives head-first and snaps into the landing.
- The sonic boom is a set of flat screen-facing discs, and during it the hero shrinks to about 12 px.
- Each payoff moment (crater, landing) is hidden by roughly 1 s of dust whiteout.
- The rescue never shows the hero carrying the load overhead.

## 2. Per-case results

- **fl01 FAIL.** The takeoff has no anticipation: vz goes from 0 to 16.0 m/s in one frame (0.983 to 1.000 s), with no crouch and no ground FX (frames 0.85 to 1.09). The touchdown also stops in one frame, from 2.08 m/s to 0 (11.117 to 11.133 s), with no knee compression. The hero then lands in a live traffic lane.
- **fl02 MINOR.** He climbs while grazing facades; at 2.8 s the fire escape overlaps his boots. The hero bounding box drops to 0.125 of frame height (135 px), parked in the right third of the frame. From 5.5 s on, the side-view fly line is good.
- **fl03 MINOR.** At 0.20 to 0.33 s there is a T-pose: arms straight out sideways while the camera pulls back from 2.79 m to 5.58 m, and the hero shrinks from 0.608 to 0.145 of frame height in 0.4 s. The same artefact appears at the start of fl03 to fl12, fl14 and fl16. During the cruise the silhouette is frozen: height stays between 0.274 and 0.290 over 2.0 to 9.5 s, with no secondary motion, and the hands are open rather than fists.
- **fl04 FAIL.**
  - The charge hang (1.00 to 1.42 s) is fine.
  - At launch, speed goes from 0.1 to 243 m/s in one 3-frame step.
  - The camera yo-yos: hero distance goes 3.2 → 24.2 m (1.55 s) → 3.56 m (1.75 s), and pitch swings from −21.8° to −2.6° and back.
  - The hero is 12 to 30 px tall from 1.45 to 1.70 s, and the blue hero-pixel count is 0 from 1.45 to 1.85 s.
  - The frame washes out: Y 184.5 with sd 18.2 at 1.50 s, and Y 173 with sd 17 at 1.75 s.
  - The boom is concentric flat screen-facing discs, not a cone. The trail is a hard-edged white slab running to the bottom-left corner (2.5 to 3.3 s).
- **fl05 MINOR.** The bank and camera roll read well. The pose flips between upright with one arm raised (3.2 to 4.3 s) and horizontal (5.4 s). The legs dangle with bent knees.
- **fl06 MINOR.** A tower fills the left third of the frame from 5.5 to 7.3 s, and the camera skims building edges (3.25 to 3.7 s). The fists-forward pose at 9.3 s is the best frame in the suite.
- **fl07 FAIL.** The body pitch ignores the flight path. With a climb at vz +27.4 (2.5 s, path about +30°) and a dive at vz −28.9 (6.5 s, path about −30°), body_pitch only moves between −83.4° and −77.9°. Visually, the climb and the dive show the same pose.
- **fl08 FAIL.** The stop itself is instant (55 → 0.1 m/s from 3.45 to 3.70 s). After that the hero floats lying horizontally on his side until about 4.9 s, which is 1.2 s of plank pose labelled `hover`. There is no brake FX.
- **fl09 FAIL.** During the dash at 1.55 to 1.60 s he is spread-eagled in a T-pose with open hands. From 1.80 to 1.95 s he snaps from horizontal to upright, about 90° in 0.15 s (≈600°/s). The camera yaws 126°/s. There is no dash FX: no streak and no burst.
- **fl10 MINOR.** The camera hugs a brick wall at about 1 m (0.68 to 2.58 s). The yaw whips 8.5° per frame (0.43 to 0.52 s). At 4 m/s he uses the same pose as at 55 m/s, and the legs look like kneeling (4.48 s).
- **fl11 FAIL.**
  - He dives head-first, feet up, until 2.25 s at z ≈ 3 m. At 2.28 s he is crouched: a 180° pose snap within about 2 frames.
  - At 2.33 to 2.37 s an opaque flat white elliptical disc covers 160k to 273k pixels, spanning 1,600 px wide.
  - Dust then hides the hero's colour for 55 frames (2.32 to 3.23 s), with sd as low as 20.8.
  - The crater is a flat dark decal plus untextured cube debris. Traffic keeps driving past it (5.6 to 6.1 s).
- **fl12 FAIL.**
  - The boom repeats the flat discs, with the camera at 17.8 m and the hero 20 px tall (0.9 to 1.0 s).
  - In the dive the body pitch holds at about −62° while the path is about −36°, so he never points at the street.
  - Speed goes from 302 m/s to 0 in one frame (2.55 to 2.57 s).
  - Dust hides the hero for 26 frames (3.17 to 3.60 s), with sd 19.0.
  - The landing is a standing lunge, not a three-point landing. A car and a truck sit unbothered beside the impact.
- **fl13 MINOR.** He walks the centre line while traffic streams past (3.6 s and 8.8 s). The touchdown has no compression.
- **fl14 MINOR.** The breach holes are flat black decals with painted cracks and an unlit, depthless interior (6.75 s). At 5.55 to 5.70 s he ploughs through a rooftop box lying flat.
- **fl15 MINOR.** The holes are the same flat decals. Whole-frame radial blur smears everything (3.91 s and 4.36 s). The camera stares at a holed tower for about 0.3 s (4.72 to 4.99 s), then shows the hero over the river beside a solid white trail slab (5.08 s).
- **fl16 FAIL.** He never slides. Position is locked within 4 cm from 2.5 to 8.0 s (x 234.40 to 234.44, y 529.922, z 30.915) while move-input y = −1 is held. For 5.5 s he holds a full prone fly pose with his head and arm clipped into the fire-escape grate. The camera yaws 11.2° per frame at 0.37 s.
- **fl17 FAIL.**
  - At 16.5 s he stands on top of the yellow crane jib, and at 16.75 s the beam passes through his chest.
  - From 17.5 to 18.0 s he stands on the grey load instead of catching it overhead.
  - The load fills the screen and occludes him: hero_occl = 1 for 25 frames (18.13 to 18.53 s).
  - From 18.75 to 20.6 s he dives with empty hands while the load falls separately and lands beside him (20.8 to 21.0 s), with the hero hidden for 15 frames.
  - The load is an untextured grey box.
  - The lives-saved counter jumps to 5 at 17.61 s, mid-air at 136 m, rather than on set-down.
  - He breached a building on the way (12.85 s), and the final landing is on a terrace at 15.3 m, not the street.

## 3. Top 8 defects

1. **The rescue does not read (fl17).** He stands on the jib and the load, the jib passes through his chest, and the load falls separately from him.
   - Test: from catch to set-down, the load's screen bbox stays above the hero's head bbox with his hands in contact, he never stands on it, the beam never overlaps the hero mask, and hero_occl is ≤ 6 frames.
2. **T-pose at the start of every hover-to-fly transition** (fl03 0.20 to 0.33 s, also fl09 1.55 s).
   - Test: in every frame of the hover→fly and dash blends, each wrist stays more than 25° from the shoulder line horizontal, and a 0.033 s burst shows no arms-out frame.
3. **Sonic boom (fl04 and fl12).** Speed jumps 0 → 243 m/s in one step, the camera yo-yos 3.2 → 24 → 3.6 m, the hero is 12 px tall, the frame washes out (sd 17), and the boom is flat discs.
   - Test: camera distance stays ≤ 6 m, hero bbox height stays ≥ 0.12, frame sd stays ≥ 30, and a ring or cone is visible around the hero in at least 10 frames, opening along the travel axis.
4. **Slam (fl11).** He dives head-first, snaps 180° in 2 frames, a flat white disc covers 273k px, and he is hidden for 55 frames.
   - Test: the body flips feet-first at least 8 frames before contact, and the hero colour stays visible (≥ 1,500 px) in every frame from 2.3 to 3.3 s.
5. **Facade slide is glued (fl16).** Position moves ≤ 4 cm over 5.5 s and he is clipped into the fire escape.
   - Test: tangential speed is ≥ 3 m/s along the wall while input is held, there is no mesh penetration, and he uses a wall-push pose rather than the prone fly pose.
6. **Brake ends horizontal (fl08).** He lies on his side for 1.2 s after stopping.
   - Test: body within 20° of vertical by 0.35 s after speed drops below 1 m/s.
7. **Dust whiteouts hide every landing** (fl11 55 frames, fl12 26 frames, fl17 15 frames).
   - Test: the hero mask is never less than 60% visible, and frame sd stays ≥ 30 throughout each landing.
8. **Dead fly animation (fl03, fl07).** The silhouette varies only ±3%, body pitch ignores ±30° climb and dive, and takeoff and touchdown happen instantly.
   - Test: body pitch tracks the path angle within 10° with a lag under 0.3 s. Takeoff has a crouch of at least 6 frames, and touchdown has a knee bend of at least 20°.

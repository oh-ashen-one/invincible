# R5 flight suite — blind critic report

Evidence used: rendered frames from the clips, ffmpeg frame bursts and crops, pixel counts, `*_telemetry.csv`, `*_luma.txt`, sheets and the mechanical CHECK.md. I read no builder notes and no code.

Provenance note: partway through the review, another process replaced the 1080p `<case>.mp4` files with `<case>_540p.mp4` and gzipped the telemetry (directory mtime 01:13). The measurements for fl01 idle, fl04 crop, fl11 van, fl12 crop, fl13 face crop and fl15 panel were taken on the original 1080p frames. All other measurements were taken on the 540p copies, which have the same 60 fps frame count. Pixel coordinates are labelled 1080p or 540p.

## 1. Verdict: **FAILS TARGET**

| axis | score |
|---|---|
| silhouette & poses | 3 |
| animation quality | 2 |
| suit / character read | 5 |
| camera | 3 |
| speed & impact | 4 |
| destruction / FX | 2 |
| glitches (10 = none) | 2 |

**Lowest: animation quality (2), destruction/FX (2) and glitches (2).**

What works: the city looks good. Super-boost speed blur at 300 m/s gives a real sense of speed (fl04 2.5–8 s, fl12 1.8–2.6 s). The charge curl before the boost reads (fl04 1.10–1.42 s). The 3/4 camera-steer views in fl06 at 6.5 s are the best flight frames in the set. Everything else is below the AAA bar described below.

## 2. Per-case results

- **fl01 takeoff/hover — FAIL**
  - Speed jumps from vz 0 to 16.0 m/s in one frame (t=0.983 → 1.000). There is no crouch on the ground first.
  - The crouch plays in the air instead: z rises 1.13 → 2.73 m between t=1.00 and 1.10 while the knees are bent.
  - The hero is cut off by the bottom of the frame for 6 frames: telemetry px_bottom=1080 at t=1.017–1.083, and the frames show it.
  - Idle on the ground with a static camera (frames 40–51, 1080p): the world state alternates between frames. A grey pickup and a white box truck swap places at frames 47/48/49, and the pickup jumps back and forth on alternate frames. The mean absolute luma difference between frames 47→48→49 is 19.1 with the camera still.
  - Hover is a rigid A-pose.
- **fl02 takeoff→fly — FAIL**
  - Same takeoff defect: telemetry rows 60–65 are identical to fl01.
  - In level flight the body's long axis sits at 40° from screen horizontal at t=5.0 and 9.0 while fl_bank_deg is 0. He looks permanently rolled about 45°.
- **fl03 hands-off cruise — MINOR**
  - The pose is frozen and identical from 2.0 to 9.5 s, with no secondary motion.
  - The body axis stays at 39–48° at zero bank.
  - The hero covers only about 2.2k–3.3k yellow+blue pixels at 540p (≈0.5% of the frame).
- **fl04 boost/sonic — MINOR**
  - The charge-then-boom beat reads.
  - The "ring" is a chain of about 20 separate translucent bead blobs (t=1.48 and fl12 t=1.0). It looks like a bubble necklace, not a shock ring or cone.
  - The field of view jumps 12.9° in one frame at t=1.42.
- **fl05 bank turns — MINOR**
  - The camera roll follows the bank, which is good.
  - At t=6.5 the whole frame is smeared by blur.
  - The pose is the same one-arm figure, just rotated.
- **fl06 look steer — MINOR**
  - The 3/4 views are good.
  - The pose is the same frozen figure.
- **fl07 climb/dive — MINOR**
  - The flight path climbs 70→124 m and comes back to 80 m.
  - The body pose is identical when climbing (3.5 s), diving (6.5 s) and level (1.5/9.0 s). There is no pitch into the climb or the dive.
- **fl08 brake — MINOR**
  - 55 → 0 m/s in 0.30 s, with a readable rotation to upright.
  - The hover afterwards does not breathe or bob: px_top stays at 184–188 (1080p) over 5.13–6.47 s. It is a mannequin A-pose with arms out about 25° and legs locked together.
- **fl09 dash — MINOR**
  - There are no dash effects (no burst, no streak).
  - After each dash the hero shrinks to bbox_h 0.18–0.21.
  - Between dashes he holds the A-pose.
- **fl10 slow flight — FAIL**
  - At t=1.2 the camera faces a brick facade that fills about 100% of the frame.
  - Camera yaw jumps 8.5° in one frame at t=0.45.
  - "Slow" flight runs at 19–24 m/s.
- **fl11 slam + crater — FAIL**
  - During the 94 m/s vertical slam the camera rides level with the hero (cam_pitch −2.2° to +0.75° at t=2.00–2.25), so the ground is never seen coming. The shot reads as an elevator going down.
  - The crater is a flat near-black decal (crater core RGB ≈20/16/13) with no rim and no depth. The double yellow road lines are drawn across the cracks (t=2.45, 5.5).
  - Debris is untextured grey cubes.
  - The landing pose holds one arm raised to the sky.
  - A white van pops out of existence in full view at t=3.550 (frame 213): white pixels in x0–560, y400–950 (1080p) drop from 90,112 to 5,389 in one frame.
- **fl12 boosted dive landing — FAIL**
  - The dive keeps the same one-arm cruise pose.
  - The landing puts the camera against a truck: the hero is hidden at t=2.67–2.69 and luma jumps 38.2 at t=2.73.
  - The landing pose is a splayed straddle with the buttocks to the camera, one hand down and one arm up (t=3.1–3.7). It is not a three-point landing.
  - An untextured grey cube sits in the pickup bed.
  - The crater is the same flat black blob.
- **fl13 soft land + walk + takeoff — FAIL**
  - The run is frozen: across 12 consecutive frames (t=7.50–7.70) at 9.8 m/s (1.96 m covered) the legs barely move. He skates.
  - A brown sedan despawns next to him at t=5.983: brown pixels in x0–400, y220–540 (540p) drop from 30,412 to 661.
  - The touchdown knee bend is small (t=3.47–3.57).
  - The takeoff repeats the cut-off: hero_in_frame=0 for 4 frames, t=9.52–9.57.
- **fl14 cruise breach — FAIL**
  - A single cruise produces 4 breaches.
  - At each of the 3 measured breaches the camera holds outside while the hero is hidden for 12, 22 and 21 frames, then teleports 11.4, 24.5 and 33.1 m (t=4.55, 5.37, 6.89).
  - At t=5.35–5.40 the hole decal extends past the edge of the wall, over the background.
- **fl15 boost breach — FAIL**
  - At t=3.850 (frame 231) a flat dark-brown rectangle flashes for exactly one frame. It covers 232,551 px (1080p), bbox x438–1322, y50–741, and is darker than both neighbouring frames by more than 25 luma.
  - The hero is hidden for 18, 6, 19 and 9 frames across the breaches.
  - Camera teleports: 79.9, 23.3, 74.3 and 44.5 m.
- **fl16 slow facade slide — MINOR**
  - No slide contact is readable: no hand on the wall, no scrape.
  - Camera yaw swings 96° in 0.25 s (t=0.333–0.500), peaking at 12.1° per frame.
- **fl17 rescue — FAIL**
  - Pedestrians block the hero for 30 frames (t=0.63–1.12).
  - On the way he unintentionally breaches a glass tower at 12.88 s: hidden 24 frames, then a 40.6 m camera jump.
  - The crane load is a flat, untextured yellow box with no cable visible (t=14.3–16.5).
  - The "carry" is not overhead: he lies prone on top of an untextured grey slab (t=18.5–19.8).
  - It ends in a superhero slam (landHero) onto a roof 14.2 m above the street at t=20.6, not a set-down. His body intersects the glass facade at t=20.8.
  - From t=21.6 to the end (23.1 s), 70% of the frame is a flat grey surface and the hero is hidden for 129 frames.
  - The mechanical CHECK also fails this case.

## 3. Top 8 defects (ranked), each with an acceptance test

1. **The rescue is broken end to end** (fl17, 18.5–23.1 s: prone on a grey slab, slam onto a roof, 129 hidden frames, 70% flat grey).
   *Test:* from catch to end, hero_occl < 0.5 on every frame. Both hands are above the head on at least 90% of carry frames. The load ends on the street. Touchdown happens at street height with |vz| ≤ 3 m/s and sub ≠ landHero. No frame is more than 20% flat grey.
2. **The world simulation is not stable between frames.** Vehicles despawn in view (fl11 t=3.550; fl13 t=5.983), and world states alternate frame to frame (fl01 frames 40–51, diff 19.1 with a static camera).
   *Test:* with a static camera at idle, the mean absolute luma difference between consecutive frames is under 3. No vehicle larger than 2% of the screen appears or disappears between two frames.
3. **Breaches hide the hero and then the camera teleports** (fl14: 12–22 hidden frames and 11–33 m jumps; fl15: up to 80 m), and a one-frame panel flashes (fl15 3.850, 232k px).
   *Test:* at most 6 hidden frames per breach. The camera's per-frame step is no more than the hero's step + 1 m. No region larger than 2% of the frame differs by more than 25 luma from both of its neighbouring frames.
4. **The character animation is lifeless.**
   - The run skates (fl13 7.50–7.70).
   - Hover is a rigid A-pose with no bob (fl08: 4 px over 1.33 s).
   - One frozen one-arm flight pose is used for cruise, climb and dive, rolled 40–48° at zero bank (fl02, fl03, fl07).

   *Test:* at ≥3 m/s the feet alternate plants at a cadence that matches the speed, with no foot sliding more than 5 cm. During hover the head moves vertically 8–20 px (1080p) at 0.3–0.6 Hz. During climb/dive the body pitch differs from level flight by at least 20°. At bank 0 the body axis is within 10° of upright on screen.
5. **The takeoff has no ground anticipation** (fl01/02/13: vz steps 0→16 m/s in one frame, the crouch plays in the air, px_bottom=1080).
   *Test:* a crouch of at least 0.2 s with z unchanged before vz > 0. vz ramps up over at least 4 frames. px_bottom < 1060 throughout.
6. **The slam and its landing have no impact** (fl11/12: level camera during the dive, flat black decal crater with road lines drawn over it, splayed straddle pose).
   *Test:* during the slam, cam_pitch ≤ −30° and the ground fills the lower third of the frame. The landing pose is one knee and one fist down with the other arm back, held at least 0.5 s. The crater shows a lit 3D rim, and no road markings are drawn inside it.
7. **Camera framing failures**: facing a wall (fl10 t=1.2), a 96° whip in 0.25 s (fl16), pedestrians blocking the hero (fl17 0.63–1.12).
   *Test:* yaw rate ≤ 180°/s. Facade covers at most 40% of the frame in open-air flight. Any occlusion lasts at most 6 frames.
8. **The effects and destruction look like placeholders**: a bead-chain boom ring, untextured grey/yellow cubes for debris and the crane load, a hole decal that extends past the wall.
   *Test:* the ring renders as a continuous band with no gaps wider than its thickness. No visible mesh uses an untextured default material. Breach decals are clipped to the facade's bounds.

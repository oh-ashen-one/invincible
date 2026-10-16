# Round 6 notes: piece "breach camera / world glitches / FX" (builder B)

These are source edits only. Nothing was compiled, launched or rendered in Unreal.

**Process deviation:** one read-only `git status` was run by mistake. Its output was discarded and it changed nothing.

The evidence measurements below were taken on the r5 540p clips and telemetry in `docs/invincible/captures/r5/`, using ffmpeg and numpy on the CPU. All behaviour numbers for the new code are design values, not measurements.

`-WHFlight=0` is unchanged:
- every camera change is gated on `FlightLeashM > 0`, which only `FlightFrame` sets;
- every traffic change is gated on `UWHFlightWorldSubsystem::bFlightMode`;
- the breach director and the flight component only run in flight mode.

## Root actions needed

1. Rerun `Scripts/build_invincible_fx.py`. It now builds the new `M_InvShockRing` and changes the `M_InvChunk` graph (LocalPosition, a `Size` vector parameter, AO). `python3 build_invincible_fx.py --dump-hlsl` parses and writes all 9 Custom-node bodies.
2. Compile. Without the rebuilt assets, the C++ falls back to segmented tubes and the old chunk look.

## Files changed

- `Life/WHLifeTraffic.h/.cpp`: the traffic. This file is not in builder A's set.
- `Traversal/WebTravCamera.h/.cpp`
- `Traversal/WebTravCharacter.cpp`: the breach-hold block only.
- `Flight/WHFlightComponent.h/.cpp`
- `Flight/WHBreachDirector.h/.cpp`
- `Scripts/build_invincible_fx.py`

## #2 World glitches

### Cause found in fl01, frames 40–51

The world itself was not alternating. The **lens** was dithering:
- `cam_dist` stepped 3.525 → 3.660 → 3.796 → 3.525 m, in 0.136 m steps, every 1–3 frames.
- `SlewFlags` read 16 or 48: edge steering plus the body-containment backtrack of the 1 s reset tail (`StartupFrameTail`).
- The large diffs sat in the lower-left blocks (mean 60–80 luma). That matches a near car toggling at the `CameraClearM` 1.8 m hide distance as the lens moved.

At t = 3.5 s in fl11 the same camera spot shows no flags and smooth motion.

**Fix:** the startup tail is 0 for the flight hero.

### Vanishing cars (fl11 3.55 s, fl13 5.98 s)

The camera was at 1.37 m height, so it counted as a street-level lens. The `CameraClearM` rule hid any moving car whose body came within 1.8 m of it.

**Fix (flight mode only):**
- A car is hidden only while the lens is inside its body: footprint + 0.15 m, and below its roof height.
- Cars brake for the hero and for a street-level lens standing in their lane, up to 45 m ahead (a stopped IDM leader).
- A car stuck for 120 s is not despawned within 250 m of the lens.
- The sim steps every rendered frame (substeps ≤ 1/30 s). The old 30 Hz accumulator moved cars only on alternate 60 fps frames.

## #3 Breaches

**Cut and hidden time:**
- `BreachMaxTime` is now 0.06 s, down from 0.3 s. The floor on that bound is now 0.02 s, down from 0.1 s.
  - Design: about 4 frames inside at 60 fps.
  - The speed shown in telemetry during a pass can read over 1000 m/s.
- At the exit, the cut happens at once on the nearest clear yaw (`FWebTravCamera::ChooseCutYaw`):
  - it tries the current yaw first, then ±25° to ±150°;
  - each candidate spot must be out of solids and see the hero's chest.
- The hold waits at most 0.05 s, and only when no yaw is clear. It used to wait up to 0.4 s.

**One-frame flat panels:** I found the same signature on the first decal of a case:
- fl15 frame 231: 57k px at 540p, 2 frames after `breachIn`, in the hole-decal box, at a ratio of 0.5.
- fl11 frame 137: 27k px, crater.
- fl17 frame 1241: 32k px, crater.

**Fix:**
- At BeginPlay the decal pools, 88 debris pieces and 24 boom pieces are pre-created, and the FX materials get `FinishCompilation`.
- A placed decal becomes visible one engine frame after placement.

## #7 Camera

- **Yaw rate (flight hero):** the output yaw, and the lens orbit around the hero, are capped at 180°/s plus deliberate look input. A capped spot is used only if it is clear. Telemetry shows `SlewFlags` bit 128 when the cap acts.
- **fl10 brick wall:** during a facade slide contact, a camera heading that points into the wall is replaced by the along-wall direction (the travel direction).

## #8 FX

- **Boom rings:** each ring is now one flattened sphere with `M_InvShockRing`, an annulus opacity mask, and a tube 1.5× thicker than before.
  - Fallback when the asset is missing: 1.5× as many tubes, each 2.2× the spacing long, with a shared opacity.
- **Hole decal:** fitted to the facade plane.
  - Line traces probe how far the plane runs on each side; the box shifts up to 30 % away from a near edge and then shrinks, never below 1.1 m.
  - Projection depth is 0.5 m, down from 0.9 m.
- **Debris:** every crater piece and rim piece now wears `M_InvChunk`; the street material is no longer used. Breaches keep the facade-material share.
  - `M_InvChunk` r6 is in the piece's own frame: a tint per face, crevices, specks, chipped edges and AO.

## Not changed

- The fl17 crane load and slab belong to the rescue director, which is builder A's.
- Pedestrian occlusion was not addressed.

# r10 notes: lens inside the box truck after the fl12 landing

This was a source-only builder pass. Nothing was compiled, launched, simulated or rendered, and no git command changed anything. The root compiles, renders and commits.

**Process deviations:**
- Two read-only git commands were run: `git branch --show-current` and `git diff --stat`. They changed nothing.
- One read-only `find /` file search was run, looking for `vehicles.glb`. It has ended and wrote nothing.

**Evidence (offline, read only):**
- `docs/invincible/captures/r9b/fl12_fast_land_telemetry.csv.gz` and `fl12_truck_frames.png`.
- `public/assets/city/vehicles.glb`: the POSITION accessor min/max of the 15 LOD0 meshes, measured with python.

**Files:**
- `Life/WHLifeTraffic.h/.cpp`
- `Flight/WHFlightComponent.h/.cpp` (`GatherVehicleBoxes`)
- `Traversal/WebTravCamera.h/.cpp` (`GuardLens`, new `GuardVehEscape`, `UpdateVehSwing` types)
- `Traversal/WebTravCharacter.cpp`: the gather call only, 3 lines.

## What r9b shows

**Truck frames, rows 187–241 (55 frames):**
- The hero kneels at (250.00, 15.757, 0.942).
- The guarded lens sits at (251.44, 15.768, 1.25), so it is 1.47 m away on the truck side (+x), with yaw 158 and pitch −11.5.
- `hero_in_frame` is 0 and `cam_slew` is 133.
- 1.47 m is roughly `LensBodyMinM` (1.4). This means the guard's pull-in toward the chest ran into the body minimum. The raise spot ("behind the view") was also on the truck side, so it was blocked. The last fallback, `PushFromBody`, left the lens where it was: inside the truck.
- None of the r7–r9 stages looked for a spot off the chest→lens line.

**Mesh size against the type table (glTF metres, from vehicles.glb; length x width x height):**

| Type | Mesh | Table | Difference |
|---|---|---|---|
| truck | x −3.98..3.60, 7.58 x 2.84 x 3.57 | 7.3 x 2.3 x 3.4 | 0.27 m wider per side, centre 0.19 m off the pivot |
| bus | 12.76 x 3.12 x 3.47 | 12.2 x 2.55 x 3.3 | |
| tour | 11.46 x 3.12 x 4.30 | | |
| van | 6.02 x 2.46 x 2.64 | | |
| cars | 0.3–0.4 m wider than the table | | |

The guard's moving boxes padded the width by 0.2 m and its parked boxes by 0.1 m, so a parked truck's real side stood 0.17 m outside its box.

## Changes

**Traffic: `AWHLifeTraffic::GetCarBoxes(CenterCm, RadiusCm, Out)`**
- Each moving and parked car within the radius becomes an oriented box: `UStaticMesh::GetBoundingBox()` of its type mesh under its render transform.
  - **Moving cars:** the transform comes from the same pose `PushInstances` draws. `CarPose` was factored out of `PushInstances` with no change in behaviour, so the pose includes the lane offset `Lat` and the brake pitch. Cars hidden by the lens rule are included.
  - **Parked cars:** the stored `ParkedXfs` transform (real yaw). The r7 code used the union of both axes instead.
  - **Moving-car stretch:** each moving box is stretched by speed/30 s at each end, because the sim can step once more before the frame renders.
  - **Mesh fallback:** if a mesh is missing, the type table is used.
- **Cost:** one loop over the active cars and the parked list with a 2D distance reject. No allocation apart from `Out`. This is cheaper than the r7 `GetPoints` + `GetMovingInfo` copies.
- **Flight-mode "lens inside the body" hide:** now uses the mesh bounds (footprint + `FlightLensInsideM`, under the mesh roof) instead of the table. This is only a fallback for moving cars, so the view stays clear if the lens does end up in one.
- **BeginPlay log:** `[life] r10 vehicle mesh bounds: truck LxWxH [min x..max x] (table …); …` gives the UE-side numbers.

**`GatherVehicleBoxes`:**
- Now returns `FWHLensObb`: metres, oriented, +0.03 m pad.
- The `GLensCar*` size tables are removed.
- The pawn gathers within 25 m of the hero, not 12 m round the lens. It gathers while the hero or the lens is below 8 m.

**Camera: `FWHLensObb`**
- Defined in `WebTravCamera.h`, with `Contains(P, Pad)`, `SegEntry(A, B, Pad, T)` (a slab test in the box frame) and `TopZ()`.
- Every r7–r9 vehicle test now uses it: lift, lift sightline, pull-in, `BoxHit`, swing. The behaviour of those stages is unchanged; only the boxes are real. `SegBoxEntry` is removed.

**Camera: vehicle escape (`GuardVehEscape`, GuardLens stage 3, after the pull and raise, not in the breach pass)**
- **Trigger:** the guarded lens is inside a vehicle box padded by `LensSolidR`, or a box cuts its line to his chest. A box that contains his chest is skipped.
- **Valid spot:**
  - above the floor + 0.4 m;
  - at least `LensBodyMinM` from his body;
  - outside every vehicle box, with no box cutting the sightline;
  - clear of traversal solids and the traversal line;
  - clear of render collision: overlap, plus a 5 cm sweep from the chest.
- **Order:**
  1. Hold last frame's escape spot (relative to him) while it stays valid.
  2. Otherwise search a ring round him. Radius = the composed lens distance, clamped 1.8..`EscMaxR` (5 m). Height levels: the composed height (clamped 0.3..2.5 m over his centre), +1.2 m, and the near roof top + R + 0.3 m. Azimuth steps of `EscStepDeg` (15°), all the way round. The cheapest spot is taken: cost = |azimuth| + 25 per metre of rise. So a small swing beats a rise, and the over-the-roof spot only counts if it sees him (r8 rule).
- **Applied in the same frame (no release lag).** The existing GuardLens re-aim keeps his screen position.
- **Release:** once the guarded lens is clear again, the held spot walks back along an arc round him, at most `EscReleaseDeg` (150°/s) and `EscReleaseV` (6 m/s). A blocked step ends the release.
- **Flags:** `LensGuardFlags` 64 = escape spot, 128 = release step. These flags are not in the telemetry CSV.
- **Logs:** `WH_CAM r10 vehicle escape: guarded lens inside|behind a vehicle box (N near) -> spot ±D deg …` or `… no clear spot round him …`.
- **Tunables:** `-WHCamTune=EscStepDeg=0` turns the escape off. The vehicle boxes stay real.
- **Cost:** only when blocked. Up to 72 candidates, cheap tests first; the physics overlap and sweep run only for candidates that pass those. While held: one validity check per frame.

`VehMaxDeg` stays 0 (the r9 swing is off, as the root set it).

## Checks for the root

**fl12:**
- **Log:** `[life] r10 vehicle mesh bounds`. Truck expected at about 7.58 x 2.84 x 3.57 if the import keeps the glTF axes (length on UE X).
- **Log:** `WH_CAM r10 vehicle escape` near 2.7–3.1 s.
- **Frames:** no frame with the lens inside a vehicle; the hero is visible through the hold and the takeoff; dark frames 0; longest hidden run ≤ 6.
- **Telemetry:** in rows 160–241, `cam_x` should not be inside the truck's footprint. The lens is expected on the −x / open side or over the roof with a sightline to him. `cam_hero_dist_m` ≥ 1.4.

**All flight cases:** count `vehicle escape` log lines. Escapes should not appear away from street traffic. On fly-bys along a street, look for any visible lens jump when a truck cuts the chest line.

## Open points (not verifiable without a run)

- **UE bounds:** the UE mesh bounds and axes were not checked. The BeginPlay log shows them; the fallback is the table.
- **Lens jumps:**
  - The escape is a jump in the frame it triggers (by design: it is never inside). On a fast fly-by a passing truck that cuts the chest line can trigger one.
  - The release then takes about 0.6 s for a 90° arc.
- **Escape trigger:** only the chest line is tested, not the 5 body points.
- **Ring radius:** if the lens composes farther than 5 m, the escape ring is closer to him than the composed lens.

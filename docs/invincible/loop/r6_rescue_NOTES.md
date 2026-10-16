# r6 rescue carry / set-down notes (builder A, critic r5 #1)

This was a source-only pass. Nothing was compiled, simulated or rendered here. The root builds, simulates, renders and commits.

**APIs checked against the UE 5.8 headers** (`/Users/Shared/Epic Games/UE_5.8/Engine/Source`):
- `UGameplayStatics::GetPlayerCameraManager(const UObject*, int32)`
- `APlayerCameraManager::GetCameraLocation()` and `GetCameraRotation()`, both `const`
- `UMaterialInstanceDynamic::SetVectorParameterValue` and `SetScalarParameterValue`
- `UPrimitiveComponent::SetCastShadow`
- `FRotationMatrix::MakeFromYZ`

`M_CmbSolid` has `Color`, `Rough`, `Metal` and `Emissive` parameters (`Scripts/build_combat.py`).

**Evidence used:**
- `captures/r5/fl17_rescue_crane_telemetry.csv.gz`
- frames extracted from the r5 540p mp4 at 14.3, 15.5, 16.8, 17.4, 17.9, 18.6, 20.2 and 20.9 s
- the r5 fl17 log (`~/sm2-invincible-cache/r5/fl17_rescue_crane/`, read only)
- the hover-descent rows of fl01 and fl13

## What r5 did (from the numbers)
**Catch:**
- Log line: "caught hanging at 135 m … from below / beside (5.2 m)".
- The hero was at about (350.9, -323.0, 137.0). The load rest point was (355.7, -324.3, 135.3).

**Carry dive (17.6–20.6 s):**
- The hero was in fly mode at about 51 m/s on a -57° path, with the camera pitched to -47° (dist 3.3 m).
- The AS_Fly clip and path pitch put him prone, with the load along his arms. Seen from above, he lies on it like a surfboard.

**Landing and set-down:**
- `heroLand` at (270.4, -302.8, 14.3) at 51.4 m/s, sub `landHero`, onto a 14 m terrace roof near 5th Av.
- The set-down put the load at the hero + 1.6 m along `Flat(LoadQ.Y)`. In the dive, the chest faces down and back, so that direction was (+0.94, -0.33): back toward the camera (cam yaw ~162°). The camera then sat inside the load, so the frame was 70 % grey and the hero was hidden for 129 frames.

**Load:** one cube, `Steel` (0.25, 0.27, 0.30) on `M_CmbSolid`. It renders as a light flat grey.

**Crane geometry, inferred from the frames:**
- At 16.8 s the jib crosses the view to the left of the hero. At 17.4 s, looking west, the mast is at the right edge.
- So the boom heading is about 40°: the mast is NW of the tip, on a roof at about 120 m, and that facade is about 6 m north of the hero's column.
- The street under the tip is the load's own fall target (street z ≈ 0, TravWorld floor 0 under the column).
- That street is an E–W cross street. The r5 dive ran down it to 5th Av, and it was open at y -306…-321 at the heights that dive passed.

## Changes

| File | Change (critic r5 #1) |
|---|---|
| `Traversal/Anim/WHHeroV2AnimInstance.cpp` | `UpdateCarry` now runs before `PickState`. While a load is carried, fly / boostHold / dash / breach / boostLaunch / slam dive → **Hover**, so the body is upright, feet down, with PitchFreedom 0. The arms keep AS_LaunchUp's fists overhead (r5). Climb while carrying still gives LaunchUp. |
| `…/WHHeroV2AnimInstance.h` | `CarryOutT` 0.3 → 0.8 s: the arms come down with the eased set-down. |
| `Flight/WHRescueDirector.h/.cpp` | Everything below is gated on `bOverheadCarry` (set only by the v2 anim), so `-WHHeroV2=0` keeps the r5 rules and look. **`DressLoad`** (once, from `TickCrane`): a shipping-container look, described below. Log line: `WH_RESCUE crane id N load dressed as a container (4.0 x 1.8 x 1.5 m, 49 trims)`. **Cable:** 0.12 m thick (was 0.06). **`PickSetDown`:** chooses the set-down spot in the camera frame, described below. **Settling:** the sideways ease runs over `SettleXyT` = max(0.6, 0.8 × dur), and the set-down lasts at least `SetDownMinS` 1.2 s. **Auto set-down:** after `CarryMaxOverheadS` 40 s (was 10 s; the descent takes about 15 s). |
| `tools/invincible/make_flight_cases.py` (fl17 only) | The DIVE keys are removed. New constants: `DESC_T` 17.6, `TURN_T` 18.4, `SET_T` 33.0. `quit` = 36.3. New checks: `max_hero_lands=0` and `grounded_end=True`. The keys up to 16.98 s (approach, breach, brake, catch) are unchanged. |

**Container look (`DressLoad`):**
- Body: dark container red (0.16, 0.032, 0.018), Metal 0.45, Rough 0.5.
- 10 corrugation ribs on each long face, ribs on the −X end and 4 pale locking bars on the +X end.
- A near-black frame: 4 corner posts and 8 rails.
- 4 roof bows and 5 bottom cross-members. The fists meet the bottom cross-members while the load is overhead.
- All trims are thin cubes attached to the load body. The relative transform is divided by the body scale. They have no collision and cast no shadow.

**`PickSetDown` (camera-frame set-down spot):**
- The forward axis is camera → hero, flattened. If the camera is directly overhead, its heading is used.
- Candidates are tried in this order: (beyond 2.4 m, beside ±3.0 m), with the side that has more room trace to 9 m tried first; then 3.6 m straight beyond; then (4.4 m, ±3.4 m).
- The load's long axis lies across the camera line.
- A candidate is rejected unless:
  - the ground under its centre and 4 corners lies within 0.5 m (it is level);
  - that ground is within 0.6 m of the hero's floor (so not a car roof, step or roof);
  - the line from the hero's waist to it is clear;
  - there is room past its outer faces.
- The near corner is 1.8 m from the hero's centre. The inner face is 1.0 m to the side of the camera–hero line.
- If no candidate passes, the r2 placement is used.
- Log line: `… load set down at … over 1.2 s, hero at …, 2.4 m beyond / ±3.0 m beside on the camera line`.

## fl17 r6 route after the catch (predictions from the r5 numbers)
1. **16.98 s:** drop released (unchanged). The hover settles at about (350.9, -323.0, 136.9).
2. **17.6 s:** `drop` held, giving a hover descent at -10 m/s (fl13 model: z = z0 − 10 (t − t0) + 2.1).
   - The catch happens about 17.5–17.7 s, "from below / beside", as the hero passes the load's height at a horizontal distance of 4.85 m.
3. **18.4–19.4 s:** `look` −162 °/s. The camera yaw goes −18 → 180, so it looks west down the street.
   - The lens swings through the south side (y ≈ −318). The hero turns with it, with the load overhead.
4. **Descent to about 31.0 s:** camera at its hover pitch (r5: −9.4°, dist 5.0 m).
   - The camera sits about 0.8 m above the hero's centre. The load's bottom is 1.25 m above it, so every ray from the camera to the hero passes under the load (computed for pitch ≤ −20°).
5. **Touchdown about 31.7 s:** auto flare, |vz| about 1.9 m/s at contact (fl13: 1.93). Sub `idle`, not `landHero`.
   - Street at z ≈ 0, so hero centre 0.95. The dip runs with the arms still up.
6. **32.8 s:** drop released.
   - **33.0 s:** E pressed. The load (centre about 2.95 m) is lowered over 1.2 s to rest at centre 0.75 m, front-left (the south side, which has more room; the north candidate fails the room test near the facade). The arms lower over 0.8 s.
7. **34.2 s:** `load rests`. The hero stands beside it until the quit at 36.3 s.

**Timing tolerance:**
- If touchdown comes as late as 33.0 s (+1.3 s), the set-down happens in a low hover instead. That is still beside / beyond on the camera line.
- If the descent is faster, he only stands longer before E.

## Things to check (sim / render)
- **Log:**
  - `load dressed as a container` before the catch;
  - `load caught hanging … from below / beside`;
  - no `WH_FLIGHT heroLand`;
  - `load set down … beyond / … beside on the camera line`. If this line lacks the "on the camera line" suffix, the fallback placement ran;
  - `saved … (load set down)`;
  - `load rests` at z ≈ 75 cm (the street), not about 1500 cm.
- **Telemetry, 17.6 s to the end:**
  - fl_sub stays `hover` (never `fly`) until ground `idle`;
  - |vz| ≤ 3 on the last air row;
  - hero_occl < 0.5 on every row;
  - cam_pitch about −3 to −12° during the carry;
  - final z ≈ 0.95.
- **Anim log:** `WH_HEROV2 state hover` stays through the descent, with no `fly` while carrying.
- **Pixels:**
  - fists over his head under a dark red ribbed container from the catch to the set-down;
  - after the set-down the container is front-left of him and never covers him;
  - no flat grey region over 20 %.

## Open risks (not verifiable without a run)
- **Street layout:** the street width, south facade position and north facade distance (about 6 m) are inferred from frames and the r5 path, not measured. During the descent, the north facade (dark glass) fills much of the right half of the frame.
- **TravWorld vs. rendered collision:** if the box index and the render collision disagree under the column, the hero lands on TravWorld's floor while `PickSetDown` traces the render collision.
- **Traffic and pedestrians:** cars are rejected by the level / floor tests. Pedestrians are pawns, which the traces ignore. Moving traffic belongs to builder B's piece.
- **Length:** the carry descent lasts about 13.4 s of steady hover (fl17 is now 36.3 s, was 23 s).

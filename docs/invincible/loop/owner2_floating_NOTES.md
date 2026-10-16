# owner2 floating notes (owner request + bug, 2026-10-16)

This was a source-only builder pass. Nothing was compiled, simulated or rendered here, and nothing was committed. The root builds, simulates, renders and commits.

APIs used are ones this module already compiles: `FWebTravWorld::SweepSolid`, `FWebTravWorld::GroundHeight`, `FParse::Value(…, int32&)` and `FMath::Min3`.

## Requests
- **Bug:** a double-tap dive onto a 52 m roof at (531.7, 469.5) froze the game, input stopped working and the camera oscillated.
  - Root's sim (fl18) shows ground mode on the roof with `height_above_floor_m` 51.85.
  - The ground system's floor probe does not see the roof the flight sweep landed on.
- **Request:** "always floating, even near the floor".

## Design
In flight mode the hero never enters the traversal GROUND mode.

`-WHFloat=0` restores the r6 ground behaviour, for A/B comparison only. `-WHFlight=0`, the legacy Spider-Man mode, never reaches this code.

| Situation | Before (r6) | Now |
|---|---|---|
| Hero landing: slam (F), double-tap dive, or impact ≥ 30 m/s | `EnterGround(landHero)`, ground mode | Mode **Air**, sub `landHero`, velocity 0, feet on the surface the landing found. Held `LandHoldTime` 1.3 s (Space / fly press ends it after `LandHoldCancelT` 0.9 s). Then sub `hover`, and the float lifts him to `FloatHeightM` 0.45 m. Crater, `heroLand` event and camera impact are unchanged. |
| Contact at 12–30 m/s in hover / brake | ground `landLight` | "Touch": vz 0, keeps `TouchKeepH` 0.6 of the horizontal speed, sub hover, `land` event (camera impact), knee dip in the anim. |
| Contact below 30 m/s in a fly / boost / dash line | ground landing | Skim: clamped to the surface, vz 0, the aim pitch levels out (no repeated touches), `flyBump` above 15 m/s. |
| Hover descent (C / Ctrl held) to the floor | touchdown → ground idle | Settles to 0.45 m and holds there, with no contact. Target vz = −min(VertSpeed, √(2·12·e), 3·e), where e = height above the float height. |
| Hands-off hover within `FloatCatchM` 1.6 m of a surface | holds altitude | Settles to 0.45 m (faded in over the top 0.4 m of the band). Higher up, or past a roof edge, the hover holds its altitude as before. |
| Below the float height (after the hold, a step up, a curb or car) | — | Rises at min(4 m/s, 5·gap). |
| Spawn / teleport onto the floor | ground idle | `EnterFloat`, which rises to 0.45 m. |
| WASD near the floor | walk / run | Hover glide, camera-relative, 9 m/s. There is no walk state. |
| Space near the floor | takeoff | Hover climb (LaunchUp clip above 5 m/s). A double tap with less than `DiveMinHeightM` 2.5 m below keeps climbing instead of diving. |
| E / Triangle while floating still (< 1 m/s, within 1.6 m of a surface) | ground: no-op | Interact only: no brake sub, no `flyStop` camera bump. This keeps the fl17 set-down calm. |

**Float vertical control:**
- `V.Z` approaches the float target at `FloatVzRate` 16 /s.
- With gains 5 (up) and 3 (down) the response is damped, with ζ ≈ 0.89 (up) and 1.15 (down). Computed overshoot is about 1 % of 0.45 m, so it should not bob.

**Surface under the hero (`SurfaceUnder`):** the maximum of two probes:
- the traversal index ray started at the **body centre**, rather than 0.4 m under the feet like `FloorAt` / `HeightAboveFloor`;
- a 0.3 m sphere swept down through the same filtered collision as the flight sweep (`SweepSolid`, normal z ≥ 0.6).

**Filtering (`FloatSurface`):**
- A higher surface is taken at once.
- A lower one eases in at 8 /s, so a single probe miss cannot drop the target.
- A drop deeper than 1.6 m (a roof edge) is taken at once, and the hover then holds altitude.

**Other uses of `SurfaceUnder`:** it also feeds the double-tap dive acceleration (`StartDive`) and, through `SurfaceBelowZ()`, the anim's time-to-impact. So a dive onto a roof the index does not know is timed to that roof.

## Files
| File | Change |
|---|---|
| `Flight/WHFlightComponent.h` | Tunables `bAlwaysFloat`, `FloatHeightM`, `FloatCatchM`, `FloatUpK`, `FloatDownK`, `FloatRiseMax`, `FloatVzRate`, `FloatFloorFall`, `FloatProbeM`, `LandHoldTime`, `LandHoldCancelT`, `TouchKeepH`, `DiveMinHeightM` (floats tunable via `-WHFlightTune=`). Accessors `IsFloatOn`, `IsLandHold`, `LandHoldS`, `SurfaceBelowZ`, `FloatGapM`, `FloatTouchCount`, `FloatTouchSpeed`. Private `SurfaceUnder`, `FloatSurface`, `StepLandHold`, `FloorSkim`, `SkimFloor`, `EnterFloat` and their state. |
| `Flight/WHFlightComponent.cpp` | `HeroLand` float branch; `MoveAndCollide` (no drop-landing, skim, no gentle-touchdown snap); hover float in `StepAirSub`; interact-only E; double-tap room guard; `StartDive` height; `StepFlight` (`-WHFloat` parse, hold input filter, hold reset on teleport, ground → float, hold substep, per-frame `SurfBelowZ` / `FloatGap`); `FlightOrient` keeps the landing heading through the hold. |
| `Traversal/Anim/WHHeroV2AnimInstance.h/.cpp` | Details in the next section. |

`WebTravCharacter.cpp`, `WebTraversalComponent.cpp`, the camera and the HUD were not touched.

**Anim instance changes:**
- Air + sub `landHero` → LandHero impact. It is the dive's contact frame when coming from the dive, otherwise it enters at `LandFeetT`.
- LandHero → Hover blends over the new `BlendLandToHover` 0.5 s. The ground lock fades out with the LandHero track weight, so the planted feet do not pop.
- In float mode the anim never picks GroundIdle; a stray ground frame maps to Hover.
- Float touch → knee dip (same dip tunables). The dip fades out at 4× when a fly-type state takes over.
- `TimeToImpact` also uses the flight surface.

## Log lines (new)
- `WH_FLIGHT float mode on (height 0.45 m, land hold 1.30 s)`: printed once.
- `WH_FLIGHT heroLand at (…) impact … sev … (airborne hold 1.30 s, then float 0.45 m)`: the prefix is unchanged for the existing regex.
- `WH_FLIGHT land hold end after 1.30 s[ (cancelled)] -> float 0.45 m over z …`
- `WH_FLIGHT float touch at (…) impact … m/s`
- `WH_FLIGHT float from ground mode at (…)`: printed on a spawn or teleport onto the floor.

## What to check (sim / render)
**fl18_roof_hero_land (the bug):**
- One `heroLand` at z ≈ 52.0.
- No telemetry row with mode `ground` / `land`.
- sub `landHero` for 1.3 s at speed 0, then `hover`.
- z_m rises from about 52.95 to about 53.40 (±0.1) within about 0.8 s, with no overshoot over 3 cm.
- 5.0–6.5 s: horizontal travel of at least 8 m (hover glide). If he glides off the roof edge, he holds about 53.4 m.
- 7.5 s: Space climbs.
- Anim log: `state landHero` → `state hover`, never `groundIdle`.
- Pixels: kneeling impact on the roof, a stand-up, then a float about 0.45 m up with AS_Hover.

**fl11 / fl12:** hold, then float. The end row is mode `air`, sub `hover`, about 0.45 m over the street (z ≈ 1.4).

**fl01 / fl13:**
- The case starts in the float (spawn on 5th Av → `float from ground mode`).
- The drop-held descent ends floating at about 0.45 m, with no `land` / `heroLand` event.
- fl13's "walk" is a hover glide.

**fl17:**
- The descent ends floating (final z ≈ 1.40, not 0.95).
- No `heroLand`.
- E at 33.0 s gives no `brake` sub and no flyStop camera bump.
- `load set down … on the camera line`, then `saved … (load set down)`.
- The set-down's level test (ground within 0.6 m of the hero's floor) traces from the hero centre + 0.5 m, so it is unaffected.

**All cases:**
- No `mode == ground` row with the flight on.
- `below the floor frames` = 0.
- `position teleports` = 0 (the rise is capped at 4 m/s).

## Suite-check updates needed (root: `tools/invincible/make_flight_cases.py`, `check_flight.py`)
1. **`grounded_end`** (fl01, fl11, fl12, fl17) → a new **`floating_end`** check:
   - last row `mode == 'air'`, `fl_sub == 'hover'`, `speed_mps < 1`;
   - feet over the floor between 0.3 and 0.7 m. Use `height_above_floor_m`, or better a new `fl_float_gap` telemetry column from `Flight->FloatGapM()`, because `HeightAboveFloor()` starts its ray 0.4 m under the feet and reads the street under thin roofs.
2. **`walked`** (fl13) → **`glided`**: more than 30 rows with mode `air`, sub `hover`, `hspeed_mps > 1` and float gap between 0.2 and 0.8 m.
3. **`subs`:**
   - fl01 `['takeoff','hover']` → `['hover']`, plus `min_rise_m` (e.g. 5).
   - fl13 `['hover','takeoff']` → `['hover']`.
   - fl02 `['takeoff','fly']` → `['fly']`.
   - The `takeoff` sub no longer occurs with the float. The case notes saying "ground takeoff" / "touchdown" / "walk" should be reworded to "float / glide".
4. **fl18:** add `never_ground`, `floating_end` and a new `min_hdisp_m` = 8 over 5.0–6.5 s, besides `hero_lands=1`. Optionally require the log line `land hold end`.
5. **Suite-wide `never_ground`:** no row with mode `ground` or `land` in any flight case (default `-WHFloat`).
6. **Camera calm regression (new):** in every window with speed < 1 m/s and sub `hover` / `landHero` (≥ 0.5 s), require:
   - std(cam_z) < 0.03 m, and std of the camera pitch < 0.5°;
   - at most 2 sign changes per second of Δcam_z among frames with |Δcam_z| > 0.01 m.

   A real-time variant: the same check over fl18 telemetry at 60 fps. Gate it on fl18, fl11 and fl17 (hold, then float near a roof / the street).

## Open points (not verifiable without a run)
- **Hold landing position:** the hold puts the feet at the landing's floor height (sweep contact or index floor). If the sweep contact sits a few cm into a slab, the AS_LandHero kneel may show a small sink. The ground lock places the feet relative to the mesh root, not the world floor.
- **Float probe cost:** the float probe adds one line trace and one sphere sweep (8 m) per 120 Hz substep while hovering, plus one 400 m sweep per frame. Watch the trace count if the frame time matters.
- **Cars:** traffic cars are within the probe filter, so he floats over car roofs. Pedestrians (pawns) are ignored.
- **v1 hero:** with `-WHHeroV2=0` (the v1 `UWebTravAnimInstance`), Air + `landHero` and the float were not mapped. That file is not in this piece.
- **HUD:** the HUD builder's prompts that key on ground mode (if any) never see ground mode now.

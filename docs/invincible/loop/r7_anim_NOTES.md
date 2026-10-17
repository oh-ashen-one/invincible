# r7 anim / rescue notes (builder B; critic r6 #2, #3, #4 pop, #6)

This was a source-only pass. Nothing was compiled, launched or rendered, and there was no git. The root compiles, simulates, renders and commits.

**Files:**
- `Traversal/Anim/WHHeroV2AnimInstance.h/.cpp`
- `Flight/WHRescueDirector.h/.cpp`
- `tools/invincible/make_flight_cases.py` (fl17 turn only)

The case JSONs have not been regenerated: run `make_flight_cases.py`.

**Paths left unchanged:** `-WHHeroV2=0` and `-WHFlight=0`.
- The director's new rules are gated on `bOverheadCarry`.
- The bob and the line prediction need `A.Flight.bActive`.
- The arm swing only applies on carry layers.

**Offline evidence:** numpy FK of the clip GLBs (`docs/invincible/character/meshy/hero_*.glb`, scratch in `/tmp/r7anim`). Also used: r6 telemetry, logs and frames, the latest sim `~/sm2-invincible-cache/simF3/fl17`, and `Scripts/life_data*/parked.txt` / `lanes.txt`.

## 1. Boost pop (fl04 1.450 → 1.467)
**Cause:**
- In AS_BoostLaunch, the whole coil → stretch happens between two 30 fps keys (0.400 → 0.433 s):
  - head–feet distance 110 → 174 cm;
  - upper arms turn by about 105°.
- The charge mapped the clip up to `BoostBurstT` 0.42, which is already about 60 % into that jump. Playing on at 1× crossed the rest in about one frame.

**Fix:**
- `AnalyzeBoostClip` (runs at init) finds `BoostCoilEndT`, the last coil frame. Offline value: 0.367.
- It also finds `BoostBurstEndT`, the frame at 95 % of the stretch. Offline value: 0.433.
- The charge now holds the clip at `BoostCoilEndT`.
- On the boom, the coil → stretch span plays over `BoostBurstBlendS` = 0.10 s. That is 6 frames at 60 fps, 5 of them in between.
- The steps are uniform in joint travel (head, pelvis, feet, knees, elbows, knuckles). After the span, the clip runs at 1×.
- The handoff to BoostHold is unchanged (0.25 s blend at the clip end).

**Offline result:** frames of the chase view from behind, 15° above.

| Version | bbox aspect change per frame |
|---|---|
| Uniform joint-travel steps (used) | at most 18 %; then 1–8 % |
| Uniform body-extension steps (tried, not used) | 51 % in the last step |
| r6 (one key) | 0.94 → 0.81 in 1 frame |

**Log:** `WH_HEROV2 boost clip: … coil end t=… burst end t=… -> used`

## 2. Hero landing pose (fl12 2.75–2.80)
**Cause:**
- A boost line hitting the street at -180 m/s descent had AS_LandHero start on the contact frame.
- That start crossfaded over 0.15 s from the horizontal boost-hold pose.
- The mesh was also still pitched about 36° nose-down, easing back at 8/s. The r6 frame at 2.75 shows him lying flat.

**Fix:**
- **Prediction (`FastLinePredict`).** A fly, boost or dash line counts as about to hero-land when both hold:
  - descent ≥ `HeroLandMinSpeed` × 1.05 (the flight's own hero-landing rule is descent at contact ≥ 30 m/s);
  - `TimeToImpact` ≤ `FastLandLeadT` 0.55 s.
- When it fires, AS_LandHero's dive starts early.
  - Hysteresis: it stays while descent ≥ 0.85× and TimeToImpact ≤ 0.8 s; otherwise it blends back to fly.
- **Entry frame (`LineDiveStartT`).** The dive starts at the frame whose head line matches the path angle.
  - Table measured at init. Offline FK: -79° at 0.20 s, -35° at 0.367, -13° at 0.40, +8° at 0.433. The flip turns the head forward through the horizon.
  - fl12 (36° down) enters at about 0.367, head forward-down.
  - Blend in: `BlendToLineDive` 0.2 s.
  - No extra mesh pitch (PitchFreedom 0 for this track).
  - The ground lock ramps in from the entry frame.
- **Approach.** While far, the frame tracks the path angle and never goes backwards. From `LandFlipLeadT` 0.36 s out, the existing timed flip makes him feet-first before contact, then he creeps to the contact frame.
- **Slam / double-tap.** A dive that is already within 0.36 s of the floor before reaching the held dive frame now goes straight into the timed flip, instead of jumping on contact.
- **Hold.** During the airborne landing hold (sub `landHero`), the clip is held at `LandKneelEndT`, so the stand-up never plays while held.
  - Measured at init; offline it is 2.23 s.
  - AS_LandHero's knee + fist contact lasts 0.53–2.13 s (right hand 4–8 cm over the lowest foot joint). The 1.3 s hold from the 0.50 contact ends at clip time 1.8, inside the kneel.

**Logs:**
- `WH_HEROV2 fast line landing: path … deg down …, … s to the floor -> AS_LandHero dive from t=…`
- `WH_HEROV2 land clip r7: kneel held to t=…`

## 3. Hover bob (fl08)
**Procedural layer** in the anim (the clip is untouched):
- **Root bob:** along the mesh up axis, `HoverBobCm` 2.5 cm amplitude (5 cm peak-to-peak) at 2 cycles per AS_Hover loop (0.5 Hz).
  - Phase-locked to the clip's own head rise (DFT bin, `AnalyzeHoverClip`).
- **Breathing:** the AS_Hover layer's own spine2 / spine3 / collar deviation from its clip mean is applied once more, so it is 1.5× the clip (`HoverBreathGain`).
  - Collars are excluded while carrying; deltas over 12° are skipped.
- **Weight:** the AS_Hover track share × (1 − smoothstep(speed, 1 → 5 m/s)) × (1 − ground lock), eased with τ 0.3 s.
  - So it fades with speed, during the landing-hold rise and in transitions.
- The capsule and camera target are untouched, so the camera-calm check is unaffected.

**Amplitude choice:** the brief asks for both "10–12 cm" and "8–20 px".
- The r6 hover renders at about 225 px/m (fl08 bbox 0.385 × 1080 px for 1.85 m).
- So 10–12 cm would be 22–54 px.
- The chosen 5 cm p-p is about 11 px, plus the clip's head motion (1.45 cm p-p × 1.5, about 5 px) for the head. Expected: about 12–16 px.
- Tune with `-WHHeroV2Tune=HoverBobCm=…`.

**Log:** `WH_HEROV2 hover clip: bob phase …`

## 4. Rescue clipping (fl17)
### Catch: "legs inside the container"
**Cause:** in simF3, the catch was "level" at 15.49 s, 5.3 m away, with the hero 1.75 m over the load centre.

**New overhead-carry reach rules (director):**

| Hero vs. load | Reach |
|---|---|
| Load's bottom face ≥ his head top (body centre + 0.90 m) + 0.20 m ("under") | `CraneTouchUnderCm` 6.5 m |
| Hero over the load | 3 m (unchanged) |
| Level with it | `CraneTouchLevelCm` 3.5 m |

- simF3 route prediction: no level catch (closest horizontal distance 5.03 m). The under catch comes at about 15.85 s, 5.6 m away.
- Log: `… from below / beside (5.6 m; load bottom 0.20 m over his head top)`

**Swing (anim, `CarrySwingT` 0.45 → 0.6 s):**
- The path is split along the body axis: height first (done by 70 %), sideways offset last (from 25 %).
- A keep-out guard holds the box horizontally clear of the body when its vertical extent overlaps the band from the feet up to the head top or raised fists.
  - Clear distance: box support + 30 cm body radius + 25 cm.
  - The guard is soft over `CarryMarginCm` 20 cm and off at the hold.
- The r6 arc through the chest's front, past the legs, is removed.

### Catch: "arms in a T"
- The carry arm override (AS_LaunchUp arms blended over the hover's arms-down) now gets the same swing-in-front correction as the cross-layer arm fix.
- The r5 offline minimum for this pair is 60° with the fix, versus 22° without.
- Takeoff's idle-arm override is unchanged.

### End: "merges into the taxi door"
**Cause:**
- In simF3, the -162° turn starts from -93°, not -18°, so the camera ends at +105°.
- It looks south across the parking lane, with the lens just behind the parked taxi at (351.4, -324.0).
- The hero at (349.1, -320.25) is 2.8 m from both parked rows.

**Changes:**
- **`make_flight_cases.py`:** `TURN_DEG` -87, so the camera ends at -180, looking west down the one-way lane (link 1043, y -320.6).
- **Director `GatherVehicles`:** returns traffic ISM instances as boxes.
  - These instances have no collision, so the ground traces miss them.
  - Hidden pool instances (scale 0.001) are skipped.
- **`PickSetDown`:** rejects spots within `SetDownVehicleClearCm` 0.5 m of a vehicle (separating-axis test), with 2 more straight-beyond candidates.
  - Predicted for the new view: the beside spots hit the parked rows.
  - The 3.6 m-beyond spot in the lane clears them by 0.78 m and 1.11 m.
  - simF3 (old view) put the load 0.44 m into a parked pickup.
  - Log: `WH_RESCUE set-down spot … skipped: within 0.5 m of a street vehicle`
- **Stand clear (anim, general case).** It runs while floating at under 2.5 m/s within 1.5 m of the floor (hover or landing hold).
  - The mesh root steps sideways (at most 150 cm, τ 0.2 s) until there is 50 cm between a 35 cm body radius and every vehicle box. Boxes are queried at 10 Hz.
  - It is visual only: the capsule, camera and flight body do not move.
  - The set-down uses the hero position as seen.
  - Log: `WH_HEROV2 stand clear: …`
  - With the new fl17 view it should not trigger: 2.8 m from the parked rows, and moving cars stop 1.5 m before the hero or camera.

## Checks for the root (sim / render)
- **fl04:** `boost clip … used`. Through the boom, at least 4 in-between frames, and bbox aspect change ≤ 25 % per frame.
- **fl12:** a `fast line landing` line before `WH_FLIGHT heroLand`.
  - Feet-first at least 8 frames before contact.
  - Knee + fist pose from contact to `land hold end` (1.3 s).
  - No flat frame at contact.
- **fl11, fl18:** slam and double-tap unchanged or better. No impact jump.
- **fl08, fl01 hover:** head bob 8–20 px p-p at 0.3–0.6 Hz. Camera-calm check still passes.
- **fl17:**
  - `load caught … from below / beside (…; load bottom ≥ 0.20 m over his head top)`;
  - no frame with the load below his head during the 0.6 s swing, and no T-pose arms;
  - camera yaw about -180 after 19.4 s;
  - `load set down … on the camera line`, with the footprint ≥ 0.5 m from vehicles;
  - hero ≥ 0.5 m from vehicles; `hero_occl` ≤ 0.10 for the last 2 s;
  - still `rescue_saved_min=1` and `floating_end`.

## Open points (not verifiable without a run)
- **fl17 catch margin:** the under catch is predicted at 5.6 m against the 6.5 m reach, over about 0.15 s of the descent. If no catch is logged, raise `CraneTouchUnderCm`.
- **Vehicle boxes:** these are mesh bounds, which may include mirrors. The yaw comes from the ISM instance transform.
- **Swing pace:** the swing pulls the load about 5 m in 0.6 s.
- **Set-down slide:** the slide from overhead to 3.6 m beyond is unchanged r6 easing.
- **Container vs. tree canopy (fl17 31.2):** not addressed.

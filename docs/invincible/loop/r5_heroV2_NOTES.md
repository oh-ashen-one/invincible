# r5 hero v2 animation integration notes (builder A, critic r4 items 1-6)

This is a source-only builder pass. Nothing here has been compiled, launched or rendered. The root session builds, renders and commits.
APIs were checked against the UE 5.8 headers under `/Users/Shared/Epic Games/UE_5.8/Engine/Source`:
- `UAnimSequence::GetBoneTransform(FTransform&, FSkeletonPoseBoneIndex, const FAnimExtractContext&, bool)`
- `FTransform::BlendWith`
- `USkinnedMeshComponent::GetEditableComponentSpaceTransforms` (public)
- `UAnimInstance::NativePostEvaluateAnimation`, which `USkeletalMeshComponent::PostAnimEvaluation` calls on the game thread after the evaluated buffers are swapped back
- `FRotationMatrix::MakeFromZY`

`UE_LOG` expands to a braced block, so every `if / else` around it uses braces.

Offline evidence comes from FK of `Saved/P2Build/invincible/SK_InvincibleV2.glb`, the merged GLB the AS_ clips were imported from. It was done with numpy in `/tmp/r5hv2`, a scratch copy that is not in the repo. Below, "arm angle" is the angle between the shoulder→wrist direction and the outward shoulder line. A T-pose is about 0°; the critic's limit is more than 25°.

## Files (piece ownership)
| File | Change |
|---|---|
| `Traversal/Anim/WHHeroV2AnimInstance.h/.cpp` | Arm swing fix, per-layer arm overrides, touchdown dip, dash → BoostHold, brake entry, takeoff crouch timing, slam flip re-timing with runtime clip analysis, carry (arms overhead + anchor from the evaluated hands) |
| `Traversal/WebTravCharacter.h/.cpp` (HeroV2 only) | `HeroV2MaxPitchDeg` 20 → 45. Takeoff plant/catch-up of the v2 mesh root in `HeroV2Frame`. New members `HeroV2FloorZ`, `HeroV2TakeoffT`, `bHeroV2OnGround` |
| `Flight/WHRescueDirector.h/.cpp` | `SetOverheadCarryHero()` flag, set by the v2 instance only. With the flag: a catch from above needs `CraneTouchAboveCm` (300); lives are saved on the set-down, not the catch. Without the flag (v1, `-WHHeroV2=0`) the r4 rules apply unchanged |

`FlightFrame`, the camera-event block, WHBreachDirector, WebTravCamera and WHFlightComponent were not touched. `-WHFlight=0` never reaches any of this code.

## 1. T-pose flash (fl03 0.20-0.33 s, fl09 1.55 s)
**Cause:** the plain per-bone crossfade from hover (arms down) to fly (arms overhead along the body). The collar and shoulder differ by about 63° and 84°, and the shoulder-arc path passes through the side.

Offline, hover→fly at 60 fps, minimum arm angle per frame:
- old: 73, 65, 57, 49, 40, 32, 23, 15, **8, 7**, 14…
- new: never below **54**

The same fix applies to fly→hover and hover→launchUp (old minimum 22°, new minimum 60°).

**Fix (proxy, `bArmFix`):** each layer's upper-arm direction is taken in the collar-parent (spine3) frame. Where the weighted mean cancels (1 − |mean| between 0.2 and 0.45), the blended shoulder is turned toward the mean plus the chest's forward, so the arm swings up in front. The fix does nothing when the layers agree.

**Dash** is now AS_BoostHold (parallel fists) instead of AS_Fly ×1.6. Dash ↔ hover/launchUp uses the new `BlendDashUpright` 0.35 s (was 0.15 s, which gave the 90° in 0.15 s in fl09). Offline, hover→dash keeps the arm angle at 56° or more.

**Takeoff crouch:** AS_Takeoff's crouch itself has arms straight out (6-16°). It now gets the idle arms until clip t = 0.5, then its own arms by 0.62. The minimum is 48°.

## 2. Brake (fl08)
**Cause:** AS_Brake from 0.15 to 0.95 s rolls onto his left side. The head direction is 63-83% lateral, which is the "lying on his side" seen at 3.8-4.2 s.

**Fix:** the clip is entered at `BrakeEnterT` 1.5 s (upright, knees 28/48°) with `BlendToBrake` 0.3 s. It plays at 1× to its end (hover pose).

Offline: tilt from vertical is under 20° 0.22 s after the brake press, and the arm angle stays at 59° or more. In fl08 the speed drops under 1 m/s about 0.15 s after the press, so he is upright about 0.07 s after the stop. The target is ≤ 0.35 s.

## 3. Slam (fl11)
**Runtime analysis** (`AnalyzeLandClip`): at init, AS_LandHero's pelvis height over the lower foot is sampled. `LandFeetT` is the first frame at half the kneel plateau; `LandImpactT` is the first at 92% of it.
- Offline values: 0.43 / 0.49 s. The old impact frame of 0.37 s was mid-flip, at tilt ~92°.
- Out-of-range results keep the tunables.
- Log line: `WH_HEROV2 land clip: kneel plateau … feet-first t=… impact t=… -> used`.

**Dive sequence:**
- Hold at 0.2 s while far.
- The flip starts at time-to-impact ≤ `LandFlipLeadT` 0.36 s. Time-to-impact now includes the eased fall acceleration.
- The rate is set so he is feet-first `LandFeetLeadT` 0.16 s (about 9.6 frames) before contact. The rate is clamped between 1× and 3×.
- He then creeps to the contact frame.
- Mesh pitch freedom fades with the flip.
- The ground lock ramps in with flip², so the feet meet the floor on the contact frame.

At 95 m/s the flip starts about 34 m up and lasts about 0.2 s (12 frames).

## 4. Path pitch
`HeroV2MaxPitchDeg` 45 (was 20); the 8 /s easing is unchanged. In AS_Fly the ankles→head line is +3° (FK), so a ±30° path gives about 3° of error. Pitch freedom still fades out through the AS_LaunchUp blend from 50° to 70°.

## 5. Takeoff / touchdown
**Takeoff:**
- AS_Takeoff starts at 0.35 s (crouch) with rate 1.5 and `BlendToTakeoff` 0.06 s.
- `HeroV2Frame` holds the v2 mesh feet on the take-off floor for `TakeoffPlantT` 0.12 s, then rejoins the capsule over `TakeoffCatchT` 0.15 s while the push-off plays. The ground lock follows the same curve.
- Offline: knees are above 100° from about 0.03 to 0.15 s, which is about 7 frames.
- This is visual only: telemetry vz is still 0 → 16 m/s in one frame, because the flight body is in WHFlightComponent.

**Touchdown:** a soft landing (air → groundIdle) blends the non-arm bones toward AS_Takeoff@0.3 s.
- Weight: 0.3 + 0.03/(m/s) of descent, maximum 0.6.
- In over 0.08 s, out over 0.35 s.
- Offline: knees go from 28° (idle) to 53° at weight 0.3 and 66° at 0.45.

## 6. Rescue carry (fl17)
**Arms:** while the director reports a carried load, every layer gets AS_LaunchUp's arms (fists overhead), blending in over 0.25 s and out over 0.3 s.

**Anchor:** in `NativePostEvaluateAnimation`, the anchor is built from the pose just evaluated:
- Load bottom face = the `left/right_middle1` midpoint plus 6 cm along the arms.
- Z = shoulders→hands.
- Y = chest forward, which the director's set-down reads.
- X = the 4 m length across the shoulders.
- It is passed to `SetCarryAnchor` each frame.

**Swing:** for 0.45 s after the catch, the load travels from its caught pose round the chest's front. Its distance from the body capsule (feet→head, r 30 cm) never drops below the box's separating distance plus 25 cm.

**Director:** with the v2 flag, a catch from above (hero centre more than half the load height + 0.95 m above the load centre) needs 3 m instead of 6 m. In the fl17 route that is about 1.3 m above the top face, before contact. Lives are saved on the set-down.

**Not fixed here (root / case owner):** the fl17 keys level out at 160 m and descend through the crane jib, which is at about 142.6 m with no collision. That causes the jib-through-chest at 16.5-16.75 s. Changing the route in `tools/invincible/make_flight_cases.py` (not this piece) would avoid it: level at the load's height (~135 m) and brake beside it, which gives a 6 m side catch.

## What to check per case
- **fl03-fl10, fl12, fl14, fl16 starts:** no arms-out frame in 0.033 s bursts across hover→fly. The arms should swing forward-up. `WH_HEROV2 state fly … blend=0.30`.
- **fl09:** `state dash clip AS_BoostHold`, parallel fists; dash→hover blend 0.35, no 90° in 0.15 s.
- **fl08:** `state brake clip AS_Brake clipT=1.50`; upright under 20° within 0.35 s of under 1 m/s; never on his side.
- **fl11/fl12:** `land clip … used` line; head-first held dive, feet-first ≥ 8 frames before `WH_FLIGHT heroLand`, no 2-frame snap, feet on the floor at contact.
- **fl07:** body line within 10° of ±30° climb/dive.
- **fl01/fl02/fl13:** about 7 frames of crouch on the floor before he leaves (the mesh lags the capsule ≤ 0.27 s); knee dip on touchdown.
- **fl17:** `load caught … from above/below` line; load above the head with both fists under it from catch to set-down; follows through the dive; `WH_RESCUE saved … (load set down)`.
- **`-WHHeroV2=0` / `-WHFlight=0`:** unchanged logs/visuals (no `land clip` line, catch line without "from").

New tunables (`-WHHeroV2Tune=`): BlendDashUpright, LandFeetT, LandFlipLeadT, LandFeetLeadT, LandFlipMaxRate, TakeoffRate, TakeoffPlantT, TakeoffCatchT, TakeoffArmsT0/T1, BrakeEnterT, DipPoseT, DipPeak, DipPeakPerMps, DipMax, DipInT, DipOutT, ArmFixStrength/Lo/Hi, CarryInT, CarryOutT, CarrySwingT, CarryFistCm, CarryClearCm. `TakeoffUnlockT` is removed.

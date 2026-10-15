# Round 3 — hero piece (builder C) notes

Source edits only. No Unreal, Blender, GPU, build or git was run. Nothing is compiled or rendered yet, so every number below is a
design value taken from the code. None of it has been measured.

## Files changed

| File | Change |
|---|---|
| `Source/WebHomage/Traversal/Anim/WebTravAnimInstance.h` | New frame fields: `FlyCarryW`, `FlyCarryHand[2]`, `FlyCarryFing[2]`, `FlyCarryPole`, `FlyDiveAng`, `FlyStandW`, `FlyLandT`, `FlyBank`, `FlySecW`, `FlySpeedK`, `FlyWallSide`. New private members: carry state, `UpdateCarry`, `CarryAxes`, `SlamTimeToImpact`, hero-landing clock, dive roll state, fist swap. Forward declarations of `AWHRescueDirector` and `USkeletalMeshComponent`. `ResetForSequenceStart` resets the new state. |
| `Source/WebHomage/Traversal/Anim/WebTravAnimInstance.cpp` | New includes: `Flight/WHRescueDirector.h`, `Traversal/WebTravCharacter.h`, `Traversal/WebTraversalComponent.h`, `Engine/SkeletalMesh.h`, `Engine/World.h`. Rewrote the game-thread flight channel block and the procedural flight block in `Evaluate`. Added `UpdateCarry`, `CarryAxes` and `SlamTimeToImpact`. `fly_landHero` now plays `idle` instead of `landHard`. |
| `Source/WebHomage/Flight/WHRescueDirector.h/.cpp` | New `SetCarryAnchor`, `GetCarriedLoad`, `FWHEmergency::LoadQ/SettleQ/SettleFromQ/SettleFromCm/SettleT/SettleDur`, and tuning values `SetDownClearCm` (70) and `SetDownSpeedCm` (600). Carry placement, set-down and settle are rewritten. The load now gets a rotation (`SetWorldLocationAndRotation`). |
| `Source/WebHomage/Traversal/WebTravTypes.h` | `FWebTravAnimFlight` gets two new fields, `WallSide` (0) and `WallDist` (99). Nothing fills them yet, and the defaults change nothing (see the requests below). |

`tools/invincible/make_flight_cases.py` (fl17) was not touched; the root owns it this round.

## 1. Rescue carry (critic r2 top-8 #6, fl17 14.4–22 s)

- **Carry pose.** The hero holds the load overhead and slightly ahead of his head.
  - Hands: from each shoulder joint, in the direction 0.82 body-up + 0.57 body-forward, at 88 % of arm length, 6 cm wider than the shoulders.
  - Load: its bottom face rests on the hands, about 3 cm above the wrists. Its centre is 0.45 half-depths ahead of the hands. The 4 m axis runs across the shoulders, depth along body forward, height along body up.
  - All of this is computed in mesh component space from the reference pose (`CarryAxes`, cached once).
- **What that looks like.**
  - Hover: an overhead lift in front of the face.
  - Fly line (body up = direction of travel): the load leads ahead of his fists.
  - Dive: the load leads below him.
  - It never sits under his feet or in his legs. In the usual chase views it is on the far side of the hero from the camera.
- **Catch.** The load is pulled from where it was touched into the carry pose over 0.45 s (ease-out). Hand targets are expressed in the load's own frame, so the hands reach toward it and then stay on it.
- **Same-frame placement.**
  - The anim instance (game thread, inside the hero mesh tick) calls `AWHRescueDirector::SetCarryAnchor(mesh, LoadInMeshCS)`.
  - `TickCrane` runs in TG_PostPhysics, after the mesh. It renders the load at `LoadInMeshCS * mesh->GetComponentTransform()`.
  - Hands and load therefore use the same transform in the same frame, with no smoothing lag (r2 lerped with exp(-10 dt)).
  - If no anchor is fresher than 0.2 s, the r1 under-the-hero fallback still runs.
- **Arms.** A carry channel `FlyCarryW` (0.12 s in, 0.25 s out). While it is on, every other arm channel is scaled by `1 - FlyCarryW`. Elbows point down and out; fingers point forward along the bottom face. Legs keep their flight goals.
- **Set-down** (interact, or 10 s):
  - The load is levelled to its heading, which is the hero's facing. Fallbacks for that heading: body up projected horizontally, then the hero→load direction.
  - It slides so its near face is 70 cm ahead of the hero's centre, inside 0.6 s.
  - It comes to rest on the **highest** surface under its footprint (5 downward traces: centre + 4 corners at 90 %), so it never sinks into a step or roof edge.
  - Vertical motion is eased over |dz| / 6 m/s, clamped to 0.6–4 s.
  - New log lines: `load set down at (...) over X s, hero at (...)` and `load rests at (...)`.
  - A straight descent after the press lands him beside the load (about 34 cm gap to his capsule), not on top of it.

## 2. Secondary motion (pose_sig ≤ 0.13 m: "rigid statue")

All on the flight clock `FlyT`. The weight `FlySecW` is 1 in fly, 0.8 in boost, 0.5 in dash, × 0.35 while carrying, and 0 otherwise (0.4 s ease).

**Legs**
- Scissor along the chest axis, in antiphase: 0.55 Hz at cruise, rising to 0.9 Hz at full boost.
- Amplitude 0.10–0.16 leg lengths, × (1 − 0.4 × stretch), breathing ±20 % at 0.13 Hz.
- At cruise (SpeedK 1, stretch 0) each foot moves about 0.23–0.29 m peak-to-peak (leg length ≈ 0.9 m assumed).
- Knee drift: alternating, 0.29 Hz, up to 0.18 knee share.

**Free arm**
- Lateral drift ±0.24 (0.37 Hz) and chest drift ±0.14 (0.23 Hz), × (1 − 0.5 × stretch).
- About 0.27 m lateral peak-to-peak at the hand at cruise.

**Leading fist and head**
- Fist drifts ±0.06 (0.31 / 0.41 Hz) and turns 0.15 × bank share into the turn.
- Head yaws ±0.10 rad at 0.13 Hz.

**Body ripple**
- spine, spine1, spine2 lean toward the chest or back by 0.045 rad as a travelling wave (0.7 Hz, 0.9 rad phase step), plus a 0.03 rad roll at 0.43 Hz.

**Fist swap**
- After 6.5 s of near-level fly (|bank| < 0.25 rad, not carrying), the leading fist changes sides (FlyFistR eases over 0.25 s). The swap resets on the ground, but not during a hero landing.
- In fl03 that is expected at about 6.6 s of fly.

**Banks**
- Bank share = eased bank / 0.9 rad, so it is full at about 52° (the max bank is 70°).
- Outer side (left in a right turn):
  - free arm opens by 0.6 lateral (≈32°);
  - leg spreads 0.22 leg lengths out, and its "legs together" pull drops by 70 %.
- Inner side:
  - knee bends +0.35;
  - leg pulls 0.04 leg lengths in;
  - free arm tucks 0.3 toward the chest.

**Hover** (fl01 "stiff mannequin")
- Legs drift forward and back, alternating, 0.06 leg lengths at 0.27 Hz.
- Arms sway sideways ±0.06 at 0.21 Hz.

**Limits**
- In boost the amplitudes are smaller by design (tighter line): foot about 0.13 m and free hand about 0.10 m peak-to-peak. The ≥ 0.25 m test is expected to pass in fly/cruise; boost alone is not expected to reach it unless a fist swap falls in the window.

## 3. Slam and landing (critic r2 #5, fl11 1.5–3.3 s)

**Dive roll (`FlyDiveAng`)**
- The whole body rolls forward about the hips joint (`RotateCS(hips)`); the root and collision are unchanged.
- Target angle = the angle between the root's body-up and the velocity, capped at 2.9 rad (≈166°), reached at 11 rad/s (about 0.26 s).
  - Because it uses the angle the root is still missing, a root that the flight controller already pitches head-down is not rotated twice.
- **Righting:** when the traversal ground index (`TravWorld.GroundHeight` under the hero / fall speed) says impact is less than 0.28 s away, the roll continues forward to 2π (a front half-flip onto the feet).
  - Rate = remaining angle / (time to impact − 0.03 s), clamped 10–26 rad/s.
  - One roll per slam.
  - If the slam ends earlier with the roll more than half done, it finishes at 22 rad/s; otherwise it unwinds.
- **Slam arms:** the leading fist drives at the ground (0.85 world-down + 0.25 body-up); the free arm sweeps back along the side toward the feet. Legs use the straight superman line, so they point up while inverted.

**Hero landing**
- `fly_landHero` now uses `idle` under the procedural kneel. The landHard squat was the r2 "frog squat" visible as the kneel faded.
- Landing clock `HeroLandT`: it starts at the landHero node and keeps running through the traversal's idle hand-over (the landHero sub ends at 0.95 s) while the hero stands still in flight mode.
- Timeline:

| Time after impact | Pose |
|---|---|
| 0–1.25 s | Kneel held |
| 1.25–1.7 s | Rise |
| from ~1.35 s (0.5 s blend) | Heroic stand, until he moves or takes off |

- At impact + 1.0 s the kneel weight is 1.
- Kneel geometry:
  - Hips at 0.85 × thigh + 5 cm (r2: thigh + 6).
  - Kneeling ankle at 10 cm height, 0.527 × thigh − 0.97 × shin along the front, so the knee lands on the ground about 0.53 thigh lengths ahead of the hip.
  - Torso fold 0.38 / 0.36 / 0.26 rad (r2: 0.30 / 0.25 / 0.15).
  - Up to 0.35 rad extra fold if the fist-side shoulder is still out of reach of the ground, plus a 0.22 rad shoulder-girdle drop.
  - 6 cm impact dip over the first 0.3 s.
  - Head down at impact, looking up from 0.55 to 0.9 s.
- Heroic stand: feet 7 cm wider than idle and planted on the ground, legs straight, fists on hips with elbows out, chest +0.07 rad, chin +0.06 rad, slow head look ±0.22 rad (0.12 Hz).

## 4. Clipping (fl16 3.55 / 7.25 s): pose notes only, no collision change

Pose changes that reduce how far the body sticks out toward a facade while sliding:
1. Lead with the fist on the side away from the wall. A raised wall-side reach was the "limp one-arm reach" the critic saw entering the window plane at 3.85 s.
2. Tuck the wall-side free arm under the chest; cancel its bank flare.
3. Pull the wall-side leg in to the line.
4. Optionally roll the shoulders away from the wall.

Items 1–3 are implemented behind `FWebTravAnimFlight::WallSide` / `WallDist` (a wall within 1.5 m, eased over 0.12 s). They do nothing until the flight controller fills those fields (request below). The head itself cannot move much farther from the wall than the body centre, so collision standoff (critic test ≥ 0.3 m) stays the main fix.

## What the root should check in captures

- **fl17**
  - From the catch to the set-down, both hands are under the load's bottom face in every frame.
  - The load turns with his body: overhead in hover, leading in fly and dive, never under his feet.
  - The load is in the chase frame during the dive.
  - The set-down slides the load about 1.6 m ahead (near face at 0.7 m) and levels it. It rests on the surface, and the touchdown is beside it.
  - Log `WH_RESCUE ... set down at ... hero at ...` and `... load rests at ...`.
  - Risks:
    - In hover the load top is about 2.9 m above the hips, so the chase camera may cut its top edge (see the camera request).
    - The 4 m load has no collision and can pass visually through facades on tight routes.
- **fl11**
  - 1.5–1.8 s: rolls head-down.
  - About 1.8–2.1 s: inverted, fist leading.
  - Last ~0.28 s: front half-flip onto the feet.
  - Kneel through about +1.25 s after impact, rise, heroic stand; no frog squat.
  - Watch: the righting peaks at up to 26 rad/s. If it reads as a pop, raise the 0.28 s trigger (one constant in `NativeUpdateAnimation`).
  - Watch: kneeling-knee ground contact (geometry puts the knee centre about 5 cm above the ground).
  - Watch: whether the fist touches the ground; with a short arm rig it may stay a few cm above it, because TwoBone clamps reach.
- **fl12:** same landing path (no dive roll).
- **fl03 / fl05**
  - pose_sig limb range over 4 s windows in fly.
  - Fist swap at about 6.6 s in fl03.
  - In fl05 banks, the outer free arm and outer leg spread wider than in level flight; the inner knee bends.
- **fl01 / fl08:** hover legs drift and arms sway (small, 0.06).
- **Compile watch-points.** These could not be compiled here:
  - `TWeakObjectPtr<const USceneComponent>` in the director header and `TWeakObjectPtr<AWHRescueDirector>` in the anim header, both with forward-declared types.
  - `USkeletalMeshComponent::GetSkeletalMeshAsset()`.
  - `-Wshadow`: new local names were checked against the enclosing scopes and the class members.

## Cross-file requests

1. **Builder A (WHFlightComponent):** fill `FWebTravAnimFlight::WallSide` / `WallDist` while sliding along or brushing a facade (fl16).
   - `WallSide = clamp(dot(-HitN, BodyQ.GetRightVector()), -1, 1)`.
   - `WallDist` = body centre to wall in metres.
   - Otherwise leave them at 0 / 99.
2. **Builder A (WHFlightComponent):** the slam root may stay upright as in r2. The anim adds only the angle the root still lacks to point the head along the velocity, so pitching the root head-down too will not double the rotation.
3. **Builder A (camera):** in carry, the load centre sits about 1.6 m along body-up and 0.9 m along body-forward from the hips. A carry framing that raises the look target about 1 m, or pulls back about 1 m, keeps the whole load in frame in hover.
   - Signal: `AWHRescueDirector::GetCarriedLoad()` returns true.
4. **Root (telemetry, WebTravCharacter.cpp):** to measure the fl17 test, log per frame:
   - the anim's `FlyCarryW`;
   - the distance from each palm (hand bone + 7 cm along the finger axis, as the existing palm code does) to the load box (`GetCarriedLoad` transform and half extents); contact = ≤ 5 cm;
   - `FlyDiveAng` and `FlyLandT` for fl11.

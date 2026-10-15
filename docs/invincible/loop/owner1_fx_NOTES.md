# Owner feedback 1 (2026-10-15 playtest): effects and flight feel, builder notes

These are source edits only. Nothing was compiled, launched, rendered or run in Unreal.

**Process deviation:** one read-only `git diff --stat` was run by mistake. The brief says no git. No git command changed anything.

All numbers below are design values worked out from the tunables. None of them are measurements. `-WHFlight=0` (the legacy hero) never calls `FlightFrame`, never spawns the director and never steps the flight component. Every new camera field defaults to 0 or false, so legacy behaviour is unchanged.

## Files changed

- `Flight/WHFlightComponent.h/.cpp`: super boost, double-tap dive, nose (attitude) steering, momentum, climb energy, anim outputs.
- `Traversal/WebTravCamera.h/.cpp`:
  - attitude-follow yaw;
  - flight FX channels (FOV past the 75° cap, shake floor, blur floor, charge pull-in);
  - `FlightBoom()` (kick, FOV punch, launch hang);
  - `bFlightHold`.
- `Traversal/WebTravCharacter.cpp`, inside `FlightFrame` only:
  - event mapping (`sonicBoom` → `FlightBoom`, `superCharge`, `heroDive`);
  - pushes the flight tunables to the camera;
  - `BreachDirector->SetFlightFx`.
- `Flight/WHBreachDirector.h/.cpp`:
  - charge slow-mo and gathering vapour;
  - bigger boom;
  - facade glass/dust shake;
  - super-speed streaks, body trail, contrails, street wake;
  - vapour shapes: ball and streak;
  - pool cap is now `MaxVapours` (was a fixed 24).
- `Traversal/WebTravTypes.h`: fields added to `FWebTravAnimFlight` only (`ChargeK`, `SuperK`, `LaunchK`, `DiveK`).
- `Scripts/build_invincible_fx.py`: new `M_InvStreak`.

## Controls

**1. Shift / L3 (from fly or hover; any airborne flight state except the slam)**

- **Charge.** Lasts `SuperChargeTime` 0.42 **real** s. The charge timer divides by the world time dilation.
  - He stops and hangs (sub `brake`) and turns to the aim.
  - The body leans back by `SuperChargeLean`.
  - The world slows to `SuperChargeSlowMo` 0.6. `-WHNoSlowMo` turns this off.
  - The camera holds the flight framing and pulls in by `SuperChargePullM` 1.1 m.
  - A vapour shell and inward streaks gather on him.
- **Sonic boom and launch.**
  - Launch speed is 0.8 × `SuperSpeed`, so 240 m/s.
  - Direction is the stick relative to the nose, which the camera follows. With no stick input it is the nose/aim.
- **Holding Shift** keeps him at `SuperSpeed` 300 m/s.
  - Steer with the mouse or stick.
  - Lateral acceleration is `SuperLatAccel` 110 m/s², which gives a turn radius of about 818 m at 300 m/s.
- **Releasing Shift** decays him to cruise at `SuperDecelRate` 2/s, taking up to `SuperDecelTime` 1.5 s.
- **Cooldown:** `SuperCooldown` 2 s.
- **Cancels:** E (brake), F (slam), double-tap Space or a landing ends the boost.
- **Removed:** the old held Shift boost to 160 m/s, and the boom on crossing 120 m/s.

**2. Space twice within `DoubleTapTime` 0.3 s while airborne**

- He dives straight down (sub `slam`, so the anim's head-first roll and righting apply) into the superhero landing.
- Downward acceleration is `max(DiveAccel 160, 2h / DiveTime²)`, with `DiveTime` 2.2 s and a cap of `DiveMaxSpeed` 600 m/s. Worked examples:

  | Height | Time to floor | Impact speed |
  |---|---|---|
  | 100 m | 1.1 s | 179 m/s |
  | 500 m | 2.2 s | 455 m/s |
  | 1000 m | about 2.4 s | — |

- The ground takeoff press never opens the double-tap window.

**3. Flight-sim feel (fly line, RMB held)**

- The mouse or right stick moves the **nose**:
  - `AimYaw` and `AimPitch`, scaled by `LookYawK` / `LookPitchK`;
  - the nose can lead the travel heading by at most `NoseLeadMaxDeg` 60°.
- Stick X turns the nose at `StickTurnRate` 70°/s and adds `StickRollDeg` 20° of roll.
- **Turn rate** is `min(TurnRateSlow, FlyLatAccel / v)`, with `FlyLatAccel` = 60 m/s². Turn radius is about 50 m at 55 m/s and about 427 m at 160 m/s.
- **Climb energy** uses `ClimbEnergyK` 1.2:
  - a 30° climb settles at about 52.6 m/s;
  - a 45° dive settles at about 61 m/s.
- The body points `NoseBodyK` 0.2 of the way toward the nose.
- **Chase camera:**
  - its yaw follows the travel heading plus `CamLeadK` 0.35 of the nose lead, with a `CamYawLagT` 0.32 s spring;
  - roll is `CamRollK` 0.18 × bank, capped at `CamRollMaxDeg` 12°.
- **Speed feedback:**
  - FOV widens by `FlyFovAdd` 9° over 40–160 m/s;
  - shake floor is `SpeedShake` 0.07;
  - wind streaks scale with speed from 60 m/s.
- **Super-speed feedback:**
  - `SuperFovAdd` 14° (total capped at `CamFovCap` 90°);
  - `SuperShake` 0.16;
  - `SuperBlur` 1.4.
- **Boom:**
  - `BoomFovDeg` 12° FOV punch;
  - launch hang of `LaunchLagT` 0.14 s, during which the lens moves at `LaunchLagK` 0.35 of the hero's speed.
- **Unchanged:**
  - Hover keeps camera orbit and camera-relative strafe.
  - Hands-off level flight holds `AimPitch`, so altitude holds.
  - Breach and slide paths are as before.

All flight tunables above are float `UPROPERTY`s, so `-WHFlightTune=Name=V` works for them.

The director tunables are not on the flight component and have no command-line switch: `StreakRate`, `FastStreakRate`, `StreakOpacity`, `TrailEvery`, `TrailOpacity`, `WakeMaxH`, `BoomRingRadM`, `BoomShakeRadM`, `GatherOpacity`, `MaxVapours`, plus the boom cone values (raised to length 9 m, radius 3.2 m, follow 0.6 s, life 1.0 s).

## What to look for in game

- **Shift from hover and from cruise:**
  - about 0.4 s hang with slow-mo, a tight camera and gathering vapour;
  - a white flash, then the cone and a 24 m ring left behind as he pulls away from the lagging lens;
  - glass and dust off facades within 45 m;
  - streaks rushing past, a body trail, and street dust when he is below 35 m.
- **Mouse flick at cruise:** the hero banks into a wide turn. There should be no instant reversal, and the camera should trail and roll slightly.
- **Double-tap Space from a rooftop height:** a fast dive, then the crater landing.
- **Logs to grep:**
  - `WH_FLIGHT super charge`
  - `sonic boom (super launch)`
  - `double-tap dive`
  - `boom shake`
  - `flight fx (owner feedback`
- **Risks to check:**
  - Additive streak brightness against the sky (`StreakOpacity`, `Gain`).
  - A camera inside the gather or boom shells washing out the frame (`GatherOpacity`, `BoomOpacity`).
  - Suite cases fl04 and fl15 (old Shift boost) and fl05/fl06 (look steering) now behave differently and need new scripts or expectations.

## Anim requests (hero piece; fields in `FWebTravAnimFlight`)

- **`ChargeK` 0..1** (sub `brake`): the coil. Knees drawn up, fists pulled to the chest, head down, shoulders hunched, slight back lean.
- **`LaunchK`** (1 at the boom, decays over 0.5 s; sub `boost`): explosive extension. Lead fist punched forward, body fully stretched, legs together.
- **`SuperK` 0..1** (sub `boost`): a tighter boost stretch. Both fists forward, or the lead fist forward with the trailing arm pinned to the side.
- **`DiveK` 0..1** (sub `slam`, double-tap dive only): an arms-forward head-first dive before the existing righting roll.

## Asset list (`build_invincible_fx.py`, still idempotent, still ends `SM2_BUILD_OK: build_invincible_fx.py`)

Rebuilt in place: `M_BreachHole`, `M_CraterDecal`, `M_InvVapour`, `M_InvDust`, `M_InvChunk`.

**New:** `/Game/Invincible/FX/M_InvStreak`

- Surface, translucent ADDITIVE, unlit, two-sided.
- Parameters: `Dir`, `HalfLen`, `Opacity`, `Color`, `Gain`, `EdgePow`.
- It is optional: without it the streaks use `M_InvVapour`.
- The `streak` HLSL body was compiled as C++ through a clang shim and checked on a grid: the output stays in 0..0.4 and falls to 0 at both ends. That checks syntax and number ranges only, not the real shader compiler.

## Requests to the root (files outside this piece)

- Telemetry columns:
  - `Flight->SuperCount`, `Flight->DiveCount`, `Flight->SuperKNow()`, `Flight->ChargeKNow()`;
  - `Cam.FlightFxFovS`, `Cam.bFlightAttitude`.
- HUD control hints for Shift and double-tap Space, if the HUD lists controls.

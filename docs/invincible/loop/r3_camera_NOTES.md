# Round 3 — camera piece (builder A) notes

These are source edits only. Nothing was compiled, run or rendered (the brief does not allow it), and no git commands were run. The numbers below are design estimates from the geometry, not measurements.

## Files changed

- `Traversal/WebTravCamera.h`, `Traversal/WebTravCamera.cpp`
- `Flight/WHFlightComponent.h`, `Flight/WHFlightComponent.cpp`
- `Traversal/WebTravCharacter.cpp`: only the body of `AWebTravCharacter::FlightFrame` and the `bBreachHold` block in Tick.

## 1. Flight framing ("blue egg", critic r2 top-8 #3)

**Camera (`WebTravCamera`)**

- New public state: `bFlightLine`, `FlightBank` and `FlightK`, plus tuning doubles. All the tuning doubles are listed in `SetTune` (`-WHCamTune=FlightElevDeg=...`).
- **`Update` (weight):** `FlightK` is a spring toward `Smooth(speed, 8..22)`. The target is non-zero only while `bFlightLine` is set and the mode is Air. It eases in over 0.45 s and out over 0.6 s.
- **`Update` (roll):** the camera rolls slightly with the hero's bank: `-FlightBank*0.12`, total capped at 8°, scaled by `FlightK`.
- **`ComposeChase`, after the trick blend:** builds a three-quarter rear spot.
  - Elevation: `FlightElevDeg` (24°) above the spine line. The spine line is the fly line's pitch, smoothed over 0.25 s. The world elevation is kept within -12°..55°.
  - Azimuth: `Yaw + 180° - side*26°`. It hangs off the camera `Yaw`, so the recenter behind the travel and the player's look input still move it.
  - Lag: the existing follow lag `LagOff` is added at 0.6×.
  - Blend: the spot is blended onto the chase spot by `FlightK` in polar coordinates about the hero (azimuth, horizontal radius, height). All later collision and visibility passes still apply.
- **Distance:** R = projected hero height / (2·tan(Fov/2)·`FlightPixH` 0.24).
  - Projected hero height = 2.0 m·sin(elevation over the spine)·cos(side) + 0.4 m·cos(elevation over the spine).
  - R is clamped to 2.8–5.2 m, plus the launch-kick pull-back.
  - `HeroProjH` only corrects the distance (±25 %) when it leaves the band 0.27–0.46.
  - Estimates: about 3.9 m at cruise (vFOV ~60°) and about 3.45 m at boost (vFOV ~67°). In both cases the model gives a hero about 0.24 of the frame height.
- **Side choice:**
  - Default is the right rear.
  - Above 30° of bank the camera goes to the outside of the turn.
  - If a facade is within 6 m on the camera side and the other side is at least 3 m more open, the camera moves to the other side.
  - A side change holds for 1.0 s and is eased by a 0.8 s spring, so it is never a cut.
- **Orientation:**
  - Framing target `FlightSFrame` is 0.52. The existing 22° look-down clamp leaves the horizon in roughly the top 15 % of the frame at cruise.
  - The view yaw leads 6° toward the travel.
- **Chase closed loop:** it rests while `FlightK` ≥ 0.5, because `HeroProjH` then measures the flight view, not the chase.

**`FlightFrame`**

- Sets `Cam.bFlightLine` when the mode is Air and the flight sub is fly, boost or breach.
- A dash counts only if `FlightK` is already above 0.5. This way a dash from a hover does not swing the lens (fl09).
- Sets `Cam.FlightBank` from `Anim.Flight.Bank`.
- `-WHFlight=0` never calls `FlightFrame`, so `FlightK` stays 0 and every new term is multiplied by 0. The legacy behaviour is unchanged.

**What to check (fl02–fl07, fl15)**

- The camera sits ≥ 15° above the spine line and off to one side, with head, leading arm and both legs readable in ≥ 90 % of cruise frames.
- The pixel-mask hero height is ≥ 0.18, with bbox around 0.3–0.4.
- No position or yaw pops when entering or leaving a fly line or changing side.
- Roll stays ≤ 8° in fl05.
- Look input still steers in fl06.
- fl17: the closer and higher camera versus the carried load (hidden-frame count).

## 2. fl14 breach exit (critic r2 top-8 #2)

**Flight component (`WHFlightComponent`)**

- **`StartBreach`:**
  - The exit speed is now `max(1.05·BreachSpeed, BreachKeep·entry)`. Before, it was `max(0.9·BreachSpeed, ...)`, which gave 44 m/s from a 55 m/s cruise entry. That was under `BreachSpeed`, so the next facade stopped him.
  - **Chaining:** if a solid starts within `exitV·BreachCooldown + 4 m` (≥ 6 m) past the exit, the breach continues through it as one breach (up to 4 links, `BreachMaxDepth` 80 m in total). The time bound is unchanged: `BreachV = len / BreachMaxTime`.
  - If the next solid is too deep, or its exit would be under the street, the first exit is kept.
- **`MoveAndCollide`:**
  - Inside the 0.25 s post-exit cooldown, a new facade ahead is breached too. "New" means its inward normal points along the last breach direction (dot > 0.3).
  - Contacts within 20° of the facade plane (dot(dir, −n) ≤ 0.34) now slide instead of breaching. This keeps a fast slide along a wall from staging a 1 m breach with its own hold and cut.
  - **New `DeflectFree`:** when a fast, fly-held breach attempt fails (or a pin punch fails), the hero keeps his speed and turns along the facade.
    - Direction: the tangential part of the travel if it is at least 0.5 of the speed. Otherwise up, left or right along the wall, whichever has the longest clear 15 m sweep (ties go up).
    - After a failed punch, the speed is at least half the cruise speed.
- **Breach hold block in Tick:** the cut also waits (still ≤ 0.4 s) until the camera's first frame after `Reset` will be clear. New `Cam.CutSpotClear(...)` checks the spot that frame will use (the flight spot while flight framing is on, otherwise the chase spot): out of every solid (`Inside`, sphere 0.4) with a clear line to the chest. There is still exactly one `Cam.Reset` per breach. `FlightK` is not reset by `Reset`, so the frame after the cut is already the flight view.

**What to check (fl14, fl15, fl17)**

- Speed stays > 40 m/s after every exit with fly held.
- No frame has luma < 40 outside the breach window.
- Camera movement relative to the hero is < 1.5 m per frame, except one cut per breach.
- The hero is visible right after the cut.
- `BreachCount` and the logged breach depth: a chained breach logs one longer depth.
- fl17: count breaches. The grazing-contact rule may remove the accidental glass breach, but that is not verified.

## 3. Hover touchdown (fl01, fl13; critic r2 top-8 #8)

- In the hover branch of `StepAirSub` with drop held, the descent target and the damped velocity are capped at `sqrt(TouchdownV² + 2·TouchdownDecel·max(0, h − TouchdownSlowH))`. Defaults: 1.4 m/s, 12 m/s², 0 m.
- This is constant deceleration from 10 m/s at about 4.1 m up to 1.4 m/s at the floor.
- Estimate: about 0.71 s over the last 4 m, which is 0.3 s more than the old 0.4 s.
- The 0.35 m snap-down band was reduced to 0.05 m. At the capped speed a 0.35 m snap started from about 3.2 m/s and moved the body 0.35 m in one step.
- **Check:** vz at the last airborne frame ≤ 2 m/s in fl01 and fl13, and touchdown time over the last 4 m.
- **Conflict between tests:** the critic's original r2 test #8 is |vz| ≤ 2 over the final 2 m, which is stricter than the brief's test. To meet it at about 0.95 s extra, use `-WHFlightTune=TouchdownV=1.95,TouchdownSlowH=2.0,TouchdownDecel=26`. That margin is tight against the 1.0 s budget.

## Requests to the root (files I do not own)

- **Telemetry:** please add `Cam.FlightK`, `Cam.FlightSideS` and `Cam.FlightDistS`. A camera elevation over the spine line (angle between hero→camera and −velocity, signed by the up side) would let the ≥ 15° test be checked from CSV.
- **`ProjectHeroH`:** it pads every bone by ±10 cm and includes all bones (twist, IK, root). This is likely the source of the 1.8× overstatement. A head/hands/feet/hips-only projection with a smaller pad would bring `hero_bbox_h` closer to the pixel mask (critic r2 #3 asks for within 15 %). The camera's band 0.27–0.46 assumes the current overstatement.
- The pose itself (head up, leading arm forward, separated legs) belongs to the hero piece. The camera only gives the angle and the size.

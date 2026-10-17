# r8 notes: camera framing (fl12, fl14, fl17 end) and from-below crane catch (fl17)

This was a source-only builder pass. Nothing was compiled, launched, simulated or rendered. The root compiles, simulates and commits.

**Process deviation:** at the start, three read-only git commands were run: `git branch --show-current`, `git log --oneline -3` and `git status --short`. They changed nothing. No other git command was used.

**Evidence:** root's sim `~/sm2-invincible-cache/simR7d/` (fl12, fl14, fl17 telemetry and logs, read only). The numbers below are offline arithmetic from those rows, not engine measurements.

**Files:**
- `Traversal/WebTravCamera.h/.cpp`
- `Flight/WHRescueDirector.h/.cpp`
- `tools/invincible/make_flight_cases.py` (fl17 entry and constants only)

The case JSONs have not been regenerated: run `make_flight_cases.py`.

**Paths left unchanged:**
- **Legacy hero:** every camera change is gated on `FlightLeashM > 0`, which is the flight hero only.
- **`-WHHeroV2=0`:** the director change needs `bOverheadCarry`.
- **A/B switches:**
  - `-WHCamTune=FlightRelPitch=0,FlightFrameBand=0,LensLiftLeadT=0` gives the r7 camera, except the lift hold.
  - `bCatchUnderOnly=false` gives the r7 reach rules.

## 1. Common cause: a pitch ratchet (fl12 6.03–6.19 s and 6.93 s; fl17 30.7 s to the end)

**Telemetry:**

| Case | Lens | Pitch | Hero |
|---|---|---|---|
| fl12 at 6.027 s | `cam_z` 2.16 → 3.97 in one frame (a lift over a vehicle box) | -42.6 → -76.5 → -80 | `hero_cy` -0.10 to -0.17 |
| fl12, 10 frames later | back to `cam_z` 2.16 in one frame | | |
| fl17 at 30.70 s | `cam_z` 1.93 → 2.17 (a parked-car lift) | `cam_pitch` falls to -23.7 while `cam_orbit_pitch` (composed) stays at -4.7 | `hero_cy` 0.19–0.25 |

In every one of these frames `cam_slew` = 2, so the pitch slew was active.

**Mechanism:**
1. `GuardLens` lifts the lens and re-aims it, keeping the hero's screen offset. Then `LastOutRot` holds the lifted aim.
2. The next `Update` composes from the unlifted chase spot. The absolute pitch slew (`MaxStepPitchDeg` per frame) then holds that view near the lifted pitch.
3. The guard lifts again and adds the lift re-aim (-25° for fl12, about -2.7° for fl17) on top.
4. The pitch ratchets down to the -80 clamp (fl12). For fl17 it stops at the point where the edge-boosted slew balances it.

The cause is not a landing or skim pitch path. In fl12 the hero had been skimming in `fly` at z 0.95 for 1.5 s with a steady -20° pitch before the lift.

**Fixes (`WebTravCamera`):**
- **Hero-relative pitch slew (`FlightRelPitch` 1).**
  - The slew cap now limits how fast the offset changes between the view pitch and the pitch toward his centre.
  - Aim changes that come from lens motion pass straight through. These include a guard lift and a breach-tail rise.
  - Prediction: the ratchet cannot build up. fl17 holds the composed framing (`frame_s` 0.50, cy ≈ 0.5). fl12 aims at him from the lifted lens.
- **Vertical band (`FlightFrameBand` 0.22).**
  - His centre is held within screen height 0.28–0.72 (`|tan off| ≤ 0.44 tan(vfov/2)`).
  - It runs after the slew and breach stages, and again after the guard re-aim. It is skipped on the breach pass line itself.
  - `SlewFlags` 512 marks frames where it acted.
- **Vehicle lift (`GuardLens`).**
  - The lift height is held as a world z and released at `LensPullRelease` (6 m/s). A 1.8 m lift now drops over 0.3 s instead of one frame.
  - The lift is also anticipated: a box that the lens segment enters within `LensLiftLeadT` (0.2 s) of his horizontal travel starts the rise early, at ≤ `LensLiftRiseV` (12 m/s, 0.2 m per frame).
  - A box the lens is already inside is still cleared at once.
- **Breach follow-through:** the leftover un-normalised `GoalR.Pitch += A1 − A0` is replaced (see section 2).

**fl12 expectation:**
- `hero_in_frame` = 1 through 6.0–7.1 s.
- While the lens passes over the vehicle box the pitch is the geometry of the lift: lens about 3 m over him at about 3.3 m, which gives about -42°.
- The pitch returns to about -20° within about 0.3 s after the box (the 6 m/s release).
- Outside the lift frames: -14 to -20°.

## 2. fl14 breach tail (5.75–5.92 s)

**Telemetry:**
- `cam_slew` 387/391 = follow-through (256) + yaw cap + pitch slew.
- The lens rose from 36.2 to 38.6 m toward the composed spot.
- The pitch moved only -6.8 → -12° in that time, then -12 → -35° at 2.2° per frame.
- `hero_cy` went 0.83 → 1.0 → 0.85.

**Cause:** the slew-limited pitch from `Update` fed `ApplyBreachFollow`'s slerp, while the position moved freely.

**Fix:**
- `ApplyBreachFollow` now blends the hero-relative pitch offsets of the composed view and the pass-line view by W.
- The result is aimed from the final capped spot, so his screen height follows the position blend.
- The 5.5° per-frame turn cap is kept. The band clamp runs after it in the tail.

**Expectation:** `hero_cy` stays between about 0.5 and 0.65 through 5.6–6.1 s (the composed value was 0.58–0.63).

## 3. fl17 catch: from below only

**Director (`TickCrane`, overhead carry, `bCatchUnderOnly`):**
- **Basic rule:** the load's bottom face must be at least `CatchUnderClearCm` (0.2 m) above his head top (centre + 0.9 m). Reach is `CraneTouchUnderCm` (6.5 m).
- **Hanging load:** the gap must also be ≤ `CatchUnderGapMaxCm` (0.9 m), and his vz must be ≥ `CatchUnderMinVzCm` (-0.5 m/s). He holds still or rises into it; a descent that passes under it does not catch it.
- **Falling load:** any gap above the clearance counts.
- **Removed:** there is no level catch and no catch from above.
- **Log:** the line now names `level` separately and adds `; hero vz …`. The prefix `from below / beside (` is unchanged.

**Route (`make_flight_cases.py`, fl17):** in simR7d the stop after the brake was at (362.6, -317.0, 151.9), not about (338, -313, 150).

| Key | Value | Effect |
|---|---|---|
| `MOVE_S` | 1.455 (strafe off at 15.845 s) | Stop at about (355.8, -322.8). In the load frame that is (-0.2, +1.5) m, 0.6 m outside the long face. He is at least 0.7 m from the face while level with it (until about 16.30 s). |
| `DROP_S` | 2.4 → 1.77 (drop off at 16.16 s) | Coast of about 2.5 m at the 4/s hover rate. He stops at z about 132.1, head about 1.5 m under the bottom face, vz ≥ -0.5 m/s by about 16.9 s. |
| `RISE_T` / `RISE_S` | 17.0 / 0.15 (climb tap) | Total rise = 10 m/s × 0.15 s = 1.5 m. Predicted catch about 17.25 s: D about 3.0 m, gap 0.9 m, rising about 3 m/s. |
| `DESC_T` | 17.6 → 17.8 | Leaves room for the climb coast. |

**Model** (from simR7d rows): drop follows the float rate (16/s to -10 m/s); release and climb follow `HoverRate` 4/s.

**Margins:**
- A stop up to 0.6 m deeper still catches during the rise.
- A stop with a gap ≤ 0.9 m catches at the stop.
- No catch would happen only if his head stopped within 0.2 m of the bottom face or above it.
- If no catch is logged, the case fails (`rescue_saved_min`), but there is no interpenetration.

## 4. fl17 end framing (30.7 s to the end)

The cause and fix are section 1 (fl17 ratchet: composed -4.7° against -23.7° output).

**Expectation:** `hero_cy` 0.45–0.55 with a floating hero at z 1.40, and pitch close to `cam_orbit_pitch` (about -5°). The lens stays lifted over the parked-car box (z about 2.17), aimed at him.

## Checks for the root (sim)
- **fl12:**
  - `hero_in_frame` = 1 for 6.0–7.2 s;
  - `cam_pitch` -14 to -25° outside lift frames, and back within 0.3 s after one;
  - no `cam_z` step over 0.25 m per frame from the lift;
  - `hero_lands` = 1 and `floating_end` unchanged.
- **fl14:** `hero_cy` 0.4–0.7 for 5.5–6.2 s, with no hidden frames in the tail.
- **fl17:**
  - log `load caught hanging … from below / beside (…; load bottom 0.20–0.90 m over his head top; hero vz ≥ -0.5 m/s)` at about 17.1–17.4 s;
  - no row with the load bottom under his head top before the catch;
  - `hero_cy` 0.4–0.65 from 30.7 s to the end, with no hidden rows;
  - still `rescue_saved_min`, `breaches=1` and `floating_end`.
- **All flight cases:** look for `cam_slew` bit 512 (band) frames. fl18 `camera_calm` should be unchanged.

## Open points (not verifiable without a run)
- **fl17 camera yaw:** the route change (strafe off earlier) may change the yaw before the `TURN_DEG` -87 turn. simR7d already ended at +136°, not -180°. Not changed here.
- **fl17 set-down:** simR7d rejected all 7 candidates ("13 near" vehicles), and the fallback put the load 1.3 m from him. Not in this piece.
- **Lift pitch:** the lift over a 3.5 m box behind a street-skimming hero is still about -42° for the frames the lens is over it. A shallower option would also move the lens back while lifted; it is not implemented.
- **Band edge:** the band clamp can override the 5.5° breach turn cap and the slew caps in the frames where it binds. Keeping him in frame takes precedence, as with the r6 22° yaw rule.

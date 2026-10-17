# Round 7 notes: piece "breach camera / lens guard" (builder A)

These are source edits only. Nothing was compiled, launched or rendered in Unreal. No build was run.

**Process deviation:** at the start, one read-only `git branch --show-current` was run. It printed `invincible` and changed nothing. No other git command was used.

The numbers below come from an offline Python model of the new camera logic: `/tmp/r7cam/sim.py`. The model uses straight-line passes through a box building and assumes backface-culled walls. These are model values, not engine measurements.

`-WHFlight=0` is unchanged:
- every change in the character is gated on `bFlightMode && Flight`;
- the camera follow-through also needs `FlightLeashM > 0`;
- the speed changes in `WHFlightComponent` run only in flight.

## Files changed

- `Traversal/WebTravCamera.h/.cpp`
- `Flight/WHFlightComponent.h/.cpp`
- `Traversal/WebTravCharacter.cpp`: only the breach-hold camera block, around line 1136. `FlightFrame` is unchanged.

## Critic #1: breach jump cut

### What was removed

The r5/r6 hold has been removed:
- no frozen view while he is in the solid;
- no `ChooseCutYaw`;
- no `Cam.Reset` at the exit.

`Cam.Update` now runs on every breach frame.

### Follow-through camera

- **Entry state.** `FWebTravCamera::SetBreachPass` is called every frame before `Update`. It switches to phase 1 while `IsBreaching()` is true.
- **One-frame passes.** A pass that starts and ends within one frame is detected from the `breachOut` event and still gets the follow-through.
- **Pass framing.** In phase 1 the output is placed 3.0 m behind him on his pass line and 0.7 m up, looking 3 m past him. The lens may be inside the block during this phase.
- **Exit state.** At the exit (phase 2):
  - `ReseedChase` re-seeds the chase composition behind him on the pass heading. It does not move the output and keeps the shake.
  - The output holds the pass line for 0.12 s, then blends to the composed flight view by 0.4 s.
- **Per-frame caps.** From entry to the end of the tail the output moves ≤ 2.9 m and turns ≤ 5.5° per frame. The 5.5° is measured on the whole quaternion, so roll is included. Both caps are absolute per frame.
  - The step cap ramps to the normal flight cap over 0.12–0.4 s of the tail.
- **Watchdog.** The watchdog boost is zeroed during these phases, so there is no whip at the hand-back.
- **Darkening.** `InsideDarkK` rises while the lens is inside a traversal solid. The pawn applies a vignette (0.4 → 0.95) and a tint (×0.65) through overrides, which are released at 0.
- **Telemetry.** `SlewFlags` bit 256 marks follow-through frames. `BreachCamPhase` and `BreachCamW` are public but not yet in the telemetry CSV.

### Pass speed (flight component)

- **Speed cap.** The body passes the solid at no more than `BreachPassStepM` = 2.6 m per rendered frame (156 m/s at 60 fps). The ceiling is `BreachPassMaxV` = 240 m/s and the floor is `BreachSpeed`.
- **Pass time.** `BreachMaxTime` went from 0.06 to 0.14 s. A 20 m block takes about 8 frames. World time dilation is unchanged at 1.
- **Exit speed.** The exit leaves at ≤ the pass speed and holds that cap for `BreachExitHoldT` = 0.2 s. After that the super/fly acceleration resumes.

### Model results

Window = breachIn to exit + 0.2 s, at 60 fps.

| entry speed / depth | frames | max step | max turn | hero visible |
|---|---|---|---|---|
| 55 m/s / 20 m | 21 | 2.45 m | 5.5° | 95 % |
| 160 m/s / 20 m | 20 | 2.76 m | 5.5° | 95 % |
| 300 m/s / 20 m | 20 | 2.90 m | 5.5° | 90 % |
| 300 m/s / 26 m | 23 | 2.90 m | 5.5° | 91 % |
| 160 m/s / 78 m | 42 | 2.85 m | 5.5° | 98 % |
| 300 m/s / 2 m | 13 | 2.90 m | 5.5° | 85 % |

In the late tail (0.2–0.4 s after the exit) of a super-speed exit, the step reaches 3.29 m. This is because the hero himself re-accelerates past 3 m per frame.

The hidden frames in the model are the 1–3 entry frames before the lens crosses the facade.

## Critic #5: lens in solids or in the hero

`FWebTravCamera::GuardLens` runs after `Update`, in flight mode only, on the final lens.

- **Body distance.** The lens is never nearer than 1.4 m to the hero's padded bone box. If it is, it is pushed straight out and re-aimed.
- **Solids.** This check runs outside the pass and the first 0.12 s of the tail. A 0.22 m lens sphere is tested against:
  - traversal solids;
  - render collision on the visibility channel, ignoring the hero and the breach director;
  - traffic vehicle boxes, gathered when the lens is under 8 m.

  When the sphere overlaps one of them, the lens is pulled in toward the chest to the first clear point. If that point is nearer than 1.4 m to his body, the lens rises over him instead. The pull releases at 6 m/s.
- **Vehicle boxes.** These come from `AWHLifeTraffic::GetPoints` and `GetMovingInfo`:
  - moving cars use their lane axis;
  - parked cars use the union of both axes, because parked yaw is not exposed;
  - sizes are copied from the `GTypes` / `GTypeH` table in `WHLifeTraffic.cpp`.
- **Slew continuity.** `LastOutPos` follows the guarded lens.

## For root to check in capture

- Whether building walls are back-face culled seen from inside. If they are two-sided, the hero is hidden for the whole pass.
- Whether the longer pass (about 0.14 s, sub `breach`) suits the v2 anim pose.
- Tunables:
  - camera: `-WHCamTune=` with `BreachFollowDist`, `BreachStepM`, `BreachTurnDeg`, `BreachTailHoldT`, `BreachTailT`, `LensBodyMinM`, `LensSolidR`, `LensPullRelease`;
  - flight: `-WHFlightTune=` with `BreachPassStepM`, `BreachMaxTime`, `BreachExitHoldT`.

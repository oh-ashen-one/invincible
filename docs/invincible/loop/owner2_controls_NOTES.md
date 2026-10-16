# Owner request 2026-10-16: on-screen controls panel (top-left)

Owner request (verbatim): "put the controls on screen on the top left, small but in a way that I can see it."

Edited files (only these two): `unreal/WebHomage/Source/WebHomage/Flight/WHFlightHUD.cpp`, `WHFlightHUD.h`.
Status: source edited; not compiled and not run (no engine / build / GPU / git by this builder; root compiles and commits).

## What changed

- New `AWHFlightHUD::DrawControls()`, called from `DrawHUD()` before the rescue panel. Always on while flight mode is on and the game is unpaused.
  - Backing box `(0,0,0,0.46)` with a 1 px (scaled) border `(1,1,1,0.30)`; white labels, key names yellow `(1.0,0.86,0.28)`; text shadow comes from the existing `Text()` helper.
  - Position: top-left, 16 px margin x `ClipY/1080`.
  - Text size: the Small font is measured once per frame (`GetTextSize("Ag|")` at scale 8) and the scale is solved for a line height of 16.5 px x `ClipY/1080`
    (about 14 px glyphs at 1080p, about 22 px line / 18.7 px glyphs at 3440x1440). It does not depend on the engine font's native point size.
  - Box width is measured from the widest row; height = 11 rows x (line x 1.06) + padding.
- The rescue panel (lives saved / lost / collateral / emergency rows) moved from the top-left to the top-right (`X = ClipX - Wd - 28*UiScale`); its size and content are unchanged.
- `H` toggles the panel (edge-detected on `PlayerOwner->IsInputKeyDown(EKeys::H)` inside `DrawHUD`). When hidden, a single dim line `H  show controls` stays at the top-left.
  `EKeys::H` is not referenced anywhere else under `Source/WebHomage` and not in `Config/DefaultInput.ini`.
- Header comment updated; new members `bShowControls` (public) and `bPrevHKey` (private). `InputCoreTypes.h` added to the .cpp (the `InputCore` module is already in `WebHomage.Build.cs`).
- `-WHNoHUD` still suppresses everything, including this panel.

## Panel rows and the binding each was checked against

| Row shown | Verified in code |
| --- | --- |
| `WASD` move / strafe / turn | `WebTravCharacter.cpp` `MapMove(W/A/S/D + arrows)`, `PollLiveInput` `I.Move`; `WHFlightComponent.cpp` `StepAirSub` (hover strafes on the camera plane; fly line: stick X turns the nose via `StickTurnRate` in `StepFlight`, stick back slows) |
| `Mouse` look / steer flight | `PollLiveInput` `I.Look`; `StepFlight`: look moves `AimYaw/AimPitch` only while `I.bSwing` (RMB) or a super state is active, otherwise it orbits the camera |
| `Space` take off / climb | IMC `JumpAction` = Space; ground: `I.bJumpPressed -> Takeoff`; air: `Climb = bJump - bDrop` |
| `Space x2` superhero landing (in air) | `StepAirSub`: second airborne `bJumpPressed` within `DoubleTapTime` (0.3 s) -> `StartDive` (the takeoff press never opens the window) |
| `Hold RMB` fly | IMC `SwingAction` = RightMouseButton; `bFly = I.bSwing` (RMB also takes off from the ground) |
| `Shift` sonic boom boost (hold = super speed) | IMC `SprintAction` = Left/Right Shift; `bSprintPressed` -> `ESuper::Charge` -> `SuperLaunch`; `ESuper::Run` while Shift stays held; airborne only (ground input masks it) |
| `C / Ctrl` descend | IMC `DropAction` = C, LeftControl (RightControl is not mapped); `Climb -1`; `bDrop` in hover lands |
| `E` brake / rescue (hold) / set down | IMC `ZipAction` = E (also MMB); air press -> `NF_brake`; `FW->bInteractHeld = I.bZip` drives the fire / bus hold; `bInteractPressed` drops a carried load (`WHRescueDirector.cpp`) |
| `Q` dash | IMC `QuickAction` = Q; `bQuickPressed` -> dash, airborne only |
| `F` slam (in air) | IMC `TrickAction` = F; `bTrickPressed` -> `NF_slam`, airborne only |
| `Esc / P` menu / release mouse | `WebHomagePlayerController::PlayerTick`: Esc / P / pad Options open the settings menu (which frees the mouse and pauses); with `bNeverCapture` Esc only releases the mouse |
| `H` hide / show controls | new, this change |

Differences from the request text: the Esc row also lists `P` (same handler); the `Q dash` and `F slam (in air)` entries share one line as requested; `Space x2` carries "(in air)" in its label instead of its key cell.

## Known gaps / notes for the next reader

- Not measured on screen: pixel size, box size and overlap with the rescue panel at 1920x1080 and 3440x1440 are computed from the formulas above, not from a capture.
- Gamepad bindings are not listed (keyboard / mouse only, as requested).
- `T` (suit cycle, `WHHeroSuit.cpp`) is a live key but is not in the panel.
- The bindings above are read from the files as they were when this was written; another builder was editing the flight / anim code in parallel. Re-check `StepAirSub` and the IMC block in `WebTravCharacter.cpp` if either changes.
- Re-check list if keys move: `WebTravCharacter.cpp` (IMC block near `MapKey`, `PollLiveInput`), `WHFlightComponent.cpp` (`StepAirSub`, `StepFlight`, `StartDive`), `WebHomagePlayerController.cpp` (`PlayerTick`).

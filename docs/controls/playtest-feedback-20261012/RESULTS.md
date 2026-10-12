# Owner playtest feedback — 2026-10-12

Runtime source: `e9a8120c` on `codex/manual-camera-20261012`, continuing unmerged PR4. The earlier trick-camera and high-sensitivity fixes remain included. The owner explicitly requires approval before merging.

## Delivered scope

- Gameplay debug/map/renderer warning text is suppressed through Unreal's screen-message display gate. Ray tracing, geometry and other rendering features remain enabled. World signage remains part of the scene.
- Settings retain readable text, wrapping and scrolling with fixed Resume/Reset/Quit actions. The inactive VSync control is hidden under the forced playable/fidelity profiles; settings explain it is off. Ordinary unprofiled runs retain their functioning toggle. Gameplay instructions are inside settings only.
- Q / L1 adds an immediate impulse along the visible camera direction, with vertical aim bounded to 45 degrees. It does not choose a nearby anchor, redirect toward a roof, or replace an active air trick. Existing perpendicular/falling momentum is retained, within the speed budget. E / Triangle remains the separate targeted perch zip and now has its nearest-valid-perch fallback while swinging.
- White web rendering requires actual Swing mode and an active, unreleased strand. Every legacy segment is hidden outside that state, including zip, boost, release, idle and perch; tiny visible proxy segments were removed.
- Ground rest and stationary landing settle use the existing authored spider crouch. Perch rest remains crouched. Movement clips and locomotion blend weights are retained.
- Enabled camera shake now has smooth attack/decay, visible catch/boost feedback and light speed feedback. Disabling it immediately clears pending shake and jolt state.
- The supplied `Curious Groove.mp3` is preserved in `assets/audio`. A 147.07-second stereo loop removes the quiet tail and uses a 0.4-second circular crossfade. A game-instance-owned 2D player runs at 25% volume, continues through pause/settings, retains playback across world transitions and stops on game-instance shutdown. Native mixer verification confirmed playback past the loop boundary while paused.

## Evidence

Final native UE5.8 Mac build passed. `RUN.json` identifies the module and imported SoundWave hashes. Independent source reviews found no blocking issue in traversal/animation/camera, UI, music lifecycle or import/cook integration.

`metrics.json` is derived from the compressed native telemetry in `evidence/`. Focused rendered cases cover rest/start/stop/jump/landing, boost during an active flip, swing release followed by zip/perch, shake on/off, settings, and live audio with pause/resume. These are behavior checks under the shared GPU coordinator, with another task's reserved slot present; no exclusive-performance or 60 FPS claim is made.

- No rendered web telemetry outside Swing in any captured case. Swing strands remain visible during Swing.
- Mid-flip Q increased speed from 24.290 to 36.162 m/s while `frontSingle` continued.
- The zip case reached and held Perch for 356 frames, including 321 `perchIdle` frames; no white line remained.
- Ground-rest native screenshots show the crouch. Stable rest uses `perchIdle`; short movement/landing blends retain their normal transitions.
- Matched shake-on/off routes have identical character positions. Maximum measured camera differences: pitch 0.45 degrees, yaw 0.25 degrees, roll 0.59 degrees. Shake behavior remains a subjective owner playtest gate.
- The audio test started once at 145 seconds into the 147.07-second loop, paused the game, logged cumulative mixer progress 1.00870 with `playing=1`, then resumed. See `music-runtime-proof.txt`. Normal play starts at the beginning; diagnostic seek flags are not in the owner launcher.
- The loop-preparation boundary sample step was 0.0000762 full scale; peak amplitude stayed below clipping. See `music-processing.json`.

The extracted production math check passed 225 camera-direction cases and 70,875 impulse cases. The previous manual-camera regression still passes 2,520 orbit samples and 1,080 radius steps. The matched shake-off capture uses a valid GameUserSettings Version=5; an initial incomplete test ini was discarded by Unreal and was corrected before the final comparison. The audio check omits benchmark mode, which disables actual sound playback.

The sound import created and saved the expected looping PCM SoundWave. Its headless commandlet returned 1 due to existing GameFeatureData asset-manager initialization errors, despite the import success sentinel. Subsequent native game playback loaded this saved asset and verified its loop; the unrelated asset-manager configuration was not changed.

## Handoff and limits

Local owner build: `/Users/midir/SpiderMan-Playtest-Feedback-20261012/Play.command`. It preserves saved player settings. Its independent Content includes the imported music asset; source MP3 and preparation/import scripts reproduce that asset under the existing generated-content policy. `STAGE.json` and `SHA256SUMS` identify the final relocated build.

Physical PS5-controller feel, subjective shake/music balance and owner acceptance remain for the playtest. The persistent music lifecycle across complete map changes was source-reviewed; the native audio test exercised the current map, pause/resume and loop boundary. Previously documented air-to-wall camera corrections remain outside this pass. No next polish loop or merge is authorized.

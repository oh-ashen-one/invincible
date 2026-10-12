# Round 13 bounded closeout

This checkpoint completes the interrupted capture/review pass. It does not authorize round14 or establish reference-quality acceptance. Runtime source is `21e43450c772292c6d9bc51b3ce1c3397ec1ae77`; all six final clips and the owner copy use its fingerprinted build. The owner playtest is the next decision point.

## Changes

- Open held poses stop advancing their clip phase after the authored settled key. Pencil leg timing freezes before its leg scale; Straddle reaches the straight split before freezing. Existing trick programs and timing remain.
- Trick-camera visibility checks horizontal and vertical frustum margins separately. The ordinary ground crane waits for trick-view blend-out.
- Kimi's preserved web material/settings are retained. The material was read back, recompiled and saved through Epic's native MCP on the verified task-owned editor.
- Capture caches are isolated and deleted only after verified encoding. Renderer detection no longer mistakes UnrealEditorServices for the game. A separate guarded owner playtest folder is staged with a hash manifest.

## Evidence

Three C++ builds succeeded; the final one took 8.93 seconds. Offline asset validation found no missing assets; both capture-cache safety tests passed. Six final MP4s have matching ordered telemetry and case counts: day swing, nine web-press cases, flip chain, seven primary flip cases, release/float and night swing. These are 1920x1080 offline fixed-60-Hz captures, not real-time FPS measurements. The exact hashes are in CAPTURE_MANIFEST.json and BUILD.json.

The relocated owner copy rendered two inspected screenshots on Manhattan_Island and exited cleanly. All 51,168 original manifest entries match before and after that run. OWNER_PLAYTEST.json records the limited smoke-test scope. Input feel, controller operation, long-session stability and performance acceptance remain untested.

## Known limits before independent review

Seven primary open holds in the probe last .4067-.4900 seconds at <=147.1 degrees/second, excluding late Kickout/Reach. The secondary wallFront tail is truncated, so this is not an eight-program pass. Strict projected F3 peaks still fail in several primary programs (roughly 811-871 degrees/second) and the truncated tail; the unchanged reports retain them. The focused landing-camera probe improved four zero-mask frames to three, not zero. Hero-size extremes and web/catch quality failures remain in the per-clip reports. No thresholds were weakened.

Runtime logs retain known nonfatal editor-Python toolset, non-Mac SDK and distance-field matrix-precision diagnostics. The task did not expand into engine/plugin remediation.

## Review and stop

One fresh GPT-6.1 Sol / extra-high critic completed a roughly 17-minute review of nine normalized blind pairs and all six native clips against unchanged targets. It received no source, telemetry, build notes or identity key. Verdict: **APPROACHES TARGET**; scores in axis order are **6 / 8 / 6 / 7 / 6 / 5** (deployment, web readability, swing body, flips, air/catches, camera). Engineering used a separate GPT-6.1 Sol / extra-high agent; tooling/scouting used GPT-6 Sol / high.

The critic found real held gymnast shapes and readable day/night strands, but identified roof-catch containment, abrupt firing-arm motion and repetitive catch endings. The orchestrator confirmed the camera loss and arm snap from independent native-frame extraction; see CLAIM_VERIFICATION.md. The key identifies the current build as the preferred side for flip containment and the slight press-sequence preference, with swing/night progress ties. Reference footage and normalized reference-containing videos remain private and are not published.

The report finds no visible crash, stuck state or progression blocker preventing a bounded owner playtest. Camera quality is still below target, and manual gameplay acceptance remains pending. This pass stops here: no automatic round14. The original checkout and named owner playtest folder remain; task-only temporary worktrees and caches are removed after the final push. Candidate MP4s, reports and selected verification images are retained locally in the owner folder and in GitHub. Detailed critic measurements preserve frame coordinates/timestamps; disposable extraction sheets are not required to reproduce them from the native clips.

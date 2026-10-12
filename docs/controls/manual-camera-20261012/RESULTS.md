# Camera control repair — 2026-10-12

This finite repair addresses the owner's two requests: pressing Square/F must not select a side-view camera, and fast mouse/controller look must not oscillate or leave the view behind the orbit. It does not start another general game-polish pass.

Runtime source: `bb945b1ee60c5c8044c562e7a702018c83e451b4` (base main `9eb3a5a7`). UE 5.8 native Mac build succeeded. Module SHA-256: `b8e257dca01fd996e46fdf53963d26124f09c52952100af3388453295c5931ef`.

## Changes

- Trick input leaves the ordinary chase view active, including normal player look and recenter behavior. The previous held three-quarter trick view is disabled; actual flip animation, body bounds and containment tail remain active. The owner's current request supersedes the older held-angle trick-camera specification.
- Manual orbit transports the camera spring's position and relative velocity together. Its output position and turn budgets include accepted player input, so maximum sensitivity does not move the lens faster than the view can follow. Ground-rejected turns receive no extra allowance; automatic motion retains its existing limits.
- Controller input uses the same bounded frame time as traversal and camera simulation.
- The framing radius stays above the emergency minimum-distance threshold. Previously, ordinary framing could cross that threshold and trigger an upward obstruction fallback even in empty air. Genuine collision sweeps and their fallback still run afterward.

## Focused verification

The before captures use the previous published runtime `2db142143bc60709a1db726a445d17aee2a57aca`, module `9fb64bb667e7be2bcf35114fc2231ed0207ce684c78a5be049b61ef493ede502`. Final captures use the source/module above. Captures run sequentially through the shared GPU guard at fixed 60 Hz. They are behavior checks, not real-time FPS benchmarks.

| Native replay | Before | Final |
| --- | --- | --- |
| Controller-equivalent maximum yaw, stops and reversal | 38.061° peak horizontal aim/bearing discrepancy; 215 yaw-limited frames; 52 body-frame misses | 0.016° discrepancy; zero yaw-limited frames; zero body-frame misses |
| Mouse-axis events at sensitivity 3, 120 injected units/frame | 35.684° discrepancy; 119 yaw-limited frames | 0.019° discrepancy; zero yaw-limited frames; no reverse orbit steps or body-frame misses during sustained horizontal input |
| Mouse-axis events at sensitivity 3, 1715 injected units/frame | No matching baseline capture | 0.019° discrepancy; zero yaw-limited frames; no reverse orbit steps during sustained horizontal input |
| Forward trick | At t=1s camera yaw −46.00° after starting near −93°; trick-view blend reaches 1 | At t=1s camera yaw −94.89°; trick-view blend stays 0; same 145 active trick frames; body fully framed throughout |

The existing input-axis configuration scales injected mouse events by 0.07: 120 injected units become 8.4 input units; 1715 reaches the existing 120-unit clamp. The extreme case requests about 51.6° per frame. It deliberately verifies large deltas; it is not a recommendation for a comfortable sensitivity.

`tools/controls/manual_camera_math.py` compiles extracted production functions and statements. It passes 2,520 orbit samples at 30/60/120 Hz plus 1,080 minimum-radius spring steps, including immediate stops/reversals, angle wrapping, moving pivots, ground rejection and pitch clamps. Disposable negative controls for missing orbit transport and the old yaw budget fail as expected. Native 30/120 Hz diagnostics were performed on the intermediate `d5e0cbd0` build; final native results in this folder are 60 Hz. The timestep hitch repair has source/math verification, not an injected native stall measurement.

A GPT-6.1 Sol/xhigh independent source review found no blocking correctness issue in the final scoped change, including the minimum-radius fix. This is separate from runtime and physical-controller acceptance.

## Limits and retained behavior

The near-wall replay covers the existing air-to-wall camera reseat. A matching old-build capture already shows a large transition turn and brief body-frame misses. This patch retains that collision/state-transition behavior and is not a claim that every existing camera transition is repaired. See the exact before/final figures in `metrics.json`.

Both mouse tests intentionally look upward after their horizontal segment. The existing pitch limit/framing can crop part of the body in those upward-look samples; horizontal tracking remains aligned. `body_not_fully_in_frame` means the full-body containment metric failed, not that the entire character disappeared. Native screenshots were inspected. Physical PS5-controller feel and owner acceptance remain for the owner playtest.

## Reproduction and playable copy

With the installed UE 5.8 engine and generated content available:

```sh
python3 tools/controls/manual_camera_math.py
python3 docs/controls/manual-camera-20261012/capture.py --out /absolute/task-owned/cache --case high-look --case mouse-look --case mouse-extreme --case trick --case wall-look
python3 docs/controls/manual-camera-20261012/analyze.py docs/controls/manual-camera-20261012/evidence/*.csv.gz
```

The local playable copy is `/Users/midir/SpiderMan-CameraFixes-OwnerPlaytest-20261012/Play.command`. It retains the owner's saved sensitivity, FOV, suit and other settings. The previous owner copy and original dirty Kimi checkout remain untouched. `STAGE.json` and `SHA256SUMS` identify the tested runtime; this is an installed-engine development build, not a portable packaged release.

Source is pushed on `codex/manual-camera-20261012`. This repair request authorizes the task branch; merging this new change into main requires owner approval. Stop after the focused handoff; no continuing refinement loop.

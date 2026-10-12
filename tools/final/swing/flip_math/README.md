# Standalone flip math verification

Run `python3 tools/final/swing/flip_math/run.py` from this checkout. Requires a C++17 compiler (`clang++` by default; override with `--compiler` or `CXX`). Use `--source-root PATH` to check an integration checkout.

The runner extracts the pure section of the **current** `WebTravFlips.cpp`, copies its current header, and extracts the actual `PostAnimTick` root-composition statement from `WebTravCharacter.cpp`. It compiles those with minimal type adapters in a temporary directory, runs assertions, and removes the executable. There is no committed generated program snapshot or binary.

The check samples 32 deterministic tempo/jitter variants of all 13 programs at 240 Hz. It verifies exact duration/catch-time scaling and final angles; peak pitch rate; mid-trick open holds excluding terminal catches; multi-rotation mean rate; three sampled terminal authored families; evaluated-axis compensation under synthetic forward/lateral lean and both twist sides; traversal-centre preservation; and nonzero decaying air sway applied exactly once in the original, noncommuting multiplication order.

The random fraction adapter follows the installed Unreal 5.8 `Math/RandomStream.h` implementation, including its high-bit `Seed >> 9` fraction. Other adapters supply only the pure code's required containers and arithmetic; they do not emulate animation evaluation or Unreal's scheduler.

These checks establish mathematical properties, not visible pose variety, catch/entry continuity, camera framing or rendered rates. Those require the task-owned rendered captures and same-frame `fw_body_axis_*` telemetry. `wallFront` is a short terminal-landing program and is excluded from the mid-chain hold assertion.

`entry_forecast.py` uses the paired c7 final-axis fixture from the 0.15-second and 0.25-second rendered entry probes. It reproduces both recorded projected peaks before forecasting the current header's `PoseEntryS`. The forecast rotates along the great circle between each pair of measured axes, using the known change in correction weight. Residual sway makes the exact path a small circle, so this estimate selects an entry candidate; it cannot replace the rendered repeat. Both projected and true 3D forecast rates must stay below 800 degrees/s. The fixture JSON records input capture paths and hashes.

The quaternion suite also checks cached author-local prediction for held poses and one frame of a 60-degree/s BodyAlign slew. This bounds that specific prediction contribution; independently changing authored clip keys or other procedural layers still require the rendered catch regression. The authoritative final pose continues to use the current frame's measured local axis.

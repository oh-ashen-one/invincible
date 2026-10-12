# Manual camera regression math

Run `python3 tools/controls/manual_camera_math.py` from the repository root. It requires a C++17 compiler (`clang++` by default); `--compiler` and `--source-root` can select another compiler or checkout.

The helper extracts the current production `ApplyLook`, angle wrapping, spring functions, manual orbit transport, orbit travel allowance, chase radial projection, accepted-ground-yaw expression, and output slew-budget expressions. It compiles those snippets with minimal arithmetic adapters in a temporary directory and removes the executable when finished. It does not compile the Unreal project or launch an engine.

The 2,520 sampled frames cover 30/60/120 Hz, the 3x full-stick yaw rate (6.21 rad/s), extreme mouse deltas (0.45 and 0.9 rad/frame), immediate stops/reversals, and repeated angle wrapping. Assertions require monotonic intended turning, immediate stop without spring drift, orbit/aim agreement, sufficient manual movement allowance, and restoration of the original procedural budget on release. Separate checks cover moving hero pivots, preserving world translation velocity while rotating only relative spring velocity, rejected ground turns, and the pitch-input clamp. Another 1,080 spring steps exercise minimum framing radii to ensure they cannot activate the emergency vertical crane in empty air.

Two negative controls were checked in disposable copies: replacing orbit transport with a no-op fails orbit tracking, and restoring the old yaw budget fails aim tracking. The helper also checks that trick input does not select the legacy side view or remove ordinary float framing, the actual flip body tail is retained, and controller input uses the bounded camera time step.

This is mathematical evidence. Rendering, collision geometry, actual controller/mouse events, body containment during a trick, camera capture behavior, and owner playtest acceptance still require the task-owned native playback and its telemetry.

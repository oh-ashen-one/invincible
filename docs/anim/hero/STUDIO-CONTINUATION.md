# Studio continuation: hero animations

> A homage game. This is not an official Marvel game. See [DISCLAIMER.md](../../../DISCLAIMER.md).

The owner cancelled the crowd/animal goal. Active objective: high-quality playable-hero jumping, flips and airborne spins, BOTH an explicit trick button and automatic context-sensitive traversal tricks, plus a side-entry flip/weighted landing/showcase idle in skin selection. Preserve existing bystander/animal behavior. Continue autonomously on 3d-animations-astra; no main merge or paid generation.

## Resume here
- Authoritative task-owned checkout: /Users/midir/sm2-astra-anim (direct writable GitHub deploy-key remote).
- Existing task-owned Blender PID 19303, port 19891, scene owner sm2-astra-anim, file art/anim/hero.blend. Revalidate live ownership; reuse it, do not launch a duplicate.
- Actual stdio MCP bridge/client: tools/heroanim/mcp_client.py, launched with `uv run --with blender-mcp==1.9.1 python ...`. Each invocation starts its own short-lived MCP server on Studio and connects to the existing Blender. Catalog has 28 tools. Matching bundled addon protocol 5, Blender 5.2.0 LTS. No shared addon/config was modified.
- Script call: `uv run --with blender-mcp==1.9.1 python tools/heroanim/mcp_client.py execute_blender_code --script tools/heroanim/FILE.py --args '{"user_prompt":"trick button and auto"}'`.
- Screenshot: get_viewport_screenshot with --output to a PNG. Inspect after visible edits.
- Own Vite on 5193 (.scratch/vite.pid); own desktop Chrome debug port 9334, profile .scratch/chrome-profile. Port 5192 belongs to somebody else. Verify actual processes, desktop visibility and browser readiness.
- Model verified from originating thread context: gpt-6-astra, high effort.

## Completed and limits
Imported hero GLB: 58 bones, 79 Actions, original textures. Visually inspected import-viewport.png; recognizable correct hero mesh/pose.
bake_hero.py converts Blender posed bone matrices back to original glTF node coordinate frames, preserving the authoritative mesh/bind skeleton. Original import used factory 24 FPS; retained 24 FPS to preserve action durations. New baking samples at 60 FPS.
Numerical check at EVERY original glTF key timestamp over all 79 clips/58 bones passes: max world-matrix component error 4.4226646423339844e-05, tolerance 0.0002.
IMPORTANT: this is not a complete animation round-trip gate. An earlier seven off-grid samples per clip check failed (max 0.08796346187591553, worst landHard/deltoid.L), likely Blender quaternion component interpolation versus glTF slerp; investigate and preserve this distinction. Do not claim between-key or in-engine equivalence. Untouched original GLB remains authoritative and unmodified. Baseline baked test clips idle/releaseFlip/releaseCorkscrew are in ignored .scratch/roundtrip-clips.json and reproducible.
No new hero motion has been authored. No runtime files changed. No visual quality/performance gate passed.

## Next work
1. Make MCP client exit nonzero for semantic tool errors: execute_blender_code can return text beginning Error while isError=false.
2. Validate baked tracks with real Three GLTFLoader/ClipSampler and confirm sanitizeNodeName mapping (dots in source names are removed by PropertyBinding). Address interpolation accuracy, without weakening proof or replacing untouched source animations.
3. Capture baseline desktop runtime and performance at 1920x1080; record quality settings.
4. Author readable high-quality keyed hero actions in Blender, export additive clip library, integrate manual/automatic tricks and suit entrance. Existing automatic tricks are procedural (PTRICK in animator.js); preserve existing double-Space shortcut.
5. Follow docs/anim/hero/PLAN.md for complete acceptance, sources, motion QA on original and all five custom skins, regression, real desktop performance, and pushed artifacts.

Read the root handoff's superseded banner, not its obsolete crowd instructions as the active task. Read applicable AGENTS.md and Blender skill. Owner asked to move continuation to Studio so laptop can shut down; do not depend on a laptop SSH orchestrator for continued agent work.

# Integration bugs found by the Manhattan map (C round 01) — include in each owner's next brief

- **P1 city:** build_city.py crashes headless without `Module Load StaticMeshEditor`; street kit missing from default build steps (two passes needed); hard-coded scratch paths + "5202/" port string; detailed city block only 768 m long. (Sent to city round 07.)
- **P2 characters:** build_characters.py tied to P2's worktree + scratch (C built from a copy of P2's prepared files); line-mode walkers only walk along world X; people read poorly in the map (small, shaded, occluded by props).
- **P3 traversal:** hero mesh/clip paths hard-coded in C++ (swap to /Game/Characters needs a P3 change; skeletons share the 58 bones); turning off the avenue pins the hero against a facade; `releasePhase` 0.85 leaves him hanging still at 49 m.
- **P4 look:** helper scripts default to P4's scratch; traversal boxes must be rebuilt after every city build. (Sent to look.)
- **Perf (first clean number):** 3840×2160 output, TSR 67 % (2573×1447): avg 51.99 ms (19.2 fps), p95 59.0 ms, 0 hitches; GPU 42.2 ms, render thread 50.6 ms. Piece F (Opus) profiling.

## From P5 combat round 01 (for P3 traversal's next round)
- Add a control-override hook (combat currently moves the hero by teleporting every frame); make `ToAir` and `LaunchJump` public; let combat consume E/Q/C/F while in combat mode (today both systems react); writable camera yaw + shake/impact API; keep the anim proxy virtual. Details: docs/night1/combat/HANDOFF.md.

# Invincible flight — round 3 builder brief (2026-10-15, owner-authorized continuation)

Project: UE 5.8 C++ fan game (unofficial "Invincible" homage — never use trademarked logos or ripped assets). Checkout:
`/Users/midir/spider-man-2-invincible` (branch `invincible`). Module source: `unreal/WebHomage/Source/WebHomage/`.
Read first: `docs/invincible/RESULTS.md`, `docs/invincible/captures/r2/CRITIC.md` (the blind critic's per-case defects + top-8 with
acceptance tests), `docs/invincible/captures/PLAN.md` (the 17-case suite).

## Rules for every builder (hard)

- Route Unreal work through the shared skills: run `~/.config/devin/brain/bin/brain resolve unreal-engine` and read the returned
  `resolved_path/SKILL.md`; read `epic-unreal-mcp` the same way for API conventions. No live editor exists for you: source edits only.
- **Do not launch Unreal (editor, -game, commandlets), Blender, or any GPU renderer. Do not run build_editor.sh / UBT. Do not run git
  (no add/commit/stash/checkout/reset).** The root session compiles, simulates, renders and commits. Several builders edit this checkout
  at the same time: touch ONLY the files you own (below). If you need a change in a file you do not own, write it as a request in your
  notes file instead.
- Write compile-clean UE 5.8 C++ (you cannot compile: check includes, signatures, const-correctness, unity-build name collisions, and
  shadowed locals by reading the code). Keep the existing comment style: each change carries a short comment naming the defect it fixes
  ("critic r2 ..."). Do not delete existing comments. Keep `-WHFlight=0` (the legacy Spider-Man hero) behaviour unchanged.
- Units: traversal/flight simulation is METRES, UE axes, Z up; rendering is cm.
- Finish by writing `docs/invincible/loop/r3_<piece>_NOTES.md`: files changed, what each change does, which critic test it targets,
  what the root should check in the captures, and any cross-file requests. Neutral notes, no self-assessment. Reply in < 300 words.

## Ownership (round 3)

| Piece | Owner | Files (exclusive) |
|---|---|---|
| camera | builder A (Opus) | `Traversal/WebTravCamera.cpp/.h`, `Flight/WHFlightComponent.cpp/.h`, and in `Traversal/WebTravCharacter.cpp` ONLY the body of `AWebTravCharacter::FlightFrame` and the breach-hold camera block in Tick (search "bBreachHold") |
| fx | builder B (Sonnet) | `Flight/WHBreachDirector.cpp/.h`, new `unreal/WebHomage/Scripts/build_invincible_fx.py` (headless UE Python asset builder the root will run) |
| hero | builder C (Opus) | `Traversal/Anim/WebTravAnimInstance.cpp/.h`, `Flight/WHRescueDirector.cpp/.h`, the `FWebTravAnimFlight` struct in `Traversal/WebTravTypes.h` (add fields only), and the `fl17_rescue_crane` entry in `tools/invincible/make_flight_cases.py` |

Root (integrator) owns everything else, including `WebTravCharacter.cpp` outside the parts listed, the suite tools, docs and builds.

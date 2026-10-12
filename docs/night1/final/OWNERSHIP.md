# Final refinement loop: ownership contract (owner brief 2026-10-08)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Scope (owner, final): Spider-Man swinging and airborne movement animation, web deployment/appearance, plus the supplied-GLB integration
exception. Nothing else: no missions, combat, map/layout changes (beyond sensible supplied-prop placement), perf or look work.

Integration branch: `codex/m5-showcase-20261006` (pushed). Never `main`. One working tree (`~/spider-man-2`); generated Content is local
and git-ignored, so pieces share the tree and are separated by FILE ownership. Each agent stages only its own paths (`git add <paths>`,
never `git add -A`), commits with a trailer naming the agent, and does not push (the orchestrator pushes).

| Piece | Agent | Owns (exclusive) | Must not touch |
|---|---|---|---|
| SW: swing / air / flips / web deployment | builder SW (persistent) | `unreal/WebHomage/Source/WebHomage/Traversal/**` (incl. `Anim/`), `docs/night1/traversal/blender/**`, `Scripts/build_traversal.py`, `/Game/Traversal` content, `docs/night1/final/swing/**`, `tools/final/swing/**`, `docs/night1/traversal/scripts/final/**` | Props, maps, Core/, Life/, Night/, configs |
| PA: supplied GLB props | builder PA | `unreal/WebHomage/Scripts/build_props_m3.py` (new), `/Game/PropsM3/**` content (incl. its own test map `/Game/PropsM3/Maps/*`), `docs/night1/final/assets/**`, `tools/final/assets/**`, scratch `~/sm2-n1/_scratch/final/assets/` | Traversal source, every existing map (Showcase/Island/WP), build_manhattan.py, any C++ |
| Integration, specs, critic packs, HANDOFF.md | orchestrator | `docs/night1/final/{OWNERSHIP,SPEC_FINAL,SHOTLIST}.md`, `HANDOFF.md`, `build_manhattan.py` step wiring, adding the PropsM3 sublevel to the showcase/island maps | — |
| Critic (fresh each round, blind) | critic | `~/sm2-n1/_scratch/final/critic-r<NN>/` only | everything else; never reads builder notes, commits, HANDOFF, SPEC rationale |

Source of supplied GLBs (read-only, never modified or moved): `/Users/midirstudio2/Documents/SpiderMan_Asset_Import_M3_2026-10-08_task-4/GLBs/`.

## Shared rules (from the loop skill + AGENTS.md; every agent reads these)
- Every engine launch (game, commandlet, capture) goes through the shared coordinator `~/.cache/gpu-slot` via the existing guarded tools
  (`tools/m5/guarded_preview.py`, `tools/showcase/with_holder.sh`, `tools/showcase/play.py`). Never bypass PAUSED, the queue or holders,
  never create a second namespace. At most ONE renderer for this whole job at a time; hard global cap two.
- Do not touch the owner's interactive game, Qwen (`omlx`), DS1 x MW2, Hollow Current, the unloaded GLM, Unity, Blender sessions or
  any other process. Stop only processes you started (driver first, SIGTERM, wait 60 s, SIGKILL last resort, by your own PID).
- Never auto-relaunch after two crashes; diagnose.
- Delete only inside your own scratch/owned folders, with a path check.
- Evidence = the real `-game` binary rendering scripted input routes (deterministic, fixed 1/60 s `-dumpmovie`), labelled as offline
  visual evidence, never perf. Builder notes are neutral (inputs, settings, measured checks): no quality self-assessment.
- Suits: ORIGINAL suits only (Tessera default). None of the 56 supplied GLBs is a Spider-Man suit (orchestrator inspection
  2026-10-08), so no supplied suit is integrated; never label a civilian model as the hero.

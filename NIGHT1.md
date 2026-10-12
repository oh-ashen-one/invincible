# Opus 5.5 Loop — Night 1 (ownership contract)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation, nothing here is meant to infringe. See `DISCLAIMER.md`.

Integration branch: **`Opus-5.5-Loop-Night-1`** (worktree `~/spider-man-2-astra6`, owned by the orchestrator session).
Target: Marvel's Spider-Man 2 quality — traversal, Manhattan streets, characters, animation, combat, cohesion.
Hardware: Mac Studio M3 Ultra (80-core GPU, 256 GB). Output target **3840×2160 @ 60 fps**, internal resolution always disclosed, perf measured during real gameplay.

## Pieces and owners

Each piece has its own branch, worktree, Unreal content folder, MCP port and Blender instance. **Only the owner edits its folders.** Shared files (`main.js`, `.uproject`, `Config/Default*.ini`, `Source/WebHomage/WebHomage.Build.cs`) change only through the integrator.

| Piece | Branch | Worktree | UE content / source it owns | MCP port | Browser dev port |
|---|---|---|---|---|---|
| F1 UE C++ foundation | `night1/ue-foundation` | `~/sm2-n1/ue-foundation` | `Source/WebHomage/Core`, Target files, `Config/` (until handed back) | 8770 | — |
| F2 Reference library | (private repo `spiderman-learnings`, branch `night1/refs`) | `~/spiderman-learnings` | `refs/` | — | — |
| F3 Browser baseline + playtest | `night1/browser-baseline` | `~/sm2-n1/browser-baseline` | `docs/night1/baseline/` | — | 5201 |
| P1 City (export + UE city + facades) | `night1/city` | `~/sm2-n1/city` | `tools/export/`, `/Game/City`, `/Game/Tests/City`, `Shaders/City/`, `Scripts/build_city.py`, `Scripts/city_shots.json` | 8771 | 5202 |
| P2 Characters (hero, skins, thugs, crowd) | `night1/characters` | `~/sm2-n1/characters` | `/Game/Characters`, `tools/ue_char/`, `Source/WebHomage/Characters/`, `Scripts/build_characters.py`, Blender work under `art/night1/characters` | 8772 | 5203 |
| P3 Traversal + camera | `night1/traversal` | `~/sm2-n1/traversal` | `Source/WebHomage/Traversal`, `/Game/Traversal`, `/Game/Tests/Traversal` | 8773 | 5204 |
| P4 Look, lighting, post, perf | `night1/look` | `~/sm2-n1/look` | `/Game/Look`, `/Game/Tests/Look`, `tools/perf_ue/` | 8774 | 5205 |
| P5 Combat (wave 2) | `night1/combat` | `~/sm2-n1/combat` | `Source/WebHomage/Combat`, `/Game/Combat` | 8775 | 5206 |
| P6 City life: crowd, traffic, water (wave 2) | `night1/life` | `~/sm2-n1/life` | `/Game/Life`, `/Game/Water` | 8776 | 5207 |
| C Integrated Manhattan map | `night1/manhattan` | `~/sm2-n1/manhattan` | `/Game/Maps/Manhattan`, `Scripts/build_manhattan.py`, `docs/night1/manhattan/` | 8777 | 5208 |
| F 4K/60 perf (wave 2) | `night1/perf` | `~/sm2-n1/perf` | `tools/perf_ue/` successors, `docs/night1/perf/` | 8778 | — |
| Water A/B (same brief, two models) | `night1/water-ab-sonnet` / `night1/water-ab-opus` | `~/sm2-n1/water-ab-sonnet` / `~/sm2-n1/water-ab-opus` | `/Game/Water`, `Scripts/build_water.py`, `docs/night1/water/` (each in its own worktree; the blind-critic winner merges) | 8779 / 8780 | — |
| Integrator / regression playtester | `Opus-5.5-Loop-Night-1` | `~/spider-man-2-astra6` | `/Game/Maps/Manhattan` (main map), merges | 8765 | 5200 |

Evidence goes to `docs/night1/<piece>/round-NN/` (captures, clips, perf CSV, critic verdicts). Large videos are committed as mp4 ≤ 15 MB each.

## Loop per piece

1. Builder builds → runs the real game → captures matching views / movement sequences listed in `docs/night1/<piece>/SHOTLIST.md`.
2. A **fresh critic** (new agent, no builder summary) gets only the rendered captures/clips + the matching Spider-Man 2 references, anonymised A/B where practical, and returns: scores per axis, the **single biggest gap**, and a verdict (`FAILS TARGET` / `APPROACHES TARGET` / `MEETS TARGET`) with evidence.
3. Builder fixes that one gap. Repeat. No fixed round count; a piece closes only on a critic `MEETS TARGET` backed by evidence.
4. Between waves, a fresh integration agent plays the merged game (browser + UE), logs regressions, fixes coherence.

## Protected (never touch)

`~/spider-man-2` (flight-dynamics session), `~/spider-man-2-claude` (3d-animations-astra), `~/spider-man-2-water-effects`, dev ports 5173/5191, Blender MCP port 19891 and any Blender/Unreal instance this loop did not start, branch `main`.

## Model assignment (owner, 2026-09-29 — applies to every spawn after 14:20; running work finishes as is)

| Role | Model / effort |
|---|---|
| Builders — hard/central engineering: P3 traversal, C Manhattan integration, P5 combat, F perf | **Opus 5.5, high** (`opus-critic` type or Workflow `{model:'opus', effort:'high'}`) |
| Builders — pipelines/assets/tooling: P1 city, P2 characters, P4 look, P6 city life, A GPU lock | **Sonnet 5.5, extra-high** (`sm2-sonnet-builder`, or Workflow `{model:'sonnet', effort:'xhigh'}`) |
| Critics every round; integration playtester between waves; any super-important engineering by judgment | **Opus 5.5, high** (`opus-critic`, or Workflow `{model:'opus', effort:'high'}`) |
| Direction: wave planning, reconciling contradictory critic demands, deciding what runs next and whether a piece is done | **Fable 5.1, high** (`fable-director`, or Workflow `{model:'fable', effort:'high'}`) — sparingly (own weekly limit): one pass per wave, stall/oscillation diagnosis, final acceptance |

Continuity between fresh builders comes from `docs/night1/<piece>/HANDOFF.md`, rewritten at the end of every round.

## Overnight resume (owner, 2026-09-29 23:55)

Weekly usage was at 50 %. Builders lean on **Sonnet 5.5 xhigh** for every piece; **Opus 5.5 high** builds the traversal flips (owner priority, from round 11) and runs every critic (never skipped); **Fable 5.1** only for a stalled/oscillating piece or final acceptance. Up to 3 rounds per piece tonight (perf 2).

## Day 2 resume (owner, 2026-09-30 ~10:30)

Weekly usage at 80 %. Owner (corrected, same morning): quality first — **split building: Opus 5.5 high for traversal/flips, combat, perf, integration; Sonnet 5.5 xhigh for city, life, look, character assets, pipelines**; **Opus 5.5 high for every blind critic** (never skipped); Fable 5.1 only for stall diagnosis/final acceptance. The three rounds already started this morning keep their Sonnet builders. One round per piece, three pieces at a time (traversal r13 renders, characters r6 engine check, perf r3 shipped preset), engine cap hard 2, new safety rules from oh-ashen-one/agents-md#4 (merged).

## Model policy update (owner, 2026-10-01 ~00:15)

Weekly limit reset. **Opus 5.5 high for every builder** (all pieces, every new round) and Opus 5.5 high for every critic; Sonnet only if a specific task is purely mechanical. Fable 5.1 still only for stalls / final acceptance. Rounds already running finish on their current model.

## Model policy correction (owner, 2026-10-01 ~01:30)

NOT all-Opus: **mostly Opus 5.5 high with a healthy share of Sonnet 5.5 xhigh** (Opus for hard engineering: traversal/flips, perf, combat, character animation/fight; Sonnet for content/pipelines: city, life, look, assets). Critics always Opus 5.5 high. **Fable 5.1 high is the orchestrator/director** (wave plans, model assignment from the ledger, stall diagnosis, acceptance) — night-2 plan in docs/night1/director/PLAN-night2.md.

## Orchestration locked in (owner, 2026-10-01 ~01:40)

**Fable 5.1 at MAX thinking makes every high-level call**: wave plans, per-round next target, builder model per round, merge decisions, stall diagnosis, morning acceptance. It is built into the loop script (a director agent after every critic). The work: a healthy mix of **Opus 5.5 high (mostly)** and **Sonnet 5.5 xhigh**; critics Opus 5.5 high. The executing session (Claude Code) only carries the director decisions out (launch, merge, push, safety). Global rule: PR oh-ashen-one/agents-md (fable-max-orchestrator).

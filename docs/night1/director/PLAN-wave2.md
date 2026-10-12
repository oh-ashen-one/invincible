# Director plan — Wave 2 (Fable 5.1, 2026-09-29 ~14:30)

Evidence read: NIGHT1.md, RULES.md, progress.json, all 16 critic texts, four HANDOFFs, baseline PLAYTEST/PERF, CAPTURE.md, r5 city street still, r8 traversal still. Live check: 3 game instances running at once, GPU 100 %, and the look piece's 4K perf run is one of them — that perf number is contaminated by construction.

## 1. Diagnosis

**Traversal (r9 running, 8 rounds, scores 3–5 flat since r5).** Not converging. Three causes:
- It is judged in the gray-box `Trav_Canyon` while the A/B pairs are against the real game. Half of every lost pair is environment, not traversal. The r8 still proves it: pastel boxes, no sky, no city read. Look already runs the traversal hero in the real city (`Look_Midtown`, 7067 boxes). **Structural fix: from r10 traversal captures in `Look_Midtown_golden` (P4's map) and the critic judges only motion/camera axes.**
- Single-gap rounds oscillate: r7 "hug facades → clear 3 m", r8 "now too centred/treadmill", r4/r7 critics mis-measured hero height. Each critic re-derives targets from scratch. **Fix: a written TRAVERSAL-SPEC.md (Opus, one pass) with fixed numeric targets from the refs** (cadence, drop, hero height %, x-spread, camera yaw/roll envelope, clearance, anchor elevation). Builder ships a checker per line; critics score against the spec and only add gaps, never contradict it.
- Body animation is capped by the browser clip set (no wall-run cycle, no landing tiers). That is a P2 asset problem; log it as a cross-piece dependency, don't keep punishing P3 for it.

**City (r6 running, 5 rounds, 4-5-3-4-5).** Converging, slowly and honestly: each round fixes one layer (horizon → foliage → glass → street kit → far field). Remaining critic asks are enumerable: far field, rooftops, Times Square coverage, sidewalks. **Switch city to multi-gap rounds (3 gaps/round) with a CITY-SPEC checklist**; single-gap is wasting a 9-min build + 8 captures per item.

**Characters (r3 running, 2 rounds, enemies 2).** Stalled on asset quality, not tuning. Thug/brute rebuild from Tripo people is right; civilians "nobody walks" is a rig/anim bug, not art. Run **two gaps per round** (enemies art + civilian locomotion) since they touch different files.

**Look (r2 running).** One round in; night targets are numeric and good. Its real problem is that it owns 4K/60 perf and cannot measure it. Split perf out (below).

## 2. Wave 2 — start now, in this order

| # | Piece | Model | Deps | Round-1 deliverable | Pass test |
|---|---|---|---|---|---|
| A | **Capture lock + perf protocol** (`tools/gpu_lock/`): `flock` on `/Users/midir/sm2-n1/_scratch/gpu.lock`, `capture` class = shared (max 2), `perf` class = exclusive + waits for `ioreg` util < 15 % for 10 s, records util before/during into the json | Sonnet xhigh | none, 1 hour | all four `capture_round.sh`/`run_perf.py` wrappers call it | first clean look perf run with util < 15 % logged; contaminated flag never true |
| B | **Specs**: TRAVERSAL-SPEC, CITY-SPEC, CHARACTERS-SPEC, LOOK-SPEC in `docs/night1/<piece>/SPEC.md` | Opus high (one agent, reads refs + all critics) | none | numeric targets per axis, each with a checker name | every critic prompt cites the spec; r10 traversal critic scores against it |
| C | **Integration map** `/Game/Maps/Manhattan` = P1 city + P4 rig + P3 hero + P2 lineup actors; `Scripts/build_manhattan.py` | Opus high (shared files, merge judgment) | A, current rounds merged | map builds headless; hero swings the avenue | 30 s scripted swing runs without falling through; 4K stills S1/S2/S4 |
| D | **P5 Combat** port of `src/game/combat` (2.5k lines) into `Source/WebHomage/Combat`, enemies = P2 thug/brute | Sonnet xhigh | C for the map; P2 r3 for meshes (use r2 meshes meanwhile) | 4-hit combo, dodge, web-strike, finisher, 6 thugs, hit FX | 25 s fight script: every beat fires, telemetry matches browser fight log; critic axis set from spec |
| E | **P6 City life**: traffic (IP-clean liveries), 6-civilian crowd on sidewalks, water plane + shore | Sonnet xhigh | C; P2 citizens | avenue with 30 cars + 40 peds moving; river reflects | critic S1/S4 with life; no lockstep (phase spread test) |
| F | **Perf piece** (own branch `night1/perf`): 4K/60 on the Manhattan map, TSR %, VSM/Lumen budgets | Opus high | A, C | table: native / 67 / 50 % with GPU per pass, all at util < 15 % | ≥ 60 fps p50, ≥ 55 p95 in the 30 s swing at a disclosed internal res |
| G | **Regression playtester** between waves | Opus high | C | plays merged map; logs bugs against baseline PLAYTEST list | every High bug from baseline is fixed or ticketed |

Order: A and B now (cheap, unblock everything). C as soon as r6/r3/r2 merge. D and E start after C lands its first build. F starts after C, runs perf only under the exclusive lock.

## 3. Concurrency

Hard cap stays 3 Unreal processes. Rule: **2 builder slots + 1 capture/perf slot**, enforced by the lock in A. Perf runs are exclusive and run in a serial queue (one agent may hold the perf lock for at most 15 min). All perf numbers so far are void; re-baseline once after A lands. Agents in parallel: 4 builders (traversal, city, characters, one wave-2 piece) + 1 critic is the budget; a 5th builder waits.

## 4. Model use

- **Fable (me)**: wave boundaries, every 4th round per piece (r12 traversal, r8 city, r6 characters, r4 look), any two consecutive FAILS with score movement < 1, final MEETS acceptance.
- **Opus**: every critic; specs (B); integration map (C); perf piece (F); regression (G); traversal builder stays Opus through r10 (spec + map move), then Sonnet.
- **Sonnet xhigh**: all other builders, the lock tool, combat/life ports.

## 5. Risks / owner decisions

1. **Hero suit resembles a licensed design** (critic r2). Decide: redesign or keep with disclaimer. Blocks any public showing.
2. **Browser build still ships Marvel-brand ads**; only UE is sanitised. Decide whether the browser build must also be sanitised.
3. **LFS exhausted**: reference clips and UE snapshots local-only. If the Studio disk fails, refs regenerate but snapshots don't. Approve a private-repo LFS purchase or accept the risk.
4. Perf: 60 fps at 4K native is unlikely; expect TSR 67 % (2573x1447 internal) as the honest target. Owner to confirm that disclosed-internal-res counts.
5. Combat/life will add GPU load after the perf budget is set; F must re-run after D/E merge.

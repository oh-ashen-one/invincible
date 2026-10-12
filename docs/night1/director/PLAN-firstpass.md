# Director plan — FIRST PASS (Fable 5.1 xhigh, 2026-10-01 ~10:30 EDT, planning only)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Evidence: OWNER-PRIORITIES, HANDOFF, ACCEPTANCE-morning, PLAN-night2, RULES, NIGHT1, latest critics (traversal r18, city r10, look r3, perf r6, water AB), piece HANDOFFs, the export/build scripts, `WebTravFlips.*`, browser `layout.js` / `suits.js` / `skinswap.js`. Shaping facts: the browser island is **6.8 x 1.45 km** (7 x 27 tiles of 256 m, ~130 land tiles); the UE city is **9 tiles** (2.45 M near tris, 547 MB export, 282 s import) plus a bare-mass far ring; facades are **non-Nanite** (8 UV data channels); the water grid already spans 80 km with an island-wide shore map; the look rig has SkyAtmosphere + VolumetricCloud + fog as three separate maps; the disk has **87 GB free**.

## 1. Pieces (7 streams)

| Piece | Branch | Scope | Builder |
|---|---|---|---|
| **A Island** (new; absorbs city + manhattan C) | `night1/island` | `tools/export`, `build_city.py`, `build_manhattan.py`. Export every land tile per district (own Chrome page each; 12 GB heap); World Partition, 256 m streaming grid, ~1.2 km detailed range, existing `facadeLod` masses + `far_skyline` as the HLOD/far layer; simple-as-complex collision on every facade/roof/ground tile; district order Midtown -> Times-Sq/Park -> FiDi/Battery -> Village -> Upper West/East -> north tip; island-wide sun-mask; Nanite spike (§5); then city r11's polish lines (S8 glass, far-LOD window grid, roof props). | M1-M2 **Opus high**; M3 **Sonnet xhigh** |
| **B Swing + camera** | `night1/traversal` (minus flip files) | Arc clear of canopies (T7), `hero_occl` counts leaves (TC-G), TC-C p90 <= .36, web <= 45 %, wall-run sprint stride, ultrawide FOV/aspect. TC-A..K frozen. | **Opus high** |
| **C Tricks** (new, split out) | `night1/tricks`: `WebTravFlips.*`, `Traversal/Anim/*`, flip clips, trick input | Per-instance variation (duration/peak rate +-10-20 % from release speed and apex, arm timing), tight tuck, >= 10 programs (front/back single + double, pike, layout, twists 180/360/540, chains), owner-clip A/B. | **Opus high**; Blender clips **Sonnet xhigh** |
| **D Sky** | `night1/look` (sky first, lighting second) | One map, continuous time of day (`wh.TimeOfDay`), clouds at every hour, aerial perspective (owns far-band luma); then golden key/fill, night windows. | ToD sequencer **Opus**; sweeps **Sonnet** |
| **E Terrain** (new) | `night1/terrain`, `/Game/Terrain` | Parks (lawns, Reservoir, meadows, grass), shorelines (seawalls, esplanades, piers), ground at swing height, street trees: `park.js` / `ground.js` / `waterfront.js` export kinds island-wide. | **Sonnet xhigh** |
| **F Water** | `night1/water` (merged Opus build) | Glints, ring artifact, piling foam, C14 brightness; coverage as the island grows (contact foam needs terrain seawalls). | **Opus high** |
| **G Hero skins** | `night1/characters` (hero only) | Original-suit generator: the Tessera procedural pipeline parameterised (JSON palettes, panel patterns, glyph set -> N material instances; whole-mesh suits later); swap by key cycle + `wh.Suit`; settings hook. | **Sonnet xhigh** |

Perf folds in: one exclusive Opus session per Island milestone, numbers only after `look_gate.py` PASS. **Paused:** combat, life (crowds/traffic), thugs/fight in characters, manhattan C as its own piece. Critics: fresh blind Opus 5.5 high every round, never skipped. Fable directs, never builds.

## 2. Ordering under the 1-GPU cap

CPU-side, parallel, no slot: island export/import (`-nullrhi`, max 2 at once, never beside perf), Blender clips, suit generator, preset JSON, water/terrain shader work. GPU FIFO: **tricks/swing 1080p clips (<= 10 min holds) > sky tour stills > island milestone capture > water dolly > skins/terrain stills > perf exclusive last**; 4K only for a round's final pack.

- **Phase 0 (today, CPU):** disk reclaim to >= 250 GB free (regenerable `Intermediate`/DDC/`Saved` of paused worktrees, old frames; anything else asks the owner); island spike (full export measured: tris, GB, minutes; WP skeleton); tricks r1 code; suit generator; ToD sequencer.
- **Phase 1 (nights 2-3):** Island M1 (Midtown 7 x 9 tiles streamed, collision everywhere) 2 rounds; traversal r19-r20; tricks r1-r2; sky r4-r5; water r2.
- **Phase 2 (nights 3-4):** Island M2 (whole island + HLOD) 2 rounds; terrain r1-r2; skins r1-r2; perf #1.
- **Phase 3:** Island M3 (district polish) 1-2; terrain r3; tricks r3-r4; sky r6; perf #2; final acceptance.

~25 rounds x ~45 GPU-min ~ 19 GPU-hours ~ three nights at cap 1. **First pass done** = one standalone `/Game/Maps/Manhattan` with continuous time of day, swingable from Battery to the north tip without leaving detailed geometry, every §4 line passing under a blind critic, perf disclosed and passing.

## 3. Models

**Opus 5.5 high:** Island M1-M2, swing/camera, trick programs, water, ToD sequencer, perf (central engineering). **Sonnet 5.5 xhigh:** Island M3, terrain, skins, sky sweeps, Blender clips (pipelines/assets; the ledger shows Sonnet converging on city/look content). Critics Opus high, blind, every round. Fable 5.1 plans, assigns, merges. Mix ~60 % Opus.

## 4. Acceptance (4K output; internal resolution stated on every number)

- **Island:** no `facadeLod` mass within 1.2 km of the hero on land; 30 s routes in 3 districts: 0 fall-through / stuck / camera-in-geometry; 60 s north-south swing at 4K TSR 50 %: 0 hitches > 25 ms; fresh `Content/` -> playable from scripts <= 90 min, Content <= 40 GB; S8 glass <= 1.5 % > 204, far band T2 <= 10 %, flat 8x8 blocks <= 10 %; skyline >= 6, no axis < 5.
- **Swing + camera:** TC-C p90 <= .36, TC-G counts foliage, T7 clear, web <= 45 %; swing >= 7, camera >= 7; reference wins <= 3 of 6 blind pairs.
- **Tricks:** same-type tricks differ >= 40 deg/s in a 0.1 s sample, durations vary +-10-20 %; tuck wrists <= .15 m from shins, knees <= .25 m apart, held >= .25 s; 0 slow limb samples; >= 10 programs in one 60 s clip; flips >= 8 vs the owner clip.
- **Sky:** `wh.TimeOfDay` 0-24 continuous in one map; golden p5 Y <= 12, p95/p5 >= 16; far band 15-32 Y under the sky, B-R +-10; overcast 0 crisp shadows, 0.00 % clipping; night median Y <= 42, window points >= 3 %; sun/sky/ToD >= 7, atmosphere >= 6.
- **Terrain:** park crops high-pass sd >= 8, grass/meadow cover >= 90 % of park land, shoreline continuous (no gap > 5 m on a shore walk), ground C2 lines hold; axes >= 6.
- **Water:** near crop high-pass sd >= 12, p99.5 >= 150, glints >= 1 %, mean Y <= 80; C14 5-35 at S4; autocorrelation <= .10 at 80 px (no ring); piling foam present; <= 2.5 ms; axes >= 6.
- **Skins:** >= 6 original suits, swap <= 0.5 s, OCR + blind IP read find no official emblem/colour blocking; no seam > 40 px at 4K; IQ >= 6.
- **Perf:** 4K output TSR 50 % (1920x1080 internal): p50 >= 60, p95 >= 55 on all 3 district routes; same at 3440x1440 output TSR 65 % (2236x936, the owner's display); `look_gate.py` PASS, no undisclosed loss.

## 5. Risks

- **Disk (87 GB free):** blocker. Phase 0 reclaim; island writes to one scratch + one worktree; abort M1 under 150 GB free.
- **Build time / memory:** linear scale ~35 M tris, ~6 GB export, ~65 min import; per-district, idempotent, resumable; export GLBs cached in scratch; real timings reported after the spike.
- **Facade shader vs scale:** non-Nanite facades at island scale may break VSM/60 fps. M1 spike: data channels to a per-building data texture + Nanite, decided by one exclusive perf A/B with a blind S1 look check; fallback tighter streaming radius + HLOD impostors. No silent look loss.
- **GPU/WindowServer:** every launch via `gpu_slot.sh` at cap 1, `stop_ue.sh` only, no listeners, orchestrator in `tmux`; commandlets `-nullrhi` but memory-heavy, max 2.
- **Rebuild-from-scripts (no LFS):** nothing in `Content/` committed; the fresh-rebuild timing in §4 is itself an acceptance step.
- **Original-suit IP:** suits only from the parameterised Tessera generator; no paid generation; critic IP gate + OCR every round; owner sees swatches before merge.
- **Scope creep:** no HUD/save/boats/rain/breakables/life/combat rounds until the owner calls the first pass done.

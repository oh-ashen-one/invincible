# ISLAND-SPEC (piece A: the whole 4K Manhattan) — fixed, measurable targets

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`. Reference footage stays private
> (`~/spiderman-learnings`); nothing from it enters this fork.

Owner north star (2026-10-01): "the highest-quality version of web slinging around the highest-quality version of Manhattan". The island
piece makes the detailed city cover the whole island and makes it **swingable everywhere** (collision that matches what is drawn).
Source of the targets: `docs/night1/director/PLAN-firstpass.md` §4 (Island) and §5 (risks). The look lines of the old city spec
(`docs/night1/city/SPEC.md` C1-C16) still apply to every detailed tile and are scored by the critic.

## 1. Coverage (milestones)
| id | target | checker |
|---|---|---|
| I1 | M1: every land tile of Midtown 7 x 9 (ix -3..3, iz -5..3) exported at full detail; **0 facadeLod (bare-mass) meshes inside the detailed region** | `tools/export/island_coll_audit.py` `facadeLod_meshes_inside_region` |
| I2 | M1: no facadeLod mass within 1.2 km of the hero **on a route inside Midtown** (M2: anywhere on land) | `tools/export/island_route_check.py` `facadeLod_min_dist_m` (>= 1200) |
| I3 | M2: whole island (ix -4..3, iz -14..13, ~159 tiles with geometry) at full detail, far layer = existing facadeLod masses + far skyline as HLOD | spike numbers below + build manifest |

## 2. Collision = what is drawn (swing everywhere)
| id | target | checker |
|---|---|---|
| I4 | Built in, not patched at runtime: merged per-tile visual meshes NoCollision; ground (asphalt / sidewalks / land / water plane) collides and is tagged `WHGround`; one invisible `WHBox` cube per browser collision box | `build_city.py` steps `mesh`/`map`/`coll`/`wp` log lines; game log `WebTravWorld: N building boxes ... 0 wide merged meshes made visual-only` |
| I5 | Building cells (1 m grid) where the box top and the drawn top agree within 1.5 m: **phantom (box above roof) <= 1 %, hollow (drawn building without box) <= 2 %** | `island_coll_audit.py` |
| I6 | 30 s routes (>= 3, in >= 2 directions, crossing new tiles): **0 fall-through, 0 stuck, 0 mid-air frames, 0 wall-air frames** | `island_route_check.py` on the route telemetry CSVs |

## 3. Streaming and build
| id | target | checker |
|---|---|---|
| I7 | `/Game/Maps/Manhattan_WP`: World Partition, 2D grid of **256 m cells, 1.2 km loading range**; detailed tiles spatially loaded, far layer + ground + WHBox always loaded; plays from scripts | `build_city.py` step `wp` log; game log (WP cells streamed); captures from this map |
| I8 | Everything rebuilt by committed scripts (no Content, no LFS); fresh rebuild time and Content size reported (§4 targets: <= 90 min, <= 40 GB for the whole island) | `build_manhattan.py` step timings, `du -sh Content` |
| I9 | Disk: no island export below **150 GB free** (abort + report) | `island_spike.py --real`, `build_manhattan.py city_export` |

## 4. Look (from the city spec; critic-scored)
Detailed tiles keep C1-C16. Island-wide additions: no visible seam between detailed tiles; no bare-mass block within the detailed range;
far band reads as city (C11) in every direction.

## 5. Not here
Performance numbers (exclusive perf runs only, later; PLAN §4 perf lines), sky / time of day (piece D), terrain / parks / shore (piece E),
water (piece F).

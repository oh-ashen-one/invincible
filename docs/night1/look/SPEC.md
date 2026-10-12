# LOOK-SPEC (P4 lighting, atmosphere, post) — fixed targets, measured from refs

> Homage fan game; not affiliated with Marvel, Sony or Insomniac. Refs private.
> Written 2026-09-29 by spec agent B. Instrument: `specs/tools/lum_by_tod.py` on every non-UI still (1920 px wide, INTER_AREA),
> luma Y = .2126R+.7152G+.0722B (8-bit sRGB), "clipped" = any channel ≥ 250, "near-black" = Y < 10. Per-still results: `specs/data/lum.json`.
> Stats are the spread across ref stills of one lighting group (p10–p90 of per-still values). Run the same script on our 1080p stills
> (captured at the documented game time, eye adaptation settled). `dn` refs are HDR tone-mapped to SDR by the uploader (source is PQ 10-bit).
> Perf (4K/60) moves to the perf piece F under the GPU lock; it is not a LOOK axis any more.

## 1. Exposure per time of day (L-A, L-E)
| id | preset | frame mean Y | Y<10 (near-black) | Y<25 | clipped | p99 Y | measured from |
|---|---|---|---|---|---|---|---|
| L1 | golden (Look_*_golden) | **61–100** (med 84) | **≤ 8 %** (med 1.0) | med 6 %, ≤ 27 % | **≤ 1.8 %** per frame, set median ≤ 0.3 % | 171–248 | 74 golden/sunset stills (nm, og, cp, gr) |
| L2 | midday overcast | **83–97** (med 91.5) | **≤ 0.05 %** | ≤ 3.8 % | **0.00 %** | 161–205 | 31 dn stills |
| L3 | night | **37–60** (nt p10–p90 37.5–53.3; incl. ts up to 80) | **≤ 1.0 %** (nt p90 0.66) | 25–45 % (nt med 37) | ≤ 1.7 % (nt p90), emissive only | 195–255 | 21 nt stills (+16 ts) |
| L4 | day/afternoon | 55–89 | ≤ 12.7 % | 10–28 % | ≤ 0.3 % | 170–220 | 24 stills |
| L5 | sun-facing golden view (S7-type) | 59–118 | ≤ 8.8 % | — | **≤ 0.7 %** | — | swing-avenue-sunset__nm_0654 .67 %, skyline-sunset-nm .00 %, sunset-swing-trailer .10 %, dive-sunset-og .02 %, sunset-river-og .07 %, rooftops-watertowers-golden .01 % |
Round-1 critic night targets (mean ≥ 35, ≤ 3 % < 10) are consistent with L3; L3 is the binding, stricter line.

## 2. Colour by time of day (L-A)
| id | target (frame mean B−R, 8-bit) | measured from (median [p10, p90]) |
|---|---|---|
| L6 | golden warm: **−55 … −20** | og −52 [−78, −31], nm −26 [−38, −17], cp −45 [−82, −31], gr −34 [−46, −8] |
| L7 | midday overcast near neutral: **−19 … +8** | dn −6.5 [−19, +8] |
| L8 | night near neutral: **−13 … +13** (blue sky/moon, warm lamps balance out) | nt 0.0 [−13, +13] |

## 3. Atmosphere and depth (L-C) — shared with CITY-SPEC C11–C15
| id | target | measured from (`haze_regions.py`) |
|---|---|---|
| L9 | RMS contrast falls with distance: far/near ratio **0.25–0.45**, monotonic near → mid → far → horizon | skyline-perch-nm .654 → .447 → .182 → .074; skyline-perch-dn .310 → .194 → .125 |
| L10 | Far band luma **15–32 below the sky band**; far band takes the sky tint (B−R within ±10 of sky) | dn far city −15.7, far shore −26.6 (B−R 15.7/15.4 vs sky 15.6); nm horizon −13.9, far shore −32.0 (−46 vs −37) |
| L11 | Midday sky: horizon band **≥ zenith band** (+3 … +5 Y) | skyline-perch-dn 134.8 vs 131.4; skyline-overcast-dn 172.9 vs 168.6. (Golden varies: gr +56, nm −10 → no golden rule) |
| L12 | Saturation drops with distance (golden): HSV S near .66 → mid .55 → far .44 → horizon .35 | skyline-perch-nm |

## 4. Night street lighting (L-F)
| id | target | measured from |
|---|---|---|
| L13 | Street-level night view: **≥ 5 lit blobs** in the bottom half (Gaussian σ = 12 px at 1080p, Y ≥ 100, area ≥ 400 px); ref median 9 | night-street-2 7, night-street-level 9, night-street-car 12, hero-idle-crosswalk-night 9, landing-crosswalk-night 3; swing-night-canyon 21 |
| L14 | Bottom third: **p90 Y ≥ 100** (pools) and **p10 Y 15–30** (dark between pools, not black) | p90: 106/143/132/131/138; p10: 17.2/21.9/20.4/26.4/19.9 |
| L15 | Hero readable at night: hero-mask mean Y ≥ 40 | round-1 critic line; ref hero-mask luma not measured in this pass (keep as provisional) |
| L16 | Lamp spacing along the street | **unmeasurable in metres from refs**; critic's "every 25–30 m" stays a guideline |

## 5. Reflections and post (L-D, L-E)
| id | target | measured from |
|---|---|---|
| L17 | No pure-black glass panel in daylight: glass-mask p10 Y ≥ 20 | rule from r1 defect; glass-only ref crops not isolated in this pass |
| L18 | Motion blur while swinging: edge/centre sharpness p50 0.20–0.65 (= TRAVERSAL T20), hero sharper than ring (T21) | swing clips, see TRAVERSAL-SPEC §4 |
| L19 | Vignette, bloom radius, lens ghosts | **unmeasurable from refs** (corner/centre luma ratio p10–p90 0.55–1.74 across 168 stills: content-dominated). Rule: no sourceless lens ghost (r1 defect) |
| L20 | Banding/aliasing | judged at native 4K crops; no numeric ref line |
Checkers: `look_lum_check.py` (= lum_by_tod.py on our stills, per preset; L1–L8), `farfield_check.py` (shared with P1; L9–L12, depth + sky masks),
`night_pool_check.py` (L13–L14 blob counter above, same σ/threshold), glass-stencil capture for L17.

## 6. Axis → spec lines
| axis | lines |
|---|---|
| L-A Sun / sky / time of day | L1, L2, L4, L5, L6, L7, L11 |
| L-B GI & shadows | L1–L3 near-black columns, L14 p10 (shadowed side lifted, never crushed) |
| L-C Atmosphere & depth | L9, L10, L12 |
| L-D Reflections & materials | L17 (+ side-by-side vs wallrun-glass-*, webwings-bridge-night) |
| L-E Post & exposure | L1–L5 clipped columns, L18, L19 rule |
| L-F Night look | L3, L8, L13, L14, L15 |
Critic rules: score against these lines; ADD observed gaps with file@coords; do not contradict a line unless `lum_by_tod.py` /
`haze_regions.py` run on the ref shows the ref violates it. Night used to hide missing city detail is judged as if lit.

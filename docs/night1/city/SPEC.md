# CITY-SPEC (P1 city: facades, streets, rooftops, skyline) — fixed targets, measured from refs

> Homage fan game; not affiliated with Marvel, Sony or Insomniac. Refs private; no ref text, logo or billboard art may enter the fork.
> Written 2026-09-29 by spec agent B. Numbers are measured on the named ref files at 1920×1080 (4K stills downscaled with INTER_AREA).
> Instruments: `specs/tools/lum_by_tod.py`, `haze_regions.py` (per-region RGB, luma Y = .2126R+.7152G+.0722B, RMS contrast, |Laplacian|),
> `count_people_vehicles.py` (YOLO11x, conf .30–.35). Region boxes are listed in `haze_regions.py`; reuse the same boxes on our S-views.
> City rounds now fix **3 gaps per round** from this checklist (director plan). Lighting-caused defects are logged to P4, not scored here.

## 1. Facades (C-A)
| id | target | measured from |
|---|---|---|
| C1 | Daylight facade crop (windows + wall, no sky): **≤ 1.5 % of pixels with Y > 204 (80 %)**, p95 Y ≤ 192, p99 ≤ 206 | 8 crops: street-avenue-hero-taxis (x910–1100,y0–300: 0.19 %, p95 185; x1150–1350,y0–200: 0.74 %), street-sidewalk-pedestrians (x1060–1330,y0–300: 0.38 %), street-midtown-high (0.12 %, 0.01 %), swing-canyon-chase-high left (1.04 %, p99 205), swing-brick-canyon left (0.91 %), swing-canyon-dn left (0.00 %) |
| C2 | Facade crop mean Y **52–119** in daylight (no blown or crushed facades) | same 8 crops: 52.0–118.7 |
| C3 | Window openings read as depth: frames/sills/recess, varied interior states | unmeasurable as a number from refs; judged side-by-side with `street-avenue-hero-taxis__og_0000`, `street-federal-hall-intersection__dn_1038` |
Checker `facade_px_check.py`: facade-only mask from a custom-stencil capture (facade materials stencil 1) on S1/S2/S7/S8; report C1/C2.
The r03 test "≤ 10 % of window pixels > 80 %" is superseded by C1 (the ref is 10× stricter on whole facade crops).

## 2. Street level (C-B)
| id | target | measured from |
|---|---|---|
| C4 | Street-level daytime frame (S1-type view): **cars 5–19 (median ≈ 11)**, people 6–32 (median ≈ 24), traffic lights ≥ 1 | YOLO on 12 street stills + 4 run stills (dn/og): avenue-hero-taxis cars 10 / people 6 / lights 1; street-walk-taxis 16/32; sidewalk-pedestrians 15/28; federal-hall 18/23/7; street-chase 19/15/7; run-sidewalk 10/30; run-turn 11/24 |
| C5 | Night street frame: cars 11–21, people 1–4 | night-street-2 13/3, night-street-level 21/1, night-street-car 11/4 |
| C6 | Avenue seen from swing height (S2-type): **vehicles median 14–22 per frame** | swing-avenue-traffic med 14 (p90 24), swing-avenue-midday med 22 (p90 24), night-street-swing med 12 |
| C7 | Street trees in the S1-type frame: **≥ 3**; signed storefronts: **≥ 2 per side** | hand count on avenue-hero-taxis (trees at x0–380, x580–720, x1380–1640; left green awning + lit sign x230, right shop signs x1450–1520) |
| C8 | Per-20 m clutter list (hydrant, trash can, news/mail box, tree pit, lamp, manhole, crosswalk paint) | **unmeasurable per metre from refs** (no depth). CRITIC_GUIDE list stays as a presence checklist, not a numeric target |
Cars/people are P6 (life) content; P1 owns parked-car and prop placement. Checker `street_count_check.py`: run `count_people_vehicles.py`
on our S1/S2/S6 captures (same model, same thresholds) + engine query of prop actors within 20 m sidewalk windows (reported, not gated).

## 3. Rooftops (C-C)
| id | target | measured from |
|---|---|---|
| C9 | Rooftop view (S3-type): **≥ 2 wooden water towers in frame** + bulkheads/AC; no roof in frame is an empty plane | hand count on rooftops-watertowers-golden__nm_0314 (towers at x≈745,y≈400 and x≈1720,y≈230; bulkhead x840–1150) |
| C10 | Clutter per rooftop (objects/roof) | **unmeasurable from refs** at countable resolution beyond C9; judged side-by-side |

## 4. Far field and skyline (C-C, C-D)
| id | target | measured from |
|---|---|---|
| C11 | Far-city band texture: mean |Laplacian| **≥ 6× the sky band's**; flat 8×8 blocks (std < 1.5) in the far band ≤ 40 % | skyline-perch-nm: far shore 6.15 vs sky 0.50 (12×), flat 13 %; skyline-perch-dn: far city 4.09 vs 0.51 (8×), far shore 3.48 (7×), flat 28–39 %; skyline-queens-aerial far Manhattan 25.9 vs 0.74, flat 9 % |
| C12 | Far-shore colour: **B−R within ±10 of the sky band's B−R** (takes the time-of-day tint); not a fixed warm-neutral | dn: far shore +15.4 vs sky +15.6; nm: −46.3 vs −37.2. (r05 "R,B within ±10" is contradicted by dn: +15 blue) |
| C13 | Far-shore mean Y **25–35 below the sky band** and above the near city; never the brightest band in frame | dn −26.6 (101 vs 127), nm −32.0 (87 vs 119); near city 38–53 |
| C14 | River band darker than the far shore: river Y 5–35 below far shore | nm 81 vs 87, dn 69 vs 101 |
| C15 | Aerial contrast falloff: RMS contrast far/near **0.25–0.45** | nm near .654 → mid .447 → far .182 → horizon .074 (0.28); dn near .310 → far .125 (0.40) |
| C16 | Shore embankment strip vs water luma | **unmeasurable in this pass** (strip not isolated); r05's test stays provisional until measured |
Checker `farfield_check.py`: depth-masked capture of S4/S8 (sky mask, depth > 1500 m band, water mask); report C11–C15.

## 5. Landmarks and IP (C-D)
- Times Square facade emissive coverage: **unmeasured in this pass** (r04's "> 80 %" is a critic estimate, not a spec line).
- No ref-game brand text or near-copies (r03–r05 flags: "FROSTED HALOS", "BOTANICA", "Hotel Mira", "HAUTE UNLIMITED", COLEXCO-like). Checker:
  `ip_text_check.py` = OCR of every billboard texture vs a denylist built from ref OCR; any hit = axis C-D capped at 3.

## 6. Axis → spec lines
| axis | lines |
|---|---|
| C-A Facade & building fidelity | C1, C2, C3 |
| C-B Street-level dressing | C4 (props/parked cars share), C7, C8 checklist |
| C-C Rooftops & skyline | C9, C11, C13, C14, C15 |
| C-D Composition / Manhattan | C6, C12, §5 |
| C-E Image quality | C1 (clipping), C11 flat-block rule, no missing materials (any untextured mesh in frame = defect) |
Critic rules: score against these lines; ADD observed gaps with file@coords; do not contradict a line unless the named tool run on the ref
shows the ref violates it. A capture framed to hide an unbuilt area is judged as if it were in view.

## 7. Round-gap tests added by the builder (r10-r11; instruments in `tools/export/`, boxes at 1920x1080)
| id | test | instrument |
|---|---|---|
| T1 | S4 silhouette-top std over x 0-1300 >= 12 px (far skyline is not a flat plateau) | `s4_far_check.py` (3 definitions) |
| T2 | S4 box (0,150,1300,300): <= 10 % of pixels above Y 204 | `s4_far_check.py`, `city_spec_check.py` crit box `s4_far_band` |
| T4 | S4 box (540,110,900,260): 8x8 blocks with mean Y > 200 and std < 3 ('flat bright blocks'): <= 10 % (reported both as share of the bright blocks and of all blocks) | `s4_far_check.py` |
| T5 | S8 glass box (1270,0,1640,300): <= 1.5 % of pixels above Y 204 (C1 on the upper tower glass) | `city_spec_check.py` crit box `s8_glass_upper` |
| T6 | S3 rooftop board: the caption reads in full in a native-4K crop, and no partial crop of it resembles a real brand name or logo (visual + `ip_ocr_check.py`) | native-4K S3 frame, `builder_checks/billboard_*.png` |
C11-C15 are measured on the S4 frame with the boxes of `spec_regions.json` (far_shore (450,192,1350,236), sky (0,0,1650,80), river (720,298,1000,338), near_city (0,750,500,1000)); a critic who uses
other boxes (e.g. far (0,150,1300,215) for C13) gets other numbers: C13 is the most box-dependent line.

# Critic W r03: water, island-wide (blind)

Homage fan game. Not an official Marvel, Sony or Insomniac game.

Method: luma Rec.709; hp = Y − gauss σ8; glint = Y≥200 and hp≥30. Near crop 4K x0–1800 y1200–2160. Dollies at 4 fps. SPEC.md is absent, so the gates are the PLAN §4 lines.

## A/B (decided before identity)
- **river-sun A:** glints in 100 % of columns, vs 47 %.
- **river-low B:** churn, hp 18.7, vs 9.7.
- **harbour-high A:** hp 33, vs 3.8 with no glints.
- **perch-s4 B:** A's river is a beige band, Y 132 vs 73.
- **still B:** no streaks, but the seawall foam is lost.
- **harbour B:** no blob decals; both flat (hp 3.8 vs 4.1).
- **dolly B:** no streaks; dT 7.9 vs 6.2.
- **sun-dolly A:** more glints; B shows streak arcs.

The reference wins all four ref-vs-ours pairs.

## Scores
1. **Motion & detail: 4.** Near hp 10.1 (ref 18.7). Harbour hp 4.3 (ref 33): a uniform leather texture. No rings (ac80 0.013).
2. **Colour & depth: 5.** Near Y 76, p1 36, p99.5 117 (ref 22–151). The S4 river is a haze band at Y 132.
3. **Reflections & glints: 5.** river-sun: glints 1.61 %, Y≥200 in 41 % of columns (ref 100 %); they are soft blobs. river-low and harbour: 0 %.
4. **Shore & pier foam: 2. REGRESSION.** The `_seawall_foam` crop shows no foam or contact band. The pile and harbour foam are gone.
5. **Horizon & believability: 4.** The sun view is believable. The harbour and S4 are brown haze from swing height.

## Plan §4
| Line | Result |
|---|---|
| hp ≥ 12 | FAIL 10.1 |
| p99.5 ≥ 150 | FAIL 117 |
| glints ≥ 1 % | FAIL near 0 % (sun 1.61 %) |
| Y ≤ 80 | PASS 76 |
| C14 | not re-measured |
| autocorr ≤ 0.10 | PASS |
| piling foam | FAIL |
| ≤ 2.5 ms | FAIL river-low passes 2.66 ms; S4 1.38 and sun 2.19 pass |

## Biggest gap
Far, high-view water has no glints or structure. Keep a sharp GGX sun lobe (roughness ≤ 0.08) and a normal layer beyond 300 m.

Pass when the harbour_high_4k crop (x0–2400, y1300–2160) shows:
- hp ≥ 10
- glints ≥ 0.5 %
- Y≥200 in ≥ 50 % of columns

## Secondary
1. Restore animated contact foam on the seawall, piles and harbour shore. Target: a band ≥ 12 px at Y ≥ 180 that changes per frame.
2. Make the sun glints sharp (≤ 6 px) and cover ≥ 50 % of columns.
3. S4 river: mean Y ≤ 100.
4. Brand flag: the "AMBROCHE" billboard is still in S4.

## Verdict
**FAILS TARGET.** Lowest axis 2; mean 4.0, flat vs r02.

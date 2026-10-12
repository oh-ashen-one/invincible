# Critic W r02: water, island-wide (blind)

Homage fan game. Not an official Marvel, Sony or Insomniac game.

Method: 4K stills; dollies at 4 fps (40 frames). Luma Rec.709. Near crop = x0–1500, y1150–1800 at 3226 px wide. Refs: `river-pier-golden`, `waterfront-perch-trailer`, `waterfront-og`.

## A/B (decided before identity)
- **river-sun: A.** White sparkles across 61 % of the frame width. B: a soft gold smear over 30 %.
- **river-low: A.** Churn and contact foam. B: flat water with pale comet streaks.
- **harbour-high: B.** hp sd 31, 14 % glints. A: hp sd 4.1, 0 % glints, 106 blob decals.
- **perch-s4: B.** A's river is a flat haze band (hp sd 2.7).
- **prev/this still: A.** Seawall foam; hp sd 7.5 vs 3.9.
- **prev/this dolly: B.** A has rings at f25 (autocorrelation 0.294 at 80 px); B peaks at 0.047.
- **sun-dolly: B.** B moves: dT 23.4 vs 2.8.

The reference wins all four ref-vs-ours pairs. This build beats the previous one in all three prev/this pairs.

## Scores
1. **Motion & detail: 4.** The rings are gone. Near hp sd is 7.5 (ref 16.9). Streaks are up to 417×73 px and +37 Y.
2. **Colour & depth: 5.** Mean Y 79.3, rgb (86,79,61). S4 is about 24 Y below the far shore. Range is p1 46 to p99.5 122 (ref 8–162).
3. **Reflections & glints: 4.** river-low has 0 % glints. Harbour has 0 % (ref 14 %). The sun path is a smeared sheen 30 % wide. Tree SSR is fine.
4. **Shore & pier foam: 4.** The seawall foam is new (21 px wide, Y 227). Far-pier foam is flat static wedges. The harbour seawalls have no foam.
5. **Horizon & believability: 3.** From swing height the water reads as brown haze with blob decals.

## Plan §4 Water
| Line | Result |
|---|---|
| hp sd ≥ 12 | FAIL |
| p99.5 ≥ 150 | FAIL |
| glints ≥ 1 % | FAIL |
| mean Y ≤ 80 | PASS |
| C14 | PASS |
| autocorrelation ≤ 0.10 | PASS |
| piling foam | PASS (street level only) |
| ≤ 2.5 ms | FAIL (water passes cost 4.55 ms; frame delta 1.23 ms) |

## Biggest gap
Add a high-frequency normal layer (wavelength 0.15–0.5 m, scrolling in two directions) with a sharp GGX sun lobe (roughness ≤ 0.08). Remove the streak and blob decals.

Pass when:
- river-low near crop: hp sd ≥ 12, p99.5 ≥ 150, glints ≥ 1 %.
- harbour 4K crop (x0–2400, y1300–2100): hp sd ≥ 10, glints ≥ 2 %.
- river_sun: Y ≥ 200 across ≥ 50 % of the frame width.

## Secondary
1. Add contact foam and a darker band where water meets the harbour and S4 seawalls. Animate and break up the far-pier wedges.
2. Bring the water passes to ≤ 2.5 ms (SingleLayerWater alone is 3.68 ms).
3. Deepen the troughs: p1 ≤ 25.
4. Brand flag: the "AMBROCHE" billboard face in S4 needs an IP check.

## Verdict
**FAILS TARGET.** Lowest axis 3; mean 4.0, up from 3.8.

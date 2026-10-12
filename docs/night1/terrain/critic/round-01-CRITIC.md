# Terrain (E) round 1: critic verdict

Homage fan game. Not official Marvel, Sony or Insomniac; no affiliation. Axes are SPEC E5. There was no earlier verdict.

**Scores**
- **Lawn / ground cover: 3.** The lawn is khaki. G/R is 0.81 to 0.92 on five crops against 1.14 to 1.17 on the reference; saturation is 0.41 to 0.58 against 0.63 to 0.89. E1 fails (high-pass SD 4.62 on p9, 4.84 on p4). E2 fails (89.90 %).
- **Paths + water edges: 4.** The p2 Reservoir works (water, reflections, fence). Paths are thin ribbons. The p3 pond-bank rocks are white plastic lumps.
- **Shoreline: 3.** No frame shows a continuous shore. A building covers about 63 % of p6's width and about 70 % of p7's. The p8 pier shed is untextured. E3 rests only on a JSON audit with 195 patch blocks. The progress-west-shore pair is identical (0.002 % of pixels differ).
- **Trees / canopy: 2.** Crowns are flat-shaded green hulls. Crown high-pass SD is 3.3 to 6.5 against 8.9 to 20.4 on the reference. In p3 the camera is inside a crown.
- **Overall beautiful terrain: 3.** Only the p9 panorama reads well. In t5 at 13 to 15 s the swing reaches flat grey ground (SD 1.6 to 2.0, saturation 0.20), which E4 forbids.

**A/B (decided before guessing identity)**
- B is better on south-high, reservoir, pond-woods, great-lawn, shore-west, shore-east and piers.
- A is better on lawn-eye.
- Progress: south B, reservoir B, lawn-eye A. West-shore is a tie (identical images).
- reservoir/B and great-lawn/B are the same file with no Reservoir in it, so that pair needs a fix.

**Biggest gap.** Replace the hull crowns with foliage that has real leaf breakup, such as the browser tree models.

Test on p1_south 4K: every 150 px crown crop must have high-pass SD (σ3) of at least 9, with no flat hull face wider than 40 px.

**Secondary**
1. Lawn: G/R ≥ 1.05, saturation ≥ 0.55, E1 ≥ 8.
2. Perimeter ground in t5 at 13 to 15 s: high-pass SD ≥ 5 at 1080p.
3. Shore shots: show the waterline across at least 50 % of the frame with nothing occluding it, and texture the pier sheds.
4. Remove the dark lawn slabs (luma 58 against 131 for the lawn, about 150 × 88 px, t4 at 9 to 13 s).

**Brand flag.** The hero's spider emblem is visible in t4 and t5. It is outside this piece.

**Verdict: FAILS TARGET.** The lowest score is 2.

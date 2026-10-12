# P2 hero skins, round 16: blind critic (Opus 5.5)
Homage fan game, not affiliated with Marvel, Sony or Insomniac. Coordinates are native 4K pixels.

## Scores (r14: 6, 5, 5, 5, 5)
- **Hero model & suit: 6.** CH1 is met (0.545–0.547H on all 8 suits).
  - Back colour-bleed is fixed; only tonal marks remain.
  - Lenses are still flat, the cloth is matte, and the cheek-cord ends are raw.
- **Hero animation: 5.** The pawn run is still **4.07 Hz** (head peaks every 14–15 frames; CH6 fail).
  - New yaw snap at **9.933 s**: diff 15.5 against 3.4 for its neighbours (CH10 fail).
  - The start ramp holds. The side run is about 3.3 steps/s.
- **Enemies: 4 (regression).** Copper blotches cover every garment in both lineups, silhouettes have halos, and there are ghost bats at (1770,1040) and (2860,1080).
  - 17% of pixels differ by more than 20 luma from the previous clean lineup.
- **Civilians: 5.** The cut at 7.483 s is still there (diff 56.7 against 1.4).
- **Image quality: 4.** The lineup corruption, plus:
  - Ash sash edge: a 34 px shelf jog (x 2340–2420).
  - Ash sash corner: the stitching gaps.
  - Verdant chest groove: a 9 px step (around x 2380).
  - Cinder chin: the seam breaks and jogs about 120 px.

## IP gate: PASS (8/8)
- No spider glyph, web, teardrop lens, red/blue blocking or text.
- **Watch Verdant:** green with yellow limb blocks, yellow rims and crown stripes. That nears a known green-and-yellow vigilante wetsuit.

## A/B (decided blind)
- **Backs:** the tonal side wins (ash A, cinder B, plum A, saffron B, tessera A, verdant B, r15-tessera B). Glacier and sage are ties.
- **Chests:** ash B, cinder B, verdant B and r15-verdant B win (bounded panels). Tessera A wins.
- **Heads:** headfront-cinder B and r15-headfront-cinder B win (straighter seam). The rest are ties.
- **Lineup:** A wins; B is blotched.
- **Ref-vs-ours:** ref wins every pair.

## Single biggest gap
Remove the enemy blotch overlay and halos, and capture after warm-up with no ghosting.

**Test:** at the same camera, enemy_lineup_4k.jpg differs from the previous clean lineup by more than 20 luma in no more than 2% of pixels, and shows no duplicate weapon.

## Secondary
1. Retime the pawn run to 3.2–3.8 Hz, and blend the 9.933 s turn over at least 0.15 s.
2. Every 40 px run of a sash or groove edge stays within 4 px of its line.
3. Join the face seam through the chin, and finish the cord ends.
4. Fix the crowd cut, and de-risk Verdant.

## Verdict: **FAILS TARGET**
Lowest axis: 4.

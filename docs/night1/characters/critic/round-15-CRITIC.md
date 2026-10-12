# P2 hero skins, round 15: blind critic (Opus 5.5)
Homage fan game, not affiliated with Marvel, Sony or Insomniac. Coordinates are native 4K pixels.

## Scores
- **Hero model & suit: 6.** CH1 met (0.544–0.548H across 8 suits). CH2 met (chase median 0.451H).
  - Verdant profile: the rim now sits 40 px behind the brow (2300 against 2342; it was 18 px proud in r14). The nose notch is 72 px.
  - Still flat lens fills, matte cloth, and cheek cords that read as tear-tracks.
- **Hero animation: 5.** The pawn start is fixed: it begins at f43 (0.717 s) and diffs ramp 1.0, 2.1, 2.3, 3.3, so CH10 passes.
  - The pawn bob is still **4.07 Hz** (a peak every 15 frames), so CH6 fails.
  - The scripted side run is 3.48 steps/s, which is OK.
- **Enemies: 5.** The lineup is unchanged from r14 (only 0.003% of pixels differ by more than 20 luma). The twin heads in slots 1/6 and 2/7 remain.
- **Civilians: 5.** The hard cut is still at f449 (7.483 s, diff 55.7 against a median of 2.3).
- **Image quality: 5.** The Ash sash ends are now corded. New defects:
  - a 20 px stair-step groove jog at the Verdant armpit (around 1300,1310);
  - an Ash notch with a smear (around 1480,1170);
  - the Cinder centre seam zig-zags about 60 px;
  - the front emblem and sash repeat on the Tessera and Plum backs, as if projected through the torso.

## IP gate: PASS (8/8)
- No spider glyph, web, teardrop lens, red/blue or black/red blocking, or text. The lenses are horizontal ovals.
- Watch: Verdant's green with yellow limb bands drifts toward a known non-Marvel vigilante costume.
- Watch: Cinder's black with cyan lines drifts toward a light-suit look.

## A/B (decided blind)
- **Profiles:** verdant A, tessera A and ash A win; the rim is behind the brow.
- **Heads:** cinder B wins (straighter seam, deeper cheeks). Tessera B wins marginally. Sage A wins (clean trapezius).
- **Chests:** ash A wins (grooves end on cords). Verdant B wins, because A has stair-steps. Cinder B wins, because A has stray groove stubs.
- **swap-pawn:** A wins. B pops at f7 (12.8 against 5.4/4.8).
- **lineup:** tie (diff 0.68).
- **All ref-vs-ours pairs:** ref wins (gloss, micro-weave, raised web, dressed street).

## Single biggest gap
Retime the playable pawn run to 3.2–3.8 steps/s, which is a bob peak every 16–19 frames at 60 fps. Keep the new start ramp.

**Test:** in swap_pawn_T_key.mp4, the head-top FFT over 1.5–11 s gives 3.2–3.8 Hz, and no 0–1.5 s frame diff exceeds 2× its neighbours.

## Secondary
1. Remove the stair-step jogs where groove cords meet panel borders (Verdant armpit, Ash and Cinder left chest).
2. Keep the face centre seam within 10 px of lateral deviation per 100 px.
3. Back stills must show no chest emblem bleed.
4. Make the enemy twin heads distinct, and remove the crowd cut at 7.483 s.

## Verdict: **FAILS TARGET**
Lowest axis: 5.

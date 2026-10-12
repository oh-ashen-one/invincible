# P2 hero skins, round 11: blind critic (Opus 5.5)

Homage fan game, not affiliated with Marvel, Sony or Insomniac. Coordinates are 4K stills unless marked; clips are 1080p60.

## Scores
- **Hero model & suit: 5.** Eight original stitched designs with visible weave, but line work is flat print with no raised piping. Heads are unsculpted eggs sharing one decal grille. CH1 fails: all front stills span y 278–1939, which is 0.77H (target 0.48–0.62). Ref: suits-duo-closeup.
- **Hero animation: 4.** CH7 is met at about 29° (`persist_start`). CH6 fails: head-bob minima in `swap_pawn_T_key` repeat every 14.7 frames, which is **4.09 steps/s**. CH10 fails: idle pops to mid-stride in 1 frame (0.733→0.750 s).
- **Enemies: 0.** Unproven: no capture this round (CRITIC_GUIDE rule 3).
- **Civilians: 0.** Unproven: no capture this round.
- **Image quality: 5.** CH5 is met for stills (3840×2160). Suit swaps are clean one-frame cuts (frames 85, 157, 229…). CH18 fails:
  - Net lines show through the sashes. Tessera (1412,1240) reads luma 89 against a sash median of 135; Ash shows the same fault.
  - Faceted polygon shading appears on Ash (1330–1480, 1330–1750) and Tessera (1430–1500, 1330–1440).
  - The Verdant chevron edge jogs 24 px at (1333–1357, 1610–1680).

## IP gate: PASS
- No suit has a spider glyph, a radial web, rimmed teardrop lenses, or official colour blocking.
- Tessera, Plum, Cinder, Glacier, Ash, Sage: no resemblance.
- Watch Verdant (a green front with black raglans and a chest ring evokes a famous green ring-hero).
- Watch Saffron (its tan/dark-brown raglan blocking echoes a clawed hero's brown suit).
- Brand check: no copied logo or text in our frames.

## A/B decisions
- **Ref vs ours:** the ref wins every ref-vs-ours pair (full ×4, back ×4, chest ×3, head ×2, swatch, swap, orbit). Ours is matte vector art on a blank plane; the ref has specular micro-weave and raised lines.
- **Swatch:** ours wins only on variety.
- **Orbit:** ours is sharp, with no stray objects in 46 frames.
- **progress-tessera: B.** It has crisper stitching and emblem; A is softer.

## Single biggest gap
Make the panel and net lines real raised piping, layered under the sash and chevron panels. Test at the 4K chest view:
- Every line shows a lit/shadow edge pair with luma difference ≥20.
- No run of pixels longer than 10 px inside any sash or chevron is darker than the panel median −15 (Tessera and Ash now fail this).

## Secondary issues
1. Blend idle→run over ≥0.15 s. Bring the run to 3.2–3.8 steps/s (CH6, CH10).
2. Remove the faceted shading blotches (smooth the normals or fix the shadow bias).
3. Fix the Verdant chevron UV jog and the stitches that do not line up across it.
4. Sculpt the head. Capture a CH1-framed street view, plus enemies and civilians.

## Verdict: **FAILS TARGET**
Lowest axis: 0 (enemies and civilians unproven). Lowest scored axis: 4.

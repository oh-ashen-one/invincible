# P2 hero skins, round 12: blind critic (Opus 5.5)

Homage fan game, not affiliated with Marvel, Sony or Insomniac. Stills are 4K; clips are 1080p60. Coordinates are in native pixels.

## Scores
- **Hero model & suit: 5.**
  - Met: CH1, front stills 0.544–0.547H. CH2, chase median 0.46.
  - Met: lines are now raised grooves (Tessera y=700: 17–43 against a lip of 65–74).
  - Failed: heads are unsculpted socks with small rimless lenses. Ref: suits-duo-closeup.
- **Hero animation: 5.**
  - Met: CH7, about 21° lean (hero_run_side @2.0 s; ref ≈30°).
  - Met: CH10, idle→run blends over frames 45–60.
  - Failed: CH6 on the playable pawn. swap_pawn_T_key bobs at 4.08 steps/s (minima at frames 87/101/117/131). Scripted runs are 3.5 steps/s.
- **Enemies: 4.**
  - Met: three weapon types.
  - Failed: lineup has 6 enemies (7 needed). The crowbar passes through the fingers at (1960,1100). Lighting is washed out.
  - Fight: enemies clump within 1 m, attack at once and get no hit FX.
- **Civilians: 5.**
  - Met: 13 people and at least 9 models (crowd_tracking @3.25 s). Legs animate.
  - Failed: rigid robe and coats, and a hard cut at 7.5 s.
- **Image quality: 5.**
  - Fixed: sash show-through and the Verdant apex.
  - Failed:
    - Unpiped sash ends: Ash (1410–1440, 700–1050) and Tessera.
    - Ash armpit stitch smear at (1150–1200, 1530–1600).
    - A 12 px black kinked face/neck seam on every suit.
    - Cinder's emblem is cyan on a cyan sash.

## IP gate: PASS
- No spider glyph, web, teardrop lenses, red/blue or black/white blocking, or brand text.
- Tessera, Cinder, Glacier, Ash, Sage: no resemblance.
- Verdant: ring removed. Pass.
- Saffron: brown raglans removed. Pass.
- Watch Plum's purple+mint palette.

## A/B decisions
- **All 20 ref pairs: the ref wins.** The ref has gloss, micro-weave, sculpted lenses, a dressed street and FX. Ours has blank planes, matte suits and no FX.
- **progress-tessera: A.** In B, net lines show through the sash and its end is smeared. A is probably round 12.

## Single biggest gap
Sculpt the mask head:
- brow, nose bridge, cheek and chin relief;
- lenses at least 1.6× wider, with a raised dark rim at least 6 px wide at 4K;
- the face seam as raised piping, not ink.

**Test:** the 4K head still's luma through the nose bridge shows at least 3 extrema with a swing of at least 20. The profile silhouette has a nose bump of at least 2% of head height.

## Secondary issues
1. Bring the playable pawn to 3.2–3.8 steps/s.
2. Pipe every sash end. Fix the Ash armpit smear and Cinder's emblem.
3. Line up at least 7 enemies with gripped weapons. In fights, space them at least 1.5 m apart and have them attack in turns.
4. Add cloth motion to coats and robes. Remove the 7.5 s crowd cut.

## Verdict: **FAILS TARGET**
Lowest axis: 4 (enemies).

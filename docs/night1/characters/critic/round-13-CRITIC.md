# P2 hero skins, round 13: blind critic (Opus 5.5)
Homage fan game, not affiliated with Marvel, Sony or Insomniac. Coordinates in native pixels.

## Scores
- **Hero model & suit: 6.**
  - Met: CH1, fronts 0.545–0.547H. CH2, chase heights 0.41–0.47.
  - Lenses are bigger with a chrome rim. The Verdant profile's nose sits 110 px (7.4% of head height) proud of the brow–chin line.
  - Failed: no brow ridge, no nose-bridge recess (the profile edge rises from y=860 to 1140) and no cheekbones or mouth.
- **Hero animation: 5.**
  - Met: CH7, about 23° lean. Scripted runs are 3.53 steps/s.
  - Failed: CH6 on the playable pawn, 4.07 steps/s.
  - The start pops between frames 7 and 8.
- **Enemies: 5.**
  - Met: lineup has 7 enemies with three weapon types. CH12, fight heights 0.28–0.43.
  - Failed: two pairs of twin heads. The pistol sits in open fingers at (2000,1100).
  - Fight: enemies stay within about 1 m, overlap the hero and get no hit FX.
- **Civilians: 5.** Unchanged: rigid robe and coat. Hard cut at frame 449 (7.483 s).
- **Image quality: 5.** Defects:
  - The Ash sash end is raw (1410–1440, 700–1050).
  - The Ash armpit stitches zigzag (1120–1200, 1530–1600).
  - The Sage trapezius groove is torn (head34).
  - Cinder's shoulders are faceted.

## IP gate: PASS
- No spider glyph, web, teardrop lenses, red/blue or red-on-black blocking, or brand text, checked by eye.
- No resemblance: Tessera, Cinder, Glacier, Ash, Saffron, Sage, Plum.
- Verdant's green+yellow is generic with no emblem. Watch it.

## A/B decisions
- **25 ref-vs-ours pairs: the ref wins every one.** The ref has gloss, micro-weave, sculpted brows and hit FX. Ours is matte.
- **progress-head-tessera and progress-head-sage: A.** A has a nose, bigger rimmed lenses and coloured piping instead of an ink seam.
- **progress-lineup: A.** A has 7 enemies against 6. B is washed out (mean luma 161 against 91).

## Single biggest gap
Finish the mask sculpt with:
- a brow ridge overhanging the lenses;
- a nose-bridge recess;
- cheekbone planes;
- a mouth bulge and a chin plane.

**Test:**
- The 4K headside profile edge has a recess between brow and nose tip at least 1.5% of head height deep.
- The brow protrudes at least 1% past the top of the lens.
- On the 4K Tessera and Cinder front stills, a luma line through the cheekbones shows at least 3 extrema with a swing of at least 20.

## Secondary issues
1. Bring the pawn to 3.2–3.8 steps/s and remove the pop at frames 7–8.
2. Pipe the Ash sash end and fix the armpit and Sage trapezius.
3. Give the twin enemies distinct heads and close fingers on the grips. In fights, space enemies at least 1.5 m apart, have them attack in turns and add hit FX.
4. Remove the crowd cut at 7.48 s.

## Verdict: **FAILS TARGET**
Lowest axis: 5.

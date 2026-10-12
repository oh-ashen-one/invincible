# P2 hero skins, round 14: blind critic (Opus 5.5)
Homage fan game, not affiliated with Marvel, Sony or Insomniac. Coordinates are native 4K pixels.

## Scores
- **Hero model & suit: 6.** CH1 met (0.545–0.547H). CH2 met (chase 0.41H).
  - The Verdant profile now has a brow, a nose-bridge notch (43 px, 2.8% of the head, at y=880), a nose, lips and a chin.
  - Fail: the lens rim sits 18 px proud of the brow (2273 against 2255), so the brow does not overhang the lens.
  - The suit is matte, and the face cords read as tear-tracks.
- **Hero animation: 5.** Scripted runs are 3.59 steps/s, but the pawn runs at 4.13 (CH6 fail).
  - Pose pop between frames 7 and 8 (diff 9.5 against 3–4).
  - The run start completes in about 3 frames at 0.73 s (CH10 fail).
- **Enemies: 5.** Compared with r8, the fight thugs now swarm into the hero (they overlap at 3 s) instead of spacing out, and there are no hit FX. Knockdowns are new.
  - Lineup: the twin heads remain (slots 1/6 and 2/7), the pistol sits by open fingers, and the brute's sleeve texture smears onto his hand.
- **Civilians: 5.** Same as r8. The robe and coat are rigid, and the hard cut is still there at frame 449 (7.483 s).
- **Image quality: 5.** The sash ends and the Sage trapezius are fixed. New defects:
  - a lime cord floats 40 px off the Ash sash end (1490–1540, 760–1150);
  - the grooves stop dead;
  - the texture is stretched under the brow;
  - the Verdant armpit piping is pinched (1160–1270, 1150–1270).

## IP gate: PASS
- No spider glyph, web, teardrop lens, red/blue or black/white blocking, or text on any of the 8 suits.
- Saffron (gold lines) and Cinder (cyan rhombus) match no known suit or shield. Verdant is a generic green/yellow; watch it.

## A/B (decided before checking identity)
- **Cord version wins** in progress-head-tessera (A), verdant-profile (B), head-cinder (B) and head-sage (B). It has a nose, cheeks, a mouth and a clean trapezius.
- **chest-ash B and chest-cinder B:** piped ends.
- **progress-lineup: tie.** The only difference is the finger pose; luma is 91.9 against 91.5.
- **All 29 ref-vs-ours pairs: ref wins.** The ref has gloss, micro-weave, raised webbing, hit sparks and a dressed street.

## Single biggest gap
Fix the playable pawn's run:
- Retime it to 3.2–3.8 steps/s.
- Blend the spawn pose and idle→run over at least 0.15 s.

**Test:** in swap_pawn_T_key.mp4:
- the head-top bob FFT gives 3.2–3.8 Hz;
- no frame diff exceeds 2× its neighbours in 0–1.5 s.

## Secondary
1. Recess the lens rims at least 1% of head height behind the brow.
2. Attach the Ash cord, and end the grooves at seams.
3. Space fight enemies at least 1.5 m apart, have them attack in turns and add hit FX. Close the grips and make the twin heads distinct.
4. Remove the crowd cut at 7.48 s.

## Verdict: **FAILS TARGET**
Lowest axis: 5.

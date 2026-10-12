# P5 Combat r03: critic (pixels only)

> Homage fan game. It is not an official Marvel, Sony or Insomniac game and has no affiliation with them.

Ours: `round-03/fight30_1080p60.mp4`, stills and hit strips. Refs: `refs/combat/clips/*`. Diffs are mean gray at 480x270.

## Scores
1. **Impact: 5** (r02: 4). The global freeze is fixed: 0.2% frozen frames, and the median whole-frame diff in a hold is 1.31. There are 33 flares of 8 frames each, peak about 1% (CB3 met), but each one is an opaque orange disc that hides the victim for the whole hold (hit_008.18, still_07 @15.65). The victim stays upright @14.30-14.48.
2. **Move set: 5.** The launcher, air hit and slam read (@6.9-7.5), and the finisher throws its victim far (@15.6-16.0). The hero passes through the victim @14.35-14.40. The finisher has no cut and no slow-mo (CB10).
3. **Enemies: 5.** Clothing varies, 8-12 enemies are in frame with telegraphs, and downed enemies stay down. They still clump, and 6 of 7 share the same hands-at-face guard (web-still A).
4. **Camera: 4.** From 0 to 4 s the eye-level backlit shot is unchanged: 20-27% of pixels are below 30, vs 12.7% @20 s. There is a snap of 28.9 @14.42 at 60 fps, over the CB9 limit of 25. The hero is 19-31% of frame height, vs about 40% in the ref hit-moments.
5. **Spectacle: 4.** The street is flat and untextured, with no environment hits, no blur and a single FX shape. Motion matches the refs (median 11.6 vs 8.3-17.2).

## A/B
I chose the reference in every pair: street-combo B, street-fight-2 B, plaza A, night A, hit-moments B, finisher B, contact B, group A, air A, web B. The refs have environment slams, blur, cinematic beats and readable swirl FX. In prev-vs-now I chose **A**: it has flares and flung bodies, while B has no FX. I guess A is r03.

## Biggest gap
**Replace the opaque disc with an additive burst that keeps the victim readable, and make every blow move the victim.**
- The flare is 4-8 radial streaks at least 8% of frame width, with 35% fill or less inside its bounding circle.
- Across contact frames 1-5, the victim box keeps at least 60% of its pre-contact Sobel energy.
- Test on all 33 blows: the victim stays visible, and it moves at least 0.5 m or rotates at least 30° (CB2).

## Secondary
1. Replace the 0-4 s opening with the combat cam: pitched 15-25° down, 15% or fewer dark pixels.
2. Fix the snap @14.42 and the pass-through @14.35.
3. Add a finisher beat: a close-up cut of 1 s or more at 0.3x slow-mo.
4. **Brand:** the white spider emblem on the chest and back is still copied (@15.65, @3.0).

## Verdict: **FAILS TARGET** (lowest 4)

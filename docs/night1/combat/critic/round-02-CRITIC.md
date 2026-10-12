# P5 Combat r02: critic (pixels only)

> Homage fan game. It is not an official Marvel, Sony or Insomniac game and has no affiliation with them.

Ours: `round-02/fight30_1080p60.mp4`. Refs: `refs/combat/clips/*`. Diffs are mean gray at 480x270, with both ours and the refs at 30 fps.

## Scores
1. **Impact: 4.** There are 39 hit-stops of 4-6 frames each, and each one freezes the whole frame, camera included (diff about 11 → 0.1 → 11 @3.63 and @13.40). Frozen frames are 7.3% of ours vs 0.3-2.7% in the refs, so it reads as stutter. The sparks are 2-px ticks. The victim @13.25-13.65 barely moves over 24 frames.
2. **Move set: 4.** An enemy holds a **T-pose** @2.67-2.83. The hero passes through enemies @14.06, @22.0 and @25.9. The web-pin splats are flat white discs (@22.0). The finisher has no cut and no slow-mo (CB10).
3. **Enemies: 5.** About 8-10 enemies are in frame, with `!` markers and aim lines (CB5 met). They clump into one knot and share one hands-at-face guard pose.
4. **Camera: 4.** From 0 to 3 s the camera is at eye level, backlit and rolled: pixels below 30 cover 26-34% of the frame (@1.5, @2.3). The hero's hands touch the top edge @14.06, which fails CB7. There are unblurred whips @14.08 (35.0) and @21.55 (32.7, a lamp pole sweeping the foreground).
5. **Spectacle: 4.** The motion level matches the refs (median 11.9 vs 8.3-17.2), but the street is flat and empty, with no environment use, tiny FX and no blur.

## A/B
In every pair I chose the reference. It shows environment slams, big flares, cinematic cuts and grounded materials. The side I did not choose looked like ours in each pair: street-combo B, street-fight-2 A, plaza B, night B, finisher B (no beat), and B in all four stills (the web line is about 1 px). In prev-vs-now I chose **A**: it has about 8 enemies with telegraphs, while B is a sparse duel. I guess A is r02.

## Biggest gap
**Hit reaction and impact.** On a hit, freeze only the hero and the victim for 3-5 frames, and keep the camera shaking by 2-4 px. Add a red-orange flare covering 1-3% of the frame, gone by frame 8. The victim rotates at least 30° and moves at least 0.5 m within 0.3 s. Heavy hits launch the victim 2 m or more. Test: the victim-crop diff is below 1.0 for 3 or more frames while the whole-frame diff stays at 1.0 or more, and frozen whole frames are 3% or less.

## Secondary
1. Replace the opening shot: pitch 15-25° down, 0° roll, hero kept 5% or more from every frame edge.
2. Fix the T-pose, and keep the hero from passing through enemies.
3. Add a finisher beat: a close-up cut of 1 s or more plus 0.3x slow-mo.
4. **Brand:** the white spider emblem on the chest and back is copied (@15.3). Replace it.

## Verdict: **FAILS TARGET** (lowest 4)

# Tricks C round 01: blind critic (Claude Opus 5.5)
*Homage fan game. Not official Marvel/Sony/Insomniac.* Evidence: `_scratch/critic-C-r01-work/`.

## Scores [merged r26]
- **Swing 7 [7].** web_on 39.8 %. Longest web-off gap 3.13 s.
- **Camera 7 [7].** 4.50–5.18 m. bbox p90 .326. Hero in frame 100 %.
- **Web 7 [7].** Rope reads at every catch.
- **Moves 6 [6].** No wall-run or perch in the reel. Traversal code unchanged.
- **Body 7 [7].** The tuck is IK-locked at a constant wrist–shin 0.040 m and knee gap 0.160 m.
- **Flips 7 [7].** 22 tricks, 12 programs, readable.
- **FLIPS vs OWNER 5.** Every catch snaps. Pike and pencil are loose. The triple chain is macroblocked.

## SPEC
- **P: PASS.** 12 programs.
- **V1: PASS.** 10/10 pairs, minimum 141 deg/s (program) and 199 deg/s (rendered).
- **V2: PASS.** Scales 0.850–1.131. Rendered timing follows (backPike 0.73 vs 0.95 s).
- **K: PASS.** Holds 0.37–1.28 s. The backSingle tuck is only 0.15 s.
- **L: FAIL.** 4 slow samples (28.5, 38.2, 54.1, 57.6 s).
- **G1: FAIL.** 21 % of 406 Layout samples are below 170°. Knee minimum 73.8° (44.1 s).
- **G2: PASS.** 99.9 %.
- **G3: PASS.** 22/22.
- **G4: PASS.** 22/22. Rendered rate ≤150 deg/s (my recompute).
- **A/B: FAIL.** The reference won 9 of 11.
- **R: PASS.** No axis below r26. Only WebTravFlips.cpp/.h changed.

## A/B (decided before identity)
single-release B, triple B, pike-twist A, inverted-pencil A, short-tuck A, release-wide B, rooftop-wide A, tuck A, layout B, pencil B, straddle A, progress B.

Ours won only single-release and pencil.

## Biggest gap: the catch pops
After the trick ends, the chest rotates at 300–921 deg/s over 0.1 s.
- 16 of 21 catches are ≥400 deg/s.
- 16.45 s peaks at 1894 deg/s per frame.
- Non-trick p95 is 149 deg/s.

**Instruction:** blend toward the rope during the last 0.3 s instead of holding the upright one-arm Reach.
- **Test:** chest-frame rotation from trick end to +0.4 s, in 0.1 s windows.
- **Pass:** ≤250 deg/s on all 22 tricks, with G4 still passing.

## Secondary
1. **Straight lines:**
   - Layout knee ≥170° on every frame.
   - Pencil knee median is 148°; make it ≥170°.
   - Pike hip median is 125°; make it ≤90°, with knee p10 ≥165° (now 105°).
2. **L:** fix the 4 slow samples.
3. **Readability:** the reel is 1.8 Mbps and macroblocks at 27–33 s. Use ≥12 Mbps and light the hero against dark facades.
4. **Variety:** 20 of 22 tricks end in the same Reach. The rudi "Straddle" is a split flail.

## Verdict: FAILS TARGET
Lowest: FLIPS vs owner 5.

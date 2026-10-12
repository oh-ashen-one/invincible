# CRITIC: P1 City r11 (pixels only)
Homage fan game, not affiliated with Marvel/Sony/Insomniac. Work: `_scratch/critic-P1-r11-work/`. No clips, so motion is unproven.

## Scores (r10 → r11)
1. **Facades 5 → 5.** S8 glass is fixed, but milky with no reflections. S5 (640,40,880,700) still fails C1: 6.0 % >204.
2. **Street 5 → 5.** S1 is unchanged (diff 3.3). Cars are toy-like and there are 0 people.
3. **Rooftops/skyline 5 → 5.** S4 far towers now have window grids and setbacks. C13 FAILS: far − sky is −68 (spec box) and −57 (0,150,1300,215). S3 vents are untextured primitives.
4. **Composition 5 → 5.** S6 steps are unchanged: sat 0.32, V 210.
5. **Image quality 5 → 5.** S6 curb (1150,760,1920,1080) is 14.65 % >204, unchanged for 3 rounds. Frames got darker overall (f).

## Checks
- **a** S4 band: 6.6 % >204. PASS (r10 29.5).
- **b** FAIL. Bright-block denominator: 11 of 24 = 45.8 %. All-block denominator: 1.4 %.
- **c** S8 glass: 0.69 % >204. PASS (r10 70.4).
- **d** T1: 22.4 px, PASS. C11 30×, C12 −0.06, C14 23, C15 0.31 pass. **C13 FAILS** (−68 / −57; target −25..−35).
- **e** Partly. Mid ranks read as buildings. The rear rank is flat-topped, pale and featureless.
- **f** Y<25 rose: S3 13.2 → 17.0 %, S7 1.4 → 3.5 %, S8 7.8 → 13.0 %. Still within the r09 limits; trend flagged.
- **g** No axis below r10. PASS.

## A/B
- street-avenue **A**
- swing **B**
- rooftop **B**
- perch **B**
- perch-dn **A**
- skyline-crop **B**
- steps **A**
- plaza-street **A**
- sunset **A**
- aerial **B**
- glass-crop **B**
- board-crop **B**
- progress-perch **B**
- progress-aerial **B**
- progress-rooftop: tie
- other progress pairs: near-identical (diff ≤4.8)

## Single biggest gap
Restore aerial perspective on S4. Do not darken the far towers further. Lower the sky (229; refs 119–127) so the far band sits 25–35 below it, and add window and crown detail to the rear rank.

Tests (1080p S4):
- sky (0,0,1650,80) mean Y ≤205;
- C13 −35..−25 on both (450,192,1350,236) and (0,150,1300,215);
- T2 ≤10 %;
- T4 ≤10 % of bright blocks;
- T1 and C11, C12, C14, C15 still pass.

## Secondary
1. S6 curb ≤1.5 % >204. Steps: sat ≥0.44, V ≤200.
2. S5 C1 ≤1.5 % >204. S8 glass needs environment reflection.
3. Texture the S3 vents.
4. Return S3/S7/S8 Y<25 to r10 levels or lower. P6: 0 people.

## Brand/IP
Visual read: FIZZO, AMBROCHE, VELVET & VINE, OÜR OÜ, COMEDY CLUB. None is on the denylist. Rooftop board excluded by owner ruling.

## Verdict: FAILS TARGET (lowest 5)

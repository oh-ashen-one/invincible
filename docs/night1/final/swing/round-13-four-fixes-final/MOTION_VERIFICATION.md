# Motion verification — completion candidate

Reviewed 2026-10-12 by GPT-6.1 Sol / xhigh against built runtime **19521659**, identified in [BUILD.json](BUILD.json). These are measured motion results, not a complete all-criteria pass or owner gameplay acceptance. The latest full seven-case gate is still running under root/scout ownership. No additional source edits were made after the freeze.

## Rate measurement

The `fw_body_axis_x/y/z`, `fw_body_pitch_deg` and `fw_body_axis_deg` columns are sampled after animation evaluation, same-frame root correction and UpdateWebs. They describe the row actually rendered; no legacy one-row shift is applied. Projected pitch is raw facing-plane atan2, without a sideways-cone hold or rate filter.

The authoritative F3 gate uses approximately **0.04-second readings**, implemented as two frame intervals at fixed 60 Hz (approximately 0.0333 s). Projected rates unwrap that pitch; true 3D rates measure the angle between normalized world-axis vectors over the same interval, using recorded timestamps. These finite-window results do not establish an instantaneous-rate upper bound.

## Latest catch repair probes

Runtime 19521659 completion probes are in `/Users/midir/sm2-r13-fourfix-cache/round-13-four-fixes-completion-probe/s3b_flip_cases/<case>/route_telemetry.csv`. Chest maxima use the unchanged W4 window, attach minus one through attach plus nine frames. All four completed catches meet chest <=400 degrees/s and hand ratio <=2.5.

| Case | Chest maximum, deg/s | Hand-speed ratio | Primary noncatch hold |
| --- | ---: | ---: | --- |
| c1 frontSingle | 349.2 | 1.911 | Throne, 0.4566 s |
| c2 backSingle | 239.9 | 2.075 | Pencil, 0.4067 s |
| c3 corkscrew | 281.7 | 2.102 | Straddle, 0.4900 s |
| c5 frontPikeSwan | 354.0 | 1.910 | Pencil, 0.4733 s |

The repaired c1/c5 chest readings were previously 418.9/431.5; baseline was 378.9/389.3. c2's hand ratio was previously 2.692. Its pre-attach/attach/next-frame anchor errors now read 2.80/0.35/0.47 degrees, replacing 15.93/15.25/0.45. Shoulder-to-hand length was already approximately 0.547 m in both builds: the demonstrated problem was the aiming/root coordinate mismatch. The author-local prediction now aligns those coordinates while current-frame evaluation remains authoritative.

Latest c1/c2 projected F3 peaks are approximately 733/718 degrees/s; both meet F8 at approximately 0.02 s after the trick and 11/28 degrees from upright. The listed holds exclude terminal catches and remain >=0.3 s at <=150 degrees/s. The earlier full seven-case gate passed all primary F3 peaks; that evidence is not relabeled as this newest full replay. Prior native frames established three catch bodies: seated Throne, one-knee-up/one-leg-long Reach, and a straight-leg split. Their authored families remain preserved; independent final pixel review is separate.

## FrontDouble chain

The latest completed chain has 1,439 rows: [telemetry](s3_flip_chain_telemetry.csv), [flip checks](s3_flip_chain_FLIPS.txt), [native movie](s3_flip_chain.mp4).

FrontDouble measures **773.25 degrees/s projected** and **795.97 degrees/s true 3D** on the authoritative two-frame windows, both below 800. The true 3D maximum is at clip 2.0333–2.0667 s, approximately flip 0.117–0.150. The preceding capture measured approximately 817.8 projected/826.7 true 3D. The actual program rate now records 690 at flip 0.133/0.150/0.167/0.183; angle integration and `PitchRate` use the same capped function, preserving 720 degrees and the existing duration/hold times.

**Precision disclosure:** single 60-Hz-frame true 3D reaches **801.8 degrees/s** at clip 2.0333–2.0500, using recorded timestamps. It exceeds 800 under that shorter definition. The two-frame F3 pass must not be described as proof that every shorter interval stays below 800.

FrontDouble's first F5 easing chunk remains below target (2.6 versus >=3; previously 2.8); later chunks read 10.0/6.8. Truncated/cancelled chain programs also remain limited evidence for F4/F5/F8. No complete all-criteria chain pass is claimed.

## BackSingle catch and retained limits

The chain backSingle catches at **14.1500 s**, approximately 0.0167 s after its final trick row, with body **10.4971 degrees from upright** and W4 chest **121.4 degrees/s** (baseline 237.8). Anchor errors before/on/after attach are 2.01/0.225/0.572 degrees: timing, orientation and aim continuity are confirmed.

Its hand ratio still fails at **2.949**; the same baseline catch already failed at **2.892**. Speeds are 3.84→11.33 m/s now versus 3.79→10.97 m/s before. This retained ratio failure is disclosed and is not the repaired approximately 15-degree-to-zero aiming discontinuity.

Late barani still reports approximately **1,136.3 degrees/s projected**, versus **686.1 degrees/s true 3D**. The projected entry reading is amplified near a sideways body-axis orientation in the facing plane; it does not demonstrate a corresponding >800 world-axis turn. The projected failure remains visible. No barani retiming, cone filter, telemetry clamp or threshold change hides it.

## Mathematical verification

`python3 tools/final/swing/flip_math/run.py` extracts current real C++ and the actual root composition. All 416 tempo/jitter variants pass angle/duration/catch scaling, noncatch holds, peaks, lag, axis compensation, centre/sway composition, held-axis prediction and angle-table/rate derivative parity. A capped rate field or forced endpoint cannot hide uncapped integration or lost turns. The paired-entry forecast is explicitly approximate; rendered c7 (~783.9 projected) is decisive. Final capture completeness, independent critique and owner control acceptance remain separate gates.

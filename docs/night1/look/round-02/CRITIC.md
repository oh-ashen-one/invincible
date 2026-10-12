# P4 LOOK critic, round 02 (pixels only; lum.py = lum_by_tod.py method + L13/L14 blob counter)

## Scores (Spider-Man 2 standard)
1. Sun/sky/time of day: 4. Midday fails L2 on 7/8 stills (mean 62–81, only S4 90.7 is inside 83–97). Near-black is 0.46–7.29% against a ≤0.05% limit. B−R fails L7 (S4 +25.8, S8 +13.2, S2 −19.6). Midday is hard sun under a blue sky, where L2 calls for overcast. L11 fails: in midday S4 the horizon is 34.7 Y darker than the zenith (97.8 vs 132.5). Golden means pass L1 on 7/8 (S4 104.8 is high). B−R fails L6 on S2 (−66.7) and S4 (−57.1).
2. GI & shadows: 4. The golden look is a global sepia wash. Shadow sides carry the same orange as the lit sides, with no cool sky fill, and there is no raking sun/shade split in the canyon (pack golden-canyon, swing_golden). Midday crushes blacks (Y<10 up to 7.29% in S7).
3. Atmosphere & depth: 4. L10 fails in S4. Golden: far city sits 39.5 below the sky (target 15–32), with B−R −20 against sky −61 (target ±10). Night: the far shore is 28 Y *brighter* than the sky, at B−R +95 against +55. Far blocks render as flat purple/violet and the embankment as a self-lit white band (S4 3840 crop, y≈400–650). Canyon haze exists but washes to white (golden S7).
4. Reflections & materials: 4. L17 fails: midday S7 left glass p10 is 14.4 (target ≥20). Windows are black holes (golden S2 facade p5 11.8). Midday S2 glass reflects gold at noon. Night wet-asphalt specular in S1/S5 is the best element.
5. Post & exposure: 5. L18 passes (edge/centre p50 0.54/0.61/0.49). Clipping fails: golden S7 2.58% (L5 ≤0.7), S8 2.05% (L1 ≤1.8), midday S3 0.65% and S7 1.24% (L2 0.00).
6. Night look: 5. L3 passes on all 8 (mean 43.9–52.9, Y<10 ≤0.66%). L8 fails on S4 (+26.9) and S8 (+19.8). L13 passes on S1 (9) and S6 (9). L14 fails: S5 p10 11.2 and S6 p90 93.6. The swing clip is day-for-night: facades are fully diffuse-lit and albedo reads as if at dusk. Trees are neon green and the Times Square screens are dead black.

## A/B (judged before identity)
- golden-canyon: A is better (sun/shade split, bounce, bloom, DOF). B is ours.
- golden-skyline: B is better (layered depth, far shore, no clipping). A is ours (2.81% clipped).
- night-street: A is better (sodium pools, varied lit windows). B is ours.
- night-street-2: B is better (warm pools, lit trees, contrast). A is ours.
- night-swing: A is better (dark mass, window-point city). B is ours (day-for-night).
- progress-night: both are ours. A is newer and far better: mean Y 10.0→55.5, Y<10 83.6%→0.15%, blobs 0→12.

## Ranked gaps
1. Build a real overcast midday. Pass means all 8 midday stills reach mean 83–97, Y<10 ≤0.05%, 0.00% clipped, B−R −19…+8, and horizon ≥ zenith +3 Y (S4).
2. Fix far-field shading. The far city must take the sky tint (B−R within ±10 of the sky) and sit 15–32 Y below the sky at all three times of day. No purple proxies and no self-lit white shore band (S4).
3. Make night a night. Kill the diffuse facade ambient so frame B−R stays within ±13 on S4/S8 and the swing clip. Bottom-third p10 must be 15–30 and p90 ≥100 on S5/S6.

## Secondary
- Golden shadows need a cool fill; B−R must be ≥−55 on S2/S4.
- Clipping must be ≤0.7% on sun-facing golden S7.
- Glass p10 must be ≥20 (midday S7), and the noon gold reflection must go.
- Tree foliage under lamps is oversaturated green. Times Square screens are unlit.

## Verdict: FAILS (no axis ≥8)

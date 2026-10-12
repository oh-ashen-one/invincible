# P4 LOOK critic, round 03 (pixels only)

> Homage fan game, not official Marvel/Sony/Insomniac. Instruments: lum.py (lum_by_tod + L13/L14 blobs), Laplacian edge/centre, row profiles (`_scratch/critic-P4-r03-work/`).

## Scores
1. **Sun/sky/ToD: 6.** Midday passes L2/L7 on 8/8 stills (mean 84.9–94.3, B−R −12…+3). Clipping fails: S3 0.03%, S7 0.04%, swing peak 0.45% at t=10.5 s (limit 0.00). Golden fails L1 on S4 (109.7), L5 on S7 (3.02% clipped) and L6 on S3 (−19.6).
2. **GI & shadows: 4.** Golden shadows are lifted and flat: p5 Y 17.6–39.6 (refs 8–11), p95/p5 4.6–11.3 (refs 18–26). No sun/shade split on S1, S5 or S6. The overcast swing shows crisp cast shadows (t≈5–6 s).
3. **Atmosphere & depth: 4.** L10 fails. Golden S4 far band is 35–44 Y below the sky, with B−R −40 against the sky's −76. Midday S4 far band is 43–49 below. The overcast far field is a purple mush. The S7 canyon god-rays are good.
4. **Reflections & materials: 4.** Glass is a flat fill (swing t=8.25 s: Y 24.2, std 0.7). It reflects nothing. The midday S2 tower glows gold. The night wet asphalt is good.
5. **Post & exposure: 5.** L18 fails: edge/centre p50 is 0.69, and ≥1.0 from t=8.0 to 9.5 s (no edge blur). See axis 1 for clipping.
6. **Night look: 5.** L3, L8 and L13 pass on 8/8, and L14 passes on the street views. The skyline is day-for-night: city median Y 58 (ref 37), window points 0.96% (ref 4.38%). The Times Square screens are gradient placeholders. The trees are neon green.

## A/B (decided before identity)
golden-canyon A · golden-skyline A (B is a sepia wash) · golden-sunstreet B (A clips 3.54%) · night-district A · night-skyline B · night-street B (close) · night-street-2 B · overcast-skyline B · overcast-street B · overcast-swing A (B is flat, with hard shadows) · progress-golden A · progress-midday A (no white shore) · progress-night A. Ours: B,B,A,B,A,A,A,A,A,B.

## Biggest gap
Rebuild the golden key/fill contrast. On golden S1–S8 at 1080p, pass means p5 Y ≤12, p95/p5 ≥16 and mean HSV saturation ≥0.44, with L1 still holding (mean 61–100, so S4 must come down; Y<10 ≤8%; clipped ≤1.8%). S1, S5 and S6 must each show a sunlit/shaded facade pair with a luma ratio ≥3.

## Secondary
1. Night S4 needs window points on ≥3% of the frame and city median Y ≤42.
2. L10 on golden S4 and midday S4: far band 15–32 Y below the sky, B−R within ±10 of the sky.
3. Overcast: no crisp sun shadows; 0.00% clipping on S3 and S7.
4. L18 p50 ≤0.65. Glass must reflect (std ≥8).

No copied brands seen.

## Verdict: FAILS TARGET (lowest 4)

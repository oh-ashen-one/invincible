# CRITIC: P1 City r08 (pixels only)
Homage fan game, not affiliated with Marvel/Sony/Insomniac. Coordinates are 1080p. Tools: `_scratch/critic-P1-r08-work/`. S3 and S8 are unchanged since r07 (mean abs diff 0.5 and 1.5).

## Scores
1. **Facades: 5.** S2 passes C2 (116 and 77). S1 still fails C2: mean Y 22.5 at (0,0,480,300) and 19.7 at (1360,0,1740,400), with 88% of pixels below 25. S8 glass at (1270,0,1640,300) still fails C1 with 70.4% of pixels >204.
2. **Street dressing: 5.** C4: S1 has 16 cars (target 5–19). C6: S2 has 17 vehicles. C7 passes with ≥6 trees and 3 + 2 signs. People: 0. The cars are low-poly with blank plates. The shed is flat green.
3. **Rooftops/skyline: 4.** S4 passes C11–C15 (Laplacian 10.4×; B−R +6.3 vs +9.6; −28.8; river 28.9 below; C15 0.25). The far band is still a pale box plateau (silhouette row std 6.5 px) above a flat grey wall embankment. S3 has not changed, and the tank is 93% Y<25.
4. **Composition: 5.** The S2 avenue now reads as Manhattan: trees, crosswalks, traffic. The red steps in S6 are a pink glow blob (saturation 0.37, V 197).
5. **Image quality: 4.** Share of pixels with Y<25: S3 72.2% and S7 62.5%, both unchanged. The S6 curb is a glowing white strip, with 14.6% >204 at (1150,760,1920,1080).

## A/B
- street-avenue: **B**. Worn, glossy cars and people.
- avenue-swing-height: **A**. Traffic and life. B is flat.
- rooftop-watertowers: **B**. A is crushed.
- perch-skyline: **B**. A's far band is a plateau.
- perch-skyline-dn: **B**. Bridges, graded haze.
- plaza-red-steps: **B**. Red steps, people.
- plaza-street: **B**. Life, lit shops.
- sunset-crosstown: **B**. A is crushed.
- aerial-midtown: **A**. Haze and depth. B is flat.
- progress-street: **A**. Trees and cars. B is empty. A is likely r08.

## Biggest gap
Lift shadowed facades into the C2 range (mean Y 52–119). Raise the albedo of shaded brick and dark glass, and add a lit-interior or sky-reflection term. If GI is the cause, log it to P4.
- Test: S1 (0,0,480,300) and (1360,0,1740,400) mean Y ≥52.
- Test: Y<25 is ≤25% of the frame in S3 and ≤30% in S7.

## Secondary
1. S8 glass (1270,0,1640,300): 70.4% >204. Target ≤1.5% (C1).
2. S4 x0–1300 y150–300: replace the grey wall embankment with a seawall, piers and trees. Vary heights (std ≥12 px).
3. Cars need reflections and trim. Texture the shed. Replace the card interiors. Flag to P6: 0 people.
4. S6: red-step saturation ≥0.44 (ref), no bloom blob. Curb and plaza crop ≤1.5% >204.

## Brand/IP
The 10 billboard and shop names in frame (AMBROCHE, FIZZO, VELVET & VINE, …) have 0 hits in the ref OCR list. Nothing to flag.

## Verdict: FAILS TARGET (lowest 4)

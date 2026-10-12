# Critic W r01: river water blind A/B (water only)

## Method
- I used only the pack and the refs. Each dolly was extracted at 10 fps (100 frames each). All luma figures are Rec.709, measured on crops of the 3226x1814 frames.
- The pack letters are anonymous, so I linked frames to builds by how they look:
  - **Build G** (grey build): `river-low/A`, `dolly/A` and, by its darker water, very likely `S4/A`. It is the same build as `ref-vs-1/B`.
  - **Build O** (olive build): `river-low/B`, `dolly/B` and very likely `S4/B`. It is the same build as `ref-vs-2/B`.
- The reference is `ref-vs-*/A` (`river-pier-golden`). Its near water measures Y 73, high-pass sd 18.7, p1–p99.5 of 23–153, 2.2 % glint pixels, warm olive rgb (81, 72, 57).

## Winner per pair
- **S4: A (G) wins by a hair.** In the same column the water is 4.3 luma below the far shore (129.4 vs 133.7). B's water is 3.0 luma *above* it (135.8 vs 132.8). The C14 spec needs the river 5–35 below the far shore, so both fail: G just misses, O is inverted. In both, the water is washed out into the haze.
- **river-low: B (O) wins.**
  - O: coherent ripple shapes and SSR reflections of the pier, trees and pilings. Its warm olive hue (98, 91, 68) matches the ref's chromaticity.
  - G: flat neutral grey (68, 68, 65) with smeared noise blotches that read as a cloud texture, not waves.
  - Neither has any glint: 0 %, with p99.5 of 92 (G) and 117 (O) against 153 in the ref.
- **dolly: B (O) wins narrowly.**
  - G moves more (water dT 2.22/frame vs 1.51) and its piling foam laps convincingly.
  - O reads more like water, but it has a visible concentric-ring artifact at about y 540–580 of the mid-dolly frame. It also shows mild periodicity: autocorrelation 0.25 at 80 px, against 0.08 for G.
- **Result:** the pairs disagree (S4 goes to G, the other two to O). **Build X = O**, 2 pairs to 1.

## Scores (0–10)
| Axis | G | O |
|---|---|---|
| 1. Motion & detail | 4 (animated, no tiling, but blotchy; high-pass sd 4.1 vs 18.7) | 4 (coherent ripples; ring artifact; high-pass sd 4.4 near / 11.2 mid) |
| 2. Colour, depth & absorption | 4 (luma 68 is right, hue is neutral grey) | 5 (hue right, too bright at 91 vs 73, flat) |
| 3. Reflections | 1 (no sky, skyline or glint) | 5 (SSR works, but detached blobs read as algae; no sky Fresnel, no glitter) |
| 4. Shore & pier foam | 5 (animated piling foam) | 1 (none) |
| 5. Horizon & believability | 3 | 4 |
| **Mean** | **3.4** | **3.8** |

**Build-vs-build margin: O ahead by +0.4, which is a near wash.**

## Against the reference
- **G:** reads as churned grey concrete. It has none of the ref's warm tint, specular sparkle or 23–153 dynamic range. Its piling foam is the only feature at ref level.
- **O:** the closest in colour and the only one with reflections. It is far too calm and matte: dynamic range 66–117, no whitecaps, and no foam where the water meets the pier.

## Biggest gap for O, as a testable instruction
Add an animated high-frequency normal layer (wavelength ≤ 0.5 m) with a sharp GGX sun specular term, and cut the water albedo/scatter. Pass when:
- **river-low near-water crop** (x 0–1500, y 1150–1800): high-pass sd ≥ 12, p99.5 ≥ 150, glint pixels ≥ 1 %, mean Y ≤ 80.
- **S4:** water at least 5 luma below the far shore (C14).

## Secondary issues
- **O:** port G's piling/seawall foam, and remove the ring artifact.
- **O:** reflections need Fresnel-weighted sky toward grazing angles.
- **Both:** the haze swallows the perch view.

## Verdict
**FAILS** (winner O).

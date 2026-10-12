# Round 08: the hero suit is now an original design ("Tessera")

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.
> No official logo, emblem, colour scheme or web pattern is used or recreated. No image-generation prompt was used for any suit art (the suit is procedural; the eye and suit tools are in `tools/ue_char/suit8/`, `hero_suit_r8.py`, `hero_lens_r8.py`).

## Why this round replaced the suit

The round-07 blind critic found that the hero's suit layout "copies a known official suit" (an enclosed spider-figure chest emblem, red-and-blue colour blocking with a red belt band and red thigh stripes, radial orb-web line work over all red areas, big white eye lenses). The suit texture of rounds 01-07 was the browser game's own baseline texture on the browser game's hero UV atlas. The mesh and UV atlas are unchanged this round (they are the game's own hero body, rig and clips, not a suit design); **every texel of colour, panel, line work, badge and eye is new**, generated from code.

## The design

Name: **Tessera** (a small tile). A masked acrobat hero suit built from a slate-teal body, ink-teal panels, amber accents and bone hairlines. The design language is: asymmetry, diagonal planes, joint sleeves, a triangular-tile net, hexagon motifs.

| Element | Tessera (round 08) | Where it lives in code (`tools/ue_char/suit8/design.py`) |
|---|---|---|
| Palette | TEAL `#0f4452` (body), TEAL_D `#0b3441` (crown), DEEP `#071a21` (panels, hood, gloves, trunks), AMBER `#e0780c` (accents) and AMBER_D `#ad5c08`, STITCH `#9cc0c6` (dashed top-stitching), INK / SOLE near-black. **No red, no blue, no white.** | `TEAL ... SOLE` |
| Colour blocking | Cross-asymmetric: the character's RIGHT arm forearm and RIGHT lower leg (greave) carry amber, the LEFT forearm has three amber wrist wraps and the LEFT thigh an amber net on a dark panel, the RIGHT thigh is teal. Left and right are deliberately different. | `Right arm = the amber light side`, `Left leg = amber side accents` |
| Torso | Dark side wedges that widen toward the waist (taper, not a stripe); a tilted amber bandolier sash that is a plane slice of the torso (it climbs differently on the front and the back); a dark belt band with amber hairlines and a hexagon buckle plate; dark trunks above a diagonal hip-wrap cut that runs across both thighs at different heights. | `side panels`, `bandolier sash`, `belt band + trunks` |
| Shoulders / joints | Dark raglan caps whose chest edge is a diagonal plane perpendicular to the arm (not a circle), plus plane-sliced sleeves at the elbows and knees with amber ring lines: one construction vocabulary for all joints. | `joint sleeves` |
| Web pattern | A **diamond net of two opposite helices** wound around each limb and the torso (`helix_dist`), hairline dark on the teal panels, amber with raised knots at the crossings on the dark right upper arm and left thigh. There is no radial / concentric orb web anywhere. The crown has a hexagonal honeycomb (hairline), the jaw a honeycomb vent. | `diamond net` |
| Chest badge | A hexagon ring with three gaps and three kite vanes around a hex core (a net junction), on the sternum; the back carries only a plain broken ring. It is not a spider, bat, star, shield or any existing logo. | `badge()` |
| Mask | Dark hood (plane cut at the neck), teal crown cap with an amber piping arc, two tapered amber brow flashes, honeycomb jaw vent, dorsal seam. Eyes: a blade-shaped lens (rounded inner end, pointed outer tip lifted 12 degrees), amber tint, each in a closed dark bezel ring (`hero_lens_r8.py`). | `mask / hood` |
| Boots / gloves | Dark boots with a near-black toe cap, dark sole and an amber welt line; dark gloves. No spider-web soles, no white soles. | `boots` |

## Side-by-side distinctness (measured, not asserted)

Old = `art/night1/characters/hero/tex/suit_basecolor_r5.png` (rounds 05-07 texture); new = `suit_basecolor_r8.png`. Hue-band shares of the covered atlas texels (`tools/ue_char/eval/suit_distinct_r8.py`, `evidence/suit_distinct.json`, atlas figure `evidence/suit_distinct_atlas.jpg`):

| band | old suit | Tessera |
|---|---|---|
| red (hue < 18 or > 340) | 44.96 % | **0 %** |
| blue (205-265) | 43.86 % | **0 %** |
| white (low saturation, bright) | 5.82 % | **0 %** |
| teal (165-205) | 0 % | 33.9 % (plus 52.4 % of the atlas in the near-black ink-teal DEEP: hood, side wedges, trunks, gloves, shoulder caps) |
| amber (22-48) | 0 % | 12.5 % |
| palette (k-means, 6) | blue (24,36,91) 43.8 %, red (156,16,21) 43.2 %, white (226,225,230) 5.8 % | ink-teal (7,26,33) 51.6 %, teal (14,65,79) 32.7 %, amber (223,120,12) 10.8 % |

Structure, side by side:

| attribute | old layout | Tessera |
|---|---|---|
| chest graphic | large white figure with eight legs, symmetric, dead centre | small amber hexagon badge with three kite vanes, on the sternum; nothing on the back but a ring |
| torso blocking | red chest, blue side panels, red belt band | teal chest, dark wedges at the waist, amber diagonal bandolier sash |
| line work | radial orb web (spokes + concentric arcs) over every red area | two-helix diamond net, sparse, with raised knots |
| legs | blue with a red stripe on both legs, symmetric | right leg teal with an amber greave, left leg dark thigh with amber net and amber ankle bands, diagonal hip-wrap cut |
| arms | red, symmetric, web over all | right forearm solid amber, left forearm teal with three wrist wraps |
| eyes | two large white teardrops slanting down toward the nose | two amber blade-shaped lenses, outer tips lifted, each in its own closed dark bezel |
| boots | red with web pattern and white sole | dark with a near-black toe cap and amber welt |

Images: `captures/hero_turntable_4k.jpg`, `captures/suit_closeup_4k.jpg`, `captures/hero_face_lens_4k.jpg` (round 08) next to `../round-07/captures/` (same shots, old suit): `evidence/suit_side_by_side.jpg`.

## Notes on legal safety (for the owner)

* No image generator, no reference image of any real suit, no scan, no trace: the pattern is a function of the body's 3D positions (planes, helices, hexagon distance fields).
* The body mesh, skeleton and animation clips are the game's own (unchanged). The owner decision "original suit" from the director plan section 5.1 is thereby implemented; whether the silhouette of a masked, fitted, web-line-suited hero is itself too close is a judgement the owner / critic keeps.
* The previous layout's texture files remain in the repository history and in the browser baseline (`public/assets`); the Unreal port no longer loads them.

# Round 12: the armpit jog, weave flip and faceted patches were one fault (a skinning fold)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Critic r11:** Verdant chevron edge jogs 24 px at (1333-1357, 1610-1680); faceted polygon shade patches on Ash (1330-1480, 1330-1750) and Tessera (1430-1500, 1330-1440);
the round-11 builder saw a weave-direction flip and a sash-border stair-step at the same armpit spot and suspected the UV islands.

## What was measured (CPU, no engine)

1. **The suit textures are continuous across the UV seam there.** `seam_profile` (a scratch probe; the committed seam check is `tools/ue_char/eval/suit_seams.py`) samples the base colour on
   both sides of every seam edge at the same 3D points: in the chest box (|x| < 0.25 m, 1.00 < y < 1.45 m) the only differences are at the armpit
   (y 1.33, |x| 0.18-0.22, thin lines crossing the seam at an angle), none on the side seam at (+-0.14, 1.19) where the jog is.
   The hero mesh is one watertight component (25 314 welded vertices, 0 open edges), with continuous normals and identical skin weights on both sides of every seam.
2. **The jog is geometry.** Skinning the mesh on the CPU with the glTF `idle` clip (`hero_weights_r12.py --check`, `cpu_posed.py` in the scratch dir) reproduces the
   notch in the silhouette and the jog of the band edge (`evidence/fold_cpu_idle2.2_before_after.jpg`, left column). Cause: neighbouring torso-side vertices carry
   small weights on DIFFERENT arm bones, e.g. rest (-0.136, 1.240, 0.027) torso 0.88 + shoulder 0.12 next to (-0.151, 1.229, -0.019) torso 0.89 + upperArm 0.11.
   With the arms down the upperArm-weighted row moves ~12 mm inward while its shoulder-weighted neighbours stay: the surface folds along that row.
   A fold hides a strip of surface (the band edge jumps), shows differently-oriented triangles side by side (faceted shade patches) and
   puts two differently-facing surfaces next to each other (the weave appears to change direction).
3. **The normal map is right.** `tools/ue_char/suits/tangent_check.py` decodes the tangent-space normal map with a MikkTSpace-style frame per UV island and compares it
   with the 3D gradient of the painted height: all-texel median cosine 0.994, every large island >= 0.99, no island flipped (fingers 0.8: coarse finite differences
   on 1-2 cm cylinders).

## Fix

`tools/ue_char/suit8/hero_weights_r12.py` (run by `build_characters.py` 'prep' after `hero_lens_r8.py`):
- below the armpit (y 1.25 -> 1.36 m ramp) the shoulder / deltoid / upperArm weights of the chest side are moved onto the vertex's own spine bones (`strip_arm`),
- then a Gaussian average of the per-joint weights over 3 cm neighbourhoods (same-facing only) inside the 1 650-vertex torso-side region, four largest kept.
Positions, normals, UVs and the suit paint are untouched. Fold count in that region (posed face normal against its vertex normals, dot < 0.3), original -> round 12:
`evidence/fold_check.json` (run, sprint and fight-idle poses drop by a half to three quarters; the idle keeps 2 folded faces in the armpit crease itself).

Also in the same round, island-independent WEAVE: `M_Char_Suit` lays the fabric weave out from the pre-skinned 3D position (triplanar), not from the UV atlas.

# Round 01 — character asset evaluation

> Fan homage project. Not an official Marvel, Sony or Insomniac product; no affiliation. See `DISCLAIMER.md`.

Clips: `assets/<asset>.mp4` (1280×720, 30 fps, 5 s: frames 1–60 camera orbit while walking, 61–105 3/4 walk, 106–150 side view run), stills `assets/<asset>.jpg` (frame 95) and `assets/<asset>_face.jpg` (humanoids). Blender 5.2 Eevee, grey studio (key/fill/rim area lights, flat grey world, grey floor), no post.
Scripts: `tools/ue_char/eval/` (`render_glb.py`, `citizens.py` + `citizen_rig.py`, `fauna.py`, `tiles.py`, `glb_stats.py`).

Measurement notes
- UV cov = share of the 0–1 tile covered by triangles (512² raster). Islands = connected UV components. Texel = median base-colour px per metre of surface.
- Hero-rig assets (hero, thug, brute, suits) play the hero `walk` / `run` clips (30 fps keys, in place). The thug has no locomotion clip of its own; in game it also borrows the hero's.
- Citizens: 18-bone crowd rig rebuilt as a Blender armature from `people.bin` baked matrices (max vertex error vs direct skinning 4.7e-6 m); clips `walk` (men) / `walkF` (women) and `run`. Body only, accessories not attached.
- Fauna: numpy port of the runtime vertex shaders (`fauna.js` quadGLSL / `pigeons.js` bird shader); phase/amp/time inputs approximated (walk 1 stride per 20 frames, flap amplitude 1), so motion timing differs from the game.
- Raw sources: suits `~/Downloads/*spiderman*.glb` are the same meshes as the shipped skins (identical vert/tri counts), 8192² base colour only; shipped skins downscale to 4096². No higher-poly source exists to bake from. Raw citizens (`~/sm2-assets/raw`) are 5.4k–6.5k tris (one 19.4k), 8192² base colour only. Raw animals/props (`raw2`) 14.6k–21.5k tris, 8192² base colour only; `pigeon_in_flight.glb` has no texture.

## Hero rig

| Asset | Tris | UV | Maps (res) | Defects seen | Verdict |
|---|---|---|---|---|---|
| hero `spiderman.glb` | 50,628 body + 2,520 lenses | cov 63%, 21 islands, 2,331 px/m, 2.2% tris >2× off median density | BC, ORM, normal, AO 4096² (lenses: factors only) | No TANGENT attribute on the body. Web lines read as painted lines plus shallow normal relief; fabric micro-detail visible only in close-up. Walk frame 95 shows bent-knee, hand-at-hip pose from the clip. Mesh, UVs and weights hold up in orbit and run; no tearing seen. | keep (refine material: tangents, fabric response) |
| thug `thug.glb` (BC a) | 55,999 | cov 64.6%, 33 islands, 1,023 px/m | BC, ORM, normal, AO 2048² | Flat hand-painted base colour: no cloth folds or wear. Face is a painted mask: cartoon eyes and brows on a flat skin band, polka-dot bandana, no facial geometry. Hood/beanie rim and bandana bottom edge show jagged texture-edge stair-stepping. Proportions are the hero body. | replace (or re-texture + new head) |
| thug_b (`thug_basecolor_b`) | same | same | BC variant 2048² | Same as thug; colour swap only. | replace (with thug) |
| thug_c (`thug_basecolor_c`) | same | same | BC variant 2048² | Same as thug; colour swap only. | replace (with thug) |
| brute (thug ×1.24 + `brute_basecolor.webp`) | same | thug UVs | BC 2048² (runtime swaps map only) | `brute_basecolor.webp` island layout does not match `thug.glb` UVs (compared side by side): texture patches land across garment borders; the red pattern lands on the back, a skin-tone patch on the thigh, a metal band across the eyes. Same code path in game (`enemy.js tintBrute` swaps `map` only). Uniform ×1.24 scale, no bulk change. | replace |

## AI-logo suits (hero skeleton, Tripo-derived)

| Asset | Tris | UV | Maps (res) | Defects seen | Verdict |
|---|---|---|---|---|---|
| suit_claude | 43,207 | cov 68.1%, 2,780 islands, 1,993 px/m | BC only 4096² (source 8192²) | Dark dash marks at UV island borders on shoulders, back, shins (texture gutter bleed across ~2.8k islands). Soft baked shading in the base colour (darker back/underarms). No normal/roughness maps: uniform 0.55 roughness. Lens shapes painted/sculpted, no separate lens material. | refine |
| suit_codex | 47,196 | cov 67.5%, 2,173 islands, 2,054 px/m | BC only 4096² | White suit makes seam dashes most visible (black streaks on back, thigh, calf). Face/mask has a painted center seam line. | refine |
| suit_gemini | 44,532 | cov 66.7%, 1,766 islands, 2,041 px/m | BC only 4096² | Chest star logo repeated on the back (painted and sculpted) inside a purple baked gradient. Seam dashes on chest/shoulders visible in close-up. | refine (back logo) or regenerate |
| suit_kimi | 43,827 | cov 61.5%, 2,713 islands, 1,891 px/m | BC only 4096² | Seam dashes on shoulders/chest; baked shading darkens torso sides; "K." chest badge is a flat decal. | refine |
| suit_qwen | 45,463 | cov 67.3%, 2,302 islands, 2,032 px/m | BC only 4096² | Chest logo repeated on the upper back. Seam dashes on shoulders/neck in close-up. | refine (back logo) or regenerate |

All five: skinning follows the hero rig through walk and run without visible tearing in the clips; fit gap 2.9–3.3 cm (skinfit README).

## Citizens (crowd pack, 18-bone rig, LOD0 5,000 tris each, 1024² tile of a 6144×5120 atlas, BC only)

Common to all 20: base colour only (roughness 0.82 at runtime); Tripo auto-unwrap with 460–880 UV islands per body; texel 460–610 px/m; dark dash artifacts at UV island borders (clothing backs, jaw/neck lines in face close-ups); lighting baked into the texture; hands at this tri budget have no separated fingers. Skirts/long coats are skinned to the legs only (no cloth bones), so they stretch between the legs in the run.

| Citizen | UV cov / islands / px/m | Fit RMS | Defects seen (in addition to the common ones) | Verdict |
|---|---|---|---|---|
| 01_retired_gent | 75.3% / 823 / 472 | 4.56 cm | Trench coat skirt stretches between legs in run; seam dashes on coat back; dark line across chin/neck. | refine |
| 02_leather_jacket | 73.5% / 611 / 568 | 4.40 cm | Face good at crowd distance; dark dash marks on jaw and jacket. | keep |
| 03_white_tee | 75.5% / 599 / 607 | 3.12 cm | Light dashes on white tee back and trousers; clean face. | keep |
| 04_blue_sweatshirt | 78.1% / 544 / 577 | 4.23 cm | Dark lines across neck/collar in close-up; long hair is a solid shell. | keep |
| 05_black_tee | 75.0% / 461 / 600 | 3.23 cm | Few visible defects; hair shell. | keep |
| 06_chrome_shades | 74.9% / 708 / 562 | 4.30 cm | Dash marks on hoodie front/back and cheek. | keep |
| 07_black_graphic_tee | 77.1% / 596 / 594 | 3.30 cm | Few visible defects. | keep |
| 08_black_suit | 75.5% / 791 / 590 | 3.48 cm | Dashes on jacket back; face readable, glasses painted/sculpted. | keep |
| 09_kurta_waistcoat | 75.3% / 466 / 461 | 4.82 cm | Long kurta panels tear/stretch between the legs in run (visible torn edges). Lowest texel density. | refine |
| 10_silver_tie | 72.4% / 621 / 549 | 3.53 cm | Dashes on jacket back and trousers; dark line across cheek. | keep |
| 11_graphic_tee_bonnet | 78.3% / 676 / 539 | 3.96 cm | Dashes on tee back; bonnet reads as lumpy solid shell. | keep |
| 12_sundress_mom | 76.8% / 855 / 536 | 5.43 cm | Dark crack lines across cheek and jaw in face close-up; dress hem stretches in run. Highest fit RMS. | refine |
| 13_construction_worker | 75.8% / 685 / 567 | 4.71 cm | Few visible defects; readable silhouette. | keep |
| 14_teen_skater | 74.8% / 724 / 498 | 5.21 cm | Dark marks by mouth; backpack and headphones are part of the body mesh. | keep |
| 15_executive | 71.8% / 620 / 553 | 4.31 cm | Dark lines on neck/collar; bag strap baked into the body. | keep |
| 16_lumberjack_hipster | 73.1% / 662 / 507 | 5.03 cm | Face/beard split lines along the jaw; dashes on vest back. | refine |
| 17_hijabi_student | 76.4% / 616 / 491 | 4.88 cm | Long coat stretches between the legs in run with torn-looking edges; dashes on coat. | refine |
| 18_dapper_elder | 73.9% / 757 / 529 | 4.60 cm | Dashes on jacket back; dark line across chin. | keep |
| 19_marathon_runner | 73.3% / 878 / 593 | 3.80 cm | Dashes on vest; hair shell with visible seams. | keep |
| 20_punk_artist | 73.9% / 821 / 530 | 4.19 cm | Dark crack lines across cheek; skirt hem stretches in run. | keep |

## Fauna (rigid-part vertex rig, 1024² tile of 3072² atlas, BC only)

Common: decimated to 0.4k–3k tris with 150–600 UV islands, so the shading reads faceted and island-border slivers show as light/dark flecks across the fur; no fur cards or normal maps.

| Animal | Tris | UV cov / islands / px/m | Defects seen | Verdict |
|---|---|---|---|---|
| golden (retriever) | 3,000 | 69.4% / 531 / 722 | Faceted body, flecked texture; legs swing rigidly from hip pivot (no knee). | refine |
| bulldog | 3,000 | 65.4% / 606 / 1,186 | Faceted, flecked; head readable. | refine |
| cat | 1,999 | 70.3% / 333 / 1,299 | Faceted body, readable face; rigid legs. | refine |
| rat | 1,198 | 35.9% / 339 / 1,259 | Low UV coverage; fur texture reads as noise at close range; acceptable at street distance. | keep |
| squirrel | 1,200 | 42.5% / 442 / 1,441 | Tail is a blocky faceted mass; body flecked. | replace |
| pigeon | 700 | 54.4% / 157 / 2,631 | Faceted feathers, readable colour. | keep |
| gull | 800 | 66.5% / 178 / 1,617 | Faceted wings/body; readable. | keep |
| pigeonfly | 400 | 32.0% / 3 / 1,738 | Card-like wings with painted planar texture (source had none); jagged feather-tip silhouette. | keep (distance only) |
| gullfly | 400 | 32.0% / 3 / 882 | Same as pigeonfly. | keep (distance only) |

## Verdict counts (39 assets)
- keep 21: hero (material refinement still listed), 15 citizens, rat, pigeon, gull, pigeonfly, gullfly.
- refine 13: 5 suits, citizens 01/09/12/16/17, golden, bulldog, cat.
- replace 5: thug, thug_b, thug_c, brute, squirrel.

# Round 04: SPEC check (CH1-CH19), builder-measured

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation.

Measured on this round's captures (`captures/`) and clip data; tools named per row. "Builder hand-check" = read by eye on the named frames, no instrument. Scores are the critic's job; this table only states numbers.

| id | target | measured | source | status |
|---|---|---|---|---|
| CH1 | ground framing hero height 0.48-0.62 | not measured (no gameplay camera in the lineup map) | - | not measured |
| CH2 | run chase framing 0.39-0.53 | side-run capture: 0.59 (a test framing, not the chase camera) | `video_checks.py hero_run` | not measured on a gameplay camera |
| CH3 | suit texel density >= 680 texels/m | not re-measured this round | - | not measured |
| CH4 | close-up suit read | lens: glossy (roughness 0.07, specular 1.0) with a grazing-angle base-colour falloff; lens triangles still flat; bezel gap at the top-left corner still visible (`hero_turntable_4k.jpg`); weave unchanged | `suit_closeup_4k.jpg`, `hero_turntable_4k.jpg` | judged by critic |
| CH5 | 4K captures rendered at 3840x2160 internal | 18 stills: internal 3840x2160, screen percentage manual | `evidence/perf_4k_groups_contaminated.json` | met |
| CH6 | run 3.2-3.8 steps/s | head-blob bob FFT **3.46 Hz** (side run 0.5-5.9 s); bob minima 3.86/s; three-quarter run FFT 3.64 Hz; clip data 3.53 steps/s. The whole-mask top (`hero_run` mode) peaks at 1.83 Hz = stride rate: the hand swings above the head top | `video_checks.py head_bob / hero_run`, `evidence/video_hero_run_side.jsonl` | met (head-blob FFT) |
| CH7 | torso lean >= 15 deg | clip head-to-hip **25.6 deg** (min 25.2); pixels, side run: head-to-belt median **24.2 deg**, 76 % of frames >= 15; whole-mask mid-band method median 15.9 deg, p10 10.4 | `measure_clip.py`, `video_checks.py lean_belt / hero_run` | met on median; not on every frame by the pixel methods |
| CH8 | arm swing | hand fore-aft swing 73 cm (clip; round 03 61 cm) | `evidence/hero_clips_r4.json` | no ref number |
| CH9 | foot drift <= 3 cm per plant | run at the lineup speed 5.70 m/s: 2.7-2.8 cm (clip natural 5.95 m/s) | `foot_speed.py` | met (clip level) |
| CH10 | blends >= 0.15 s, no pops; run -> jump >= 9 frames with a crouch | head drops from 1.350 s, lowest 1.517 s (head top +144 px), feet leave the ground 1.533-1.550 s: **11-12 frames** of crouch before lift-off; clip level 15 frames | `evidence/hero_takeoff_r4.json`, `hero_liftoff_strip_1500-1667ms.jpg` | met |
| CH11 | 5-7 enemies in frame | lineup wide: 7 people >= 3 % height in every sampled second 0-5 s (movie) and in the 4K still | `evidence/yolo_enemy_lineup*.json` | met (lineup, not a fight) |
| CH12 | enemy height 0.16-0.60 | 0.25-0.34 (wide), 0.07-0.34 (3/4, one far figure at 0.07) | same | met on the wide shot |
| CH13 | >= 5 outfit silhouettes, >= 2 weapon types | 5 outfits (leather jacket + hood, puffer vest + beanie, hoodie + cargo + shades, tee + cap, tee + chains) + 2 tints; 3 weapon types (bat, pipe, pistol; own models, no lettering) | `enemy_lineup_wide_4k.jpg` | met (builder count) |
| CH14 | faces, hands, cloth folds, shoes | masks are the head surface (conform to nose and chin, ears bare, no poke-through); face stills of all five | `*_face_4k.jpg` | judged by critic; defects listed below |
| CH16 | 8-25 people per street frame | civilians tracking: median **11**, min 9, max 14 (16 samples); wide: median 11, min 9; 4K stills 12 / 11 | `evidence/yolo_civilians_*.json` | met |
| CH17 | 0 gliders; >= 6 distinct models; no hero copies | 12 distinct citizen meshes, each walker plays a walk clip (no bind pose); legs change pose frame to frame in the tracking clip; no hero-suit mesh in the civilian shots; per-plant slide 0.9-2.9 cm at each style's speed (clip level) | `civilians_tracking_legs_strip.jpg`, `evidence/crowd_gait.json` | builder hand-check: no glider seen |
| CH18 | zero seam / sparkle pixels at 4K | defects remain (below) | 4K stills | not met |
| CH19 | gait phase spread >= 0.2 cycle | not measured (start positions and 5 walk styles differ) | - | not measured |

## Defects seen by the builder at native 4K (CH18 / CH14)
1. Hero: white texels on the back of one glove remain (`hero_run_side_4k.jpg`, right hand): those texels are shared in UV with the chest emblem, so the round-04 inpaint (hand-only texels) cannot reach them without a UV change.
2. Hood: two small dark triangular holes at the lower mask edge; the hair has a brown shell at the back and front-left under the blond (raw atlas reuses texels, gotcha 4).
3. Beard: a pale diagonal streak across the lower-left of the mask; a pale patch on the hair at the right temple.
4. Brute: the mask's lower edge forms a stiff flap over the vest collar on the right side (`brute_face_4k.jpg`).
5. Citizens: white speckle streaks on the dark suits (`08_black_suit`, `15_executive`) in the tracking clip.
6. Hero lens bezel gap at the top-left corner of each lens.

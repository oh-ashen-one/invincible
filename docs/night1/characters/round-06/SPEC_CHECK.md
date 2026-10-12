# Round 06: SPEC check (CH1-CH19), builder-measured in the engine

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation.

Measured on this round's captures (`captures/`, provenance and resolution in `CAPTURES.md`) with the tool named per row; numbers in `evidence/`. "Builder hand-check" = read by eye on the named frames. Scores are the critic's job; this table states numbers and what I saw. Every 4K still is native 3840x2160 (internal 3840x2160); movies are 1080p60 (internal 1920x1080), motion blur off. All GPU runs shared the GPU with other agents: **no frame time here is a performance number.** The hero, enemies, weapons, hero clips, crowd layout and gait phases are byte-for-byte unchanged since round 05; only the 18 citizens (refit meshes + welded weights + 2048 px textures, the round-06 fix) and the lineup lighting changed.

## Round target: verify the seam fix in the engine (CH18, garment integrity)

Baseline = the round-05 critic's three demands. Evidence per demand:

**1. Zero enclosed key pixels inside any torso or sleeve silhouette in `crowd_key_*_4k`.**
- The black-tee armpit hole (round 05: 279 px at 413,1167 in `crowd_key_a_4k`) is gone: `captures/crops_3x/armpit_key_a_3x.jpg` (left round 05 with the hole, right round 06: one closed torso / sleeve).
- Full census with `tools/ue_char/eval/key_report.py` (now separates real see-through from green-tinted surface: a component counts as `true_key` only if its mean colour is within 45 (BGR) of the rendered key colour (0,230,0); hair, skin and cloth in shade under the green bounce light pass the key thresholds but are surface). Enclosed components of the person mask (>= 6 px):

| still | round 05: interior / true key (px) | round 06: interior / true key (px) |
|---|---|---|
| crowd_key_a | 47 / 3 (493) | 53 / 4 (18770) |
| crowd_key_c | 47 / 13 (14745) | 36 / 5 (7331) |
| crowd_key_tracking | 31 / 2 (101) | 20 / 2 (266) |
| crowd_key_wide | 31 / 4 (635) | 24 / 9 (909) |
| **total** | 156 / **22** | 133 / **20** |

  The raw counts hardly move, and I do not present them as the result: what is enclosed is dominated by natural gaps (between two overlapping walkers, between a hanging arm and the torso, between the legs), which depend on framing and the director clock. The result is **where** they are. I classified every one of the 42 true-key components by eye on 3x crops (`evidence/truekey_interior_components_round05.jpg` and `..._round06.jpg`, labelled x,y,px,width):
  - round 05: **at least 6 holes through cloth**: the black-tee armpit (a 427,1174), two torso slits and a plaid sleeve slit (c 3390,1206 / 3346,1198 / 1826,1059), a coat slit (tracking 2998,1504), a trouser slit (wide 140,1488); the rest gaps between limbs / people.
  - round 06: **0 holes through a torso, sleeve, coat or trouser panel.** The 20 are: 6 gaps between two different walkers (a 601,1003 and a 603,1509 are the two 9 k px gaps between two overlapping people; c 3344,1783; c 3363,953; a 799,1948; a 2950,1234), 9 natural arm / torso, arm / hip, forearm / hem or leg / leg gaps enclosed by a hand or hem (c 305,1110; c 1285,1321; wide 3747,1108; 3522,1138; 3655,1294; 1253,1155; 963,1397; 3533,1170; 2129,1242), 2 specks of 9 px by a bag strap (wide 1244,1200 / 1245,1196), and **3 small ankle gaps between a trouser cuff and a shoe collar (tracking 1625,1277 211 px; 1655,1274 55 px; c 901,1269 9 px)**, the one real geometry defect left in this metric (about 2 cm wide at the near lane's 700 px/m, see Known problems). Hand classification: uncertain calls are the two a-still leg slivers (799,1948 / 2950,1234: leg edge of one walker against another walker's cloth, I read them as between-people gaps).
  - The 113 interior components that are not true key are green-tinted surface (bearded cheek, hair, hijab shadow, olive cloth fold): crop montages `keyreport_round06/*_crop_0*.jpg`.
- Round-05's own legacy counter (`key_holes.py`, counts tinted surface too) is nearly flat: thin components 263 -> 226 (-14 %), thin px 8704 -> 7054 (-19 %); it is not a crack measure.
- Offline gate for the same fix (`evidence/offline_ch18_*`, `eval_r6.py`, proxy of the engine's skinning on the crowd's own clips, 18 citizens x 72 views at 700 px/m): cracks 1035 comp / 42551 px -> **244 / 13362**; triangles growing > 5 cm in a walk 2134 -> **13**, > 10 cm 915 -> **0**; worst edge growth 51.5 -> **5.6 cm**.

**2. No vertex spikes > 5 px outside the cloth on the olive coat, trousers, hoodie collar.**
- Coat, near-lane trousers: `captures/crops_3x/coat_tracking_3x.jpg` and `trousers_tracking_3x.jpg` (left round 05: the knee flap of the olive coat, torn hem, black spikes off the trouser knee and shins; right round 06: one closed coat panel with a clean hem, smooth trouser). Across the 7.4 s clip the coat stays one piece (`crowd_tracking.mp4`, sequence checked at 1 s steps).
- Silhouette-spike census on the key stills (`spike_key.py`: parts of the person mask thinner than 7 px reaching > 6 px off the body; it also counts fingertips and hair strands, so it cannot read zero): longest spike round 05 **37 / 25 / 25 / 21 px**, round 06 **19 / 45 / 23 / 18 px** (a, c, tracking, wide); the 45 px one is a vest edge line, the others are finger tips and forearm edge lines (viewed at 3x: the five wedge fingers are separate and intact; `evidence/spike_key_*.jsonl`). No 100+ px shard remains (the round-05 coat flap and trouser spikes reached ~100+ px in the colour still).
- Hoodie collar (`thug_face_4k`, `collar_thug_3x.jpg`): the dark shapes are **not geometry**. Same frame with shadows off (`evidence/collar_shadow_test.jpg`): the hard-edged dark wedge inside the hood and the black wedge at the shoulder vanish. Measured earlier: collar-zone edge growth <= 0.9 cm in the thug's walk. Fix applied to the lineup lighting only (3 deg sun disc, fill 1.4 lux): the shadow edges are softer and the neck reads calmer (`evidence/collar_lighting_before_after.jpg`); **the hood-interior shadow wedge is still visible**, only softer. Not claimed fixed.

**3. No stretched fingers.** `captures/crops_3x/hand_tracking_3x.jpg` (left: round-05 claw of stretched wedges with a triangular web; right: five separate tapered fingers, one hand) and the near-lane hand in `trousers_tracking_3x.jpg` (fingers on the hip, no tears). The citizens' hands are the raw Tripo hands, still low-poly (faceted wedges), but each finger is a clean, separate, single-bone piece.

`captures/crops_3x/` = 3x Lanczos crops of the exact boxes the critic named.
The critic's own `cracks.py` (bright thin components on dark-clothed people) still prints 37 on `crowd_tracking_4k` (round 05: 37): `evidence/cracks_classify.jsonl` = 11 hair / face, 8 hand / arm skin, 18 cloth / other; overlaying them (`eval/crack_view.py`, `evidence/cracks_overlay_crowd_tracking_4k.jpg`) shows they are hair highlights and 1-px silhouette-edge lines against the pale wall on the near-lane black-tee walker and the lumberjack's vest edge, none is an opening in the cloth. The tool measures brightness, not see-through; the chroma-key census above is the see-through measurement.

## The other lines

| id | target | measured | source | status |
|---|---|---|---|---|
| CH1 | ground framing hero height 0.48-0.62 | chase camera (behind, 5 m, FOV 62) **0.421** median; toward the camera 0.329; whole-body / side test framings not re-measured (unchanged, round 05: 0.79 / 0.70) | `evidence/video_hero_run_chase_heroRun.json`, `_toward_` | 0.42 below the 0.48-0.62 band (unchanged from round 05); the run band CH2 is met |
| CH2 | run chase framing 0.39-0.53 | chase **0.421**, toward 0.329 | same | met (chase) |
| CH3 | suit texel density >= 680 texels/m | hero unchanged: 2331 texels/m (`art/night1/characters/hero/tex/suit_r5.json`). Citizens: 2048 px raw Tripo texture per citizen (round 05: 1024 px tile) | file | met |
| CH4 | close-up suit read | unchanged content (`suit_closeup_4k.jpg`, `hero_face_lens_4k.jpg`) | - | judged by critic |
| CH5 | 4K captures rendered at 3840x2160 internal | every 4K still: output 3840x2160, internal 3840x2160 (screen percentage manual 100); movies 1920x1080 internal | `evidence/perf_*.json` | met |
| CH6 | run 3.2-3.8 steps/s | head-blob FFT: side **3.66 Hz** (bob minima 3.46 / s), chase **3.54**, toward **3.54** | `video_checks.py head_bob / hero_run` | met |
| CH7 | torso lean >= 15 deg | head-to-belt median **24.5 deg**, 82 % of frames >= 15 (side run) | `video_checks.py lean_belt` | met on median |
| CH8 / CH9 | arm swing / foot drift | unchanged clip: not re-measured (round 04 / 05 numbers stand) | - | no ref number / met at clip level |
| CH10 | blends >= 0.15 s, take-off crouch, no T-pose | leap clip: head top 398 px (run) -> **516 px at 1.517 s (crouch, 118 px)** -> 355 px at the 1.85 s apex; landing dip at 2.15 s; the contact sheet of the clip shows no T-pose frame | `evidence/leap_track.json` (`eval/leap_track.py`), `hero_run_leap_side.mp4` | met (pixel level); the same take as round 05 (both leaps are one take) |
| CH11 | 5-7 enemies in frame | fight clips, people >= 3 % height: median **6 (wide) / 7 (3/4) / 7 (orbit, max 9)**; 4K stills **7 / 7 / 7** (6 enemies + hero) | `count_videos.txt`, `yolo_street_fight_*_4k.json` | met |
| CH12 | enemy height 0.16-0.60 | clips: median 0.293 / 0.309 / 0.330, p90 0.397 / 0.398 / 0.465, max 0.51; 4K stills 0.159-0.398 / 0.228-0.402 / 0.142-0.502 (incl. the hero) | same | met |
| CH13 | >= 5 outfit silhouettes, >= 2 weapon types | unchanged: 6 distinct enemy outfits; bat, pipe, pistol (own primitives) | `street_fight_1080.jpg` | met (builder count) |
| CH14 | faces, hands, cloth folds, shoes | faces re-lit in the lineup (`*_face_4k.jpg`); masks / hands / shoes unchanged | - | judged by critic |
| CH16 | 8-25 people per street frame | tracking clip median **9** (p10 8, max 11, 16 samples); wide median **15** (p10 13.1, max 16, 12 samples); 4K stills 9 / 17 people >= 3 % height; tallest 0.568 of frame height | `count_videos.txt`, `yolo_crowd_*_4k.json` | met (tracking at the low end, as in round 05) |
| CH17 | 0 gliders; >= 6 distinct models; no twins | 18 distinct citizen meshes, every visible walker strides in the 1 s-step sequence of `crowd_tracking.mp4`; no hero-suit mesh in the civilian shots | builder hand-check | met (hand-check) |
| CH18 | zero seam / sparkle pixels at native 4K | see the round target above: **0 holes through cloth** (round 05: >= 6), 3 tiny ankle-cuff gaps remain, hands / coat / trousers clean in 3x crops | `evidence/keyreport_*`, `crops_3x/` | met for torso / sleeve / coat / trousers; ankle gaps open |
| CH19 | gait phase spread >= 0.2 cycle | pairwise circular phase difference median **0.27 / 0.273 / 0.257** at t = 0 / 5.5 / 11.5 s, min 0.006-0.034; resultant length R 0.02 / 0.03 / 0.17 (near lane R 0.14 / 0.16 / 0.52: three same-style walkers drift into step at 11.5 s) | `evidence/gait_phase.json` (build-script parameters, unchanged) | met on the median |

## Known problems (builder)

1. **Ankle / shoe-collar gaps** (3 in the key stills, 211 / 55 / 9 px at 4K, tracking still 1625,1277): the trouser cuff and the shoe do not overlap at mid-stride; `boundary_loops.py` lists the loops; fix = bridge strip between facing boundary loops. The offline gate's remaining 244 slivers are the same class plus silhouette-edge slivers.
2. **Hood-interior shadow wedge** in `thug_face_4k` is softened, not gone (a self-shadow of the hood rim; the mesh is fine).
3. **Streaming warm-up**: every `-movie` run shows low-mip textures for ~0.4 s at the start; the first clip of each run is trimmed by 0.6 s (see `CAPTURES.md`); a proper fix is `r.Streaming.FullyLoadUsedTextures 1` (not tried).
4. Untouched secondary items of the round-05 critic: the hero suit design is still the open brand (IP) flag (owner decision), the lens rim, arms held ~30 deg out on the walkers, no crowd avoidance (two walkers overlap in `crowd_key_a`), the fight has no hit reactions / knockdowns, masks read the lips.
5. Citizens are low-poly (6 k triangles): fingers are faceted wedges, arms are 10-12-sided tubes; the silhouette shows it at 4K.
6. Performance not measured (shared GPU, contaminated slots).

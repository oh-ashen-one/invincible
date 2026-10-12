# Round 02: captures of the running lineup map

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Source:** real `-game` runs of `/Game/Tests/Characters/Char_Lineup` (UE 5.8.3, Metal, offscreen, `-RenderOffScreen -NoSound`) through F1's `unreal/WebHomage/Scripts/run_game.sh`. `AWHCharShowDirector` drives the camera. Rebuild with `tools/ue_char/build_characters_headless.sh`, then `tools/ue_char/capture_lineup.sh` (clips and 1080p stills) and `tools/ue_char/capture_4k_stills.sh` (4K stills).

**Method change from round 01:** the six clips are cut from ONE 51.5 s fixed-step 1080p run of the whole director cycle (shot 0 at t = 0) instead of one launch per clip. Walker phases therefore differ from round 01 (each clip starts at its shot's place in the cycle, not at t = 0). Same shots, same names; one added clip.

**Movies:** `-movie` gives a fixed 1/60 s step and writes every frame, so playback is smooth and says nothing about real-time speed. 1920x1080, 60 fps, H.264 crf 20. Motion blur on. Internal resolution for 1080p output is auto screen percentage (1399x787 per CAPTURE.md; not re-measured for these runs).

**Stills:** `lineup4k_*` are from a real-time 3840x2160 run at game seconds 3, 8, 13, 18, 21 (file 03 at 18 s not kept, as in round 01). Perf json: `lineup4k_perf.json` (output 3840x2160, internal 1920x1080, auto_display; avg 17.35 ms, p95 21.76 ms, p99 24.65 ms, one 2018 ms hitch; GPU avg 11.8 ms). GPU utilisation was 69 % from other sessions right before that run (`gpu_util_before_4k_stills.txt`), so it is not a clean measurement. The 1080p movie run and the 4K brute runs were not perf-measured.

| File | Shot | Content |
|---|---|---|
| `hero_turntable_walk.mp4` (6 s) | orbit | Hero walking in place, turning 30 deg/s, camera orbiting 45 deg/s. Unchanged content from round 01. |
| `hero_run_side_34_hop.mp4` (10 s) | side, then 3/4 | Hero on the 9x4.2 m ellipse at 5.6 m/s, hop every 5 s. Unchanged. |
| `hero_suit_fabric_closeup.mp4` (4 s) | close-up | Chest/shoulder at 95 cm, FOV 30. Unchanged. |
| `thug_brute_walk.mp4` (7 s) | 3/4, then side | 0-4 s thug (round-01 texture) on the hero skeleton with the hero walk at 1.5 m/s; 4-7 s brute at 1.3 m/s: thug mesh x1.24 x girth 1.2, `brute_basecolor` painted on the thug UVs, `MI_Brute` tint 0.85. Camera 700 cm, aim 105 cm, on the opposite flank from round 01. |
| `brute_orbit.mp4` (6 s) | orbit | New. The brute walking, camera orbiting once (60 deg/s) at 700 cm. |
| `citizens_walk.mp4` (13 s) | wide, side, 3/4 | 4 citizens on the shared 18-bone skeleton. Unchanged. |
| `ai_suits_walk.mp4` (5 s) | wide | Five AI suits walking in place and turning. Unchanged. |
| `lineup4k_00_t003.jpg`, `01_t008`, `02_t013`, `04_t021` | orbit / side / 3/4 / close-up | Hero turntable, hero run, hero 3/4, suit fabric close-up, 4K. |
| `thug_walk_1080.jpg` (movie t = 22.5 s), `brute_walk_1080.jpg` (25.5 s), `citizens_wide_1080.jpg` (29 s), `ai_suits_1080.jpg` (42.5 s) | | 1080p frames from the run. |
| `browser_brute_game.jpg` | | Headless Chrome, browser build, `__cmb.debug.fight('b')`, 1280x720: the browser brute with the new map. |
| `brute_test/` | | 4K brute frames and the skin/white measurement (below). |

**Lighting:** directional sun at 8 lux with atmosphere, real-time sky light, height fog, auto exposure. New in round 02: four shadowless directional fill lights (0.8 lux each, pitch -30 deg, yaw 0/90/180/270) on lighting channel 1, affecting only the thug and the brute.

**Backdrop:** box facades with window strips, sidewalks, road and crosswalk stripes, built by `build_characters.py`. Unchanged.

**`brute_test/`:** `brute4k_side_f060/120/180.jpg` (side span, 3840x2160), `brute4k_orbit_f040/110/190/260/330.jpg` (orbit, 3840x2160), `brute4k_side.mp4` (3.3 s, 4K), `side_measure.json` and `orbit_measure.json` (summary plus per-frame counts), `*_flag_overlay.jpg` (worst frame per run: green = pixels judged, magenta = flagged). Method: `tools/ue_char/brute/measure_frames.py`; described in `HANDOFF.md`. A second deterministic run of each shot on `Char_Lineup_BruteMask` (brute unlit region colours, other characters unlit yellow) gives the brute's cloth pixels; skin-like = hue 8-38 deg, saturation 0.22-0.65, value >= 0.42; white-like = value >= 0.80, saturation <= 0.18.

| Run | Frames judged | Cloth px | Skin-like px | White-like px | Largest flagged region |
|---|---|---|---|---|---|
| Side span (shot 5, frames 30-198, every 3rd) | 51 | 18,692,093 | 0 | 10 (one frame) | 7 px |
| Orbit (shot 10, frames 30-378, every 3rd) | 111 | 50,134,901 | 0 | 0 | 0 |

Detector control on hand/face pixels: 24 % (side) and 92 % (orbit) flagged skin-like.

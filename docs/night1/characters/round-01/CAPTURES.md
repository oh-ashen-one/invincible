# Round 01: captures of the running lineup map

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Source:** real `-game` runs of `/Game/Tests/Characters/Char_Lineup` (UE 5.8.3, Metal, offscreen) through F1's `unreal/WebHomage/Scripts/run_game.sh`. `AWHCharShowDirector` drives the camera. Rebuild with `tools/ue_char/build_characters_headless.sh`, then capture with `tools/ue_char/capture_lineup.sh`.

**Movies:** `-movie` gives a fixed 1/60 s step, and every frame is written, so playback is smooth. It says nothing about real-time speed. Output is 1920×1080 at 60 fps. Internal resolution is auto screen percentage: 1399×787 for 1080p output according to CAPTURE.md; it was not re-measured for these runs. Motion blur is on, as in the game defaults.

**Stills:** `lineup4k_*` are from a 3840×2160 run with internal resolution 1920×1080 (perf json). GPU utilisation was 91 % from other sessions before the run, so no frame-time claim is made.

| File | Shot | Content |
|---|---|---|
| `hero_turntable_walk.mp4` (6 s) | orbit | Hero walking in place (walk clip at 1.6 m/s blend), turning 30°/s, camera orbiting at 45°/s. The first ~0.5 s show low texture mips while streaming. |
| `hero_run_side_34_hop.mp4` (10 s) | side, then 3/4 | Hero on a 9×4.2 m ellipse at 5.6 m/s (jog/run blend). Hops every 5 s (jump clip up, fall clip down, landLight on contact). |
| `hero_suit_fabric_closeup.mp4` (4 s) | close-up | Chest/shoulder at 95 cm, FOV 30. Base colour + OpenGL normal (green flipped in UE) + ORM + knit micro-normal tiled ×48, Cloth shading with fuzz sheen. |
| `thug_brute_walk.mp4` (7 s) | 3/4, then side | Thug on the hero skeleton playing the hero walk at 1.5 m/s. Brute = thug × 1.24 with `brute_basecolor` at 1.3 m/s. |
| `citizens_walk.mp4` (13 s) | wide, side, 3/4 | 4 citizens on a shared 18-bone skeleton (walk 1.08 m/s natural), 1.05–1.35 m/s. Hero and suits visible in the background. |
| `ai_suits_walk.mp4` (5 s) | wide | Claude, Codex, Gemini, Kimi and Qwen suits (new normal/ORM maps) walking in place and turning. |
| `lineup4k_00_t003.jpg` | orbit | Hero turntable, 4K output. |
| `lineup4k_01_t008.jpg` | side | Hero run, 4K. |
| `lineup4k_02_t013.jpg` | 3/4 | Hero mid-hop, 4K. |
| `lineup4k_04_t021.jpg` | close-up | Suit fabric, 4K. |
| `thug_walk_1080.jpg`, `brute_walk_1080.jpg`, `citizens_wide_1080.jpg`, `ai_suits_1080.jpg` | | Frames from the movies. |

**Lighting:** directional sun at 8 lux with atmosphere, real-time sky light, height fog and auto exposure.

**Backdrop:** box facades with window strips, sidewalks, road and crosswalk stripes, built by `build_characters.py`.

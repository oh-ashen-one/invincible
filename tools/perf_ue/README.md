# tools/perf_ue: P4 look / perf / capture tooling

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

| file | what |
|---|---|
| `run_perf.py` | real-gameplay perf at 3840x2160: one run per config (`tsr50`, `tsr67`, `native100`, or `name=SP+cvar=val`), CSV profiler + WH_PERF + top GPU passes + GPU utilisation before / during + contamination flag; `--fixed-step` = deterministic hero route; `--reanalyze` recomputes an existing directory |
| `sweep_views.sh` | perf of every static city view under one preset (finds the heaviest view) |
| `make_perf_md.py` | writes `PERF.md` of a round from the run directories |
| `capture_looks.py` | stills (S1..S8 x presets x 4K / 1080p), 60 fps clips (shader warm-up render, 0.8 s pre-roll trimmed), `NOTES.md` (neutral facts) for the critic; runs `night_tests.py` on the night S1 / S6 stills and the night swing |
| `capture_tour.py` | (round 03) ONE game session per preset and resolution visits the eight `city_shots.json` poses through the C++ shot tour (`Source/WebHomage/Look/WHLookTour.*`, `-WHLookTour=<file>`), settling 4 s per pose; `--variants <json>` sweeps live look variants (`! set / post / cvar / exec` lines) in one session; JPEGs + notes into the round folder |
| `look_spec_check.py` | (round 03) numbers of `docs/night1/look/SPEC.md` per still: L1 / L2 / L3 / L5 (mean, near-black, clipped, B-R), L10 / L11 far field of S4, L13 / L14 night pools, L17 glass p10; `--md` / `--json` |
| `sweep_report.py` | ranks the variants of a `capture_tour.py --variants` sweep against the spec lines (`<preset>_<S#>_<res>_<variant>.jpg`) |
| `round_tests.py` | writes `round-NN/TESTS.md` (spec tables for 1080p and 4K, night_tests numbers, clip_check numbers incl. L18 edge / centre sharpness, hero luma) |
| `clip_check.py` | per-frame mean Y, B-R, near-black, clipped and L18 edge / centre sharpness of a swing clip (ffmpeg decode at 960x540) |
| `night_tests.py` | night numbers: mean luma / share of pixels < 10 (`still`), light pools in the bottom third (`pools`), hero pixel-box mean luma per frame from the P3 hero-only depth mask (`hero`) |
| `scripts/city_swing_avenue.json` | traversal driver for perf (14 s warm-up, then a swing chain up the avenue) |
| `scripts/city_swing_clip.json` | traversal driver for clips (airborne start, swing chain) |
| `rebuild_city.sh` | P1's city pipeline on P4's own dev port / scratch / editor (never touches P1's) |
| `rebuild_look.sh` | headless `Scripts/build_look.py` (editor closed) |
| `launch_editor.sh`, `job_server.py`, `uejob.py` | P4 editor (MCP 8774, `-RenderOffScreen -NoSound`, waits while 3+ editors run) with a file-based job server; `uejob.py <script.py> [k=v]` runs a Python file in it |

Scratch (never committed): `/Users/midir/sm2-n1/_scratch/look/` (export, textures, job dir, captures). See `docs/night1/look/HANDOFF.md`.

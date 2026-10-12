# F3 browser baseline: handoff

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

**State (round 1, closed):** all five deliverables exist in this folder: `BUILD.md`, `stills/` (26 shots + 6 time-of-day variants at 3840x2160, 40 suit close-ups), `clips/` (9 clips, 111 MB), `PERF.md`, `PLAYTEST.md`. Game code was not changed. Nothing here is a critic verdict; it is a measured "before".

**How to run / capture:** see `README.md`. Dev port 5201 only; own headless Chrome (Playwright `channel: 'chrome'` passes `--headless`, which is the new headless mode on Chrome 154; scratch `--user-data-dir` under `_scratch/baseline/`); one scenario per `MODE=perf` invocation. `MODE=film` clips are frame-stepped (deterministic), `MODE=perf` is real time.

**Open issues found (details, evidence and timestamps in `PLAYTEST.md`):** camera falls to a top-down view under tree canopy and stays there; camera can end up inside the hero's head; texture-unit overflow (17 > 16, the `SpiderSuit` program: fabric + symbiote mask + PBR maps + 6 shadow cascades; about 90 warnings per second of play); Gemini and Qwen suit emblem repeated on the back; crack / stair-step dash artifacts on all five Tripo skins and on citizen clothing; hero stops dead when run head-on into a parked car's side (`clips/carBlock.mp4`); crowd corner clusters all play the same raised-arms loop and interpenetrate; roll-up shutter moire; black hole in a bus rear; night lighting crushes the hero and streets; `?shot=` destruction compositions are not deterministic (pedestrians walk into frame, hydrant / bench not in frame).

**Caveats a reader must keep in mind:**
- The GPU is shared: every perf run was contaminated (other sessions' Unreal editors and Chrome held the GPU at 40-100 % before this game started). Frame-time numbers are a pessimistic bound; re-run on a quiet GPU before quoting them as the browser game's ceiling (`QUIET_WAIT=<s>` waits for < 25 %).
- Perf numbers are rAF frame deltas plus `EXT_disjoint_timer_query_webgl2` GPU time per frame in a non-throttled headless Chrome with vsync / frame-rate limit disabled, not a display-locked 60 Hz; rAF under-reports and the GPU timer over-reports under time-slicing, so quote both.
- Clips are frame-stepped (about 0.2-0.5 fps of wall time), not real-time footage.
- Pointer lock cannot be entered in headless Chrome, so camera turning is injected through `ctx.input.mouse.dx`; the 24 "pointer lock" page errors in `fight` come from that.
- Reference images stay in the private `spiderman-learnings` repo; nothing from it is committed here.

**Next gap for whoever continues:** re-run `MODE=perf` on a quiet GPU (the P4 piece owns the 60 fps question); if the browser game is still needed as a comparison target after the Unreal work, fix the camera canopy flip and the 17-sampler program first, because they show up in every clip.

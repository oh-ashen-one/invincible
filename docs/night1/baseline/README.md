# Night 1 / F3 — browser game baseline ("before" record)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation, nothing here is meant to infringe. See `DISCLAIMER.md`.
> Reference images/videos of the real game are NOT in this repo (private repo `spiderman-learnings`); documents here only cite their paths.

Honest record of the **browser** game (Vite + three.js, branch `night1/browser-baseline`, game code untouched) before the Unreal work, captured by an agent playing the game with real input events in its own headless Chrome.

| file | what |
|---|---|
| `PERF.md` | median / p95 / p99 frame times, hitches, internal resolution, GPU utilisation before each run, contamination flags |
| `PLAYTEST.md` | numbered bugs with clip/still + timestamp, console errors, asset-branch checks (skins, T-poses, floating props), biggest gaps vs Marvel's Spider-Man 2 |
| `BUILD.md` | `npm ci` / `npm test` / `npx vite build` results (raw logs in `logs/build/`) |
| `stills/*.jpg` | every `?shot=` composition at **3840x2160** (plus `&tod=sunset` / `&tod=night` for street, swing, parkHigh); `stills/skins/` = every suit x front / 3/4 / back / side / head+chest at 1920x1080; `stills/bugs/` = bug close-ups |
| `clips/*.mp4` | gameplay clips, 1920x1080, h264, <= 15 MB each (see "clip fps" below) |
| `logs/*.json` | per clip: marks with game-time stamps, player state every 0.25 s, console messages; `logs/skinclose.json` per-suit console |
| `perf/*.json` | per perf run: frame-time stats + every raw frame delta and GPU time per frame, GPU utilisation samples; `perf/v1_raf_only/` first pass without GPU timers; `perf/shots_perf.txt` `tools/perf.mjs` output |
| `tools/` | `playtest.mjs` (scenario runner: film / perf modes), `skinclose.mjs`, `carprobe.mjs`, `perf_table.py`, `probe.mjs`, `texunits.mjs` |
| `SHOTLIST.md` | every clip / still with the reference it should be compared with |
| `HANDOFF.md` | state, caveats, next gap |

## Clip fps — what "60 fps" means here
Clips are **frame-stepped**: `ctx.manualStep = true`, every video frame is one `ctx.stepFrame(1/60)` (game time advances exactly 1/60 s) followed by a CDP screenshot piped to ffmpeg. The files therefore play back at exactly 60 fps of game time, but were **captured at about 0.2-0.5 fps of wall time** (3-5 s of wall time per game second at 1080p). They are not real-time footage; real-time frame times are in `PERF.md`. Input is real: CDP `Input.dispatchKeyEvent` / `dispatchMouseEvent` for every key and mouse button. Camera turning uses `ctx.input.mouse.dx` (pointer lock cannot be entered in headless Chrome). Two scripts (street / crowd) steer the camera yaw with a small autopilot (`a.goto`, `window.__steer`) so the run does not end in a wall; W / Shift / E / Space / RMB are still real key events.

## Reproduce
```
cd <worktree> && npm ci
npx vite --port 5201 --host 127.0.0.1 --strictPort &          # F3 dev port
MODE=film node docs/night1/baseline/tools/playtest.mjs swingChain trickZip wallRun street fight water skins crowd carBlock
MODE=perf W=3840 H=2160 QUIET_WAIT=30 node docs/night1/baseline/tools/playtest.mjs swingChain   # one scenario per invocation (GPU load is read before Chrome starts)
node docs/night1/baseline/tools/skinclose.mjs
python3 docs/night1/baseline/tools/perf_table.py
W=3840 H=2160 URL=http://127.0.0.1:5201/ OUT=/Users/midir/sm2-n1/_scratch/baseline/stills_png node tools/shot.mjs street swing 'street&tod=night' ...   # stills (PNG, then converted with ffmpeg -q:v 4 to stills/*.jpg)
```
Stop the dev server and Chrome when finished (`pkill -f "vite --port 5201"`; the tools launch and remove their own Chrome profiles under `/Users/midir/sm2-n1/_scratch/baseline/`).

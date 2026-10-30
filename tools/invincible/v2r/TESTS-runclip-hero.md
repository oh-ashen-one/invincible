Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.

# run_clip.sh (hero): tests without the reader (2026-10-30)

No GPU, no engine, no reader training, no `video2rig run`/`check`/`review`. Blender 5 `-b --factory-startup`, one process at a time
(nothing else of ours running; the Blender slot rule found a free slot at once). `$V` = `tools/invincible/v2r`, `$P` = `/Users/midir/spider-man-2-invincible/Local/video2rig/hero`.
Evidence of the runs below (logs, state, strip, mp4, PIPELINE.log, the refine JSON): `$P/work/runclip_test/` (gitignored `Local/`).

## a. Selftest (system bash 3.2.57)

```
/bin/bash $V/run_clip.sh --selftest
RUN_CLIP_SELFTEST PASS (parsers: check, run, refine, export, size; wiring: airborne, stance, slot, version, refine flags, neutral path)
```
Covers the Brute's parser cases plus: airborne list (Hover Fly LaunchUp BoostHold BoostLaunch Brake Takeoff yes; LandHero GroundIdle no),
stance dir (rig-stand for LandHero/GroundIdle, rig otherwise), Blender slot rule (0/2/3/5 Blender, with and without an UnrealEditor),
`<Clip>_v2r_v<N>` version parsing, refine flag assembly (`--loop --no-plant`, `--return-to-stance --return-target stance
--stance-yaw-align [--no-plant]`, `--frame0-return`, `--plant`, `--plant-floor-tol`) and the neutral project path. A deliberately
wrong expectation makes it print `SELFTEST FAIL ver1 ...` and exit 1 (checked).

## b. Size gate alone

```
/bin/bash $V/run_clip.sh $P hover_sd_v2 Hover --loop --to size
[run_clip Hover hover_sd_v2] step size: size_gate.py (limit 1.3x)
[run_clip Hover hover_sd_v2] size ok: scale 1.05
# work/hover_sd_v2/size.log
SIZE_GATE hover_sd_v2 PASS width 1.15 height 1.03 peak_frame 56 scale 1.05 metric area
```
exit 0, 7.5 s. The traced command (`bash -x`) is `V2R_HOME=/Users/midir/video2rig-hero /Users/midir/video2rig/.venv/bin/python
$V/size_gate.py /Users/midir/spider-man-2-invincible/Local/v2r-hero hover_sd_v2 --max 1.3`: the project goes in through the neutral symlink.

## c. refine -> export -> sheet -> log on the synthetic fit (no reader)

```
cp $P/work/export_test/test_fit.blend $P/Hover_v2r_v1.blend
/bin/bash $V/run_clip.sh $P hover_sd_v2 Hover --loop --from refine --refine-args "--xfade 12"
[run_clip Hover hover_sd_v2] step refine: refine_hero.py --loop --no-plant
[run_clip Hover hover_sd_v2] WARN refine: toe_min -1113.8 mm (feet through the floor)
    REFINE trim {"threshold": 0.4, "still_tail_start": 120, ...}
    REFINE spikes {}
[run_clip Hover hover_sd_v2] refine ok: REFINE_GATE seam 1.11 foot_drift_mm n/a toe_min_mm -1113.8 peakhand_L 60 peakhand_R 58
[run_clip Hover hover_sd_v2] step export: export_hero_clip.py -> $P/out-glb
[run_clip Hover hover_sd_v2] export ok: EXPORT_GATE max_vertex_delta_mm 0.0006 PASS -> $P/out-glb/Hover_v2r_v1.glb
[run_clip Hover hover_sd_v2] step sheet: CPU close-up (tq) of the exported glb -> strip + mp4
[run_clip Hover hover_sd_v2] sheet ok: $P/work/hover_sd_v2/new_tq_strip.jpg (49 frames), $P/work/hover_sd_v2/new_tq.mp4
[run_clip Hover hover_sd_v2] step log: append to PIPELINE.log
CLIP Hover hover_sd_v2 check n/a n/a fit n/a warn n/a outline n/a refine 1.11 n/a -1113.8 export 0.0006 PASS blend $P/Hover_v2r_v1_refined.blend glb $P/out-glb/Hover_v2r_v1.glb
```
exit 0, 33 s wall. Gate lines in the logs: `REFINE_GATE Hover seam 1.11 foot_drift_mm n/a toe_min_mm -1113.8 peakhand_L 60 peakhand_R 58`,
`EXPORT_GATE Hover_v2r_v1 max_vertex_delta_mm 0.0006 frames 6 PASS`, `EXPORT Hover_v2r_v1 wrote .../out-glb/Hover_v2r_v1.glb (30.9 MB) frames 121 seconds 4.000`.
Same numbers as TESTS-refine-hero.md section 1 (the fixture is not on the floor, so the toe warning is expected; check/fit show n/a
because steps check/run were not run). The strip (`new_tq_strip.jpg`, 10 tiles of 49 frames, tq camera) shows the hero hovering upright;
`new_tq.mp4` is 49 frames at 12 fps.

Cleanup (the script moves nothing; everything it wrote was copied to `work/runclip_test/` first, then removed):
- removed from `$P`: `Hover_v2r_v1.blend`, `Hover_v2r_v1_refined.blend`, `Hover_v2r_v1_refined.json` (moved to work/runclip_test/), `out-glb/Hover_v2r_v1.glb` and
  the `out-glb/` directory (created by the run), `PIPELINE.log` (created by the run)
- removed from `$P/work/hover_sd_v2/`: `size.log refine.log export.log sheet.log pipeline.state new_tq_strip.jpg new_tq.mp4 closeup/`
  (the directory's own earlier files `check.log front_small.mp4 look_*.* sheet*.jpg` were not touched)
- kept: `$P/work/runclip_test/` (copies of the logs, state, strip, mp4, PIPELINE.log, refine JSON)

## Census check (why `v2r_cmd.py`)

gpu_slot's ML pattern (`~/.cache/gpu-slot/bin/gpu_slot.py` DEFAULT_ML_PAT) includes `\bvideo2rig\b`. With the specified defaults the v2r
command line still contains it (`/Users/midir/video2rig/.venv/bin/python` and the fork `/Users/midir/video2rig-hero`), checked with the regex:
```
True   /Users/midir/video2rig/.venv/bin/python $V/v2r_cmd.py /Users/midir/video2rig-hero check $H/Local/v2r-hero hover_sd_v2
False  /opt/py/bin/python $V/v2r_cmd.py $H/Local/v2r-fork check $H/Local/v2r-hero hover_sd_v2     (neutral python and fork paths)
```
So the neutral project symlink alone does not keep `check`/`run`/`review` out of the census; the interpreter and fork paths would also need
neutral names (`--python`, `--fork-dir` accept them). size_gate.py is a python process with the same match (the Brute's was too); Blender steps are counted as Blender, not as ML.

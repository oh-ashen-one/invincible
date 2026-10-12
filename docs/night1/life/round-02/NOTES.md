# P6 City life round 02: capture notes

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

The round was interrupted by the 23:08 kernel panic (WIP committed as 713f856 / 4d094f6) and resumed. The WIP captures in git history (stills, three clips, perf) were taken with the pre-interruption code and are superseded: they showed a box truck filling the S1 camera at t = 28 s (people detected: 1 in the S1 4K still), a signal clip whose green arrived at clip t = 7 s, and 60 looks with twin heads.

## Which build produced which file (all real `-game`, offscreen, `Scripts/run_game.sh`, inside `gpu_slot.sh capture`; native internal resolution, `r.ScreenPercentage 100`)

| build | content | files |
|---|---|---|
| B2 (crowd 1300 / 860 per km, 100 looks, corridor clear) | before the pink head-covering recolour of citizens 17 / 20 | `stills/S2_avenue_*.jpg`, `swing_clip_1080p60.mp4`, `probe_S2_*.txt`, `probe_swing.txt`, `feet_S2_*.csv` (the crowd is not visible in these views: detector people 0-3 at S2 and 0 in the swing clip; traffic code and data are identical to B3) |
| B3 (= committed HEAD of this round) | final | `stills/S1_street_*.jpg`, `street_clip_1080p60.mp4`, `signal_clip_1080p60.mp4`, `probe_S1_*.txt`, `probe_street.txt`, `probe_signal.txt`, `feet_S1_*.csv`, `feet_clip.csv`, perf runs |

Still times: every still view also shoots game t = 12, 16, 20, 24 s (1080p run); those four frames per view are in `series/` (the detector series of the spec table uses them together with the published t = 28 s still). S1 series = B3, S2 series = B2.
Clips: 1920x1080 at 60 fps, fixed 1/60 s steps (`-movie`), 2.5 s hold at the start pose trimmed, crf 17 (each <= 15 MB). Contact strips: `strip_street.jpg`, `strip_swing.jpg`, `strip_signal.jpg` (1 frame per second).
S1 stills use `-WHLifeClearAhead=12` (no moving car drawn in a 12 m corridor ahead of the S1 camera, which stands in a traffic lane); the clips do not.

## Measurement

Detector (`tools/life/detect_counts.py`, YOLO11x-seg, conf 0.35, imgsz 1920, CPU device): `detector.txt`, `detector.json`; tables: `SPEC_TABLE.md`; gait / feet: `feet_analysis.json` (street clip), `feet_analysis_S1_4k.json`, `feet_analysis_*.txt`; IP: `ip_check.txt`.
The S1 / S2 still series (t = 12-24 s in `series/`, t = 28 s = the published still) feeds the medians; per-file numbers are in `detector.txt`.

## Known limits of this evidence

* Detector counts on stills depend on when the still is taken (S1 24-30 people over five times, S2 12-19 vehicles); medians are over five times, not a promise for every frame.
* S2 vehicle count (still series median 13) is one below the 14-22 range; the swing clip (median 17) is the fuller C6 test.
* Twin looks: a pair of identical looks within 30 m occurs in 8 of 41 S1 samples (probe, people >= 28 px, occlusion-tested); none in the street and signal clips.
* Foot planting: ankle-bone displacement only.
* Two soft glows of unidentified origin are in the frames (green-white smear over the S1 road centre, present in the round-01 S1 stills too; green haze on a P1 litter bin at the start of the street clip). They are at ground level, not at the 3-8 m of the signal lens discs; not investigated further (P1 / P4 territory).

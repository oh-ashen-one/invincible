# TRAVERSAL-SPEC (P3 traversal + camera) — fixed targets, measured from refs

> Homage fan game; not affiliated with Marvel, Sony or Insomniac. Refs are private (`~/spiderman-learnings/refs`), never copied into the fork.
> Written 2026-09-29 by spec agent B. Every number below was measured on the ref files named. "Unmeasurable from refs" = no number is set from the refs.
> Instruments (run the SAME tool on refs and on our captures): `specs/tools/` — `ref_hero_dets.py` (YOLO11x-seg person boxes, 5 fps),
> `vp_cam.py` (roll/pitch/FOV/yaw from vertical + forward vanishing points, 10 fps), `nearflow.py` (near-field coverage by optical flow),
> `hero_height_stats.py`. Raw ref data: `specs/data/` (picks_*.json = hand-confirmed hero centres; *_cam.csv; d_*_dets.json).
> Tool env: `uv venv v --python 3.12 && . v/bin/activate && uv pip install ultralytics opencv-python-headless scipy` (weights auto-download).
> Ref clips are 60 fps containers with **30 fps content** (48–55 % duplicate frames, measured): compare motion at 30 fps.

## 0. Scope rules (binding)
- **From round 10, every P3 capture runs in the real lit city `Look_Midtown_golden` (P4 map)**, not `Trav_Canyon`. Gray-box captures are
  evidence for nothing on axes T-A..T-D. The critic scores only motion/camera/web/moves; city and light defects are logged to P1/P4.
- **Body-animation limits caused by the missing clip set** (no wall-run cycle, no landing tiers, no dedicated sprint/lean run, no
  trick library beyond the browser clips) are a **P2 dependency**, tracked in `CHARACTERS-SPEC.md` §5. They are listed, not scored against P3.
  P3 is still scored on blending/timing/pose-to-rope alignment it controls (T-E lines marked P3).
- Measurement window: the 15 s `a_swing_chain` + `swing-chain-2`; stats over any 8 s window unless stated.

## 1. Swing rhythm and web (T-A, T-C)
| id | target | measured from |
|---|---|---|
| T1 | Rope-held time per swing **0.5–1.6 s** (not 1.2–1.8) | hero-crop sheets at 10 fps: canyon-chase ropes 2.2–2.7, 2.8–3.3, 3.9–5.4 s; avenue-midday 3.6–4.5, 7.0–7.7 s; avenue-traffic 4.3–5.4 s |
| T2 | Attaches per 8 s: **2–4**; attach→next-attach interval 0.6–3.3 s | same sheets: canyon 3–4 attaches, midday 2–3, traffic 2 in 8 s |
| T3 | Rope on screen **25–45 %** of chain time (≥75 % is NOT the ref) | canyon ≈42 %, midday ≈25 %, traffic ≈20 % of 8 s |
| T4 | Web-less phases up to **3.1 s** are allowed ONLY if the body is in a trick/flip/dive: silhouette differs at every 0.1 s sample. A web-less phase > 0.6 s with a held pose fails. | canyon 0.6–2.1 s and 5.5–7.9 s, midday 0.3–3.4 s and 4.5–6.9 s: pose changes in every 0.1 s tile |
| T5 | Rope on screen runs hand → frame edge; **anchor point need not be in frame** | 6/6 grid-read rope frames (canyon 4.3/5.2, avenue-traffic 4.5/5.0, midday 4.0, sunset 4.1 s): rope exits the top edge |
| T6 | On-screen rope angle from vertical **8–54°**, typical 15–20°; rope 2–4 px wide at 1080p, straight, readable against sky and facade | same 6 frames, grid-read |
| T7 | Altitude swing: every ≤ 4 s the hero goes from roofline height to **1–4 storeys above the street** and back | midday 0.3→3.6 s (above roof → over crosswalk), canyon 0.9→4.3 s; storeys counted on frames. Metres: ≈ 25–45 m at 3.3 m/storey (derived, not telemetry) |
Checkers: `cadence_check.py` (T1–T4: change targets to these), `drop_test.py` (T7: require ≥ 1 release→low drop ≥ 20 m per 4 s and low
point 3–13 m over street), new `rope_px_check.py` (T5/T6: projected rope width in px, angle from vertical, visible from hand to edge).

## 2. Framing and camera (T-B)
| id | target | measured from |
|---|---|---|
| T8 | Hero bbox height / frame height: **median 0.15–0.23, p10 ≥ 0.09, p90 ≤ 0.38**, never < 0.05 while swinging | 104 hero boxes (YOLO masks + 35 hand-read): canyon med 0.229 (p10 .139, p90 .378), midday .152, traffic .160, low-street .168; pooled p10 .121, p50 .185, p90 .302; min .05 |
| T9 | Hero centre x: **p5–p95 inside 0.44–0.56** (hero stays horizontally centred) | 145 hand-confirmed centres: canyon .49–.52, midday .49–.51, traffic .46–.51, low-street .49–.52 |
| T10 | Hero centre y: **p5–p95 spread ≥ 0.20** over 8 s, range 0.20–0.70 | canyon .20–.65, midday .35–.59, traffic .35–.68; low-street .52–.60 (low-glide clip, exempt) |
| T11 | Camera pitch in avenue swings: **median 4–12° down, p95 15–30° down, p5 between 10° up and 3° down** | vp_cam: canyon p50 5.1/p95 24.1/p5 −5.2; sunset 9.1/16.7/1.2; traffic 5.8/18.4/3.2; midday 1.5/15.1/−9.8; river-to-canyon 10.3/27.7/−9.9 |
| T12 | Camera yaw off the avenue axis: **median 2–10°, p90 10–25°** (composition is off-axis without moving the hero) | vp_cam yaw_off: sunset p50 9.4/p90 13.7, traffic 2.0/14.2, canyon 2.0/16.3, river-to-canyon 4.6/20.8 |
| T13 | Roll: **|roll| median ≤ 1.5°, p90 ≤ 10°, max ≤ 20°** outside dives. Roll is allowed, not required | vp_cam: canyon p50 .1/p90 3.5/max 7.8; sunset .3/1.1/1.5; traffic .2/.8/17.2; midday .3/2.9/11.7; river .8/10.1/19 |
| T14 | Horizontal FOV **100–110°** (vertical ≈ 68–76° at 16:9) during swings; ±10 % method error | vp_cam focal from orthogonal VPs: canyon hFOV 100 (IQR 93–104), sunset 108, traffic 109, midday 109, river 108 |
| T15 | Camera distance ≈ **4–7 m** (derived: T8 median, 1.2–1.8 m pose extent, T14 vFOV). Not measured directly | derived |
| T16 | Hero in frame ≥ 94 % of samples of a chain | traffic 75/80 samples (one 0.5 s cut-away 3.3–3.8 s) |
Checkers: `px_check.py` / `cam_check.py` extended with T8–T10 percentiles (hero pixel mask), `vp_cam.py` on our 1080p capture for T11–T14
(same instrument as refs), telemetry `pcm_pitch`, `pcm_yaw` vs avenue heading, `pcm_roll`, `pcm_fov` for the engine-side check.

## 3. Facade clearance vs weave — resolved (r07 vs r08)
- r08's "hero x alternates 30 %–70 %, spread ≥ 30 %" is **contradicted by the refs** (T9: spread 3–5 %). Our r08 spread (46–56 %) was already wider than the ref. Void.
- r07's "no wall covers > 30 % of screen" is **contradicted by the refs**: near geometry is part of the look.
- What the ref does: hero centred, camera yawed 2–25° off axis (T12), and **one side third of the frame is filled by fast-moving near geometry
  (facade or trees) in 42–78 % of frames**. Measured with `nearflow.py 8` (median-removed Farneback flow over 1/30 s, 480×270, > 8 px):
| id | target | measured from |
|---|---|---|
| T17 | Near-field coverage (whole frame): **p50 0.20–0.45, p90 ≤ 0.55** | canyon .28/.45, midday .23/.46, traffic .32/.53, low-street .44/.52, sunset .33/.46, river .35/.51 |
| T18 | Max side-third coverage: **p50 0.45–0.65**; frames with a side third > 50 % covered: **40–80 %** | canyon 51 %, midday 55 %, traffic 51 %, low-street 78 %, sunset 64 %, river 63 %, riverside 42 % |
| T19 | Hero never occluded (hero mask pixels behind geometry = 0) and camera never inside geometry | safety; ref never shows either (all sheets) |
- **Corridor in metres from canyon centre: unmeasurable from refs** (no depth). Engineering bound until a depth probe exists: hero ≥ 3 m and camera
  ≥ 1.5 m from any facade (hard, `facade_check.py`), and the lateral offset tuned so T17/T18 land in band. Both T17/T18 AND T19 must hold.

## 4. Speed read and blur (T-B)
| id | target | measured from |
|---|---|---|
| T20 | Edge/centre sharpness (mean |Laplacian| of 12 % side strips ÷ centre 40 % box): **p50 0.20–0.65** while swinging | canyon .21, low-street .20, riverside .42, midday .52, traffic .55, sunset .64, river .64 |
| T21 | Hero sharper than its surroundings: hero-mask |Lap| ÷ 16 px ring **median ≥ 1.0** | canyon .99, traffic 1.48, midday 2.29, low-street 5.21 (from d_*_dets.json) |
Checker: new `blur_check.py` (both ratios on the 1080p capture, hero mask from the pixel-mask capture).

## 5. Moves (T-D) and wall-run
| id | target | measured from |
|---|---|---|
| T22 | Wall-run camera pitches **up 20–65°** during the vertical run | vp_cam: wallrun-glass-midday 2.0–6.7 s 21°→64° up; wallrun-empire 2.0–3.5 s 25–56° up |
| T23 | Release trick: silhouette against sky with hero ≥ 0.10 of frame height | midday 0.3–1.2 s hero .11–.16 against sky (hand-read) |
- Landing settle time, dive speed-streak onset, zip duration: **unmeasurable from refs so far** (not timed in this pass); CRITIC_GUIDE text stands as description only.

## 6. Axis → spec lines (critics score against these)
| axis | spec lines | notes |
|---|---|---|
| T-A Swing arc & rhythm | T1, T2, T4, T7 | cadence judged on 8 s windows |
| T-B Camera | T8–T21 | T17–T19 replace every earlier clearance/weave demand |
| T-C Web read | T3, T5, T6 | anchor-in-frame demands (r02, r04) are void (T5) |
| T-D Moves & transitions | T4, T22, T23 | |
| T-E Body animation | T4 (P3: pose variety, rope alignment ±15° at arc bottom — builder-owned) | clip-set gaps → P2 dependency, not scored here |
Critic rules: score each axis only against its lines; you may ADD a gap you observe (cite file@time); you may NOT contradict a line unless
you run the named instrument on the ref and show the ref violates it. Any 8+ score needs every line of that axis passing on our 1080p capture.

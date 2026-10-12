# P4 Look, lighting, post, perf: shot list (Night 1)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Nothing here is meant to infringe.

Target: the look of Marvel's Spider-Man 2's Manhattan: warm physically plausible sun, deep blue skylight, aerial perspective and
haze layers, strong bounce light in the avenue canyons, glossy glass reflections, bloom / lens character, filmic tonemapping,
motion blur, and 60 fps at 3840x2160 output on the M3 Ultra with the internal resolution disclosed.

## Stills: the city views under each preset

The eight views of `unreal/WebHomage/Scripts/city_shots.json` (P1 SHOTLIST, `docs/night1/city/SHOTLIST.md`) are rebuilt as
`/Game/Tests/Look/Look_View_<preset>_<S#>` by `Scripts/build_look.py` for each preset, so a still differs from its P1 counterpart only by the
lighting rig. References: `~/spiderman-learnings/refs/streets/` (private repo, never committed here), the same files P1 lists.

| id | view | preset(s) | reference focus |
|---|---|---|---|
| S1_avenue_street | avenue canyon at street level looking north | midday, golden, night | canyon bounce light, sun shafts at the end of the avenue, street level exposure |
| S2_avenue_swing | 42 m swing view down the avenue | midday, golden, night | haze layers in depth, glass reflections of the sky |
| S3_rooftop_watertower | rooftop with a timber water tank, towers behind | midday, golden, night | sun colour and shadow softness on rooftop clutter |
| S4_perch_skyline | perch on a 300 m glass tower, skyline to the north-west | midday, golden, night | aerial perspective over kilometres, cloud layer, night city lights |
| S5_timessq_south | bowtie from the red steps looking south | midday, golden, night | billboard / neon emission at night, bloom |
| S6_timessq_street | bowtie at street level looking north | midday, golden, night | night street level, lens character |
| S7_sunset_crosstown | 30 m up looking west down a cross street into the sun | midday, golden, night | golden hour beams, volumetric fog, lens flare |
| S8_aerial_midtown | high aerial over midtown toward the park | midday, golden, night | distance haze, sun angle on roofs |

Each is captured at 3840x2160 and 1920x1080 (native internal resolution, `r.ScreenPercentage 100`) at game time 20 s
(`tools/perf_ue/capture_looks.py`), after the eye adaptation, Lumen scene and TSR history have settled.

## Clips: real gameplay per preset

`swing_<preset>.mp4`: 1920x1080, 60 fps (fixed 1/60 s step, every frame dumped), 12 s, <= 15 MB. The P3 traversal hero
(`Scripts/build_traversal.py` builds the hero; `-WHTravScript=tools/perf_ue/scripts/city_swing_clip.json`) starts 35 m over the avenue
at 22 m/s northward and web-swings with the deterministic autoChain rhythm through the real city (map `Look_Midtown[_golden|_night]`).

## Perf (real gameplay)

`tools/perf_ue/run_perf.py`: the same hero replays `tools/perf_ue/scripts/city_swing_avenue.json` (14 s standing warm-up, then a
sprint, jump and continuous swing chain up the avenue) at 3840x2160 output with `r.ScreenPercentage` 50 (TSR, 1920x1080 internal),
67 (2573x1447) and 100 (native). Numbers, GPU utilisation before each run and the top GPU passes: `round-NN/PERF.md`.

## Round 02 additions (night tests and spec numbers)

- Night stills S1 and S6 (street level) are measured by `tools/perf_ue/night_tests.py` (round-1 critic tests: mean luma, share of pixels below 10/255, distinct light pools in the bottom third with peak >= 120 and
  valley <= 40) and, for every still of every preset, by `tools/perf_ue/look_lum_check.py` (LOOK-SPEC L1..L8, L13, L14: mean, near-black share, clipped share, B-R, lit blobs in the bottom half, bottom-third p90 / p10).
- `swing_night.mp4`: per frame, the mean luma inside the hero's pixel bounding box (telemetry `px_left/right/top/bottom` from the P3 hero-only depth capture) is written to `swing_night_hero_luma.json`.
- Every clip is preceded by an unrecorded low-resolution shader warm-up render and starts after a 0.8 s pre-roll (exposure / Lumen / TSR settle) that is trimmed from the video and the telemetry.
- All captures run inside `gpu_slot.sh capture`; perf under `gpu_slot.sh perf` (`round-02/perf_gpu*.json` sidecars).

## Round 03 additions (shot tour, spec checker, presets v2)

- Stills are now captured by `tools/perf_ue/capture_tour.py`: ONE game session per preset and resolution visits the eight poses of `Scripts/city_shots.json` (C++ `UWHLookTour`, `-WHLookTour=<file>`), waits 4 s (first pose 10 s, at least 90 frames) at each for exposure / TSR / Lumen, and saves a back-buffer PNG per pose
  (same maps `Look_Midtown[_golden|_night]`, same traversal game mode and hero, the hero teleported to the view's `player` position). `capture_looks.py` still exists for the per-view maps and for the swing clips.
- Live tuning: `capture_tour.py --variants <json>` sweeps many look variants in one session (`! set / post / cvar / exec` lines of the tour file, see `Source/WebHomage/Look/WHLookTour.h`); `tools/perf_ue/sweep_report.py` ranks them against the spec lines.
- Spec checker: `tools/perf_ue/look_spec_check.py` (L1 / L2 / L3 / L5 means, near-black, clipped, B-R; L10 / L11 far field of S4 with P1's `spec_regions.json` boxes; L13 / L14 night pools; L17 glass p10) and
  `tools/perf_ue/round_tests.py` (writes `round-NN/TESTS.md`, adds night_tests.py and clip_check.py numbers for the swing clips).

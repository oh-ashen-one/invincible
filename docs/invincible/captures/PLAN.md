# Invincible flight capture suite — plan

Homage fan game; not an official Marvel, Sony, Image Comics or Skybound product. No owner gameplay acceptance is implied by any capture.

## What runs

- Cases: `tools/invincible/make_flight_cases.py` (single source) writes `tools/invincible/flight_cases/*.json` (UWebTravScript format) and
  `cases.json` (quit time, extra args, mechanical checks). Map `/Game/Showcase/Maps/Manhattan_Island`, day.
- Runner: `tools/invincible/run_flight_suite.py <tag> [--sim] [--cases fl01,fl05]`. One real `-game` engine per case, always through
  `tools/gpu/gpu_slot.sh capture` (shared FIFO, PAUSED / holders / cap respected; never bypassed). Stops after two runs without telemetry.
  - `--sim`: `-nullrhi`, telemetry only (cheap; island r03 showed nullrhi telemetry is bit-identical to a rendered run). Used to iterate.
  - default (render): playable profile + Fast preset, 1920x1080, 100 % internal, TSR, fixed 1/60 s step (`-benchmark -fps=60`),
    `-dumpmovie` + `-WHMovieAsync`, 1.5 s pre-roll cut, `-WHSuit=invincible`, flight on (default), rescue off except fl17.
- Checks: `tools/invincible/check_flight.py` — per-case gates from `cases.json` plus suite-wide sanity (camera inside geometry, hero off
  screen, below the floor, position teleports, log errors). Measured numbers are printed on failure. A pass is necessary, not sufficient.
- Outputs: `docs/invincible/captures/<tag>/` — `<case>.mp4`, `<case>_sheet.jpg` (8-frame contact sheet), `<case>_telemetry.csv`,
  `CHECK.json`, `CHECK.md`, `RUN.json` (source head, dirty flag, mode). Raw frames stay in `~/sm2-invincible-cache/<tag>/` (disposable).

**Fixed-step footage is not real-time FPS proof.** Real-time performance is only measured from a game launched in the logged-in desktop.

## Cases (17)

| case | what it shows | key gates |
|---|---|---|
| fl01_takeoff_hover | ground takeoff, hover climb, strafe, gentle touchdown | takeoff + hover subs, grounded at end, no crater |
| fl02_takeoff_to_fly | fly + climb from the ground straight into a climbing fly line | takeoff + fly, >= 45 m/s, >= 10 m gained |
| fl03_cruise_hands_off | fly held, no look input, 60 m over 5th Av | altitude drift <= 12 m |
| fl04_boost_sonic | boost 1-8 s, one sonic boom, glide back to cruise | >= 140 m/s, exactly one boom |
| fl05_bank_turns | stick right / left at cruise | peak bank >= 20 deg |
| fl06_look_steer | steering with the camera only (yaw, pitch up, pitch down) | heading change >= 60 deg |
| fl07_climb_dive_keys | climb / descend keys pitch the fly line | >= 15 m gained |
| fl08_brake | instant stop into a hover | brake entry, end speed <= 3 m/s |
| fl09_dash | three dashes from a hover | 3 dash entries |
| fl10_slow_flight | stick back = slow flight | 12-24 m/s after 2 s |
| fl11_slam_crater | slam from a 60 m hover | one hero landing, grounded |
| fl12_fast_land | steep fast fly into the street | one hero landing without the slam key |
| fl13_soft_land_walk | hover descent, touchdown, walk, take off again | no crater, walked |
| fl14_breach_cruise | turn into a facade at cruise | >= 1 breach |
| fl15_breach_boost | boost into a block | >= 1 breach, >= 110 m/s |
| fl16_slow_facade_slide | slow flight into a facade | no breach |
| fl17_rescue_crane | rescue wave (seed 1977): climb over the roofs, brake over the crane load, drop onto it, set it down | >= 1 life saved |

fl17 route: the seed-1977 wave with the hero idle at Times Square places the crane load at (355.7, -324.3, 135.3) m (probe log
`WH_RESCUE spawn id 2`). The case climbs at 50 deg, levels out, cruises, brakes over the load, drops onto it, then sets it down.

## Review

One fresh independent critic pass per `docs/night1/final/swing/round-13-four-fixes-final/REVIEW_PROTOCOL.md` spirit: the critic sees only
the clips / sheets / telemetry numbers, quotes defects with case + time, and never reads builder notes. Results go to `CRITIC.md` in the tag
folder and the summary into `docs/invincible/RESULTS.md`.

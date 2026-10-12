# Live look sweeps of round 03 (recipes)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Generators of the `capture_tour.py --variants` files that tuned presets v2 (each writes `<SM2_LOOK_SCRATCH>/eval/v_<name>.json`; paths are the round-03 scratch, edit `dump()`), kept as recipes for the next tuning:
- `gen_m5.py` (helper `M()`: one full midday look as `!` commands), `gen_m8.py` (histogram metering windows), `gen_m9.py` (sun strength with average metering): the midday overcast.
- `gen_g3.py` (helper `G()`), `gen_g5.py` (sky luminance factor / Mie / sun): golden.
- `gen_n1.py` (helper `N()`), `gen_n3.py` (lamp cones, storefront), `gen_n5.py` (darker ambient), `gen_n6.py` (fine tune around the baked preset): night.
Run: `tools/perf_ue/capture_tour.py --round <scratch dir> --presets <preset> --res 1920x1080 --variants <json> --timeout 6000 --work <dir>` then `tools/perf_ue/sweep_report.py --dir <scratch dir>/stills --preset <preset>`.
**Every variant must set every property that any variant changes** (settings stay in force for the following variants of the session).

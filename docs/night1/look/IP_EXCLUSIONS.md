# P4 Look: IP exclusions

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

P4 adds no copied names, logos, liveries or art.
- Night stand-in traffic (`build_look.py` step `night`): plain boxes and cylinders with a generic paint palette. No `vehicles.glb` geometry and no `vehicles_atlas*` cell or livery is used.
- Night screen glow: only the geometry (centre, normal, area) of the LED-screen quads is read (`tools/perf_ue/extract_ts_screens.py` -> `Scripts/look_ts_screens.json`); no ad texture, name or brand text is read or reproduced.
  The screens' own content stays excluded by P1 (`docs/night1/city/IP_EXCLUSIONS.md`), so the screens themselves render black; the colours are generic LED hues chosen by a seeded random pick.
  (round 03) Each screen quad additionally gets an emissive stand-in content quad (`M_LookScreen`, `mat_screen` in `build_look.py`): procedural gradient cells with a soft blob, bars that stand in for lines of text (no glyphs), an LED dot grid and a rare flash.
  No texture, no text, no logo, no imagery and nothing derived from the port's ad atlases; the material is pure maths (hash-based colours from a cosine palette tinted by the seeded LED hue).
- Stars, lamps, storefront and headlight lights are parametric (numbers in `look_presets.json`).

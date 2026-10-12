# Prepared owner playtest — October 4, 2026

The owner explicitly requested preparation **without opening Unreal**. No editor,
game, commandlet, offscreen renderer or autoplay was launched during preparation.

Source branch: `codex/owner-playtest-20261004`, based on integration `70949401`.
The playtest uses `/Game/TerrainR5b/Maps/Manhattan_Terrain` and the current integrated
gameplay module. The preserved, accepted R5b terrain composition contains the city,
terrain, golden light, traversal actors and river water. The explicit
`-WHPreparedPlaytest` option adds the current integrated Life_Actors sublevel for
crowds/traffic. Full r17 character content, including the missing suit set, is staged.

## Prepared, verified and unverified

- Native module compiled successfully against UE 5.8 on the M3 Ultra, 36 actions,
  `Result: Succeeded`; module manifest points at the new dylib.
- Required maps, hero mesh and suit set exist. All 25 package paths named by the suit
  set resolve to staged assets. SHA-256 values are in `Saved/OwnerPreview/prepared.json`.
- This is an offline existence/provenance check, not an Unreal asset-load test.
- The R5b city-geometry composition predates city r11; its referenced City meshes and
  materials come from the r11 integration content. This combination, the runtime
  Life_Actors addition and the framebuffer dimensions await the first authorized run.
- No new upstream night port, rejected r06 terrain/water/look experiments, unfinished
  island map, or unreviewed r02 tricks are included.
- No performance or gameplay-acceptance claim. First opening may compile shaders.

## Check without opening

```sh
python3 tools/owner_preview/prepare.py
python3 tools/owner_preview/play.py
```

`prepare.py --stage` can re-clone the recorded donor content on this Studio; it checks
the donor commit IDs and refuses a different task branch. Generated Content and
Binaries remain local per the repository's normal policy. Compile the native module
after source changes with `unreal/WebHomage/Scripts/build_editor.sh -MaxParallelActions=8 -NoUBA`.

## Open ONLY after the owner requests it

After fresh desktop/GPU health and ownership checks through the shared protocol:

```sh
python3 tools/owner_preview/play.py --launch
```

Default request: 3840×2160 output, 100% internal, Cinematic scalability, 30 FPS cap.
This is a frame-rate ceiling, not a measured performance result. The opt-in settings
path prevents the old 55% profile and desktop resolution from silently replacing the
requested values. User settings go to a private UserDir. The owner's 3440×1440 display
is not physically 4K; inspect the actual viewport and window fit at launch. An explicit
`--ultrawide` alternate requests 3440×1440 at 100%, and must not be described as 4K.

The launcher does not clear the existing shared PAUSED marker, bypass locks, restart
the old loop or stop other sessions' processes. The marker remained during preparation.
Resolve it through the approved recovery procedure before launch. A default invocation
checks state only; no scheduled or background launch exists.

After opening, verify: `WH_PREVIEW`, `WH_SETTINGS`, `WH_SUIT` log lines; real framebuffer
size; loaded terrain and Life_Actors; responsive controls; suit cycling; absence of
missing assets. The owner remains the judge of movement feel.

Controls from current source: WASD movement, mouse look, right mouse swing, Space
jump/release, E zip, F trick, Shift sprint, C drop/dive, T next suit, Shift+T previous
suit, Escape releases mouse / opens settings. Validate live before claiming all passed.

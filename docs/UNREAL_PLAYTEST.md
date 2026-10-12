# Unreal Engine setup and playtest

The current Unreal implementation is on [`main`](https://github.com/oh-ashen-one/spider-man-2/tree/main). It includes the integrated continuation branch. The latest full feedback/music runtime is `e9a8120c`; main also includes the final optional Times Square start. The owner authorized closeout and merge; see [the closure record](controls/project-closeout-20261012/CLOSEOUT.md).

## Get the correct source

```bash
git clone https://github.com/oh-ashen-one/spider-man-2.git
cd spider-man-2
```

The project is `unreal/WebHomage/WebHomage.uproject`, using Unreal Engine 5.8. The recorded verification host was a Mac Studio M3 Ultra. The latest owner map was `/Game/Showcase/Maps/Manhattan_Island` with the Tessera suit.

## Content and build requirements

A clean Git clone is source plus builders, not a ready-to-run Unreal binary distribution. Generated content is intentionally ignored. Read [CONTENT.md](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/unreal/WebHomage/CONTENT.md) and the [current handoff](https://github.com/oh-ashen-one/spider-man-2/blob/main/HANDOFF.md) before building.

The project keeps these entry points:

- [C++ build script](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/unreal/WebHomage/Scripts/build_editor.sh): builds the editor module with the installed engine/Xcode toolchain.
- [Content/showcase orchestrator](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/unreal/WebHomage/Scripts/build_manhattan.py): staged export, import, material, character, world and validation operations.
- [Local playtest staging](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/tools/final/swing/stage_playtest.py): produces a separate owner copy from already built content and a specified source commit.
- [Guarded launcher](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/tools/m5/guarded_preview.py): checks the shared GPU coordinator, existing owners, pause state and desktop before starting a game.

Some builders retain machine-specific source/export paths. Resolve them for your own checkout and inputs; the fresh-clone content pipeline is not presented as a one-command portable installer. The historical `m5` tool directory name does not establish the current machine's identity.

For an already prepared local owner copy, run its `Play.command`. It uses the installed Unreal Engine; it is not a standalone packaged application. The verified settings were a windowed 1920×1080 output, 100% internal scale and a 60 FPS cap. A cap is not measured sustained performance.

## Controls

| Action | Keyboard / mouse | PS5 DualSense |
|---|---|---|
| Move | WASD | Left stick |
| Camera | Mouse | Right stick |
| Swing | Hold right mouse | Hold R2 |
| Jump | Space | Cross |
| Air trick | F | Square |
| Targeted perch zip | E / middle mouse | Triangle |
| Drop / dive | C / Left Ctrl | Circle |
| Camera-direction boost (air/swing) | Q | L1 |
| Sprint | Shift | L3 |
| Pause / resume | Escape / P | Options |

Gamepad mappings are defined in [WebTravCharacter.cpp](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/unreal/WebHomage/Source/WebHomage/Traversal/WebTravCharacter.cpp). The owner session detected a DualSense as player 1, but controller recognition alone is not a comprehensive physical-input acceptance test.

## Shared-machine operation

Use a task-owned game/editor and the existing shared GPU coordinator. Preserve other sessions and never clear their pause/reservation state. The project hard cap is two renderer-bearing engines; the manual launcher is more conservative. Close the game normally when finished. For a stuck task-owned process, stop its launch/restart driver first, send SIGTERM, wait up to 60 seconds, and use SIGKILL only as a last resort. Do not start another renderer while one is stuck exiting.

Epic's native Unreal MCP is used for applicable owned-editor work after connection verification. Playing the staged game does not require enabling a new MCP server or exposing a port.

## Verification and limitations

See [the evidence index](PROJECT_HISTORY.md#verification-records) and [latest repair results](https://github.com/oh-ashen-one/spider-man-2/blob/9ad990d6ab482d5b1946b0bc9a60244eac8e320a/docs/night1/final/swing/round-13-four-fixes-final/RESULTS.md). Fixed-step videos, source checks and launch screenshots have different purposes. The records retain known occlusion, web-flight and performance/acceptance limits rather than treating every checker as passed.

## Times Square and background music

Add `-WHSpawnTimesSquare` to the normal interactive Unreal game command to start in the open plaza beside the red steps. It changes only the initial transform, so keyboard/controller input remains live. The final local owner copy also has `Play-TimesSquare.command`.

The supplied track source is `assets/audio/Curious Groove.mp3`. Run `python3 -B tools/audio/prepare_background_music.py`, then import with `unreal/WebHomage/Scripts/import_background_music.py` through the shared GPU coordinator when rebuilding generated content. See [the music source instructions](../assets/audio/README.md).

The latest owner session reported E sometimes choosing its older dash fallback when no perch is valid, and repeated ledge attempts around a building trap. These remain known limitations at owner-authorized closeout.

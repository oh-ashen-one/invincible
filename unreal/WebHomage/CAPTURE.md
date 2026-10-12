# WebHomage — capturing and measuring the RUNNING game (UE 5.8.3, Mac Studio M3 Ultra)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `../../DISCLAIMER.md`.

Verified by piece F1 on 2026-09-29. Everything here runs the real game (`-game`, the project's
GameMode + hero pawn), not an editor viewport.

## Rules for every agent (owner complaints behind each one)

1. **Never trap the owner's mouse or focus.** Automated runs are offscreen (`-RenderOffScreen`),
   so no window appears. If you truly need a window, put it on the secondary 1080x1920 display
   "27E40" (`-windowed -WinX=-1080 -WinY=40`), never on the main 3440x1440 ultrawide.
2. Project input config: `bCaptureMouseOnLaunch=False`, `CaptureDuringRightMouseDown`, `DoNotLock`.
   `AWebHomagePlayerController` starts with the mouse released, captures only on a left click in the
   game window, and **Escape always releases it**. Any `-WH*` automation flag or
   `-WHNoMouseCapture` disables capture completely. Keep these if you subclass or replace the controller.
3. **Kill your game process as soon as the capture is done.** `run_game.sh` quits via `-WHQuitAt`
   and hard-kills after `-timeout`. Kill only your own process, by its own path or PID. Never use
   `pkill -f WebHomage.uproject`: every worktree's project has that name.
4. Pass `-abslog=<your dir>/x.log` on every launch. Without it, all instances of the project share
   `~/Library/Logs/Unreal Engine/WebHomageEditor/WebHomage*.log`.
5. **Perf numbers are only valid on an idle GPU.** Check first:
   `ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*'`.
   On 2026-09-29 it read **95-99 % with none of F1's processes running** (other editors, Chrome,
   Blender were active), so every F1 frame time below is contaminated. Always report
   the utilization before the run, together with the numbers.

## Build (close your own editor first)

`Scripts/build_editor.sh`: a wrapper around
`Build.sh WebHomageEditor Mac Development -Project=<abs uproject> -WaitMutex`.
It works with **Xcode 27.0 as installed**: UE 5.8.3's `Engine/Config/Apple/Apple_SDK.json`
allows Xcode 15.2 to 27.9 and maps 27.0 to LLVM 21.1.6, and UBT reports "Mac SDK 27.0, Apple clang 21".
No overrides were needed. The wrapper exists because, while other UnrealEditor instances of this
engine are running, UBT links `libUnrealEditor-WebHomage-000N.dylib` but leaves
`Binaries/Mac/UnrealEditor.modules` on the old dylib, so the next launch silently runs stale code.
The wrapper deletes the old dylibs first, which forces the manifest update, and then verifies it.

## One command: screenshots + frame times + auto-quit

```
Scripts/run_game.sh <out_dir> -res 3840x2160 -shots 20,30,40 -perf 20:40 -name f4k -- -WHAutoMove
```
- Offscreen `-game` run at the true requested back-buffer size. Screenshots are `<out>/<name>_NN_tSSS.png`.
- `-perf a:b` writes `<out>/<name>_perf.json` and a `WH_PERF` log line: frame count, avg / p50 / p95 / p99 / max
  frame ms, frames over 16.67 ms, GPU ms (`RHIGetGPUFrameCycles`), output size, **effective internal
  (pre-TSR) resolution** and screen-percentage mode. It also runs `CsvProfile Start/Stop` over the same window,
  so the CSV lands in `Saved/Profiling/CSV/Profile(<timestamp>).csv`. Add `-- -csvGpuStats` for per-pass GPU columns.
- `-exec "r.ScreenPercentage 100,r.Lumen.HardwareRayTracing 0"` sets console variables at start (`t.MaxFPS 0` is always set,
  and `-NoVSync` is passed).
- `-WHAutoMove` (or cvar `wh.AutoMove 1`) makes the hero run forward, turn slowly and jump every 3 s, so
  the measured frames are real movement. Replace it with your own piece's driver when you have one.
- Warm-up: the first 10-20 s include shader/DDC/Lumen settling (multi-second hitches). Start `-perf` at 15 s or later.
- The underlying flags are implemented by `UWebHomageAutomation` (GameInstanceSubsystem) and work with any launch:
  `-WHShotAt=t1,t2 -WHShotDir= -WHShotName= -WHPerfFrom= -WHPerfTo= -WHCsv -WHQuitAt= -WHNoMouseCapture`.
  Times are game seconds.
- Settings menu (2026-10-01, `Core/WHSettings*`): Escape / P / gamepad Options open it in interactive play; saved to
  `Saved/Config/<platform>/GameUserSettings.ini` `[WebHomage.Settings]`. Automated runs (any flag above) never open it and never
  load the saved look / FOV / shake / graphics values, so captures and perf runs are unchanged. `-WHShowSettings` forces it open
  (no pause, no mouse capture) and makes the `-WHShotAt` shots include the UI, for verifying the menu.

## Video / frame sequences

```
Scripts/run_game.sh <out_dir> -res 1920x1080 -quit 4 -name mov -movie -- -WHAutoMove
```
This uses `-benchmark -fps=60 -dumpmovie`: a fixed 1/60 s game step, with every rendered frame written to
`Saved/Screenshots/MacEditor/MovieFrameNNNNN.png`. The script moves the frames to `<out>/<name>_frames/`
and encodes `<out>/<name>.mp4` (H.264, 60 fps, crf 18). The result is deterministic, smooth 60 fps footage
however slowly the machine renders. Verified: 4 s of game time gave 241 frames and a 1920x1080 60 fps mp4
(3.5 MB) in about 100 s of wall time. The footage says nothing about real-time performance. At 4K each PNG
is about 7 MB (about 420 MB per second of footage), so keep 4K clips short. Commit only mp4 files up to 15 MB.

## Resolution: what is actually achieved

- `-RenderOffScreen -ResX=3840 -ResY=2160 -ForceRes` gives a **true 3840x2160 back buffer**
  (screenshot PNG measured at 3840x2160, perf json `output_w/h` 3840x2160).
- Internal resolution: `r.ScreenPercentage` defaults to 0, meaning automatic by display size
  (`[Rendering.AutoScreenPercentage]`). A **2160p output renders internally at 1920x1080** (50 %, TSR upscale),
  and a 1080p output at 1399x787. For a native internal resolution pass `-exec "r.ScreenPercentage 100"`.
  Always disclose `internal_w/h` from the perf json.
- Windowed 3840x2160 was **not** tested: neither display (3440x1440, 1080x1920) can hold that window, and
  windows on the main display violate rule 1. Use offscreen.

## In-editor (MCP, port per piece) alternatives

- `EditorToolset.EditorAppToolset.StartPIE {"options":{"bSimulate":false,"playMode":"PlayMode_InViewPort","warmupSeconds":5}}`
  then `StopPIE`. Verified: PIE spawns the WebHomage hero.
- `EditorAppToolset.CaptureViewport` needs **every** argument (`captureTransform` and `annotations` included, or it
  errors with "needs a default value"). It renders the level viewport from the given pose, not the game camera,
  so it suits framing checks and not gameplay evidence.
- On a live game, console commands `stat unit`, `stat fps`, `stat gpu`, `CsvProfile Start|Stop` and
  `HighResShot 3840x2160` also work. Use them through `-exec`, since no agent types into a game window.

## Evidence from F1 (2026-09-29; GPU at 95-99 % from other processes, so numbers are NOT representative)

| run | output | internal | avg frame ms | GPU ms |
|---|---|---|---|---|
| Foundation_Test, HWRT Lumen on | 3840x2160 | 1920x1080 | 88.1 | 72.4 |
| HWRT Lumen off | 3840x2160 | 1920x1080 | 55.3 | 52.6 |
| HWRT Lumen off | 1920x1080 | 1399x787 | 82.1 | 68.0 |

The 1080p run is slower than the 4K one, which shows contention noise. Re-measure on an idle GPU before drawing conclusions.

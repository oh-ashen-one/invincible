#!/usr/bin/env python3
"""Stage the Invincible flight build for a local owner playtest (no engine launch).

Reuses tools/final/swing/stage_playtest.py (APFS clone of Config/Binaries/Content/
Shaders, hash manifest, guarded launcher) and adds `Play-Invincible.command`:
flying hero (flight is the default; no -WHFlight=0), Invincible-homage suit,
Times Square start. Requires macOS with Unreal Engine 5.8 installed; the
destination must be new. Never launches anything.
"""

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "final/swing/stage_playtest.py"


def load_base():
    spec = importlib.util.spec_from_file_location("stage_playtest_base", BASE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def invincible_command():
    return '''#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
UE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
if [ ! -x "$UE" ]; then echo "Unreal Engine 5.8 is missing: $UE" >&2; exit 1; fi
mkdir -p "$HERE/Saved/OwnerPlaytest/User" "$HERE/Saved/OwnerPlaytest/logs"
export GPU_SLOT_DIR="$HOME/.cache/gpu-slot"
unset SM2_COEXIST_HOLDER
exec /usr/bin/env python3 "$HERE/tools/m5/guarded_preview.py" -- \\
  "$UE" "$HERE/WebHomage/WebHomage.uproject" /Game/Showcase/Maps/Manhattan_Island \\
  -game -windowed -ResX=1920 -ResY=1080 -ForceRes -NoVSync \\
  -WHProfile=playable -WHResScale=100 \\
  "-WHPerfPreset=$HERE/WebHomage/Config/PerfPlayableFast.cvars" -WHSuit=invincible -WHSpawnTimesSquare \\
  "-UserDir=$HERE/Saved/OwnerPlaytest/User/" -NoCrashReports -notraceserver \\
  "-ExecCmds=t.MaxFPS 60,r.ScreenPercentage 100,r.AntiAliasingMethod 4" \\
  "-abslog=$HERE/Saved/OwnerPlaytest/logs/play-invincible.log"
'''


README_ADD = '''
## Invincible flight build

Double-click `Play-Invincible.command` (flying hero, Times Square start). The
older `Play.command` in this folder starts the same build at the default spawn.
Flight controls (keyboard / DualSense):

| Action | Keyboard / mouse | DualSense |
|---|---|---|
| Move / strafe / steer | WASD | Left stick |
| Camera / aim | Mouse | Right stick |
| Take off / climb (hold) | Space | Cross |
| Fly forward along the aim (hold) | Right mouse | R2 |
| Boost (while flying; sonic boom past the boom speed) | Shift | L3 |
| Descend (hold) / land near the ground | C / Left Ctrl | Circle |
| Instant stop / rescue interact (hold near an emergency) | E | Triangle |
| Dash | Q | L1 |
| Slam dive -> superhero landing | F | Square |
| Pause | Escape / P | Options |

Hitting a facade above the breach speed carries the hero through the building.
The hero cannot be hurt. Score = lives saved; the HUD also shows collateral damage.
Unofficial, non-commercial homage; no affiliation with the "Invincible" rights holders.
'''


def main():
    base = load_base()
    original_main = base.main
    state = {}

    def patched_readme(commit):
        return base_readme(commit) + README_ADD

    base_readme = base.readme
    base.readme = patched_readme
    # run the base stager, then add the extra launcher and refresh the manifest + STAGE.json
    args = sys.argv[1:]
    dest_arg = None
    for i, a in enumerate(args):
        if a == "--dest" and i + 1 < len(args):
            dest_arg = args[i + 1]
        elif a.startswith("--dest="):
            dest_arg = a.split("=", 1)[1]
    original_main()
    if "--check-only" in args or not dest_arg:
        return
    dest = Path(dest_arg).expanduser().resolve()
    launcher = dest / "Play-Invincible.command"
    launcher.write_text(invincible_command())
    launcher.chmod(0o755)
    stage_path = dest / "STAGE.json"
    stage = json.loads(stage_path.read_text())
    # the base manifest did not list the new launcher: rebuild it without the old manifest / STAGE.json (as the base does)
    stage_path.unlink()
    (dest / "SHA256SUMS").unlink()
    manifest, entries = base.write_manifest(dest)
    stage.update({"files": len(entries), "bytes": sum((dest / rel).stat().st_size for rel, _ in entries),
                  "sha256_manifest": base.sha256(manifest), "launchers": ["Play.command", "Play-Invincible.command"],
                  "build": "invincible-flight", "runtime_verified": False})
    stage_path.write_text(json.dumps(stage, indent=2) + "\n")
    print(json.dumps({"invincible_launcher": str(launcher), **state}, indent=2))


if __name__ == "__main__":
    main()

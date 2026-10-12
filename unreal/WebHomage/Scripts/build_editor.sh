#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Build the WebHomageEditor target for THIS worktree's project, headless.
# Why the wrapper: with other UnrealEditor instances of the same engine running (other agents),
# UBT links a new libUnrealEditor-WebHomage-000N.dylib but leaves Binaries/Mac/UnrealEditor.modules
# pointing at the OLD dylib, so your editor/-game silently loads stale code. Deleting the old
# dylibs first forces the manifest update. Close YOUR editor first (never touch anyone else's).
set -euo pipefail
PROJ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
UPROJECT="$PROJ_DIR/WebHomage.uproject"
if pgrep -f "$UPROJECT" >/dev/null; then
  echo "Your editor/game for $UPROJECT is running; stop it first:"
  echo "Stop your launch driver, then terminate your editor gracefully and wait up to 60 seconds."
  exit 2
fi
rm -f "$PROJ_DIR"/Binaries/Mac/libUnrealEditor-WebHomage-*.dylib
"/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh" WebHomageEditor Mac Development \
  -Project="$UPROJECT" -WaitMutex -NoHotReload "$@"
DYLIB=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['Modules']['WebHomage'])" "$PROJ_DIR/Binaries/Mac/UnrealEditor.modules")
if [ ! -f "$PROJ_DIR/Binaries/Mac/$DYLIB" ]; then
  echo "ERROR: UnrealEditor.modules points at missing $DYLIB"; exit 3
fi
echo "OK: UnrealEditor.modules -> $DYLIB"

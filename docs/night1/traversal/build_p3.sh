#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 build helper: clear every WebHomage dylib + the module manifest first (F1 wrapper can leave the manifest pointing at a
# deleted hot-reload dylib), then run the F1 wrapper.
cd "$(dirname "$0")/../../../unreal/WebHomage" || exit 1
mkdir -p Saved
# round 26: build_editor.sh refuses while this worktree's game runs -- check BEFORE deleting the dylibs (r26 deleted them, then the build refused)
if pgrep -f "[s]m2-n1/traversal/unreal/WebHomage/WebHomage.uproject" > /dev/null; then echo "build_p3: this worktree's engine is running; nothing deleted, not built"; exit 3; fi
rm -f Binaries/Mac/libUnrealEditor-WebHomage*.dylib Binaries/Mac/UnrealEditor.modules
Scripts/build_editor.sh > Saved/build_last.log 2>&1
RC=$?
grep -E "error|Result:|OK:|ERROR" Saved/build_last.log | head -30
exit $RC

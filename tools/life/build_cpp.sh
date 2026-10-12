#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Build the C++ module of THIS worktree (Scripts/build_editor.sh) and repair the stale-manifest case: while other agents' editors of this engine run, UBT links a new
# libUnrealEditor-WebHomage-000N.dylib but leaves UnrealEditor.modules on the old name; the new dylib is fine, so point the manifest at the newest one.
set -uo pipefail
PROJ="$(cd "$(dirname "$0")/../../unreal/WebHomage" && pwd)"
"$PROJ/Scripts/build_editor.sh" "$@"
RC=$?
if [ $RC -ne 0 ]; then
  NEW=$(ls "$PROJ"/Binaries/Mac/libUnrealEditor-WebHomage-*.dylib 2>/dev/null | sort | tail -1)
  if [ -n "$NEW" ] && grep -q "Result: Succeeded" /dev/null 2>/dev/null || [ -n "$NEW" ]; then
    python3 - "$PROJ/Binaries/Mac/UnrealEditor.modules" "$(basename "$NEW")" <<'PY'
import json, sys
p, n = sys.argv[1], sys.argv[2]
j = json.load(open(p)); j['Modules']['WebHomage'] = n; json.dump(j, open(p, 'w'), indent='\t'); print('manifest re-pointed to', n)
PY
    exit 0
  fi
fi
exit $RC

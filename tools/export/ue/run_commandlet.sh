#!/bin/zsh
# Run an editor-Python script (build_city.py steps, set_mpc.py, atmo_variants.py ...) in a HEADLESS -nullrhi commandlet of THIS worktree's project (no window, no GPU),
# wrapped in the GPU lock like every other Unreal launch (owner rule after the 2026-09-29 16:43 WindowServer reset: <= 1 Unreal process per agent, all through gpu_slot).
# Needs the P1 editor to be closed (same project).   usage: tools/export/ue/run_commandlet.sh <script.py> [key=value ...]     (key=value -> JOB_ARGS, like uejob.py)
HERE=${0:A:h}; WT=${HERE:h:h:h}; P=$WT/unreal/WebHomage/WebHomage.uproject
SCR=${SM2_CITY_SCRATCH:-/Users/midir/sm2-n1/_scratch/city}; mkdir -p $SCR
SCRIPT=${1:A}; shift
WRAP=$SCR/cmdlet_$$.py
python3 - "$SCRIPT" "$@" > $WRAP <<'PYEOF'
import sys, json, os
script = sys.argv[1]; args = dict(a.split('=', 1) for a in sys.argv[2:])
print('JOB_ARGS = ' + json.dumps(args)); print('JOB_SCRIPT_DIR = ' + repr(os.path.dirname(script)))
print('exec(compile(open(%r).read(), %r, "exec"), globals())' % (script, script))
PYEOF
# (r07-fix) never SIGKILL an engine (2026-09-29 23:08 kernel panic): if an engine of THIS project is still running, refuse instead of killing it (stop it with stop_ue.sh first)
if pgrep -f "MacOS/UnrealEditor .*${P:gs/./[.]/}" >/dev/null; then echo "run_commandlet: an Unreal process of this project is still running; stop it with /Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh first (never kill -9)"; rm -f $WRAP; exit 3; fi
$HERE/wait_slot.sh
${GPU_SLOT:-/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh} capture --label city -- "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "$P" \
  -run=pythonscript -script=$WRAP -unattended -nullrhi -NoSound -NoCrashReports -abslog=$WT/unreal/WebHomage/Saved/Logs/city_cmdlet.log
RC=$?
rm -f $WRAP
grep -a "build_city\|Traceback\|Error:.*\.py\|LogPython: Error" $WT/unreal/WebHomage/Saved/Logs/city_cmdlet.log | tail -25
exit $RC

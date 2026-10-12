#!/bin/bash
# Homage fan game tooling. Not an official Marvel, Sony or Insomniac project; no affiliation.
# Self-contained test of gpu_slot.sh. Starts NO Unreal instance: "Unreal capture processes" are faked
# with a tagged python sleeper, GPU utilization is mocked through GPU_SLOT_MOCK_UTIL_FILE, and the
# lock state lives in a private dir, so the real state in /Users/midir/sm2-n1/_scratch/gpu is untouched.
#   tools/gpu/test_gpu_slot.sh [--save <dir>]      exit 0 = all passed
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
GS="$HERE/gpu_slot.sh"
SAVE=""
[ "${1:-}" = "--save" ] && SAVE="$2"
TOKEN="GPUSLOTTEST$$_$RANDOM"
T="/Users/midir/sm2-n1/_scratch/gpu/test-$TOKEN"
case "$T" in /Users/midir/sm2-n1/_scratch/gpu/test-GPUSLOTTEST*) ;; *) echo "bad test dir"; exit 1;; esac
mkdir -p "$T"
export GPU_SLOT_DIR="$T/state" GPU_SLOT_LOG="$T/gpu_slot.log" GPU_SLOT_QUIET=1
export GPU_SLOT_POLL=0.1 GPU_SLOT_CALM_SECONDS=1.0 GPU_SLOT_SAMPLE_INTERVAL=0.2 GPU_SLOT_WAIT_LOG_EVERY=1
export GPU_SLOT_MOCK_UTIL_FILE="$T/util"
export GPU_SLOT_UNREAL_PATTERN="FAKEUE_$TOKEN" GPU_SLOT_CAPTURE_PATTERN='-game'
export GPU_SLOT_LABEL=test
unset GPU_SLOT_HELD GPU_SLOT_JSON

cat > "$T/job.py" <<'PY'
import sys, time
d, name, secs = sys.argv[1], sys.argv[2], float(sys.argv[3])
rc = int(sys.argv[4]) if len(sys.argv) > 4 else 0
open("%s/%s.start" % (d, name), "w").write("%.3f" % time.time())
time.sleep(secs)
open("%s/%s.end" % (d, name), "w").write("%.3f" % time.time())
sys.exit(rc)
PY
JOB="python3 $T/job.py $T"
setutil() { echo "$1" > "$T/util"; }
now() { python3 -c 'import time;print("%.3f"%time.time())'; }
waitf() { local i; for ((i = 0; i < ${2:-15} * 20; i++)); do [ -e "$1" ] && return 0; sleep 0.05; done; return 1; }
val() { cat "$T/$1" 2>/dev/null || echo 0; }
ge() { python3 -c "import sys;sys.exit(0 if float('$1') >= float('$2') else 1)"; }
fake_ue() { python3 -c 'import time,sys;time.sleep(float(sys.argv[1]))' "$1" "FAKEUE_$TOKEN" -game & FAKE_PID=$!; }
PASS=0; FAIL=0
check() { # desc, then a command that must succeed
  local d="$1"; shift
  if "$@"; then PASS=$((PASS + 1)); echo "  PASS  $d"; else FAIL=$((FAIL + 1)); echo "  FAIL  $d"; fi
}
cleanup() {
  pkill -9 -f "$TOKEN" 2>/dev/null
  wait 2>/dev/null
  if [ -n "$SAVE" ]; then
    mkdir -p "$SAVE"; cp "$GPU_SLOT_LOG" "$SAVE/gpu_slot.test.log" 2>/dev/null
    cp "$GPU_SLOT_DIR/runs.jsonl" "$SAVE/runs.test.jsonl" 2>/dev/null
    cp "$T/perf_b.json" "$SAVE/perf_result_example.json" 2>/dev/null
  fi
  case "$T" in /Users/midir/sm2-n1/_scratch/gpu/test-GPUSLOTTEST*) rm -rf "$T";; esac
}
trap cleanup EXIT

echo "== (a) two captures overlap, a third waits =="
setutil 50   # capture slots must not care about utilization
$GS capture --label A -- $JOB A 2.5 & PA=$!
$GS capture --label B -- $JOB B 2.5 & PB=$!
waitf "$T/A.start"; waitf "$T/B.start"
sleep 0.3
$GS capture --label C -- $JOB C 0.4 & PC=$!
sleep 0.8
check "third capture has NOT started while both slots are held" test ! -e "$T/C.start"
wait $PA $PB $PC
check "A and B overlapped (each started before the other ended)" \
  python3 -c "import sys;sys.exit(0 if $(val B.start) < $(val A.end) and $(val A.start) < $(val B.end) else 1)"
check "C started only after a slot was released (>= first end - 0.05)" \
  ge "$(val C.start)" "$(python3 -c "print(min($(val A.end),$(val B.end)) - 0.05)")"
check "at most 2 captures ran at once" python3 - "$T" <<'PY'
import sys
d = sys.argv[1]
iv = []
for n in "ABC":
    iv.append((float(open("%s/%s.start" % (d, n)).read()), float(open("%s/%s.end" % (d, n)).read())))
ev = sorted([(s, 1) for s, e in iv] + [(e, -1) for s, e in iv])
cur = mx = 0
for t, dlt in ev:
    cur += dlt; mx = max(mx, cur)
sys.exit(0 if mx <= 2 else 1)
PY
check "log has acquire/release/wait lines with utilization" \
  bash -c "grep -q 'event=wait' '$GPU_SLOT_LOG' && grep -q 'event=acquire' '$GPU_SLOT_LOG' && grep -q 'event=release' '$GPU_SLOT_LOG' && grep -q 'util=50' '$GPU_SLOT_LOG'"
$GS capture -- sh -c 'exit 7'; check "exit code of the command is propagated (capture, 7)" test $? -eq 7

echo "== (b) perf: exclusive, waits for captures + fake capture process + utilization < threshold for CALM =="
setutil 50
fake_ue 3.0; FAKE=$FAKE_PID
$GS capture --label A2 -- $JOB A2 1.5 & P1=$!
$GS capture --label B2 -- $JOB B2 1.5 & P2=$!
waitf "$T/A2.start"; waitf "$T/B2.start"
$GS perf --label P --json "$T/perf_b.json" -- $JOB P 0.6 & PP=$!
sleep 0.3
$GS capture --label D -- $JOB D 0.3 & PD=$!          # queued after perf: must wait for it
waitf "$T/A2.end"; waitf "$T/B2.end"
sleep 0.3
check "perf not started while the fake -game process is still alive" test ! -e "$T/P.start"
while kill -0 $FAKE 2>/dev/null; do sleep 0.05; done
T_FAKE_END="$(now)"
sleep 1.5
check "perf still waiting after captures + fake process ended because util=50 >= 15" test ! -e "$T/P.start"
setutil 5; T_LOW1="$(now)"
sleep 0.5
setutil 40                      # blip shorter than CALM total: streak must reset
sleep 0.6
check "perf did not start on the interrupted low-util streak" test ! -e "$T/P.start"
setutil 5; T_LOW2="$(now)"
waitf "$T/P.start" 10
check "perf start >= end of A2/B2/fake process" \
  ge "$(val P.start)" "$(python3 -c "print(max($(val A2.end),$(val B2.end),$T_FAKE_END) - 0.05)")"
check "perf start >= (last low-util onset + CALM 1.0 s) - 0.1" \
  ge "$(val P.start)" "$(python3 -c "print($T_LOW2 + 1.0 - 0.1)")"
wait $PP $PD $P1 $P2 2>/dev/null
check "capture queued after perf ran only after perf finished (exclusive)" \
  ge "$(val D.start)" "$(python3 -c "print($(val P.end) - 0.05)")"
check "perf sidecar json: exclusive, not contaminated, util_before < 15, wait/instances recorded" python3 - "$T/perf_b.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
ok = (r["class"] == "perf" and r["exclusive"] is True and r["contaminated"] is False and r["perf_valid"] is True
      and r["util_before"] < 15 and r["wait_s"] > 3 and "instances_before" in r and "instances_max_during" in r
      and r["util_during"]["n"] >= 1 and r["exit_code"] == 0 and r["settle"]["samples"] >= 5)
print("   ", {k: r[k] for k in ("wait_s", "util_before", "util_after", "instances_before", "instances_max_during", "contaminated")})
sys.exit(0 if ok else 1)
PY

echo "-- (b2) foreign capture process alone blocks perf even at low util"
setutil 5
fake_ue 2.0; FAKE=$FAKE_PID
$GS perf --label P2 -- $JOB PF 0.2 & PP=$!
while kill -0 $FAKE 2>/dev/null; do sleep 0.05; done
T_FAKE_END="$(now)"
wait $PP
check "perf start >= fake process end + CALM(1.0) - 0.1" \
  ge "$(val PF.start)" "$(python3 -c "print($T_FAKE_END + 1.0 - 0.1)")"

echo "-- (b3) foreign capture appearing DURING a perf run marks the result contaminated"
# a stranger = not a descendant of the perf wrapper
setutil 5
$GS perf --label P3 --json "$T/perf_b3.json" -- $JOB P3 1.5 & PP=$!
waitf "$T/P3.start"; fake_ue 1.0; wait $PP; wait $FAKE_PID 2>/dev/null
check "stranger capture process during perf => contaminated, perf_valid=false" python3 - "$T/perf_b3.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
sys.exit(0 if r["contaminated"] and not r["perf_valid"] and "foreign-capture-process-during-run" in r["contaminated_reasons"] else 1)
PY

echo "-- (b4) max hold kills the command (exit 124), wait timeout does not run it (exit 75), exit codes"
setutil 5
GPU_SLOT_PERF_MAX_HOLD=1.2 $GS perf --json "$T/perf_b4.json" -- $JOB HOLD 30; RC=$?
check "perf max hold exceeded => exit 124 and command was killed early" test $RC -eq 124 -a ! -e "$T/HOLD.end"
check "  ... result json flags max-hold + contaminated" python3 - "$T/perf_b4.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1])); sys.exit(0 if r["outcome"] == "max-hold-killed" and r["contaminated"] else 1)
PY
setutil 60
$GS perf --timeout 1.5 -- $JOB NOTRUN 0.1; RC=$?
check "perf wait timeout (util 60) => exit 75 and command NOT run" test $RC -eq 75 -a ! -e "$T/NOTRUN.start"
setutil 5
$GS perf -- sh -c 'exit 3'; RC=$?; check "perf exit code propagated (3)" test $RC -eq 3
$GS capture -- /nonexistent/cmd_$TOKEN; RC=$?; check "command not found => 127" test $RC -eq 127
$GS capture -- $GS capture --label inner -- $JOB NEST 0.1; RC=$?
check "nested capture inside a held capture passes through (no deadlock), exit 0" test $RC -eq 0 -a -e "$T/NEST.end"
$GS capture -- $GS perf -- true 2>/dev/null; RC=$?
check "perf nested inside a capture slot is refused (exit 2) instead of deadlocking" test $RC -eq 2

echo "== (c) stale lock recovery =="
setutil 50
echo "-- (c1) both capture holders killed -9: slots free again, stale records recovered"
$GS capture --label H1 -- $JOB H1 60 & W1=$!
$GS capture --label H2 -- $JOB H2 60 & W2=$!
waitf "$T/H1.start"; waitf "$T/H2.start"
"$HERE/gpu_status.sh" | grep -E 'Capture slots|Holders' | sed 's/^/     before kill: /'
kill -9 $W1 $W2; wait $W1 $W2 2>/dev/null
T0="$(now)"
$GS capture --label X -- $JOB X 0.2; RC=$?
T1="$(val X.start)"
check "new capture acquires immediately after holders were killed (start - kill < 2 s), exit 0" \
  python3 -c "import sys;sys.exit(0 if $RC == 0 and float('$T1') - float('$T0') < 2.0 else 1)"
check "log records 'stale-recovered' for both dead holders" \
  test "$(grep -c 'event=stale-recovered.*kind=holder' "$GPU_SLOT_LOG")" -ge 2
check "status shows no live holders after recovery" bash -c "'$HERE/gpu_status.sh' | grep -q 'Holders (0)'"
pkill -9 -f "$T/job.py $T H[12]" 2>/dev/null     # orphaned children of the killed wrappers (ours, tagged by test dir)

echo "-- (c2) dead waiter at the head of the queue does not block the next waiter"
$GS capture --label F1 -- $JOB F1 60 & W1=$!
$GS capture --label F2 -- $JOB F2 60 & W2=$!
waitf "$T/F1.start"; waitf "$T/F2.start"
$GS capture --label Q1 -- $JOB Q1 0.2 & QW1=$!
sleep 0.4
$GS capture --label Q2 -- $JOB Q2 0.2 & QW2=$!
sleep 0.4
kill -9 $QW1; wait $QW1 2>/dev/null
kill -TERM $W1; wait $W1 2>/dev/null           # frees a slot; Q2 is behind the dead Q1
waitf "$T/Q2.end" 8
check "Q2 ran although dead Q1 was ahead of it (waiter record recovered)" test -e "$T/Q2.end" -a ! -e "$T/Q1.start"
check "log records 'stale-recovered' kind=waiter" grep -q 'event=stale-recovered.*kind=waiter' "$GPU_SLOT_LOG"
kill -TERM $W2 2>/dev/null; wait $W2 2>/dev/null; pkill -9 -f "$T/job.py $T F[12]" 2>/dev/null

echo "-- (c3) perf holder killed -9 while settling: perf.lock is freed by the kernel"
setutil 50
$GS perf --label PS -- $JOB PS 5 & PSW=$!
sleep 0.8
"$HERE/gpu_status.sh" | grep -E 'Perf lock' | sed 's/^/     before kill: /'
check "perf holder is in settling state (holding the lock, waiting for calm)" bash -c "'$HERE/gpu_status.sh' | grep -q 'Perf lock:.*HELD.*state=settling'"
kill -9 $PSW; wait $PSW 2>/dev/null
T0="$(now)"
$GS capture --label Y -- $JOB Y 0.2; RC=$?
check "capture runs promptly after perf holder died (< 2 s), and the dead perf never ran its command" \
  python3 -c "import sys,os;sys.exit(0 if $RC == 0 and float('$(val Y.start)') - float('$T0') < 2.0 and not os.path.exists('$T/PS.start') else 1)"
check "log records 'stale-recovered' for the dead perf holder" grep -q 'event=stale-recovered.*dead_class=perf' "$GPU_SLOT_LOG"

echo "-- (c4) PID-reuse defence: a live PID with the wrong start time is treated as stale"
python3 - "$GPU_SLOT_DIR/queue" $$ <<'PY'
import json, sys
d, pid = sys.argv[1], int(sys.argv[2])
json.dump({"pid": pid, "start": "Mon Jan  1 00:00:00 1990", "class": "perf", "label": "impostor",
           "since": "x", "since_epoch": 0, "ticket": "00000000000000000001-%d" % pid, "cmd": "x"},
          open("%s/00000000000000000001-%d.json" % (d, pid), "w"))
PY
$GS capture --label Z -- $JOB Z 0.1; RC=$?
check "capture not blocked by a queue record whose PID was reused (start time differs)" test $RC -eq 0 -a -e "$T/Z.end"
check "  ... and it was logged as stale-recovered dead_label=impostor" grep -q 'stale-recovered.*dead_label=impostor' "$GPU_SLOT_LOG"

echo
echo "RESULT: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]

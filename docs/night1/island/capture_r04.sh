#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island r04: capture r1-r5 (+ warm-up) from ONE build into round-04, as consecutive GPU-lock holds (capture_round.sh inside the hold:
# ISLAND_IN_LOCK=1; a route starts only with >= 1,500 s of the 2,400 s hold left). Re-queues until every route movie exists (max 8 holds).
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; WT="$(cd "$HERE/../../.." && pwd)"
R="$HERE/round-04"; GPU=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh
T0=${CAP_T0:-$(date +%s)}
done_r() { local f="$R/$1.mp4"; [ -f "$f" ] && [ "$(stat -f %m "$f")" -ge "$T0" ]; }
todo() { local out=(); [ -n "${WARM-1}" ] && [ ! -f "$R/.warm_done" ] && out+=(warmup)
  for p in r1:r1_north_avenue r2:r2_south_avenue r3:r3_crosstown_east r4:r4_wallrun_roofs r5:r5_m2_avenue r5b:r5_m2_avenue_alt0; do done_r "${p#*:}" || out+=("${p%%:*}"); done
  echo "${out[@]:-}"; }
for k in 1 2 3 4 5 6 7 8; do
  T=$(todo); [ -z "$T" ] && break
  while pgrep -f "$WT/unreal/WebHomage/WebHomage.uproject" >/dev/null; do sleep 10; done
  echo "== hold $k: $T  $(date +%T)"
  ISLAND_IN_LOCK=1 "$GPU" capture --label island -- "$HERE/capture_round.sh" "$R" $T 2>&1 | grep -v "wait phase" | tail -20
  case " $T " in *" warmup "*) [ -f "$R/warmup_webtravworld_log.txt" ] && touch "$R/.warm_done";; esac
done
rm -f "$R/.warm_done"
echo "captures: todo now [$(WARM= todo)]  $(date +%T)"

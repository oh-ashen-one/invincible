#!/bin/bash
# Homage fan game tooling. Not an official Marvel, Sony or Insomniac project; no affiliation.
# GPU lock wrapper for the Night-1 Unreal loop. See tools/gpu/gpu_slot.py and docs/night1/gpu/PROTOCOL.md.
#   gpu_slot.sh capture [--label NAME] [--json FILE] -- <cmd...>   shared slot (2 at once)
#   gpu_slot.sh perf    [--label NAME] [--json FILE] -- <cmd...>   EXCLUSIVE, waits for an idle GPU
# `exec` on purpose: the wrapper's PID is the lock holder's PID.
PY="$(command -v python3 || echo /usr/bin/python3)"
exec "$PY" "$(cd "$(dirname "$0")" && pwd)/gpu_slot.py" "$@"

#!/bin/bash
# Homage fan game tooling. Not an official Marvel, Sony or Insomniac project; no affiliation.
# Prints lock holders, waiters, current GPU utilization and running Unreal processes. `--json` for machines.
PY="$(command -v python3 || echo /usr/bin/python3)"
exec "$PY" "$(cd "$(dirname "$0")" && pwd)/gpu_slot.py" status "$@"

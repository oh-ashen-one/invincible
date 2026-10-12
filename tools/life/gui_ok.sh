#!/bin/bash
# Homage fan game tooling (not affiliated with Marvel/Sony/Insomniac). P6 city life: exit 0 when a macOS GUI app can finish launching in this session (8 s probe), 1 when it cannot.
# Every Unreal launch needs it (see docs/night1/life/round-03/NOTES.md, the 2026-09-30 WindowServer incident): a launch while it fails hangs the engine, once in the kernel.
#   tools/life/gui_ok.sh && echo "safe to start an engine"
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN=${SM2_LIFE_BIN:-/Users/midir/sm2-n1/_scratch/life/bin}
mkdir -p "$BIN"
[ -x "$BIN/ns_launch_probe" ] || swiftc -O "$HERE/ns_launch_probe.swift" -o "$BIN/ns_launch_probe" 2>/dev/null || exit 1
O=$(mktemp "$BIN/probe.XXXXXX")
"$BIN/ns_launch_probe" > "$O" 2>&1 &
P=$!
for i in 1 2 3 4 5 6 7 8; do sleep 1; grep -q didFinishLaunching "$O" && break; done
R=1; grep -q didFinishLaunching "$O" && R=0
kill $P 2>/dev/null; wait $P 2>/dev/null; rm -f "$O"
exit $R

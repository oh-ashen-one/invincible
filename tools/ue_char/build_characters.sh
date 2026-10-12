#!/bin/bash
# Rebuild /Game/Characters + /Game/Tests/Characters in the running P2 editor (tools/ue_char/launch_editor.sh).
# In the live editor Interchange imports issued from the mailbox don't finish inside the same Python call, so each
# mesh is imported in two calls (start, poll until done, finish). Fan homage project; not official Marvel/Sony/Insomniac.
set -e
cd "$(dirname "$0")/../.."
B=unreal/WebHomage/Scripts/build_characters.py
run() { python3 tools/ue_char/uebox.py $B --timeout 1800 --args "$1" | grep -v '^OK$' | tail -4; }
waitfor() {  # $1 = tmp folder
  for i in $(seq 1 180); do
    r=$(python3 tools/ue_char/uebox.py -c "
E=unreal.EditorAssetLibrary; d='$1'
n=[p for p in (E.list_assets(d,recursive=True) if E.does_directory_exist(d) else [])]
busy=unreal.InterchangeManager.get_interchange_manager_scripted().is_interchange_active()
print('READY' if n and not busy else 'WAIT', len(n))" | tail -1)
    case "$r" in READY*) sleep 2; return 0;; esac; sleep 2
  done; echo "timeout waiting for $1"; return 1; }
item() { run "{\"steps\":\"$1\",\"items\":\"$2\",\"phase\":\"start\"}"; waitfor "$3"; run "{\"steps\":\"$1\",\"items\":\"$2\",\"phase\":\"finish\"}"; }
[ "$1" = "--skip-base" ] || run '{"steps":"prep,clean,tex,mat"}'
item mesh hero /Game/Characters/_tmp/Hero
item mesh thug /Game/Characters/_tmp/Thug
for s in Claude Codex Gemini Kimi Qwen; do item mesh $s /Game/Characters/_tmp/Suit_$s; done
for c in 03_white_tee 12_sundress_mom 13_construction_worker 15_executive; do item citizens $c /Game/Characters/_tmp/Cit_$c; done
run '{"steps":"abp,map"}'

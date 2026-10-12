#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Guard for the traversal-box dependency: /Game/Look/Look_Boxes (the hero's building boxes) and the WorldDynamic patch of the city geometry level
are produced by build_look.py step `geo` and go stale whenever Scripts/build_city.py rebuilds /Game/Tests/City/City_Midtown_Geo. If Look_Boxes.umap is older
than City_Midtown_Geo.umap (or missing), re-run `tools/perf_ue/rebuild_look.sh geo` (headless, this worktree's editor must be closed).
usage: ensure_boxes.py [--check]   (--check only reports; exit 1 when stale)   or  import ensure_boxes; ensure_boxes.ensure()"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); WT = os.path.abspath(os.path.join(HERE, '..', '..'))
CONTENT = os.path.join(WT, 'unreal', 'WebHomage', 'Content')
def stale():
    geo = os.path.join(CONTENT, 'Tests', 'City', 'City_Midtown_Geo.umap'); boxes = os.path.join(CONTENT, 'Look', 'Look_Boxes.umap')
    if not os.path.exists(geo): return 'city geometry level missing (run tools/perf_ue/rebuild_city.sh)'
    if not os.path.exists(boxes): return 'Look_Boxes.umap missing'
    if os.path.getmtime(boxes) < os.path.getmtime(geo): return 'Look_Boxes.umap is older than City_Midtown_Geo.umap (the city was rebuilt after the boxes)'
    return None
def ensure(check_only=False):
    why = stale()
    if not why: return True
    print('ensure_boxes: ' + why)
    if check_only: return False
    if subprocess.run(['pgrep', '-f', os.path.join(WT, 'unreal/WebHomage/WebHomage.uproject')], capture_output=True).stdout.strip():
        print('ensure_boxes: this worktree\'s editor/game is running: close it, then run tools/perf_ue/rebuild_look.sh geo'); return False
    r = subprocess.run([os.path.join(HERE, 'rebuild_look.sh'), 'geo'], capture_output=True, text=True); print(r.stdout[-600:])
    return stale() is None
if __name__ == '__main__':
    sys.exit(0 if ensure('--check' in sys.argv) else 1)

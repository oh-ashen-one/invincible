# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C: run build_manhattan.py steps INSIDE a held gpu_slot capture slot (the lock governs the instance count, so build_manhattan's own
# 3-instance poll is replaced by a no-op -- it starves while the capture slots are busy).   python3 tools/tricks/run_build.py <steps>
import os, runpy, sys
WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['SM2_MANHATTAN_SCR'] = '/Users/midir/sm2-n1/_scratch/tricks/manhattan'
sys.argv = ['build_manhattan.py', '--steps', sys.argv[1] if len(sys.argv) > 1 else 'traversal']
g = runpy.run_path(os.path.join(WT, 'unreal/WebHomage/Scripts/build_manhattan.py'), run_name='bm')
g['main'].__globals__['wait_slot'] = lambda: None
g['main']()

# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 headless driver for P1's Scripts/build_city.py (unchanged): the script reads its steps from JOB_ARGS (set by P1's editor job
# server), so a -run=pythonscript commandlet always ran the default steps; the mesh step also needs the editor
# (StaticMeshEditorSubsystem is None in a commandlet), so this runs in P3's own offscreen editor via -ExecCmds="py <this file>". A fresh project needs the street-kit meshes imported
# AFTER the geometry level exists (the 'kit' step opens it), so this runs two passes in one process:
#   1. clean,tex,mat,mesh,proto,map     2. kit
import os
# `open -n` does not pass the caller's environment to the editor: P3 scratch paths are the defaults here
os.environ.setdefault('SM2_CITY_EXPORT', '/Users/midir/sm2-n1/_scratch/traversal/city/export/midtown3x3')
os.environ.setdefault('SM2_CITY_TEX', '/Users/midir/sm2-n1/_scratch/traversal/city/tex')
_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../unreal/WebHomage/Scripts/build_city.py')
_SRC = os.path.normpath(_SRC)
for _steps in os.environ.get('SM2_CITY_PASSES', 'clean,tex,mat,mesh,proto,map;kit').split(';'):
    print('[build_city P3 driver] pass', _steps)
    _g = {'__name__': '__main__', '__file__': _SRC, 'JOB_ARGS': {'steps': _steps}}
    exec(compile(open(_SRC).read(), _SRC, 'exec'), _g)
print('[build_city P3 driver] ALL_PASSES_DONE')

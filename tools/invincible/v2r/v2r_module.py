#!/usr/bin/env python3
# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.
# Runs a video2rig submodule (reader.poses, reader.visible, twins, limbs ...) from the fork checkout under a neutral command line
# (see v2r_cmd.py for why). Project paths go through Local/v2r-hero.
#   <fork venv python> tools/invincible/v2r/v2r_module.py <fork checkout> <module after "video2rig."> <args...>
import os, runpy, sys


def main():
    fork, mod = sys.argv[1], sys.argv[2]
    os.chdir(fork); sys.path.insert(0, fork)
    sys.argv = [mod] + sys.argv[3:]
    import importlib
    m = importlib.import_module('video2rig.' + mod)
    if hasattr(m, 'main'):
        m.main()          # imported under its real name, so multiprocessing can pickle the module's workers (reader.visible)
    else:
        runpy.run_module('video2rig.' + mod, run_name='__main__')


if __name__ == '__main__':   # the spawn start method re-imports this file in every worker: nothing may run at import
    main()

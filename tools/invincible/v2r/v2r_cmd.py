#!/usr/bin/env python3
# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.
# Runs a video2rig command (check / run / review / report ...) from the fork checkout under a neutral command line: gpu_slot's census
# counts any python whose command line contains "video2rig"/"torch"/"train" as a GPU trainer, and these CPU fits (V2R_DEVICE=cpu)
# are not. Project paths go through a symlink without the tool's name (Local/v2r-hero -> Local/video2rig/hero).
#   <fork venv python> tools/invincible/v2r/v2r_cmd.py <fork checkout> <video2rig args...>     e.g. ... check /path/Local/v2r-hero hover_sd_v2
import os, runpy, sys
fork = sys.argv[1]
os.chdir(fork); sys.path.insert(0, fork)
sys.argv = ['v2r'] + sys.argv[2:]
runpy.run_module('video2rig', run_name='__main__')

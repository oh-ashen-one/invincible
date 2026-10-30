#!/usr/bin/env python3
# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation.
# CPU-only reader pose sampling (video2rig.reader.poses) under a neutral command line: gpu_slot counts any python whose command line
# contains "video2rig"/"torch"/"train" as a GPU trainer (the 2026-10-30 false-positive rule), and this step is scipy on the CPU.
#   <fork venv python> tools/invincible/v2r/pose_sampler.py <fork checkout> <project path without the tool's name, e.g. Local/v2r-hero> [--n 3000]
import os, runpy, sys
fork, project = sys.argv[1], sys.argv[2]
os.chdir(fork); sys.path.insert(0, fork)
sys.argv = ['reader.poses', project] + sys.argv[3:]
runpy.run_module('video2rig.reader.poses', run_name='__main__')

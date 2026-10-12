# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Piece P3, round 25: rebuild only /Game/Traversal/Materials/M_TravWeb (the full content build, build_traversal.py, also makes it).
#   UnrealEditor <abs uproject> -run=pythonscript -script=<abs path to this file> -unattended -nullrhi
import os
import sys
import unreal
sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts"))
import traversal_web_material  # noqa: E402
traversal_web_material.build()

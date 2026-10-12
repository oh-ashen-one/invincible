#!/usr/bin/env python3
"""One command for the whole AI-suit map pipeline (Studio; needs Blender 5.2 on PATH as `blender`).

    python3 tools/ue_char/suitmaps/run.py --all            # all five suits
    python3 tools/ue_char/suitmaps/run.py qwen gemini      # some
    python3 tools/ue_char/suitmaps/run.py --all --from geom   # skip the (slow, geometry-only) base bake

Steps per suit: src (8K basecolor from the Tripo source in ~/Downloads) -> base (Blender: mask/pos/normal/AO bakes)
-> geom (seam weld, back-emblem flatten) -> maps (basecolor/height/ORM) -> normal (Blender: tangent-space bake)
-> glb (public/assets/skins/<suit>.glb + art/night1/characters/suits/<suit>_{basecolor,normal_ogl,orm}.png).
Inputs: the original skinfit GLBs are read from git history (common.ORIG_COMMIT), the Tripo sources from ~/Downloads
(names in common.SUITS). Scratch: $P2_SCRATCH/suits/ (tools/ue_char/p2paths.py).

Homage fan project, not an official Marvel/Sony/Insomniac product.
"""
import io, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import SUITS, SCRATCH, mesh_arrays, basecolor_bytes  # noqa: E402

STEPS = ['src', 'base', 'geom', 'maps', 'normal', 'glb']
FLATTEN = {'gemini', 'qwen'}


def sh(*cmd):
    print('+', ' '.join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main():
    args = sys.argv[1:]
    start = args[args.index('--from') + 1] if '--from' in args else 'src'
    suits = list(SUITS) if '--all' in args else [a for a in args if a in SUITS]
    todo = STEPS[STEPS.index(start):]
    py = sys.executable
    for s in suits:
        if 'src' in todo:
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = None
            j, b, *_ = mesh_arrays(SUITS[s])
            os.makedirs(SCRATCH, exist_ok=True)
            Image.open(io.BytesIO(basecolor_bytes(j, b))).convert('RGB').save(os.path.join(SCRATCH, f'{s}_src8k.png'))
        if 'base' in todo:
            sh('blender', '-b', '--factory-startup', '-P', os.path.join(HERE, 'bake_base.py'), '--', s)
        if 'geom' in todo:
            sh(py, os.path.join(HERE, 'geom.py'), s, *(['--flatten-back'] if s in FLATTEN else []))
        if 'maps' in todo:
            sh(py, os.path.join(HERE, 'build_maps.py'), s)
        if 'normal' in todo:
            sh('blender', '-b', '--factory-startup', '-P', os.path.join(HERE, 'bake_normal.py'), '--', s)
        if 'glb' in todo:
            sh(py, os.path.join(HERE, 'write_glb.py'), s)


if __name__ == '__main__':
    main()

#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# r04 canopy guard fallback: put the pass-2 canopy hunks of r03 (commit dfaf7f94: Foliage.ush holes / ragged borders / value spread, FILL 450, the 4,771 Lumen shade-proxy instances) back to the cdaa64a0 state
# (= r03 pass 1, the capture set that was critic-judged), keeping every r04 change. Run from the worktree root, then rebuild (tools/terrain/run_build.sh) and recapture.
set -euo pipefail
cd "$(dirname "$0")/../.."
for f in unreal/WebHomage/Scripts/build_terrain.py unreal/WebHomage/Shaders/Terrain/Foliage.ush; do git diff cdaa64a0 dfaf7f94 -- "$f" | git apply -R; echo "reverted $f"; done
python3 - <<'PY'
p = 'unreal/WebHomage/Scripts/terrain_materials.py'; s = open(p).read()
a = "FILL = 450.0"; b = "FILL = 700.0"
assert a in s; s = s.replace(a, b)
old = """float eb = min(min(uv0.x, 1.0 - uv0.x), min(uv0.y, 1.0 - uv0.y));   // r03 pass 2: ragged quad borders (straight leaf-card edges against the sky in p10)
Op = tx.a * bnd * smoothstep(0.0, 0.07, eb + 0.04 * (lum - 0.5)); Sub = c * 0.85; Rough = 0.78;"""
new = "Op = tx.a * bnd; Sub = c * 0.85; Rough = 0.78;"
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s); print('reverted terrain_materials.py (FILL 700, plain leaf opacity)')
PY

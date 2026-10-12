#!/usr/bin/env python3
"""calibration helper: set the night preset's sky knobs in look_presets.json (sky_luminance_factor, SkyLight intensity, rayleigh scale); prints the new values"""
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[2] / 'unreal/WebHomage/Scripts/look_presets.json'
j = json.loads(P.read_text())
n = j['presets']['night']
for a in sys.argv[1:]:
    k, v = a.split('=')
    if k == 'slf':
        n['atmosphere']['sky_luminance_factor'] = [float(v)] * 3 + [1.0]
    elif k == 'skylight':
        n['sky']['intensity'] = float(v)
    elif k == 'rayleigh':
        n['atmosphere']['rayleigh_scattering_scale'] = float(v)
    else:
        raise SystemExit('unknown ' + k)
P.write_text(json.dumps(j, indent=1, ensure_ascii=False))
print(n['atmosphere']['sky_luminance_factor'], n['sky']['intensity'], n['atmosphere']['rayleigh_scattering_scale'])

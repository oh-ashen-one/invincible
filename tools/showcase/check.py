#!/usr/bin/env python3
"""Offline showcase check: the .umap/.uasset files of every showcase map, sublevel and hero asset exist on disk and the
module dylib manifest is valid. Prints JSON; exits nonzero if anything is missing. Never launches Unreal."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'unreal/WebHomage'
CONTENT = PROJECT / 'Content'
sys.path.insert(0, str(PROJECT / 'Scripts'))
import sm2_common  # noqa: E402


def on_disk(game_path, ext):
    return CONTENT / (game_path.removeprefix('/Game/') + ext)


def main():
    maps = sorted(sm2_common.SHOWCASE_MAPS.values())
    levels = sorted({lp for p in sm2_common.SHOWCASE_MAPS for lp in sm2_common.showcase_levels(p)})
    assets = ['/Game/Characters/Hero/SK_Hero', '/Game/Characters/Hero/Suits/DA_HeroSuits']
    missing = []
    for lp in maps + levels:
        if not on_disk(lp, '.umap').is_file():
            missing.append(lp)
    for ap in assets:
        if not on_disk(ap, '.uasset').is_file():
            missing.append(ap)
    suit_refs = []
    suit_set = on_disk('/Game/Characters/Hero/Suits/DA_HeroSuits', '.uasset')
    if suit_set.is_file():
        suit_refs = sorted(set(re.findall(rb'/Game/Characters/[A-Za-z0-9_/-]+', suit_set.read_bytes())))
        for raw in suit_refs:
            if not on_disk(raw.decode(), '.uasset').is_file():
                missing.append(raw.decode())
        if len(suit_refs) < 2:
            missing.append('DA_HeroSuits references fewer than 2 suit assets')
    night = PROJECT / 'Content/Night'
    for n in ('CityLights.bin', 'CityLights.meta.json', 'CityLights.json', 'NightGeometry.json'):
        if not (night / n).is_file():
            missing.append('Content/Night/' + n + ' (python3 tools/night/prep_night.py; build look)')
    try:
        meta = json.loads((night / 'CityLights.meta.json').read_text())
        size = (night / 'CityLights.bin').stat().st_size
        if sum(meta['counts'].values()) != meta['count'] or size != 52 + meta['count'] * 84:
            missing.append('Content/Night/CityLights.bin does not match CityLights.meta.json (%d bytes, %d records)' % (size, meta['count']))
        if json.loads((night / 'NightGeometry.json').read_text())['counts'] != meta['geometry_counts']:
            missing.append('Content/Night/NightGeometry.json counts differ from CityLights.meta.json')
    except (OSError, KeyError, ValueError):
        pass
    # every '#include "/Project/..."' of our shaders must exist on disk (some are generated and gitignored: Terrain/ParkData.ush)
    shader_includes = sorted({m for f in (PROJECT / 'Shaders').rglob('*.ush') for m in re.findall(r'#include "(/Project/[^"]+)"', f.read_text())})
    for inc in shader_includes:
        if not (PROJECT / 'Shaders' / inc[len('/Project/'):]).is_file():
            missing.append('Shaders/%s (generated shader include; Terrain/ParkData.ush: python3 tools/terrain/prep_terrain.py)' % inc[len('/Project/'):])
    module = None
    modules = PROJECT / 'Binaries/Mac/UnrealEditor.modules'
    try:
        module = json.loads(modules.read_text())['Modules']['WebHomage']
        if not (PROJECT / 'Binaries/Mac' / module).is_file():
            missing.append('Binaries/Mac/%s (named by UnrealEditor.modules)' % module)
    except (OSError, KeyError, ValueError) as e:
        missing.append('Binaries/Mac/UnrealEditor.modules invalid: %s' % e)
    report = {'status': 'ready_on_disk' if not missing else 'incomplete', 'showcase_maps': maps, 'sublevels': levels,
              'suit_references_checked': len(suit_refs), 'module': module, 'missing': missing,
              'night_lights_level': sm2_common.NIGHT_LIGHTS_LEVEL, 'runtime_verified': False}
    print(json.dumps(report, indent=2))
    if missing:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

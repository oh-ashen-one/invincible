#!/usr/bin/env python3
"""Stage accepted cached content for the owner's CLOSED preview; never run Unreal."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'unreal/WebHomage'
STATE = PROJECT / 'Saved/OwnerPreview'
CONTENT = PROJECT / 'Content'
SOURCES = [
    (Path('/Users/midir/spider-man-2-astra6'), '7094940146da974955a6daed8b4d9ce3ea16cc26', 'Content', 'Content'),
    (Path('/Users/midir/sm2-n1/characters'), 'd9067fddaac490125ab5c30a1e2c3113f2f4aa67', 'Content/Characters', 'Content/Characters'),
    (Path('/Users/midir/sm2-n1/terrain'), '54e0c007fd6f40ab39ad5c0a2073fb33f08acd4e', 'Content/TerrainR5b', 'Content/TerrainR5b'),
]
# The terrain branch tip is r06, but ONLY its preserved, accepted r05 checkpoint
# at /Game/TerrainR5b is staged. See integration docs/night1/terrain/round-05/README.md.
REQUIRED = [
    'TerrainR5b/Maps/Manhattan_Terrain.umap', 'TerrainR5b/Terrain_Land.umap',
    'TerrainR5b/City_Geo_T.umap', 'Maps/Manhattan_Actors.umap',
    'Look/Look_Boxes.umap', 'Look/Rigs/Look_Rig_golden.umap',
    'Water/Maps/Water_River.umap', 'Tests/Life/Life_Actors.umap',
    'Characters/Hero/SK_Hero.uasset', 'Characters/Hero/Suits/DA_HeroSuits.uasset',
]

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage', action='store_true', help='copy accepted content into this task checkout')
    args = ap.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    if args.stage:
        branch = subprocess.check_output(['git', '-C', str(ROOT), 'branch', '--show-current'], text=True).strip()
        if not branch.startswith('codex/owner-playtest-'):
            raise SystemExit('Refusing to stage outside a task-owned owner-playtest branch')
        for repo, expected, src_rel, dst_rel in SOURCES:
            head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
            if head != expected:
                raise SystemExit(f'Donor changed: {repo}: {head}; review provenance before staging')
            src, dst = repo / 'unreal/WebHomage' / src_rel, PROJECT / dst_rel
            dst.mkdir(parents=True, exist_ok=True)
            subprocess.run(['cp', '-cRp', str(src) + '/.', str(dst)], check=True)
    missing = [p for p in REQUIRED if not (CONTENT / p).is_file()]
    suit_set = CONTENT / 'Characters/Hero/Suits/DA_HeroSuits.uasset'
    suit_refs = sorted(set(re.findall(rb'/Game/Characters/[A-Za-z0-9_/-]+', suit_set.read_bytes()))) if suit_set.exists() else []
    for raw in suit_refs:
        rel = raw.decode().removeprefix('/Game/') + '.uasset'
        if not (CONTENT / rel).is_file():
            missing.append(rel)
    modules = PROJECT / 'Binaries/Mac/UnrealEditor.modules'
    binary = None
    if modules.exists():
        binary = PROJECT / 'Binaries/Mac' / json.loads(modules.read_text())['Modules']['WebHomage']
    if binary is None or not binary.is_file():
        missing.append('Binaries/Mac module referenced by UnrealEditor.modules')
    files = {str(p.relative_to(PROJECT)): {'bytes': p.stat().st_size, 'sha256': digest(p)}
             for p in [CONTENT / f for f in REQUIRED] + ([binary] if binary else []) if p.is_file()}
    report = {
        'status': 'prepared_on_disk' if not missing else 'incomplete',
        'integration_commit': SOURCES[0][1],
        'map': '/Game/TerrainR5b/Maps/Manhattan_Terrain',
        'output_requested': [3840, 2160], 'internal_scale_requested': 100,
        'quality_requested': 'Cinematic', 'frame_cap': 30,
        'opened': False, 'runtime_verified': False, 'source_donors': [
            {'repo': str(r), 'head': h, 'content': sr} for r, h, sr, _ in SOURCES],
        'required_files': files, 'suit_references_checked': len(suit_refs), 'missing': missing,
        'limitations': [
            'No Unreal instance, editor, game or commandlet launched during preparation.',
            'Runtime crowd/traffic composition and actual framebuffer size await the owner-authorized launch.',
            'Accepted R5b terrain geometry composition predates city r11; referenced City assets are from current integration.',
            'New upstream night mode and unfinished full-island expansion are excluded.',
            'First launch may compile material shaders; no real-time performance claim.'
        ]
    }
    (STATE / 'prepared.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['status', 'map', 'suit_references_checked', 'missing', 'opened', 'runtime_verified']}, indent=2))
    if missing:
        raise SystemExit(1)

if __name__ == '__main__':
    main()

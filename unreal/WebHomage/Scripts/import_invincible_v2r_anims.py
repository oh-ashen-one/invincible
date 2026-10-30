"""Import ANIMATIONS ONLY (new hero clips, e.g. the video2rig / Seedance takes) onto the EXISTING v2 hero skeleton, into their own folder,
for the in-game blind A/B: the game plays them with -WHHeroV2Clips=<that folder> (UWHHeroV2AnimInstance; a clip missing there falls back
to the shipped /Game/Invincible/HeroV2/Anims). The shipped hero (/Game/Invincible/HeroV2/...) is never written.

Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation. Companion of import_invincible_v2.py (same
A_<Clip> -> AS_<Clip> naming); the GLB comes from tools/invincible/v2r/make_v2r_glb.sh (the rig + only the listed clips).
Run headless through the GPU guard (build_manhattan.ue_python / gpu_slot capture); see docs/invincible/video2rig/INGAME-AB.md.
Prints a CLIPS line and SM2_BUILD_OK: import_invincible_v2r_anims.py.
env: WH_V2R_GLB   (default <project>/Saved/P2Build/invincible/SK_InvincibleV2R.glb)
     WH_V2R_DEST  (default /Game/Invincible/HeroV2R/Anims; this folder is cleared first -- it must be this script's own output)
"""
import json
import os
import struct
import unreal

SKMESH = '/Game/Invincible/HeroV2/SK_InvincibleV2'      # the shipped hero: its skeleton is the target, nothing here is written
SHIPPED = '/Game/Invincible/HeroV2'
DEST = os.environ.get('WH_V2R_DEST', '/Game/Invincible/HeroV2R/Anims').rstrip('/')
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
proj = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
glb = os.environ.get('WH_V2R_GLB', os.path.join(proj, 'Saved/P2Build/invincible/SK_InvincibleV2R.glb'))

# guard: the destination is wiped below -- never the shipped hero folder (or anything above it), never outside /Game
if not DEST.startswith('/Game/') or DEST == SHIPPED or (DEST + '/').startswith(SHIPPED + '/') or (SHIPPED + '/').startswith(DEST + '/'):
    raise RuntimeError('WH_V2R_DEST %r must be its own folder under /Game, outside %s' % (DEST, SHIPPED))
if not os.path.isfile(glb):
    raise FileNotFoundError('run tools/invincible/v2r/make_v2r_glb.sh first: ' + glb)


def glb_animation_names(path):
    """glTF animation names from the GLB's JSON chunk (A_Hover, ...)"""
    with open(path, 'rb') as f:
        magic, _ver, _len = struct.unpack('<4sII', f.read(12))
        if magic != b'glTF':
            raise RuntimeError('not a GLB: ' + path)
        clen, ctype = struct.unpack('<I4s', f.read(8))
        if ctype != b'JSON':
            raise RuntimeError('GLB without a JSON first chunk: ' + path)
        doc = json.loads(f.read(clen).decode('utf-8'))
    return [a.get('name', '') for a in doc.get('animations', [])]


want = [n for n in glb_animation_names(glb) if n.startswith('A_')]
if not want:
    raise RuntimeError('no A_<Clip> animation in ' + glb)
print('[invincible-v2r] GLB', glb, 'animations', want)

skm = unreal.load_asset(SKMESH)
if not isinstance(skm, unreal.SkeletalMesh):
    raise RuntimeError('shipped hero %s not found: run import_invincible_v2.py first' % SKMESH)
skel = skm.get_editor_property('skeleton')
if not skel:
    raise RuntimeError('no skeleton on ' + SKMESH)
print('[invincible-v2r] target skeleton', skel.get_path_name())

# UE 5.8 Interchange (InterchangeGenericAssetsPipelineSharedSettings.h, UInterchangeGenericCommonSkeletalMeshesAndAnimationsProperties):
# bImportOnlyAnimations + Skeleton (TSoftObjectPtr<USkeleton>). With import-only on, the generic pipeline itself turns off materials,
# textures, static meshes and the physics asset and disables the skeleton / skeletal-mesh factory nodes (no mesh is written).
p = unreal.InterchangeGenericAssetsPipeline()
p.set_editor_property('use_source_name_for_asset', False)   # keep the glTF animation names (no "<file name>" prefix / single-clip rename)
cs = p.get_editor_property('common_skeletal_meshes_and_animations_properties')
cs.set_editor_property('import_only_animations', True)
cs.set_editor_property('skeleton', skel)
cs.set_editor_property('add_curve_metadata_to_skeleton', False)   # leave the shipped skeleton asset unchanged
ap = p.get_editor_property('animation_pipeline')
ap.set_editor_property('import_animations', True)
mp = p.get_editor_property('mesh_pipeline')
mp.set_editor_property('import_static_meshes', False)
mp.set_editor_property('create_physics_asset', False)
mat = p.get_editor_property('material_pipeline')
mat.set_editor_property('import_materials', False)
mat.get_editor_property('texture_pipeline').set_editor_property('import_textures', False)

# clear only this script's own destination (a fresh import every run; re-importing over renamed AS_* targets skips clips)
EAL.make_directory(DEST)
for x in EAL.list_assets(DEST, recursive=True, include_folder=False):
    EAL.delete_asset(x)
t = unreal.AssetImportTask(); t.filename = glb; t.destination_path = DEST
t.automated = True; t.replace_existing = True; t.save = False
stack = unreal.InterchangePipelineStackOverride(); stack.add_pipeline(p); t.options = stack
AT.import_asset_tasks([t])
paths = list(t.imported_object_paths)
print('[invincible-v2r] imported', len(paths), 'objects')

clips, other = [], []
for x in paths:
    a = unreal.load_asset(x)
    if isinstance(a, unreal.AnimSequence): clips.append(a)
    elif a is not None: other.append(a)
for a in other:   # import-only should create nothing else; anything that did land inside DEST is our own stray output
    pn = a.get_path_name().split('.')[0]
    if pn.startswith(DEST + '/'):
        print('[invincible-v2r] removing non-animation import', pn, type(a).__name__); EAL.delete_asset(pn)
    else:   # e.g. the existing target skeleton reported back: never deleted, never saved by this script
        print('[invincible-v2r] note: import reported an object outside %s (left untouched, not saved): %s %s' % (DEST, pn, type(a).__name__))
if not clips:
    raise RuntimeError('no AnimSequence imported from ' + glb)


def clip_key(nm):
    """A_<key> -> key. The asset name ends with the glTF animation name (longest match; e.g. A_Fly vs A_FlyingFistKick); same rule as
    import_invincible_v2.py's 'part after A_' otherwise; a single imported clip with an unrelated name takes the GLB's only animation."""
    hits = [w for w in want if nm.endswith(w)]
    if hits: return max(hits, key=len)[2:]
    if 'A_' in nm: return nm[nm.find('A_') + 2:]
    if len(clips) == 1 and len(want) == 1: return want[0][2:]
    raise RuntimeError('cannot map imported clip %s to an A_<Clip> animation of %s' % (nm, want))


out, bad = [], []
for a in clips:
    key = clip_key(a.get_name())
    dst = DEST + '/AS_' + key
    src = a.get_path_name().split('.')[0]
    if src != dst:
        if EAL.does_asset_exist(dst): EAL.delete_asset(dst)
        if not EAL.rename_asset(src, dst): raise RuntimeError('rename failed %s -> %s' % (src, dst))
    seq = unreal.load_asset(dst)
    sk = seq.get_editor_property('skeleton') if seq else None
    if not sk or sk.get_path_name() != skel.get_path_name():
        bad.append('AS_%s (%s)' % (key, sk.get_path_name() if sk else 'none'))
    out.append('AS_' + key)
missing = sorted(set('AS_' + w[2:] for w in want) - set(out))
if missing:
    raise RuntimeError('clips in the GLB that did not import: %s' % missing)
if bad:
    raise RuntimeError('clips not on the target skeleton %s: %s' % (skel.get_path_name(), bad))
for x in EAL.list_assets(DEST, recursive=True, include_folder=False):
    EAL.save_asset(x, only_if_is_dirty=False)
print('CLIPS', sorted(out))
print('DEST', DEST, 'SKELETON', skel.get_path_name(), 'GLB', glb)
print('SM2_BUILD_OK: import_invincible_v2r_anims.py')

# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F (round 05, critic: "re-measure on the integrated map WITH traffic and crowd on"): a LOCAL copy of the integrated map with piece P6's
# city life (traffic + crowd + signals + probe = /Game/Tests/Life/Life_Actors, built by P6's UNCHANGED Scripts/build_life.py --steps content,map)
# streamed in as one more always-loaded sublevel. The shipped /Game/Maps/Manhattan is not modified.
#   /Game/PerfF/Life/Manhattan = /Game/Maps/Manhattan (+ its sublevels) + /Game/Tests/Life/Life_Actors   (perf_route.py spec: name@ini+variant:Life)
# Run in a headless commandlet of THIS worktree (editor + game closed, no GPU):
#   "<UnrealEditor>" <uproject> -run=pythonscript -script=<abs>/tools/perf_ue2/make_life_variant.py -unattended -nullrhi -RenderOffScreen -NoSound
import unreal, json, os

EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
SRC, DST, LIFE = '/Game/Maps/Manhattan', '/Game/PerfF/Life/Manhattan', '/Game/Tests/Life/Life_Actors'
LOG = os.environ.get('SM2_PERF_VAR_LOG', '/Users/midir/sm2-n1/_scratch/perf/life_variant.json')
for need in (SRC, LIFE):
    if not EAL.does_asset_exist(need): raise RuntimeError('missing ' + need)
if EAL.does_asset_exist(DST): EAL.delete_asset(DST)
if not EAL.duplicate_asset(SRC, DST): raise RuntimeError('duplicate failed')
unreal.EditorLoadingAndSavingUtils.load_map(DST)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
have = [l.get_path_name() for l in unreal.EditorLevelUtils.get_levels(world)]
if not any('Life_Actors' in h for h in have):
    unreal.EditorLevelUtils.add_level_to_world(world, LIFE, unreal.LevelStreamingAlwaysLoaded)
les.set_current_level_by_name(str(world.get_name()))
ok = unreal.EditorLoadingAndSavingUtils.save_map(world, DST)
levels = [l.get_path_name() for l in unreal.EditorLevelUtils.get_levels(world)]
json.dump({'map': DST, 'saved': bool(ok), 'levels': levels}, open(LOG, 'w'), indent=1)
print('[make_life_variant]', ok, levels)

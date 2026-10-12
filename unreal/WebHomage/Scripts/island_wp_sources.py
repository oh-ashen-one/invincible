# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Island (A), round 03: extra World Partition streaming sources on the whole-island map.
#
# Why: the traversal (WebTravWorld::InitWorld, piece P3) indexes the collision components of the cells that are loaded around the player at
# BeginPlay ONCE; a cell that streams in later is not a traversal solid (no web anchor / wall / roof). With one streaming source (the pawn at the
# map's PlayerStart, y 178 m) only the facade / roofs / detail / fire-escape tiles y -1024 .. 1536 are solid; every route south of y ~1500 m
# (the M2 tiles) fell to the street (round-03/README.md, REQUEST-traversal-r03.md section 0). A source actor placed on the avenue loads (and
# activates) the cells around it at start in addition to the player's, so the index covers the stretch of island around each source.
# Content only: the map's PlayerStart is untouched (a second PlayerStart would be chosen at random by AGameModeBase::ChoosePlayerStart).
#
# usage (editor closed; one commandlet of this worktree; through gpu_slot.sh):
#   UnrealEditor WebHomage.uproject -run=pythonscript -script=Scripts/island_wp_sources.py -unattended -nullrhi -NoSound -NoCrashReports
#   env SM2_ISLAND_WP_MAP (default /Game/Maps/Manhattan_WP), SM2_ISLAND_WP_SOURCES="M2:250:1560,..."  (tag:x:y in UE metres, x east, y south)
# build_manhattan.py's map step runs the same code (exec) after it re-creates the PlayerStart, so a clean rebuild gets the sources too.
import os
import unreal

WP_MAP_DEFAULT = '/Game/Maps/Manhattan_WP'
# tag -> (x, y) UE metres on the avenue. M2 = the middle of the new south tiles (route r5: y 1010 .. 2290).
SOURCES_DEFAULT = {'M2': (250.0, 1560.0)}
LABEL = 'WH_StreamSrc_'


def parse_sources(s):
    out = {}
    for part in (s or '').split(','):
        if part.strip():
            tag, x, y = part.strip().split(':')
            out[tag] = (float(x), float(y))
    return out


def add_component(actor, cls, log=print):
    """add an instance component of `cls` to a level actor: Actor.add_component_by_class when the Python API has it, else SubobjectDataSubsystem"""
    if hasattr(actor, 'add_component_by_class'):
        return actor.add_component_by_class(cls, False, unreal.Transform(), False)
    log('Actor has no add_component_by_class; SubobjectDataSubsystem members:',
        [m for m in dir(unreal.SubobjectDataSubsystem) if not m.startswith('_')][:60])
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_instance(actor)
    log('subobject handles of the instance:', len(handles))
    params = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=cls, blueprint_context=None)
    new_handle, fail = sds.add_new_subobject(params)
    log('add_new_subobject ->', new_handle, 'fail reason:', fail)
    data = sds.k2_find_subobject_data_from_handle(new_handle)
    comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
    log('component object:', comp)
    return comp


def apply_sources(world, sources, log=print):
    """(re)create the always-loaded streaming source actors of `sources` in the open WP `world`; returns how many were made"""
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label().startswith((LABEL, 'PlayerStart_')):   # idempotent; also drops the abandoned PlayerStart_<tag> portals
            eas.destroy_actor(a)
    n = 0
    for tag, (x, y) in sources.items():
        a = eas.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(x * 100.0, y * 100.0, 100.0), unreal.Rotator(0, 0, 0))
        a.set_actor_label(LABEL + tag)
        a.set_folder_path('Manhattan')
        a.set_editor_property('is_spatially_loaded', False)
        comp = add_component(a, unreal.WorldPartitionStreamingSourceComponent, log)
        if comp is None:
            raise RuntimeError('could not add a WorldPartitionStreamingSourceComponent to ' + LABEL + tag)
        for prop, val in (('target_state', unreal.StreamingSourceTargetState.ACTIVATED), ('streaming_source_enabled', True)):
            try:
                comp.set_editor_property(prop, val)
            except Exception as ex:
                log('WARN streaming source %s: %s not set (%s)' % (tag, prop, ex))
        try:
            log('WP streaming source %s at x %.0f y %.0f m: target state %s, enabled %s, shapes %d, priority %s' % (
                tag, x, y, comp.get_editor_property('target_state'), comp.get_editor_property('streaming_source_enabled'),
                len(comp.get_editor_property('shapes')), comp.get_editor_property('priority')))
        except Exception as ex:
            log('WP streaming source %s at x %.0f y %.0f m (readback failed: %s)' % (tag, x, y, ex))
        n += 1
    return n


def main():
    path = os.environ.get('SM2_ISLAND_WP_MAP', WP_MAP_DEFAULT)
    sources = parse_sources(os.environ.get('SM2_ISLAND_WP_SOURCES')) or SOURCES_DEFAULT
    unreal.EditorLoadingAndSavingUtils.load_map(path)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    n = apply_sources(world, sources, lambda *a: unreal.log('[island_wp_sources] ' + ' '.join(str(x) for x in a)))
    ok = unreal.EditorLoadingAndSavingUtils.save_map(world, path)
    unreal.log('[island_wp_sources] %s: %d streaming source(s), %s' % (path, n, 'saved' if ok else 'SAVE FAILED'))


if __name__ != 'island_wp_sources_lib':   # build_manhattan.py execs this file as the library 'island_wp_sources_lib' and calls apply_sources itself
    main()

# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# (island r03) WHBox spawn-rate probe, headless (-run=pythonscript -nullrhi).
# Run b (log _scratch/island/logs/probe_spawn_r03b.log + macOS `sample`): EditorActorSubsystem.spawn_actor_from_class goes through
#   UEditorEngine::AddActor -> FActorLabelUtilities::SetActorLabelUnique -> FCachedActorLabels::Populate(World) = every actor label of the
#   world hashed per spawn (93 % of the samples). 0.2 s / 1000 at 1 k, 3.4 s at 17 k, 25 s at 22 k (r02: 70 s / 1000 at 56 k): quadratic,
#   ~3 h for the island's ~140 k boxes.
# Run c: EditorActorSubsystem.duplicate_actors (one label populate per paste) crashes in a -run=pythonscript commandlet (SIGSEGV inside
#   UEditorActorSubsystem::DuplicateActors): not usable headless.
# Run d (this script): 'comp' mode = one always-loaded actor per tile holding one plain (non-instanced) invisible /Engine/BasicShapes/Cube
#   StaticMeshComponent per box. WebTravWorld.cpp (SolidMode 2) indexes IsTravCube() per COMPONENT (P->Bounds), so the index is the same as one
#   actor per box, with ~160 actors instead of ~140 k (no label scan). Saves, reloads, counts the components.
import unreal, time, os
EAL = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
SDL = unreal.SubobjectDataBlueprintFunctionLibrary
MAP = os.environ.get('PROBE_MAP', '/Game/Tests/IslandProbe/WPSpawnProbe3')
N_ACT = int(os.environ.get('PROBE_ACTORS', '40'))
PER = int(os.environ.get('PROBE_PER', '1000'))
def P(*a): print('[probe]', *a)
if EAL.does_asset_exist(MAP): unreal.EditorLoadingAndSavingUtils.load_map(MAP)
elif not les.new_level(MAP, True): raise RuntimeError('no WP map')
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
cube = unreal.load_asset('/Engine/BasicShapes/Cube')

def add(root_h, cls):
    h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root_h, new_class=cls, blueprint_context=None))
    return h, SDL.get_object(SDL.get_data(h))

t0 = time.time(); n = 0
for k in range(N_ACT):
    tb = time.time()
    a = eas.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    a.set_actor_label('WHBoxesP__t%d' % k); a.set_folder_path('City/TraversalBoxes')
    root_h = sds.k2_gather_subobject_data_for_instance(a)[0]
    rh, root = add(root_h, unreal.SceneComponent)
    root.set_mobility(unreal.ComponentMobility.STATIC)
    for i in range(PER):
        _, c = add(rh, unreal.StaticMeshComponent)
        c.set_static_mesh(cube)
        c.set_relative_location(unreal.Vector((n % 400) * 300.0, (n // 400) * 300.0, 500), False, False)
        c.set_relative_scale3d(unreal.Vector(2, 3, 10))
        c.set_collision_profile_name('BlockAll'); c.set_visibility(False); c.set_cast_shadow(False)
        c.set_mobility(unreal.ComponentMobility.STATIC)
        n += 1
    a.set_editor_property('is_spatially_loaded', False)
    if (k + 1) % 5 == 0: P('actor %d: %d comps total, %.1f s for this actor' % (k + 1, n, time.time() - tb))
P('comp mode: %d actors, %d cube components in %.1f s' % (N_ACT, n, time.time() - t0))
t2 = time.time()
ok = unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)
P('save_map', ok, '%.1f s' % (time.time() - t2))
unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
t3 = time.time()
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
P('reload %.1f s' % (time.time() - t3))
acts = [a for a in eas.get_all_level_actors() if a.get_actor_label().startswith('WHBoxesP__t')]
ncomp = 0; ok_cube = 0; sample = None
for a in acts:
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        ncomp += 1
        m = c.get_editor_property('static_mesh')
        if m and m.get_path_name().startswith('/Engine/BasicShapes/Cube') and not c.is_visible() and c.get_collision_profile_name() == 'BlockAll': ok_cube += 1
        sample = c
P('after reload: %d actors, %d static mesh components, %d invisible BlockAll cubes' % (len(acts), ncomp, ok_cube),
  'sample', sample.get_name() if sample else None, sample.get_world_location() if sample else None, sample.get_world_scale() if sample else None, acts[-1].get_editor_property('is_spatially_loaded') if acts else None)
P('total %.1f s' % (time.time() - t0))

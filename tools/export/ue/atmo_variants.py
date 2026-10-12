# Make atmosphere-variant copies of a view map (for tuning the far field): JOB_ARGS: src (view id), names 'a,b,c', and per variant fog_<n>, aerial_<n>, fogc_<n>
import unreal
src = JOB_ARGS.get('src', 'S4_perch_skyline')
for n in JOB_ARGS['names'].split(','):
    unreal.EditorLoadingAndSavingUtils.load_map('/Game/Tests/City/City_View_' + src)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == 'HeightFog':
            fc = a.component
            fc.set_editor_property('fog_density', float(JOB_ARGS['fog_' + n]))
            c = [float(v) for v in JOB_ARGS['fogc_' + n].split(',')]
            fc.set_editor_property('fog_inscattering_luminance', unreal.LinearColor(c[0], c[1], c[2], 1))
        if a.get_actor_label() == 'SkyAtmosphere':
            a.get_component_by_class(unreal.SkyAtmosphereComponent).set_editor_property('aerial_pespective_view_distance_scale', float(JOB_ARGS['aerial_' + n]))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.EditorLoadingAndSavingUtils.save_map(world, '/Game/Tests/City/City_View_' + src.split('_')[0] + 'v' + n)
    print('saved variant', n)

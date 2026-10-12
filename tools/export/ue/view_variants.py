# (r10) Atmosphere / exposure variant copies of a view map (scratch maps City_View_<id>v<name>, not committed, regenerable).
# JOB_ARGS: src (view id, default S4_perch_skyline), names 'a,b,c'; per variant (all optional) exp_<n> = manual exposure bias (EV), fog_<n> = height fog density,
# fogc_<n> = 'r,g,b' inscattering, aerial_<n> = aerial perspective view distance scale, fh_<n> = fog height falloff, fs_<n> = fog start distance (METRES, r11), sun_<n> = sun intensity, sky_<n> = sky light intensity.
# Superset of atmo_variants.py (which only knew fog / fogc / aerial). Run through run_commandlet.sh (headless, GPU-lock wrapped).
import unreal
src = JOB_ARGS.get('src', 'S4_perch_skyline')
for n in JOB_ARGS['names'].split(','):
    unreal.EditorLoadingAndSavingUtils.load_map('/Game/Tests/City/City_View_' + src)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    def A(k): return JOB_ARGS.get(k + '_' + n)
    for a in eas.get_all_level_actors():
        lab = a.get_actor_label()
        if lab == 'HeightFog':
            fc = a.component
            if A('fog') is not None: fc.set_editor_property('fog_density', float(A('fog')))
            if A('fh') is not None: fc.set_editor_property('fog_height_falloff', float(A('fh')))
            if A('fs') is not None: fc.set_editor_property('start_distance', float(A('fs')) * 100.0)
            if A('fogc') is not None:
                c = [float(v) for v in A('fogc').split(',')]
                fc.set_editor_property('fog_inscattering_luminance', unreal.LinearColor(c[0], c[1], c[2], 1))
        elif lab == 'SkyAtmosphere' and A('aerial') is not None:
            a.get_component_by_class(unreal.SkyAtmosphereComponent).set_editor_property('aerial_pespective_view_distance_scale', float(A('aerial')))
        elif lab == 'PPV' and A('exp') is not None:
            st = a.get_editor_property('settings')
            st.set_editor_property('override_auto_exposure_bias', True); st.set_editor_property('auto_exposure_bias', float(A('exp')))
            a.set_editor_property('settings', st)
        elif lab == 'Sun' and A('sun') is not None:
            a.light_component.set_editor_property('intensity', float(A('sun')))
        elif lab == 'SkyLight' and A('sky') is not None:
            a.light_component.set_editor_property('intensity', float(A('sky')))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.EditorLoadingAndSavingUtils.save_map(world, '/Game/Tests/City/City_View_' + src.split('_')[0] + 'v' + n)
    print('saved variant', n)

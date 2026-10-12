# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P4 Look: idempotent rebuild of /Game/Look and /Game/Tests/Look from committed sources.
#   sources: Scripts/look_presets.json (time-of-day presets), Scripts/city_shots.json (the S1..S8 views),
#            the city content of piece P1 (/Game/City + /Game/Tests/City/City_Midtown_Geo, built by Scripts/build_city.py),
#            the export's collision.json (building boxes for the traversal, <SM2_CITY_EXPORT>/collision.json)
#   run:     tools/perf_ue/rebuild_look.sh [steps] [presets]   (headless, editor closed: UnrealEditor <uproject> -run=pythonscript
#            -script=<this file> -unattended -nullrhi; env SM2_LOOK_STEPS / SM2_LOOK_PRESETS select parts), or in the P4 editor:
#            tools/perf_ue/uejob.py unreal/WebHomage/Scripts/build_look.py [steps=geo,rigs,maps] [presets=midday,golden,night]
# What it owns:
#   /Game/Look/Look_Boxes                invisible traversal building boxes (see step geo); the city geometry level itself is P1's
#   /Game/Look/Rigs/Look_Rig_<preset>    ALL lighting of a preset: SkyAtmosphere, sun (+moon), SkyLight (real-time capture),
#                                        VolumetricCloud, ExponentialHeightFog (+volumetric fog, +haze layer), PostProcessVolume,
#                                        star dome (night), MPC_City night parameters through a Level Sequence (see step rigs)
#   /Game/Look/Look_NightLights          night street lighting (step night): lamps, storefront spill, stand-in traffic lights, wet-street decal, hero lights
#   /Game/Tests/Look/Look_Midtown[_golden|_night]     playable maps (traversal game mode): city geometry + Look_Boxes + rig + PlayerStart
#   /Game/Tests/Look/Look_View_<preset>_<S#>          the city shot views (Scripts/city_shots.json) under each preset
import unreal, os, sys, json, math, time, random, shutil
sys.path.insert(0, os.environ.get('SM2_SCRIPTS_DIR') or os.path.dirname(os.path.abspath(globals().get('__file__') or '.')))
import sm2_common
_B = sm2_common.Build('build_look.py')

EXPORT = os.environ.get('SM2_CITY_EXPORT', os.path.join(os.environ.get('SM2_LOOK_SCRATCH', '/Users/midir/sm2-n1/_scratch/look'), 'export', 'midtown3x3'))   # the city export (collision.json, layout.json)
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.path.join(os.environ.get('SM2_LOOK_WORKTREE', '/Users/midir/sm2-n1/look'), 'unreal/WebHomage/Scripts')
try: ARGS = JOB_ARGS  # noqa: F821 (set by tools/perf_ue/uejob.py)
except NameError: ARGS = {}
STEPS = set((ARGS.get('steps') or os.environ.get('SM2_LOOK_STEPS') or 'geo,rigs,night,maps').split(','))
PRESETS_JSON = json.load(open(os.path.join(HERE, 'look_presets.json')))
ORDER = [p for p in PRESETS_JSON['order'] if p in (ARGS.get('presets') or os.environ.get('SM2_LOOK_PRESETS') or ','.join(PRESETS_JSON['order'])).split(',')]
PRE = PRESETS_JSON['presets']
SHOTS = json.load(open(os.path.join(HERE, 'city_shots.json')))
CITY_GEO = '/Game/Tests/City/City_Midtown_Geo'
LOOK, RIGS, TESTS = '/Game/Look', '/Game/Look/Rigs', '/Game/Tests/Look'
MPC = '/Game/City/Materials/MPC_City'
EAL = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
T0 = time.time()
MISS = []
def log(*a): print('[build_look %5.0fs]' % (time.time() - T0), *a)

# ------------------------------------------------------------------------------------------------ helpers
def conv(v):
    """json value -> unreal value (lists of 3/4 numbers become LinearColor)"""
    if isinstance(v, list) and len(v) in (3, 4) and all(isinstance(x, (int, float)) for x in v):
        return unreal.LinearColor(*[float(x) for x in v]) if len(v) == 4 else unreal.Vector(*[float(x) for x in v])
    return v

ALIAS = {'aerial_perspective_distance_scale': 'aerial_pespective_view_distance_scale',  # (sic) the engine property name has a typo
         'volumetric_fog': 'enable_volumetric_fog'}
def fix_type(name, v):
    if isinstance(v, unreal.LinearColor):
        if name.endswith('albedo'): return unreal.Color(*[int(round(255 * c)) for c in (v.r, v.g, v.b, v.a)])
        if name.startswith('color_'): return unreal.Vector4(v.r, v.g, v.b, v.a)
    return v
def setp(obj, name, value, what=''):
    """set_editor_property that never aborts the build: unknown / rejected properties are collected in MISS"""
    name = ALIAS.get(name, name); value = fix_type(name, value)
    try:
        obj.set_editor_property(name, value); return True
    except Exception as e:
        MISS.append('%s.%s (%s)' % (what or type(obj).__name__, name, str(e).split('\n')[0][:90])); return False

def U(x, y, z): return unreal.Vector(x * 100.0, z * 100.0, y * 100.0)  # browser metres (x east, y up, z south) -> UE cm

def look_rot(p, t):
    d = unreal.Vector(t.x - p.x, t.y - p.y, t.z - p.z)
    return unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(d.z, math.hypot(d.x, d.y))), yaw=math.degrees(math.atan2(d.y, d.x)))

def sun_rotator(elev, az):
    """light travel direction for a sun at elevation elev above the horizon, compass azimuth az (clockwise from north, east = 90).
    UE frame of the city export: X east, Y south (north = -Y), Z up."""
    e, a = math.radians(elev), math.radians(az)
    to_sun = (math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))
    d = tuple(-c for c in to_sun)
    return unreal.Rotator(roll=0.0, pitch=math.degrees(math.asin(max(-1.0, min(1.0, d[2])))), yaw=math.degrees(math.atan2(d[1], d[0])))

def spawn(cls, loc=unreal.Vector(0, 0, 0), rot=unreal.Rotator(0, 0, 0), label=None, folder=None):
    a = eas.spawn_actor_from_class(cls, loc, rot)
    if label: a.set_actor_label(label)
    if folder: a.set_folder_path(folder)
    return a

KEEP = ('WorldSettings', 'Brush', 'DefaultPhysicsVolume', 'GameplayDebuggerCategoryReplicator', 'WorldDataLayers', 'WorldPartitionMiniMap')
def open_level(path):
    """idempotent: an existing map is opened and emptied (deleting maps pops a modal dialog), else created"""
    if EAL.does_asset_exist(path):
        unreal.EditorLoadingAndSavingUtils.load_map(path)
        for a in eas.get_all_level_actors():
            if a.get_class().get_name() not in KEEP: eas.destroy_actor(a)
    else:
        les.new_level(path)
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

def open_level_keep(path):
    unreal.EditorLoadingAndSavingUtils.load_map(path)
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

# ------------------------------------------------------------------------------------------------ step geo
# Prepares the city geometry (P1's City_Midtown_Geo, patched IN PLACE in this worktree's content) and builds Look_Boxes for the
# traversal hero (piece P3): its world queries index every WorldStatic primitive by its bounds as a "building box".
#  * every city component becomes WorldDynamic (still blocks traces and the camera): a merged 256 m facade tile or a whole-city
#    instanced prop component would otherwise be one giant solid;
#  * the bare ground (asphalt, sidewalks, water) is tagged WHGround (floor that never holds a web);
#  * /Game/Look/Look_Boxes: the browser's own collision boxes (collision.json: wall / glass / hero / spire / bulkhead / watertower)
#    as invisible WorldStatic box actors = the building boxes of the traversal (anchors, wall-run, perch points, capsule push-out).
# Re-run this step after every Scripts/build_city.py run (it recreates the city level).
BOX_KINDS = {0: 'wall', 7: 'bulkhead', 8: 'watertower', 13: 'spire', 14: 'hero', 17: 'glass'}
BOXES = LOOK + '/Look_Boxes'
def build_geo():
    if not EAL.does_asset_exist(CITY_GEO): raise RuntimeError('city geometry level missing: run Scripts/build_city.py first')
    world = open_level_keep(CITY_GEO)
    n_dyn = n_gnd = 0
    for a in eas.get_all_level_actors():
        if a.get_class().get_name() in KEEP: continue
        lab = a.get_actor_label()
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            c.set_collision_object_type(unreal.CollisionChannel.ECC_WORLD_DYNAMIC); n_dyn += 1
        if lab.startswith(('asphalt', 'sidewalk')) or lab == 'WaterPlane':
            a.tags = [unreal.Name('WHGround')]; n_gnd += 1
    les.save_current_level()
    world = open_level(BOXES)
    C = json.load(open(os.path.join(EXPORT, 'collision.json')))
    cube = unreal.load_asset('/Engine/BasicShapes/Cube')
    n_box = 0
    for s in C['solids']:
        if s['t'] != 0 or s['k'] not in BOX_KINDS: continue
        x0, y0, z0, x1, y1, z1 = s['bb']  # browser metres: x east, y up, z south
        if (y1 - y0) < 3.0 or ((x1 - x0) < 1.2 and (z1 - z0) < 1.2): continue
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor, U((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        a.set_actor_label('WHBox_%d' % n_box); a.set_folder_path('Look/TraversalBoxes')
        c = a.static_mesh_component; c.set_static_mesh(cube)
        a.set_actor_scale3d(unreal.Vector((x1 - x0), (z1 - z0), (y1 - y0)))  # the cube is 100 cm: scale = size in metres
        c.set_collision_profile_name('BlockAll'); c.set_visibility(False); c.set_cast_shadow(False)
        a.set_mobility(unreal.ComponentMobility.STATIC)
        n_box += 1
    unreal.EditorLoadingAndSavingUtils.save_map(world, BOXES)
    log('geo: %d components -> WorldDynamic, %d ground actors tagged, %d traversal boxes in %s' % (n_dyn, n_gnd, n_box, BOXES))

# ------------------------------------------------------------------------------------------------ step rigs
def lin_to_srgb_color(rgb):
    f = lambda x: 12.92 * x if x <= 0.0031308 else 1.055 * (x ** (1 / 2.4)) - 0.055
    return unreal.Color(r=int(round(255 * f(max(0.0, min(1.0, rgb[0]))))), g=int(round(255 * f(max(0.0, min(1.0, rgb[1]))))), b=int(round(255 * f(max(0.0, min(1.0, rgb[2]))))), a=255)

def browser_rotator(elev, az):
    """light travel direction for the author's browser moon: direction TO the moon = (cos el cos az, sin el, cos el sin az) in browser (x east, y up, z south); UE X = x, Y = z, Z = y"""
    e, a = math.radians(elev), math.radians(az)
    d = (-math.cos(e) * math.cos(a), -math.cos(e) * math.sin(a), -math.sin(e))
    return unreal.Rotator(roll=0.0, pitch=math.degrees(math.asin(max(-1.0, min(1.0, d[2])))), yaw=math.degrees(math.atan2(d[1], d[0])))

def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)

def derive_fog(F):
    """UE ExponentialHeightFog from the author's night fog (pipeline.js composite: od = a * (dist - start) * mix(0.45, 1.3, smoothstep(150, 2600, dist)), od / (1 + 0.22 od), T = exp(-od), a = density * exp(-h0 / 300);
    a = fogBase 0.00013 x NH.fog 4.0 per metre, start 120 m). UE (SceneCore.cpp): extinction = FogDensity / 1000 per cm, height falloff = FogHeightFalloff / 1000 per cm in base 2, od = d_cm * (dist_cm - s_cm).
    Two equations match the optical depth at 300 m and 2 km: d = (od2 - od1) / (200000 - 30000), s = 30000 - od1 / d (cm). Height falloff: exp(-h / 300 m) = 2^(-f h_cm) -> f = 1 / (30000 ln 2)."""
    a = F['density_base'] * F['density_mult'] * math.exp(-F['camera_h_m'] / F['falloff_m'])
    def od(dist):
        o = a * max(dist - F['start_m'], 0.0) * (0.45 + 0.85 * smoothstep(150.0, 2600.0, dist))
        return o / (1.0 + 0.22 * o)
    o1, o2 = od(F['match_near_m']), od(F['match_far_m'])
    d = (o2 - o1) / ((F['match_far_m'] - F['match_near_m']) * 100.0)
    s = F['match_near_m'] * 100.0 - o1 / d
    return {'fog_density': d * 1000.0, 'fog_height_falloff': 1000.0 / (F['falloff_m'] * 100.0 * math.log(2.0)), 'start_distance': s, 'od_near': o1, 'od_far': o2, 'T_near_green': math.exp(-o1), 'T_far_green': math.exp(-o2)}

def derive_units(P):
    """night preset in the author's units: one constant K = UE cd/m2 (and lux, nits) per browser unit. Exposure, moon, fog in-scatter, emissive scale and the fog fit follow from `units`."""
    U = P.get('units')
    if not U: return None
    K = float(U['K'])
    ev = math.log2(K / (1.2 * U['display_exposure']))   # browser display = radiance x display_exposure; UE: radiance x K / (1.2 x 2^EV100)
    P['exposure'] = {'min_ev': round(ev - U['auto_range'], 3), 'max_ev': round(ev + U['auto_range'], 3), 'bias': U.get('exposure_bias', 0.0)}
    P['moon']['lux'] = U['moon_intensity'] * K
    P['moon']['color_linear'] = U['moon_color_linear']
    P['mpc']['EmissiveScale'] = K
    P['fog']['fog_inscattering_luminance'] = [U['nh_low'][i] * K for i in range(3)] + [1.0]
    fg = derive_fog(U['fog'])
    P['fog'].update({k: fg[k] for k in ('fog_density', 'fog_height_falloff', 'start_distance')})
    P['fog']['fog_max_opacity'] = U['fog']['max_opacity']
    log('units: K %.0f, EV100 %.3f (min %.2f max %.2f), moon %.1f lux, fog density %.5f falloff %.4f start %.0f cm, T(300 m) %.4f T(2 km) %.4f (green)' %
        (K, ev, P['exposure']['min_ev'], P['exposure']['max_ev'], P['moon']['lux'], fg['fog_density'], fg['fog_height_falloff'], fg['start_distance'], fg['T_near_green'], fg['T_far_green']))
    return fg

def build_rig(name):
    P = PRE[name]
    derive_units(P)
    path = '%s/Look_Rig_%s' % (RIGS, name)
    world = open_level(path)
    sun_d, moon_d = P['sun'], P.get('moon')
    # --- sun (atmosphere sun light 0). Physical units: illuminance in lux, exposure comes from the post volume. (night: no sun, the moon is the one atmosphere light)
    if sun_d:
      sun = spawn(unreal.DirectionalLight, unreal.Vector(0, 0, 50000), sun_rotator(sun_d['elev'], sun_d['az']), 'Sun', 'Lighting')
      lc = sun.light_component
      lc.set_mobility(unreal.ComponentMobility.MOVABLE)
      for k, v in (('intensity', sun_d['lux']), ('use_temperature', True), ('temperature', sun_d['temp']), ('light_source_angle', sun_d['angle']),
                 ('atmosphere_sun_light', True), ('atmosphere_sun_light_index', 0), ('cast_shadows', True), ('cast_volumetric_shadow', True),
                 ('cast_cloud_shadows', bool(sun_d.get('cloud_shadows', True))), ('cloud_shadow_strength', 0.8), ('per_pixel_atmosphere_transmittance', True),
                 ('atmosphere_sun_disk_color_scale', unreal.LinearColor(sun_d.get('disk', 1.0), sun_d.get('disk', 1.0), sun_d.get('disk', 1.0), 1.0))):
        setp(lc, k, v, 'Sun')
    if moon_d:
        rot = browser_rotator(moon_d['elev'], moon_d['az_browser']) if 'az_browser' in moon_d else sun_rotator(moon_d['elev'], moon_d['az'])
        moon = spawn(unreal.DirectionalLight, unreal.Vector(0, 0, 50000), rot, 'Moon', 'Lighting')
        mc = moon.light_component; mc.set_mobility(unreal.ComponentMobility.MOVABLE)
        colour = (('use_temperature', False), ('light_color', lin_to_srgb_color(moon_d['color_linear']))) if 'color_linear' in moon_d else (('use_temperature', True), ('temperature', moon_d['temp']))
        for k, v in (('intensity', moon_d['lux']), *colour, ('light_source_angle', moon_d['angle']),
                     ('atmosphere_sun_light', bool(moon_d.get('atmosphere', True))), ('atmosphere_sun_light_index', int(moon_d.get('atmosphere_index', 1))), ('cast_shadows', True), ('cast_volumetric_shadow', True),
                     ('cast_cloud_shadows', False), ('per_pixel_atmosphere_transmittance', True)):
            setp(mc, k, v, 'Moon')
    for fill_d in P.get('fills', []):   # unshadowed, non-atmosphere fill directional lights (night: horizon city glow, lights facades the moon does not reach)
        fl = spawn(unreal.DirectionalLight, unreal.Vector(0, 0, 50000), sun_rotator(fill_d['elev'], fill_d['az']), 'CityGlow' + fill_d['name'], 'Lighting')
        fc_ = fl.light_component; fc_.set_mobility(unreal.ComponentMobility.MOVABLE)
        for k, v in (('intensity', fill_d['lux']), ('use_temperature', True), ('temperature', fill_d['temp']), ('atmosphere_sun_light', False), ('cast_shadows', False),
                     ('cast_volumetric_shadow', False), ('volumetric_scattering_intensity', 0.0), ('light_source_angle', 2.0)):
            setp(fc_, k, v, 'CityGlow' + fill_d['name'])
    # --- sky atmosphere (aerial perspective) + real-time captured sky light
    sa = spawn(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), label='SkyAtmosphere', folder='Lighting')
    for k, v in P['atmosphere'].items():
        if k == 'ground_albedo': v = unreal.Color(*[int(x) for x in v])
        else: v = conv(v)
        setp(sa.get_component_by_class(unreal.SkyAtmosphereComponent), k, v, 'SkyAtmosphere')
    sl = spawn(unreal.SkyLight, unreal.Vector(0, 0, 3000), label='SkyLight', folder='Lighting')
    slc = sl.light_component
    slc.set_mobility(unreal.ComponentMobility.MOVABLE)
    for k, v in (('real_time_capture', True), ('intensity', P['sky']['intensity']), ('cloud_ambient_occlusion', False),
                 ('light_color', unreal.Color(r=int(255 * P['sky']['tint'][0]), g=int(255 * P['sky']['tint'][1]), b=int(255 * P['sky']['tint'][2]), a=255)), ('lower_hemisphere_is_black', False)):
        setp(slc, k, v, 'SkyLight')
    # --- volumetric clouds
    if P['clouds'].get('enabled', True):
        vc = spawn(unreal.VolumetricCloud, unreal.Vector(0, 0, 0), label='Clouds', folder='Lighting')
        vcc = vc.get_component_by_class(unreal.VolumetricCloudComponent)
        cl = P['clouds']
        mat = unreal.load_asset('/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst')
        if cl.get('mi'): mat = make_cloud_mi(name, cl['mi']) or mat   # (round 03) overcast: own instance of the engine cloud material (coverage / density / albedo)
        if mat: setp(vcc, 'material', mat, 'Clouds')
        else: MISS.append('Clouds: m_SimpleVolumetricCloud_Inst missing')
        for k in ('layer_bottom_altitude', 'layer_height', 'tracing_max_distance'): setp(vcc, k, float(cl[k]), 'Clouds')
        setp(vcc, 'view_sample_count_scale', 0.6, 'Clouds'); setp(vcc, 'shadow_view_sample_count_scale', 0.3, 'Clouds')
        setp(vcc, 'reflection_view_sample_count_scale_value', 0.5, 'Clouds')
    # --- exponential height fog: near-clear canyon, aerial haze band, volumetric fog for light shafts, a second high haze layer
    fog = spawn(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), label='HeightFog', folder='Lighting')
    fc = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    for k, v in P['fog'].items():
        if k == 'haze':
            sf = fc.get_editor_property('second_fog_data')
            for hk, hv in v.items(): setp(sf, hk, hv, 'Fog.second')
            setp(fc, 'second_fog_data', sf, 'Fog')
        else:
            setp(fc, k, conv(v), 'Fog')
    # --- post process: exposure, Lumen, bloom / lens, filmic tonemapper, grade, motion blur, AO
    ppv = spawn(unreal.PostProcessVolume, unreal.Vector(0, 0, 0), label='PostProcess', folder='Lighting')
    ppv.set_editor_property('unbound', True); ppv.set_editor_property('priority', 10.0)
    st = ppv.get_editor_property('settings')
    ex = P['exposure']
    post = {'auto_exposure_min_brightness': ex['min_ev'], 'auto_exposure_max_brightness': ex['max_ev'],
            'auto_exposure_bias': ex['bias'], 'auto_exposure_speed_up': 6.0, 'auto_exposure_speed_down': 3.0, 'auto_exposure_low_percent': 70.0,
            'auto_exposure_high_percent': 98.0, 'auto_exposure_apply_physical_camera_exposure': False,
            'ambient_occlusion_quality': 60.0, 'ambient_occlusion_power': 1.6}
    for k, en, names in (('auto_exposure_method', 'AutoExposureMethod', ('AEM_HISTOGRAM',)), ('dynamic_global_illumination_method', 'DynamicGlobalIlluminationMethod', ('LUMEN', 'DGIM_LUMEN')),
                         ('reflection_method', 'ReflectionMethod', ('LUMEN', 'RM_LUMEN')), ('bloom_method', 'BloomMethod', ('BM_SOG',))):
        cls = getattr(unreal, en, None); v = next((getattr(cls, n) for n in names if cls is not None and hasattr(cls, n)), None)
        if v is None: MISS.append('enum %s.%s missing' % (en, names))
        else: post[k] = v
    for k, v in P['post'].items(): post[k] = conv(v) if isinstance(v, list) else v
    for k, v in post.items():
        if setp(st, 'override_' + k, True, 'PostProcess'): setp(st, k, v, 'PostProcess')
    ppv.set_editor_property('settings', st)
    # --- night: procedural star dome (additive, unlit) so the sky is not an empty black gradient
    if P['mpc'].get('NightK', 0.0) > 0.5: build_stars()
    # --- MPC_City through a Level Sequence (auto-plays at level start): night lights of the city materials
    build_mpc_sequence(name, P['mpc'], world)
    unreal.EditorLoadingAndSavingUtils.save_map(world, path)
    log('rig', name)

def make_cloud_mi(name, d):
    """/Game/Look/MI_LookClouds_<preset>: instance of the engine's m_SimpleVolumetricCloud with the preset's coverage / density / albedo
    (parameters: Cloud_GlobalCoverage, Cloud_GlobalDensity, Cloud_AlbedoColor, Layout_CloudGlobalScale; engine defaults -0.2 / 0.008 / 0.98)"""
    parent = unreal.load_asset('/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud')
    if not parent: MISS.append('m_SimpleVolumetricCloud missing'); return None
    path = LOOK + '/MI_LookClouds_' + name
    if EAL.does_asset_exist(path): mi = unreal.load_asset(path)
    else: mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset('MI_LookClouds_' + name, LOOK, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel = unreal.MaterialEditingLibrary
    mel.set_material_instance_parent(mi, parent)
    for k, v in d.get('scalars', {}).items(): mel.set_material_instance_scalar_parameter_value(mi, k, float(v))
    for k, v in d.get('vectors', {}).items(): mel.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(*[float(x) for x in v]))
    EAL.save_asset(path)
    return mi

def build_stars():
    MAT_PATH = LOOK + '/M_LookStars'
    mel = unreal.MaterialEditingLibrary
    if EAL.does_asset_exist(MAT_PATH): EAL.delete_asset(MAT_PATH)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_LookStars', LOOK, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT); m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property('two_sided', True)
    code = mel.create_material_expression(m, unreal.MaterialExpressionCustom, -600, 0)
    code.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ci = unreal.CustomInput(); ci.set_editor_property('input_name', 'D'); code.set_editor_property('inputs', [ci])
    code.set_editor_property('code', r"""
float3 d = normalize(D);
float3 g = d * 260.0; float3 c = floor(g); float3 f = frac(g) - 0.5;
float h = frac(sin(dot(c, float3(12.9898, 78.233, 37.719))) * 43758.5453);
float h2 = frac(h * 91.7 + 0.31);
float star = step(0.9935, h) * smoothstep(0.42, 0.0, length(f));
float3 tint = lerp(float3(0.75, 0.85, 1.0), float3(1.0, 0.85, 0.7), h2);
float horizon = smoothstep(0.02, 0.35, d.z);
return tint * star * (0.4 + 1.6 * h2) * horizon * 135.0;""")   # 6.0 under the old EV 1 exposure; x22.5 for the night exposure (white point 54 cd/m2)
    wp = mel.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -900, 0)
    cam = mel.create_material_expression(m, unreal.MaterialExpressionCameraPositionWS, -900, 120)
    sub = mel.create_material_expression(m, unreal.MaterialExpressionSubtract, -750, 0)
    mel.connect_material_expressions(wp, '', sub, 'A'); mel.connect_material_expressions(cam, '', sub, 'B')
    mel.connect_material_expressions(sub, '', code, 'D')
    mel.connect_material_property(code, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(m); EAL.save_asset(MAT_PATH)
    dome = spawn(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), label='StarDome', folder='Lighting')
    dome.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Sphere'))
    dome.static_mesh_component.set_material(0, m)
    dome.set_actor_scale3d(unreal.Vector(6000, 6000, 6000))  # 300 km radius: outside the atmosphere shell, inside the far plane
    dome.static_mesh_component.set_cast_shadow(False)
    dome.static_mesh_component.set_collision_profile_name('NoCollision')  # a 600 km WorldStatic sphere would be one giant traversal "building box"
    dome.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    dome.static_mesh_component.set_editor_property('cast_dynamic_shadow', False)

def build_mpc_sequence(name, values, world):
    """MPC_City parameter values of the preset, applied at level start by a Level Sequence with an MPC track (holds the values)."""
    mpc = unreal.load_asset(MPC)
    if not mpc: MISS.append('MPC_City missing'); return
    seq_path = '%s/LS_Look_%s' % (RIGS, name)
    if EAL.does_asset_exist(seq_path): EAL.delete_asset(seq_path)
    seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset('LS_Look_' + name, RIGS, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    try:
        seq.set_display_rate(unreal.FrameRate(30, 1)); seq.set_playback_start(0); seq.set_playback_end(30 * 60)
        tr = seq.add_track(unreal.MovieSceneMaterialParameterCollectionTrack)
        tr.set_editor_property('mpc', mpc)
        sec = tr.add_section()
        sec.set_range(0, 30 * 60)
        for k, v in values.items():
            sec.add_scalar_parameter_key(k, unreal.FrameNumber(0), float(v))
        EAL.save_asset(seq_path)
        act = spawn(unreal.LevelSequenceActor, unreal.Vector(0, 0, 0), label='MPC_City_' + name, folder='Lighting')
        act.set_editor_property('level_sequence_asset', seq)
        ps = act.get_editor_property('playback_settings'); ps.set_editor_property('auto_play', True); ps.set_editor_property('loop_count', unreal.MovieSceneSequenceLoopCount(value=-1))
        act.set_editor_property('playback_settings', ps)
    except Exception as e:
        MISS.append('mpc sequence %s: %s' % (name, str(e).split('\n')[0][:160]))


# ------------------------------------------------------------------------------------------------ step night
# /Game/Look/Look_NightLights (added to the night maps as an always-loaded sublevel by step maps). Everything is driven by
# presets.night.lights in look_presets.json and by the browser's own layout (layout.json):
#   * a spot light + a small halo point light + an emissive head at every street lamp (instances.lamp, head = base + arm 2.9 m, 9.15 m up)
#   * storefront spill: spot lights on the street-facing ground-floor faces of the building footprints, onto the sidewalks
#   * STAND-IN TRAFFIC (P6 owns real traffic later): dark box car proxies (no collision) in the avenue / street lanes with head lights
#     (spot on the road, emissive) and tail lights (red point, emissive) so the roadway has light pools and moving-looking colour
#   * a deferred decal over the whole city that makes street and sidewalk surfaces damp (lower roughness, darker) so pools read
#   * AWHLookHeroLight (C++, Source/WebHomage/Look): rim + fill that follow the player's pawn on lighting channel 1
NIGHT = sm2_common.NIGHT_LIGHTS_LEVEL
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
def add_component(actor, cls):
    root = sds.k2_gather_subobject_data_for_instance(actor)[0]
    h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=cls, blueprint_context=None))
    return unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h))

def cfg(obj, props, what=''):
    for k, v in props.items(): setp(obj, k, v, what)

def pick(rng, items, weights):
    r, a = rng.random() * sum(weights), 0.0
    for it, w in zip(items, weights):
        a += w
        if r <= a: return it
    return items[-1]

def make_mat(name, build, **props):
    """(re)create /Game/Look/<name> as a Material; build(m, mel) wires the graph"""
    path = LOOK + '/' + name
    if EAL.does_asset_exist(path): EAL.delete_asset(path)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, LOOK, unreal.Material, unreal.MaterialFactoryNew())
    for k, v in props.items(): setp(m, k, v, name)
    mel = unreal.MaterialEditingLibrary
    build(m, mel)
    for u in (unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES,):
        try: mel.set_material_usage(m, u)
        except Exception as e: MISS.append('%s usage %s' % (name, str(e).split('\n')[0][:80]))
    mel.recompile_material(m); EAL.save_asset(path)
    return m

def mat_emissive(m, mel):
    """unlit-looking emissive: Color (vector param) x Gain (scalar param); black base"""
    c = mel.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -500, 0); c.set_editor_property('parameter_name', 'Color'); c.set_editor_property('default_value', unreal.LinearColor(1, 0.7, 0.4, 1))
    g = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -500, 160); g.set_editor_property('parameter_name', 'Gain'); g.set_editor_property('default_value', 20.0)
    mul = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, 0)
    mel.connect_material_expressions(c, '', mul, 'A'); mel.connect_material_expressions(g, '', mul, 'B')
    mel.connect_material_property(mul, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)

def mat_car(m, mel):
    """dark car paint: per-instance random colour from a palette, glossy so the lamps read as reflections"""
    r = mel.create_material_expression(m, unreal.MaterialExpressionPerInstanceRandom, -700, 0)
    code = mel.create_material_expression(m, unreal.MaterialExpressionCustom, -450, 0)
    code.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ci = unreal.CustomInput(); ci.set_editor_property('input_name', 'R'); code.set_editor_property('inputs', [ci])
    code.set_editor_property('code', r"""
float3 c;
if (R < 0.22) c = float3(0.012, 0.012, 0.014);
else if (R < 0.42) c = float3(0.05, 0.052, 0.058);
else if (R < 0.60) c = float3(0.30, 0.31, 0.33);
else if (R < 0.72) c = float3(0.34, 0.34, 0.33);
else if (R < 0.82) c = float3(0.02, 0.04, 0.11);
else if (R < 0.90) c = float3(0.13, 0.015, 0.015);
else if (R < 0.95) c = float3(0.6, 0.42, 0.02);
else c = float3(0.08, 0.14, 0.1);
return c;""")
    mel.connect_material_expressions(r, '', code, 'R')
    mel.connect_material_property(code, '', unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -450, 200); rough.set_editor_property('r', 0.24)
    mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    met = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -450, 280); met.set_editor_property('r', 0.55)
    mel.connect_material_property(met, '', unreal.MaterialProperty.MP_METALLIC)

def mat_glass(m, mel):
    c = mel.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -450, 0); c.set_editor_property('constant', unreal.LinearColor(0.006, 0.008, 0.012, 1))
    mel.connect_material_property(c, '', unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -450, 200); rough.set_editor_property('r', 0.05)
    mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    sp = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -450, 280); sp.set_editor_property('r', 0.9)
    mel.connect_material_property(sp, '', unreal.MaterialProperty.MP_SPECULAR)

def mat_screen(m, mel):
    """(round 03) abstract LED video-wall content for the Times-Square-like screens (the ads of the port are IP-excluded, the screens' own emission is black):
    1-3 x 1-2 "ad" cells per panel, each a two-colour gradient with a soft blob and fake text rows (bars, no glyphs), a per-cell brightness, an LED dot grid, a rare flash,
    tinted by the instance's Tint; NO text, NO logos, NO imagery. Unlit (emissive only)."""
    uv = mel.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -900, 0)
    tm = mel.create_material_expression(m, unreal.MaterialExpressionTime, -900, 120)
    rn = mel.create_material_expression(m, unreal.MaterialExpressionPerInstanceRandom, -900, 240)
    tint = mel.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -600, 320); tint.set_editor_property('parameter_name', 'Tint'); tint.set_editor_property('default_value', unreal.LinearColor(1, 0.3, 0.6, 1))
    gain = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, 420); gain.set_editor_property('parameter_name', 'Gain'); gain.set_editor_property('default_value', 8.0)
    asp = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -900, 380); asp.set_editor_property('parameter_name', 'Aspect'); asp.set_editor_property('default_value', 1.0)
    code = mel.create_material_expression(m, unreal.MaterialExpressionCustom, -600, 0)
    code.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ins = []
    for nm in ('UV', 'T', 'R', 'C', 'A'):
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', nm); ins.append(ci)
    code.set_editor_property('inputs', ins)
    code.set_editor_property('code', r"""
float ar = max(A, 0.05);
float tgt = 0.55 + 0.9 * frac(R * 5.17);
float nx = 1.0 + floor(frac(R * 3.71) * 1.99);
float ny = clamp(floor(ar * nx / tgt + 0.5), 1.0, 8.0);
float2 g = UV * float2(nx, ny);
float2 cell = floor(g);
float2 f = frac(g);
float ch = frac(sin(dot(cell + R * 13.7, float2(12.9898, 78.233))) * 43758.5453);
float ch2 = frac(ch * 91.3 + 0.17);
float ch3 = frac(ch2 * 47.1 + 0.53);
float t = T * (0.15 + 0.2 * ch2);
float3 pa = 0.5 + 0.5 * cos(6.2831 * (ch + float3(0.0, 0.33, 0.67)));
float3 pb = 0.5 + 0.5 * cos(6.2831 * (ch2 + 0.4 + float3(0.0, 0.33, 0.67)));
float3 bg = lerp(pa, pb, saturate(f.y * 0.9 + 0.1 * sin(t * 3.0 + f.x * 4.0)));
float2 bc = float2(0.3 + 0.4 * ch3, 0.5) + 0.12 * float2(sin(t * 2.0), cos(t * 1.7));
float blob = smoothstep(0.42, 0.10, length((f - bc) * float2(1.0, 1.4)));
float3 fg = lerp(bg, lerp(C, float3(1.0, 1.0, 1.0), 0.65), blob);
float rows = step(0.5, frac(f.y * 14.0)) * step(f.y, 0.34) * step(f.x, 0.25 + 0.55 * frac(floor(f.y * 14.0) * 0.618 + ch));
fg = lerp(fg, float3(1.0, 1.0, 1.0), rows * 0.85);
float edge = smoothstep(0.0, 0.03, f.x) * smoothstep(1.0, 0.97, f.x) * smoothstep(0.0, 0.03, f.y) * smoothstep(1.0, 0.97, f.y);
float gain = 0.3 + 0.7 * ch3;
float2 dg = frac(UV * float2(150.0, 150.0 * ar));
float dots = smoothstep(0.05, 0.3, dg.x) * smoothstep(0.05, 0.3, dg.y);
float flash = smoothstep(0.985, 1.0, sin(T * (0.6 + 0.4 * R) + R * 40.0)) * 1.6;
float3 outc = fg * gain * edge * (0.7 + 0.3 * dots);
outc = lerp(outc, outc * C * 2.0, 0.35);
return outc + C * flash * 0.3;""")
    mel.connect_material_expressions(uv, '', code, 'UV'); mel.connect_material_expressions(tm, '', code, 'T'); mel.connect_material_expressions(rn, '', code, 'R'); mel.connect_material_expressions(tint, '', code, 'C'); mel.connect_material_expressions(asp, '', code, 'A')
    mul = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, 60)
    mel.connect_material_expressions(code, '', mul, 'A'); mel.connect_material_expressions(gain, '', mul, 'B')
    mel.connect_material_property(mul, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)

def mat_wet(W):
    def build(m, mel):
        # world position + reconstructed geometric normal (from depth derivatives) -> puddle / damp mask
        wp = mel.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -900, 0)
        code = mel.create_material_expression(m, unreal.MaterialExpressionCustom, -600, 0)
        code.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT4)
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', 'P'); code.set_editor_property('inputs', [ci])
        code.set_editor_property('code', """
float3 pm = P * 0.01;
float3 dx = ddx(pm), dy = ddy(pm);
float3 n = normalize(cross(dx, dy));
float up = saturate((abs(n.z) - 0.86) / 0.1);
float2 q = pm.xy;
float h1 = frac(sin(dot(floor(q / 5.5), float2(12.9898, 78.233))) * 43758.5453);
float h2 = frac(sin(dot(floor(q / 5.5) + float2(1, 0), float2(12.9898, 78.233))) * 43758.5453);
float h3 = frac(sin(dot(floor(q / 5.5) + float2(0, 1), float2(12.9898, 78.233))) * 43758.5453);
float h4 = frac(sin(dot(floor(q / 5.5) + float2(1, 1), float2(12.9898, 78.233))) * 43758.5453);
float2 f = frac(q / 5.5); f = f * f * (3.0 - 2.0 * f);
float n1 = lerp(lerp(h1, h2, f.x), lerp(h3, h4, f.x), f.y);
float g1 = frac(sin(dot(floor(q / 1.4), float2(39.346, 11.135))) * 43758.5453);
float g2 = frac(sin(dot(floor(q / 1.4) + float2(1, 0), float2(39.346, 11.135))) * 43758.5453);
float g3 = frac(sin(dot(floor(q / 1.4) + float2(0, 1), float2(39.346, 11.135))) * 43758.5453);
float g4 = frac(sin(dot(floor(q / 1.4) + float2(1, 1), float2(39.346, 11.135))) * 43758.5453);
float2 f2 = frac(q / 1.4); f2 = f2 * f2 * (3.0 - 2.0 * f2);
float n2 = lerp(lerp(g1, g2, f2.x), lerp(g3, g4, f2.x), f2.y);
float pud = smoothstep(0.52, 0.72, n1 * 0.7 + n2 * 0.3);
return float4(up, pud, 0, 0);""")
        mel.connect_material_expressions(wp, '', code, 'P')
        # opacity = up * (base + (puddle - base) * pud); roughness lerp(dry, wet, ...)
        def k(v, y):
            e = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -300, y); e.set_editor_property('r', float(v)); return e
        def op(cls, a, b, x, y, ia='A', ib='B'):
            e = mel.create_material_expression(m, cls, x, y); mel.connect_material_expressions(a, '', e, ia); mel.connect_material_expressions(b, '', e, ib); return e
        mask = mel.create_material_expression(m, unreal.MaterialExpressionComponentMask, -450, -100); mask.set_editor_property('r', True); mask.set_editor_property('g', False); mask.set_editor_property('b', False); mask.set_editor_property('a', False)
        mel.connect_material_expressions(code, '', mask, '')
        maskp = mel.create_material_expression(m, unreal.MaterialExpressionComponentMask, -450, 60); maskp.set_editor_property('r', False); maskp.set_editor_property('g', True); maskp.set_editor_property('b', False); maskp.set_editor_property('a', False)
        mel.connect_material_expressions(code, '', maskp, '')
        lerp_o = mel.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -250, 60)
        mel.connect_material_expressions(k(W['base'], 0), '', lerp_o, 'A'); mel.connect_material_expressions(k(W['puddle'], 40), '', lerp_o, 'B'); mel.connect_material_expressions(maskp, '', lerp_o, 'Alpha')
        opac = op(unreal.MaterialExpressionMultiply, mask, lerp_o, -100, 0)
        mel.connect_material_property(opac, '', unreal.MaterialProperty.MP_OPACITY)
        lerp_r = mel.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -250, 200)
        mel.connect_material_expressions(k(W['rough_dry'], 160), '', lerp_r, 'A'); mel.connect_material_expressions(k(W['rough_wet'], 200), '', lerp_r, 'B'); mel.connect_material_expressions(maskp, '', lerp_r, 'Alpha')
        mel.connect_material_property(lerp_r, '', unreal.MaterialProperty.MP_ROUGHNESS)
        bc = mel.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -250, 300); bc.set_editor_property('constant', unreal.LinearColor(0.012, 0.014, 0.02, 1))
        mel.connect_material_property(bc, '', unreal.MaterialProperty.MP_BASE_COLOR)
        sp = k(0.55, 340); mel.connect_material_property(sp, '', unreal.MaterialProperty.MP_SPECULAR)
    return make_mat('M_LookWet', build, material_domain=unreal.MaterialDomain.MD_DEFERRED_DECAL, blend_mode=unreal.BlendMode.BLEND_TRANSLUCENT)

def make_mi(name, parent, vec=None, scal=None):
    path = LOOK + '/' + name
    if EAL.does_asset_exist(path): EAL.delete_asset(path)
    mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, LOOK, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent)
    for k, v in (vec or {}).items(): unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(*v))
    for k, v in (scal or {}).items(): unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, k, float(v))
    EAL.save_asset(path)
    return mi

def kelvin_rgb(t):
    """approximate blackbody colour (linear-ish, max 1) for the emissive lamp heads"""
    t = t / 100.0
    r = 1.0 if t <= 66 else max(0.0, min(1.0, 1.2929 * ((t - 60) ** -0.1332)))
    g = max(0.0, min(1.0, 0.39008 * math.log(t) - 0.63184)) if t <= 66 else max(0.0, min(1.0, 1.1298 * ((t - 60) ** -0.0755)))
    b = 1.0 if t >= 66 else (0.0 if t <= 19 else max(0.0, min(1.0, 0.54321 * math.log(t - 10) - 1.19625)))
    return (r ** 2.2, g ** 2.2, b ** 2.2, 1.0)

def spawn_spot(loc, rot, label, folder, cd, outer, inner, radius, temp, vol=0.0, maxd=0.0, indirect=1.0, color=None):
    a = spawn(unreal.SpotLight, loc, rot, label, folder)
    lc = a.get_component_by_class(unreal.SpotLightComponent)
    lc.set_mobility(unreal.ComponentMobility.MOVABLE)
    cfg(lc, {'intensity_units': unreal.LightUnits.CANDELAS, 'intensity': float(cd), 'use_temperature': True, 'temperature': float(temp), 'attenuation_radius': float(radius),
             'outer_cone_angle': float(outer), 'inner_cone_angle': float(inner), 'source_radius': 8.0, 'cast_shadows': False, 'volumetric_scattering_intensity': float(vol),
             'indirect_lighting_intensity': float(indirect)}, 'SpotLight')
    if color: cfg(lc, {'use_temperature': False, 'light_color': unreal.Color(r=int(255 * color[0]), g=int(255 * color[1]), b=int(255 * color[2]), a=255)}, 'SpotLight')
    if maxd: cfg(lc, {'max_draw_distance': float(maxd), 'max_distance_fade_range': float(maxd) * 0.2}, 'SpotLight')
    return a

def spawn_point(loc, label, folder, cd, radius, temp=None, color=None, vol=0.0, maxd=0.0, indirect=1.0):
    a = spawn(unreal.PointLight, loc, unreal.Rotator(0, 0, 0), label, folder)
    lc = a.get_component_by_class(unreal.PointLightComponent)
    lc.set_mobility(unreal.ComponentMobility.MOVABLE)
    cfg(lc, {'intensity_units': unreal.LightUnits.CANDELAS, 'intensity': float(cd), 'attenuation_radius': float(radius), 'source_radius': 6.0, 'cast_shadows': False,
             'volumetric_scattering_intensity': float(vol), 'indirect_lighting_intensity': float(indirect)}, 'PointLight')
    if temp: cfg(lc, {'use_temperature': True, 'temperature': float(temp)}, 'PointLight')
    if color: cfg(lc, {'light_color': unreal.Color(r=int(255 * color[0]), g=int(255 * color[1]), b=int(255 * color[2]), a=255)}, 'PointLight')
    if maxd: cfg(lc, {'max_draw_distance': float(maxd), 'max_distance_fade_range': float(maxd) * 0.2}, 'PointLight')
    return a

def ism(label, mesh, mat, folder='NightLights', shadow=False):
    a = spawn(unreal.Actor, unreal.Vector(0, 0, 0), label=label, folder=folder)
    c = add_component(a, unreal.HierarchicalInstancedStaticMeshComponent)
    c.set_static_mesh(mesh); c.set_material(0, mat)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); c.set_collision_profile_name('NoCollision')
    c.set_editor_property('cast_shadow', shadow)
    return c

def build_night_legacy():   # the old night-light system (Look_NightLights): unused, replaced by build_night below
    L = PRE['night']['lights']
    layout = json.load(open(os.path.join(EXPORT, 'layout.json')))
    world = open_level(NIGHT)
    CUBE, SPHERE, CYL = (unreal.load_asset('/Engine/BasicShapes/' + n) for n in ('Cube', 'Sphere', 'Cylinder'))
    # ---- materials
    m_em = make_mat('M_LookEmissive', mat_emissive, shading_model=unreal.MaterialShadingModel.MSM_UNLIT)
    m_car = make_mat('M_LookCarPaint', mat_car)
    m_glass = make_mat('M_LookCarGlass', mat_glass)
    lc_ = L['lamps']
    glow = {t: make_mi('MI_LookGlow_%d' % t, m_em, vec={'Color': kelvin_rgb(t)}, scal={'Gain': lc_['glow_gain']}) for t in lc_['temps']}
    mi_head = make_mi('MI_LookHead', m_em, vec={'Color': (1.0, 0.92, 0.8, 1)}, scal={'Gain': L['cars']['head_gain']})
    mi_tail = make_mi('MI_LookTail', m_em, vec={'Color': (1.0, 0.03, 0.01, 1)}, scal={'Gain': L['cars']['tail_gain']})
    n_l = 0
    # ---- street lamps
    rng = random.Random(3)
    glow_c = {t: ism('LampGlow_%d' % t, SPHERE, glow[t]) for t in lc_['temps']}
    glow_x = {t: [] for t in lc_['temps']}
    for i, it in enumerate(layout['instances']['lamp']['items']):
        ry = it.get('ry', 0.0)
        hx, hy, hz = it['x'] + lc_['arm'] * math.sin(ry), it['y'] + lc_['head_h'], it['z'] + lc_['arm'] * math.cos(ry)
        t = pick(rng, lc_['temps'], lc_['weights'])
        loc = U(hx, hy, hz)
        spawn_spot(loc, unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0), 'LampSpot_%d' % i, 'NightLights/Lamps', lc_['spot_cd'] * rng.uniform(0.85, 1.15), lc_['spot_outer'], lc_['spot_inner'],
                   lc_['spot_radius'], t, vol=lc_['volumetric'], maxd=lc_['max_draw'], indirect=lc_.get('indirect', 1.0))
        spawn_point(loc - unreal.Vector(0, 0, 30), 'LampHalo_%d' % i, 'NightLights/Lamps', lc_['halo_cd'], lc_['halo_radius'], temp=t, maxd=lc_.get('halo_max_draw', lc_['max_draw'] * 0.7))
        s = lc_['glow_size_cm'] / 100.0
        glow_x[t].append(unreal.Transform(loc - unreal.Vector(0, 0, 12), unreal.Rotator(0, 0, 0), unreal.Vector(s, s, s * 0.55)))
        n_l += 1
    for t in lc_['temps']: glow_c[t].add_instances(glow_x[t], False, True)
    log('night: %d lamps' % n_l)
    # ---- storefront spill
    S = L['storefront']; n_s = 0
    if S.get('enabled'):
        rng = random.Random(11)
        blocks = layout['blocks']
        def block_of(f):
            cx, cz = (f['x0'] + f['x1']) / 2, (f['z0'] + f['z1']) / 2
            return next((b for b in blocks if b['x0'] <= cx <= b['x1'] and b['z0'] <= cz <= b['z1']), None)
        for f in layout['footprints']:
            b = block_of(f)
            if not b: continue
            faces = []   # (normal x, normal z, along-axis 'x'|'z', fixed coord, a0, a1)
            if abs(f['x1'] - b['x1']) < S['face_tol']: faces.append((1, 0, 'z', f['x1'], f['z0'], f['z1']))
            if abs(f['x0'] - b['x0']) < S['face_tol']: faces.append((-1, 0, 'z', f['x0'], f['z0'], f['z1']))
            if abs(f['z1'] - b['z1']) < S['face_tol']: faces.append((0, 1, 'x', f['z1'], f['x0'], f['x1']))
            if abs(f['z0'] - b['z0']) < S['face_tol']: faces.append((0, -1, 'x', f['z0'], f['x0'], f['x1']))
            for nx, nz, ax, fixed, a0, a1 in faces:
                if a1 - a0 < S['min_face']: continue
                k = max(1, int((a1 - a0) / S['spacing']))
                for j in range(k):
                    a = a0 + (j + 0.5) * (a1 - a0) / k
                    x, z = (fixed + nx * S['setback'], a) if ax == 'z' else (a, fixed + nz * S['setback'])
                    if rng.random() > 0.8: continue
                    t = pick(rng, S['temps'], S['weights'])
                    yaw = math.degrees(math.atan2(nz, nx))
                    spawn_spot(U(x, S['height'], z), unreal.Rotator(pitch=S['pitch'], yaw=yaw, roll=0.0), 'Shop_%d' % n_s, 'NightLights/Storefront', S['spot_cd'] * rng.uniform(0.6, 1.4),
                               S['outer'], S['inner'], S['radius'], t, vol=0.2, maxd=S['max_draw'])
                    n_s += 1
    log('night: %d storefront lights' % n_s)
    # ---- Times-Square-like screen glow (screen quads: look_ts_screens.json)
    T = L.get('screens', {}); n_t = 0; n_q = 0
    if T.get('enabled'):
        rng = random.Random(29)
        cols = T['palette']['colors']
        plane = unreal.load_asset('/Engine/BasicShapes/Plane')
        m_scr = make_mat('M_LookScreen', mat_screen, shading_model=unreal.MaterialShadingModel.MSM_UNLIT, two_sided=True) if T.get('content', {}).get('enabled') else None
        quad_c, quad_x = {}, {}
        def quad_group(i, b):   # one instanced component per (palette colour, aspect bin: panel height / width = 2 ** b)
            if (i, b) not in quad_c:
                col = cols[i]
                mi_s = make_mi('MI_LookScreen_%d_%d' % (i, b + 4), m_scr, vec={'Tint': (col[0], col[1], col[2], 1.0)}, scal={'Gain': T['content']['gain'], 'Aspect': float(2.0 ** b)})
                quad_c[(i, b)] = ism('ScreenContent_%d_%d' % (i, b + 4), plane, mi_s, folder='NightLights/Screens'); quad_x[(i, b)] = []
            return quad_x[(i, b)]
        for k, sc in enumerate(json.load(open(os.path.join(HERE, 'look_ts_screens.json')))['screens']):
            nrm, c = sc['n'], sc['c']
            if abs(nrm[1]) > 0.5: continue   # vertical screens only
            col = pick(rng, cols, T['palette']['weights'])
            pos = (c[0] + nrm[0] * T['offset'], c[1], c[2] + nrm[2] * T['offset'])
            spawn_spot(U(*pos), unreal.Rotator(pitch=T['pitch'], yaw=math.degrees(math.atan2(nrm[2], nrm[0])), roll=0.0), 'TSScreen_%d' % k, 'NightLights/Screens', T['cd_per_sqrt_area'] * math.sqrt(sc['a']),
                       T['outer'], T['inner'], T['radius'], 6500, vol=T['volumetric'], maxd=T['max_draw'], color=col)
            n_t += 1
            if m_scr and sc.get('w') and sc.get('h'):   # emissive stand-in content quad, 5 cm in front of the (black) screen, facing the same way
                nu = unreal.Vector(nrm[0], nrm[2], nrm[1])                      # browser normal -> UE
                tx = unreal.Vector(-nu.y, nu.x, 0.0); tl = math.hypot(tx.x, tx.y)
                if tl < 1e-3: continue
                tx = unreal.Vector(tx.x / tl, tx.y / tl, 0.0)
                rot = unreal.MathLibrary.make_rot_from_zx(nu, tx)
                loc = U(c[0] + nrm[0] * T['content']['offset'], c[1], c[2] + nrm[2] * T['content']['offset'])
                quad_group(cols.index(col), max(-4, min(4, int(round(math.log2(max(sc['h'], 0.1) / max(sc['w'], 0.1))))))).append(unreal.Transform(loc, rot, unreal.Vector(sc['w'], sc['h'], 1.0)))
                n_q += 1
        for key, c_ in quad_c.items(): c_.add_instances(quad_x[key], False, True)
    log('night: %d screen lights, %d content quads' % (n_t, n_q))
    # ---- stand-in traffic
    C = L['cars']; n_c = 0
    if C.get('enabled'):
        rng = random.Random(C['seed'])
        clear = [(s['pos'][0], s['pos'][2]) for s in SHOTS] + [(s['player'][0], s['player'][2]) for s in SHOTS]
        body = ism('CarBody', CUBE, m_car, shadow=False); cab = ism('CarCabin', CUBE, m_glass); whl = ism('CarWheels', CYL, m_glass); hl = ism('CarHeadlights', CUBE, mi_head); tl = ism('CarTaillights', CUBE, mi_tail)
        bx, cx_, wx, hx_, tx_ = [], [], [], [], []
        def add_car(px, pz, yaw_deg, idx):
            rr = unreal.Rotator(0, 0, yaw_deg)
            yaw = math.radians(yaw_deg); fx, fy = math.cos(yaw), math.sin(yaw); sx, sy = -fy, fx     # forward / right in UE XY
            kind = rng.random()                                      # 0..0.2 SUV / van (taller, longer cabin), rest sedans of slightly different length
            L_ = 4.3 + 0.5 * rng.random() + (0.35 if kind < 0.2 else 0.0)
            Hb, Hc = (0.62, 0.66) if kind < 0.2 else (0.5, 0.5)
            def at(f, r, z): return unreal.Vector((px + f * fx + r * sx) * 100.0, (pz + f * fy + r * sy) * 100.0, z * 100.0)
            bx.append(unreal.Transform(at(0, 0, 0.30 + Hb / 2), rr, unreal.Vector(L_, 1.82, Hb)))                       # lower body (paint)
            cl = L_ * (0.62 if kind < 0.2 else 0.5)
            cx_.append(unreal.Transform(at(-0.12 * L_, 0, 0.30 + Hb + Hc / 2 - 0.02), rr, unreal.Vector(cl, 1.50, Hc)))    # greenhouse (glass)
            bx.append(unreal.Transform(at(-0.12 * L_, 0, 0.30 + Hb + Hc + 0.02), rr, unreal.Vector(cl * 0.88, 1.46, 0.06)))  # roof (paint)
            cx_.append(unreal.Transform(at(L_ / 2 - 0.02, 0, 0.42), rr, unreal.Vector(0.16, 1.80, 0.22)))                 # front bumper (dark)
            cx_.append(unreal.Transform(at(-L_ / 2 + 0.02, 0, 0.42), rr, unreal.Vector(0.16, 1.80, 0.22)))                # rear bumper (dark)
            for wf in (0.33 * L_, -0.31 * L_):
                for wr in (-0.86, 0.86):
                    wx.append(unreal.Transform(at(wf, wr, 0.32), unreal.Rotator(pitch=0, yaw=yaw_deg, roll=90), unreal.Vector(0.64, 0.64, 0.24)))
            for wr in (-0.66, 0.66):
                hx_.append(unreal.Transform(at(L_ / 2, wr, 0.62), rr, unreal.Vector(0.08, 0.40, 0.13)))
                tx_.append(unreal.Transform(at(-L_ / 2, wr, 0.70), rr, unreal.Vector(0.08, 0.42, 0.12)))
            spawn_spot(at(L_ / 2 + 0.1, 0, 0.66), unreal.Rotator(pitch=C['head_pitch'], yaw=yaw_deg, roll=0.0), 'CarHead_%d' % idx, 'NightLights/Cars', C['head_cd'] * rng.uniform(0.8, 1.2), C['head_outer'], C['head_inner'],
                       C['head_radius'], 4300, vol=0.3, maxd=C['max_draw'])
            spawn_point(at(-L_ / 2 - 0.4, 0, 0.72), 'CarTail_%d' % idx, 'NightLights/Cars', C['tail_cd'], C['tail_radius'], color=(1.0, 0.05, 0.02), maxd=C.get('tail_max_draw', C['max_draw'] * 0.7))
        idx = 0
        for st in layout['streets']:
            if 'x1' not in st: continue   # the diagonal Broadway polygon: no stand-in traffic
            w_x, w_z = st['x1'] - st['x0'], st['z1'] - st['z0']
            if st['kind'] == 'avenue' and w_z > 40 and w_x > 15: # N-S avenue block segment: lanes along z
                half = w_x / 2 - C['lane_edge_park']; n = 2; cxm = (st['x0'] + st['x1']) / 2
                lanes = [(cxm + (k + 0.5) * half / n, -90.0, 'nb', 'z') for k in range(n)] + [(cxm - (k + 0.5) * half / n, 90.0, 'sb', 'z') for k in range(n)]
                a0, a1 = st['z0'] + 8.0, st['z1'] - 8.0
            elif st['kind'] == 'street' and w_x > 40:
                half = w_z / 2 - C['lane_edge_park'] * 0.8; n = 1 if w_z < 14 else 2; czm = (st['z0'] + st['z1']) / 2
                lanes = [(czm + (k + 0.5) * half / n, 0.0, 'eb', 'x') for k in range(n)] + [(czm - (k + 0.5) * half / n, 180.0, 'wb', 'x') for k in range(n)]
                a0, a1 = st['x0'] + 8.0, st['x1'] - 8.0
            else: continue
            for (lane_c, yaw, _, axis) in lanes:
                a = a0 + rng.uniform(0, C['gap_max'])
                while a < a1 - 4.5:
                    px, pz = (lane_c, a) if axis == 'z' else (a, lane_c)
                    ok = rng.random() < C['fill'] and all(math.hypot(px - cx, pz - cz) > C['clear_radius'] for cx, cz in clear)
                    if ok: add_car(px, pz, yaw, idx); idx += 1
                    a += rng.uniform(C['gap_min'], C['gap_max'])
        for c_, xs in ((body, bx), (cab, cx_), (whl, wx), (hl, hx_), (tl, tx_)): c_.add_instances(xs, False, True)
        n_c = idx
    log('night: %d stand-in cars' % n_c)
    # ---- damp streets: one big deferred decal (roads + sidewalks), night only
    W = L['wet']
    if W.get('enabled'):
        m_wet = mat_wet(W)
        d = spawn(unreal.DecalActor, unreal.Vector(0, 0, W['z_center_cm']), unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0), 'WetStreets', 'NightLights')
        dc = d.get_component_by_class(unreal.DecalComponent)
        cfg(dc, {'decal_material': m_wet, 'decal_size': unreal.Vector(W['half_depth_cm'], W['half_size_cm'], W['half_size_cm']), 'fade_screen_size': 0.0}, 'Decal')
        d.set_actor_location(unreal.Vector(0, 0, W['z_center_cm']), False, False)
        log('night: wet-street decal')
    # ---- hero rim + fill (C++ actor)
    Hh = L['hero']
    if Hh.get('enabled'):
        cls = unreal.load_class(None, '/Script/WebHomage.WHLookHeroLight')
        if cls:
            h = spawn(cls, unreal.Vector(0, 0, 0), label='HeroLights', folder='NightLights')
            cfg(h, {'rim_intensity': float(Hh['rim_cd']), 'fill_intensity': float(Hh['fill_cd']), 'top_intensity': float(Hh['top_cd'])}, 'HeroLight')
        else: MISS.append('AWHLookHeroLight class missing (build the C++ module)')
    unreal.EditorLoadingAndSavingUtils.save_map(world, NIGHT)
    log('night level saved', NIGHT)

# ------------------------------------------------------------------------------------------------ step night (the author's night mode)
# /Game/Look/Look_NightCity = ONE AWHCityLights (the budgeted light pool + ambient, Source/WebHomage/Look/WHCityLights.cpp) + the hero fill
# lights + 6 emissive HISM components (NightEmissive actor) built from Content/Night/NightGeometry.json (tools/night/prep_night.py):
# neon tube segments, neon words (neon_words atlas), screen boards (ts_ads atlas), blade-sign faces (ts_signs atlas), signal lenses, lamp heads.
# Every emissive material multiplies MPC_City NightK, so it is dark by day. Emissive = browser pre-exposure radiance x K x EmissiveK.
NC = LOOK + '/NightCity'
NC_TEX = os.path.join(os.environ.get('SM2_NIGHT_TEX', os.path.join(os.path.expanduser('~'), 'sm2-n1/_scratch/night/tex')))

def _nc_missing(what):
    raise RuntimeError('night step: missing %s (run python3 tools/night/prep_night.py after tools/night/export_night.mjs)' % what)

def nc_import_textures():
    at = unreal.AssetToolsHelpers.get_asset_tools()
    spec = [('neon_words', 'T_NeonWords', False), ('ts_ads', 'T_TsAds', True), ('ts_signs', 'T_TsSigns', True)]
    for src, name, srgb in spec:
        f = os.path.join(NC_TEX, src + '.png')
        if not os.path.isfile(f): _nc_missing('texture ' + f + ' (sips -s format png <spiderbench>/public/assets/city/tex/%s.webp --out %s)' % (src, f))
    EAL.make_directory(NC + '/Textures')
    tasks = []
    for src, name, srgb in spec:
        t = unreal.AssetImportTask(); t.filename = os.path.join(NC_TEX, src + '.png'); t.destination_path = NC + '/Textures'; t.destination_name = name
        t.automated = True; t.replace_existing = True; t.save = False; tasks.append(t)
    at.import_asset_tasks(tasks)
    out = {}
    for src, name, srgb in spec:
        tex = unreal.load_asset(NC + '/Textures/' + name)
        if tex is None: _B.fail('texture import failed: ' + name); continue
        tex.set_editor_property('srgb', srgb)
        if not srgb: tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_VECTOR_DISPLACEMENTMAP)
        try: tex.set_editor_property('never_stream', True)
        except Exception as e: _B.warn('never_stream ' + name, e)
        EAL.save_asset(NC + '/Textures/' + name)
        out[name] = tex
    return out

def nc_material(name, code, inputs, em_k):
    """emissive-only unlit two-sided material for instanced meshes; code = HLSL body returning float3 emissive; inputs = [(name, kind, arg)]"""
    path = NC + '/' + name
    if EAL.does_asset_exist(path): EAL.delete_asset(path)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, NC, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property('two_sided', True)
    mel = unreal.MaterialEditingLibrary
    def ex(cls, x, y, **props):
        e = mel.create_material_expression(m, cls, x, y)
        for k, v in props.items(): e.set_editor_property(k, v)
        return e
    ins, y = [], -600
    for n, kind, arg in inputs:
        if kind == 'cd': e = ex(unreal.MaterialExpressionPerInstanceCustomData, -900, y, data_index=int(arg), const_default_value=0.0)
        elif kind == 'lp': e = ex(unreal.MaterialExpressionLocalPosition, -900, y)
        elif kind == 'tex': e = ex(unreal.MaterialExpressionTextureObject, -900, y, texture=arg[0], sampler_type=arg[1])
        elif kind == 'mpc': e = ex(unreal.MaterialExpressionCollectionParameter, -900, y, collection=unreal.load_asset(MPC), parameter_name=arg)
        elif kind == 'param': e = ex(unreal.MaterialExpressionScalarParameter, -900, y, parameter_name=n, default_value=float(arg))
        else: raise RuntimeError('input kind ' + kind)
        ins.append((n, e)); y += 100
    c = ex(unreal.MaterialExpressionCustom, -400, -300)
    c.set_editor_property('code', code); c.set_editor_property('description', name)
    c.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    cis = []
    for n, _ in ins:
        ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); cis.append(ci)
    c.set_editor_property('inputs', cis)
    for n, e in ins: mel.connect_material_expressions(e, '', c, n)
    mel.connect_material_property(c, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    try: mel.set_material_usage(m, unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES)
    except Exception as e: _B.fail(name + ' instanced usage', e)
    mel.recompile_material(m); EAL.save_asset(path)
    return m

# HLSL bodies of the night materials' Custom nodes and their input lists: the single source for build_night and tools/night/hlsl_check.py.
# Textures are sampled with UE's Texture2DSample() (never Tex.Sample): the material is also compiled for ray-tracing hit shaders (SF_METAL_SM6, lib_6_6 closesthit), where the implicit-derivative Sample opcode is invalid.
NC_HLSL = {
    'M_NightColor': 'return float3(CD0, CD1, CD2) * NK * EK;',
    'M_NightWord': 'float2 q = LP.xy * 0.01 + 0.5;\nfloat cell = CD3, asp = CD4;\nfloat2 sz = asp > 2.3077 ? float2(0.9, 0.9 / asp * 2.0) : float2(0.78 * asp * 0.5, 0.78);\nif (cell > 23.5) sz = float2(0.5, 1.0) / 1.12;\nfloat2 cuv = 0.5 + (q - 0.5) * min(sz * 1.12, float2(0.995, 0.995));\nfloat2 uv = float2((fmod(cell, 4.0) + cuv.x) / 4.0, (floor(cell / 4.0) + 1.0 - cuv.y) / 8.0);\nfloat2 nt = max(Texture2DSample(Tex, TexSampler, uv).rg - 0.02, 0.0) / 0.98;\nfloat2 eq = min(q, 1.0 - q);\nnt.g *= smoothstep(0.0, 0.12, min(eq.x, eq.y * 2.0));\nfloat3 col = float3(CD0, CD1, CD2);\nfloat3 e = col * nt.r + lerp(col, max(max(col.r, col.g), col.b).xxx, 0.25) * nt.r * nt.r * 0.2 + col * nt.g * GL;\nreturn e * WG * NK * EK;',
    'M_NightBoard': 'float2 q = LP.xy * 0.01 + 0.5;\nfloat3 c = CD7 > 0.5 ? Texture2DSample(Tex, TexSampler, float2(lerp(CD3, CD5, q.x), 1.0 - lerp(CD4, CD6, q.y))).rgb : float3(CD0, CD1, CD2);\nfloat m = max(max(c.r, c.g), c.b) + 1e-4;\nif (m > KN) { float w = TP - KN; float y = KN + w * (1.0 - exp(-(m - KN) / w)); c *= y / m; }\nreturn c * BG * NK * EK;',
    'M_NightBlade': 'float2 q = LP.xy * 0.01 + 0.5;\nfloat2 uv = float2(CD0 + q.y * CD2, 1.0 - (CD1 + (1.0 - q.x) * CD3));\nfloat3 bt = Texture2DSample(Tex, TexSampler, uv).rgb;\nfloat bm = max(max(bt.r, bt.g), bt.b) + 1e-4;\nfloat3 bn = bt / bm * pow(bm, 0.45) * 2.0;\nfloat ex = min(q.x, 1.0 - q.x) * 2.0, ey = min(q.y, 1.0 - q.y) * 2.0 * 2.3;\nfloat lit = 0.55 + 0.45 * smoothstep(0.0, 0.8, min(ex, ey));\nreturn bn * lit * SK * NK * EK;',
}
NC_INPUTS = {   # (input name, kind): kind cd = PerInstanceCustomData (index from the name), lp = LocalPosition, tex = TextureObject, mpc = MPC_City NightK, param = scalar parameter
    'M_NightColor': [('CD0', 'cd'), ('CD1', 'cd'), ('CD2', 'cd'), ('NK', 'mpc'), ('EK', 'param')],
    'M_NightWord': [('CD0', 'cd'), ('CD1', 'cd'), ('CD2', 'cd'), ('CD3', 'cd'), ('CD4', 'cd'), ('LP', 'lp'), ('Tex', 'tex'), ('NK', 'mpc'), ('EK', 'param'), ('WG', 'param'), ('GL', 'param')],
    'M_NightBoard': [('CD0', 'cd'), ('CD1', 'cd'), ('CD2', 'cd'), ('CD3', 'cd'), ('CD4', 'cd'), ('CD5', 'cd'), ('CD6', 'cd'), ('CD7', 'cd'), ('LP', 'lp'), ('Tex', 'tex'), ('NK', 'mpc'),
                    ('EK', 'param'), ('BG', 'param'), ('KN', 'param'), ('TP', 'param')],
    'M_NightBlade': [('CD0', 'cd'), ('CD1', 'cd'), ('CD2', 'cd'), ('CD3', 'cd'), ('LP', 'lp'), ('Tex', 'tex'), ('NK', 'mpc'), ('EK', 'param'), ('SK', 'param')],
}
NC_OUT = [('', 3)]

def night_custom_nodes():
    """(name, code, [(input name, kind)], outputs) of every Custom node the night step builds (read by tools/night/hlsl_check.py)"""
    return [(n, NC_HLSL[n], NC_INPUTS[n], NC_OUT) for n in NC_HLSL]

def nc_inputs(name, args):
    out = []
    for n, kind in NC_INPUTS[name]:
        out.append((n, kind, int(n[2:]) if kind == 'cd' else (0 if kind == 'lp' else ('NightK' if kind == 'mpc' else args[n]))))
    return out

def build_night():
    NJ = json.load(open(os.path.join(HERE, 'night_city.json')))
    nd = os.path.join(unreal.Paths.project_content_dir(), 'Night')
    for f in ('CityLights.bin', 'CityLights.meta.json', 'NightGeometry.json'):
        if not os.path.isfile(os.path.join(nd, f)): _nc_missing(os.path.join(nd, f))
    shutil.copyfile(os.path.join(HERE, 'night_city.json'), os.path.join(nd, 'CityLights.json'))
    meta = json.load(open(os.path.join(nd, 'CityLights.meta.json')))
    G = json.load(open(os.path.join(nd, 'NightGeometry.json')))
    if G['counts'] != meta['geometry_counts'] or sum(meta['counts'].values()) != meta['count']: raise RuntimeError('night step: CityLights.meta.json is inconsistent with NightGeometry.json (re-run prep_night.py)')
    if not unreal.load_asset(MPC): raise RuntimeError('night step: MPC_City missing (build the city first)')
    EAL.make_directory(NC)
    tex = nc_import_textures()
    if len(tex) != 3: raise RuntimeError('night step: texture import failed')
    EK = float(NJ['K']) * float(NJ['EmissiveK'])
    P = G['params']
    CD = lambda i: ('CD%d' % i, 'cd', i)
    MPCN = ('NK', 'mpc', 'NightK')
    TEXS = lambda t, st: (tex[t], st)
    colour = nc_material('M_NightColor', NC_HLSL['M_NightColor'], nc_inputs('M_NightColor', {'EK': EK}), EK)
    word = nc_material('M_NightWord', NC_HLSL['M_NightWord'], nc_inputs('M_NightWord', {'Tex': TEXS('T_NeonWords', unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR), 'EK': EK,
                                                                                       'WG': P['word_gain'], 'GL': P['neon_glow']}), EK)
    board = nc_material('M_NightBoard', NC_HLSL['M_NightBoard'], nc_inputs('M_NightBoard', {'Tex': TEXS('T_TsAds', unreal.MaterialSamplerType.SAMPLERTYPE_COLOR), 'EK': EK, 'BG': P['board_gain'],
                                                                                          'KN': P['knee'], 'TP': P['top']}), EK)
    blade = nc_material('M_NightBlade', NC_HLSL['M_NightBlade'], nc_inputs('M_NightBlade', {'Tex': TEXS('T_TsSigns', unreal.MaterialSamplerType.SAMPLERTYPE_COLOR), 'EK': EK, 'SK': P['screen_k']}), EK)

    world = open_level(NIGHT)
    gm = spawn(unreal.WHCityLights, unreal.Vector(0, 0, 0), label='CityLights', folder='NightCity')
    Hh = PRE['night']['lights']['hero']
    cls = unreal.load_class(None, '/Script/WebHomage.WHLookHeroLight')
    if cls:
        h = spawn(cls, unreal.Vector(0, 0, 0), label='HeroLights', folder='NightCity')
        cfg(h, {'rim_intensity': float(Hh['rim_cd']), 'fill_intensity': float(Hh['fill_cd']), 'top_intensity': float(Hh['top_cd'])}, 'HeroLight')
    else: _B.fail('AWHLookHeroLight class missing (build the C++ module)')
    em = spawn(unreal.Actor, unreal.Vector(0, 0, 0), label='NightEmissive', folder='NightCity')
    up = unreal.Vector(0, 0, 1)
    V3 = lambda a: unreal.Vector(a[0], a[1], a[2])
    def norm(v):
        l = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
        return (v[0] / l, v[1] / l, v[2] / l)
    def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    def rot_xy(x, y):   # local X, Y given; Z = X x Y
        z = cross(x, y)
        return unreal.MathLibrary.make_rotation_from_axes(V3(x), V3(y), V3(z))
    def rot_z(axis):    # local Z along `axis`
        z = norm(axis); ref = (0.0, 0.0, 1.0) if abs(z[2]) < 0.9 else (1.0, 0.0, 0.0)
        x = norm(cross(ref, z)); y = cross(z, x)
        return unreal.MathLibrary.make_rotation_from_axes(V3(x), V3(y), V3(z))
    def hism(tag, mesh_path, material, transforms, cdata, cull):
        c = add_component(em, unreal.HierarchicalInstancedStaticMeshComponent)
        c.set_static_mesh(unreal.load_asset(mesh_path)); c.set_material(0, material)
        c.set_editor_property('component_tags', [unreal.Name(tag)])
        nf = len(cdata[0]) if cdata else 0
        if nf: c.set_editor_property('num_custom_data_floats', nf)
        ids = []
        for i in range(0, len(transforms), 20000): ids += list(c.add_instances(transforms[i:i + 20000], True, True))
        for k, d in zip(ids, cdata or []):
            for j, v in enumerate(d): c.set_custom_data_value(k, j, float(v), False)
        c.set_cast_shadow(False); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        for k, v in (('can_ever_affect_navigation', False), ('affect_distance_field_lighting', False), ('affect_dynamic_indirect_lighting', False), ('instance_end_cull_distance', int(cull))):
            try: c.set_editor_property(k, v)
            except Exception as e: _B.warn('%s.%s' % (tag, k), e)
        log('night: %s %d instances' % (tag, c.get_instance_count()))
        return c
    # tubes: cylinder segments (BasicShapes/Cylinder: 100 cm tall, radius 50)
    T = G['tubes']; tr, cd = [], []
    for i in range(0, len(T), 12):
        cx, cy, cz, ax, ay, az, ln, rad, flat, r, g, b = T[i:i + 12]
        tr.append(unreal.Transform(unreal.Vector(cx, cy, cz), rot_z((ax, ay, az)), unreal.Vector(rad * 2.0 / 100.0, rad * 2.0 / 100.0, ln / 100.0))); cd.append((r, g, b))
    hism('nc_tubes', '/Engine/BasicShapes/Cylinder', colour, tr, cd, 9000)
    W = G['words']; tr, cd = [], []
    for i in range(0, len(W), 15):
        cx, cy, cz, wx, wy, wz, nx, ny, nz, w, h, cell, r, g, b = W[i:i + 15]
        tr.append(unreal.Transform(unreal.Vector(cx, cy, cz), rot_xy((wx, wy, 0.0), (0.0, 0.0, 1.0)), unreal.Vector(w / 100.0, h / 100.0, 1.0))); cd.append((r, g, b, cell, w / h))
    hism('nc_words', '/Engine/BasicShapes/Plane', word, tr, cd, 14000)
    B = G['boards']; tr, cd = [], []
    for i in range(0, len(B), 20):
        cx, cy, cz, nx, ny, nz, ux, uy, uz, w, h, u0, v0, u1, v1, hasuv, r, g, b, pr = B[i:i + 20]
        tr.append(unreal.Transform(unreal.Vector(cx, cy, cz), rot_xy(norm((ux, uy, uz)), (0.0, 0.0, 1.0)), unreal.Vector(w / 100.0, h / 100.0, 1.0))); cd.append((r, g, b, u0, v0, u1, v1, hasuv))
    hism('nc_boards', '/Engine/BasicShapes/Plane', board, tr, cd, 80000)
    L = G['blades']; tr, cd = [], []
    for i in range(0, len(L), 15):
        cx, cy, cz, wx, wy, wz, nx, ny, nz, w, h, cu, cv, cdu, cdv = L[i:i + 15]
        tr.append(unreal.Transform(unreal.Vector(cx, cy, cz), rot_xy((wx, wy, 0.0), (0.0, 0.0, 1.0)), unreal.Vector(w / 100.0, h / 100.0, 1.0))); cd.append((cu, cv, cdu, cdv))
    hism('nc_blades', '/Engine/BasicShapes/Plane', blade, tr, cd, 9000)
    S = G['signals']; tr, cd = [], []
    for i in range(0, len(S), 6):
        x, y, z, r, g, b = S[i:i + 6]
        tr.append(unreal.Transform(unreal.Vector(x, y, z), unreal.Rotator(0, 0, 0), unreal.Vector(0.14, 0.14, 0.14))); cd.append((r * NJ['emissive']['signal_lens'], g * NJ['emissive']['signal_lens'], b * NJ['emissive']['signal_lens']))
    hism('nc_signals', '/Engine/BasicShapes/Sphere', colour, tr, cd, 9000)
    Hd = G['lamp_heads']; tr, cd = [], []
    for i in range(0, len(Hd), 6):
        x, y, z, r, g, b = Hd[i:i + 6]
        tr.append(unreal.Transform(unreal.Vector(x, y, z - 12.0), unreal.Rotator(0, 0, 0), unreal.Vector(0.32, 0.32, 0.07))); cd.append((r * NJ['emissive']['lamp_head'], g * NJ['emissive']['lamp_head'], b * NJ['emissive']['lamp_head']))
    hism('nc_lamp_heads', '/Engine/BasicShapes/Sphere', colour, tr, cd, 14000)
    want = {'nc_tubes': G['counts']['tube_segments'], 'nc_words': G['counts']['words'], 'nc_boards': G['counts']['boards'], 'nc_blades': G['counts']['blade_faces'],
            'nc_signals': G['counts']['signals'], 'nc_lamp_heads': G['counts']['lamp_heads']}
    for c in em.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
        tag = str(c.get_editor_property('component_tags')[0]) if c.get_editor_property('component_tags') else '?'
        if c.get_instance_count() != want.get(tag): _B.fail('%s instances %d != expected %s' % (tag, c.get_instance_count(), want.get(tag)))
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, NIGHT): _B.fail('save_map failed: ' + NIGHT)
    log('night level saved', NIGHT)

# ------------------------------------------------------------------------------------------------ step maps
def rig_path(name): return '%s/Look_Rig_%s' % (RIGS, name)

def add_sublevels(world, name, boxes=False):
    for l in list(unreal.EditorLevelUtils.get_levels(world)):   # never stack the old night lights with the new ones
        if l.get_path_name().split('.')[0] == sm2_common.LEGACY_NIGHT_LEVEL: unreal.EditorLevelUtils.remove_level_from_world(l)
    for lp in (CITY_GEO, BOXES, rig_path(name), NIGHT):
        if lp == BOXES and not (boxes and EAL.does_asset_exist(BOXES)): continue
        if lp == NIGHT and name != 'night': continue
        if lp == NIGHT and not EAL.does_asset_exist(NIGHT): _B.fail('night map needs %s (step night)' % NIGHT); continue
        if not any(lp.split('/')[-1] in l.get_path_name() for l in unreal.EditorLevelUtils.get_levels(world)):
            unreal.EditorLevelUtils.add_level_to_world(world, lp, unreal.LevelStreamingAlwaysLoaded)
    les.set_current_level_by_name(str(world.get_name()))

def build_maps():
    EAL.make_directory(TESTS)
    trav_gm = unreal.load_class(None, '/Script/WebHomage.WebTravGameMode')
    ps = SHOTS[0]['player']
    for name in ORDER:
        mp = 'Look_Midtown' if name == ORDER[0] and name == 'midday' else 'Look_Midtown_' + name
        world = open_level('%s/%s' % (TESTS, mp))
        add_sublevels(world, name, boxes=True)
        spawn(unreal.PlayerStart, U(ps[0], ps[1] + 1.0, ps[2]), unreal.Rotator(0, 0, -90), 'PlayerStart')
        if trav_gm: world.get_world_settings().set_editor_property('default_game_mode', trav_gm)
        else: MISS.append('WebTravGameMode class missing (build the C++ module)')
        unreal.EditorLoadingAndSavingUtils.save_map(world, '%s/%s' % (TESTS, mp))
        log('map', mp)
        for s in SHOTS:
            mv = '%s/Look_View_%s_%s' % (TESTS, name, s['id'].split('_')[0])
            world = open_level(mv)
            add_sublevels(world, name)
            sp = s.get('player', ps)
            spawn(unreal.PlayerStart, U(sp[0], sp[1] + 1.0, sp[2]), unreal.Rotator(0, 0, -90), 'PlayerStart')
            p, t = U(*s['pos']), U(*s['target'])
            ca = spawn(unreal.CameraActor, p, look_rot(p, t), 'ShotCam_' + s['id'])
            ca.camera_component.set_editor_property('field_of_view', s.get('fov', 70))
            ca.camera_component.set_editor_property('constrain_aspect_ratio', False)
            ca.set_editor_property('auto_activate_for_player', unreal.AutoReceiveInput.PLAYER0)
            unreal.EditorLoadingAndSavingUtils.save_map(world, mv)
        log('views', name)

# ------------------------------------------------------------------------------------------------ run
EAL.make_directory(RIGS)
if 'geo' in STEPS: build_geo()
if 'rigs' in STEPS:
    for n in ORDER: build_rig(n)
if 'night' in STEPS: build_night()
if 'maps' in STEPS: build_maps()
if MISS: log('WARNINGS (%d):' % len(MISS)); [print('   ', m) for m in MISS]
for m_ in MISS: _B.fail(m_)
log('DONE')
_B.finish()

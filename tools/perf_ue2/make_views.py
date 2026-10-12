# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Piece F: extra still-view maps that piece C's build does not make (C builds S1/S2/S4 only). LOCAL content, never committed:
#   /Game/PerfF/View_<S#> = a copy of C's /Game/Maps/Manhattan_View_S1 (golden map + sublevels) with its shot camera moved to the
#   P1 shot <S#> from Scripts/city_shots.json (same browser-metre -> UE conversion as build_manhattan.make_map).
# Run in a headless commandlet of THIS worktree after build_manhattan's `map` step (editor closed):
#   "<UnrealEditor>" <uproject> -run=pythonscript -script=<abs>/tools/perf_ue2/make_views.py -unattended -nullrhi -NoSound
# env SM2_PERF_VIEWS (default "S7").
import unreal, json, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = {s['id'].split('_')[0]: s for s in json.load(open(os.path.join(HERE, '..', '..', 'unreal', 'WebHomage', 'Scripts', 'city_shots.json')))}
SRC = '/Game/Maps/Manhattan_View_S1'
EAL = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def U(x, y, z): return unreal.Vector(x * 100.0, y * 100.0, z * 100.0)


for v in [x for x in os.environ.get('SM2_PERF_VIEWS', 'S7').split(',') if x]:
    dst = '/Game/PerfF/View_' + v
    if EAL.does_asset_exist(dst): EAL.delete_asset(dst)
    if not EAL.duplicate_asset(SRC, dst): raise RuntimeError('duplicate failed ' + dst)
    unreal.EditorLoadingAndSavingUtils.load_map(dst)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    cam = SHOTS[v]
    b = lambda q: U(q[0], q[2], q[1])
    p, t = b(cam['pos']), b(cam['target'])
    d = unreal.Vector(t.x - p.x, t.y - p.y, t.z - p.z)
    rot = unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(d.z, math.hypot(d.x, d.y))), yaw=math.degrees(math.atan2(d.y, d.x)))
    n = 0
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.CameraActor) and a.get_actor_label().startswith('ShotCam_'):
            a.set_actor_location_and_rotation(p, rot, False, False)
            a.set_actor_label('ShotCam_' + cam['id'])
            a.camera_component.set_editor_property('field_of_view', cam.get('fov', 70))
            n += 1
    ok = unreal.EditorLoadingAndSavingUtils.save_map(world, dst)
    print('[perf_views] %s cams=%d saved=%s pos=%s rot=%s' % (dst, n, ok, p, rot))

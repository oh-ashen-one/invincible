# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.
# One GLB for Unreal: the v2 hero (CustomUse rig) + every game clip (all authored on the same 52-bone rig, so actions transfer by bone
# name). usage: Blender -b --factory-startup -P merge_hero_clips.py -- <rigged.glb> <out.glb> <clips.glb>:<ACTION>[=<NEW NAME>] ...
import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
RIG, OUT, SPECS = a[0], a[1], a[2:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=RIG)
sc = bpy.context.scene; sc.render.fps = 30
for o in list(sc.objects):
    if o.type == 'MESH' and o.name.lower().startswith('icosphere'): bpy.data.objects.remove(o)
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); arm.name = 'HeroRig'
for x in list(bpy.data.actions): bpy.data.actions.remove(x)
arm.animation_data_create()
for spec in SPECS:
    path, act = spec.rsplit(':', 1); new = act
    if '=' in act: act, new = act.split('=')
    before_o = set(bpy.data.objects); before_a = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    src = bpy.data.actions.get(act)
    if src is None: raise SystemExit('missing action %s in %s' % (act, path))
    src.name = new; src.use_fake_user = True
    tr = arm.animation_data.nla_tracks.new(); tr.name = new; st = tr.strips.new(new, 0, src); tr.mute = False
    for o in [o for o in bpy.data.objects if o not in before_o]: bpy.data.objects.remove(o, do_unlink=True)
    for x in [x for x in bpy.data.actions if x not in before_a and x is not src]: bpy.data.actions.remove(x)
    print('CLIP', new, int(src.frame_range[1] - src.frame_range[0] + 1))
arm.animation_data.action = None
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animation_mode='NLA_TRACKS', export_force_sampling=True)
print('MERGE_OK', len(SPECS), OUT)

"""Side-view contact sheet of hero clips (Blender headless, Workbench). Fan homage project; not official Marvel/Sony/Insomniac.
blender -b -P preview_clip.py -- GLB OUT_PREFIX clip:n_frames[,clip:n] [--fps 60]"""
import bpy, sys, os, math
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, spec = a[0], a[1], a[2]
fps = int(a[a.index('--fps') + 1]) if '--fps' in a else 60
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
rig.animation_data_create()
for t in rig.animation_data.nla_tracks: t.mute = True
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x, sc.render.resolution_y = 360, 480
sc.render.fps = 30
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.4
cam.location = (5, 0, 1.0); cam.rotation_euler = (math.pi / 2, 0, math.pi / 2)   # looking -X: side view, hero faces -Y in Blender (glTF +Z)
floor = bpy.data.objects.new('floor', bpy.data.meshes.new('f')); 
import bmesh
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=3); bm.to_mesh(floor.data); sc.collection.objects.link(floor)
files = []
for item in spec.split(','):
    clip, n = item.split(':'); n = int(n)
    act = bpy.data.actions[clip]
    rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    for k in range(n):
        t = k / fps
        f = f0 + t * 30
        if f > f1: break
        sc.frame_set(int(math.floor(f)), subframe=f % 1)
        p = '%s_%s_%02d.png' % (out, clip, k)
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        files.append(p)
print('PREVIEW', len(files))

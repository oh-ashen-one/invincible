"""Blender background preview of the supplied GLBs (PA phase 1). CPU Cycles only.

run: Blender -b --factory-startup --python preview_glbs.py -- <glb_dir> <out_dir> [file ...]
Writes <out_dir>/<stem>.png: a 2x2 tile (3/4 view, Blender -Y view, Blender +X view, top view)
with a neutral grey world + a key sun, so shading/baked light/holes are visible. Read-only on sources.
"""
import bpy, sys, os
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
src, out = args[0], args[1]
want = set(args[2:])
os.makedirs(out, exist_ok=True)
RES = 384
for f in sorted(os.listdir(src)):
    if not f.endswith(".glb") or (want and f not in want):
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(src, f))
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ctr, size = (lo + hi) / 2, max(hi - lo)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 16
    sc.cycles.use_denoising = False
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.35, 0.37, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.5; sun.rotation_euler = (0.8, 0.2, 0.6); sc.collection.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"; cam.data.ortho_scale = size * 1.15
    views = (("q", Vector((1, -1, 0.7)).normalized()), ("my", Vector((0, -1, 0))),
             ("px", Vector((1, 0, 0))), ("top", Vector((0, 0, 1))))
    tiles = []
    for tag, d in views:
        cam.location = ctr + d * size * 3
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        p = os.path.join(out, "_tile_%s_%s.png" % (f[:-4], tag))
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        tiles.append(p)
    # compose 2x2 with Blender image API (no PIL inside Blender)
    big = bpy.data.images.new("big", RES * 2, RES * 2)
    px = [0.0] * (RES * 2 * RES * 2 * 4)
    for i, p in enumerate(tiles):
        im = bpy.data.images.load(p); src_px = list(im.pixels)
        ox, oy = (i % 2) * RES, (1 - i // 2) * RES
        for row in range(RES):
            a = (row * RES) * 4; b = ((oy + row) * RES * 2 + ox) * 4
            px[b:b + RES * 4] = src_px[a:a + RES * 4]
        os.remove(p)
    big.pixels = px
    big.filepath_raw = os.path.join(out, f[:-4] + ".png"); big.file_format = "PNG"; big.save()
    print("DIMS", f, tuple(round(v, 3) for v in (hi - lo)), flush=True)

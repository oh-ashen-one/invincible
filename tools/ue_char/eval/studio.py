"""Neutral grey studio for asset evaluation renders (Blender 5.2, headless).

Fan homage project, not official Marvel/Sony/Insomniac; no affiliation.

Shared by render_glb.py, citizens.py and fauna.py. Timeline (30 fps, 150 frames):
  1-60    camera orbits 360 deg around the subject (subject already moving)
  61-105  fixed 3/4 front camera
  106-150 fixed side camera (second clip, e.g. run)
"""
import bpy, math, os, subprocess
from mathutils import Vector

FPS = 30
N = 150
ORBIT_END = 60
SEG2 = 105


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, N
    return sc


def setup(height=1.8, target=None, dist=None, lens=50, res=(1280, 720)):
    """Lights, floor, world and an orbit/3-4/side camera rig sized to the subject height (metres)."""
    sc = bpy.context.scene
    try:
        sc.render.engine = 'BLENDER_EEVEE'
    except TypeError:
        sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    ee = sc.eevee
    for k, v in (('taa_render_samples', 32), ('use_shadows', True), ('use_raytracing', False)):
        if hasattr(ee, k):
            setattr(ee, k, v)
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Base Contrast'
    except TypeError:
        pass
    sc.render.image_settings.file_format = 'PNG'
    # world: flat mid grey ambient
    w = bpy.data.worlds.new('studio')
    sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs[0].default_value = (0.18, 0.18, 0.18, 1)
    bg.inputs[1].default_value = 0.35
    # floor
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    fl = bpy.context.object
    fl.name = 'floor'
    m = bpy.data.materials.new('floor')
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (0.22, 0.22, 0.22, 1)
    p.inputs['Roughness'].default_value = 0.8
    fl.data.materials.append(m)
    s = height / 1.8

    def area(name, loc, energy, size, color=(1, 1, 1)):
        d = bpy.data.lights.new(name, 'AREA')
        d.energy, d.size, d.color = energy * s * s, size * s, color
        o = bpy.data.objects.new(name, d)
        sc.collection.objects.link(o)
        o.location = Vector(loc) * s
        dirv = (Vector((0, 0, 0.9 * height)) - o.location).normalized()
        o.rotation_euler = dirv.to_track_quat('-Z', 'Y').to_euler()
        return o
    # Blender -Y is the subject's front (glTF +Z)
    area('key', (-2.6, -3.0, 3.2), 900, 2.0, (1.0, 0.97, 0.93))
    area('fill', (3.2, -2.2, 1.6), 250, 3.0, (0.93, 0.96, 1.0))
    area('rim', (0.8, 3.4, 3.0), 700, 1.5)
    # camera rig: pivot empty at subject centre height
    tz = target if target is not None else 0.55 * height
    piv = bpy.data.objects.new('pivot', None)
    sc.collection.objects.link(piv)
    piv.location = (0, 0, tz)
    cd = bpy.data.cameras.new('cam')
    cd.lens = lens
    cam = bpy.data.objects.new('cam', cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    dist = dist or (2.55 * height * lens / 50.0 + 0.6)
    tr = cam.constraints.new('TRACK_TO')
    tr.target, tr.track_axis, tr.up_axis = piv, 'TRACK_NEGATIVE_Z', 'UP_Y'
    elev = 0.06 * height

    def put(f, ang):
        cam.location = (math.sin(ang) * dist, -math.cos(ang) * dist, tz + elev)
        cam.keyframe_insert('location', frame=f)
    # orbit: start in front, go round once
    for i in range(0, ORBIT_END + 1, 2):
        put(1 + i, 2 * math.pi * i / ORBIT_END)
    put(ORBIT_END + 1, math.radians(-35))  # 3/4 front-left
    put(SEG2, math.radians(-35))
    put(SEG2 + 1, math.radians(-90))     # side
    put(N, math.radians(-90))
    for fc in _fcurves(cam):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'
    for f in (ORBIT_END + 1, SEG2 + 1):   # hard cuts
        for fc in _fcurves(cam):
            for k in fc.keyframe_points:
                if abs(k.co.x - (f - 1)) < 0.01:
                    k.interpolation = 'CONSTANT'
    return cam, piv


def _fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    a = ad.action
    if hasattr(a, 'fcurves') and len(getattr(a, 'fcurves', [])):
        return list(a.fcurves)
    out = []
    for L in getattr(a, 'layers', []):
        for st in L.strips:
            for cb in st.channelbags:
                out.extend(cb.fcurves)
    return out


def assign(ob, action):
    ad = ob.animation_data or ob.animation_data_create()
    ad.action = action
    if hasattr(ad, 'action_slot') and ad.action_slot is None and len(getattr(action, 'slots', [])):
        ad.action_slot = action.slots[0]


def nla_sequence(ob, segs, blend=6):
    """segs: [(action, start_frame, end_frame)] -> repeated NLA strips back to back."""
    ad = ob.animation_data or ob.animation_data_create()
    ad.action = None
    for i, (act, a, b) in enumerate(segs):
        tr = ad.nla_tracks.new()
        f0, f1 = act.frame_range
        L = max(1.0, f1 - f0)
        st = tr.strips.new(act.name, int(a), act)
        if hasattr(st, 'action_slot') and st.action_slot is None and len(getattr(act, 'slots', [])):
            st.action_slot = act.slots[0]
        st.repeat = max(1.0, (b - a) / L)
        st.extrapolation = 'HOLD'
        if i:
            st.blend_in = blend
            st.blend_type = 'REPLACE'


def render(out_dir, name, docs_dir, still_frame=95, face=None):
    """Render PNG frames -> h264 mp4 + still jpg. face: (target_z, dist) for an extra close-up still."""
    sc = bpy.context.scene
    fr = os.path.join(out_dir, name)
    os.makedirs(fr, exist_ok=True)
    sc.render.filepath = os.path.join(fr, 'f_')
    bpy.ops.render.render(animation=True)
    os.makedirs(docs_dir, exist_ok=True)
    mp4 = os.path.join(docs_dir, name + '.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-start_number', '1', '-i',
                    os.path.join(fr, 'f_%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '23',
                    '-preset', 'slow', '-movflags', '+faststart', mp4], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(fr, 'f_%04d.png' % still_frame),
                    '-q:v', '3', os.path.join(docs_dir, name + '.jpg')], check=True)
    if face:
        tz, d = face
        cam = sc.camera
        sc.frame_set(still_frame)
        cam.animation_data_clear()
        piv = bpy.data.objects['pivot']
        piv.location.z = tz
        cam.location = (math.sin(math.radians(-20)) * d, -math.cos(math.radians(-20)) * d, tz + 0.02)
        sc.render.filepath = os.path.join(fr, 'face.png')
        bpy.ops.render.render(write_still=True)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(fr, 'face.png'), '-q:v', '3',
                        os.path.join(docs_dir, name + '_face.jpg')], check=True)
    return mp4

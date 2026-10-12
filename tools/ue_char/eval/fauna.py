"""Fauna evaluation clips (Blender 5.2, headless). Fan homage, not official Marvel/Sony/Insomniac; no affiliation.

  blender -b -P tools/ue_char/eval/fauna.py -- NAME [NAME ...]
Geometry from public/assets/city/npc/fauna.{json,bin} LOD0 + atlas tile (cropped by tiles.py).
Motion is a numpy port of the runtime vertex shaders (src/world/npc/fauna.js quadGLSL, pigeons.js birdGLSL):
quadrupeds walk (phase ph advancing 1 stride / 20 frames, amp 1) with tail wag; standing birds peck/look;
flying birds flap (iA.y = 1, iA.z = time). Per-frame vertex positions are written by a frame_change handler.
"""
import bpy, sys, os, json, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); from p2paths import WT as _P2WT, scr as _scr  # noqa: E402
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
NPC = os.path.join(ROOT, 'public/assets/city/npc')
SCR = _scr('eval')
DOCS = os.path.join(ROOT, 'docs/night1/characters/round-01/assets')
C3 = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)   # game Y-up +Z fwd -> Blender Z-up -Y fwd
BREED = {'golden': 0.5, 'bulldog': 0.6}


def rot_yz(q, a):   # rotate about x (shader: q.y' = c y - s z, q.z' = s y + c z)
    c, s = np.cos(a), np.sin(a)
    return np.c_[q[:, 0], c * q[:, 1] - s * q[:, 2], s * q[:, 1] + c * q[:, 2]]


def rot_xz(q, a):   # about y (shader: x' = c x + s z, z' = -s x + c z)
    c, s = np.cos(a), np.sin(a)
    return np.c_[c * q[:, 0] + s * q[:, 2], q[:, 1], -s * q[:, 0] + c * q[:, 2]]


def pose(P, part, w, piv, kind, t, leg=0.5):
    p = P.copy()
    if kind == 'quad':
        ph, amp = 2 * math.pi * t * 30 / 20.0, 1.0
        for pid, nm, o in ((3, 'legFL', 0.0), (4, 'legFR', math.pi), (5, 'legBL', math.pi), (6, 'legBR', 0.0)):
            m = part == pid
            if not m.any():
                continue
            pv = np.array(piv[nm])
            a = np.sin(ph + o) * leg * amp * w[m]
            q = rot_yz(p[m] - pv, a)
            q[:, 1] += np.maximum(0, np.cos(ph + o)) * 0.03 * amp * w[m]
            p[m] = pv + q
        isleg = (part >= 3) & (part <= 6)
        p[:, 1] += np.sin(ph * 2) * 0.012 * amp * np.where(isleg, 1 - w, 1)
        m = part == 2
        if m.any() and 'tail' in piv:
            pv = np.array(piv['tail'])
            p[m] = pv + rot_xz(p[m] - pv, np.sin(t * 9.0) * 0.45 * w[m])
    elif kind == 'bird':
        m = part == 1
        if m.any():
            pv = np.array(piv['head'])
            peck = max(0.0, math.sin(t * 2.0)) ** 4 * 0.9   # periodic peck (iA.w)
            q = rot_yz(p[m] - pv, peck * w[m])
            a = math.sin(t * 2.3) * 0.4 * (1.0 if peck < 0.01 else 0.0) * w[m]
            p[m] = pv + rot_xz(q, a)
    elif kind == 'fly':
        for pid, nm, sg in ((7, 'wingL', 1.0), (8, 'wingR', -1.0)):
            m = part == pid
            if not m.any():
                continue
            pv = np.array(piv[nm])
            a = sg * (1.0 * np.sin(t * 17.0) + 0.12) * w[m]
            q = p[m][:, :2] - pv[:2]
            c, s = np.cos(a), np.sin(a)
            p[m, 0] = pv[0] + c * q[:, 0] - s * q[:, 1]
            p[m, 1] = pv[1] + s * q[:, 0] + c * q[:, 1]
    return p


names = sys.argv[sys.argv.index('--') + 1:]
meta = json.load(open(os.path.join(NPC, 'fauna.json')))
b = open(os.path.join(NPC, 'fauna.bin'), 'rb').read()
for name in names:
    studio.reset()
    it = next(x for x in meta['items'] if x['name'] == name)
    L = it['lods'][0]
    nv, nt = L['nv'], L['nt']
    P = np.frombuffer(b, np.float32, nv * 3, L['pos']).reshape(-1, 3).astype(float)
    uv = np.frombuffer(b, np.float32, nv * 2, L['uv']).reshape(-1, 2).astype(float)
    idx = np.frombuffer(b, np.uint32 if L.get('idx32') else np.uint16, nt * 3, L['idx']).reshape(-1, 3).astype(int)
    part = np.frombuffer(b, np.uint8, nv, L['part']).astype(int)
    w = np.frombuffer(b, np.uint8, nv, L['pw']).astype(float) / 255.0
    gx, gy = meta['grid']
    c, r = it['tile']
    kind = 'fly' if 'wingL' in it['pivots'] else ('quad' if 'legFL' in it['pivots'] else 'bird')
    me = bpy.data.meshes.new(name)
    me.from_pydata((C3 @ P.T).T.tolist(), [], idx.tolist())
    uvl = me.uv_layers.new(name='UVMap')
    li = np.zeros(len(me.loops), int)
    me.loops.foreach_get('vertex_index', li)
    tuv = np.c_[uv[:, 0] * gx - c, 1 - (uv[:, 1] * gy - r)]
    uvl.data.foreach_set('uv', tuv[li].ravel())
    for pl in me.polygons:
        pl.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    pr = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    pr.inputs['Roughness'].default_value = 0.85
    tn = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tn.image = bpy.data.images.load(os.path.join(SCR, 'tiles', name + '.png'))
    mat.node_tree.links.new(tn.outputs['Color'], pr.inputs['Base Color'])
    me.materials.append(mat)
    size = max(it['size'])
    if kind == 'fly':
        ob.location.z = 0.6 * size

    def upd(scene, *_a, P=P, part=part, w=w, piv=it['pivots'], kind=kind, me=me, leg=BREED.get(name, 0.5)):
        t = scene.frame_current / 30.0
        q = pose(P, part, w, piv, kind, t, leg)
        me.vertices.foreach_set('co', (C3 @ q.T).T.ravel())
        me.update()
    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(upd)
    h = max(it['size'][1], 0.25)
    cam, piv = studio.setup(height=1.8)
    # re-frame the camera rig for small subjects: scale distance to the animal's longest side
    s = max(size, 0.35) * 2.6 / (2.55 * 1.8 + 0.6)
    piv.location.z = (0.6 * size if kind == 'fly' else 0) + 0.5 * it['size'][1]
    for fc in studio._fcurves(cam):
        for k in fc.keyframe_points:
            if fc.array_index < 2:
                k.co.y *= s
            else:
                k.co.y = piv.location.z + 0.3 * size
    for lt in [o for o in bpy.context.scene.objects if o.type == 'LIGHT']:
        lt.data.energy *= 0.6
    studio.render(os.path.join(SCR, 'frames'), 'fauna_' + name, DOCS, still_frame=95)
    print('RESULT', name, kind, nv, nt)

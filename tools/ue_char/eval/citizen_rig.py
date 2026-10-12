"""Rebuild a crowd citizen (public/assets/city/npc) as a real Blender armature + skinned mesh + actions.

Fan homage project, not official Marvel/Sony/Insomniac; no affiliation.

Source data (see src/world/npc/crowd.js):
  people.json/.bin  18-bone crowd skeleton (bone heads, parents) and baked per-frame skinning matrices at
                    offset meta.anim: frames*nb*12 float32, a 3x4 row-major matrix per bone per frame, v' = M.[v,1]
  citizens.json/.bin  LOD geometry (pos/nrm/uv float32, si/sw uint8x4, idx u16/u32) + citizens_atlas.webp tiles
The bind pose of the crowd skeleton has identity rotation, so a bone's rest matrix is T(head) (times the
Blender bone's own rest orientation R). The posed armature-space bone matrix is then M.rest, and the local basis is
  basis_b = rest_b^-1 . M_parent^-1 . M_b . rest_b   (root: rest^-1 . M . rest)
Coordinates: game is Y-up, facing +Z; Blender is Z-up, facing -Y: C maps (x, y, z) -> (x, -z, y).
"""
import bpy, json, os, sys
import numpy as np
from mathutils import Matrix

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
NPC = os.path.join(ROOT, 'public/assets/city/npc')
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p2paths import scr as _p2scr   # noqa: E402
C = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
Ci = np.linalg.inv(C)


def load_people():
    p = json.load(open(os.path.join(NPC, 'people.json')))
    pb = open(os.path.join(NPC, 'people.bin'), 'rb').read()
    A = np.frombuffer(pb, np.float32, p['frames'] * p['nb'] * 12, p['anim']).reshape(p['frames'], p['nb'], 3, 4)
    M = np.zeros((p['frames'], p['nb'], 4, 4))
    M[:, :, :3, :] = A
    M[:, :, 3, 3] = 1
    if os.environ.get('CIT_LIFT_CAP', '1') != '0':   # round 09 (critic r08: the rear shin goes horizontal at 18 % of stature): swing-foot lift capped at 10 % of stature
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'crowd'))
        from lift_cap import cap_lift
        M, _ = cap_lift(p, M)
    return p, M


def load_citizen(name, lod=0):
    m = json.load(open(os.path.join(NPC, 'citizens.json')))
    b = open(os.path.join(NPC, 'citizens.bin'), 'rb').read()
    v = next(x for x in m['variants'] if x['name'] == name)
    L = v['lods'][lod]
    nv, nt = L['nv'], L['nt']
    g = dict(
        pos=np.frombuffer(b, np.float32, nv * 3, L['pos']).reshape(-1, 3).astype(float),
        nrm=np.frombuffer(b, np.float32, nv * 3, L['nrm']).reshape(-1, 3).astype(float),
        uv=np.frombuffer(b, np.float32, nv * 2, L['uv']).reshape(-1, 2).astype(float),
        si=np.frombuffer(b, np.uint8, nv * 4, L['si']).reshape(-1, 4).astype(int),
        sw=np.frombuffer(b, np.uint8, nv * 4, L['sw']).reshape(-1, 4).astype(float) / 255.0,
        idx=np.frombuffer(b, np.uint32 if L.get('idx32') else np.uint16, nt * 3, L['idx']).reshape(-1, 3).astype(int))
    return m, v, g


def lbs(g, Mf):
    """Direct linear-blend skinning in game space. Mf: (nb,4,4) for one frame."""
    w = g['sw'] / g['sw'].sum(1, keepdims=True)
    P = np.c_[g['pos'], np.ones(len(g['pos']))]
    out = np.zeros((len(P), 3))
    for k in range(4):
        out += w[:, k:k + 1] * np.einsum('nij,nj->ni', Mf[g['si'][:, k]], P)[:, :3]
    return out


def load_refit(name):
    """Round 06 (CH18): the raw-Tripo refit of a citizen (refit.py + weights_r6.py: welded skin weights, no shredded shells), or None (legacy pack LOD0
    + hull) when it has not been generated or CIT_SRC=legacy."""
    if os.environ.get('CIT_SRC') == 'legacy': return None
    f = os.path.join(_p2scr('eval', 'refit'), name + '_final.npz')
    if not os.path.exists(f): return None
    z = np.load(f)
    return {k: z[k] for k in z.files}


def refit_tex(name):
    """Round 06: the refit citizen's own base colour (raw Tripo 8192 px texture at 2048), or None."""
    if load_refit(name) is None: return None
    f = os.path.join(_p2scr('eval', 'refit'), name + '_tex.png')
    return f if os.path.exists(f) else None


def load_hull(name):
    """Round 05 (CH18): the closed under-layer hull made by underlayer.py (None when it has not been generated)."""
    try:
        from p2paths import scr
    except ImportError:
        import sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); from p2paths import scr
    f = os.path.join(scr('eval', 'hull'), name + '.npz')
    if not os.path.exists(f):
        print('citizen_rig: no under-layer hull for', name, '(run tools/ue_char/eval/underlayer.py)')
        return None
    z = np.load(f)
    return {k: z[k] for k in z.files}


def build(name, clips=('walk', 'run', 'idle'), tex=None, obj_name='Armature', hull=True):
    p, M = load_people()
    meta, var, g = load_citizen(name)
    R6 = load_refit(name)
    if R6 is not None:   # round 06: the refit mesh replaces the pack LOD0 (uv = glTF, origin top-left; the weights are final, 4 per vertex)
        top6 = np.argsort(-R6['dense'], 1)[:, :4]
        wt6 = np.take_along_axis(R6['dense'], top6, 1); wt6 = wt6 / np.maximum(wt6.sum(1, keepdims=True), 1e-9)
        g = dict(pos=R6['pos'].astype(float), nrm=R6['nrm'].astype(float), uv=R6['uv'].astype(float), si=top6, sw=wt6, idx=R6['idx'].astype(int))
        hull = False
        print('citizen_rig: %s from the round-06 refit (%d verts, %d tris)' % (name, len(g['pos']), len(g['idx'])))
    bones = p['bones']
    sc = bpy.context.scene
    # armature
    ad = bpy.data.armatures.new(name + '_rig')
    arm = bpy.data.objects.new(obj_name, ad)
    sc.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    heads = [np.array(C[:3, :3] @ np.array(b['head'])) for b in bones]
    kids = {i: [j for j, c in enumerate(bones) if c['parent'] == i] for i in range(len(bones))}
    prefer = {'hips': 'spine', 'chest': 'neck'}
    ebs = []
    for i, b in enumerate(bones):
        eb = ad.edit_bones.new(b['name'])
        h = heads[i]
        ks = kids[i]
        if ks:
            j = next((k for k in ks if bones[k]['name'] == prefer.get(b['name'])), ks[0])
            t = heads[j]
        else:
            par = b['parent']
            d = h - heads[par] if par >= 0 else np.array([0, 0, 1.0])
            if b['name'] == 'head':
                d = np.array([0, 0, 1.0])
            if b['name'].startswith('foot'):
                d = np.array([0, -1.0, 0])
            t = h + d / max(1e-6, np.linalg.norm(d)) * 0.1
        if np.linalg.norm(t - h) < 1e-3:
            t = h + np.array([0, 0, 0.05])
        eb.head, eb.tail = h.tolist(), t.tolist()
        eb.roll = 0
        ebs.append(eb)
    for i, b in enumerate(bones):
        if b['parent'] >= 0:
            ebs[i].parent = ebs[b['parent']]
    bpy.ops.object.mode_set(mode='OBJECT')
    # mesh
    vb = (C[:3, :3] @ g['pos'].T).T
    nb_ = (C[:3, :3] @ g['nrm'].T).T
    nv0 = len(vb)
    H_ = load_hull(name) if hull else None
    faces = g['idx']
    if R6 is not None:
        tuv = np.c_[g['uv'][:, 0], 1.0 - g['uv'][:, 1]]                     # whole texture, Blender v up
    else:
        gx, gy = meta['grid']
        c, r = var['tile']
        tuv = np.c_[g['uv'][:, 0] * gx - c, 1.0 - (g['uv'][:, 1] * gy - r)]   # tile-local, Blender v up
    loop_uv = tuv[faces.ravel()]
    EXPAND_M = 0.0 if R6 is not None else float(os.environ.get('CIT_EXPAND', '0.003'))
    idx_g = g['idx']
    if EXPAND_M > 0:   # round 05b (CH18, geometry level): every garment triangle grows by EXPAND_M on each edge (about its incentre, uv scaled identically so the
        # texture stays put): hairline gaps between the crowd pack's separate shells (up to ~2 x EXPAND_M wide) close (uv NOT scaled: the atlas has gutters); triangles are unwelded (3 corners each,
        # corner weights / normals / uv copied from the source vertex).  Offline proxy on 9 dark walkers: slivers 31 -> 15 (garment), 17 -> 11 (with hull).
        from underlayer import expand_triangles
        P3, UV3 = expand_triangles(vb, idx_g, tuv, EXPAND_M)
        vb = P3.reshape(-1, 3); nb_ = nb_[idx_g.reshape(-1)]
        faces = np.arange(len(vb)).reshape(-1, 3); loop_uv = tuv[idx_g.reshape(-1)]   # corners keep their ORIGINAL uv: growing the uv too samples the atlas gutters (white speckles)
        nv0 = len(vb)
    if H_ is not None:   # round 05: closed backing hull (one flat uv per triangle = the local garment texel), appended as extra vertices / faces
        vb = np.vstack([vb, (C[:3, :3] @ H_['V'].T).T])
        nb_ = np.vstack([nb_, (C[:3, :3] @ H_['N'].T).T])
        faces = np.vstack([faces, H_['T'] + nv0])
        loop_uv = np.vstack([loop_uv, np.repeat(H_['tri_uv'], 3, axis=0)])
    me = bpy.data.meshes.new(name)
    me.from_pydata(vb.tolist(), [], faces.tolist())
    uvl = me.uv_layers.new(name='UVMap')
    li = np.zeros(len(me.loops), int)
    me.loops.foreach_get('vertex_index', li)
    assert len(li) == len(loop_uv)
    uvl.data.foreach_set('uv', loop_uv.ravel())   # loops are in face order: 3 per triangle
    me.update()
    try:
        me.normals_split_custom_set_from_vertices([tuple(n / max(1e-9, np.linalg.norm(n))) for n in nb_])
    except Exception as e:
        print('custom normals skipped', e)
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    ob.parent = arm
    for i, b in enumerate(bones):
        vg = ob.vertex_groups.new(name=b['name'])
    if R6 is not None:   # round 06: final weights come from weights_r6.py (welded, smoothed, skirt rig, stretch relaxed)
        dense = R6['dense'].astype(float)
    else:
        w = g['sw'] / g['sw'].sum(1, keepdims=True)
        # round 04: weld the weights of UV-seam duplicates (same position, different vertex) - unequal quantised weights open hairline
        # cracks along every texture seam as soon as the pose changes (the white streaks / sparkles the critics saw on citizens)
        dense = np.zeros((len(w), len(bones)))
        for k in range(4): np.add.at(dense, (np.arange(len(w)), g['si'][:, k]), w[:, k])
        key = np.round(g['pos'] / 1e-5).astype(np.int64)
        _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.reshape(-1)
        acc = np.zeros((inv.max() + 1, len(bones))); np.add.at(acc, inv, dense)
        cnt = np.bincount(inv).astype(float)
        dense = acc[inv] / cnt[inv][:, None]
        # round 05 (CH18, weights level): abutting garment shells move together (underlayer.smooth_weights); the hull skins from these weights too
        from underlayer import final_weights   # = smooth_weights + skirt-panel blend (round 05b)
        dense = final_weights(g['pos'], g['nrm'], g['idx'], dense)
    top = np.argsort(-dense, 1)[:, :4]
    wt = np.take_along_axis(dense, top, 1); wt /= wt.sum(1, keepdims=True)
    g['si'], g['sw'], w = top, wt, wt
    g_eval = None
    if EXPAND_M > 0:   # per-corner copies for the expanded, unwelded triangles (g['si'] / g['sw'] stay per source vertex for the hull and the checks)
        ci = idx_g.reshape(-1)
        g_eval = dict(pos=(Ci[:3, :3] @ vb[:len(ci)].T).T, si=top[ci], sw=wt[ci])
        top, wt, w = top[ci], wt[ci], wt[ci]
    if H_ is not None:   # hull vertices skin like their 4 nearest garment vertices (weighted by 1 / distance; `dense` is still per SOURCE vertex = H_['nn'] indices)
        dh = np.einsum('nk,nkb->nb', H_['nw'], dense[H_['nn']])
        toph = np.argsort(-dh, 1)[:, :4]
        wh = np.take_along_axis(dh, toph, 1); wh /= wh.sum(1, keepdims=True)
        top, wt = np.vstack([top, toph]), np.vstack([wt, wh]); w = wt   # garment rows first, hull rows after (g['si'] / g['sw'] stay garment-only)
    for k in range(4):
        for bi in range(len(bones)):
            sel = np.where((top[:, k] == bi) & (w[:, k] > 0))[0]
            vg = ob.vertex_groups[bi]
            for vi in sel:
                vg.add([int(vi)], float(w[vi, k]), 'ADD')
    mod = ob.modifiers.new('Armature', 'ARMATURE')
    mod.object = arm
    # material
    mat = bpy.data.materials.new(name + '_mat')
    mat.use_nodes = True
    pr = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    pr.inputs['Roughness'].default_value = 0.82
    if tex:
        tn = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tn.image = bpy.data.images.load(tex)
        mat.node_tree.links.new(tn.outputs['Color'], pr.inputs['Base Color'])
    me.materials.append(mat)
    # actions
    rest = [Matrix(ad.bones[b['name']].matrix_local) for b in bones]   # by name: ad.bones is depth-first order
    rest_np = [np.array(r) for r in rest]
    acts = {}
    arm.rotation_mode = 'QUATERNION'
    for pb_ in arm.pose.bones:
        pb_.rotation_mode = 'QUATERNION'
    for cn in clips:
        cl = p['clips'][cn]
        act = bpy.data.actions.new(cn)
        act.use_fake_user = True
        arm.animation_data_create()
        arm.animation_data.action = act
        if hasattr(arm.animation_data, 'action_slot') and arm.animation_data.action_slot is None and len(act.slots):
            arm.animation_data.action_slot = act.slots[0]
        n = cl['len']
        prevq = {}
        # round 04: walks are re-timed so the planted ankle moves at a constant speed (crowd_gait.warp_times; foot slide
        # per plant 5-6 cm -> <= 3 cm at the clip's natural speed); other clips keep their frame times
        kt = list(range(n + 1))
        if cn.startswith('walk') and cn in ('walk', 'walkF', 'walkBrisk', 'walkStroll', 'walkOld'):
            import crowd_gait
            p2, A2 = crowd_gait.load()
            kt = [float(x) for x in crowd_gait.warp_times(p2, A2, cn)]
        for f in range(n + 1):             # extra key at n == frame 0: seamless loop
            Mf = M[cl['row'] + (f % n)]
            Mb = [C @ Mf[i] @ Ci for i in range(len(bones))]
            for i, b in enumerate(bones):
                pbn = arm.pose.bones[b['name']]
                par = b['parent']
                if abs(np.linalg.det(Mb[i][:3, :3])) < 1e-6 or (par >= 0 and abs(np.linalg.det(Mb[par][:3, :3])) < 1e-6):
                    basis = np.eye(4)
                else:
                    rel = Mb[i] if par < 0 else np.linalg.inv(Mb[par]) @ Mb[i]
                    basis = np.linalg.inv(rest_np[i]) @ rel @ rest_np[i]
                loc, q, s = Matrix(basis.tolist()).decompose()
                if b['name'] in prevq and prevq[b['name']].dot(q) < 0:
                    q.negate()
                prevq[b['name']] = q.copy()
                pbn.location, pbn.rotation_quaternion, pbn.scale = loc, q, s
                for dp in ('location', 'rotation_quaternion', 'scale'):
                    pbn.keyframe_insert(dp, frame=kt[f])
        try:
            fcs = act.fcurves if hasattr(act, 'fcurves') and len(act.fcurves) else [fc for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
        except Exception:
            fcs = []
        for fc in fcs:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
        acts[cn] = act
    arm.animation_data.action = None
    for pb_ in arm.pose.bones:
        pb_.location, pb_.scale = (0, 0, 0), (1, 1, 1)
        pb_.rotation_quaternion = (1, 0, 0, 0)
    return dict(arm=arm, ob=ob, acts=acts, p=p, M=M, g=g, meta=meta, var=var, g_eval=g_eval)


def recon_error(R, clip='walk', frames=(0, 5, 11, 17, 23)):
    """Max |Blender armature-deformed vertex - direct LBS| in metres over sample frames."""
    arm, ob, p, M, g = R['arm'], R['ob'], R['p'], R['M'], (R.get('g_eval') or R['g'])   # expanded, unwelded corners when CIT_EXPAND > 0
    from studio import assign
    assign(arm, R['acts'][clip])
    sc = bpy.context.scene
    worst = 0.0
    for f in frames:
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        eo = ob.evaluated_get(dg)
        em = eo.to_mesh()
        co = np.zeros(len(em.vertices) * 3)
        em.vertices.foreach_get('co', co)
        eo.to_mesh_clear()
        ref = (C[:3, :3] @ lbs(g, M[p['clips'][clip]['row'] + f]).T).T
        worst = max(worst, float(np.abs(co.reshape(-1, 3)[:len(ref)] - ref).max()))   # garment vertices only (a hull may follow)
    arm.animation_data.action = None
    return worst

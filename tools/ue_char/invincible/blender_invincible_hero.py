"""Invincible-homage hero mesh, Blender FALLBACK generator (2026-10-15, owner-approved Invincible conversion).

Unofficial, non-commercial fan homage. Not an official Marvel, Sony, Insomniac, Image Comics or Skybound product; no affiliation.
Original geometry only: the input is this project's own hero rig (public/assets/spiderman.glb, or the round-14 sculpted
$P2_SCRATCH/ueimport/SK_Hero.glb that build_characters.py 'prep' writes). No logo, NO CAPE, no ripped asset.

What it does (headless, CPU only, no network):
  1. imports the hero GLB (58-joint skin 'SpiderRig'); deletes the old Spider-Man-style eye lenses (the 'Lenses' object and/or the merged
     Lens / LensFrame faces of SK_Hero.glb);
  2. re-materials the body by zones computed in the rig's rest pose (the same metric frame as tools/ue_char/suit8/design.py):
       InvYellow torso + neck | InvBlack belt, soles, toe caps | InvBlue arms (set-in sleeve at the deltoid), gloves, hips, legs, boots |
       InvSkin face | InvHair scalp
  3. HAIR: a short dark hair cap = the scalp vertices displaced outward 7-12 mm with a noise tuft pattern and a small forward fringe,
     faded in over 1.5 cm at the hairline (no new bones; the weights are the head's own);
  4. GOGGLES: new geometry added to the same mesh, skinned 100 % to 'head': a black strap band around the head at eye height,
     two oval yellow-tinted lens domes ('Lens' slot: UE's suit system gives it MI_HeroLens_invincible) and black tube rims ('LensFrame');
  5. checks: same 58 joint names as the source, no cape (no geometry > 20 cm behind the back between knee and shoulder height),
     height within 2 % of the source; writes a JSON report;
  6. exports a skinned GLB (mesh + skin, no clips by default: in UE it binds to the HeroDev skeleton and plays every existing clip),
     optionally saves the .blend (with --ref images as reference empties) and renders preview stills.

The skinned body keeps the source UVs, so a texture from customuse (or any painted atlas on the SAME hero UVs) can be attached later; the
flat zone colours are the fallback look.  The masked hero head has no mouth / nose geometry beyond the round-14 mask sculpt: the exposed
face is therefore a stylised, feature-light face (honest interim; the customuse mesh is the real fix - docs/invincible/character/README.md).

usage (on the studio Mac, never from the cloud session):
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/ue_char/invincible/blender_invincible_hero.py -- \
      --in "$P2_SCRATCH/ueimport/SK_Hero.glb" --out "$P2_SCRATCH/invincible/SK_Invincible.glb" \
      [--report R.json] [--blend OUT.blend] [--render DIR] [--ref IMG [--ref IMG2]] [--with-anims]
Prints INVINCIBLE_HERO_OK on success (the runbook greps for it).
"""
import bpy, bmesh, sys, os, json, math, argparse
from mathutils import Vector, Matrix, noise
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))

ap = argparse.ArgumentParser()
ap.add_argument('--in', dest='inp', default=os.path.join(ROOT, 'public/assets/spiderman.glb'))
ap.add_argument('--out', required=True)
ap.add_argument('--report')
ap.add_argument('--blend')
ap.add_argument('--render')
ap.add_argument('--ref', action='append', default=[], help='reference image (customuse render / concept) added as an image empty in the saved .blend')
ap.add_argument('--with-anims', action='store_true', help='also export the rig clips (standalone test GLB; UE does not need them)')
ap.add_argument('--res', type=int, default=1024)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])

# ------------------------------------------------------------------------------------------------ palette (sRGB hex -> linear)
PAL = {'InvYellow': ('#f2c21b', 0.62, 0.0), 'InvBlue': ('#1f4ea6', 0.66, 0.0), 'InvBlack': ('#121317', 0.55, 0.0),
       'InvSkin': ('#c99a7c', 0.55, 0.0), 'InvHair': ('#17110d', 0.60, 0.0), 'LensFrame': ('#0f1013', 0.30, 0.6), 'Lens': ('#ffcc33', 0.06, 0.0)}
SLOTS = list(PAL)


def lin(h):
    def c(v):
        v = int(v, 16) / 255.0
        return ((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92
    return (c(h[1:3]), c(h[3:5]), c(h[5:7]), 1.0)


def make_mat(name):
    hexc, rough, metal = PAL[name]
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = lin(hexc)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    m.diffuse_color = lin(hexc)
    return m


def ss(x, e0, e1):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------------------------------------ import
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(a.inp))
sc = bpy.context.scene
rigs = [o for o in sc.objects if o.type == 'ARMATURE']
assert len(rigs) == 1, 'expected one armature, got %d' % len(rigs)
rig = rigs[0]
src_bones = sorted(b.name for b in rig.data.bones)
meshes = [o for o in sc.objects if o.type == 'MESH']
for o in meshes:
    if o.name.startswith('Lenses'):
        bpy.data.objects.remove(o, do_unlink=True)
meshes = [o for o in sc.objects if o.type == 'MESH']
body = max(meshes, key=lambda o: len(o.data.vertices))
for o in meshes:
    if o is not body: bpy.data.objects.remove(o, do_unlink=True)
body.name = 'SK_Invincible'

MW = body.matrix_world.copy(); MWi = MW.inverted()
def to_g(v_obj):
    """object space -> glTF-style metres (x = character's left, y up, z forward): Blender world (x, y, z) = glTF (x, -z, y)."""
    w = MW @ v_obj
    return np.array([w.x, w.z, -w.y])
def from_g(g):
    return MWi @ Vector((g[0], -g[2], g[1]))
def jpos(name):
    b = rig.data.bones[name]
    w = rig.matrix_world @ b.head_local
    return np.array([w.x, w.z, -w.y])

# ------------------------------------------------------------------------------------------------ mesh + per-vertex data
bm = bmesh.new(); bm.from_mesh(body.data)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
dl = bm.verts.layers.deform.verify()
uvl = bm.loops.layers.uv.active or bm.loops.layers.uv.new('UVMap')
old_mats = [m.name if m else '' for m in body.data.materials]
# drop the merged Spider-Man eye faces of SK_Hero.glb (slots Lens / LensFrame), keep the suit faces
eye_faces = [f for f in bm.faces if f.material_index < len(old_mats) and old_mats[f.material_index] in ('Lens', 'LensFrame')]
if eye_faces:
    bmesh.ops.delete(bm, geom=eye_faces, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); bm.normal_update()
# clean seams (round 2, 2026-10-15): per-face zoning on the raw triangles left saw-tooth borders at the belt, collar and sleeves, so the
# zone boundaries below are first cut into the mesh as exact edge loops (bisect interpolates UVs and skin weights on the new vertices)
BELT_LO, BELT_HI, COLLAR_Y = 1.031, 1.079, 1.545
def cut(co_g, n_g, near_g=None, rad=0.0):
    co = from_g(np.asarray(co_g, float)); no = (MWi.to_3x3() @ Vector((n_g[0], -n_g[2], n_g[1]))).normalized()
    geom = bm.faces[:] if near_g is None else [f for f in bm.faces if np.linalg.norm(to_g(f.calc_center_median()) - near_g) < rad]
    if geom:
        es = list({e for f in geom for e in f.edges}); vs = list({v for f in geom for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=vs + es + geom, plane_co=co, plane_no=no)
        bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
for yc in (BELT_LO, BELT_HI):
    cut([0, yc, 0], [0, 1, 0], np.array([0, yc, 0]), 0.30)
cut([0, COLLAR_Y, 0], [0, 1, 0], np.array([0, COLLAR_Y, -0.02]), 0.14)
for s_ in ('L', 'R'):
    A0, B0 = jpos('deltoid.' + s_), jpos('forearm.' + s_)
    cut(A0, (B0 - A0) / np.linalg.norm(B0 - A0), A0, 0.16)
bm.normal_update()

GROUPS = {'head': ('head', 'neck'), 'torso': ('hips', 'glute', 'spine', 'spine1', 'spine2'), 'shoulder': ('shoulder', 'deltoid'),
          'armU': ('upperArm',), 'armF': ('forearm', 'forearmTwist'), 'hand': ('hand', 'index', 'middle', 'pinky', 'ring', 'thumb'),
          'thigh': ('thigh',), 'shin': ('shin',), 'foot': ('foot', 'toe')}
gidx = {}
for vg in body.vertex_groups:
    base = vg.name.split('.')[0].split('_')[0]
    for g, names in GROUPS.items():
        if base in names: gidx[vg.index] = g
head_vg = body.vertex_groups.get('head')
assert head_vg is not None, "no 'head' vertex group: not the hero rig"
NV = len(bm.verts)
Pg = np.array([to_g(v.co) for v in bm.verts])
Ng = np.array([(lambda n: np.array([n.x, n.z, -n.y]))((MW.to_3x3() @ v.normal).normalized()) for v in bm.verts])
W = {g: np.zeros(NV) for g in GROUPS}
for i, v in enumerate(bm.verts):
    for k, w in v[dl].items():
        g = gidx.get(k)
        if g: W[g][i] += w
x, y, z = Pg[:, 0], Pg[:, 1], Pg[:, 2]
H0 = float(y.max() - y.min())

# head frame: vertical axis through the centre of the head at eye height
hsel = (W['head'] > 0.5) & (y > 1.60) & (y < 1.76)
cx, cz = float(x[hsel].mean()), float(z[hsel].mean())
theta = np.arctan2(x - cx, z - cz)                     # 0 = front (+z), +-pi = back


def hairline(th):
    t = abs(math.degrees(th))
    bp = [(0, 1.745), (50, 1.722), (90, 1.700), (130, 1.640), (180, 1.600)]
    for (t0, h0), (t1, h1) in zip(bp, bp[1:]):
        if t <= t1: return h0 + (h1 - h0) * (t - t0) / (t1 - t0)
    return bp[-1][1]


r_neck = np.hypot(x, z + 0.022)
is_head = (y > 1.48) & ((y >= 1.54) | (r_neck < 0.080)) & (W['head'] > 0.1)

# ------------------------------------------------------------------------------------------------ 1. hair cap (displace the scalp)
hl = np.array([hairline(t) for t in theta])
hair_v = is_head & (y > hl)
moved = 0
for i, v in enumerate(bm.verts):
    if not is_head[i] or y[i] < hl[i]: continue
    fade = ss(y[i], hl[i], hl[i] + 0.015)
    p = Vector((x[i], y[i], z[i]))
    tuft = 0.5 + 0.5 * noise.noise(p * 38.0)                 # 0..1 clumps
    t = (0.007 + 0.005 * tuft) * fade
    if abs(theta[i]) < math.radians(60) and y[i] < hl[i] + 0.035:
        t += 0.004 * fade                                    # a little fringe volume over the forehead
    v.co = v.co + v.normal * t
    moved += 1
bm.normal_update()
Pg = np.array([to_g(v.co) for v in bm.verts]); x, y, z = Pg[:, 0], Pg[:, 1], Pg[:, 2]

# ------------------------------------------------------------------------------------------------ 2. zone materials (per face, rest pose)
body.data.materials.clear()
mats = {n: make_mat(n) for n in SLOTS}
for n in SLOTS: body.data.materials.append(mats[n])
MI = {n: i for i, n in enumerate(SLOTS)}
JA = {s: (jpos('deltoid.' + s), jpos('forearm.' + s)) for s in ('L', 'R')}
counts = {n: 0 for n in SLOTS}
for f in bm.faces:
    ids = [v.index for v in f.verts]
    c = Pg[ids].mean(0); fx, fy, fz = c
    w = {g: float(W[g][ids].mean()) for g in GROUPS}
    head = bool(is_head[ids].mean() > 0.5)
    if head:
        th = math.atan2(fx - cx, fz - cz)
        if fy > hairline(th): m = 'InvHair'
        elif fy < COLLAR_Y: m = 'InvYellow'                           # suit collar up to the jaw line
        else: m = 'InvSkin'
    else:
        side = 'L' if fx > 0 else 'R'
        A_, B_ = JA[side]; d_ = (B_ - A_) / np.linalg.norm(B_ - A_)
        s_ = float(np.dot(c - A_, d_)); rr = float(np.linalg.norm((c - A_) - s_ * d_))
        arm = (s_ >= 0.0 and rr < 0.095) or (w['armF'] + w['hand'] > 0.5)
        leg = w['thigh'] + w['shin'] + w['foot'] > 0.5
        if w['foot'] > 0.5 and (fy < 0.022 or fz > 0.085): m = 'InvBlack'      # sole, toe cap
        elif arm or leg: m = 'InvBlue'
        elif BELT_LO <= fy <= BELT_HI: m = 'InvBlack'                     # belt
        elif fy < BELT_LO: m = 'InvBlue'                                  # hips / trunks
        else: m = 'InvYellow'
    f.material_index = MI[m]; counts[m] += 1

# ------------------------------------------------------------------------------------------------ 3. goggles (new geometry, skinned to 'head')
HG = head_vg.index
Y_E = 1.675                                            # eye line of the hero mask (the old lenses spanned y 1.635 - 1.713)
hv = np.where(is_head)[0]
Ph = Pg[hv]


def radius_profile(yc, band=0.008, bins=96):
    sel = np.abs(Ph[:, 1] - yc) < band
    q = Ph[sel]
    th = np.arctan2(q[:, 0] - cx, q[:, 2] - cz); r = np.hypot(q[:, 0] - cx, q[:, 2] - cz)
    k = ((th + math.pi) / (2 * math.pi) * bins).astype(int) % bins
    prof = np.full(bins, np.nan)
    for b_ in range(bins):
        if (k == b_).any(): prof[b_] = r[k == b_].max()
    ok = ~np.isnan(prof)
    idx = np.arange(bins)
    prof = np.interp(idx, idx[ok], prof[ok], period=bins)
    return lambda t: float(np.interp((t + math.pi) / (2 * math.pi) * bins, np.arange(bins + 1), np.append(prof, prof[0])))


def surf_z(px, py, rad=0.006):
    """front-most head surface z at (px, py) (glTF frame)."""
    d = np.hypot(Ph[:, 0] - px, Ph[:, 1] - py)
    sel = (d < rad) & (Ph[:, 2] > cz)
    if not sel.any(): sel = (d < rad * 2.5) & (Ph[:, 2] > cz)
    return float(Ph[sel, 2].max())


new_verts = []
def add_v(g):
    v = bm.verts.new(from_g(g)); v[dl][HG] = 1.0; new_verts.append(v); return v
def add_f(vs, mat):
    try: f = bm.faces.new(vs)
    except ValueError: return None
    f.material_index = MI[mat]; f.smooth = True
    for lp in f.loops: lp[uvl].uv = (0.995, 0.995)       # a texel in the atlas corner (flat-colour slots)
    return f

# strap band: a closed thin shell around the head, 2.8 cm tall, 1 - 5 mm off the (hair-displaced) surface
SEG = 96
rows = [Y_E - 0.014, Y_E, Y_E + 0.014]
profs = [radius_profile(yr) for yr in rows]
ring = {}
for ri, yr in enumerate(rows):
    for side, off in (('o', 0.005), ('i', 0.001)):
        for k in range(SEG):
            t = -math.pi + 2 * math.pi * k / SEG
            r = profs[ri](t) + off
            ring[(ri, side, k)] = add_v(np.array([cx + r * math.sin(t), yr, cz + r * math.cos(t)]))
for k in range(SEG):
    k2 = (k + 1) % SEG
    for ri in range(len(rows) - 1):
        add_f([ring[(ri, 'o', k)], ring[(ri, 'o', k2)], ring[(ri + 1, 'o', k2)], ring[(ri + 1, 'o', k)]], 'LensFrame')
        add_f([ring[(ri, 'i', k)], ring[(ri + 1, 'i', k)], ring[(ri + 1, 'i', k2)], ring[(ri, 'i', k2)]], 'LensFrame')
    add_f([ring[(0, 'i', k)], ring[(0, 'i', k2)], ring[(0, 'o', k2)], ring[(0, 'o', k)]], 'LensFrame')
    top = len(rows) - 1
    add_f([ring[(top, 'o', k)], ring[(top, 'o', k2)], ring[(top, 'i', k2)], ring[(top, 'i', k)]], 'LensFrame')

# lens domes (oval, 4.8 x 3.6 cm) + tube rims
LA, LB, NR, NS = 0.024, 0.018, 6, 40
lens_info = []
for sx in (1.0, -1.0):
    x0 = sx * 0.034
    def lp(rho, phi):
        px, py = x0 + LA * rho * math.cos(phi), Y_E + LB * rho * math.sin(phi)
        return np.array([px, py, surf_z(px, py) + 0.006 + 0.004 * (1 - rho * rho)])
    centre = add_v(lp(0.0, 0.0))
    grid = [[add_v(lp(ri / NR, 2 * math.pi * k / NS)) for k in range(NS)] for ri in range(1, NR + 1)]
    for k in range(NS):
        k2 = (k + 1) % NS
        add_f([centre, grid[0][k], grid[0][k2]] if sx > 0 else [centre, grid[0][k2], grid[0][k]], 'Lens')
        for ri in range(NR - 1):
            q = [grid[ri][k], grid[ri + 1][k], grid[ri + 1][k2], grid[ri][k2]]
            add_f(q if sx > 0 else q[::-1], 'Lens')
    # rim: a 3 mm tube along the lens edge
    TS = 8
    tube = []
    for k in range(NS):
        phi = 2 * math.pi * k / NS
        e = lp(1.0, phi); e[2] -= 0.004 * 0.0
        radial = np.array([math.cos(phi) * LB, math.sin(phi) * LA, 0.0]); radial /= np.linalg.norm(radial)
        zh = np.array([0.0, 0.0, 1.0])
        tube.append([add_v(e + 0.003 * (math.cos(2 * math.pi * j / TS) * radial + math.sin(2 * math.pi * j / TS) * zh)) for j in range(TS)])
    for k in range(NS):
        k2 = (k + 1) % NS
        for j in range(TS):
            j2 = (j + 1) % TS
            q = [tube[k][j], tube[k2][j], tube[k2][j2], tube[k][j2]]
            add_f(q if sx > 0 else q[::-1], 'LensFrame')
    lens_info.append(dict(x=x0, y=Y_E, front_z=round(float(lp(0, 0)[2]), 4)))
counts['goggle_verts'] = len(new_verts)
bm.normal_update()
bm.to_mesh(body.data); bm.free()
body.data.update()
# glTF exports per-face smooth normals; recalc for the new shells only would need edit mode - consistent winding was set above

# ------------------------------------------------------------------------------------------------ 4. checks
Pv = np.array([to_g(v.co) for v in body.data.vertices])
yb = Pv[:, 1]; zb = Pv[:, 2]
back_lim = -0.20
cape = int(((zb < back_lim) & (yb > 0.45) & (yb < 1.50)).sum())
bones_now = sorted(b.name for b in rig.data.bones)
H1 = float(yb.max() - yb.min())
checks = {
    'same_joints_as_source': bones_now == src_bones, 'n_joints': len(bones_now),
    'no_cape_vertices_behind_20cm': cape == 0, 'cape_suspect_vertices': cape,
    'height_src_m': round(H0, 4), 'height_out_m': round(H1, 4), 'height_within_2pct': abs(H1 - H0) / H0 < 0.02,
    'no_spidersuit_slot': 'SpiderSuit' not in [m.name for m in body.data.materials if m],
    'slots': [m.name for m in body.data.materials if m],
}
ok = all(v for k, v in checks.items() if k in ('same_joints_as_source', 'no_cape_vertices_behind_20cm', 'height_within_2pct', 'no_spidersuit_slot'))

# ------------------------------------------------------------------------------------------------ 5. export / save / render
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
for o in sc.objects: o.select_set(o in (rig, body))
bpy.context.view_layer.objects.active = body
kw = dict(filepath=os.path.abspath(a.out), export_format='GLB', use_selection=True, export_skins=True, export_animations=bool(a.with_anims), export_yup=True)
try:
    bpy.ops.export_scene.gltf(**kw)
except TypeError:
    kw.pop('use_selection'); kw['export_selected'] = True      # Blender < 2.9x spelling
    bpy.ops.export_scene.gltf(**kw)

for p in a.ref:
    img = bpy.data.images.load(os.path.abspath(p))
    e = bpy.data.objects.new('REF_' + os.path.basename(p), None)
    e.empty_display_type = 'IMAGE'; e.data = img; e.empty_display_size = 2.0
    e.location = (1.4 + 0.1 * len([o for o in sc.objects if o.name.startswith('REF_')]), 0.3, 0.9); e.rotation_euler = (math.radians(90), 0, 0)
    sc.collection.objects.link(e)
if a.blend:
    os.makedirs(os.path.dirname(os.path.abspath(a.blend)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))

renders = []
if a.render:
    os.makedirs(a.render, exist_ok=True)
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
        try: sc.render.engine = eng; break
        except TypeError: continue
    sc.render.resolution_x = a.res; sc.render.resolution_y = int(a.res * 1.25)
    sc.view_settings.view_transform = 'Standard'
    wd = bpy.data.worlds.new('w'); sc.world = wd; wd.use_nodes = True
    bg = next(n for n in wd.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.30, 0.31, 0.34, 1); bg.inputs[1].default_value = 1.0
    for loc, en, sz in (((-2.5, -3, 3), 350, 3), ((3, -2, 1.5), 150, 3), ((0.5, 3, 3), 250, 2)):
        d = bpy.data.lights.new('l', 'AREA'); d.energy = en; d.size = sz
        lo = bpy.data.objects.new('l', d); sc.collection.objects.link(lo); lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 1.0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    idle = next((ac for ac in bpy.data.actions if ac.name.split('_')[0].split('.')[0] == 'idle'), None)
    if idle is not None:
        rig.animation_data_create(); rig.animation_data.action = idle
        try:
            if len(idle.slots): rig.animation_data.action_slot = idle.slots[0]
        except AttributeError: pass
    sc.frame_set(1)
    cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 70
    cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
    tgt = bpy.data.objects.new('tgt', None); sc.collection.objects.link(tgt)
    tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
    views = [('front', 0, 0.95, 4.6), ('34', 35, 0.95, 4.6), ('side', 90, 0.95, 4.6), ('back', 180, 0.95, 4.6), ('head', 25, 1.66, 1.3), ('headfront', 0, 1.66, 1.2)]
    for name, az, ty, dist in views:
        t = math.radians(az)
        tgt.location = (0, 0, ty)
        cam.location = (dist * math.sin(t), -dist * math.cos(t), ty + (0.05 if ty > 1.5 else 0.25))
        sc.render.filepath = os.path.join(os.path.abspath(a.render), 'blender_fallback_%s.png' % name)
        bpy.ops.render.render(write_still=True)
        renders.append(sc.render.filepath)

rep = dict(input=os.path.abspath(a.inp), output=os.path.abspath(a.out), checks=checks, ok=ok, face_counts=counts, hair_vertices_moved=moved,
           lenses=lens_info, removed_eye_faces=len(eye_faces), renders=renders, blender=bpy.app.version_string,
           note='Blender fallback: flat zone colours on the hero UVs; stylised face (no mouth geometry); generated on the studio Mac only')
if a.report:
    os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
    json.dump(rep, open(a.report, 'w'), indent=1)
print(json.dumps(rep, indent=1))
print('INVINCIBLE_HERO_OK' if ok else 'INVINCIBLE_HERO_CHECK_FAILED')

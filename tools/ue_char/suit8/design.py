# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""ORIGINAL hero suit, round 08 ("Tessera"); round 11 turned it into a generator: paint(..., style) takes a style dict (DEFAULT_STYLE = Tessera, texel for texel)
and tools/ue_char/suits/gen_suits.py evaluates the JSON styles of tools/ue_char/suits/suits.json (palette, net kind, sash kind, glyph, hood pattern, accent placement).

ORIGINAL hero suit, round 08 ("Tessera").  Procedural, evaluated per texel in rest-pose object space (x = character's left,
y up, z forward, metres), so there is no hand-drawn source art and nothing is copied from any existing suit.

Design language (written up in docs/night1/characters/round-08/SUIT_ORIGINALITY.md):
  * palette: slate TEAL body, DEEP ink-teal panels, AMBER accents, STITCH light-teal dashes.  No red / blue blocking, no white emblem.
  * asymmetric cross-balance: the character's RIGHT arm and right greave carry the amber "light" side, the LEFT thigh an amber net, the other limbs the dark side.
  * a tilted amber bandolier sash (a plane slice of the torso, front and back differ) instead of a symmetric chest graphic.
  * joint sleeves: DEEP slabs between two planes perpendicular to the limb axis with amber rings at the shoulders (raglan caps), elbows and knees
    (plane cuts, not sphere cuts: a sphere cut of the faceted low-poly mesh zig-zags).
  * net: a diamond net of two opposite helices wound around each body segment (helix_dist), hairline dark on the TEAL panels, amber with raised knots on the
    right upper arm and the left thigh; no radial / orb web and no spider figure anywhere.  Hexagonal honeycomb on the crown and the jaw vent.
  * chest badge: a hexagon ring with three gaps and three kite vanes around a hex core (a net junction), on the sternum; a plain broken ring on the back.
  * dashed top-stitching beside the piping lines, raised piping / grooves in the height map, per-panel roughness.
  * the mask: DEEP hood (plane cut at the neck, inside the neck cylinder), TEAL_D crown cap with an amber piping arc, two amber brow flashes, honeycomb jaw vent,
    dorsal seam; the eyes are separate geometry (tools/ue_char/hero_lens_r8.py).
"""
import copy
import numpy as np

SQ3 = 1.7320508075688772

# ------------------------------------------------------------------------------------------------ style (round 11: the suit generator)
# Every design decision of Tessera is a field of one style dict; DEFAULT_STYLE reproduces round 08 texel for texel.  New suits are JSON overrides of it
# (tools/ue_char/suits/suits.json -> gen_suits.py): palette, panel layout (wedges, trunks, sash kind), net kind, chest / back glyph, hood pattern,
# accent placement.  Nothing in a style names or copies an existing suit.
DEFAULT_STYLE = dict(
    id='tessera', name='Tessera',
    palette=dict(body='#0f4452', crown='#0b3441', deep='#071a21', ink='#050d11', accent='#e0780c', accent_d='#ad5c08', stitch='#9cc0c6', sole='#0d1012'),
    flip=False,                                       # mirror the whole layout left <-> right (the accent arm becomes the character's left)
    net=dict(kind='diamond', scale=1.0, width=1.0),    # diamond | hex | rib | square | chevron | brick | none
    sash=dict(kind='slash', n=[0.36, 0.88, 0.30], c_y=1.27, half=0.035, curve=0.0, gap=0.09, fold=False, along=[0.925, -0.379, 0.0]),   # slash | vee | double | yoke | placket | none
    wedge=dict(on=True, base=0.088, flare=0.10),
    trunks=dict(on=True, slope=0.62, y0=0.80),
    belt=dict(on=True, buckle='hex'),                  # hex | round | bar | none
    spine=True,
    arm=dict(upper='deep', fore='sleeve', other_fore='bands'),     # accent arm: upper deep | body ; fore sleeve | deep | body; other forearm: bands | sleeve | body
    greave='accent',                                   # accent | none   (the accent-side shin)
    thigh_deep=True,                                   # the other thigh is a DEEP panel with an accent net
    sleeves=True,
    glyph=dict(kind='hexvane', size=1.0, y=1.372, x=0.0),    # hexvane | orbit | tally | lattice | gate | keystone | ladder | chevrons
    crown=dict(kind='honeycomb', edge=True),           # honeycomb | racing | chevron | plain
    brow='flash',                                      # flash | tick | none
    vent='hex',                                        # hex | slots | none
    hood='deep', glove='deep', boot='deep',            # colour role of the mask, gloves and boots: deep | body | accent_d
    mott=1.0,
    fuzz=[0.50, 0.62, 0.68],                           # cloth sheen tint (material parameter, not painted)
    # round 12: relief.kind 'piping' = every panel / net line is a RAISED rounded cord (height profile, glossier roughness) and the net / piping / panel
    # lines are layered UNDER the sash and chevron panels (colour, height and roughness); 'r8' = the round-08 flat print (grooves, net over the sash),
    # kept so tools/ue_char/suits/test_regression.py can still prove the round-08 maps texel for texel.
    # round 14: the sculpted mask reads on a dark hood only if the hood is not near-black and the relief carries a baked tone (the "cavity / highlight" tone of the
    # sculpt field of tools/ue_char/suit8/hero_head_r14.py: raised features up to +up of the albedo, hollows down to -dn).  lift = how far a 'deep' hood is mixed toward the body colour.
    cap=dict(r_out=0.108, r_in=0.075),                  # round 15: the DEEP shoulder cap's radius around the arm axis (r_out away from the torso, r_in on the torso side: no cord over the armpit crease)
    face=dict(tone_up=0.34, tone_dn=0.42, lift=1.0, amp_mm=8.0),
    relief=dict(kind='piping', net=1.30, pipe=1.80, ring=1.80, glyph=1.40, sash=0.60, border=1.60, rough_pipe=0.34, rough_net=0.40, cavity=0.35, net_tone=0.38, seam=2.2, rough_hood=0.50, rough_crown=0.60),
)


def merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict): out[k] = merge(out[k], v)
        else: out[k] = copy.deepcopy(v)
    return out


def resolve(style=None):
    return merge(DEFAULT_STYLE, style) if style else copy.deepcopy(DEFAULT_STYLE)


def srgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255.0


TEAL = srgb('#0f4452')   # (round 08 constants; paint() takes its colours from the style palette)
TEAL_D = srgb('#0b3441')
DEEP = srgb('#071a21')
INK = srgb('#050d11')
AMBER = srgb('#e0780c')
AMBER_D = srgb('#ad5c08')
BONE = srgb('#e6dfc9')
STITCH = srgb('#9cc0c6')
SOLE = srgb('#0d1012')


# ------------------------------------------------------------------------------------------------ helpers
def ss(x, a, b):
    t = np.clip((x - a) / (b - a + 1e-12), 0, 1)
    return t * t * (3 - 2 * t)


def cover(d, aa):
    """Anti-aliased coverage of a signed distance d (metres, negative inside) with texel footprint aa."""
    return np.clip(0.5 - d / aa, 0, 1)


def band(dist, half, aa):
    return cover(np.abs(dist) - half, aa)


def stitch(d, along, aa, off=0.0030, period=0.0048, hw=0.00038, duty=0.58):
    """Two rows of dashed top-stitching at +-off (metres) from a seam line.  d = signed distance to the line, along = coordinate along it (metres)."""
    ph = np.abs((along / period) % 1.0 - 0.5) * 2.0                                # 0 at the dash centre, 1 at the gap centre
    on = 1.0 - ss(ph, duty - 0.12, duty + 0.04)
    return band(np.abs(d) - off, hw, aa) * on


def cord(dist, hw, aa, H):
    """Round-12 raised piping: (coverage, height mm) of a rounded cord of half width hw (metres) centred on dist = 0: the height is a half-ellipse
    profile (H at the centre, 0 at the edge), so the normal map gets a lit flank and a shadowed flank on every line."""
    a = band(dist, hw, aa)
    u = np.clip(np.abs(dist) / max(hw, 1e-6), 0, 1)
    return a, (H * np.sqrt(np.clip(1.0 - u * u, 0.0, 1.0)) * 0.85 + 0.15 * H).astype(np.float32)


def mix(a, b, t):
    return a * (1 - t[..., None]) + b * t[..., None]


def hex_d(u, v, apothem, pointy=True):
    """Signed distance-ish of a regular hexagon (negative inside), apothem = centre-to-flat distance."""
    if not pointy: u, v = v, u
    d = np.maximum(np.maximum(np.abs(u), np.abs(0.5 * u + 0.5 * SQ3 * v)), np.abs(-0.5 * u + 0.5 * SQ3 * v))
    return d - apothem


def hex_cell_edge(u, v, R):
    """Distance to the nearest edge of a pointy-top hexagonal lattice with circumradius R (>= 0)."""
    q = (SQ3 / 3 * u - v / 3) / R; r = (2 / 3 * v) / R
    x, z = q, r; y = -x - z
    rx, ry, rz = np.round(x), np.round(y), np.round(z)
    dx, dy, dz = np.abs(rx - x), np.abs(ry - y), np.abs(rz - z)
    m1 = (dx > dy) & (dx > dz); m2 = (~m1) & (dy > dz)
    rx = np.where(m1, -ry - rz, rx); rz = np.where((~m1) & (~m2), -rx - ry, rz)
    cu = R * SQ3 * (rx + rz / 2); cv = R * 1.5 * rz
    a = R * SQ3 / 2
    return a - hex_d(u - cu, v - cv, 0.0)


def noise3(P, f, seed=0):
    """Cheap smooth 3D value-ish noise (sum of sines), range about [-1, 1]."""
    r = np.random.RandomState(seed)
    k = r.randn(4, 3); ph = r.rand(4) * 6.28
    acc = 0
    for i in range(4):
        acc = acc + np.sin((P @ (k[i] * f / 1.3)) + ph[i])
    return acc / 2.0


def unit(v):
    v = np.asarray(v, np.float64); return v / np.linalg.norm(v)


def seg_coords(P, A, B, e1=None):
    """(s metres along A->B, theta around it with theta = 0 facing e1 (default +z))."""
    A = np.asarray(A, np.float32); B = np.asarray(B, np.float32)
    d = (B - A); d = d / np.linalg.norm(d)
    if e1 is None: e1 = np.array([0, 0, 1.0], np.float32)
    e1 = e1 - d * float(np.dot(e1, d)); e1 = (e1 / np.linalg.norm(e1)).astype(np.float32)
    e2 = np.cross(d, e1).astype(np.float32)
    rel = P - A
    return rel @ d, np.arctan2(rel @ e2, rel @ e1)


def helix_dist(P, A, B, R, cell, K=None, phase=0.0, e1=None, nodes=False):
    """Distance (metres, on the surface) to the nearest line of a diamond net wound around the segment A->B: two helix families of opposite
    hand, 45 degrees to the axis, K cells around (integer so the net closes), `cell` metres along the axis per diamond half-period."""
    A = np.asarray(A, np.float32); B = np.asarray(B, np.float32)
    d = (B - A); L = float(np.linalg.norm(d)); d = d / L
    if e1 is None: e1 = np.array([0, 0, 1.0], np.float32)
    e1 = e1 - d * float(np.dot(e1, d)); e1 = (e1 / np.linalg.norm(e1)).astype(np.float32)
    e2 = np.cross(d, e1).astype(np.float32)
    rel = P - A
    s = rel @ d
    r1 = rel @ e1; r2 = rel @ e2
    th = np.arctan2(r2, r1)
    if K is None: K = max(3, int(round(2 * np.pi * R / cell)))
    u = s / cell + K * th / (2 * np.pi) + phase
    v = s / cell - K * th / (2 * np.pi) + phase
    k = cell / np.sqrt(2.0)
    du = np.abs(u - np.round(u)); dv = np.abs(v - np.round(v))
    if nodes: return np.minimum(du, dv) * k, np.sqrt(du * du + dv * dv) * k
    return np.minimum(du, dv) * k



# ------------------------------------------------------------------------------------------------ net kinds (round 11)
def hex_lattice(u, v, R):
    """Pointy-top hexagonal lattice, circumradius R: (distance to the nearest cell edge >= 0, distance to the nearest cell centre)."""
    q = (SQ3 / 3 * u - v / 3) / R; r = (2 / 3 * v) / R
    x, z = q, r; y = -x - z
    rx, ry, rz = np.round(x), np.round(y), np.round(z)
    dx, dy, dz = np.abs(rx - x), np.abs(ry - y), np.abs(rz - z)
    m1 = (dx > dy) & (dx > dz); m2 = (~m1) & (dy > dz)
    rx = np.where(m1, -ry - rz, rx); rz = np.where((~m1) & (~m2), -rx - ry, rz)
    cu = R * SQ3 * (rx + rz / 2); cv = R * 1.5 * rz
    a = R * SQ3 / 2
    du, dv = u - cu, v - cv
    hn = np.maximum(np.maximum(np.abs(du), np.abs(0.5 * du + 0.5 * SQ3 * dv)), np.abs(-0.5 * du + 0.5 * SQ3 * dv))
    return a - hn, np.sqrt(du * du + dv * dv)


def netd(P, A, B, R, cell, kind='diamond', phase=0.0, scale=1.0, nodes=False):
    """Distance (metres, on the surface) to the nearest line of a surface net wound around the segment A->B (radius R), and with nodes=True also the
    distance to the nearest knot.  kind: diamond (two opposite helices: the round-08 net) | hex (honeycomb, integer columns so it closes around the
    limb) | rib (rings) | square (rings + meridians) | chevron (V rings, cusp at the front and the back) | brick (rings + staggered verticals) | none."""
    cell = cell * scale
    if kind == 'diamond':
        return helix_dist(P, A, B, R, cell, phase=phase, nodes=nodes)
    A = np.asarray(A, np.float32); B = np.asarray(B, np.float32)
    s, th = seg_coords(P, A, B)
    far = np.full(s.shape, 1.0, np.float32)
    if kind == 'none':
        return (far, far) if nodes else far
    circ = 2 * np.pi * R
    arc = R * th
    ring = s / cell + phase
    d_ring = np.abs(ring - np.round(ring)) * cell
    if kind == 'rib':
        return (d_ring, far) if nodes else d_ring
    if kind == 'square':
        K = max(4, int(round(circ / (cell * 1.15))))
        m = th * K / (2 * np.pi)
        d_mer = np.abs(m - np.round(m)) * (circ / K)
        d = np.minimum(d_ring, d_mer)
        return (d, np.sqrt(d_ring ** 2 + d_mer ** 2)) if nodes else d
    if kind == 'chevron':
        t = 0.9
        u = (s + np.abs(arc) * t) / cell + phase
        d = np.abs(u - np.round(u)) * cell / np.sqrt(1 + t * t)
        return (d, far) if nodes else d
    if kind == 'brick':
        K = max(4, int(round(circ / (cell * 1.6))))
        rows = np.floor(ring)
        m = th * K / (2 * np.pi) + 0.5 * (rows % 2)
        d_mer = np.abs(m - np.round(m)) * (circ / K)
        d = np.minimum(d_ring, d_mer)
        return (d, np.sqrt(d_ring ** 2 + d_mer ** 2)) if nodes else d
    if kind == 'hex':
        K = max(4, int(round(circ / (SQ3 * cell))))
        Rh = circ / (K * SQ3)
        e, c = hex_lattice(arc, s + phase * cell, Rh)
        return (e, c) if nodes else e
    raise KeyError('net kind %s' % kind)


# ------------------------------------------------------------------------------------------------ chest / back glyphs (round 11, all original abstract marks)
def glyph(kind, x, y, cx, cy, size, aa):
    """(line, solid) anti-aliased masks of an abstract glyph centred at (cx, cy); size 1 = about 9 cm across.  None of them is a spider, bat, star, shield,
    crescent, letter or any existing emblem: they are geometric marks built from rings, bars, rhombi and arches."""
    u = (x - cx) / size; v = (y - cy) / size
    a = aa / size
    zero = np.zeros_like(u)
    if kind == 'orbit':
        r = np.hypot(u, v); ang = np.arctan2(v, u)
        da = np.abs((ang - 0.9 + np.pi) % (2 * np.pi) - np.pi)
        line = band(r - 0.043, 0.0024, a) * (1 - cover(da - 0.42, a / 0.043))
        solid = np.maximum(cover(np.hypot(u - 0.007, v + 0.004) - 0.0165, a), cover(np.hypot(u - 0.043 * np.cos(0.9), v - 0.043 * np.sin(0.9)) - 0.0048, a))
        return line, solid
    if kind == 'tally':
        solid = zero.copy()
        us = u - 0.28 * (v + 0.03)                                  # sheared bars
        for i in range(4):
            xi = (i - 1.5) * 0.0165; hi = 0.020 + 0.0135 * i
            d = np.maximum(np.abs(us - xi) - 0.0030, np.maximum(-0.030 - v, v - (-0.030 + hi)))
            solid = np.maximum(solid, cover(d, a))
        line = band(v + 0.037, 0.0016, a) * cover(np.abs(u) - 0.042, a)
        return line, solid
    if kind == 'lattice':
        ka = 1.0 / np.sqrt(1 / 0.040 ** 2 + 1 / 0.052 ** 2)
        d_out = (np.abs(u) / 0.040 + np.abs(v) / 0.052 - 1.0) * ka
        d_in = (np.abs(u) / 0.020 + np.abs(v) / 0.026 - 1.0) * ka * 0.5
        diag = band((0.78 * u - 0.62 * v) * 1.0, 0.0017, a) * cover(d_out + 0.004, a)
        line = np.maximum(band(d_out + 0.0022, 0.0023, a), np.maximum(band(d_in, 0.0018, a) * 0.0, diag))
        solid = cover((np.abs(u) / 0.010 + np.abs(v) / 0.013 - 1.0) * ka * 0.3, a) * 1.0
        return line, solid
    if kind == 'gate':
        top = np.hypot(u, v - 0.010) - 0.033
        side = np.abs(u) - 0.033
        d = np.where(v > 0.010, top, side)
        line = band(d + 0.0018, 0.0023, a) * cover(-0.040 - v, a)          # open at the bottom (v < -0.040)
        solid = np.maximum(cover(np.maximum(np.abs(u) - 0.013, np.abs(v + 0.004) - 0.0030), a), cover(np.hypot(u, v - 0.016) - 0.0058, a))
        return line, solid
    if kind == 'keystone':
        hw = 0.031 + 0.009 * (v / 0.032)
        d = np.maximum((np.abs(u) - hw) * 0.99, np.abs(v) - 0.032)
        line = band(d + 0.0019, 0.0023, a)
        solid = cover(np.maximum(np.abs(u) - 0.0036, np.maximum(-0.019 - v, v - 0.013)), a)
        return line, solid
    if kind == 'ladder':
        rails = np.maximum(cover(np.maximum(np.abs(np.abs(u) - 0.020) - 0.0030, np.abs(v) - 0.034), a), 0)
        line = zero.copy()
        for k in (-0.022, -0.007, 0.008, 0.023):
            line = np.maximum(line, cover(np.maximum(np.abs(v - k) - 0.0026, np.abs(u) - 0.019), a))
        return line, rails
    if kind == 'chevrons':
        line = zero.copy()
        for i in range(3):
            c = 0.026 - 0.018 * i
            d = np.abs(v - (c - 0.82 * np.abs(u))) / np.sqrt(1 + 0.82 ** 2)
            line = np.maximum(line, band(d, 0.0028, a) * cover(np.abs(u) - (0.036 - 0.004 * i), a))
        return line, zero
    raise KeyError('glyph kind %s' % kind)


# ------------------------------------------------------------------------------------------------ the suit
class Canvas:
    """Layered texel canvas: colour, height (mm), roughness, occlusion."""
    def __init__(self, shape, base):
        self.col = np.tile(base, shape + (1,)).astype(np.float32)
        self.h = np.zeros(shape, np.float32)
        self.rough = np.full(shape, 0.74, np.float32)
        self.ao = np.ones(shape, np.float32)

    def lay(self, alpha, c, h=None, rough=None, ao=None, hmode='set'):
        a = np.clip(alpha, 0, 1).astype(np.float32)
        c = np.asarray(c, np.float32)
        self.col = self.col * (1 - a[..., None]) + (c if c.ndim > 1 else c[None, None, :]) * a[..., None]
        if h is not None:
            self.h = self.h + (np.asarray(h, np.float32) - self.h) * a if hmode == 'set' else self.h + a * np.asarray(h, np.float32)
        if rough is not None: self.rough = self.rough + (rough - self.rough) * a
        if ao is not None: self.ao = self.ao + (ao - self.ao) * a


def paint(P, N, G, mpt, gi, jp, style=None, dbg=None):
    """P, N (r, n, 3) float32 rest-pose positions / normals; G (r, n, 9) group weights; mpt (r, n) metres per texel (AA footprint);
    gi = {group name: index}; jp = {joint name: (x, y, z)}; style = override dict of DEFAULT_STYLE (None = Tessera).
    Returns dict(col (r, n, 3) sRGB 0..1, h mm, rough, ao).
    dbg (round 15, an instrument hook): a dict that receives 'cord' (union of every raised cord / border laid) and 'net' (a list of (line coverage, zone mask) pairs of every net layer),
    so tools/ue_char/suits/net_end_check_r15.py can find the net lines that end where no cord is."""
    S = resolve(style)
    RL = S['relief']; PIPE = RL['kind'] == 'piping'
    pal = {k: srgb(v) for k, v in S['palette'].items()}
    TEAL, TEAL_D, DEEP, INK = pal['body'], pal['crown'], pal['deep'], pal['ink']
    AMBER, AMBER_D, STITCH, SOLE = pal['accent'], pal['accent_d'], pal['stitch'], pal['sole']
    if S['flip']:       # evaluate the mirrored suit: x -> -x on positions and normals (the body is bilaterally symmetric, joints are looked up by the mirrored side)
        P = P * np.array([-1, 1, 1], np.float32); N = N * np.array([-1, 1, 1], np.float32)
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    ax = np.abs(x)
    aa = np.maximum(mpt, 6e-5).astype(np.float32) * 1.2
    g = lambda k: G[..., gi[k]]
    sharp = lambda w: ss(w, 0.42, 0.58)
    head = g('head'); torso = g('torso'); shoulder = g('shoulder'); armU = sharp(g('armU')); armF = sharp(g('armF')); hand = sharp(g('hand'))
    thigh = sharp(g('thigh')); shin = sharp(g('shin')); foot = sharp(g('foot'))
    nx, ny, nz = N[..., 0], N[..., 1], N[..., 2]
    C = Canvas(x.shape, TEAL)
    def mark_cord(a):
        if dbg is not None: dbg['cord'] = np.maximum(dbg['cord'], a) if 'cord' in dbg else np.asarray(a, np.float32).copy()
    r_neck = np.hypot(x, z + 0.022)
    neck_ok = np.where(y < 1.54, cover(r_neck - 0.080, aa), 1.0).astype(np.float32)     # below the ear line only the neck cylinder (not the trapezius) belongs to the hood
    is_head = cover(1.480 - y, aa) * neck_ok * ss(head, 0.05, 0.15)            # hood: straight plane cut at the neck (the skin-weight ramp is soft and uneven)
    shoulder_arm = shoulder * ss(ax, 0.10, 0.17)
    arm_w = np.clip(armU + armF + hand + shoulder_arm, 0, 1)
    tors_w = sharp(np.clip(torso + shoulder * (1 - ss(ax, 0.10, 0.17)), 0, 1))
    leg_w = np.clip(thigh + shin + foot, 0, 1)
    trunk_w = sharp(np.clip(g('torso') + g('thigh') + g('shoulder') * (1 - ss(ax, 0.10, 0.17)), 0, 1))
    body_w = 1 - is_head
    R_ = (x < 0).astype(np.float32)               # the character's RIGHT (amber arm, dark leg)
    L_ = 1 - R_
    sgn = np.where(x < 0, -1.0, 1.0).astype(np.float32)
    front = ss(nz, 0.15, 0.55); back = ss(-nz, 0.15, 0.55)

    def D(c): return np.sqrt((x - c[0]) ** 2 + (y - c[1]) ** 2 + (z - c[2]) ** 2)
    def pdot(v, c=(0.0, 0.0, 0.0)): return P @ np.asarray(v, np.float32) - np.float32(np.dot(v, c))
    def J(n): return np.asarray(jp[n], np.float32)

    # ------------------------------------------------------------------ colour blocking
    # 1. torso side panels: a DEEP wedge that widens toward the waist
    wd = S['wedge']
    xb = wd['base'] + wd['flare'] * ss(y, 1.06, 1.33)
    m_side = tors_w * body_w * cover(xb - ax, aa) * ss(y, 1.00, 1.04) * (1.0 if wd['on'] else 0.0)
    C.lay(m_side, DEEP, rough=0.80)
    # 2. waist belt band + trunks (DEEP) above a diagonal hip-wrap cut across the thighs
    tk = S['trunks']
    belt_d = np.abs(y - 1.055) - 0.024
    if S['belt']['on']:
        C.lay(body_w * tors_w * cover(belt_d, aa), DEEP, rough=0.80)
    cut_norm = np.sqrt(1 + tk['slope'] ** 2)
    cut_d = (y - (tk['y0'] + tk['slope'] * x)) / cut_norm            # > 0 above the diagonal
    cut_along = (x + tk['slope'] * y) / (1.176 if abs(tk['slope'] - 0.62) < 1e-9 else cut_norm)
    if tk['on']:
        m_trunk = body_w * trunk_w * cover(np.maximum(y - 1.03, -cut_d), aa)
        C.lay(m_trunk, DEEP, rough=0.80)
    # back spine stripe (under the sash)
    back = ss(-nz, 0.15, 0.55)
    if S['spine']:
        m_spine = back * tors_w * body_w * cover(np.abs(x) - 0.013, aa) * cover(y - 1.44, aa) * cover(1.085 - y, aa) * cover(y - 1.335, aa)
        C.lay(m_spine, DEEP, rough=0.8)
    # 3. sash: a plane slice of the torso (slash), a folded plane (vee), two parallel slices (double), a curved yoke, or a vertical placket (front and back differ)
    sa = S['sash']
    zone_s = None
    sash_fg = 1.0         # round 16: the gate of the sash END finishing (stitches, accent pipe) to the front panel
    if sa['kind'] != 'none':
        n_s = unit(sa['n'])
        Pf = np.stack([ax, y, z], -1) if sa['fold'] else P
        d_s = Pf @ np.asarray(n_s, np.float32) - np.float32(np.dot(n_s, (0.0, sa['c_y'], 0.0)))
        if sa['curve']: d_s = d_s + np.float32(sa['curve']) * x * x
        if sa['kind'] == 'placket':
            d_s = ax - 0.0 * y                                           # vertical band down the sternum
        y_lo, y_hi = (1.045, 1.44) if sa['kind'] != 'yoke' else (1.20, 1.50)
        zone_s = tors_w * body_w * ss(y, y_lo, y_lo + 0.045) * (1 - ss(y, y_hi, y_hi + 0.03)) * cover(ax - 0.160, aa)
        end_x = sa.get('end_x', 0.118)
        if PIPE:     # round 12: CRISP panel ends (the skin-weight / height ramps faded the sash end over centimetres: a dark smear at the cut end in the 4K chest view)
            # round 14 (critic r13: "the Ash sash end is raw"): the ends are STRAIGHT planes (the skin-weight cut of r12 left a ragged, unfinished end line) and every end is
            # finished like the long edges: DEEP border cord, two rows of stitching, an accent pipe just outside (below)
            e_lo = y - (y_lo + 0.0225); e_hi = (y_hi + 0.015) - y; e_x = end_x - ax
            e_min = np.minimum(np.minimum(e_lo, e_hi), e_x)
            sash_ends = [(e_x, y), (e_lo, x), (e_hi, x)]
            if sa.get('front_only', True):
                # round 16 (critic r15: "the front emblem and sash repeat on the Tessera and Plum backs, as if projected through the torso"): the sash is a FRONT panel.  Its plane
                # slice used to come out on the back as a second accent bar; the panel now also ends on the coronal plane z = SASH_ZC (the torso axis); where that end shows (over the
                # shoulder top / under the arm) it is finished like every other end (border cord, stitches, accent pipe)
                e_z = z - np.float32(sa.get('z_cut', -0.012))
                e_min = np.minimum(e_min, e_z); sash_ends.append((e_z, y))
                sash_fg = cover(-(e_z + 0.008), aa)      # the end finishing of the OTHER ends must not come out on the back either (r16 hold 1: short accent pipes floated on the Plum back)
            zone_s = ss(tors_w, 0.30, 0.40) * body_w * cover(-e_min, aa)
        if sa['kind'] == 'placket':
            zone_s = tors_w * body_w * front * cover(1.083 - y, aa) * cover(y - 1.43, aa)      # hard ends: belt to collar
            if PIPE: sash_ends = [(y - 1.083, x), (1.43 - y, x)]
        hw = sa['half']
        offs = [0.0] if sa['kind'] != 'double' else [-sa['gap'] * 0.5, sa['gap'] * 0.5]
        t_s = np.asarray(sa['along'], np.float32)
        for o in offs:
            if PIPE:     # round 12: the DEEP border strips are raised cords, the accent panel a padded plateau
                a_b, h_b = cord(np.abs(d_s - o) - (hw - 0.002), 0.0021, aa, RL['border'])
                C.lay(zone_s * band(d_s - o, hw, aa), DEEP, h=np.where(np.abs(d_s - o) > hw - 0.0042, h_b, RL['sash']), rough=RL['rough_pipe'] + 0.06)
                mark_cord(zone_s * band(d_s - o, hw, aa) * (np.abs(d_s - o) > hw - 0.0042))
                C.lay(zone_s * band(d_s - o, hw - 0.004, aa), AMBER, h=RL['sash'], rough=0.50)
            else:
                C.lay(zone_s * band(d_s - o, hw, aa), DEEP, rough=0.8)
                C.lay(zone_s * band(d_s - o, hw - 0.004, aa), AMBER, h=0.25, rough=0.50)
    if PIPE and zone_s is not None:
        for o in offs:
            pan = band(d_s - o, sa['half'], aa)
            for e_, al_ in sash_ends:
                _, h_e = cord(e_ - 0.0021, 0.0021, aa, RL['border'])
                C.lay(zone_s * pan * cover(e_ - 0.0042, aa), DEEP, h=h_e, rough=RL['rough_pipe'] + 0.06)          # round 14: the DEEP border cord along every sash END (same 4.2 mm as the long edges)
                mark_cord(zone_s * pan * cover(e_ - 0.0042, aa))
    # round 12: everything laid after this point that is not part of the sash goes UNDER it (colour, height, roughness): sash_cov masks it
    sash_cov = np.zeros(x.shape, np.float32)
    if PIPE and zone_s is not None:
        for o in offs:
            sash_cov = np.maximum(sash_cov, zone_s * band(d_s - o, sa['half'] + 0.0006, aa))
    under = (1.0 - sash_cov) if PIPE else 1.0
    net_layer = [False]          # set while a net line is laid (the instrument keeps net lines out of its cord mask)
    def LN(line, zone, c, name='net', **kw):
        """a NET line: coverage `line` (the line's own distance field) inside `zone`; both go to the instrument"""
        if dbg is not None: dbg.setdefault('net', []).append((np.asarray(line, np.float32), np.asarray(zone * under, np.float32), name))
        net_layer[0] = True
        try: L(line * zone, c, **kw)
        finally: net_layer[0] = False
    def L(alpha, c, h=None, rough=None, ao=None, H=None, dist=None, hw=None, r_pipe=None):
        """lay a line: round 08 = flat print with the given h / rough; round 12 = a raised cord of height H (dist / hw = its distance field) with the piping
        roughness, masked UNDER the sash"""
        if not PIPE or H is None:
            C.lay(alpha * under if PIPE else alpha, c, h=h, rough=rough, ao=ao); return
        _, hp = cord(dist, hw, aa, H)
        C.lay(alpha * under, c, h=hp, rough=r_pipe if r_pipe is not None else RL['rough_pipe'], ao=ao)
        if dbg is not None and not net_layer[0]: mark_cord(alpha * under)
    # 5. arms.  Right arm = the amber "light" side, left arm = teal / dark side
    ar = S['arm']
    Rb = (x < 0)
    E_R, W_R = J('forearm.R'), J('hand.R'); E_L, W_L = J('forearm.L'), J('hand.L')
    def arm_t(E, W): d = W - E; return pdot(d / np.linalg.norm(d), E) / float(np.linalg.norm(d))
    t_fore_R, t_fore_L = arm_t(E_R, W_R), arm_t(E_L, W_L)
    t_fore = np.where(Rb, t_fore_R, t_fore_L)
    arm_tot = np.maximum(armU + shoulder_arm + armF + hand, 1e-3)
    upper_deep = ar['upper'] == 'deep'
    if upper_deep:
        C.lay(arm_w * R_ * ss(ax, 0.17, 0.22), DEEP, rough=0.80)                      # right upper arm + shoulder: DEEP
    if ar['fore'] == 'sleeve':
        C.lay(arm_w * R_ * (armF / arm_tot) * ss(t_fore, -0.02, 0.02), AMBER, rough=0.55)   # right forearm sleeve: amber
    elif ar['fore'] == 'deep':
        C.lay(arm_w * R_ * (armF / arm_tot) * ss(t_fore, -0.02, 0.02), DEEP, rough=0.78)
    if ar['other_fore'] == 'bands':
        for tc in (0.66, 0.76, 0.86):                                                  # left forearm: three amber wrist bands (cord wraps)
            L(arm_w * L_ * armF * band(t_fore - tc, 0.0034, aa), AMBER, h=0.40, rough=0.5, H=RL['ring'], dist=(t_fore - tc) * float(np.linalg.norm(W_L - E_L)), hw=0.0034)
    elif ar['other_fore'] == 'sleeve':
        C.lay(arm_w * L_ * (armF / arm_tot) * ss(t_fore, 0.30, 0.34), AMBER_D, rough=0.55)
    ROLE = dict(deep=DEEP, body=TEAL, accent_d=AMBER_D, crown=TEAL_D)
    C.lay(hand * body_w, ROLE[S['glove']], rough=0.68)                                         # gloves
    for nm_, tw in (('R', t_fore_R), ('L', t_fore_L)):                                # amber wrist ring between sleeve and glove
        L(band(tw - 1.02, 0.0042, aa) * arm_w * (x < 0 if nm_ == 'R' else x > 0), AMBER, h=0.4, rough=0.5, H=RL['ring'], dist=(tw - 1.02) * 0.25, hw=0.0042)
    # 6. legs.  Left leg = amber side accents, right leg = dark side
    y_top = 0.40 + 0.5 * z
    greave_on = 1.0 if S['greave'] == 'accent' else 0.0
    m_greaveR = shin * R_ * cover(y - y_top, aa) * cover(0.10 - y, aa) * greave_on             # right shin: amber greave, slanted top edge
    C.lay(m_greaveR, AMBER, rough=0.52)
    if S['thigh_deep']:
        C.lay(thigh * L_ * ss(y, 0.52, 0.56), DEEP, rough=0.80)
        if PIPE and S['net'].get('terminate', True) and S['net'].get('geo', True) and S['net']['kind'] != 'none' and tk['on']:      # round 16: the DEEP thigh panel = the net's geometric zone (hip-wrap cut -> knee), not the soft weight
            _A = J('thigh.L'); _B = J('shin.L'); _d = (_B - _A) / np.linalg.norm(_B - _A); _rel = P - _A; _sa = _rel @ _d; _rr = np.linalg.norm(_rel - _sa[..., None] * _d, axis=-1)
            C.lay(L_ * body_w * cover(_sa - 0.4015, aa) * cover(_rr - 0.16, aa) * cover(cut_d + 0.0018, aa), DEEP, rough=0.80)
    lat = np.abs(z - 0.0) - 0.011                                                   # outer seam stripe
    m_stripe = leg_w * np.clip(thigh + shin * ss(y, 0.42, 0.50), 0, 1) * cover(lat, aa) * ss(-sgn * nx, 0.4, 0.8)
    L(m_stripe * R_ * (1 - m_greaveR), AMBER, h=0.35, rough=0.5, H=RL['pipe'], dist=lat + 0.011, hw=0.011)
    L(m_stripe * L_, TEAL, h=0.35, rough=0.7, H=RL['pipe'] * 0.8, dist=lat + 0.011, hw=0.011, r_pipe=0.55)
    for yc in (0.175, 0.205):                                                       # left shin ankle bands
        L(shin * L_ * band(y - yc, 0.0040, aa), AMBER, h=0.4, rough=0.5, H=RL['ring'], dist=y - yc, hw=0.0040)
    m_boot = foot * body_w                                                          # boots: DEEP upper, INK toe cap, sole, amber welt
    C.lay(m_boot, ROLE[S['boot']], rough=0.72)
    C.lay(m_boot * ss(z, 0.085, 0.092), INK, rough=0.6)
    C.lay(foot * cover(y - 0.022, aa), SOLE, h=0.0, rough=0.88)
    L(foot * band(y - 0.0265, 0.0015, aa), AMBER, h=0.3, rough=0.5, H=RL['pipe'] * 0.7, dist=y - 0.0265, hw=0.0015)

    # ------------------------------------------------------------------ joint sleeves: DEEP slabs between planes perpendicular to the limb axis + amber rings
    # (plane slices, not sphere cuts: a plane slice of the faceted mesh is a clean curve, a sphere cut zig-zags +-1.5 mm on the low-poly shoulder)
    plate_m = np.zeros(x.shape, np.float32)
    def sleeve(A, B, s0, s1, zone):
        nonlocal plate_m
        s_, th_ = seg_coords(P, J(A), J(B))
        inside = cover(np.abs(s_ - 0.5 * (s0 + s1)) - 0.5 * (s1 - s0), aa)
        C.lay(inside * zone, DEEP, h=0.35, rough=0.60, ao=0.85)
        for sb in (s0 - 0.0035, s1 + 0.0035):
            L(band(s_ - sb, 0.0017, aa) * zone, AMBER, h=0.55, rough=0.45, H=RL['ring'], dist=s_ - sb, hw=0.0017)
            C.lay(stitch(s_ - sb, th_ * 0.055, aa, off=0.0042) * zone, STITCH, h=0.12, rough=0.7)
        plate_m = np.maximum(plate_m, inside * zone)
    for side_, nm in ((1.0, 'L'), (-1.0, 'R')):
        sidew = (sgn == side_).astype(np.float32)
        A_, B_ = J('deltoid.' + nm), J('forearm.' + nm)
        d_ = (B_ - A_) / np.linalg.norm(B_ - A_)
        rel_ = P - A_; s_a = rel_ @ d_; rr = np.linalg.norm(rel_ - s_a[..., None] * d_, axis=-1)
        if S['sleeves']:
            # round 15 (critic r14: "the Verdant armpit piping is pinched"): the shoulder cap used to reach 10.8 cm from the arm axis on every side, so its plane ring cords and its INK edge cord ran over
            # the armpit crease (the surface folds there; the cord pinched to a point).  On the side that faces the torso the cap now ends at cap.r_in (7.5 cm), on the arm itself; the radius
            # blends back to 10.8 cm over the upper half, so the raglan edge across the chest and the shoulder is unchanged.
            cp = S['cap']
            e_in = np.array([-side_, 0.0, 0.0], np.float32); e_in = e_in - d_ * float(np.dot(e_in, d_)); e_in = e_in / np.linalg.norm(e_in)
            cph = ((rel_ - s_a[..., None] * d_) @ e_in) / np.maximum(rr, 1e-6)           # +1 = toward the torso, -1 = away from it
            r_lim = cp['r_out'] - (cp['r_out'] - cp['r_in']) * ss(cph, 0.05, 0.60) if PIPE else cp['r_out']      # (the round-08 legacy print keeps its 10.8 cm cap on every side)
            z_sh = sidew * body_w * (1 - is_head) * cover(rr - r_lim, aa) * 1.0
            sleeve('deltoid.' + nm, 'forearm.' + nm, -0.050, 0.075, z_sh)
            L(band(rr - r_lim, 0.0010, aa) * sidew * body_w * (1 - is_head) * cover(np.abs(s_a - 0.0125) - 0.0625, aa), INK, h=-0.3, rough=0.9, H=RL['net'], dist=rr - r_lim, hw=0.0010, r_pipe=RL['rough_net'])
            z_el = sidew * body_w * np.clip(armU + armF, 0, 1)
            sleeve('deltoid.' + nm, 'forearm.' + nm, 0.262, 0.322, z_el)
            z_kn = sidew * body_w * np.clip(thigh + shin, 0, 1)
            sleeve('thigh.' + nm, 'shin.' + nm, 0.405, 0.470, z_kn)

    # ------------------------------------------------------------------ surface net (diamond / hex / rib / square / chevron / brick, wound around each body segment)
    nk, nsc = S['net']['kind'], S['net']['scale']
    def s_arm(nm):      # metres along the deltoid -> forearm axis from the deltoid joint (negative = toward the neck)
        A_ = J('deltoid.' + nm); B_ = J('forearm.' + nm); return (P - A_) @ ((B_ - A_) / np.linalg.norm(B_ - A_))
    s_armL, s_armR = s_arm('L'), s_arm('R')
    def axial(A_n, B_n):     # (metres along A -> B from A, distance from the A -> B axis)
        A_ = J(A_n); B_ = J(B_n); d_ = (B_ - A_) / np.linalg.norm(B_ - A_); rel_ = P - A_; s_ = rel_ @ d_
        return s_, np.linalg.norm(rel_ - s_[..., None] * d_, axis=-1)
    # round 16 (critic r15 / net_end_check: 83 net lines still died in the open fabric, all on the limbs): with GEO the limb net zones are bounded by geometry only - planes that
    # carry a cord (the cap's lower ring, the elbow / knee slab rings, the wrist / ankle bands, the hip-wrap cut piping) and a radius around the limb axis - not by the soft skin weights
    GEO = bool(PIPE and S['net'].get('terminate', True) and S['net'].get('geo', True) and nk != 'none')
    rrUL = axial('deltoid.L', 'forearm.L')[1]
    s_thL, rr_thL = axial('thigh.L', 'shin.L'); s_thR, rr_thR = axial('thigh.R', 'shin.R')

    def segnet(name_a, name_b, R, cell, phase=0.0):
        return netd(P, J(name_a), J(name_b), R, cell, kind=nk, phase=phase, scale=nsc)
    netw_a = 0.0015 * S['net']['width']      # half width of an amber net line
    netw_d = 0.0011 * S['net']['width']      # half width of a dark hairline
    nd_armU_R, nn_armU_R = netd(P, J('deltoid.R'), J('forearm.R'), 0.050, 0.052, kind=nk, scale=nsc, nodes=True); nd_armU_L = segnet('deltoid.L', 'forearm.L', 0.050, 0.052)
    nd_armF_R = segnet('forearm.R', 'hand.R', 0.040, 0.046); nd_armF_L = segnet('forearm.L', 'hand.L', 0.040, 0.046)
    tor_a, tor_b = np.array([0, 0.95, -0.012], np.float32), np.array([0, 1.52, -0.012], np.float32)
    nd_tor = netd(P, tor_a, tor_b, 0.14, 0.056, kind=nk, scale=nsc)
    nd_thR = segnet('thigh.R', 'shin.R', 0.078, 0.062); nd_thL, nn_thL = netd(P, J('thigh.L'), J('shin.L'), 0.078, 0.062, kind=nk, scale=nsc, nodes=True)
    nd_shR = segnet('shin.R', 'foot.R', 0.052, 0.050); nd_shL = segnet('shin.L', 'foot.L', 0.052, 0.050)
    z_up = tors_w * body_w * ss(y, 1.30, 1.38) * (1 - m_side)
    if PIPE: z_up = z_up * (1.0 - ss(y, 1.425, 1.455))       # round 14 (critic r13: the Sage trapezius groove is torn): the torso net stops at the neck base - on the oblique trapezius slope the cords stretch over a few texels and read as torn creases
    # round 15 (critic r14 "the grooves stop dead"): EVERY net line ends on a seam cord.  Round 14 faded the torso net out at the neck base (y 1.425 - 1.455) and over y 1.30 - 1.38 at the
    # bottom, and a net line also stopped wherever the skin weights ended: the lines died in the open fabric.  The torso net is now a YOKE PANEL with hard edges: above y 1.31, below y 1.43,
    # outside the DEEP shoulder caps (the cap's own cord closes it), inside the DEEP side wedge; a raised seam cord (the face-seam tone) lies on the top and the bottom edge.  The limb nets
    # (below) end hard on a cord that is already there: the wrist bands, the ankle bands, the knee / elbow slab rings, the hip-wrap cut piping.
    TERM = bool(PIPE and S['net'].get('terminate', True) and nk != 'none')
    YOKE_T, YOKE_B = 1.43, 1.31
    if TERM:
        z_up = body_w * cover(ax - 0.215, aa) * (1 - plate_m) * (1 - m_side) * cover(y - YOKE_T, aa) * cover(YOKE_B - y, aa)
    knots = nk in ('diamond', 'square', 'brick', 'hex')
    # amber net on the DEEP right upper arm; DEEP hairline net on the amber right forearm
    zR = arm_w * R_ * (armU + shoulder_arm) * ss(ax, 0.17, 0.22) * (1 - plate_m) * (1.0 if upper_deep else 0.0)
    if PIPE and S['net'].get('terminate', True): zR = zR * cover(-0.0518 - s_armR, aa)      # round 15: no net on the shoulder top, on the neck side of the cap's inner ring cord (the lines used to end there in the open)
    LN(cover(nd_armU_R - netw_a, aa), zR, AMBER, name='armU_R', h=0.30, rough=0.5, H=RL['net'] * 1.1, dist=nd_armU_R, hw=netw_a)
    if knots: L(cover(nn_armU_R - 0.0032, aa) * zR, AMBER, h=0.55, rough=0.42, H=RL['net'] * 1.5, dist=nn_armU_R, hw=0.0032)
    sF_R, thF_R = seg_coords(P, J('forearm.R'), J('hand.R'))
    if ar['fore'] == 'sleeve':
        top_R = cover(np.abs((thF_R - np.pi / 2 + np.pi) % (2 * np.pi) - np.pi) * 0.040 - 0.0035, aa)             # dorsal DEEP stripe on the amber forearm
        _dR = np.abs((thF_R - np.pi / 2 + np.pi) % (2 * np.pi) - np.pi) * 0.040
        L(top_R * arm_w * R_ * (armF / arm_tot) * ss(t_fore, 0.03, 0.08) * (1 - plate_m), DEEP, h=-0.30, rough=0.8, H=RL['net'], dist=_dR, hw=0.0035, r_pipe=RL['rough_net'])
        for tc in (0.25, 0.50):                                                                                  # two DEEP cross seams
            L(band(t_fore - tc, 0.0016, aa) * arm_w * R_ * (armF / arm_tot) * (1 - plate_m), DEEP, h=-0.30, rough=0.8, H=RL['net'], dist=(t_fore - tc) * float(np.linalg.norm(W_R - E_R)), hw=0.0016, r_pipe=RL['rough_net'])
    # dark hairline net on the TEAL panels: upper chest / shoulders / back yoke, the whole left arm, left shin, right thigh
    NK = dict(h=-0.25, rough=0.82, H=RL['net'], hw=netw_d, r_pipe=RL['rough_net'])
    NETC = DEEP * (1 - RL.get('net_tone', 0.0)) + TEAL * RL.get('net_tone', 0.0) if PIPE else DEEP      # round 12: a mid-dark cord shows its lit and its shadowed flank (a near-black one reads flat)
    if TERM:
        len_fL = float(np.linalg.norm(W_L - E_L))
        f_forearm = cover((t_fore - 0.658) * len_fL, aa)                 # ends on the first wrist band (t 0.66, half width 3.4 mm)
        f_shin = cover(0.2095 - y, aa)                                   # starts on the upper ankle band (y 0.205, half width 4 mm)
        f_thR = cover(cut_d + 0.0018, aa) if tk['on'] else ss(y, 0.60, 0.66)          # from the knee slab ring up to the hip-wrap cut piping
    else:
        f_forearm = 1 - ss(t_fore, 0.55, 0.6); f_shin = ss(y, 0.22, 0.26); f_thR = ss(y, 0.60, 0.66)
    LN(cover(nd_tor - netw_d, aa) * 0.85, z_up, NETC, name='torso', dist=nd_tor, **NK)
    zUL = arm_w * L_ * (armU + shoulder_arm) * (1 - plate_m)
    if TERM: zUL = zUL * cover(-0.0518 - s_armL, aa)
    if GEO: zUL = L_ * body_w * cover(0.0785 - s_armL, aa) * cover(s_armL - 0.2585, aa) * cover(rrUL - 0.090, aa) * (1 - plate_m)     # cap's lower ring cord (s 0.0785) -> elbow slab's upper ring (0.2585); 9 cm takes in the deltoid bulge
    LN(cover(nd_armU_L - netw_d, aa) * 0.85, zUL, NETC, name='armU_L', dist=nd_armU_L, **NK)
    zF_L = arm_w * L_ * armF * (1 - plate_m) * f_forearm
    zS_L = shin * L_ * (1 - plate_m) * f_shin
    zT_R = thigh * R_ * (1 - plate_m) * f_thR
    if GEO:
        if ar['other_fore'] == 'bands': t_end = 0.658
        else:       # no wrist bands on this forearm: the net ends on a ring cord of its own (at the sleeve start, or where the bands would be)
            t_end = 0.30 if ar['other_fore'] == 'sleeve' else 0.658
            L(arm_w * L_ * band((t_fore - t_end - 0.0034 / len_fL) * len_fL, 0.0034, aa), NETC * 0.6 + TEAL * 0.4, h=0.35, rough=0.5, H=RL['ring'], dist=(t_fore - t_end - 0.0034 / len_fL) * len_fL, hw=0.0034)
        rrF = axial('forearm.L', 'hand.L')[1]
        zF_L = L_ * body_w * cover(0.3255 - s_armL, aa) * cover((t_fore - t_end) * len_fL, aa) * cover(rrF - 0.065, aa) * (1 - plate_m)                          # elbow slab's lower ring (s 0.3255) -> the wrist band / ring
        zS_L = L_ * body_w * cover(0.4735 - s_thL, aa) * cover(rr_thL - 0.16, aa) * f_shin * (1 - plate_m)                            # knee slab's lower ring -> the upper ankle band
        zT_R = R_ * body_w * cover(s_thR - 0.4015, aa) * cover(rr_thR - 0.16, aa) * f_thR * (1 - plate_m)                            # the hip-wrap cut piping -> the knee slab's upper ring
    if GEO:
        RC = dict(h=0.35, rough=0.5, H=RL['ring'], r_pipe=RL['rough_pipe'])
        rcol = NETC * 0.6 + TEAL * 0.4
        if not S['sleeves']:      # no cap / elbow / knee slabs on this suit: the planes that bound the limb nets get ring cords of their own
            for sd_, nm_, sg_ in ((L_, 'L', 1.0), (R_, 'R', -1.0)):
                A_r = J('deltoid.' + nm_); d_r = (J('forearm.' + nm_) - A_r) / np.linalg.norm(J('forearm.' + nm_) - A_r)
                rel_r = P - A_r; s_a = rel_r @ d_r; perp_r = rel_r - s_a[..., None] * d_r; r_a = np.linalg.norm(perp_r, axis=-1)
                e_r = np.array([-sg_, 0.0, 0.0], np.float32); e_r = e_r - d_r * float(np.dot(e_r, d_r)); e_r = e_r / np.linalg.norm(e_r)
                ph_r = (perp_r @ e_r) / np.maximum(r_a, 1e-6)                      # +1 = toward the torso
                r_ring = 0.090 - 0.032 * ss(ph_r, 0.05, 0.60)                        # the ring stays ON the arm: 9 cm outside (the deltoid bulge), 5.8 cm on the torso side (r16 hold 2: a cord stub crossed onto the Saffron torso at the armpit)
                for c_ in (0.0785, 0.2585, 0.3255):
                    L(sd_ * body_w * band(s_a - c_, 0.0017, aa) * cover(r_a - r_ring, aa), rcol, dist=s_a - c_, hw=0.0017, **RC)
                s_t, r_t = axial('thigh.' + nm_, 'shin.' + nm_)
                for c_ in (0.4015, 0.4735):
                    L(sd_ * body_w * band(s_t - c_, 0.0017, aa) * cover(r_t - 0.16, aa), rcol, dist=s_t - c_, hw=0.0017, **RC)
        if tk['on']:              # the inseam: where the hip-wrap cut lies above the crotch the two thigh nets meet on the midline - a seam cord there
            L(body_w * band(x, 0.0024, aa) * cover(cut_d + 0.0018, aa) * ss(y, 0.60, 0.64), rcol, dist=x, hw=0.0024, **RC)
    LN(cover(nd_armF_L - netw_d, aa) * 0.85, zF_L, NETC, name='armF_L', dist=nd_armF_L, **NK)
    LN(cover(nd_shL - netw_d, aa) * 0.85, zS_L, NETC, name='shin_L', dist=nd_shL, **NK)
    LN(cover(nd_thR - netw_d, aa) * 0.85, zT_R, NETC, name='thigh_R', dist=nd_thR, **NK)
    # amber net on the DEEP left thigh and dark net on the amber greave
    zL = thigh * L_ * ss(y, 0.56, 0.60) * (1 - plate_m) * ss(0.78 - y, -0.03, 0.03) * (1.0 if S['thigh_deep'] else 0.0)
    if TERM and tk['on']: zL = thigh * L_ * (1 - plate_m) * cover(cut_d + 0.0018, aa) * (1.0 if S['thigh_deep'] else 0.0)           # round 15: from the knee slab ring to the hip-wrap cut piping
    if GEO and tk['on']: zL = L_ * body_w * cover(s_thL - 0.4015, aa) * cover(rr_thL - 0.16, aa) * (1 - plate_m) * cover(cut_d + 0.0018, aa) * (1.0 if S['thigh_deep'] else 0.0)
    LN(cover(nd_thL - netw_a * 0.9, aa), zL, AMBER_D, name='thigh_L', h=0.25, rough=0.55, H=RL['net'] * 1.1, dist=nd_thL, hw=netw_a * 0.9)
    if knots: L(cover(nn_thL - 0.0034, aa) * zL, AMBER, h=0.55, rough=0.42, H=RL['net'] * 1.5, dist=nn_thL, hw=0.0034)
    sS_R, thS_R = seg_coords(P, J('shin.R'), J('foot.R'))
    _dS = np.abs((thS_R - 0.0 + np.pi) % (2 * np.pi) - np.pi) * 0.045
    L(cover(_dS - 0.0035, aa) * m_greaveR * (1 - plate_m), DEEP, h=-0.30, rough=0.8, H=RL['net'], dist=_dS, hw=0.0035, r_pipe=RL['rough_net'])   # shin-front DEEP stripe

    if TERM:      # round 15: the yoke seam cords (the face-seam tone, like the cheek panel seams): the top and the bottom edge of the torso net panel, front and back, under the sash
        ycol = 0.55 * TEAL + 0.45 * STITCH
        yoke_m = body_w * cover(ax - 0.215, aa) * (1 - plate_m) * (1 - m_side)
        for yc_ in (YOKE_T, YOKE_B):
            L(yoke_m * band(y - yc_, 0.0015, aa), ycol, h=0.4, rough=RL['rough_pipe'] + 0.05, H=RL['seam'] * 0.8, dist=y - yc_, hw=0.0015)
        if not S['sleeves'] and S['net'].get('geo', True):      # round 16: no shoulder caps close the yoke panel's sides on this suit: a side seam cord at |x| 0.215
            L(body_w * (1 - m_side) * band(ax - 0.215, 0.0015, aa) * cover(y - YOKE_T - 0.0015, aa) * cover(YOKE_B - 0.0015 - y, aa), ycol, h=0.4, rough=RL['rough_pipe'] + 0.05, H=RL['seam'] * 0.8, dist=ax - 0.215, hw=0.0015)

    # ------------------------------------------------------------------ chest badge (front) and back mark
    gl = S['glyph']
    def badge(cx, cy, outer_a):
        u = (x - cx); v = (y - cy)
        ring = band(hex_d(u, v, outer_a, pointy=True) + 0.0020, 0.0024, aa)
        ang = np.arctan2(v, u)
        gap = np.zeros_like(ang)
        for a0 in (np.pi / 6, 5 * np.pi / 6, -np.pi / 2):        # 3 gaps in the ring
            da = np.abs((ang - a0 + np.pi) % (2 * np.pi) - np.pi)
            gap = np.maximum(gap, cover(da - 0.16, aa / max(outer_a, 1e-3)))
        ring = ring * (1 - gap)
        vanes = np.zeros_like(ang)                                # 3 kite vanes pointing at 90, 210, 330 deg
        for a0 in (np.pi / 2, np.pi / 2 + 2 * np.pi / 3, np.pi / 2 + 4 * np.pi / 3):
            c, s_ = np.cos(a0), np.sin(a0)
            along = u * c + v * s_; perp = -u * s_ + v * c
            half = 0.0075 * np.clip(1 - (along / (outer_a * 0.68)), 0, 1) * np.clip(along / 0.006, 0, 1) + 0.0004
            vanes = np.maximum(vanes, cover(np.abs(perp) - half, aa) * cover(along - outer_a * 0.68, aa) * cover(-along + 0.004, aa))
        core = cover(hex_d(u, v, outer_a * 0.20, pointy=False), aa)
        return ring, vanes, core
    f_ = front * tors_w * body_w
    b_ = back * tors_w * body_w
    # round 13 (critic r12: Cinder's emblem is cyan on a cyan sash): where the front mark lies on the accent sash panel it is laid in the DEEP colour
    gcol = (AMBER[None, None, :] * (1 - sash_cov[..., None]) + DEEP[None, None, :] * sash_cov[..., None]) if PIPE else AMBER
    # round 16 (critic r15: the back mark read as the front emblem "projected through the torso"): the back mark is a TONE-ON-TONE emboss (a raised mark in a darker shade of
    # the body colour), never the accent; the round-08 legacy print keeps its accent back mark
    TONE_B = PIPE and gl.get('back', 'tone') == 'tone'
    BCOL = (0.55 * TEAL + 0.45 * DEEP) if TONE_B else AMBER
    BH = (RL['glyph'] * 0.8, RL['glyph'] * 0.7, 0.50) if TONE_B else (0.45, 0.40, 0.40)
    if gl['kind'] == 'hexvane':
        ring, vanes, core = badge(gl['x'], gl['y'], 0.046 * gl['size'])
        gh = (RL['glyph'], RL['glyph'] * 0.9) if PIPE else (0.45, 0.40)
        C.lay(f_ * ring, gcol, h=gh[0], rough=0.40)
        C.lay(f_ * np.maximum(vanes, core), gcol, h=gh[1], rough=0.40)
        ring_b, _, core_b = badge(0.0, gl['y'] + 0.023, 0.042 * gl['size'])
        C.lay(b_ * ring_b, BCOL, h=BH[0], rough=BH[2])
        C.lay(b_ * core_b, BCOL, h=BH[1], rough=BH[2])
    else:
        ln, so = glyph(gl['kind'], x, y, gl['x'], gl['y'], gl['size'], aa)
        gh = (RL['glyph'], RL['glyph'] * 0.9) if PIPE else (0.45, 0.40)
        C.lay(f_ * ln, gcol, h=gh[0], rough=0.40)
        C.lay(f_ * so, gcol, h=gh[1], rough=0.40)
        ln_b, so_b = glyph(gl['kind'], x, y, 0.0, gl['y'] + 0.023, gl['size'] * 0.8, aa)
        C.lay(b_ * ln_b, BCOL, h=BH[0], rough=BH[2])
        C.lay(b_ * so_b, BCOL, h=BH[1], rough=BH[2])
    # belt buckle
    bkind = S['belt']['buckle']
    if bkind == 'hex':
        bk = hex_d(x, y - 1.055, 0.021, pointy=False)
        C.lay(front * tors_w * body_w * cover(bk, aa), AMBER, h=0.5, rough=0.4)
        C.lay(front * tors_w * body_w * cover(hex_d(x, y - 1.055, 0.011, pointy=False), aa), DEEP, h=0.2, rough=0.6)
    elif bkind == 'round':
        rb = np.hypot(x, y - 1.055)
        C.lay(front * tors_w * body_w * cover(rb - 0.021, aa), AMBER, h=0.5, rough=0.4)
        C.lay(front * tors_w * body_w * cover(rb - 0.011, aa), DEEP, h=0.2, rough=0.6)
    elif bkind == 'bar':
        bk = np.maximum(np.abs(x) - 0.030, np.abs(y - 1.055) - 0.0075)
        C.lay(front * tors_w * body_w * cover(bk, aa), AMBER, h=0.5, rough=0.4)

    # ------------------------------------------------------------------ piping (amber hairlines) along the main cuts
    pip = 0.0014
    PK = dict(h=0.45, rough=0.45, H=RL['pipe'], hw=pip)
    L(body_w * tors_w * band(y - 1.0795, pip, aa), AMBER, dist=y - 1.0795, **PK)
    L(body_w * tors_w * band(y - 1.0305, pip, aa), AMBER, dist=y - 1.0305, **PK)
    if tk['on']:
        L(body_w * np.clip(tors_w + thigh, 0, 1) * band(cut_d, pip * 1.3, aa) * ss(1.03 - y, -0.002, 0.004), AMBER, h=0.45, rough=0.45, H=RL['pipe'], dist=cut_d, hw=pip * 1.3)
    wtop = (1.0 - ss(y, 1.195, 1.235)) if PIPE else 1.0       # round 14 (critic r13: the Ash armpit stitches zigzag): the wedge pipe + stitch rows end 3.5 cm below the armpit crease (the surface folds there and the dashes pile up)
    if TERM: wtop = np.maximum(wtop, ss(y, 1.285, 1.305) * cover(y - 1.435, aa))      # round 15: the wedge edge is the SIDE SEAM of the torso net panel from the yoke's bottom seam up to its top seam (the armpit crease, y 1.2 - 1.29, stays bare)
    if PIPE and S['wedge'].get('back_tone', True):
        # round 16: the wedge edge pipe is accent on the FRONT only; on the back (z < the torso axis) it is the seam tone (no accent line on the back torso)
        fr_w = cover(-0.012 - z, aa)
        L(m_side * band(xb - ax, pip, aa) * ss(y, 1.06, 1.12) * wtop * fr_w, AMBER_D, h=0.35, rough=0.5, H=RL['pipe'], dist=xb - ax, hw=pip)
        L(m_side * band(xb - ax, pip, aa) * ss(y, 1.06, 1.12) * wtop * (1 - fr_w), 0.55 * TEAL + 0.45 * STITCH, h=0.35, rough=0.5, H=RL['pipe'], dist=xb - ax, hw=pip)
    else:
        L(m_side * band(xb - ax, pip, aa) * ss(y, 1.06, 1.12) * wtop, AMBER_D, h=0.35, rough=0.5, H=RL['pipe'], dist=xb - ax, hw=pip)
    # top-stitching beside the piping (dashed, light teal): belt, hip-wrap cut, sash edges, side wedge
    STa = 0.85
    L(body_w * tors_w * np.maximum(stitch(y - 1.0795, x, aa), stitch(y - 1.0305, x, aa)) * STa, STITCH, h=0.12, rough=0.7)
    if tk['on']:
        L(body_w * np.clip(tors_w + thigh, 0, 1) * stitch(cut_d, cut_along, aa, off=0.0034) * ss(1.03 - y, -0.002, 0.004) * STa, STITCH, h=0.12, rough=0.7)
    if zone_s is not None:
        for o in offs:
            hw_ = sa['half']
            C.lay(zone_s * np.maximum(stitch(d_s - o - hw_, P @ t_s, aa, off=0.0030) * (d_s - o > 0.0), stitch(d_s - o + hw_, P @ t_s, aa, off=0.0030) * (d_s - o < 0.0)) * STa, STITCH, h=0.12, rough=0.7)
            if PIPE:     # round 14: the sash ENDS are finished like the long edges: two stitch rows (inside the border cord and 3 mm outside) and an accent pipe 5.8 mm outside the end
                tw_ = ss(tors_w, 0.30, 0.40) * body_w
                for e_, al_ in sash_ends:
                    pan = band(d_s - o, hw_, aa) * tw_ * sash_fg
                    ext = pan * cover(-(e_ + 0.0045), aa)
                    C.lay(ext * stitch(e_, al_, aa, off=0.0030) * STa, STITCH, h=0.12, rough=0.7)
                    if sa.get('pipe_join', True):      # round 15 (critic r14: "a lime cord floats 40 px off the Ash sash end"): the accent pipe lies ON the end line, its inner edge touching the DEEP border cord (no gap, 1 mm wide)
                        L(pan * band(e_ + 0.0005, 0.0005, aa), AMBER, h=0.45, rough=0.45, H=RL['pipe'], dist=e_ + 0.0005, hw=0.0005)
                    else:
                        L(pan * cover(-(e_ + 0.0070), aa) * band(e_ + 0.0058, 0.0014, aa), AMBER, h=0.45, rough=0.45, H=RL['pipe'], dist=e_ + 0.0058, hw=0.0014)
    L(m_side * stitch(xb - ax, y, aa, off=0.0030) * ss(y, 1.06, 1.12) * wtop * STa, STITCH, h=0.12, rough=0.7)

    # ------------------------------------------------------------------ mask / hood
    yb = (1.668 if PIPE else 1.662) + 0.46 * z          # round 13: the crown piping arc moves up with the bigger lenses (it sits on the sculpted brow ridge)
    crown = is_head * cover(yb - y, aa)                         # above the boundary
    hood_col = ROLE[S['hood']]
    FC = S['face']
    if PIPE and S['hood'] == 'deep':
        hood_col = 0.5 * DEEP + 0.5 * TEAL_D        # round 13: a near-black hood hides the sculpted relief (luma ~14 in the 4K stills): halfway to the crown colour
        hood_col = hood_col * (1.0 - FC['lift']) + TEAL * FC['lift']       # round 14: dark hoods (Tessera / Plum) go on toward the body colour: the cheek-line luma test needs an albedo luma of ~50+
    C.lay(is_head, hood_col, rough=RL.get('rough_hood', 0.80) if PIPE else 0.80)       # round 13: a satin hood (0.50) catches the key light on the sculpted brow / nose / cheeks
    C.lay(crown, TEAL_D, rough=RL.get('rough_crown', 0.74) if PIPE else 0.74)
    if PIPE and (FC['tone_up'] > 0 or FC['tone_dn'] > 0):
        # round 14: baked relief tone.  The sculpt field (hero_head_r14.field_mm, evaluated at this texel's rest-pose x, y exactly as it displaced the vertex) in units of amp_mm:
        # + on the brow ridge, cheek bones, nose, alae, mouth, chin (lighter); - in the eye sockets, hollows, the nostril undercut, the groove (darker).
        zone_f = (y > 1.545) & (y < 1.76) & (ax < 0.095) & (is_head > 0.01) & (nz > 0.2)
        if zone_f.any():
            import hero_head_r14 as HH14
            hf = np.zeros(x.shape, np.float32)
            hf[zone_f] = HH14.field_mm(ax[zone_f].astype(np.float64), y[zone_f].astype(np.float64)).astype(np.float32)
            wz_f = ss(np.clip(nz, 0, 1), 0.32, 0.68)
            tn = np.clip(hf * wz_f / FC['amp_mm'], -1.0, 1.0)
            mul = 1.0 + FC['tone_up'] * np.maximum(tn, 0.0) - FC['tone_dn'] * np.maximum(-tn, 0.0)
            C.col = np.clip(C.col * np.where(is_head > 0.01, mul, 1.0)[..., None], 0, 1)
    if S['crown']['edge']:
        L(is_head * band(y - yb, 0.0018, aa), AMBER, h=0.5, rough=0.45, H=RL['pipe'], dist=y - yb, hw=0.0018)
    ck = S['crown']['kind']
    if ck == 'honeycomb':           # crown honeycomb (hairline, projected from above)
        hc = hex_cell_edge(x, z, 0.014)
        C.lay(crown * ss(y, 1.72, 1.76) * cover(0.0009 - hc, aa) * 0.9 + 0.0 * crown, DEEP, h=-0.25, rough=0.85)
    elif ck == 'racing':            # two accent stripes over the crown, front to back
        for s_ in (-1.0, 1.0):
            C.lay(crown * ss(y, 1.70, 1.74) * band(x - s_ * 0.016, 0.0042, aa), AMBER, h=0.35, rough=0.5)
            C.lay(crown * ss(y, 1.70, 1.74) * band(x - s_ * 0.016, 0.0052, aa) * 0.0, INK)
    elif ck == 'chevron':           # nested forward-pointing Vs over the crown
        for k_ in range(4):
            dch = np.abs(z * 1.0 + 0.9 * np.abs(x) - (0.045 - 0.020 * k_)) / np.sqrt(1.81)
            C.lay(crown * ss(y, 1.70, 1.74) * band(dch, 0.0024, aa), AMBER_D, h=0.30, rough=0.5)
    if PIPE:     # round 13: the face seam (critic r12: a 12 px black kinked ink seam on every suit) is a RAISED cord in the body colour, a lit / shadow pair, not ink
        seam_a, seam_h = cord(x, 0.0017, aa, RL['seam'])
        fcol = 0.55 * TEAL + 0.45 * STITCH
        C.lay(is_head * cover(-z, aa) * seam_a, fcol, h=seam_h, rough=RL['rough_pipe'] + 0.05)     # round 14: a lighter tint than the lifted hood (a cord in the hood colour would only show by its shading)
        if S['face'].get('cheek_seams', True):
            # round 14: two raised PANEL SEAMS per cheek (the critic's G3 line - a horizontal luma line through the cheek bones - crosses them): the outer one runs from the eye frame down
            # the cheek bone plane to the jaw (bowing outward below the cheek bone), the inner one from the nose-bridge flank toward the mouth piece.  Light raised cords (like the face seam):
            # their luma contrast does not depend on the sun, which on a dark hood gives the sculpt only a 10 - 20 luma swing.
            def panel_seam(xc, g, ya, yb, hwc, Hc, tip=0.0):
                dd = (ax - xc) / np.sqrt(1.0 + g * g)
                if tip > 0.0:
                    # round 17 (critic r16: "the cheek-cord ends are raw"): the free (jaw) end of the cord is finished with a ROUNDED TIP: over the last `tip` metres the half width and the height
                    # follow a circular cap (sqrt(c (2 - c))), so the cord closes like a piped end instead of being cut off square.  The upper end sits under the eye frame.
                    c = np.clip((y - yb) / tip, 0.0, 1.0); cap = np.sqrt(c * (2.0 - c))
                    hw_ = hwc * np.maximum(cap, 0.05)
                    a_c = band(dd, hw_, aa)
                    u_ = np.clip(np.abs(dd) / np.maximum(hw_, 1e-6), 0, 1)
                    h_c = (Hc * cap * np.sqrt(np.clip(1.0 - u_ * u_, 0.0, 1.0)) * 0.85 + 0.15 * Hc * cap).astype(np.float32)
                    msk = is_head * cover(-z, aa) * cover(y - ya, aa) * cover((yb - 0.0008) - y, aa)
                    C.lay(msk * a_c, fcol, h=h_c, rough=RL['rough_pipe'] + 0.05)
                    return
                a_c, h_c = cord(dd, hwc, aa, Hc)
                msk = is_head * cover(-z, aa) * cover(y - ya, aa) * cover(yb - y, aa)
                C.lay(msk * a_c, fcol, h=h_c, rough=RL['rough_pipe'] + 0.05)
            s1 = np.maximum((1.640 - y) / 0.05, 0.0)
            ptip = 0.006 if S['face'].get('cord_tip', True) else 0.0
            # tip mode: the cord is drawn for y >= yb - 0.0008 and the cap closes it between yb and yb + tip (y - yb = 0 is the end)
            panel_seam(0.056 + 0.012 * s1 * s1, -0.48 * s1, 1.662, 1.570, 0.0016, RL['seam'] * 0.85, ptip)
            u2 = np.clip((1.659 - y) / 0.039, 0.0, 1.0)
            panel_seam(0.0185 + 0.021 * u2 ** 1.5, -0.8077 * np.sqrt(u2), 1.659, 1.620, 0.0015, RL['seam'] * 0.85, ptip * 0.8)
    else:
        C.lay(is_head * cover(np.abs(x) - 0.0011, aa) * cover(-z, aa), INK, h=-0.3, rough=0.9)       # dorsal seam (round 08 legacy)
    if S['brow'] != 'none':
        for s_ in (-1.0, 1.0):                                                                          # brow flashes (front projection)
            cx, cy = s_ * 0.036, (1.737 if PIPE else 1.716)
            ang = np.radians(22.0)
            u = (x - cx) * s_; v = (y - cy)
            ca, sa_ = np.cos(ang), np.sin(ang)
            along = u * ca + v * sa_; perp = -u * sa_ + v * ca
            if S['brow'] == 'flash':
                halfw = 0.0030 * np.clip(1 - np.abs(along) / 0.017, 0, 1) + 0.0004
                fl = cover(np.abs(perp) - halfw, aa) * cover(np.abs(along) - 0.017, aa)
            else:   # tick: a short bar above the outer corner of each eye
                fl = cover(np.maximum(np.abs(along - 0.004) - 0.010, np.abs(perp) - 0.0022), aa)
            C.lay(is_head * front * fl, AMBER, h=0.45, rough=0.45)
    # jaw vents under the lens line
    if S['vent'] == 'hex':          # honeycomb (INK hairlines on DEEP)
        cell = hex_cell_edge(x, y, 0.0062)
        ell = np.sqrt((x / 0.040) ** 2 + ((y - 1.606) / 0.021) ** 2)
        vent_zone = is_head * front * cover(ell - 1.0, aa / 0.02)
        C.lay(vent_zone * 0.85 * cover(cell - 0.0009, aa) * 0 + vent_zone * cover(0.0011 - cell, aa), AMBER_D, h=0.3, rough=0.5)
        C.lay(vent_zone * cover(cell - 0.0011, aa) * 0.0, INK)
    elif S['vent'] == 'slots':      # three horizontal slots
        ell = np.sqrt((x / 0.040) ** 2 + ((y - 1.606) / 0.021) ** 2)
        vent_zone = is_head * front * cover(ell - 1.0, aa / 0.02)
        for yc_ in (1.596, 1.606, 1.616):
            C.lay(vent_zone * band(y - yc_, 0.0017, aa), AMBER_D, h=0.3, rough=0.5)
    L(neck_ok * ss(head, 0.05, 0.15) * band(y - 1.4765, 0.0013, aa), AMBER, h=0.4, rough=0.45, H=RL['pipe'], dist=y - 1.4765, hw=0.0013)                                   # collar piping

    # ------------------------------------------------------------------ fabric mottling and occlusion in the grooves
    mott = 0.035 * noise3(P, 22.0, 1) + 0.02 * noise3(P, 140.0, 2)
    C.col = np.clip(C.col * (1 + S['mott'] * mott[..., None]), 0, 1)
    C.ao = np.clip(C.ao - 0.25 * np.clip(-C.h, 0, 1), 0, 1)
    out = dict(col=C.col, h=C.h, rough=C.rough, ao=C.ao)
    if PIPE: out['cavity'] = float(RL['cavity'])      # the map writer darkens the AO at the foot of every cord (needs the whole atlas: hero_suit_r8.cavity_ao)
    return out

#!/usr/bin/env python3
"""Street-level 3D kit for the Unreal port (round 05): everything between the pavement and the second-floor cornice, plus fire escapes.

For every ground-floor face of the exported facade meshes (tools/export/street_faces.py: face frame, storefront height gH, bay layout of the
browser facade shader: nb = max(1, round(W / 6.5)) bays of width W / nb) this script builds real geometry in front of the shader-drawn wall:
  * masonry piers with plinth + capital on every bay boundary, a stepped stone cornice at gH (thin metal canopy on curtain-wall podiums)
  * 3D storefront frames (jambs, head, sill, transom, mullions at the shader's positions, doors with kick plates and pull bars)
  * fascia sign boards and awnings (fabric with a lettered valance, or metal marquees) with ORIGINAL signage from gen_street_signs.py
  * fire escapes (grated platforms, railings, stair flights, drop ladder) on pre-war faces and on some side-street faces
Bays that already carry a browser signage mesh (awnings, canopies, marquees) keep it: no second awning / board is added there.
Output: <export>/mesh/streetkit/streetkit__t<ix>_<iz>.glb (positions relative to the tile centre like every exported mesh) + streetkit.json;
(island r02) the fire escapes in their own tiles <export>/mesh/fireescape/fireescape__t<ix>_<iz>.glb (streetkit.json 'fireescape_files').
Vertex data: POSITION, NORMAL, TEXCOORD_0 (atlas uv, image space v = 0 at the top), TEXCOORD_1 (kind, param), TEXCOORD_2 (metres along the
element, used by the procedural masonry / grating), COLOR_0 (linear base colour). Kinds: 0 masonry (param 0 ashlar, 1 brick, 2 smooth), 1 metal,
2 fabric (param = stripes per metre), 3 sign atlas (param 0 fascia, 1 valance light letters, 2 valance dark letters), 4 grating, 5 railing, 6 ladder,
7 lamp / emissive.
usage: street_kit.py [export_dir]
"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbio import read_glb, write_glb
from street_faces import load_faces, EXPORT

EXP = sys.argv[1] if len(sys.argv) > 1 else EXPORT
f32 = np.float32

# ------------------------------------------------------------------ hashes (mirror the browser shader's fh1 in float32)
def fh1(x, y):
    px = f32(x) * f32(123.34); py = f32(y) * f32(456.21)
    px = px - np.floor(px); py = py - np.floor(py)
    d = px * (px + f32(45.32)) + py * (py + f32(45.32))
    px = px + d; py = py + d
    r = px * py; return float(r - np.floor(r))

def hrand(*a):
    h = 2166136261
    for v in a:
        h ^= int(abs(v) * 1000003.0) & 0xFFFFFFFF; h = (h * 16777619) & 0xFFFFFFFF
    h ^= h >> 13; h = (h * 0x5bd1e995) & 0xFFFFFFFF; h ^= h >> 15
    return (h & 0xFFFFFF) / float(0x1000000)

# ------------------------------------------------------------------ mesh builder
class MB:
    def __init__(self, cx, cz):
        self.cx, self.cz = cx, cz
        self.P, self.N, self.U0, self.U1, self.U2, self.C, self.I = [], [], [], [], [], [], []
        self.n = 0
    def quad(self, p, n, kind, param, col, uv0=None, uv2=None):
        """p: 4 corners (browser world metres); n: outward normal; winding fixed to face n."""
        p = [np.asarray(q, float) for q in p]
        g = np.cross(p[1] - p[0], p[2] - p[0])
        order = [0, 1, 2, 3] if np.dot(g, n) >= 0 else [0, 3, 2, 1]
        uv0 = uv0 if uv0 is not None else [(0, 0), (1, 0), (1, 1), (0, 1)]
        uv2 = uv2 if uv2 is not None else [(0, 0), (1, 0), (1, 1), (0, 1)]
        for k in order:
            self.P.append((p[k][0] - self.cx, p[k][1], p[k][2] - self.cz)); self.N.append(tuple(n))
            self.U0.append(uv0[k]); self.U1.append((kind, param)); self.U2.append(uv2[k]); self.C.append((*col, 1.0))
        b = self.n; self.I += [b, b + 1, b + 2, b, b + 2, b + 3]; self.n += 4
    def tri(self, p, n, kind, param, col, uv0=None, uv2=None):
        self.quad([p[0], p[1], p[2], p[2]], n, kind, param, col, uv0, uv2)
    def arrays(self):
        a = {'POSITION': np.array(self.P, f32), 'NORMAL': np.array(self.N, f32), 'TEXCOORD_0': np.array(self.U0, f32), 'TEXCOORD_1': np.array(self.U1, f32),
             'TEXCOORD_2': np.array(self.U2, f32), 'COLOR_0': np.array(self.C, f32)}
        return a, np.array(self.I, np.uint32)

class Frame:
    def __init__(self, f):
        self.O = np.array(f['O']); self.T = np.array(f['T']); self.N = np.array(f['N'])
    def p(self, u, y, n=0.0):
        return np.array([self.O[0] + self.T[0] * u + self.N[0] * n, y, self.O[1] + self.T[1] * u + self.N[1] * n])
    @property
    def n3(self): return np.array([self.N[0], 0, self.N[1]])
    @property
    def t3(self): return np.array([self.T[0], 0, self.T[1]])

def box(mb, F, u0, u1, y0, y1, n0, n1, kind, param, col, faces='FTLRUD', uvfront=None):
    """box in the face frame. faces: F front(+N) B back(-N) T=+T side, L=-T side, U up, D down"""
    n3, t3 = F.n3, F.t3; up = np.array([0, 1.0, 0])
    P = F.p
    if 'F' in faces: mb.quad([P(u0, y0, n1), P(u1, y0, n1), P(u1, y1, n1), P(u0, y1, n1)], n3, kind, param, col, uvfront, [(u0, y0), (u1, y0), (u1, y1), (u0, y1)])
    if 'B' in faces: mb.quad([P(u1, y0, n0), P(u0, y0, n0), P(u0, y1, n0), P(u1, y1, n0)], -n3, kind, param, col, None, [(u1, y0), (u0, y0), (u0, y1), (u1, y1)])
    if 'T' in faces: mb.quad([P(u1, y0, n1), P(u1, y0, n0), P(u1, y1, n0), P(u1, y1, n1)], t3, kind, param, col, None, [(n1, y0), (n0, y0), (n0, y1), (n1, y1)])
    if 'L' in faces: mb.quad([P(u0, y0, n0), P(u0, y0, n1), P(u0, y1, n1), P(u0, y1, n0)], -t3, kind, param, col, None, [(n0, y0), (n1, y0), (n1, y1), (n0, y1)])
    if 'U' in faces: mb.quad([P(u0, y1, n1), P(u1, y1, n1), P(u1, y1, n0), P(u0, y1, n0)], up, kind, param, col, None, [(u0, n1), (u1, n1), (u1, n0), (u0, n0)])
    if 'D' in faces: mb.quad([P(u0, y0, n0), P(u1, y0, n0), P(u1, y0, n1), P(u0, y0, n1)], -up, kind, param, col, None, [(u0, n0), (u1, n0), (u1, n1), (u0, n1)])

# ------------------------------------------------------------------ palettes (linear)
STONE = [(0.34, 0.32, 0.28), (0.30, 0.24, 0.17), (0.075, 0.075, 0.08), (0.36, 0.34, 0.30), (0.23, 0.11, 0.075)]  # limestone, sandstone, granite, cream, brick
STONE_PARAM = [0, 0, 0, 2, 1]
METAL = [(0.02, 0.02, 0.022), (0.03, 0.05, 0.04), (0.06, 0.04, 0.03), (0.09, 0.09, 0.095), (0.015, 0.02, 0.05)]  # black, bottle green, bronze, aluminium, navy
AWN = [(0.05, 0.28, 0.13), (0.04, 0.09, 0.32), (0.4, 0.05, 0.07), (0.05, 0.05, 0.055), (0.48, 0.34, 0.14), (0.5, 0.2, 0.05), (0.04, 0.26, 0.28), (0.5, 0.48, 0.44), (0.55, 0.07, 0.08), (0.1, 0.1, 0.36), (0.36, 0.05, 0.2), (0.6, 0.5, 0.2)]

# ------------------------------------------------------------------ builders
def atlas_fascia(i, ratio):
    col, row = i % 4, i // 4
    return [(col * 0.25, (row * 160) / 2048.0 + 160 / 2048.0), ((col + 1) * 0.25, (row * 160) / 2048.0 + 160 / 2048.0),
            ((col + 1) * 0.25, (row * 160) / 2048.0), (col * 0.25, (row * 160) / 2048.0)]  # (u,v) with v downwards; corners: bl, br, tr, tl
def atlas_valance(i):
    col, row = i % 4, i // 4
    v0 = (1280 + row * 64) / 2048.0; v1 = (1280 + row * 64 + 64) / 2048.0
    return [(col * 0.25, v1), ((col + 1) * 0.25, v1), ((col + 1) * 0.25, v0), (col * 0.25, v0)]

def pier(mb, F, u, gH, col, param, wide=0.84):
    hw = wide / 2
    box(mb, F, u - hw - 0.05, u + hw + 0.05, 0.0, 0.5, 0.0, 0.27, 0, param, tuple(c * 0.8 for c in col), 'FTLU')            # plinth
    box(mb, F, u - hw, u + hw, 0.5, gH - 1.15, 0.0, 0.22, 0, param, col, 'FTL')                                           # shaft
    box(mb, F, u - hw - 0.03, u + hw + 0.03, gH - 1.15, gH - 1.0, 0.0, 0.26, 0, param, col, 'FTLU')                       # capital ring
    box(mb, F, u - hw - 0.08, u + hw + 0.08, gH - 1.0, gH - 0.5, 0.0, 0.31, 0, param, col, 'FTLU')

def cornice(mb, F, u0, u1, gH, col, param, modern):
    if modern:
        box(mb, F, u0, u1, gH - 0.32, gH, 0.0, 0.7, 1, 0, METAL[3], 'FTLUD')
        return
    box(mb, F, u0, u1, gH - 0.5, gH - 0.28, 0.0, 0.2, 0, param, col, 'FTLD')
    box(mb, F, u0, u1, gH - 0.28, gH + 0.06, 0.0, 0.4, 0, param, tuple(c * 1.06 for c in col), 'FTLD')
    box(mb, F, u0, u1, gH + 0.06, gH + 0.3, 0.0, 0.54, 0, param, tuple(c * 1.1 for c in col), 'FTLUD')
    # dentils
    step = 0.28; n = int((u1 - u0) / step)
    for k in range(0, n, 2):
        box(mb, F, u0 + k * step, u0 + k * step + 0.14, gH - 0.28, gH - 0.1, 0.4, 0.5, 0, param, col, 'F')

def storefront_frame(mb, F, ua, ub, signY0, mcol, rnd, wdoor):
    """3D frame of the shader's glass opening [ua, ub] x [0.55, signY0]"""
    fw, fd = 0.07, 0.10
    box(mb, F, ua, ua + fw, 0.5, signY0, 0.0, fd, 1, 0, mcol, 'FTL')          # jambs
    box(mb, F, ub - fw, ub, 0.5, signY0, 0.0, fd, 1, 0, mcol, 'FTL')
    box(mb, F, ua, ub, signY0 - 0.08, signY0, 0.0, fd, 1, 0, mcol, 'FDU')     # head
    box(mb, F, ua - 0.04, ub + 0.04, 0.45, 0.6, 0.0, 0.2, 0, 2, tuple(c * 0.9 for c in (0.06, 0.06, 0.065)), 'FTLU')  # sill / bulkhead cap
    gw = ub - ua; nm = max(1, int(math.floor(gw / 1.8 + 0.5))); mw = gw / nm
    box(mb, F, ua, ub, signY0 - 0.95, signY0 - 0.88, 0.0, 0.08, 1, 0, mcol, 'FUD')  # transom
    for k in range(1, nm):
        u = ua + k * mw
        box(mb, F, u - 0.03, u + 0.03, 0.6, signY0 - 0.08, 0.0, 0.07, 1, 0, mcol, 'FTL')
    if wdoor:  # a door leaf at one end of the opening
        dw = 0.95; left = rnd < 0.5
        d0 = ua + 0.07 if left else ub - 0.07 - dw; d1 = d0 + dw; top = min(2.25, signY0 - 0.95)
        for (a, b) in ((d0, d0 + 0.09), (d1 - 0.09, d1)): box(mb, F, a, b, 0.5, top, 0.0, 0.13, 1, 0, mcol, 'FTL')
        box(mb, F, d0, d1, top - 0.1, top, 0.0, 0.13, 1, 0, mcol, 'FUD')
        box(mb, F, d0, d1, 0.5, 0.84, 0.0, 0.13, 1, 0, tuple(c * 1.6 for c in mcol), 'FTL')          # kick plate
        hx = d1 - 0.16 if left else d0 + 0.16
        box(mb, F, hx - 0.015, hx + 0.015, 0.95, 1.5, 0.11, 0.17, 1, 3, METAL[3], 'FTL')            # pull bar

def sign_board(mb, F, ua, ub, y0, y1, idx, flip):
    """fascia board in front of the wall; the text reads left to right for a viewer facing the wall"""
    uv = atlas_fascia(idx, (ub - ua) / (y1 - y0))
    if flip:  # T points to the viewer's left
        uv = [uv[1], uv[0], uv[3], uv[2]]
    box(mb, F, ua, ub, y0, y1, 0.0, 0.09, 1, 0, (0.02, 0.02, 0.022), 'TLUD')
    P = F.p
    mb.quad([P(ua, y0, 0.091), P(ub, y0, 0.091), P(ub, y1, 0.091), P(ua, y1, 0.091)], F.n3, 3, 0, (1, 1, 1), uv, [(ua, y0), (ub, y0), (ub, y1), (ua, y1)])
    # thin metal border
    for (a, b, c, d) in ((ua, ub, y1 - 0.03, y1), (ua, ub, y0, y0 + 0.03)): box(mb, F, a, b, c, d, 0.0, 0.1, 1, 0, (0.03, 0.03, 0.03), 'FU')

def awning_fabric(mb, F, ua, ub, yt, rnd, vidx, col, stripes, flip, dark_text):
    P = F.p; n3 = F.n3
    out = 1.35 + 0.45 * rnd; drop = 0.62 + 0.18 * rnd; vh = 0.4
    yb = yt - drop; W = ub - ua
    # top (slope) and underside
    slope_n = np.cross(P(ub, yb, out) - P(ua, yb, out), P(ua, yt, 0.0) - P(ua, yb, out)); slope_n /= np.linalg.norm(slope_n)
    if slope_n[1] < 0: slope_n = -slope_n
    uvs = [(ua * max(stripes, 0.001), 0), (ub * max(stripes, 0.001), 0), (ub * max(stripes, 0.001), 1), (ua * max(stripes, 0.001), 1)]
    mb.quad([P(ua, yb, out), P(ub, yb, out), P(ub, yt, 0.03), P(ua, yt, 0.03)], slope_n, 2, stripes, col, uvs, [(ua, 0), (ub, 0), (ub, out), (ua, out)])
    ug = tuple(c * 0.45 for c in col)
    mb.quad([P(ua, yb - 0.02, out - 0.03), P(ub, yb - 0.02, out - 0.03), P(ub, yt - 0.04, 0.03), P(ua, yt - 0.04, 0.03)], -slope_n, 2, 0, ug, None, [(ua, 0), (ub, 0), (ub, out), (ua, out)])
    # valance with lettering
    uv = atlas_valance(vidx)
    if flip: uv = [uv[1], uv[0], uv[3], uv[2]]
    mb.quad([P(ua, yb - vh, out), P(ub, yb - vh, out), P(ub, yb, out), P(ua, yb, out)], n3, 3, 2 if dark_text else 1, col, uv, [(ua, 0), (ub, 0), (ub, 1), (ua, 1)])
    for u in (ua, ub):  # side cheeks
        sgn = 1.0 if u == ub else -1.0
        mb.quad([P(u, yt - 0.04, 0.03), P(u, yb - vh, out), P(u, yb, out), P(u, yt, 0.03)], sgn * F.t3, 2, 0, ug)
    # frame rods
    for u in (ua + 0.05, ub - 0.05):
        box(mb, F, u - 0.012, u + 0.012, yb - vh + 0.02, yb - vh + 0.05, 0.0, out - 0.03, 1, 0, (0.02, 0.02, 0.02), 'F')

def marquee(mb, F, ua, ub, yt, vidx, col, flip, dark_text):
    out = 1.25
    box(mb, F, ua, ub, yt - 0.42, yt - 0.3, 0.0, out, 1, 0, METAL[3] if col is None else col, 'FTLUD')
    P = F.p; uv = atlas_valance(vidx)
    if flip: uv = [uv[1], uv[0], uv[3], uv[2]]
    mb.quad([P(ua, yt - 0.3, out + 0.001), P(ub, yt - 0.3, out + 0.001), P(ub, yt - 0.02, out + 0.001), P(ua, yt - 0.02, out + 0.001)], F.n3, 3, 2 if dark_text else 1, (0.04, 0.04, 0.045), uv, [(ua, 0), (ub, 0), (ub, 1), (ua, 1)])
    box(mb, F, ua, ub, yt - 0.3, yt - 0.02, 0.0, out, 1, 0, (0.03, 0.03, 0.035), 'BU')
    for u in (ua + 0.1, ub - 0.1):  # hanger rods
        box(mb, F, u - 0.012, u + 0.012, yt - 0.02, yt + 0.5, 0.0, 0.03, 1, 0, (0.03, 0.03, 0.03), 'FTL')

# ------------------------------------------------------------------ fire escape
FE_COLS = [(0.05, 0.046, 0.042), (0.025, 0.07, 0.04), (0.14, 0.065, 0.035), (0.2, 0.2, 0.2), (0.06, 0.06, 0.07)]  # black, dark green, rust, silver, blue-grey
GRATE_COL = FE_COLS[0]
def rect_minus(r, h):
    """(island r04) axis rectangle r = (u0, u1, n0, n1) minus the hole h (same frame) -> up to 4 rectangles (left / right strips, back / front)"""
    u0, u1, n0, n1 = r; a0, a1, b0, b1 = max(h[0], u0), min(h[1], u1), max(h[2], n0), min(h[3], n1)
    if a1 <= a0 or b1 <= b0: return [r]
    out = [(u0, a0, n0, n1), (a1, u1, n0, n1), (a0, a1, n0, b0), (a0, a1, b1, n1)]
    return [q for q in out if q[1] - q[0] > 0.02 and q[3] - q[2] > 0.02]

FE_SOLID = os.environ.get('SM2_FE_SOLID', '1') == '1'   # (island r04) 0 = diagnostic: the whole fire escape visual-only (in the street-kit tile)
FE_GAP = float(os.environ.get('SM2_FE_GAP', '0.40'))   # (island r04) wall-side edge of the landing grating = of its collision (m from the facade; r03: 0.02). The 0.38 m slot along the wall keeps the landings out of the wall-run's top-out probe (r3: 0 top-outs at the r03 loop spot; 0.02 gave 3)
FE_WELL_LEN, FE_WELL_N = 1.5, (0.25, 0.95)   # (island r04) stair well: the arriving flight's last 1.5 m (head room ~2 m under the deck), over the flight's width
FE_LADDER_HOLE = 0.30                          # (island r04) drop-ladder hatch: +-0.30 m along the wall around the ladder, n 0.10 .. 0.60

def fire_escape(mb, F, uc, w, y_first, y_top, fh, seed, GRATE_COL=FE_COLS[0], vis=None, stats=None):
    """fire escape on face frame F, centred at uc. (island r04, critic r03 'make fire-escape collision match the drawn platforms, with a top-out'):
    mb = the fire-escape tile (a traversal SOLID with its own triangles): ONLY the landings: grating top / underside + frame beams, with an
    open stair well (where the flight from the level below comes up) and an open drop-ladder hatch in the lowest landing;
    vis = the street-kit tile (visual-only, `streetkit` is on the traversal's exclusion list): railings, brackets, stair flights, ladders.
    Up to r03 everything was in the solid tile: the 1.05 m railing planes were walls and the hero topped out from the railing into the
    landing above (r3 crosstown east: 6 top-outs at x -235.5 m from t = 2.4 s). The space above every landing is now clear of solids up to
    the next landing, the front frame beam is the lip."""
    vis = vis if vis is not None else mb
    P = F.p; n3, t3 = F.n3, F.t3; up = np.array([0, 1.0, 0])
    depth = 1.15; u0, u1 = uc - w / 2, uc + w / 2
    levels = []
    y = y_first
    while y <= y_top - 0.5: levels.append(y); y += fh
    if not levels: return 0
    ul = u1 - 0.35   # drop / roof ladder line
    for i, y in enumerate(levels):
        # landing grating (top + underside) with its wells, frame beams (front lip + two sides): the SOLID part
        holes = []
        if i > 0:   # well of the flight arriving from level i - 1 (it ends at its sb, see below)
            sb = (u1 - 0.2) if ((i - 1) % 2 == 0) else (u0 + 0.2)
            holes.append((sb - FE_WELL_LEN, sb, FE_WELL_N[0], FE_WELL_N[1]) if (i - 1) % 2 == 0 else (sb, sb + FE_WELL_LEN, FE_WELL_N[0], FE_WELL_N[1]))
        else:       # drop-ladder hatch
            holes.append((ul - FE_LADDER_HOLE, ul + FE_LADDER_HOLE, 0.10, 0.60))
        rects = [(u0 + 0.05, u1 - 0.05, FE_GAP, depth - 0.06)]
        for h in holes: rects = [q for r in rects for q in rect_minus(r, h)]
        for (a0, a1, b0, b1) in rects:
            mb.quad([P(a0, y, b0), P(a1, y, b0), P(a1, y, b1), P(a0, y, b1)], up, 4, 0, GRATE_COL, [(a0 - u0, b0), (a1 - u0, b0), (a1 - u0, b1), (a0 - u0, b1)], [(a0 - u0, b0), (a1 - u0, b0), (a1 - u0, b1), (a0 - u0, b1)])
            mb.quad([P(a0, y - 0.03, b0), P(a0, y - 0.03, b1), P(a1, y - 0.03, b1), P(a1, y - 0.03, b0)], -up, 4, 0, GRATE_COL, [(a0 - u0, b0), (a0 - u0, b1), (a1 - u0, b1), (a1 - u0, b0)])
        for h in holes:   # well rim (inner edge faces of the grating, 3 cm)
            a0, a1, b0, b1 = h
            for (pa, pb, nn) in (((a0, b0), (a1, b0), -n3), ((a1, b1), (a0, b1), n3), ((a0, b1), (a0, b0), -t3), ((a1, b0), (a1, b1), t3)):
                mb.quad([P(pa[0], y - 0.03, pa[1]), P(pb[0], y - 0.03, pb[1]), P(pb[0], y, pb[1]), P(pa[0], y, pa[1])], -nn, 1, 4, GRATE_COL)
        box(mb, F, u0, u1, y - 0.08, y, depth - 0.06, depth, 1, 4, GRATE_COL, 'FTLUD')
        box(mb, F, u0, u0 + 0.05, y - 0.08, y, FE_GAP, depth - 0.06, 1, 4, GRATE_COL, 'FTUD')
        box(mb, F, u1 - 0.05, u1, y - 0.08, y, FE_GAP, depth - 0.06, 1, 4, GRATE_COL, 'FLUD')
        if FE_GAP > 0.05:   # wall-side rail of the landing frame (the grating hangs from it on the brackets), and the wall angle the brackets bolt to: visual only
            box(vis, F, u0, u1, y - 0.08, y, FE_GAP - 0.05, FE_GAP, 1, 4, GRATE_COL, 'FBUD')
            box(vis, F, u0, u1, y - 0.12, y - 0.02, 0.0, 0.04, 1, 4, GRATE_COL, 'FUD')
        if stats is not None: stats['fe_landings'] = stats.get('fe_landings', 0) + 1; stats['fe_wells'] = stats.get('fe_wells', 0) + len(holes)
        # railing planes (front + two sides), masked bars: visual only (the hero vaults / lands over them)
        rh = 1.05
        vis.quad([P(u0, y, depth), P(u1, y, depth), P(u1, y + rh, depth), P(u0, y + rh, depth)], n3, 5, 0, GRATE_COL, [(0, 0), (w, 0), (w, 1), (0, 1)], [(0, 0), (w, 0), (w, rh), (0, rh)])
        vis.quad([P(u0, y, depth), P(u0, y, 0.02), P(u0, y + rh, 0.02), P(u0, y + rh, depth)], -t3, 5, 0, GRATE_COL, [(0, 0), (depth, 0), (depth, 1), (0, 1)])
        vis.quad([P(u1, y, 0.02), P(u1, y, depth), P(u1, y + rh, depth), P(u1, y + rh, 0.02)], t3, 5, 0, GRATE_COL, [(0, 0), (depth, 0), (depth, 1), (0, 1)])
        # brackets under the platform
        for u in (u0 + 0.15, u1 - 0.15):
            vis.quad([P(u - 0.02, y - 0.08, 0.02), P(u - 0.02, y - 0.08, depth * 0.9), P(u - 0.02, y - 0.7, 0.02), P(u - 0.02, y - 0.7, 0.05)], -t3, 1, 0, GRATE_COL)
            vis.quad([P(u + 0.02, y - 0.08, depth * 0.9), P(u + 0.02, y - 0.08, 0.02), P(u + 0.02, y - 0.7, 0.05), P(u + 0.02, y - 0.7, 0.02)], t3, 1, 0, GRATE_COL)
        # stair flight to the level above (alternating side), running along the wall: visual only
        if i + 1 < len(levels):
            yn = levels[i + 1]; left = (i % 2 == 0)
            sa, sb = (u0 + 0.2, u1 - 0.2) if left else (u1 - 0.2, u0 + 0.2)   # start (low) -> end (high)
            n0, n1 = FE_WELL_N
            vis.quad([P(sa, y, n0), P(sa, y, n1), P(sb, yn, n1), P(sb, yn, n0)], up, 4, 0, GRATE_COL, [(0, 0), (0.7, 0), (0.7, 3.2), (0, 3.2)], [(0, 0), (0.7, 0), (0.7, 3.2), (0, 3.2)])
            for nn in (n0, n1):  # stringers
                vis.quad([P(sa, y - 0.12, nn), P(sb, yn - 0.12, nn), P(sb, yn + 0.02, nn), P(sa, y + 0.02, nn)], t3 if nn == n1 else -t3, 1, 0, GRATE_COL)
            # sloped rail on the open (street) side
            vis.quad([P(sa, y, n1), P(sb, yn, n1), P(sb, yn + 1.0, n1), P(sa, y + 1.0, n1)], n3, 5, 0, GRATE_COL, [(0, 0), (abs(sb - sa), 0), (abs(sb - sa), 1), (0, 1)])
    # drop ladder from the lowest platform to ~2.4 m above the pavement (through the hatch)
    y0 = levels[0]; yl = 2.6  # (r05) drop ladder to 2.6 m; build_kit aligns it with a pier (0.9 m gap between neighbouring awnings / boards)
    vis.quad([P(ul - 0.22, yl, 0.35), P(ul + 0.22, yl, 0.35), P(ul + 0.22, y0 + 1.0, 0.35), P(ul - 0.22, y0 + 1.0, 0.35)], n3, 6, 0, GRATE_COL, [(0, 0), (0.44, 0), (0.44, y0 + 1.0 - yl), (0, y0 + 1.0 - yl)])
    vis.quad([P(ul + 0.22, yl, 0.35), P(ul - 0.22, yl, 0.35), P(ul - 0.22, y0 + 1.0, 0.35), P(ul + 0.22, y0 + 1.0, 0.35)], -n3, 6, 0, GRATE_COL, [(0, 0), (0.44, 0), (0.44, y0 + 1.0 - yl), (0, y0 + 1.0 - yl)])
    # roof ladder above the highest platform
    yt = levels[-1]; vis.quad([P(ul - 0.22, yt, 0.35), P(ul + 0.22, yt, 0.35), P(ul + 0.22, yt + 1.6, 0.35), P(ul - 0.22, yt + 1.6, 0.35)], n3, 6, 0, GRATE_COL, [(0, 0), (0.44, 0), (0.44, 1.6), (0, 1.6)])
    return len(levels)

# ------------------------------------------------------------------ main
def main():
    faces = load_faces(EXP)
    man = json.load(open(EXP + 'manifest.json'))
    centers = {tuple(r['tile']): r['center'] for r in man['meshes'] if r['name'] == 'facade'}
    # existing browser signage (awnings, canopies, marquees, blade / wall signs) low on the walls: those bays are skipped for awnings / boards
    sig_pts = []
    for r in man['meshes']:
        if r['kind'] != 'signage': continue
        g = read_glb(EXP + r['file']); A = g['attrs']; P = A['POSITION'] + np.array([r['center'][0], 0.0, r['center'][2]])
        K = np.rint(A['TEXCOORD_1'][:, 0]) if 'TEXCOORD_1' in A else np.zeros(len(P))
        m = (P[:, 1] > 1.8) & (P[:, 1] < 9.0) & ((K == 7) | (K == 6))  # awning / canopy fabric and marquee bulbs only
        sig_pts.append(P[m])
    sig_pts = np.concatenate(sig_pts) if sig_pts else np.zeros((0, 3))
    elements = []  # element centres for the census (tools/export/crop_census.py)
    builders, fe_builders, stats = {}, {}, {'faces': 0, 'bays': 0, 'awnings': 0, 'marquees': 0, 'boards': 0, 'doors': 0, 'fire_escapes': 0, 'skipped_bays_existing_signage': 0, 'fire_escape_faces': []}
    for fi, f in enumerate(faces):
        F = Frame(f); gH = f['gH']; W = f['W']; seed = f['seed']; style = int(round(f['style'])); kind = f['kind']
        tile = tuple(f['tile']); cx, cz = centers[tile][0], centers[tile][2]
        mb = builders.setdefault(tile, MB(cx, cz))
        fmb = fe_builders.setdefault(tile, MB(cx, cz))   # (island r02) fire escapes: their own kit tile (a traversal solid, see main())
        modern = style == 2
        r = hrand(seed, 1); si = int(r * len(STONE)) if kind in ('loft', 'walkup') else (int(r * 4) if not modern else 2)
        if kind in ('loft', 'walkup') and hrand(seed, 2) < 0.6: si = 4  # mostly brick on the pre-war blocks
        scol, sparam = STONE[si % len(STONE)], STONE_PARAM[si % len(STONE)]
        mcol = METAL[int(hrand(seed, 3) * len(METAL))]
        nb = max(1, int(math.floor(W / 6.5 + 0.5))); bw = W / nb
        signY0, signY1 = gH - 1.55, gH - 0.55
        # right direction check for text orientation
        right = np.cross(-F.n3, np.array([0, 1.0, 0]))
        flip = float(np.dot(F.t3, right)) < 0
        # bays occupied by existing signage
        occupied = set()
        if len(sig_pts):
            d = sig_pts - np.array([F.O[0], 0, F.O[1]])
            u = d[:, 0] * F.T[0] + d[:, 2] * F.T[1]; n = d[:, 0] * F.N[0] + d[:, 2] * F.N[1]
            m = (np.abs(n) < 3.0) & (u > -0.5) & (u < W + 0.5) & (n > -0.2) & (d[:, 1] < gH + 3.0)
            for uu in u[m]: occupied.add(int(min(nb - 1, max(0, math.floor(uu / bw)))))
        stats['faces'] += 1; stats['bays'] += nb
        if not modern:
            for i in range(nb + 1): pier(mb, F, i * bw, gH, scol, sparam)
        else:
            for i in range(nb + 1):
                box(mb, F, i * bw - 0.09, i * bw + 0.09, 0.0, gH - 0.32, 0.0, 0.16, 1, 0, mcol, 'FTL')
        cornice(mb, F, 0.0, W, gH, scol, sparam, modern)
        for i in range(nb):
            ua, ub = i * bw + 0.35, (i + 1) * bw - 0.35
            rnd = fh1(i + seed * 13.1, seed * 7.7 + W)
            shutter = rnd >= 0.78
            door = (not shutter) and hrand(seed, i, 5) < 0.4
            if not shutter:
                storefront_frame(mb, F, ua, ub, signY0, mcol, hrand(seed, i, 6), door)
                stats['doors'] += int(door)
            occ = i in occupied
            stats['skipped_bays_existing_signage'] += int(occ)
            fidx = int(hrand(seed, i, 7) * 31) % 31
            sign_board(mb, F, ua + 0.02, ub - 0.02, signY0 + 0.05, signY1 - 0.05, fidx, flip)
            stats['boards'] += 1; elements.append(['board', *[round(float(v), 2) for v in F.p((ua + ub) / 2, (signY0 + signY1) / 2, 0.1)]])
            if not occ:
                if not shutter:
                    ra = hrand(seed, i, 8)
                    vidx = int(hrand(seed, i, 9) * 48) % 48
                    if modern or ra < 0.22:
                        marquee(mb, F, ua + 0.1, ub - 0.1, signY0 - 0.02, vidx, tuple(c * 1.0 for c in mcol), flip, False); stats['marquees'] += 1; elements.append(['marquee', *[round(float(v), 2) for v in F.p((ua + ub) / 2, signY0 - 0.3, 0.6)]])
                    elif ra < 0.78:
                        ac = AWN[int(hrand(seed, i, 10) * len(AWN))]
                        stripes = 2.4 if hrand(seed, i, 11) < 0.55 else 0.0
                        light = (ac[0] + ac[1] + ac[2]) / 3 < 0.2
                        awning_fabric(mb, F, ua + 0.1, ub - 0.1, signY0 - 0.02, hrand(seed, i, 12), vidx, ac, stripes, flip, not light); stats['awnings'] += 1; elements.append(['awning', *[round(float(v), 2) for v in F.p((ua + ub) / 2, signY0 - 0.4, 0.7)]])
        # fire escapes
        prewar = kind in ('loft', 'walkup', 'other')
        side = abs(F.N[1]) > 0.5
        p_fe = (0.9 if prewar else (0.95 if (side and style in (1, 4)) else (0.85 if style == 4 else 0.0)))
        if p_fe > 0 and hrand(seed, 20) < p_fe and W > 8.0:
            fh = 3.7; nfe = 1 if W < 22 else 2
            for k in range(nfe):
                uc = W * ((0.3 + 0.4 * hrand(seed, 21 + k)) if nfe == 1 else (0.22 + 0.56 * k + 0.02 * hrand(seed, 30 + k)))
                if nb >= 2:  # align the drop ladder (uc + 1.3) with the nearest pier
                    kp = min(nb - 1, max(1, int(round((uc + 1.3) / bw)))); uc = kp * bw - 1.3
                ytop = min(f['h'] - 1.0, 48.0 if prewar else 30.0)
                fe_col = FE_COLS[int(hrand(seed, 40) * len(FE_COLS)) % len(FE_COLS)] if hrand(seed, 41) < 0.6 else FE_COLS[0]
                n = fire_escape(fmb if FE_SOLID else mb, F, uc, 3.3, gH + 0.7, ytop, fh, seed, fe_col, vis=mb, stats=stats)   # (island r04) platforms solid, the rest visual-only
                if n: elements.append(['fire_escape', *[round(float(v), 2) for v in F.p(uc, gH + 0.7 + fh * n / 2.0, 0.6)]]); stats['fire_escapes'] += 1; stats['fire_escape_faces'].append([round(F.O[0] + F.T[0] * uc, 1), round(F.O[1] + F.T[1] * uc, 1), kind, n])
    out = EXP + 'mesh/streetkit/'; os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):   # (island r02) skip exFAT AppleDouble '._*' files (they vanish with their sibling)
        if f.endswith('.glb') and not f.startswith('._') and os.path.exists(out + f): os.remove(out + f)
    files = []
    for tile, mb in builders.items():
        if mb.n == 0: continue
        a, idx = mb.arrays(); name = f'streetkit__t{tile[0]}_{tile[1]}'
        write_glb(out + name + '.glb', a, idx, name)
        files.append({'file': f'mesh/streetkit/{name}.glb', 'name': name, 'tile': list(tile), 'center': [centers[tile][0], 0, centers[tile][2]], 'verts': int(mb.n), 'tris': int(len(idx) // 3)})
    # (island r02) fire escapes go to <export>/mesh/fireescape/fireescape__t<ix>_<iz>.glb (same vertex layout / material M_CityKit). The traversal
    # (WebTravWorld.cpp, round 20) makes every visible mesh a solid with its own triangles EXCEPT names on its exclusion list, which holds
    # 'streetkit': kit tiles stay visual-only (awnings / signs / boards are not floors), fire escapes become platforms the hero lands on.
    fout = EXP + 'mesh/fireescape/'; os.makedirs(fout, exist_ok=True)
    for f in os.listdir(fout):
        if f.endswith('.glb') and not f.startswith('._') and os.path.exists(fout + f): os.remove(fout + f)
    fe_files = []
    for tile, mb in fe_builders.items():
        if mb.n == 0: continue
        a, idx = mb.arrays(); name = f'fireescape__t{tile[0]}_{tile[1]}'
        write_glb(fout + name + '.glb', a, idx, name)
        fe_files.append({'file': f'mesh/fireescape/{name}.glb', 'name': name, 'tile': list(tile), 'center': [centers[tile][0], 0, centers[tile][2]], 'verts': int(mb.n), 'tris': int(len(idx) // 3)})
    json.dump({'files': files, 'fireescape_files': fe_files, 'stats': stats, 'elements': elements}, open(EXP + 'streetkit.json', 'w'), indent=1)
    print('fire-escape kit tiles', len(fe_files), 'tris', sum(f['tris'] for f in fe_files))
    print({k: v for k, v in stats.items() if k != 'fire_escape_faces'}, 'tris', sum(f['tris'] for f in files))

if __name__ == '__main__':
    main()

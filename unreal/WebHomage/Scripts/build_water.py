# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# River water (Hudson / East River around the island): idempotent, headless rebuild of /Game/Water on top of the integrated Manhattan build
# (Scripts/build_manhattan.py). Nothing here is committed as .uasset / .umap (unreal/WebHomage/CONTENT.md).
#
# Two modes in one file (same pattern as build_manhattan.py):
#   * plain python3 (YOUR editor closed; needs numpy + opencv, node):
#         python3 unreal/WebHomage/Scripts/build_water.py [--steps inputs,ue]
#       inputs   generated sources into $SM2_WATER_SCR (default /Users/midir/sm2-n1/_scratch/water):
#                  water_grid.glb   camera-centred polar grid, 384 segments x ~540 rings (0.1 m at the centre, +2 % per ring, 80 km radius)
#                  water_noise.png  4 tileable band-limited noise channels (gusts / slicks / streaks / foam cells / glitter facets)
#                  shore_dist.png   distance (m, 0..400 -> 0..255) from every water point to the nearest land, 8 m/px, from the browser's
#                                   own land polygons (tools/water/dump_shores.mjs: layout.js LAND_POLY + farshore.js FAR_LANDS)
#                  water_slope.png  (r02) tileable random-phase wind-sea slope spectrum, 2 realizations (tools/water/water_inputs.py)
#                  water_contact.png + .json  (r02) distance to the nearest place where the city export's geometry crosses the water plane
#                                   (seawalls, bulkheads, pier piles, bridge piers), island shore box, ~0.9 m/px; export = $SM2_WATER_EXPORT
#                                   (else $SM2_CITY_EXPORT / the Manhattan build's export)
#       ue       headless commandlet (-nullrhi) running this file inside Unreal
#   * inside Unreal (-run=pythonscript -script=<this file>):
#       /Game/Water/Textures/T_WaterNoise, T_ShoreDist, /Game/Water/Meshes/SM_WaterGrid
#       /Game/Water/Materials/M_RiverWater   Single Layer Water material:
#           vertex: the browser's 12 Gerstner waves (src/world/waves.js, same constants), evaluated at the camera-centred grid vertex
#                   (grid follows the camera through WPO; waves shorter than ~4 grid spacings fade out exactly like waves.js waveDisp)
#           pixel:  (r02) analytic slopes of the 5 longest waves + 4 layers of the baked wind-sea slope spectrum (rotated, scrolled at
#                   their phase speed; mip bias +1), filtered by the pixel footprint (resolved -> normal, unresolved slope variance ->
#                   roughness, Cox-Munk), facets whose reflection would point below the horizon bent up, wind gust / slick / streak fields,
#                   contact foam where the surface meets geometry crossing the water line (baked contact map + SceneDepthWithoutWater), sparse whitecaps,
#                   sun glitter facets (emissive, sun = SkyAtmosphere light 0), turbid-river optics as SLW scattering / absorption
#                   coefficients (olive-grey Hudson, siltier within ~100 m of the shore)
#       /Game/Water/Maps/Water_River        sublevel with the water actor (no shadows, not in Lumen scene / ray tracing, no collision)
#       P1's flat WaterPlane in /Game/Tests/City/City_Midtown_Geo is hidden (collision kept: it is still the traversal floor)
#       Water_River is added (always loaded) to /Game/Maps/Manhattan, _Midday, _Night, _View_S1|S2|S4
#       /Game/Water/Maps/Water_View_RiverLow[_Midday]   golden / midday + the low river camera (docs/night1/water/views.json)
#       /Game/Water/Maps/Water_View_RiverLow_Dolly      same camera on an InterpToMovement dolly (16 s, 2 m/s, at the view point at t = 6 s)
#       /Game/Water/Maps/Water_Perf_<RiverLow|S4|RiverSun>_Base  perf baseline: same view, P1's old flat water instead of this water
#       (r02) /Game/Water/Maps/Water_View_RiverSun[_Dolly], Water_View_HarbourHigh; /Game/Maps/Manhattan_WP (island piece) gets the water
#       actor directly (not spatially loaded); tuning variants: SM2_WATER_VARIANTS='{"A": {"ChopK": 1.4, "_views": ["river_sun"]}}' ->
#       /Game/Water/Variants/MI_Water_A + Water_Var_A_<view>. Material scalar parameters: PARAMS below (+ GlitterK, Dbg).
import os, sys, json, math, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '/Users/midir/sm2-n1/water-ab-opus/unreal/WebHomage/Scripts'
sys.path.insert(0, os.environ.get('SM2_SCRIPTS_DIR') or HERE)
import sm2_common
_B = sm2_common.Build('build_water.py')
PROJ = os.path.dirname(HERE)
WT = os.path.dirname(os.path.dirname(PROJ))
UPROJECT = os.path.join(PROJ, 'WebHomage.uproject')
UE = '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor'
SCR = os.environ.get('SM2_WATER_SCR', '/Users/midir/sm2-n1/_scratch/water')
VIEWS_JSON = os.path.join(WT, 'docs', 'night1', 'water', 'views.json')
STEPS_ALL = ['inputs', 'ue']
GPU_SLOT = '/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh'   # every Unreal launch goes through the GPU lock (RULES.md)

WATER_Y = -1.6                                  # browser G.WATER_Y (m)
SHORE_BOX = (-6400.0, -8000.0, 12800.0, 17600.0)  # x0, z0, w, h (browser metres; UE X = x, Y = z)
SHORE_PX = 8.0
GRID_SEG, GRID_R0, GRID_DR0, GRID_G, GRID_R1 = 384, 4.0, 0.1, 1.02, 80000.0

# ---------------------------------------------------------------------------------------------------- waves (src/world/waves.js)
GRAV = 9.81
# [wavelength m, amplitude m, direction deg (0 = +x, 90 = +z), steepness q, phase]   (wind toward the north-east: -50 deg)
SPEC = [
    [31.0, 0.06, -38, 0.2, 0.0], [16.5, 0.055, -62, 0.35, 5.1], [11.2, 0.065, -24, 0.45, 1.7], [7.9, 0.05, -83, 0.5, 4.1],
    [5.6, 0.042, -47, 0.55, 2.3], [4.3, 0.03, -2, 0.5, 3.9], [3.3, 0.026, -71, 0.55, 5.6], [2.45, 0.019, -28, 0.5, 0.9],
    [1.8, 0.014, -104, 0.45, 3.3], [1.33, 0.01, -52, 0.4, 6.0], [0.97, 0.0072, 8, 0.35, 2.0], [0.71, 0.005, -66, 0.3, 4.6],
]
def waves():
    out = []
    for L, A, dd, q, ph in SPEC:
        k = 2 * math.pi / L; d = math.radians(dd)
        out.append(dict(L=L, A=A, k=k, w=math.sqrt(GRAV * k), dx=math.cos(d), dy=math.sin(d), Q=q / (k * A * len(SPEC)), ph=ph))
    return out
WAVE_MAX = sum(w[1] for w in SPEC)
VAR_K = 1.2   # filtered slope variance -> GGX alpha^2 (Cox-Munk: alpha^2 ~ 2 sigma^2 per axis; 1.2 keeps the far river glossy)
# round 02: wind-sea slope spectrum layers (T_WaterSlope, tools/water/water_inputs.py) replace the 12 capillary sinusoids:
#   [tile size m, angle of realization A / B to the wind (deg), RMS slope per axis]   bands: tile/24 .. tile/3
# r03: the 0.73 m layer is replaced by the resolved wind-chop layer (CHOP); per-axis RMS slopes before ChopK
LAYERS = [(21.0, 8.0, -47.0, 0.040), (6.7, -19.0, 38.0, 0.045), (2.2, 27.0, -33.0, 0.050)]
# r03 wind chop (T_WaterChop, 3..10 cycles per tile): [tile m, angle to the wind deg, scroll speed factor] for the two realizations
# (two scroll directions); per-axis RMS slope CHOP_RMS * ChopK * MicroK, resolved (no roughness) within NEAR_M of the camera
CHOP = [(1.5, 28.0, 1.0), (1.17, -36.0, 1.13)]
CHOP_RMS = 0.065
NEAR_M = 150.0        # r03: near field (two realizations, chop layer, foam, contact map); beyond: one realization, no foam
PS_WAVE_MIN_L = 5.5   # analytic Gerstner slopes in the pixel shader: only the waves >= 5.5 m (the vertex geometry); shorter = spectrum layers
WIND_DEG = -50.0
SLOPE_ENC = 6.0       # water_inputs.SLOPE_ENC
CONTACT_MAX = 32.0    # water_inputs.CONTACT_MAX
WIND = (math.cos(math.radians(WIND_DEG)), math.sin(math.radians(WIND_DEG)))


# ================================================================================================ orchestrator (plain python3)
def log(*a):
    print('[build_water %s]' % time.strftime('%H:%M:%S'), *a, flush=True)


def step_inputs():
    import numpy as np, cv2
    sys.path.insert(0, os.path.join(WT, 'tools', 'export'))
    import glbio
    os.makedirs(SCR, exist_ok=True)
    # ---- polar grid (glTF: y up; x east, z south). Rings: uniform 0.1 m to 4 m, then +2 % per ring to 80 km.
    radii = [GRID_DR0 * j for j in range(1, int(round(GRID_R0 / GRID_DR0)) + 1)]
    while radii[-1] < GRID_R1: radii.append(radii[-1] * GRID_G)
    R = np.array(radii); th = np.arange(GRID_SEG) * 2 * math.pi / GRID_SEG
    P = np.zeros((1 + len(R) * GRID_SEG, 3))
    P[1:, 0] = (R[:, None] * np.cos(th)[None, :]).reshape(-1)
    P[1:, 2] = (R[:, None] * np.sin(th)[None, :]).reshape(-1)
    vid = lambda j, a: 1 + j * GRID_SEG + (a % GRID_SEG)
    tris = []
    a = np.arange(GRID_SEG)
    tris.append(np.stack([np.zeros(GRID_SEG, int), vid(0, a + 1), vid(0, a)], 1))  # centre fan
    for j in range(len(R) - 1):
        A_, B_, C_, D_ = vid(j, a), vid(j + 1, a), vid(j + 1, a + 1), vid(j, a + 1)
        tris.append(np.stack([A_, D_, B_], 1)); tris.append(np.stack([D_, C_, B_], 1))
    I = np.concatenate(tris)
    e1, e2 = P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]
    ny = np.cross(e1, e2)[:, 1]
    assert (ny > 0).all(), 'grid winding: %d faces point down' % int((ny <= 0).sum())
    N = np.zeros_like(P); N[:, 1] = 1.0
    UV = np.zeros((len(P), 2))
    glbio.write_glb(os.path.join(SCR, 'water_grid.glb'), {'POSITION': P, 'NORMAL': N, 'TEXCOORD_0': UV}, I.reshape(-1), name='SM_WaterGrid')
    log('grid: %d rings (r %.1f m .. %.0f m), %d verts, %d tris' % (len(R), R[0], R[-1], len(P), len(I)))
    # ---- tileable band-limited noise, 4 channels, ~N(0.5, 0.17) clipped to [0, 1]
    rng = np.random.default_rng(1729); S = 512
    fy, fx = np.meshgrid(np.fft.fftfreq(S) * S, np.fft.fftfreq(S) * S, indexing='ij'); f = np.hypot(fx, fy)
    chans = []
    for lo, hi in ((2, 16), (4, 32), (8, 64), (16, 128)):
        w = rng.standard_normal((S, S))
        band = ((f >= lo) & (f <= hi)) / np.maximum(f, 1)
        n = np.real(np.fft.ifft2(np.fft.fft2(w) * band)); n = (n - n.mean()) / n.std()
        chans.append(np.clip(0.5 + 0.17 * n, 0, 1))
    rgba = (np.stack(chans, -1) * 255 + 0.5).astype(np.uint8)
    cv2.imwrite(os.path.join(SCR, 'water_noise.png'), rgba[..., [2, 1, 0, 3]])  # cv2 writes BGRA
    # ---- shore distance map
    shores = os.path.join(SCR, 'shores.json')
    r = subprocess.run(['node', os.path.join(WT, 'tools', 'water', 'dump_shores.mjs'), shores], cwd=WT, capture_output=True, text=True)
    if r.returncode: raise SystemExit('dump_shores failed: ' + r.stderr[-800:])
    lands = json.load(open(shores))['lands']
    x0, z0, W, H = SHORE_BOX; nw, nh = int(W / SHORE_PX), int(H / SHORE_PX)
    land = np.zeros((nh, nw), np.uint8)
    for L in lands:
        pts = np.array([[(max(-1e5, min(1e5, x)) - x0) / SHORE_PX, (max(-1e5, min(1e5, z)) - z0) / SHORE_PX] for x, z in L['pts']])
        cv2.fillPoly(land, [np.round(pts * 16).astype(np.int32)], 255, lineType=cv2.LINE_8, shift=4)
    dist = cv2.distanceTransform((land == 0).astype(np.uint8), cv2.DIST_L2, 5) * SHORE_PX
    # r03: resampled to 2048^2 (power of two -> the texture gets mips; r02 sampled the NPOT map at level 0 = cache thrash at distance)
    sd = cv2.resize(np.clip(dist / 400.0 * 255 + 0.5, 0, 255).astype(np.float32), (2048, 2048), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(SCR, 'shore_dist.png'), np.clip(sd + 0.5, 0, 255).astype(np.uint8))
    log('shore map %dx%d (%.0f %% water), noise %dx%d' % (nw, nh, (land == 0).mean() * 100, S, S))
    # ---- round 02: wind-sea slope spectrum + contact-distance map (tools/water/water_inputs.py)
    sys.path.insert(0, os.path.join(WT, 'tools', 'water'))
    import water_inputs
    st = water_inputs.slope_texture(os.path.join(SCR, 'water_slope.png'))
    log('slope spectrum texture', st)
    log('wind-chop texture (r03)', water_inputs.chop_texture(os.path.join(SCR, 'water_chop.png')))
    exp = export_dir()
    cm = water_inputs.contact_map(exp, os.path.join(SCR, 'water_contact.png'))
    json.dump(dict(cm, export=exp), open(os.path.join(SCR, 'water_contact.json'), 'w'), indent=1)
    log('contact map from %s: box %s, %.2f m/px, %d segments, %d files' % (exp, [round(v, 1) for v in cm['box']], cm['px'], cm['segments'], len(cm['files'])))


def export_dir():
    """the city export whose geometry defines the contact (water line) map: $SM2_WATER_EXPORT, else the export the Manhattan build used"""
    for c in (os.environ.get('SM2_WATER_EXPORT'), os.environ.get('SM2_CITY_EXPORT'),
              os.path.join(os.environ.get('SM2_MANHATTAN_SCR', ''), 'export', 'midtown3x3') if os.environ.get('SM2_MANHATTAN_SCR') else None,
              os.path.join(SCR, 'manhattan', 'export', 'midtown3x3')):
        if c and os.path.exists(os.path.join(c, 'manifest.json')): return c
    raise SystemExit('no city export found for the contact map: set SM2_WATER_EXPORT=<export dir with manifest.json>')


def step_ue():
    if subprocess.run(['pgrep', '-f', UPROJECT], capture_output=True).returncode == 0:
        raise SystemExit('an Unreal process of this worktree is running; stop it first')
    n = 0
    while int(subprocess.run("pgrep -f '^%s( |$)' | wc -l" % UE, shell=True, capture_output=True, text=True).stdout.strip() or 0) >= 3:
        if n % 12 == 0: log('3+ Unreal instances running, waiting')
        n += 1; time.sleep(5)
    os.makedirs(os.path.join(SCR, 'logs'), exist_ok=True)
    # r02: start from an empty /Game/Water on disk. Rebuilding M_RiverWater in place (delete_all_material_expressions + new graph) compiled
    # in a fresh project but left a material that failed to compile for SF_METAL_SM6 on every later rebuild (default material in game).
    cw = os.path.realpath(os.path.join(PROJ, 'Content', 'Water'))
    if not cw.startswith(os.path.realpath(WT) + '/'): raise SystemExit('refusing to delete ' + cw)
    if os.path.isdir(cw):
        import shutil; shutil.rmtree(cw); log('removed', cw)
    lg = os.path.join(SCR, 'logs', 'water_ue.log')
    t0 = time.time()
    with open(lg + '.stdout', 'w') as so:
        r = subprocess.run([GPU_SLOT, 'capture', '--label', 'water', '--', UE, UPROJECT, '-run=pythonscript', '-script=' + os.path.abspath(__file__), '-unattended', '-nullrhi', '-nosplash',
                            '-RenderOffScreen', '-NoSound', '-NoCrashReports', '-abslog=' + lg], env={**os.environ, 'SM2_WATER_SCR': SCR},
                           stdout=so, stderr=subprocess.STDOUT, timeout=5400)
    txt = open(lg, errors='replace').read() if os.path.exists(lg) else ''
    bad = [l for l in txt.splitlines() if 'LogPython: Error' in l or 'Traceback' in l]
    for l in txt.splitlines():
        if '[water' in l: print(l.split('LogPython: ')[-1])
    log('UE commandlet: rc %d, %.0f s, %d python error lines (log %s)' % (r.returncode, time.time() - t0, len(bad), lg))
    if bad:
        print('\n'.join(bad[:40])); raise SystemExit('python error in the water build')


def main():
    import argparse
    ap = argparse.ArgumentParser(description='River water: /Game/Water on top of the Manhattan build (headless)')
    ap.add_argument('--steps', default=','.join(STEPS_ALL))
    a = ap.parse_args()
    for s in STEPS_ALL:
        if s in a.steps.split(','):
            log('=== step', s); globals()['step_' + s]()


# ================================================================================================ inside Unreal
def hlsl_vs():
    """WPO of the camera-centred grid: grid translation + Gerstner displacement (waves.js waveDisp); extra output Lag (m) -> vertex interpolator -> pixel shader"""
    c = ['float2 cam = Cam.xy * 0.01;', 'float2 rel = WPos.xy * 0.01;', 'float2 lag = rel + cam;',
         'float sp = max(%.3f, %.4f * length(rel));' % (GRID_DR0 * 0.8, GRID_G - 1.0), 'float3 o = 0; float s, c, a;']
    for w in waves():
        c.append('sincos(%.6f * dot(float2(%.6f, %.6f), lag) - %.6f * T + %.4f, s, c); a = %.6f * (1.0 - smoothstep(0.18, 0.3, sp / %.4f)); '
                 'o.xy += %.6f * a * float2(%.6f, %.6f) * c; o.z += a * s;' % (w['k'], w['dx'], w['dy'], w['w'], w['ph'], w['A'], w['L'], w['Q'], w['dx'], w['dy']))
    c += ['float3 h3 = frac(float3(rel.xyx) * 0.1031 * 7.31); h3 += dot(h3, h3.yzx + 33.33);', 'Lag = float3(lag, frac((h3.x + h3.y) * h3.z));', 'return float3((cam + o.xy) * 100.0, o.z * 100.0);']
    return '\n'.join(c)


def hlsl_ps():
    """round 03: the 5 longest Gerstner waves analytically (they match the vertex geometry) + 3 layers of the baked random-phase wind-sea slope
    spectrum (T_WaterSlope, 21 / 6.7 / 2.2 m tiles) + the resolved 0.15-0.5 m wind-chop layer (T_WaterChop, two realizations scrolling in two
    directions). Near field (<= NEAR_M): both realizations, the chop, contact / whitecap foam; textures sampled with their true gradients (no
    mip bias) and the BRDF roughness stays <= 0.08 (r02 turned mip-biased variance into roughness ~0.4 here: the flat look). Beyond NEAR_M:
    one realization per layer, no chop sample (its variance -> GGX roughness x FarVarK), no foam, no contact-map lookup (perf)."""
    CONTACT = json.load(open(os.path.join(SCR, 'water_contact.json')))
    W = [w for w in waves() if w['L'] >= PS_WAVE_MIN_L]
    big = '\n'.join('sincos(%.6f * dot(float2(%.6f, %.6f), p) - %.6f * t + %.4f, s, c); f = 1.0 - smoothstep(0.12, 0.35, foot * %.6f); '
                    'sl2 += float2(%.6f, %.6f) * (%.6f * c / max(1.0 - %.6f * s, 0.35)) * f; varU += %.8f * (1.0 - f); h += %.6f * s;'
                    % (w['k'], w['dx'], w['dy'], w['w'], w['ph'], w['k'] / math.pi, w['dx'], w['dy'], w['k'] * w['A'], w['Q'] * w['k'] * w['A'],
                       0.5 * (w['k'] * w['A']) ** 2, w['A']) for w in W)
    def rot(c, s_): return 'float2(%.6f, %.6f)' % (c, s_), 'float2(%.6f, %.6f)' % (-s_, c)
    lay = []
    for i, (sc, aA, aB, amp) in enumerate(LAYERS):
        lc = sc / 8.5
        kc = 2 * math.pi / lc
        spd = math.sqrt(GRAV / kc + 7.28e-5 * kc)
        tA, tB = math.radians(WIND_DEG + aA), math.radians(WIND_DEG + aB)
        cA, sA, cB, sB = math.cos(tA), math.sin(tA), math.cos(tB), math.sin(tB)
        sc2 = sc * 0.87
        uA, vA = rot(cA, sA); uB, vB = rot(cB, sB)
        lay.append(('{ float2 qa = float2(dot(p, %(uA)s), dot(p, %(vA)s)) / %(sc).4f - float2(%(va).6f * t, 0.0);\n'
                    '  float2 ga = (Texture2DSampleGrad(tW, tWSampler, qa, float2(dot(dpx, %(uA)s), dot(dpx, %(vA)s)) / %(sc).4f, float2(dot(dpy, %(uA)s), dot(dpy, %(vA)s)) / %(sc).4f).rg - 0.5) * %(enc).2f;\n'
                    '  ga = float2(ga.x * %(cA).6f - ga.y * %(sA).6f, ga.x * %(sA).6f + ga.y * %(cA).6f);\n'
                    '  float2 g = ga * waR;\n'
                    '  [branch] if (nearW > 0.0) {\n'
                    '    float2 qb = float2(dot(p, %(uB)s), dot(p, %(vB)s)) / %(sc2).4f - float2(%(vb).6f * t, 0.0) + float2(0.37, %(off).3f);\n'
                    '    float2 gb = (Texture2DSampleGrad(tW, tWSampler, qb, float2(dot(dpx, %(uB)s), dot(dpx, %(vB)s)) / %(sc2).4f, float2(dot(dpy, %(uB)s), dot(dpy, %(vB)s)) / %(sc2).4f).ba - 0.5) * %(enc).2f;\n'
                    '    g += float2(gb.x * %(cB).6f - gb.y * %(sB).6f, gb.x * %(sB).6f + gb.y * %(cB).6f) * wbR; }\n'
                    '  slT += g * %(amp).5f; varL += %(amp2).7f * saturate(log2(2.0 * foot / %(lmin).5f) / 3.0); }')
                   % dict(uA=uA, vA=vA, uB=uB, vB=vB, cA=cA, sA=sA, cB=cB, sB=sB, sc=sc, sc2=sc2, va=spd / sc, vb=spd * 1.07 / sc2, off=0.61 * (i + 1),
                          enc=SLOPE_ENC, amp=amp, amp2=amp * amp, lmin=sc2 / 24.0))
    chop = []
    for j, (sc, ang, vf) in enumerate(CHOP):
        lc = sc / 5.5; kc = 2 * math.pi / lc
        spd = math.sqrt(GRAV / kc + 7.28e-5 * kc) * vf
        th = math.radians(WIND_DEG + ang); c_, s_ = math.cos(th), math.sin(th); u, v = rot(c_, s_)
        ch = 'rg' if j == 0 else 'ba'
        chop.append(('{ float2 q = float2(dot(p, %(u)s), dot(p, %(v)s)) / %(sc).4f - float2(%(vv).6f * t, %(off).3f);\n'
                     '    float2 g = (Texture2DSampleGrad(tK, tKSampler, q, float2(dot(dpx, %(u)s), dot(dpx, %(v)s)) / %(sc).4f, float2(dot(dpy, %(u)s), dot(dpy, %(v)s)) / %(sc).4f).%(ch)s - 0.5) * %(enc).2f;\n'
                     '    slC += float2(g.x * %(c).6f - g.y * %(s).6f, g.x * %(s).6f + g.y * %(c).6f); lostC += 0.5 * saturate(log2(2.0 * foot / %(lmin).5f) / 1.74); }')
                    % dict(u=u, v=v, sc=sc, vv=spd / sc, off=0.29 * (j + 1), ch=ch, enc=SLOPE_ENC, c=c_, s=s_, lmin=sc / 10.0))
    return PS_TEMPLATE % dict(wx=WIND[0], wy=WIND[1], sx=SHORE_BOX[0], sz=SHORE_BOX[1], sw=SHORE_BOX[2], sh=SHORE_BOX[3], big=big, lay='\n'.join(lay),
                              chop='\n    '.join(chop), crms=CHOP_RMS, near=NEAR_M,
                              hmax=WAVE_MAX * 0.5, ss='%(SCAT)s', sa='%(ABS)s', cx=CONTACT['box'][0], cz=CONTACT['box'][1], cw=CONTACT['box'][2],
                              ch=CONTACT['box'][3], cmax=CONTACT_MAX)


PS_TEMPLATE = r'''
#define NZG(uv, s) Texture2DSampleGrad(tN, tNSampler, (uv), dpx * (s), dpy * (s))
float2 p = Lag.xy; float t = T;
float3 wp = WPos * 0.01, cm = Cam * 0.01;
float3 Vv = cm - wp; float dist = length(Vv); float3 V = Vv / max(dist, 1e-3);
float2 dpx = ddx(p), dpy = ddy(p);
float foot = max(length(abs(dpx) + abs(dpy)), 1e-4);
// r03: near field (<= %(near).0f m): two realizations per layer, the resolved wind chop, foam, contact map; beyond: one realization
float nearW = 1.0 - smoothstep(%(near).1f * 0.73, %(near).1f, dist);
float wbR = 0.70711 * nearW, waR = sqrt(1.0 - wbR * wbR);
// ---- wind gusts (broad, wind-aligned patches of rougher water). r03: wind-streak and slick terms deleted (pale comet streaks)
float2 wdir = float2(%(wx).6f, %(wy).6f);
float4 nA = NZG(p / 620.0, 1.0 / 620.0), nB = NZG(p / 230.0 + float2(t * 0.0009, 0.37), 1.0 / 230.0);
float gust = saturate((nA.r * 0.62 + nB.g * 0.38 - 0.5) * 2.4 + 0.5);
float2 su = (p - float2(%(sx).1f, %(sz).1f)) / float2(%(sw).1f, %(sh).1f);
float shore = (all(su > 0.0) && all(su < 1.0)) ? Texture2DSampleGrad(tS, tSSampler, su, dpx / float2(%(sw).1f, %(sh).1f), dpy / float2(%(sw).1f, %(sh).1f)).r * 400.0 : 400.0;
float gk = lerp(0.75, 1.25, gust);
// ---- the long Gerstner waves (waves.js waveSlope: resolved -> slope, unresolved -> slope variance)
float2 sl2 = 0; float varU = 0, h = 0, s, c, f;
%(big)s
float crest = h / %(hmax).5f;
sl2 *= lerp(0.85, 1.1, gust); varU *= 1.2;
// ---- wind-sea spectrum layers (baked random-phase slopes, true texture gradients: what the mips drop is counted in varL)
float2 slT = 0; float varL = 0;
%(lay)s
// ---- r03 resolved wind chop 0.15-0.5 m: two realizations, two scroll directions (near field only; beyond, all of it is sub-pixel variance)
float2 slC = 0; float lostC = 1.0;
[branch] if (nearW > 0.0) {
    lostC = 0.0;
    %(chop)s
    slC *= nearW * 0.70711;
    lostC = lerp(1.0, lostC, nearW);
}
float ck = ChopK * gk, mk = ChopK * MicroK * gk * %(crms).4f;
slT *= ck; varL *= ck * ck;
float2 slope = sl2 + slT + slC * mk;
float varF = varL + lostC * mk * mk;      // per-axis slope variance the shading cannot resolve
// ---- foam (near field only, faded to zero by %(near).0f m): contact (the water line against anything below it), rare whitecaps
float cf = 0.0, wf = 0.0;
[branch] if (nearW > 0.0) {
    float fn = NZG(p / 7.0 + float2(t * 0.01, -t * 0.007), 1.0 / 7.0).b;
    float lap = 0.55 + 0.225 * sin(dot(p, float2(0.11, -0.17)) + t * 1.1) + 0.35 * crest + 0.15 * (slT.x - slT.y);
    float dnw = max(DNW - PD, 0.0) * 0.01;
    float lr = dnw / max(dot(-V, View.ViewForward), 0.2);
    cf = 1.0 - smoothstep(0.04, 0.25 + 1.1 * fn + 0.6 * lap, lr);
    float2 cu = (p - float2(%(cx).2f, %(cz).2f)) / float2(%(cw).2f, %(ch).2f);
    float cdm = (all(cu > 0.0) && all(cu < 1.0)) ? Texture2DSampleLevel(tC, tCSampler, cu, 0).r * %(cmax).1f : %(cmax).1f;
    cf = max(cf, 1.0 - smoothstep(0.12, 0.45 + 1.5 * fn + 0.9 * lap, cdm));
    float foam = cf * (0.4 + 0.45 * lap) * smoothstep(0.25, 0.6, NZG(p / 3.1 + float2(-t * 0.02, t * 0.013), 1.0 / 3.1).r + 0.25 * lap) * FoamK;
    foam = max(foam, smoothstep(0.8, 1.0, crest) * smoothstep(0.55, 0.9, gust) * 0.2);
    float cov = saturate(foam);
    float pat = NZG(p / 1.9 + float2(t * 0.004, 0.0), 1.0 / 1.9).r * 0.62 + NZG(p / 0.63 + float2(0.0, t * 0.006), 1.0 / 0.63).g * 0.5;
    wf = saturate(smoothstep(1.05 - cov, 1.3 - cov, pat) * smoothstep(0.0, 0.25, cov)) * nearW;
}
// ---- normal / roughness. Near field: GGX alpha from RoughN only (<= 0.08: the resolved facets carry the slope variance);
//      beyond: + the unresolved variance x FarVarK (Cox-Munk alpha^2 = 2 sigma^2 per axis)
float3 N = normalize(float3(-slope.x, -slope.y, 1.0));
{ float3 Rr = reflect(-V, N); float wl = saturate((0.05 - Rr.z) * 8.0); N = normalize(lerp(N, float3(0, 0, 1), wl * BendK));
  Rr = reflect(-V, N); wl = saturate((0.03 - Rr.z) * 12.0); N = normalize(lerp(N, float3(0, 0, 1), wl * BendK)); }
float farW = smoothstep(%(near).1f * 0.4, %(near).1f, dist);
float r4 = RoughN * RoughN; r4 *= r4;
float a2 = r4 + VARK * FarVarK * farW * (varU + 2.0 * varF);
float rcap = lerp(0.08, 0.7, smoothstep(%(near).1f, %(near).1f * 2.7, dist));
Rough = lerp(clamp(pow(a2, 0.25), 0.03, rcap), 0.6, wf);
NormalW = normalize(lerp(N, float3(0, 0, 1), wf * 0.6));
Spec = 0.25 * SpecK;     // F0 = 0.02 (IOR 1.333) x SpecK
Opac = wf * 0.92;
// ---- turbid river optics (per cm): olive-grey Hudson body (ScatK), siltier / browner along the bulkheads
float silt = (1.0 - smoothstep(10.0, 120.0, shore)) * 0.75;
float turb = 0.85 + 0.3 * NZG(p / 900.0 + float2(0.0, t * 0.0015), 1.0 / 900.0).r;
float3 sS = float3(%(ss)s) * ScatK * turb * (1.0 + float3(0.9, 0.6, 0.3) * silt);
float3 sA = float3(%(sa)s) * (1.0 + float3(0.1, 0.2, 0.5) * silt);
Scat = sS * 0.01; Abs = sA * 0.01;
// ---- sun glitter: sparse facets that face the sun get their normal tilted onto the sun half-vector (beyond 25 m; the near field glints
//      off its own resolved facets with the sharp GGX lobe)
float3 Ls = normalize(SunDir);
float3 Hh = normalize(Ls + V);
float gw = 0.0;
[branch] if (dist < 900.0 && dist > 20.0 && Ls.z > 0.0) {
    float2 gn = (NZG(p / 2.3 + float2(t * 0.05, t * 0.034), 1.0 / 2.3).ga - 0.5) * 2.0 + 0.8 * (NZG(float2(-p.y, p.x) / 3.7 + float2(-t * 0.041, t * 0.02), 1.0 / 3.7).ga - 0.5) * 2.0;
    float3 nG = normalize(N + float3(gn * 0.22, 0.0));
    float gl = pow(saturate(dot(nG, Hh)), 700.0);
    float spark = smoothstep(0.62, 0.9, NZG(p / 5.0 + float2(t * 0.02, 0.0), 1.0 / 5.0).r);
    gw = saturate(gl * spark * (1.0 - smoothstep(600.0, 900.0, dist)) * smoothstep(20.0, 40.0, dist) * (1.0 - wf) * saturate(Ls.z * 8.0) * 3.0 * GlitterK);
}
NormalW = normalize(lerp(NormalW, Hh, gw));
Rough = lerp(Rough, 0.06, gw);
Emis = 0;
if (Dbg > 0.5) { float3 dv = Dbg < 1.5 ? float3(frac(p / 10.0), 0.0) : (Dbg < 2.5 ? N * 0.5 + 0.5 : (Dbg < 3.5 ? Rough.xxx : (Dbg < 4.5 ? float3(wf, cf, gust) : Lag.zzz))); Emis = 0; Opac = 1.0; return dv; }
return float3(0.62, 0.6, 0.55);   // r03: cream foam albedo (r02 0.74 clipped at the seawall in the golden key)
#undef NZG
'''


# body optics per metre (tuned against CITY-SPEC C14 and the refs; see docs/night1/water/HANDOFF.md)
SCAT = (0.07, 0.09, 0.078)
ABS = (0.50, 0.34, 0.56)
PHASE_G = 0.55
GLITTER = 0.5
# material scalar parameters (round 02 look; variants for tuning: SM2_WATER_VARIANTS, see build_in_unreal)
WP_MAPS = ('/Game/Maps/Manhattan_WP',)   # island piece's World Partition map(s), if built in this project
# r03 start (CPU emulation of the river_low near crop against the round-02 frame, see docs/night1/water/round-03/NOTES.md): dark body
# (ScatK 0.06: the body radiance set the r02 trough floor p1 46), steeper resolved chop, F0 x1.6 (SpecK) for the sky / mist reflections
# round-03 captures: autopick variant V3 (lowest penalty on the 1080p iteration stills, docs/night1/water/round-03/iter/autopick.json)
PARAMS = {'ChopK': 2.6, 'MicroK': 2.0, 'ScatK': 0.04, 'FarVarK': 0.1, 'FoamK': 1.8, 'BendK': 0.3, 'RoughN': 0.06, 'SpecK': 2.0}
if os.environ.get('SM2_WATER_PARAMS'): PARAMS.update(json.loads(os.environ['SM2_WATER_PARAMS']))


def build_in_unreal():
    import unreal
    EAL = unreal.EditorAssetLibrary
    at = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    T0 = time.time()
    WARN = []
    def wlog(*a): print('[water %5.0fs]' % (time.time() - T0), *a)
    ROOT = '/Game/Water'
    CITY_GEO = '/Game/Tests/City/City_Midtown_Geo'
    BOXES = '/Game/Look/Look_Boxes'
    RIG = '/Game/Look/Rigs/Look_Rig_%s'
    ACTORS = '/Game/Maps/Manhattan_Actors'
    LEVEL = ROOT + '/Maps/Water_River'
    views = json.load(open(VIEWS_JSON))
    for need in (CITY_GEO, BOXES, RIG % 'golden', RIG % 'midday'):
        if not EAL.does_asset_exist(need): raise RuntimeError('missing %s: run build_manhattan.py first' % need)
    KEEP = ('WorldSettings', 'Brush', 'DefaultPhysicsVolume', 'GameplayDebuggerCategoryReplicator', 'WorldDataLayers', 'WorldPartitionMiniMap')
    if sms is None:  # commandlet: the subsystem needs its module
        unreal.SystemLibrary.execute_console_command(None, 'Module Load StaticMeshEditor'); sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

    def load(p): return unreal.load_asset(p)

    def open_level(path):
        if EAL.does_asset_exist(path):
            unreal.EditorLoadingAndSavingUtils.load_map(path)
            for a in eas.get_all_level_actors():
                if a.get_class().get_name() not in KEEP and a.get_path_name().startswith(path + '.'): eas.destroy_actor(a)
        else:
            les.new_level(path)
        return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    def import_files(files, dest, options=None):
        tasks = []
        for f in files:
            t = unreal.AssetImportTask(); t.filename = f; t.destination_path = dest; t.automated = True; t.replace_existing = True; t.save = False
            if options: t.options = options
            tasks.append(t)
        at.import_asset_tasks(tasks)

    # ---------------------------------------------------------------- textures
    # imported in place under their final names (re-import replaces the asset; no rename / delete of referenced assets)
    import shutil
    stage = os.path.join(SCR, 'ue_import'); os.makedirs(stage, exist_ok=True)
    TEXS = (('water_noise.png', 'T_WaterNoise'), ('shore_dist.png', 'T_ShoreDist'), ('water_slope.png', 'T_WaterSlope'), ('water_contact.png', 'T_WaterContact'),
            ('water_chop.png', 'T_WaterChop'))
    for src, name in TEXS + (('water_grid.glb', 'SM_WaterGrid'),):
        shutil.copyfile(os.path.join(SCR, src), os.path.join(stage, name + os.path.splitext(src)[1]))
    import_files([os.path.join(stage, n + '.png') for _, n in TEXS], ROOT + '/Textures')
    for _, name in TEXS:
        tx = load(f'{ROOT}/Textures/{name}')
        tx.set_editor_property('srgb', False)
        vec = name in ('T_WaterNoise', 'T_WaterSlope', 'T_WaterChop')
        tx.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_VECTOR_DISPLACEMENTMAP if vec else unreal.TextureCompressionSettings.TC_GRAYSCALE)
        if not vec:
            tx.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP); tx.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
        if name == 'T_WaterContact':   # non-power-of-two distance map, sampled at level 0 only
            tx.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        EAL.save_asset(f'{ROOT}/Textures/{name}')
    wlog('textures')

    # ---------------------------------------------------------------- grid mesh
    p = unreal.InterchangeGenericAssetsPipeline()
    p.common_meshes_properties.set_editor_properties({'recompute_normals': False, 'recompute_tangents': False, 'use_full_precision_u_vs': True,
                                                      'remove_degenerates': False})
    p.mesh_pipeline.set_editor_properties({'generate_lightmap_u_vs': False, 'build_nanite': False})
    try: p.mesh_pipeline.set_editor_property('collision', False)
    except Exception as e: WARN.append('pipeline collision flag: %s' % str(e)[:80])
    p.material_pipeline.set_editor_property('import_materials', False)
    p.material_pipeline.texture_pipeline.set_editor_property('import_textures', False)
    import_files([os.path.join(stage, 'SM_WaterGrid.glb')], ROOT + '/Meshes', p)
    dst = ROOT + '/Meshes/SM_WaterGrid/StaticMeshes/SM_WaterGrid'   # Interchange glTF layout <dest>/<file>/StaticMeshes/<mesh>
    if not EAL.does_asset_exist(dst):
        found = [x.split('.')[0] for x in EAL.list_assets(ROOT + '/Meshes', recursive=True) if isinstance(load(x.split('.')[0]), unreal.StaticMesh)]
        raise RuntimeError('grid import: %s missing, found %s' % (dst, found))
    sm = load(dst)
    bs = sms.get_lod_build_settings(sm, 0)
    for k, v in (('use_full_precision_u_vs', True), ('generate_lightmap_u_vs', False), ('recompute_normals', False), ('recompute_tangents', False),
                 ('distance_field_resolution_scale', 0.0)):
        try: bs.set_editor_property(k, v)
        except Exception as e: WARN.append('build setting %s: %s' % (k, str(e)[:60]))
    sms.set_lod_build_settings(sm, 0, bs)
    try: sms.remove_collisions(sm)
    except Exception as e: WARN.append('remove_collisions: %s' % str(e)[:80])
    EAL.save_asset(dst, only_if_is_dirty=False)
    bb = sm.get_bounding_box()
    wlog('grid mesh', dst, 'verts', sm.get_num_vertices(0), 'tris', sm.get_num_triangles(0), 'bounds', bb.min, bb.max)

    # ---------------------------------------------------------------- material
    MATP = ROOT + '/Materials/M_RiverWater'
    if EAL.does_asset_exist(MATP):
        m = load(MATP); mel.delete_all_material_expressions(m)
    else:
        m = at.create_asset('M_RiverWater', ROOT + '/Materials', unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_SINGLE_LAYER_WATER)
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_OPAQUE)
    m.set_editor_property('tangent_space_normal', False)
    m.set_editor_property('two_sided', False)
    MP = unreal.MaterialProperty
    def expr(cls, x, y, **props):
        e = mel.create_material_expression(m, cls, x, y)
        for k, v in props.items(): e.set_editor_property(k, v)
        return e
    def custom(name, code, inputs, outputs, x, y):
        c = expr(unreal.MaterialExpressionCustom, x, y)
        c.set_editor_property('code', code); c.set_editor_property('description', name)
        c.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        ins = []
        for n, _ in inputs:
            ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
        c.set_editor_property('inputs', ins)
        T = {1: unreal.CustomMaterialOutputType.CMOT_FLOAT1, 2: unreal.CustomMaterialOutputType.CMOT_FLOAT2, 3: unreal.CustomMaterialOutputType.CMOT_FLOAT3}
        outs = []
        for n, k in outputs:
            co = unreal.CustomOutput(); co.set_editor_property('output_name', n); co.set_editor_property('output_type', T[k]); outs.append(co)
        c.set_editor_property('additional_outputs', outs)
        for n, e in inputs: mel.connect_material_expressions(e, '', c, n)
        return c
    wpos_vs = expr(unreal.MaterialExpressionWorldPosition, -1400, -400)
    cam = expr(unreal.MaterialExpressionCameraPositionWS, -1400, -300)
    tim = expr(unreal.MaterialExpressionTime, -1400, -200)
    vs = custom('WaterVS', hlsl_vs(), [('WPos', wpos_vs), ('Cam', cam), ('T', tim)], [('Lag', 3)], -900, -400)
    mel.connect_material_property(vs, '', MP.MP_WORLD_POSITION_OFFSET)
    # Lag (m) travels vertex -> pixel through a vertex interpolator (the Python API does not expose the CustomizedUV material pins)
    vi = expr(unreal.MaterialExpressionVertexInterpolator, -600, -250)
    if not (mel.connect_material_expressions(vs, 'Lag', vi, 'VS') or mel.connect_material_expressions(vs, 'Lag', vi, '')): raise RuntimeError('interpolator not connected')
    wpos_ps = expr(unreal.MaterialExpressionWorldPosition, -1400, 100)
    try: wpos_ps.set_editor_property('world_position_shader_offset', unreal.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    except Exception: pass
    cam2 = expr(unreal.MaterialExpressionCameraPositionWS, -1400, 200)
    tim2 = expr(unreal.MaterialExpressionTime, -1400, 300)
    tN = expr(unreal.MaterialExpressionTextureObject, -1400, 400, texture=load(ROOT + '/Textures/T_WaterNoise'), sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    tS = expr(unreal.MaterialExpressionTextureObject, -1400, 500, texture=load(ROOT + '/Textures/T_ShoreDist'), sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
    sund = expr(unreal.MaterialExpressionSkyAtmosphereLightDirection, -1400, 600, light_index=0)
    sune = expr(unreal.MaterialExpressionSkyAtmosphereLightIlluminance, -1400, 700, light_index=0)
    dnw = expr(unreal.MaterialExpressionSceneDepthWithoutWater, -1400, 800)
    try: dnw.set_editor_property('fallback_depth', 1.0e7)
    except Exception as e: WARN.append('fallback_depth: %s' % str(e)[:60])
    pd = expr(unreal.MaterialExpressionPixelDepth, -1400, 900)
    gk = expr(unreal.MaterialExpressionScalarParameter, -1400, 1000, parameter_name='GlitterK', default_value=GLITTER)
    tW = expr(unreal.MaterialExpressionTextureObject, -1600, 400, texture=load(ROOT + '/Textures/T_WaterSlope'), sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    tC = expr(unreal.MaterialExpressionTextureObject, -1600, 500, texture=load(ROOT + '/Textures/T_WaterContact'), sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
    tK = expr(unreal.MaterialExpressionTextureObject, -1600, 300, texture=load(ROOT + '/Textures/T_WaterChop'), sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    prm = {k: expr(unreal.MaterialExpressionScalarParameter, -1600, 600 + 100 * i, parameter_name=k, default_value=float(v)) for i, (k, v) in enumerate(PARAMS.items())}
    dbg = expr(unreal.MaterialExpressionScalarParameter, -1400, 1100, parameter_name='Dbg', default_value=float(os.environ.get('SM2_WATER_DBG', '0')))
    dbgk = expr(unreal.MaterialExpressionScalarParameter, -1400, 1200, parameter_name='DbgK', default_value=float(os.environ.get('SM2_WATER_DBGK', '3000')))
    code = hlsl_ps().replace('VARK', '%.3f' % VAR_K) % dict(SCAT='%.4f, %.4f, %.4f' % SCAT, ABS='%.4f, %.4f, %.4f' % ABS)
    ps = custom('WaterPS', code, [('Lag', vi), ('WPos', wpos_ps), ('Cam', cam2), ('T', tim2), ('tN', tN), ('tS', tS), ('SunDir', sund), ('SunE', sune),
                                  ('DNW', dnw), ('PD', pd), ('GlitterK', gk), ('Dbg', dbg), ('DbgK', dbgk), ('tW', tW), ('tC', tC), ('tK', tK)] + list(prm.items()),
                [('NormalW', 3), ('Rough', 1), ('Opac', 1), ('Emis', 3), ('Spec', 1), ('Scat', 3), ('Abs', 3)], -900, 200)
    for out, prop in (('', MP.MP_BASE_COLOR), ('NormalW', MP.MP_NORMAL), ('Rough', MP.MP_ROUGHNESS), ('Opac', MP.MP_OPACITY), ('Emis', MP.MP_EMISSIVE_COLOR),
                      ('Spec', MP.MP_SPECULAR)):
        mel.connect_material_property(ps, out, prop)
    slw = expr(unreal.MaterialExpressionSingleLayerWaterMaterialOutput, -300, 600)
    phase = expr(unreal.MaterialExpressionConstant, -600, 750, r=PHASE_G)
    ins = [str(n) for n in mel.get_material_expression_input_names(slw)] if hasattr(mel, 'get_material_expression_input_names') else []
    def slw_in(want):
        for n in ins:
            if n.replace(' ', '').lower() == want.replace(' ', '').lower(): return n
        return want
    for src_e, out, want in ((ps, 'Scat', 'Scattering Coefficients'), (ps, 'Abs', 'Absorption Coefficients'), (phase, '', 'Phase G')):
        if not mel.connect_material_expressions(src_e, out, slw, slw_in(want)): WARN.append('SLW input %s not connected (inputs %s)' % (want, ins))
    mel.recompile_material(m)
    EAL.save_asset(MATP)
    wlog('material', MATP, 'SLW inputs', ins)

    # ---------------------------------------------------------------- water sublevel
    def water_actor(label='RiverWater', material=None):
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, WATER_Y * 100.0), unreal.Rotator(0, 0, 0))
        a.set_actor_label(label); a.set_folder_path('Water')
        c = a.static_mesh_component
        c.set_editor_property('mobility', unreal.ComponentMobility.STATIC)
        c.set_static_mesh(sm); c.set_material(0, material or m)
        for k, v in (('cast_shadow', False), ('affect_distance_field_lighting', False), ('affect_dynamic_indirect_lighting', False),
                     ('affect_indirect_lighting_while_hidden', False), ('visible_in_ray_tracing', False), ('visible_in_reflection_captures', False),
                     ('visible_in_real_time_sky_captures', False), ('receives_decals', False), ('bounds_scale', 1.5), ('can_ever_affect_navigation', False)):
            try: c.set_editor_property(k, v)
            except Exception as e: WARN.append('%s.%s: %s' % (label, k, str(e)[:60]))
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        return a
    open_level(LEVEL); water_actor()
    unreal.EditorLoadingAndSavingUtils.save_map(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(), LEVEL)
    wlog('level', LEVEL)

    # ---------------------------------------------------------------- P1 flat water plane: hidden (collision kept)
    unreal.EditorLoadingAndSavingUtils.load_map(CITY_GEO)
    n = 0
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == 'WaterPlane':
            a.static_mesh_component.set_visibility(False, False); a.set_actor_hidden_in_game(True); n += 1
    unreal.EditorLoadingAndSavingUtils.save_map(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(), CITY_GEO)
    if n != 1: _B.fail('WaterPlane actors hidden in %s: %d (expected 1)' % (CITY_GEO, n))
    wlog('P1 WaterPlane hidden:', n)

    # ---------------------------------------------------------------- Manhattan maps get the water sublevel
    def add_sublevels(world, levels):
        have = [l.get_path_name() for l in unreal.EditorLevelUtils.get_levels(world)]
        for lp in levels:
            nm = lp.split('/')[-1]
            if not any((nm + '.') in h or h.endswith(nm) or ('/' + nm + ':') in h for h in have):
                unreal.EditorLevelUtils.add_level_to_world(world, lp, unreal.LevelStreamingAlwaysLoaded)
        les.set_current_level_by_name(str(world.get_name()))
    for mp in ('/Game/Maps/Manhattan', '/Game/Maps/Manhattan_Midday', '/Game/Maps/Manhattan_Night', '/Game/Maps/Manhattan_View_S1',
               '/Game/Maps/Manhattan_View_S2', '/Game/Maps/Manhattan_View_S4'):
        if not EAL.does_asset_exist(mp): WARN.append('missing map ' + mp); continue
        unreal.EditorLoadingAndSavingUtils.load_map(mp)
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        add_sublevels(w, [LEVEL])
        unreal.EditorLoadingAndSavingUtils.save_map(w, mp)
        wlog('water added to', mp)

    # ---------------------------------------------------------------- view / perf maps
    def cam_actor(v, label):
        loc = unreal.Vector(*v['ue_cm'])
        ca = eas.spawn_actor_from_class(unreal.CameraActor, loc, unreal.Rotator(roll=0.0, pitch=v['pitch'], yaw=v['yaw']))
        ca.set_actor_label(label)
        ca.camera_component.set_editor_property('field_of_view', v['hfov'])
        ca.camera_component.set_editor_property('constrain_aspect_ratio', False)
        ca.set_editor_property('auto_activate_for_player', unreal.AutoReceiveInput.PLAYER0)
        return ca
    def view_map(path, rig, v, water=True, dolly=None, mat=None):
        world = open_level(path)
        add_sublevels(world, [CITY_GEO, BOXES, RIG % rig, ACTORS] + ([LEVEL] if water and mat is None else []))
        if mat is not None: water_actor('RiverWater_Variant', mat)   # tuning variant: its own water actor with a material instance
        if not water:  # perf baseline: P1's previous flat water (M_CityWater plane at G.WATER_Y), as the city had it before this piece
            g = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, WATER_Y * 100.0), unreal.Rotator(0, 0, 0))
            g.set_actor_label('BaselineWaterPlane')
            g.static_mesh_component.set_static_mesh(load('/Engine/BasicShapes/Plane')); g.set_actor_scale3d(unreal.Vector(60000, 60000, 1))
            g.static_mesh_component.set_material(0, load('/Game/City/Materials/M_CityWater'))
        if dolly:
            yaw = math.radians(v['yaw']); d = (math.cos(yaw), math.sin(yaw))
            start = [v['ue_cm'][0] - d[0] * dolly['pre_m'] * 100, v['ue_cm'][1] - d[1] * dolly['pre_m'] * 100, v['ue_cm'][2]]
            ca = cam_actor(dict(v, ue_cm=start), 'DollyCam')
            ca.root_component.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
            root = sds.k2_gather_subobject_data_for_instance(ca)[0]
            hnd, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.InterpToMovementComponent, blueprint_context=None))
            mv = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(hnd))
            L = (dolly['pre_m'] + dolly['post_m']) * 100
            pts = []
            # InterpToMovement rotates EVERY control point by the actor rotation (UE 5.8 InterpToMovementComponent.cpp:280), relative or not:
            # give it the world offset un-rotated by the camera rotation (yaw + pitch -3 deg), relative to the start -> a level, straight dolly
            P_, Y_ = math.radians(v['pitch']), math.radians(v['yaw'])
            Fw = (math.cos(P_) * math.cos(Y_), math.cos(P_) * math.sin(Y_), math.sin(P_)); Rt = (-math.sin(Y_), math.cos(Y_), 0.0)
            Up = (-math.sin(P_) * math.cos(Y_), -math.sin(P_) * math.sin(Y_), math.cos(P_))
            unrot = lambda w: unreal.Vector(sum(a * b for a, b in zip(w, Fw)), sum(a * b for a, b in zip(w, Rt)), sum(a * b for a, b in zip(w, Up)))
            for s_ in (0.0, 1.0):
                cp = unreal.InterpControlPoint()
                cp.set_editor_property('position_control_point', unrot((d[0] * L * s_, d[1] * L * s_, 0.0)))
                cp.set_editor_property('position_is_relative', True); pts.append(cp)
            mv.set_editor_property('control_points', pts)
            mv.set_editor_property('duration', float(dolly['duration_s']))
            mv.set_editor_property('behaviour_type', unreal.InterpToBehaviourType.ONE_SHOT)
            try: mv.finalise_control_points()
            except Exception as e: WARN.append('finalise_control_points: %s' % str(e)[:60])
        else:
            cam_actor(v, 'ShotCam_' + v['id'])
        ok = unreal.EditorLoadingAndSavingUtils.save_map(world, path)
        wlog('map', path, rig, 'water' if water else 'BASELINE', 'saved' if ok else 'SAVE FAILED')
    rl, s4 = views['river_low'], views['S4_perch_skyline']
    view_map(ROOT + '/Maps/Water_View_RiverLow', 'golden', rl)
    view_map(ROOT + '/Maps/Water_View_RiverLow_Midday', 'midday', rl)
    view_map(ROOT + '/Maps/Water_View_S4_Midday', 'midday', s4)
    view_map(ROOT + '/Maps/Water_View_RiverLow_Dolly', 'golden', rl, dolly=views['river_low_dolly'])
    view_map(ROOT + '/Maps/Water_Perf_RiverLow_Base', 'golden', rl, water=False)
    view_map(ROOT + '/Maps/Water_Perf_S4_Base', 'golden', s4, water=False)
    view_map(ROOT + '/Maps/Water_Perf_S4', 'golden', s4)   # = Manhattan_View_S4 with the same camera construction as the baseline
    rs = views['river_sun']
    view_map(ROOT + '/Maps/Water_View_RiverSun', 'golden', rs)
    view_map(ROOT + '/Maps/Water_View_RiverSun_Dolly', 'golden', rs, dolly=views['river_sun_dolly'])
    view_map(ROOT + '/Maps/Water_View_HarbourHigh', 'golden', views['harbour_high'])
    view_map(ROOT + '/Maps/Water_Perf_RiverSun_Base', 'golden', rs, water=False)
    # ---------------------------------------------------------------- tuning variants (SM2_WATER_VARIANTS = {"name": {param: value}, ...})
    var = json.loads(os.environ.get('SM2_WATER_VARIANTS') or '{}')
    if EAL.does_directory_exist(ROOT + '/Variants'): EAL.delete_directory(ROOT + '/Variants')
    for vn, pv in var.items():
        mi = at.create_asset('MI_Water_' + vn, ROOT + '/Variants', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property('parent', m)
        for k, val in pv.items():
            if k.startswith('_'): continue
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, k, float(val))
        EAL.save_asset(mi.get_path_name().split('.')[0])
        for key in pv.get('_views', ['river_low', 'river_sun', 'S4_perch_skyline']):
            view_map(ROOT + '/Variants/Water_Var_%s_%s' % (vn, key), 'golden', views[key], mat=mi)
    # ---------------------------------------------------------------- World Partition Manhattan (island piece): the water actor goes straight
    # into the persistent WP level, not spatially loaded (a classic sublevel cannot be added to a WP map)
    for mp in WP_MAPS:
        if not EAL.does_asset_exist(mp): continue
        try:
            unreal.EditorLoadingAndSavingUtils.load_map(mp)
            for a in eas.get_all_level_actors():
                if a.get_actor_label() in ('RiverWater', 'RiverWater_WP'): eas.destroy_actor(a)
            hid = 0
            for a in eas.get_all_level_actors():
                if a.get_actor_label() == 'WaterPlane':
                    a.static_mesh_component.set_visibility(False, False); a.set_actor_hidden_in_game(True); hid += 1
            wa = water_actor('RiverWater_WP')
            try: wa.set_editor_property('is_spatially_loaded', False)
            except Exception as e: _B.fail('WP is_spatially_loaded', e)
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
            wlog('water added to WP map', mp, '(flat WaterPlane actors hidden: %d)' % hid)
            if hid == 0: WARN.append('%s: no loaded WaterPlane actor hidden (hide or drop the flat plane in the city build when /Game/Water exists)' % mp)
        except Exception as e:
            _B.fail('WP map ' + mp, e)
    if WARN:
        wlog('WARNINGS (%d):' % len(WARN))
        for w in WARN: print('    ', w)
    wlog('DONE')
    if not EAL.does_asset_exist(LEVEL): _B.fail('missing ' + LEVEL)
    _B.finish()


try:
    import unreal  # noqa: F401
    IN_UE = hasattr(unreal, 'EditorAssetLibrary')
except ImportError:
    IN_UE = False

if IN_UE:
    build_in_unreal()
elif __name__ == '__main__':
    main()

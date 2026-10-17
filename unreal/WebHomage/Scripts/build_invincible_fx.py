# Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation. See DISCLAIMER.md.
# Invincible flight conversion, round 3 (critic r2: breaches, sonic boom and craters looked fake).
# Round 7 (critic r6 #4 / #8): M_BreachHole now draws a recessed interior (reveal + room), M_InvShockRing a hard bright leading edge,
# and M_InvGlassShard (glass-tower debris panes) is new. See the asset list below.
#
# Headless UE Python asset builder (run it inside a -nullrhi commandlet, like import_invincible_hero.py / build_characters.py):
#     UnrealEditor <project> -run=pythonscript -script=<this file> -unattended -nullrhi -NoSound ...   (through the GPU slot guard)
# Idempotent: every asset below is created when missing, or its expression graph is cleared and rebuilt in place when it exists. It only
# touches /Game/Invincible/FX/ (it never deletes anything outside that folder). Any failure raises; the last line printed on success is
#     SM2_BUILD_OK: build_invincible_fx.py
#
# Assets created (all Materials, domain / blend as noted; parameters in brackets, defaults after '='):
#   M_BreachHole   deferred decal (translucent decal blend). Procedural JAGGED opening (a ragged star, analytic outline shared with the
#                  director's rim chunks: WHBreachDirector.cpp BdHoleRadius) with a RECESSED INTERIOR (r7, critic r6 #8 "crack decals, no interior"):
#                  the view ray is traced into the wall -- a lit concrete / steel reveal (wall thickness, Glass = 1 -> a thin curtain-wall edge),
#                  then a virtual room (floor, ceiling with light panels, side and back walls, desks, monitor glow; stacked floors by world
#                  height) drawn dark and exposure-independent through the emissive output. Outside the opening: broken concrete rim, radial
#                  cracks and a soot smear fading out before the decal box edge. The decal frame comes from the director (Centre, AxU, AxV, AxN,
#                  HalfCm) so the shader and the C++ rim chunks share one coordinate system; no UV or normal output depends on UE's decal UV.
#                  [Seed=0.37, Open=1 (0 -> 1 grows the opening), RimCol=(0.30, 0.28, 0.25), Centre=(0,0,0) cm, AxU=(0,1,0), AxV=(0,0,1),
#                   AxN=(-1,0,0), HalfCm=400, Glass=0 (0 masonry .. 1 curtain wall)]
#   M_CraterDecal  deferred decal. Scorched near-black centre, a fractured-slab band (grid cracks) around it, 14 long radial cracks +
#                  27 hairlines, a soft soot halo; opacity fades to 0 before the box edge. Same outputs (+ a bowl / crack normal).
#                  [Seed=0.61, Open=1, Bump=0.10, RimCol=(0.085, 0.082, 0.078)]
#   M_InvVapour    translucent, UNLIT, two-sided. White vapour with a fresnel-bright edge (face-on is nearly clear, grazing is opaque), noise
#                  turbulence that travels with the object (world position - object position + time); opacity = the Opacity parameter.
#                  Used for the sonic-boom cone / rings and the ground shock ring.
#                  [Color=(0.92, 0.95, 1.0), Opacity=1, EdgePow=1.6, Gain=1.2, Soft=0.7, NearFade=60, NearFadeLen=220 (r5: opacity fades to 0 near the lens)]
#   M_InvDust      translucent LIT (surface lighting), two-sided. A dust puff for a sphere: soft round silhouette (opacity falls to 0 at the
#                  rim), eroded lumpy interior from noise; denser and more opaque than the combat FX puffs.
#                  [Color=(0.34, 0.31, 0.27), Opacity=0.7, Emissive=0.12, Soft=1, Seed=0.5, NearFade=40, NearFadeLen=200]
#   M_InvChunk     opaque LIT. Broken concrete (per-face tint, crevices, aggregate specks, chipped edges, AO) or brick courses with mortar
#                  (Brick >= 0.5), in the piece's own frame (LocalPosition x Size; r6, critic r5 #8 "untextured grey cubes").
#                  [Color=(0.40, 0.38, 0.35), Rough=0.9, Brick=0, Seed=0.5, Size=(100, 100, 100) cm]
#   M_InvShockRing (critic r5 #8: the boom ring read as a bead chain; r7 / critic r6 #4: it read as a haze disc) translucent, UNLIT,
#                  two-sided. One flattened sphere = one ring: opacity is an annulus of the mesh radius (Band +- BandW) with a HARD, hot leading
#                  (outer) edge (emissive Gain + RimGain, exposure-independent), a short soft wake behind it and a CLEAR interior.
#                  [Color, Opacity=1, EdgePow=1.3, Gain=1.1, RimGain=3.2, Soft=0.3, Band=0.86, BandW=0.12, NearFade=60, NearFadeLen=220]
#   M_InvGlassShard (r7, critic r6 #8: a glass tower threw bricks) translucent UNLIT two-sided. A thin glass pane shard for a flat box:
#                  mostly clear face-on, bright at grazing angles, with a per-shard glint that flashes as it tumbles.
#                  [Color=(0.62, 0.78, 0.86), Opacity=0.8, Gain=1.0, NearFade=40, NearFadeLen=160]
#   M_InvStreak    (owner feedback 2026-10-15 #1, super-boost speed read) translucent ADDITIVE, UNLIT, two-sided. A speed line for a sphere
#                  stretched along Dir: bright on the centre line facing the camera, fading to the silhouette and to 0 at both ends along Dir
#                  (HalfLen cm), a little brighter at the front. Used for the world wind streaks, the charge's inward streaks, the body trail.
#                  [Dir=(1, 0, 0), HalfLen=500, Opacity=0.5, Color=(0.9, 0.93, 1.0), Gain=1.6, EdgePow=1 (unused), NearFade=80, NearFadeLen=250]
# The C++ side (Flight/WHBreachDirector.cpp) loads all of them optionally and falls back to the round-2 proxies when one is missing.
#
# Plain python3 (no Unreal): `python3 build_invincible_fx.py --dump-hlsl <dir>` writes the HLSL body of every Custom node to <dir>/*.hlsl
# (one file per node, first lines = inputs / output type) for review; it does not need an editor.
import os
import sys

try:
    import unreal
except ImportError:
    unreal = None

DEST = '/Game/Invincible/FX'
SCRIPT = 'build_invincible_fx.py'


# ====================================================================================================== HLSL generation (pure python)
# Custom-node code is a function BODY: no function / macro definitions, scalar-heavy, no reversed smoothstep edges (undefined in MSL),
# no HLSL-reserved identifiers as variable names, no divisions by zero. Every Custom node ends in a return of its declared output type.
FBM_T = """
float @V@ = 0.0; float @V@_a = 0.5; float @V@_x = (@PX@) * @F@; float @V@_y = (@PY@) * @F@;
for (int @V@_i = 0; @V@_i < @O@; @V@_i++)
{
  float @V@_ix = floor(@V@_x); float @V@_iy = floor(@V@_y);
  float @V@_ux = @V@_x - @V@_ix; float @V@_uy = @V@_y - @V@_iy;
  @V@_ux = @V@_ux * @V@_ux * (3.0 - 2.0 * @V@_ux); @V@_uy = @V@_uy * @V@_uy * (3.0 - 2.0 * @V@_uy);
  float @V@_h00 = frac(sin(@V@_ix * 12.9898 + @V@_iy * 78.233 + (@S@)) * 43758.5453);
  float @V@_h10 = frac(sin((@V@_ix + 1.0) * 12.9898 + @V@_iy * 78.233 + (@S@)) * 43758.5453);
  float @V@_h01 = frac(sin(@V@_ix * 12.9898 + (@V@_iy + 1.0) * 78.233 + (@S@)) * 43758.5453);
  float @V@_h11 = frac(sin((@V@_ix + 1.0) * 12.9898 + (@V@_iy + 1.0) * 78.233 + (@S@)) * 43758.5453);
  @V@ = @V@ + @V@_a * lerp(lerp(@V@_h00, @V@_h10, @V@_ux), lerp(@V@_h01, @V@_h11, @V@_ux), @V@_uy);
  @V@_x = @V@_x * 2.03 + 11.7; @V@_y = @V@_y * 2.03 + 5.3; @V@_a = @V@_a * 0.5;
}
@V@ = @V@ / @NORM@;
"""


def fbm(var, px, py, octaves, freq, seed):
    """HLSL text: value-noise fBm in [0, 1) into the scalar `var` at (px, py) * freq, `octaves` octaves, hash offset `seed`"""
    norm = '%.6f' % (1.0 - 0.5 ** octaves)
    return (FBM_T.replace('@V@', var).replace('@PX@', px).replace('@PY@', py).replace('@O@', str(octaves)).replace('@F@', '%.4f' % freq)
            .replace('@S@', seed).replace('@NORM@', norm))


def tpl(text, **kw):
    for k, v in kw.items():
        text = text.replace('@%s@' % k, v)
    return text


# ------------------------------------------------------------------------------------------------ the facade opening (breach hole)
# r7 (critic r6 #8: "breach holes are crack decals with no interior"): the opening is a ragged star in the facade plane whose analytic outline
# (pf below) is ALSO evaluated by the director in C++ (WHBreachDirector.cpp BdHoleRadius) to seat the lit broken-rim chunks on its edge, so the plane
# coordinates here come from the director's own frame (RP = world position - Centre, AU / AV = in-plane axes, HalfCm) and not from UE's decal UV.
HOLE_FIELD_T = """
float cx@T@ = @CX@;
float cy@T@ = @CY@;
float rr@T@ = sqrt(cx@T@ * cx@T@ + cy@T@ * cy@T@);
float th@T@ = atan2(cy@T@, cx@T@ + 0.00001);
@FBM_NW@
float tw1@T@ = abs(frac(th@T@ * 1.11408 + Seed * 0.713) - 0.5) * 2.0;
float tw2@T@ = abs(frac(th@T@ * 1.75070 + Seed * 0.377 + 0.31) - 0.5) * 2.0;
float tw3@T@ = abs(frac(th@T@ * 3.02394 + Seed * 0.911 + 0.57) - 0.5) * 2.0;
float pf@T@ = 0.58 + 0.17 * tw1@T@ + 0.10 * tw2@T@ + 0.07 * tw3@T@ + 0.09 * sin(th@T@ * 2.0 + Seed * 9.1) + 0.06 * sin(th@T@ * 3.0 + Seed * 4.3);
float rh@T@ = pf@T@ * 0.58 * (0.12 + 0.88 * grow);
float d@T@ = rr@T@ + (nw@T@ - 0.5) * 0.07 - rh@T@;
@FBM_NR@
"""


def hole_field(t, cx, cy):
    """HLSL text: the jagged opening's signed distance d<t> (< 0 inside; box units, the decal edge is 1) and the broken-concrete noise nr<t>
    at (cx, cy) in [-1, 1]. Needs Seed and grow. The outline is a ragged star: three triangle waves with integer tooth counts (7, 11, 19 -> periodic in
    the angle) + two low sines, warped by a 3-octave noise of +-0.035 (r7: was +-0.08, so the C++ rim chunks sit within ~14 cm of the edge)."""
    return (tpl(HOLE_FIELD_T, T=t, CX=cx, CY=cy,
                FBM_NW=fbm('nw' + t, 'cx' + t, 'cy' + t, 3, 3.1, 'Seed * 17.31'),
                FBM_NR=fbm('nr' + t, 'cx' + t, 'cy' + t, 4, 7.0, 'Seed * 5.77 + 3.0')))


HOLE_PRE = """
float op = saturate(Open);
float grow = 1.0 - (1.0 - op) * (1.0 - op);
"""

# the outline distance of the opening at another plane position (the back of the reveal): the same ragged star without the nr noise, scaled
# by SC (the opening narrows a little with depth) and with the surface pixel's warp reused
HOLE_LITE_T = """
float lx@T@ = @PX@;
float ly@T@ = @PY@;
float lr@T@ = sqrt(lx@T@ * lx@T@ + ly@T@ * ly@T@);
float lh@T@ = atan2(ly@T@, lx@T@ + 0.00001);
float l1@T@ = abs(frac(lh@T@ * 1.11408 + Seed * 0.713) - 0.5) * 2.0;
float l2@T@ = abs(frac(lh@T@ * 1.75070 + Seed * 0.377 + 0.31) - 0.5) * 2.0;
float l3@T@ = abs(frac(lh@T@ * 3.02394 + Seed * 0.911 + 0.57) - 0.5) * 2.0;
float lp@T@ = 0.58 + 0.17 * l1@T@ + 0.10 * l2@T@ + 0.07 * l3@T@ + 0.09 * sin(lh@T@ * 2.0 + Seed * 9.1) + 0.06 * sin(lh@T@ * 3.0 + Seed * 4.3);
float ld@T@ = lr@T@ + wob - lp@T@ * 0.58 * (0.12 + 0.88 * grow) * @SC@;
"""

# r7 interior: the view ray goes into the wall. Frame = (AU, AV, -AN): da / db / dcn are the unit ray's components along them (cm per cm).
# 1. REVEAL: across the wall thickness rvt the ray moves lateral (lsx, lsy); if it has left the (narrower) opening by then it hit the side wall of the
#    opening (lit concrete / steel, darker deeper in) at the fraction rvl of the thickness.
# 2. ROOM: else it enters a virtual room and meets the nearest of back wall, floor, ceiling, left / right wall; floors stack with world height (FH),
#    side walls every WW cm. Dark display-referred colours (the shader writes them as exposure-independent emissive), ceiling light panels,
#    a desk band and monitor glow on the back wall, daylight spill near the opening, falloff with distance.
HOLE_INTERIOR = """
float3 au = float3(AU.x, AU.y, AU.z);
float3 av = float3(AV.x, AV.y, AV.z);
float3 an = float3(AN.x, AN.y, AN.z);
float3 cvv = float3(CV.x, CV.y, CV.z);
float3 cc3 = float3(CC.x, CC.y, CC.z);
float rvt = lerp(28.0, 11.0, glassk);
float da = -dot(cvv, au);
float db = -dot(cvv, av);
float dcn = max(dot(cvv, an), 0.06);
float lsx = da / dcn * rvt;
float lsy = db / dcn * rvt;
float wob = (nw - 0.5) * 0.07;
@LITE_B@
float sidehit = smoothstep(-0.015, 0.015, ldb);
float rvl = saturate(-d / max(ldb - d, 0.0001));
float u1 = cx * Hh + lsx;
float v1 = cy * Hh + lsy;
float wz1 = cc3.z + au.z * u1 + av.z * v1 - an.z * rvt;
float avz = max(abs(av.z), 0.25);
float cellf = floor(wz1 / 380.0);
float vfl = v1 + (cellf * 380.0 - wz1) / avz;
float vce = vfl + 380.0 / avz;
float cellu = floor(u1 / 640.0);
float ulf = cellu * 640.0;
float urt = ulf + 640.0;
float tbk = max(620.0 - rvt, 10.0) / dcn;
float tfl = db < -0.0005 ? (vfl - v1) / db : 1000000.0;
float tce = db > 0.0005 ? (vce - v1) / db : 1000000.0;
float tlf = da < -0.0005 ? (ulf - u1) / da : 1000000.0;
float trt = da > 0.0005 ? (urt - u1) / da : 1000000.0;
float tmn = min(min(tbk, tfl), min(tce, min(tlf, trt)));
float hu = u1 + da * tmn;
float hv = v1 + db * tmn;
float hdp = rvt + dcn * tmn;
float kfl = tfl <= tmn ? 1.0 : 0.0;
float kce = (tce <= tmn && kfl < 0.5) ? 1.0 : 0.0;
float kbk = (tbk <= tmn && kfl + kce < 0.5) ? 1.0 : 0.0;
float ksd = saturate(1.0 - kfl - kce - kbk);
float roomh = frac(sin(cellf * 12.9898 + cellu * 78.233 + Seed * 3.7) * 43758.5453);
float pau = lerp(hu, hdp, ksd);
float tileh = frac(sin(floor(hu / 60.0) * 12.9898 + floor(hdp / 60.0) * 78.233 + roomh * 9.0) * 43758.5453);
float3 floorc = float3(0.050, 0.052, 0.060) * (0.65 + 0.7 * tileh);
float pnu = hu / 120.0;
float pnd = hdp / 160.0;
float pnon = step(0.35, frac(sin(floor(pnu) * 12.9898 + floor(pnd) * 78.233 + roomh * 17.0) * 43758.5453));
float pnl = (1.0 - smoothstep(0.30, 0.34, abs(frac(pnu) - 0.5))) * (1.0 - smoothstep(0.34, 0.38, abs(frac(pnd) - 0.5))) * pnon;
float tseam = 1.0 - 0.5 * smoothstep(0.46, 0.5, max(abs(frac(hu / 60.0) - 0.5), abs(frac(hdp / 60.0) - 0.5)));
float3 ceilc = float3(0.075, 0.078, 0.084) * tseam + float3(0.85, 0.92, 1.0) * 0.55 * pnl;
float hab = hv - vfl;
float desk = step(55.0, hab) * (1.0 - step(125.0, hab));
float monu = frac(hu / 170.0 + roomh);
float monl = step(0.08, monu) * (1.0 - step(0.30, monu)) * step(95.0, hab) * (1.0 - step(125.0, hab)) * step(0.45, frac(sin(floor(hu / 170.0 + roomh) * 12.9898 + cellf * 4.1) * 43758.5453));
float3 wallc = float3(0.055, 0.057, 0.062) * (0.75 + 0.5 * frac(sin(floor(pau / 90.0) * 12.9898 + roomh * 5.0) * 43758.5453)) * (1.0 + 0.9 * desk);
wallc = wallc * (1.0 - 0.35 * smoothstep(0.455, 0.5, abs(frac(pau / 120.0) - 0.5)));
wallc = wallc * (0.55 + 0.45 * smoothstep(0.0, 28.0, hab));
float3 roomc = floorc * kfl + ceilc * kce + wallc * (kbk + ksd);
roomc = roomc + float3(0.20, 0.36, 0.60) * 0.55 * monl * kbk;
float spill = 0.45 + 0.55 * exp(-hdp / 300.0);
roomc = roomc * exp(-tmn / 1500.0) * spill;
float3 revc = rc * (0.30 + 0.34 * lt) * (0.6 + 0.8 * nr) * (1.0 - 0.55 * rvl);
revc = lerp(revc, revc * 1.5, (1.0 - smoothstep(0.0, 0.12, rvl)) * 0.6);
float3 holeb = lerp(roomc * 0.2, revc, sidehit);
"""

HOLE_COLOR_POST = """
@FBM_NC@
@FBM_NS@
float glassk = saturate(Glass);
float inside = 1.0 - smoothstep(-0.012, 0.012, d);
float rimw = (0.12 + 0.10 * nr) * (1.0 - 0.6 * glassk);
float rima = (1.0 - smoothstep(rimw - 0.03, rimw + 0.01, d)) * (1.0 - inside);
rima = rima * smoothstep(0.28, 0.42, nr + (1.0 - smoothstep(0.0, rimw, d)) * 0.45);
float soot = saturate(1.0 - d / 0.55) * smoothstep(0.30, 0.65, ns) * 0.55 * (1.0 - inside);
float ang = th * 1.90986 + (nc - 0.5) * 0.8;
float cd = abs(frac(ang) - 0.5);
float cl = 0.20 + 0.45 * frac(sin(floor(ang) * 12.9898 + Seed * 78.233) * 43758.5453);
float cw = 0.020 / max(rr, 0.25) * (1.0 + 1.0 * (1.0 - saturate(d / 0.4)));
float crack = (1.0 - smoothstep(cw * 0.4, cw, cd)) * smoothstep(0.0, 0.03, d) * (1.0 - smoothstep(cl * 0.6, cl, d));
float lt = 0.5 + 0.5 * (cx * 0.35 - cy * 0.94) / max(rr, 0.05);
float3 rc = float3(RimCol.x, RimCol.y, RimCol.z);
@INTERIOR@
float3 rimc = rc * (0.55 + 0.9 * nr) * (0.7 + 0.3 * lt);
float3 col = lerp(float3(0.018, 0.016, 0.014), holeb, inside);
col = lerp(col, rimc, rima);
col = lerp(col, float3(0.018, 0.016, 0.014), saturate(soot) * (1.0 - rima));
col = lerp(col, float3(0.012, 0.011, 0.010), crack * 0.95);
float a = max(inside, rima);
a = max(a, soot);
a = max(a, crack * 0.92);
a = a * (1.0 - smoothstep(0.78, 0.98, rr)) * saturate(op * 6.0);
Emis = roomc * (1.0 - sidehit) * inside * saturate(op * 6.0);
return float4(col.x, col.y, col.z, a);
"""


def hole_color_code():
    body = HOLE_PRE + 'float Hh = max(HalfCm, 1.0);\n'
    body += hole_field('', 'dot(float3(RP.x, RP.y, RP.z), float3(AU.x, AU.y, AU.z)) / Hh', 'dot(float3(RP.x, RP.y, RP.z), float3(AV.x, AV.y, AV.z)) / Hh')
    interior = tpl(HOLE_INTERIOR, LITE_B=tpl(HOLE_LITE_T, T='b', PX='cx + lsx / Hh', PY='cy + lsy / Hh', SC='0.88'))
    body += tpl(HOLE_COLOR_POST, FBM_NC=fbm('nc', 'cx', 'cy', 3, 2.3, 'Seed * 9.1 + 1.0'), FBM_NS=fbm('ns', 'cx', 'cy', 3, 4.0, 'Seed * 3.3 + 7.0'), INTERIOR=interior)
    return body


# ------------------------------------------------------------------------------------------------------------------ the crater decal
CRATER_FIELD_T = """
float cx@T@ = @CX@;
float cy@T@ = @CY@;
float rr@T@ = sqrt(cx@T@ * cx@T@ + cy@T@ * cy@T@);
float th@T@ = atan2(cy@T@, cx@T@ + 0.00001);
@FBM_NW@
float tw1@T@ = abs(frac(th@T@ * 1.11408 + Seed * 0.713) - 0.5) * 2.0;
float tw2@T@ = abs(frac(th@T@ * 1.75070 + Seed * 0.377 + 0.31) - 0.5) * 2.0;
float pf@T@ = 0.78 + 0.16 * tw1@T@ + 0.08 * tw2@T@ + 0.06 * sin(th@T@ * 3.0 + Seed * 4.0);
float rc@T@ = 0.27 * pf@T@ * (0.25 + 0.75 * grow);
float rw@T@ = rr@T@ + (nw@T@ - 0.5) * 0.10;
float core@T@ = 1.0 - smoothstep(rc@T@ * 0.6, rc@T@, rw@T@);
float bowl@T@ = 1.0 - smoothstep(rc@T@, rc@T@ * 2.0, rw@T@);
float ringk@T@ = smoothstep(rc@T@ * 1.1, rc@T@ * 1.5, rw@T@) * (1.0 - smoothstep(rc@T@ * 1.9, rc@T@ * 2.7, rw@T@));
"""


def crater_field(t, cx, cy, nw_oct=3):
    return tpl(CRATER_FIELD_T, T=t, CX=cx, CY=cy, FBM_NW=fbm('nw' + t, 'cx' + t, 'cy' + t, nw_oct, 2.6, 'Seed * 13.7'))


CRATER_COLOR_POST = """
@FBM_ND@
@FBM_NS@
@FBM_NC@
float gx = cx * 8.0 + (nw - 0.5) * 1.6 + Seed * 3.1;
float gy = cy * 8.0 + (nd - 0.5) * 1.6 + Seed * 1.7;
float fx = frac(gx);
float fy = frac(gy);
float gl = 1.0 - smoothstep(0.02, 0.10, min(min(fx, 1.0 - fx), min(fy, 1.0 - fy)));
float shade = frac(sin(floor(gx) * 12.9898 + floor(gy) * 78.233 + Seed * 3.7) * 43758.5453);
float ang = th * 2.22817 + (nc - 0.5) * 0.7;
float cf = abs(frac(ang) - 0.5);
float cl = 0.40 + 0.55 * frac(sin(floor(ang) * 12.9898 + Seed * 78.233) * 43758.5453);
float cw = 0.026 / max(rr, 0.2) * (1.0 + 1.2 * (1.0 - saturate(rr / 0.6)));
float crack = (1.0 - smoothstep(cw * 0.4, cw, cf)) * smoothstep(rc * 0.7, rc * 1.2, rr) * (1.0 - smoothstep(cl * 0.7 * grow, cl * grow + 0.001, rr));
float ang2 = th * 4.29718 + (nd - 0.5) * 1.1;
float cf2 = abs(frac(ang2) - 0.5);
float cl2 = 0.25 + 0.35 * frac(sin(floor(ang2) * 39.346 + Seed * 11.135) * 43758.5453);
float cw2 = 0.0105 / max(rr, 0.2);
float hair = (1.0 - smoothstep(cw2 * 0.4, cw2, cf2)) * smoothstep(rc * 1.3, rc * 1.8, rr) * (1.0 - smoothstep(cl2 * 0.7 * grow, cl2 * grow + 0.001, rr));
float soot = (1.0 - smoothstep(0.2, 0.95, rr)) * smoothstep(0.25, 0.7, ns);
float3 rc3 = float3(RimCol.x, RimCol.y, RimCol.z);
float3 col = rc3 * (0.7 + 0.8 * shade) * (1.0 - 0.8 * gl);
col = lerp(float3(0.02, 0.018, 0.017), col, ringk);
col = lerp(col, float3(0.022, 0.02, 0.018), bowl * (1.0 - ringk));
col = lerp(col, float3(0.004, 0.004, 0.004), core);
float cr = max(crack, hair);
col = lerp(col, float3(0.008, 0.008, 0.008), cr * 0.9);
float a = max(core, bowl * 0.8);
a = max(a, ringk * (0.55 + 0.4 * shade));
a = max(a, cr * 0.92);
a = max(a, soot * 0.5);
a = a * (1.0 - smoothstep(0.72, 0.98, rr)) * saturate(op * 8.0);
return float4(col.x, col.y, col.z, a);
"""


def crater_color_code():
    body = HOLE_PRE + crater_field('', 'UV.x * 2.0 - 1.0', 'UV.y * 2.0 - 1.0')
    body += tpl(CRATER_COLOR_POST, FBM_ND=fbm('nd', 'cx', 'cy', 4, 8.0, 'Seed * 5.3 + 1.0'), FBM_NS=fbm('ns', 'cx', 'cy', 3, 3.5, 'Seed * 3.1 + 9.0'),
                FBM_NC=fbm('nc', 'cx', 'cy', 3, 2.0, 'Seed * 9.7 + 4.0'))
    return body


CRATER_H_T = """
@FBM_NC@
float ang@T@ = th@T@ * 2.22817 + (nc@T@ - 0.5) * 0.7;
float cf@T@ = abs(frac(ang@T@) - 0.5);
float cl@T@ = 0.40 + 0.55 * frac(sin(floor(ang@T@) * 12.9898 + Seed * 78.233) * 43758.5453);
float cw@T@ = 0.026 / max(rr@T@, 0.2) * (1.0 + 1.2 * (1.0 - saturate(rr@T@ / 0.6)));
float crack@T@ = (1.0 - smoothstep(cw@T@ * 0.4, cw@T@, cf@T@)) * smoothstep(rc@T@ * 0.7, rc@T@ * 1.2, rr@T@) * (1.0 - smoothstep(cl@T@ * 0.7 * grow, cl@T@ * grow + 0.001, rr@T@));
float h@T@ = -1.0 * bowl@T@ - 0.8 * core@T@ + 0.5 * ringk@T@ * nw@T@ - 0.5 * crack@T@;
"""


def crater_normal_code():
    body = HOLE_PRE + 'float ex = 0.012;\n'
    for t, cx, cy in (('a', 'UV.x * 2.0 - 1.0', 'UV.y * 2.0 - 1.0'), ('b', 'UV.x * 2.0 - 1.0 + ex', 'UV.y * 2.0 - 1.0'), ('c', 'UV.x * 2.0 - 1.0', 'UV.y * 2.0 - 1.0 + ex')):
        body += crater_field(t, cx, cy) + tpl(CRATER_H_T, T=t, FBM_NC=fbm('nc' + t, 'cx' + t, 'cy' + t, 2, 2.0, 'Seed * 9.7 + 4.0'))
    body += """
float gx = (hb - ha) / ex;
float gy = (hc - ha) / ex;
float3 nn = normalize(float3(-gx * Bump, -gy * Bump, 1.0));
return nn;
"""
    return body


# ------------------------------------------------------------------------------------------------------- vapour / dust / debris
VAPOUR_T = """
float nl = sqrt(N.x * N.x + N.y * N.y + N.z * N.z) + 0.00001;
float vl = sqrt(V.x * V.x + V.y * V.y + V.z * V.z) + 0.00001;
float ndv = abs(N.x * V.x + N.y * V.y + N.z * V.z) / (nl * vl);
float fr = pow(1.0 - saturate(ndv), max(EP, 0.2));
float px = RP.x * 0.02 + RP.z * 0.011 + T * 0.4;
float py = RP.y * 0.02 + RP.z * 0.017;
@FBM_NZ@
float turb = lerp(1.0, 0.25 + 1.5 * nz, saturate(Soft));
float o = Op * turb * (0.10 + 0.90 * fr);
o = o * saturate((PD - NF) / max(NL, 1.0));
return saturate(o);
"""

DUST_T = """
float nl = sqrt(N.x * N.x + N.y * N.y + N.z * N.z) + 0.00001;
float vl = sqrt(V.x * V.x + V.y * V.y + V.z * V.z) + 0.00001;
float ndv = abs(N.x * V.x + N.y * V.y + N.z * V.z) / (nl * vl);
float fa = pow(saturate(ndv), 0.6);
float px = RP.x * 0.012 + Seed * 3.7 + T * 0.15;
float py = RP.y * 0.012 + RP.z * 0.017;
@FBM_NZ@
float lump = smoothstep(0.12, 0.45, nz + (fa - 1.0) * 0.7);
float o = Op * lerp(fa, lump * fa, saturate(Soft));
o = o * saturate((PD - NF) / max(NL, 1.0));
return saturate(o);
"""

# critic r5 #8 ("debris is untextured grey cubes"): the r3 speckle was a +-30 % brightness wobble in WORLD offsets (it swam over a tumbling
# piece and read as flat grey at chase distance). r6: the piece's OWN frame (LocalPosition, the engine cube is +-50 units, scaled by Size =
# the piece's dimensions in cm), so the pattern rides with it, and a much stronger broken-concrete read: a per-face tint (each of the six faces
# its own shade, one in three a lighter fresh break), dark crevices from ridged noise, aggregate specks, chipped light edges and dirt in the
# crevices / on the edges (returned as ambient occlusion in .w). Brick (B >= 0.5) keeps the courses, now in the piece frame too.
CHUNK_T = """
float sx = max(PSz.x, 1.0) * 0.01;
float sy = max(PSz.y, 1.0) * 0.01;
float sz = max(PSz.z, 1.0) * 0.01;
float rx = LP.x * sx;
float ry = LP.y * sy;
float rz = LP.z * sz;
float ax = abs(LP.x) / 50.0;
float ay = abs(LP.y) / 50.0;
float az = abs(LP.z) / 50.0;
float fid = (ax >= ay && ax >= az) ? (LP.x > 0.0 ? 1.0 : 2.0) : ((ay >= az) ? (LP.y > 0.0 ? 3.0 : 4.0) : (LP.z > 0.0 ? 5.0 : 6.0));
float fh = frac(sin(fid * 12.9898 + Seed * 78.233) * 43758.5453);
float emax = max(ax, max(ay, az));
float emid = ax + ay + az - emax - min(ax, min(ay, az));
@FBM_N1@
@FBM_N2@
@FBM_N3@
float3 cc0 = float3(C.x, C.y, C.z);
float fresh = step(0.67, fh);
float ftint = lerp(0.72 + 0.36 * fh, 1.28, fresh);
float3 conc = cc0 * ftint * (0.45 + 1.1 * n1) * (0.8 + 0.4 * n2);
float rdg = 1.0 - abs(2.0 * n3 - 1.0);
float crev = smoothstep(0.84, 0.96, rdg);
float ck = frac(sin(floor(rx * 0.9) * 12.9898 + floor(ry * 0.9) * 78.233 + floor(rz * 0.9) * 37.719 + Seed) * 43758.5453);
float speck = step(0.9, ck) - step(ck, 0.07);
conc = conc * (1.0 + 0.35 * speck);
float chip = smoothstep(0.84, 0.97, emid) * step(0.45, n2);
conc = lerp(conc, cc0 * 1.45 + float3(0.05, 0.05, 0.05), chip * 0.6);
conc = conc * (1.0 - 0.6 * crev);
float bu = (rx + ry) * 0.0454;
float bv = rz * 0.1429;
float brow = floor(bv);
bu = bu + 0.5 * (brow - 2.0 * floor(brow * 0.5));
float fu = frac(bu);
float fv = frac(bv);
float me = min(min(fu, 1.0 - fu) * 3.14, min(fv, 1.0 - fv));
float mortar = 1.0 - smoothstep(0.05, 0.14, me);
float hb = frac(sin(floor(bu) * 12.9898 + brow * 78.233 + Seed) * 43758.5453);
float3 brk = cc0 * (0.7 + 0.6 * hb) * (0.75 + 0.5 * n1) * (1.0 - 0.5 * crev);
brk = lerp(brk, float3(0.32, 0.31, 0.29), mortar);
float bsel = step(0.5, B);
float3 outc = lerp(conc, brk, bsel);
float ao = saturate(1.0 - 0.55 * crev - 0.25 * smoothstep(0.9, 1.0, emid) * (1.0 - chip) - 0.35 * mortar * bsel);
return float4(outc.x, outc.y, outc.z, ao);
"""

# critic r5 #8 (the boom ring "reads as a chain of ~20 separate bubbles"): ONE flattened sphere per ring whose opacity is an annulus in the
# mesh's own radius (LocalPosition: the engine sphere is radius 50) -- Band = ring radius / mesh radius, BandW = tube half-thickness / mesh
# radius (the director sets both each frame).
# r7 (critic r6 #4: "a soft filled disc, luma lifted evenly 131-173 with no edge peak"): the profile is now asymmetric. dr = (rr - Band) / BandW
# is the signed distance from the ring's centre line in band widths (+ outside). OUTSIDE it is a HARD leading edge (opaque to dr 0.08, gone by
# 0.42); INSIDE a short soft wake (gone at dr -2.4); the mesh interior inside that is fully clear. The emissive brightness is returned as the
# second component: Gain on the whole profile plus RimGain on a hot core that peaks at the leading edge and is gone ~0.9 band widths inside it,
# so the rim reads >= 220/255 against the sky while the interior stays clear. Faded to 0 near the lens (PixelDepth) like M_InvVapour.
# Output float2 = (opacity, emissive multiplier).
RING_T = """
float nl = sqrt(N.x * N.x + N.y * N.y + N.z * N.z) + 0.00001;
float vl = sqrt(V.x * V.x + V.y * V.y + V.z * V.z) + 0.00001;
float ndv = abs(N.x * V.x + N.y * V.y + N.z * V.z) / (nl * vl);
float fr = pow(1.0 - saturate(ndv), max(EP, 0.2));
float rr = sqrt(LP.x * LP.x + LP.y * LP.y) / 50.0;
float bw = max(BandW, 0.01);
float dr = (rr - Band) / bw;
float lead = 1.0 - smoothstep(0.08, 0.42, dr);
float wake = pow(saturate(1.0 + dr / 2.4), 2.2);
float prof = lead * wake;
float rim = lead * pow(saturate(1.0 + dr * 1.1), 2.0);
float ci = LP.x / max(rr * 50.0, 0.001);
float si = LP.y / max(rr * 50.0, 0.001);
float px = ci * 2.6 + T * 0.7;
float py = si * 2.6 + dr * 1.2 + LP.z * 0.02;
@FBM_NZ@
float turb = lerp(1.0, 0.7 + 0.6 * nz, saturate(Soft));
float o = Op * prof * turb * (0.8 + 0.2 * fr);
o = o * saturate((PD - NF) / max(NL, 1.0));
float br = Gain * (0.25 + 0.75 * prof) + RimGain * rim;
return float2(saturate(o), br);
"""

# r7 (critic r6 #8: "a glass tower spawns bricks"): a thin pane shard for a flat box. Face-on it is mostly clear (a faint tint), at grazing angles
# bright (fresnel), and a per-shard glint flashes as it tumbles (a phase from the object position). Unlit, exposure-independent through the
# graph's EyeAdaptationInverse. Output float2 = (opacity, emissive multiplier).
GLASS_T = """
float nl = sqrt(N.x * N.x + N.y * N.y + N.z * N.z) + 0.00001;
float vl = sqrt(V.x * V.x + V.y * V.y + V.z * V.z) + 0.00001;
float ndv = abs(N.x * V.x + N.y * V.y + N.z * V.z) / (nl * vl);
float fr = pow(1.0 - saturate(ndv), 3.0);
float ph = frac(sin(OP.x * 0.0173 + OP.y * 0.0291 + OP.z * 0.0117) * 43758.5453);
float gl = pow(saturate(sin(T * (4.0 + 6.0 * ph) + ph * 40.0) * 0.5 + 0.5), 6.0);
float o = Op * (0.22 + 0.55 * fr + 0.35 * gl);
o = o * saturate((PD - NF) / max(NL, 1.0));
float br = Gain * (0.35 + 2.4 * fr + 2.2 * gl);
return float2(saturate(o), br);
"""


# owner feedback 2026-10-15 #1 (super boost speed read): a speed line on a sphere stretched along Dir (the director's streak pieces). Brightest on
# the centre line facing the camera, fading to the silhouette (so it reads as a thin line, not a capsule) and to 0 at both ends along Dir
# (|axial| / HalfLen, HalfLen in cm set per piece), a little brighter at the front end. Additive: the output is an emissive gain 0..1.
STREAK_T = """
float nl = sqrt(N.x * N.x + N.y * N.y + N.z * N.z) + 0.00001;
float vl = sqrt(V.x * V.x + V.y * V.y + V.z * V.z) + 0.00001;
float ndv = abs(N.x * V.x + N.y * V.y + N.z * V.z) / (nl * vl);
float core = pow(saturate(ndv), 1.6);
float dl = sqrt(Dir.x * Dir.x + Dir.y * Dir.y + Dir.z * Dir.z) + 0.00001;
float ax = (RP.x * Dir.x + RP.y * Dir.y + RP.z * Dir.z) / dl;
float hl = max(HalfLen, 1.0);
float u = saturate(abs(ax) / hl);
float along = (1.0 - u * u) * (1.0 - u * u);
float head = 0.6 + 0.4 * saturate(ax / hl * 0.5 + 0.5);
float nfade = saturate((PD - NF) / max(NL, 1.0));
return saturate(Op * core * along * head * nfade);
"""


def vapour_code():
    return tpl(VAPOUR_T, FBM_NZ=fbm('nz', 'px', 'py', 3, 1.0, '0.0'))


def streak_code():
    return STREAK_T


def dust_code():
    return tpl(DUST_T, FBM_NZ=fbm('nz', 'px', 'py', 4, 1.0, 'Seed'))


def chunk_code():
    return tpl(CHUNK_T, FBM_N1=fbm('n1', 'rx * 0.085 + Seed * 7.0', 'ry * 0.085 + rz * 0.06', 3, 1.0, '0.0'),
               FBM_N2=fbm('n2', 'rx * 0.35 + ry * 0.11', 'rz * 0.35 + ry * 0.2', 2, 1.0, '1.7'),
               FBM_N3=fbm('n3', 'rx * 0.16 + rz * 0.07 + Seed * 3.0', 'ry * 0.16 - rz * 0.05', 3, 1.0, '4.1'))


def ring_code():
    return tpl(RING_T, FBM_NZ=fbm('nz', 'px', 'py', 3, 1.0, '0.0'))


def glass_code():
    return GLASS_T


# name -> (hlsl, [(input, type)], output type[, [(extra output name, type)]]) ; the Custom nodes of the materials
CUSTOM_NODES = {
    'hole_color': (hole_color_code, [('RP', 'float3'), ('CV', 'float3'), ('AU', 'float3'), ('AV', 'float3'), ('AN', 'float3'), ('CC', 'float3'),
                                     ('Seed', 'float'), ('Open', 'float'), ('RimCol', 'float3'), ('HalfCm', 'float'), ('Glass', 'float')], 'float4',
                   [('Emis', 'float3')]),
    'crater_color': (crater_color_code, [('UV', 'float2'), ('Seed', 'float'), ('Open', 'float'), ('RimCol', 'float3')], 'float4'),
    'crater_normal': (crater_normal_code, [('UV', 'float2'), ('Seed', 'float'), ('Open', 'float'), ('Bump', 'float')], 'float3'),
    'vapour': (vapour_code, [('N', 'float3'), ('V', 'float3'), ('RP', 'float3'), ('T', 'float'), ('Op', 'float'), ('EP', 'float'), ('Soft', 'float'),
                             ('PD', 'float'), ('NF', 'float'), ('NL', 'float')], 'float'),
    'dust': (dust_code, [('N', 'float3'), ('V', 'float3'), ('RP', 'float3'), ('T', 'float'), ('Op', 'float'), ('Soft', 'float'), ('Seed', 'float'),
                         ('PD', 'float'), ('NF', 'float'), ('NL', 'float')], 'float'),
    'chunk': (chunk_code, [('LP', 'float3'), ('PSz', 'float3'), ('C', 'float3'), ('B', 'float'), ('Seed', 'float')], 'float4'),
    'ring': (ring_code, [('N', 'float3'), ('V', 'float3'), ('LP', 'float3'), ('T', 'float'), ('Op', 'float'), ('EP', 'float'), ('Soft', 'float'),
                         ('Band', 'float'), ('BandW', 'float'), ('Gain', 'float'), ('RimGain', 'float'), ('PD', 'float'), ('NF', 'float'), ('NL', 'float')], 'float2'),
    'glass': (glass_code, [('N', 'float3'), ('V', 'float3'), ('OP', 'float3'), ('T', 'float'), ('Op', 'float'), ('Gain', 'float'),
                           ('PD', 'float'), ('NF', 'float'), ('NL', 'float')], 'float2'),
    'streak': (streak_code, [('N', 'float3'), ('V', 'float3'), ('RP', 'float3'), ('Dir', 'float3'), ('HalfLen', 'float'), ('Op', 'float'),
                             ('PD', 'float'), ('NF', 'float'), ('NL', 'float')], 'float'),
}


def dump_hlsl(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for name, spec in CUSTOM_NODES.items():
        gen, ins, outt = spec[0], spec[1], spec[2]
        extra = spec[3] if len(spec) > 3 else []
        path = os.path.join(out_dir, name + '.hlsl')
        with open(path, 'w') as f:
            f.write('// inputs: %s\n// output: %s\n' % (', '.join('%s %s' % (t, n) for n, t in ins), outt))
            if extra:
                f.write('// additional outputs: %s\n' % ', '.join('%s %s' % (t, n) for n, t in extra))
            f.write(gen())
        print('wrote', path)


# ============================================================================================================== inside Unreal
def build_in_unreal():
    EAL = unreal.EditorAssetLibrary
    MEL = unreal.MaterialEditingLibrary
    AT = unreal.AssetToolsHelpers.get_asset_tools()
    log = lambda *a: print('[build_invincible_fx]', *a, flush=True)

    if not EAL.make_directory(DEST) and not EAL.does_directory_exist(DEST):
        raise RuntimeError('cannot create ' + DEST)

    def guard(path):
        if not path.startswith(DEST + '/'):
            raise RuntimeError('refusing to touch an asset outside %s/: %s' % (DEST, path))

    def material(name, **props):
        """the Material /Game/Invincible/FX/<name>: created when missing, otherwise its graph is cleared and rebuilt in place"""
        path = '%s/%s' % (DEST, name)
        guard(path)
        if EAL.does_asset_exist(path):
            mat = unreal.load_asset(path)
            if not isinstance(mat, unreal.Material):
                raise RuntimeError('%s exists but is not a Material' % path)
            MEL.delete_all_material_expressions(mat)
        else:
            mat = AT.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
        if mat is None:
            raise RuntimeError('could not create ' + path)
        for k, v in props.items():
            mat.set_editor_property(k, v)
        return mat, path

    def node(mat, cls, x, y):
        e = MEL.create_material_expression(mat, cls, x, y)
        if e is None:
            raise RuntimeError('could not create expression %s' % cls)
        return e

    def sparam(mat, name, val, x, y):
        p = node(mat, unreal.MaterialExpressionScalarParameter, x, y)
        p.set_editor_property('parameter_name', name); p.set_editor_property('default_value', float(val))
        return p

    def vparam(mat, name, val, x, y):
        p = node(mat, unreal.MaterialExpressionVectorParameter, x, y)
        p.set_editor_property('parameter_name', name); p.set_editor_property('default_value', unreal.LinearColor(*val))
        return p

    def const(mat, val, x, y):
        c = node(mat, unreal.MaterialExpressionConstant, x, y)
        c.set_editor_property('r', float(val))
        return c

    def custom(mat, key, srcs, x, y):
        """a Custom node for CUSTOM_NODES[key]; srcs = {input name: (expression, output name)}; r7: additional outputs (the 4th table entry) are declared too"""
        spec = CUSTOM_NODES[key]
        gen, ins, outt = spec[0], spec[1], spec[2]
        extra = spec[3] if len(spec) > 3 else []
        c = node(mat, unreal.MaterialExpressionCustom, x, y)
        c.set_editor_property('code', gen())
        c.set_editor_property('output_type', getattr(unreal.CustomMaterialOutputType, {'float': 'CMOT_FLOAT1', 'float2': 'CMOT_FLOAT2', 'float3': 'CMOT_FLOAT3', 'float4': 'CMOT_FLOAT4'}[outt]))
        c.set_editor_property('description', key)
        ci = []
        for n, _t in ins:
            i = unreal.CustomInput(); i.set_editor_property('input_name', n); ci.append(i)
        c.set_editor_property('inputs', ci)
        if extra:
            outs = []
            for n, t in extra:
                co = unreal.CustomOutput(); co.set_editor_property('output_name', n)
                co.set_editor_property('output_type', getattr(unreal.CustomMaterialOutputType, {'float': 'CMOT_FLOAT1', 'float2': 'CMOT_FLOAT2', 'float3': 'CMOT_FLOAT3'}[t]))
                outs.append(co)
            c.set_editor_property('additional_outputs', outs)
        for n, _t in ins:
            src, out = srcs[n]
            if not MEL.connect_material_expressions(src, out, c, n):
                raise RuntimeError('%s: could not connect input %s' % (key, n))
        return c

    def mask(mat, src, r, g, b, a, x, y):
        m = node(mat, unreal.MaterialExpressionComponentMask, x, y)
        m.set_editor_property('r', r); m.set_editor_property('g', g); m.set_editor_property('b', b); m.set_editor_property('a', a)
        MEL.connect_material_expressions(src, '', m, '')
        return m

    def mul(mat, a, b, x, y):
        m = node(mat, unreal.MaterialExpressionMultiply, x, y)
        MEL.connect_material_expressions(a, '', m, 'A'); MEL.connect_material_expressions(b, '', m, 'B')
        return m

    def prop(src, p, name):
        if not MEL.connect_material_property(src, '', p):
            raise RuntimeError('%s: could not connect %s' % (name, p))

    def finish(mat, path):
        errs = MEL.recompile_material(mat)
        errs = [str(e) for e in (errs or [])]
        if errs:
            raise RuntimeError('%s: material compile errors: %s' % (path, '; '.join(errs[:6])))
        if not EAL.save_asset(path):
            raise RuntimeError('could not save ' + path)
        if not EAL.does_asset_exist(path):
            raise RuntimeError('missing after save: ' + path)
        log('built', path, '(%d expressions)' % MEL.get_num_material_expressions(mat))

    # ---- decals: deferred decal domain, translucent decal blend. M_LookWet (build_look.py) is the working precedent in this project.
    def decal(name, seed, rimcol, bump, color_key, normal_key):
        mat, path = material(name, material_domain=unreal.MaterialDomain.MD_DEFERRED_DECAL, blend_mode=unreal.BlendMode.BLEND_TRANSLUCENT)
        uv = node(mat, unreal.MaterialExpressionTextureCoordinate, -1100, 0)
        sd = sparam(mat, 'Seed', seed, -1100, 120)
        op = sparam(mat, 'Open', 1.0, -1100, 220)
        bp = sparam(mat, 'Bump', bump, -1100, 320)
        rc = vparam(mat, 'RimCol', rimcol, -1100, 420)
        col = custom(mat, color_key, {'UV': (uv, ''), 'Seed': (sd, ''), 'Open': (op, ''), 'RimCol': (rc, '')}, -700, 0)
        nrm = custom(mat, normal_key, {'UV': (uv, ''), 'Seed': (sd, ''), 'Open': (op, ''), 'Bump': (bp, '')}, -700, 360)
        rgb = mask(mat, col, True, True, True, False, -420, -40)
        alpha = mask(mat, col, False, False, False, True, -420, 80)
        prop(rgb, unreal.MaterialProperty.MP_BASE_COLOR, name)
        prop(alpha, unreal.MaterialProperty.MP_OPACITY, name)
        prop(nrm, unreal.MaterialProperty.MP_NORMAL, name)
        prop(const(mat, 1.0, -420, 200), unreal.MaterialProperty.MP_ROUGHNESS, name)
        prop(const(mat, 0.05, -420, 280), unreal.MaterialProperty.MP_SPECULAR, name)
        finish(mat, path)

    # ---- r7: the breach opening with a recessed interior. The frame (Centre, AxU, AxV, AxN, HalfCm) is set per placement by the director.
    # World position (LWC) minus Centre (masked to rgb) = RP; the interior colours are display-referred and written as EMISSIVE x EyeAdaptationInverse
    # (exposure-independent, like the vapour); the lit reveal and the rim are base colour. No normal output (no dependence on UE's decal tangent frame).
    def breach_hole(name='M_BreachHole'):
        mat, path = material(name, material_domain=unreal.MaterialDomain.MD_DEFERRED_DECAL, blend_mode=unreal.BlendMode.BLEND_TRANSLUCENT)
        wp = node(mat, unreal.MaterialExpressionWorldPosition, -1300, 0)
        ctr = vparam(mat, 'Centre', (0.0, 0.0, 0.0, 0.0), -1300, 100)
        ctr3 = mask(mat, ctr, True, True, True, False, -1100, 100)
        rp = node(mat, unreal.MaterialExpressionSubtract, -900, 40)
        MEL.connect_material_expressions(wp, '', rp, 'A'); MEL.connect_material_expressions(ctr3, '', rp, 'B')
        cv = node(mat, unreal.MaterialExpressionCameraVectorWS, -1300, 220)
        axu = vparam(mat, 'AxU', (0.0, 1.0, 0.0, 0.0), -1300, 320)
        axv = vparam(mat, 'AxV', (0.0, 0.0, 1.0, 0.0), -1300, 420)
        axn = vparam(mat, 'AxN', (-1.0, 0.0, 0.0, 0.0), -1300, 520)
        hf = sparam(mat, 'HalfCm', 400.0, -1300, 620)
        gl = sparam(mat, 'Glass', 0.0, -1300, 720)
        sd = sparam(mat, 'Seed', 0.37, -1300, 820)
        op = sparam(mat, 'Open', 1.0, -1300, 920)
        rc = vparam(mat, 'RimCol', (0.30, 0.28, 0.25, 1.0), -1300, 1020)
        col = custom(mat, 'hole_color', {'RP': (rp, ''), 'CV': (cv, ''), 'AU': (axu, ''), 'AV': (axv, ''), 'AN': (axn, ''), 'CC': (ctr, ''),
                                         'Seed': (sd, ''), 'Open': (op, ''), 'RimCol': (rc, ''), 'HalfCm': (hf, ''), 'Glass': (gl, '')}, -600, 100)
        rgb = mask(mat, col, True, True, True, False, -300, 20)
        alpha = mask(mat, col, False, False, False, True, -300, 140)
        prop(rgb, unreal.MaterialProperty.MP_BASE_COLOR, name)
        prop(alpha, unreal.MaterialProperty.MP_OPACITY, name)
        prop(const(mat, 1.0, -300, 260), unreal.MaterialProperty.MP_ROUGHNESS, name)
        prop(const(mat, 0.05, -300, 340), unreal.MaterialProperty.MP_SPECULAR, name)
        eai = node(mat, unreal.MaterialExpressionEyeAdaptationInverse, -600, 520)
        em = node(mat, unreal.MaterialExpressionMultiply, -300, 460)
        if not MEL.connect_material_expressions(col, 'Emis', em, 'A') or not MEL.connect_material_expressions(eai, '', em, 'B'):
            raise RuntimeError('%s: could not connect the Emis output' % name)
        prop(em, unreal.MaterialProperty.MP_EMISSIVE_COLOR, name)
        finish(mat, path)

    breach_hole('M_BreachHole')
    decal('M_CraterDecal', 0.61, (0.085, 0.082, 0.078, 1.0), 0.10, 'crater_color', 'crater_normal')

    # ---- vapour: translucent unlit two-sided, fresnel-bright edge, noise travelling with the object
    mat, path = material('M_InvVapour', material_domain=unreal.MaterialDomain.MD_SURFACE, blend_mode=unreal.BlendMode.BLEND_TRANSLUCENT,
                         shading_model=unreal.MaterialShadingModel.MSM_UNLIT, two_sided=True)
    pn = node(mat, unreal.MaterialExpressionPixelNormalWS, -1100, 0)
    cv = node(mat, unreal.MaterialExpressionCameraVectorWS, -1100, 100)
    wp = node(mat, unreal.MaterialExpressionWorldPosition, -1100, 200)
    ob = node(mat, unreal.MaterialExpressionObjectPositionWS, -1100, 300)
    rp = node(mat, unreal.MaterialExpressionSubtract, -900, 250)
    MEL.connect_material_expressions(wp, '', rp, 'A'); MEL.connect_material_expressions(ob, '', rp, 'B')
    tm = node(mat, unreal.MaterialExpressionTime, -1100, 400)
    colp = vparam(mat, 'Color', (0.92, 0.95, 1.0, 1.0), -1100, 500)
    opp = sparam(mat, 'Opacity', 1.0, -1100, 600)
    epp = sparam(mat, 'EdgePow', 1.6, -1100, 700)
    gnp = sparam(mat, 'Gain', 1.4, -1100, 800)
    sfp = sparam(mat, 'Soft', 0.7, -1100, 900)
    # critic r4 (fl04 frames washed to Y 173-185 with the lens inside / against vapour): opacity fades to 0 within NearFade + NearFadeLen cm of
    # the lens (PixelDepth); the director also fades whole pieces near the lens (CamFade)
    pdp = node(mat, unreal.MaterialExpressionPixelDepth, -1100, 1000)
    nfp = sparam(mat, 'NearFade', 60.0, -1100, 1100)
    nlp = sparam(mat, 'NearFadeLen', 220.0, -1100, 1200)
    vap = custom(mat, 'vapour', {'N': (pn, ''), 'V': (cv, ''), 'RP': (rp, ''), 'T': (tm, ''), 'Op': (opp, ''), 'EP': (epp, ''), 'Soft': (sfp, ''),
                                 'PD': (pdp, ''), 'NF': (nfp, ''), 'NL': (nlp, '')}, -600, 300)
    # owner capture (boom ring read as a DARK disc): the city is lit in physical units with auto-exposure, so a plain emissive of ~1 is
    # near-black after exposure; multiplying by EyeAdaptationInverse makes the vapour's brightness exposure-independent (display-relative)
    eai = node(mat, unreal.MaterialExpressionEyeAdaptationInverse, -800, 640)
    prop(mul(mat, mul(mat, colp, gnp, -650, 520), eai, -500, 560), unreal.MaterialProperty.MP_EMISSIVE_COLOR, 'M_InvVapour')
    prop(vap, unreal.MaterialProperty.MP_OPACITY, 'M_InvVapour')
    finish(mat, path)

    # ---- dust: translucent lit (surface lighting), soft round silhouette, eroded lumpy interior
    mat, path = material('M_InvDust', material_domain=unreal.MaterialDomain.MD_SURFACE, blend_mode=unreal.BlendMode.BLEND_TRANSLUCENT,
                         shading_model=unreal.MaterialShadingModel.MSM_DEFAULT_LIT, two_sided=True)
    try:
        mat.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE)
    except Exception as ex:
        print('WARN', SCRIPT, 'M_InvDust: translucency_lighting_mode not settable:', str(ex).split('\n')[0][:120], flush=True)
    pn = node(mat, unreal.MaterialExpressionPixelNormalWS, -1100, 0)
    cv = node(mat, unreal.MaterialExpressionCameraVectorWS, -1100, 100)
    wp = node(mat, unreal.MaterialExpressionWorldPosition, -1100, 200)
    ob = node(mat, unreal.MaterialExpressionObjectPositionWS, -1100, 300)
    rp = node(mat, unreal.MaterialExpressionSubtract, -900, 250)
    MEL.connect_material_expressions(wp, '', rp, 'A'); MEL.connect_material_expressions(ob, '', rp, 'B')
    tm = node(mat, unreal.MaterialExpressionTime, -1100, 400)
    colp = vparam(mat, 'Color', (0.34, 0.31, 0.27, 1.0), -1100, 500)
    opp = sparam(mat, 'Opacity', 0.7, -1100, 600)
    emp = sparam(mat, 'Emissive', 0.12, -1100, 700)
    sfp = sparam(mat, 'Soft', 1.0, -1100, 800)
    sdp = sparam(mat, 'Seed', 0.5, -1100, 900)
    pdp = node(mat, unreal.MaterialExpressionPixelDepth, -1100, 1000)   # critic r4: near-lens fade (see M_InvVapour)
    nfp = sparam(mat, 'NearFade', 40.0, -1100, 1100)
    nlp = sparam(mat, 'NearFadeLen', 200.0, -1100, 1200)
    dst = custom(mat, 'dust', {'N': (pn, ''), 'V': (cv, ''), 'RP': (rp, ''), 'T': (tm, ''), 'Op': (opp, ''), 'Soft': (sfp, ''), 'Seed': (sdp, ''),
                               'PD': (pdp, ''), 'NF': (nfp, ''), 'NL': (nlp, '')}, -600, 300)
    prop(colp, unreal.MaterialProperty.MP_BASE_COLOR, 'M_InvDust')
    prop(mul(mat, colp, emp, -500, 520), unreal.MaterialProperty.MP_EMISSIVE_COLOR, 'M_InvDust')
    prop(const(mat, 1.0, -500, 640), unreal.MaterialProperty.MP_ROUGHNESS, 'M_InvDust')
    prop(const(mat, 0.0, -500, 700), unreal.MaterialProperty.MP_SPECULAR, 'M_InvDust')
    prop(dst, unreal.MaterialProperty.MP_OPACITY, 'M_InvDust')
    finish(mat, path)

    # ---- debris: opaque lit concrete speckle / brick courses; Color / Rough match M_CmbSolid so the director's MIDs work on either
    mat, path = material('M_InvChunk', material_domain=unreal.MaterialDomain.MD_SURFACE, blend_mode=unreal.BlendMode.BLEND_OPAQUE,
                         shading_model=unreal.MaterialShadingModel.MSM_DEFAULT_LIT, two_sided=False)
    # (critic r5 #8: the piece's own frame -- LocalPosition (mesh units) x Size (cm, set per piece by the director); .w = ambient occlusion)
    lp = node(mat, unreal.MaterialExpressionLocalPosition, -1100, 0)
    szp = vparam(mat, 'Size', (100.0, 100.0, 100.0, 0.0), -1100, 100)
    colp = vparam(mat, 'Color', (0.40, 0.38, 0.35, 1.0), -1100, 200)
    rgp = sparam(mat, 'Rough', 0.9, -1100, 300)
    brp = sparam(mat, 'Brick', 0.0, -1100, 400)
    sdp = sparam(mat, 'Seed', 0.5, -1100, 500)
    chk = custom(mat, 'chunk', {'LP': (lp, ''), 'PSz': (szp, ''), 'C': (colp, ''), 'B': (brp, ''), 'Seed': (sdp, '')}, -600, 100)
    prop(mask(mat, chk, True, True, True, False, -350, 60), unreal.MaterialProperty.MP_BASE_COLOR, 'M_InvChunk')
    prop(mask(mat, chk, False, False, False, True, -350, 160), unreal.MaterialProperty.MP_AMBIENT_OCCLUSION, 'M_InvChunk')
    prop(rgp, unreal.MaterialProperty.MP_ROUGHNESS, 'M_InvChunk')
    finish(mat, path)

    # ---- critic r5 #8: the continuous shock ring -- translucent unlit two-sided (as M_InvVapour), opacity = an annulus of the mesh radius.
    # r7 (critic r6 #4): the Custom node returns (opacity, emissive multiplier): a hard hot leading edge, a short wake, a clear interior.
    mat, path = material('M_InvShockRing', material_domain=unreal.MaterialDomain.MD_SURFACE, blend_mode=unreal.BlendMode.BLEND_TRANSLUCENT,
                         shading_model=unreal.MaterialShadingModel.MSM_UNLIT, two_sided=True)
    pn = node(mat, unreal.MaterialExpressionPixelNormalWS, -1100, 0)
    cv = node(mat, unreal.MaterialExpressionCameraVectorWS, -1100, 100)
    lp = node(mat, unreal.MaterialExpressionLocalPosition, -1100, 200)
    tm = node(mat, unreal.MaterialExpressionTime, -1100, 300)
    colp = vparam(mat, 'Color', (0.92, 0.95, 1.0, 1.0), -1100, 400)
    opp = sparam(mat, 'Opacity', 1.0, -1100, 500)
    epp = sparam(mat, 'EdgePow', 1.3, -1100, 600)
    gnp = sparam(mat, 'Gain', 1.1, -1100, 700)
    sfp = sparam(mat, 'Soft', 0.3, -1100, 800)
    bdp = sparam(mat, 'Band', 0.86, -1100, 900)
    bwp = sparam(mat, 'BandW', 0.12, -1100, 1000)
    pdp = node(mat, unreal.MaterialExpressionPixelDepth, -1100, 1100)
    nfp = sparam(mat, 'NearFade', 60.0, -1100, 1200)
    nlp = sparam(mat, 'NearFadeLen', 220.0, -1100, 1300)
    rgp2 = sparam(mat, 'RimGain', 3.2, -1100, 1400)
    rng = custom(mat, 'ring', {'N': (pn, ''), 'V': (cv, ''), 'LP': (lp, ''), 'T': (tm, ''), 'Op': (opp, ''), 'EP': (epp, ''), 'Soft': (sfp, ''),
                               'Band': (bdp, ''), 'BandW': (bwp, ''), 'Gain': (gnp, ''), 'RimGain': (rgp2, ''), 'PD': (pdp, ''), 'NF': (nfp, ''), 'NL': (nlp, '')}, -600, 300)
    eai3 = node(mat, unreal.MaterialExpressionEyeAdaptationInverse, -800, 640)   # exposure-independent (see M_InvVapour)
    ring_br = mask(mat, rng, False, True, False, False, -350, 400)               # emissive multiplier (Gain x profile + RimGain x hot core)
    prop(mul(mat, mul(mat, colp, ring_br, -300, 520), eai3, -150, 560), unreal.MaterialProperty.MP_EMISSIVE_COLOR, 'M_InvShockRing')
    prop(mask(mat, rng, True, False, False, False, -350, 300), unreal.MaterialProperty.MP_OPACITY, 'M_InvShockRing')
    finish(mat, path)

    # ---- r7 (critic r6 #8): glass pane shard for glass-tower debris -- translucent unlit two-sided; opacity / emissive multiplier from the Custom node
    mat, path = material('M_InvGlassShard', material_domain=unreal.MaterialDomain.MD_SURFACE, blend_mode=unreal.BlendMode.BLEND_TRANSLUCENT,
                         shading_model=unreal.MaterialShadingModel.MSM_UNLIT, two_sided=True)
    pn = node(mat, unreal.MaterialExpressionPixelNormalWS, -1100, 0)
    cv = node(mat, unreal.MaterialExpressionCameraVectorWS, -1100, 100)
    ob = node(mat, unreal.MaterialExpressionObjectPositionWS, -1100, 200)
    ob3 = mask(mat, ob, True, True, True, False, -950, 200)
    tm = node(mat, unreal.MaterialExpressionTime, -1100, 300)
    colp = vparam(mat, 'Color', (0.62, 0.78, 0.86, 1.0), -1100, 400)
    opp = sparam(mat, 'Opacity', 0.8, -1100, 500)
    gnp = sparam(mat, 'Gain', 1.0, -1100, 600)
    pdp = node(mat, unreal.MaterialExpressionPixelDepth, -1100, 700)
    nfp = sparam(mat, 'NearFade', 40.0, -1100, 800)
    nlp = sparam(mat, 'NearFadeLen', 160.0, -1100, 900)
    gls = custom(mat, 'glass', {'N': (pn, ''), 'V': (cv, ''), 'OP': (ob3, ''), 'T': (tm, ''), 'Op': (opp, ''), 'Gain': (gnp, ''),
                                'PD': (pdp, ''), 'NF': (nfp, ''), 'NL': (nlp, '')}, -600, 300)
    eai4 = node(mat, unreal.MaterialExpressionEyeAdaptationInverse, -800, 640)   # exposure-independent (see M_InvVapour)
    gls_br = mask(mat, gls, False, True, False, False, -350, 400)
    prop(mul(mat, mul(mat, colp, gls_br, -300, 520), eai4, -150, 560), unreal.MaterialProperty.MP_EMISSIVE_COLOR, 'M_InvGlassShard')
    prop(mask(mat, gls, True, False, False, False, -350, 300), unreal.MaterialProperty.MP_OPACITY, 'M_InvGlassShard')
    finish(mat, path)

    # ---- owner feedback 2026-10-15 #1: speed lines -- translucent ADDITIVE unlit two-sided; emissive = Color x Gain x streak(N, V, RP, Dir, HalfLen, Opacity)
    mat, path = material('M_InvStreak', material_domain=unreal.MaterialDomain.MD_SURFACE, blend_mode=unreal.BlendMode.BLEND_ADDITIVE,
                         shading_model=unreal.MaterialShadingModel.MSM_UNLIT, two_sided=True)
    pn = node(mat, unreal.MaterialExpressionPixelNormalWS, -1100, 0)
    cv = node(mat, unreal.MaterialExpressionCameraVectorWS, -1100, 100)
    wp = node(mat, unreal.MaterialExpressionWorldPosition, -1100, 200)
    ob = node(mat, unreal.MaterialExpressionObjectPositionWS, -1100, 300)
    rp = node(mat, unreal.MaterialExpressionSubtract, -900, 250)
    MEL.connect_material_expressions(wp, '', rp, 'A'); MEL.connect_material_expressions(ob, '', rp, 'B')
    drp = vparam(mat, 'Dir', (1.0, 0.0, 0.0, 0.0), -1100, 400)
    hlp = sparam(mat, 'HalfLen', 500.0, -1100, 500)
    opp = sparam(mat, 'Opacity', 0.5, -1100, 600)
    colp = vparam(mat, 'Color', (0.9, 0.93, 1.0, 1.0), -1100, 700)
    gnp = sparam(mat, 'Gain', 1.6, -1100, 800)
    sparam(mat, 'EdgePow', 1.0, -1100, 900)   # (unused by the graph; the director sets it on every vapour piece)
    pdp = node(mat, unreal.MaterialExpressionPixelDepth, -1100, 1000)   # critic r4: near-lens fade (see M_InvVapour)
    nfp = sparam(mat, 'NearFade', 80.0, -1100, 1100)
    nlp = sparam(mat, 'NearFadeLen', 250.0, -1100, 1200)
    stk = custom(mat, 'streak', {'N': (pn, ''), 'V': (cv, ''), 'RP': (rp, ''), 'Dir': (drp, ''), 'HalfLen': (hlp, ''), 'Op': (opp, ''),
                                 'PD': (pdp, ''), 'NF': (nfp, ''), 'NL': (nlp, '')}, -600, 300)
    cg = mul(mat, colp, gnp, -500, 620)
    eai2 = node(mat, unreal.MaterialExpressionEyeAdaptationInverse, -500, 640)   # exposure-independent (see M_InvVapour)
    prop(mul(mat, mul(mat, cg, stk, -350, 500), eai2, -250, 560), unreal.MaterialProperty.MP_EMISSIVE_COLOR, 'M_InvStreak')
    finish(mat, path)

    # ---- verify: every asset reloads as the right kind with the right domain
    want = {'M_BreachHole': unreal.MaterialDomain.MD_DEFERRED_DECAL, 'M_CraterDecal': unreal.MaterialDomain.MD_DEFERRED_DECAL,
            'M_InvVapour': unreal.MaterialDomain.MD_SURFACE, 'M_InvDust': unreal.MaterialDomain.MD_SURFACE, 'M_InvChunk': unreal.MaterialDomain.MD_SURFACE,
            'M_InvStreak': unreal.MaterialDomain.MD_SURFACE, 'M_InvShockRing': unreal.MaterialDomain.MD_SURFACE, 'M_InvGlassShard': unreal.MaterialDomain.MD_SURFACE}
    for n, dom in want.items():
        m = unreal.load_asset('%s/%s' % (DEST, n))
        if not isinstance(m, unreal.Material) or m.get_editor_property('material_domain') != dom:
            raise RuntimeError('verification failed for %s/%s' % (DEST, n))
    log('verified', ', '.join(sorted(want)))
    print('SM2_BUILD_OK: ' + SCRIPT, flush=True)


if unreal is not None and hasattr(unreal, 'EditorAssetLibrary'):
    build_in_unreal()
elif __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == '--dump-hlsl':
        dump_hlsl(sys.argv[2])
    else:
        print('usage: python3 %s --dump-hlsl <dir>   (inside Unreal this file builds /Game/Invincible/FX/*)' % SCRIPT)

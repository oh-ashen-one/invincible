# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Piece E: the Custom-HLSL material definitions of /Game/Terrain as plain data (no `unreal` import), shared by
#   * unreal/WebHomage/Scripts/build_terrain.py   (creates the material assets from them)
#   * tools/terrain/check_hlsl.py                 (offline DXC compile of every body, so a typo costs seconds instead of a GPU-lock turn)
# Each entry: name, include (virtual shader path or None), code (the Custom node body; Rough / NormalW / Metal / Wpo are additional outputs),
# inputs [(name, kind, arg)] with kind tex|vc|wpos|scalar|vector|time|pir, outputs [(name, floats, material property name)], two_sided.
# Frames: wpos is the UE world position in cm; the browser frame is (x, y up, z) metres = (X, Z, Y) / 100.

PARK_INC = '/Project/Terrain/Park.ush'
LAWN_GRADE = (0.8, 1.62, 0.12, 1.0)   # r05 test hold 2: R 1.0 with the sun-facing turf read R / G 1.11 on p4 (yellow); r04 0.86   # r04 lawn albedo grade (R, G, B): the r02 grade (0.54, 1.20, 0.46) kept the blue (display B / G 0.4-0.5 against 0.17 on the reference lawn): saturation 0.54-0.58 -> target 0.70
LAWN_K = (1.0, 0.16, 1.0, 1.0)        # r04 Lawn.ush: (detail amplitude, mowing-stripe amplitude, grass saturation)
LAWN_INC = '/Project/Terrain/Lawn.ush'   # r04: lawn albedo detail + grade (hand-written; Park.ush is generated)
# r05 lawn sun share (target: tree shadows on the lawn <= 0.6 x the lit lawn luma). Under the golden rig (sun 9 deg, sky light x8, indirect x3.2) a horizontal lawn gets ~sin 9 = 0.16 of the
# sun's irradiance and the sky / Lumen bounce dominates it, so the trees' shadows (near cards cast at every distance) read ~0.9 of the lit lawn (r05 diag: ShowFlag.DynamicShadows 0 vs on,
# 1080p p4: lawn ratio 0.93-1.0 except a few spots). The turf's material AO (indirect diffuse / sky only, the sun is untouched) is LAWN_SKYOCC and the albedo is raised by LAWN_SUNGAIN so the
# sunlit lawn keeps its r04 brightness (sky / sun ~3.8 on the lawn: gain = (1 + 3.8) / (1 + 3.8 x skyocc)); shade becomes the sky-lit share only.
LAWN_SKYOCC = 1.0     # r05 test hold: AO 0.12 x gain 3.3 changed the lawn's look only through the exposure (no shadow appeared): AO off again, the turf normal does the work
LAWN_SUNGAIN = 0.55   # albedo scale with the sun-facing turf normal (the sunlit lawn gets ~1.8 x its r04 irradiance)
LAWN_TILT = 0.85
FILL = 650.0   # r05 (was 450): the shaded foreground crowns of p1 read luma 60-75   # r03 residual shade fill scale (cd/m2 per unit albedo, x tfFillW): the r02 constant was 1800 x (0.4 .. 1.0) on every leaf pixel, sun or shade
FOLI_INC = '/Project/Terrain/Foliage.ush'   # round 2: LOD bands + the browser's clump-crown / leaf-card shaders (hand-written, committed)


def materials(pm):
    """pm: pathmask.json (x0, z0, w_m, h_m of the path-mask rectangle, browser metres)"""
    consts = 'float2 mo = float2(%.4f, %.4f); float2 ms = float2(%.4f, %.4f);' % (pm['x0'], pm['z0'], pm['w_m'], pm['h_m'])
    BASE = [('', 3, 'MP_BASE_COLOR'), ('Rough', 1, 'MP_ROUGHNESS'), ('NormalW', 3, 'MP_NORMAL')]
    M = []
    # park ground: the browser's park lawn shader (meadows / groves / ball fields / pond banks / Reservoir track / schist) + the path overlay and the dark park drives
    # (the browser draws the paths as alpha-blended ribbons; here they are a baked mask so there is no z-fight and the edges stay soft)
    M.append(dict(name='M_TerrainPark', include=LAWN_INC, code='''
float r; float3 n;
float2 p = wpos.xy * 0.01;
float3 c = TerrainParkEntry(tCol, tColSampler, tNoise, tNoiseSampler, wpos, 0.0, r, n);
c = TerrainLawnR4(tCol, tColSampler, tDet, tDetSampler, tNoise, tNoiseSampler, p, c, grade, lk, length(wpos - cam) * 0.01);   // r04: lawn grade (blue ~0), 0.3-16 m albedo detail (mottling, wear, clover, mowing stripes), saturation
''' + consts + '''
float4 pm = Texture2DSample(tPath, tPathSampler, (p - mo) / ms);
float3 n1 = Texture2DSample(tNoise, tNoiseSampler, fl2(p / 9.0)).rgb;
float3 n2 = Texture2DSample(tNoise, tNoiseSampler, fl2(p / 2.3)).rgb;
float e = pm.r * 0.5;
float edge = smoothstep(0.02, 0.2 + 0.12 * n1.r, e + 0.08 * (n2.g - 0.5)) * smoothstep(0.0, 0.6, pm.g);
float3 pc = Texture2DSample(tAsph, tAsphSampler, fl2(p / 4.0)).rgb * float3(0.7157, 0.6514, 0.5395);
pc *= lerp(float3(1.0, 1.0, 1.0), float3(1.08, 1.0, 0.86), n1.b) * (0.9 + 0.2 * n2.r);
pc = lerp(pc, float3(0.4, 0.38, 0.34) * (0.9 + 0.2 * n1.r), 0.45);
float4 dg = Texture2DSample(tDet, tDetSampler, p / 0.55);   // r04: gravel / asphalt grain (the path read as a flat smooth band at eye level)
float4 dg2 = Texture2DSample(tDet, tDetSampler, lwRot(p, 1.1) / 2.3 + float2(0.5, 0.2));
pc *= (0.8 + 0.4 * dg.a) * (0.86 + 0.28 * dg2.r) * (0.94 + 0.12 * dg.r);
c = lerp(c, pc, edge);
float dr = smoothstep(0.35, 0.65, pm.b);
c = lerp(c, float3(0.0742, 0.0704, 0.0648) * (0.9 + 0.2 * n2.r) * (0.82 + 0.36 * dg.a), dr);
r = lerp(r, 0.9, max(edge, dr));
float Lk = dot(c, float3(0.2126, 0.7152, 0.0722));   // soft luma knee: sunlit light gravel must not clip under the golden rig (same idea as the city sidewalk's SunK)
c *= lerp(1.0, min(1.0, (0.30 + (Lk - 0.30) * 0.3) / max(Lk, 0.0001)), step(0.30, Lk));
Rough = r; NormalW = lerp(lwTurfNormal(n, sun, tilt), float3(0.0, 0.0, 1.0), max(edge, dr)); Spec = lerp(0.04, 0.25, max(edge, dr)); AO = skyocc; return min(c * gain * sungain, float3(0.9, 0.9, 0.9));   // r05: AO = sky / bounce share, albedo x sungain (LAWN_SKYOCC)   // r04: Spec 0.04 on turf (UE default 0.5: at the p10 eye height (73 deg incidence) the Fresnel term mirrored the sky: display blue 49 on a lawn whose albedo blue is 0.004)''',
        inputs=[('tCol', 'tex', 'grass_col'), ('tNoise', 'tex', 'noise'), ('tAsph', 'tex', 'asphalt_col'), ('tPath', 'tex', 'pathmask'), ('tDet', 'tex', 'lawn_detail'), ('wpos', 'wpos', None), ('cam', 'cam', None), ('gain', 'scalar', 1.0), ('grade', 'vector', LAWN_GRADE), ('lk', 'vector', LAWN_K), ('skyocc', 'scalar', LAWN_SKYOCC), ('sungain', 'scalar', LAWN_SUNGAIN), ('sun', 'sun', 0), ('tilt', 'scalar', LAWN_TILT)], outputs=BASE + [('Spec', 1, 'MP_SPECULAR'), ('AO', 1, 'MP_AMBIENT_OCCLUSION')]))
    # coast / plaza lawns: the same lawn shader, lawn variant (meadow everywhere, no ball fields / ponds / woodland floor)
    M.append(dict(name='M_TerrainLawn', include=LAWN_INC, code='''
float r; float3 n;
float2 p = wpos.xy * 0.01;
float3 c = TerrainParkEntry(tCol, tColSampler, tNoise, tNoiseSampler, wpos, 1.0, r, n);
c = TerrainLawnR4(tCol, tColSampler, tDet, tDetSampler, tNoise, tNoiseSampler, p, c, grade, lk, length(wpos - cam) * 0.01);
Rough = r; NormalW = lwTurfNormal(n, sun, tilt); Spec = 0.04; AO = skyocc; return min(c * gain * sungain, float3(0.9, 0.9, 0.9));''',
        inputs=[('tCol', 'tex', 'grass_col'), ('tNoise', 'tex', 'noise'), ('tDet', 'tex', 'lawn_detail'), ('wpos', 'wpos', None), ('cam', 'cam', None), ('gain', 'scalar', 1.0), ('grade', 'vector', LAWN_GRADE), ('lk', 'vector', LAWN_K), ('skyocc', 'scalar', LAWN_SKYOCC), ('sungain', 'scalar', LAWN_SUNGAIN), ('sun', 'sun', 0), ('tilt', 'scalar', LAWN_TILT)], outputs=BASE + [('Spec', 1, 'MP_SPECULAR'), ('AO', 1, 'MP_AMBIENT_OCCLUSION')]))
    # City Hall Park / Bowling Green / Battery lawns (ground.js 'mapLawns': grass_col at 7 m x tint 0xb4b89a)
    M.append(dict(name='M_TerrainMapLawn', include=None, code='''
float2 p = wpos.xy * 0.01;
float3 c = Texture2DSample(tCol, tColSampler, float2(p.x / 7.0, 1.0 - p.y / 7.0)).rgb * float3(0.4564, 0.4793, 0.3231) * (0.85 + 0.3 * Texture2DSample(tNoise, tNoiseSampler, float2(p.x / 53.0, 1.0 - p.y / 53.0)).r);
Rough = 0.95; NormalW = float3(0.0, 0.0, 1.0); return c * gain;''',
        inputs=[('tCol', 'tex', 'grass_col'), ('tNoise', 'tex', 'noise'), ('wpos', 'wpos', None), ('gain', 'scalar', 1.0)], outputs=BASE))
    # still tannin-green pond / Reservoir water (browser: createRiverMaterial body (0.045, 0.06, 0.05), roughness 0.06): glossy, two drifting normal layers
    M.append(dict(name='M_TerrainPond', include=None, code='''
float2 p = wpos.xy * 0.01;
float2 q1 = p / 7.0 + float2(0.011, 0.007) * t;
float2 q2 = p / 2.3 - float2(0.013, 0.009) * t;
float3 a = Texture2DSample(tNrm, tNrmSampler, q1).rgb * 2.0 - 1.0;
float3 b = Texture2DSample(tNrm, tNrmSampler, q2).rgb * 2.0 - 1.0;
float2 d = (a.xy + b.xy) * 0.5 * 0.28;
Rough = 0.05; NormalW = normalize(float3(d.x, d.y, 1.0)); Spec = 0.25;   // r05: water F0 0.02 (UE default Specular 0.5 = F0 0.04 mirrored the pale golden sky: the p3 Lake read as white blobs, luma > 190)
return float3(0.045, 0.06, 0.05) * gain;''',
        inputs=[('tNrm', 'tex', 'water_nrm'), ('wpos', 'wpos', None), ('t', 'time', None), ('gain', 'scalar', 1.0)], outputs=BASE + [('Spec', 1, 'MP_SPECULAR')]))
    # vertex-coloured / flat-coloured furniture (benches, lamps, fences, posts, coping)
    for nm, two in (('M_TerrainVC', False), ('M_TerrainVC2', True)):
        M.append(dict(name=nm, include=None, code='''
float3 c = lerp(tint.rgb, vc.rgb * tint.rgb, usevc);
float3 pw = wpos * 0.01;
float g1 = Texture2DSample(tNoise, tNoiseSampler, float2(pw.x * 0.9 + pw.z * 2.3, pw.y * 7.0 + pw.z * 0.4)).r;   // r04: wood grain / paint wear (the flat tint read as a flat quad on the t4 lawn)
float g2 = Texture2DSample(tNoise, tNoiseSampler, float2(pw.x * 0.31 + pw.y * 0.27, pw.y * 0.29 - pw.z * 0.8)).g;
c *= 0.8 + 0.28 * g1 + 0.2 * (g2 - 0.5);
Rough = roughp; Metal = metalp; return c;''',
            inputs=[('vc', 'vc', None), ('tNoise', 'tex', 'noise'), ('wpos', 'wpos', None), ('tint', 'vector', (1, 1, 1, 1)), ('usevc', 'scalar', 0.0), ('roughp', 'scalar', 0.8), ('metalp', 'scalar', 0.0)],
            outputs=[('', 3, 'MP_BASE_COLOR'), ('Rough', 1, 'MP_ROUGHNESS'), ('Metal', 1, 'MP_METALLIC')], two_sided=two))
    # r04 schist outcrops / bank rocks: the vertex colour (0.46, 0.44, 0.40 x 0.7-1.2) went white under the golden sun (critic r3: 'white lumps' at the pond banks, p3). Darker grey-brown stone, triplanar
    # (the mesh has no UVs) albedo texture at 0.4 / 1.9 / 7 m, foliation joints, dark crevices on the steep faces, a little moss on the up-facing parts.
    M.append(dict(name='M_TerrainRock', include=None, code='''
float3 pw = wpos * 0.01;
float3 an = abs(wn); an = an / max(an.x + an.y + an.z, 0.001);
float4 a1 = Texture2DSample(tNoise, tNoiseSampler, pw.yz / 1.9) * an.x + Texture2DSample(tNoise, tNoiseSampler, pw.xz / 1.9) * an.y + Texture2DSample(tNoise, tNoiseSampler, pw.xy / 1.9) * an.z;
float4 a2 = Texture2DSample(tNoise, tNoiseSampler, pw.yz / 0.43) * an.x + Texture2DSample(tNoise, tNoiseSampler, pw.xz / 0.43) * an.y + Texture2DSample(tNoise, tNoiseSampler, pw.xy / 0.43) * an.z;
float4 a3 = Texture2DSample(tNoise, tNoiseSampler, pw.yz / 7.0) * an.x + Texture2DSample(tNoise, tNoiseSampler, pw.xz / 7.0) * an.y + Texture2DSample(tNoise, tNoiseSampler, pw.xy / 7.0) * an.z;
float3 c = lerp(vc.rgb, dot(vc.rgb, float3(0.3, 0.59, 0.11)).xxx, 0.6) * 0.32;   // r05: greyer schist (r04 read dark brown), a touch lighter   // hold W (0.5 x vc, albedo ~0.2): the sunlit blocks still read pale (display luma 160-210 at the p3 / t5 pond banks); schist is ~0.1-0.12
c *= (0.55 + 0.9 * a1.r) * (0.78 + 0.5 * a2.g) * (0.82 + 0.36 * a3.b);
float jn = frac((pw.x * 0.8 + pw.y * 0.6 + pw.z * 1.3) / 1.7 + a1.g * 1.4);
c *= 1.0 - 0.5 * smoothstep(0.55, 0.64, jn) * (1.0 - smoothstep(0.64, 0.72, jn));                       // foliation joints
c *= 1.0 - 0.4 * smoothstep(0.62, 0.8, a2.b) * (1.0 - saturate(wn.z));                                   // dark crevices on steep faces
float up = saturate(wn.z);
c = lerp(c, float3(0.07, 0.095, 0.03) * (0.7 + 0.6 * a2.r), smoothstep(0.5, 0.78, a1.b * 0.6 + a3.r * 0.4) * up * 0.55);   // moss
Rough = 0.92; return c;''',
        inputs=[('vc', 'vc', None), ('wn', 'wn', None), ('tNoise', 'tex', 'noise'), ('wpos', 'wpos', None)],
        outputs=[('', 3, 'MP_BASE_COLOR'), ('Rough', 1, 'MP_ROUGHNESS')]))
    # r04 blade turf (replaces the 9-blade star-sprite tuft): patches of ~600 blades (tools/terrain/prep_lawn.py), per-blade colour from the vertex colour (R height along the blade,
    # G blade random, B clump random), dark root -> saturated yellow-green tip, two-sided foliage (light through the blades), the blades shrink to the ground between fade0 and fade1 metres
    # (no pop at the instance cull distance), wind sways the tips. Lumen / ray tracing never see these pools (HWRT would treat every blade as a shell, see build_terrain.py).
    M.append(dict(name='M_TerrainGrass', include=None, code='''
float2 p = wpos.xy * 0.01;
float h = vc.r;
float dist = length(wpos - cam) * 0.01;
float fade = saturate((dist - near0) / max(near1 - near0, 0.001)) * (1.0 - smoothstep(fade0, fade1, dist));   // grows in between near0 / near1 metres (far layer: no tall tufts at the hero's feet), shrinks out between fade0 / fade1
float wo = 6.2831 * (0.5 + 0.5 * sin(p.x * 0.35 + p.y * 0.27)) + vc.g * 5.0;
float gust = 0.5 + 0.5 * sin(p.x * 0.1 - t * 0.5) * cos(p.y * 0.08);
float sway = h * h * windamp * (0.4 + 0.9 * gust) * sin(t * 1.6 + wo);
Wpo = float3(sway, sway * 0.7, -(wpos.z - rootz) * (1.0 - fade) - 1.5 * (1.0 - fade));
float3 tip = float3(0.26, 0.35, 0.007);   // r05: R x1.53 (r04 critic: p10 R / G 0.77 = lime; meadow reference 0.88; test holds: x1.35 -> 0.80, x1.75 -> 1.00)
float3 mid = float3(0.16, 0.225, 0.0045);
float3 root = float3(0.041, 0.06, 0.0025);
float3 g = lerp(lerp(root, mid, smoothstep(0.0, 0.45, h)), tip, smoothstep(0.35, 1.0, h));
float3 yel = float3(0.29, 0.32, 0.014);
g = lerp(g, yel * lerp(0.35, 1.0, h), saturate((vc.b - 0.62) * 3.0) * 0.8);
g *= lerp(0.72, 1.28, vc.g) * lerp(0.9, 1.1, rnd);
g = lerp(g, float3(0.3, 0.23, 0.05) * lerp(0.4, 1.0, h), step(0.988, vc.g) * 0.85);
AO = lerp(0.3, 1.0, smoothstep(0.0, 0.6, h));
Sub = g * 0.55;
Rough = 0.8; Spec = 0.05; NormalW = normalize(lerp(wn, float3(0.0, 0.0, 1.0), 0.4));
return g * gain;''',
        inputs=[('vc', 'vc', None), ('wn', 'wn', None), ('wpos', 'wpos', None), ('cam', 'cam', None), ('t', 'time', None), ('rnd', 'pir', None), ('windamp', 'scalar', 2.0), ('gain', 'scalar', 1.0),
                ('fade0', 'scalar', 12.0), ('fade1', 'scalar', 17.5), ('near0', 'scalar', 0.0), ('near1', 'scalar', 0.0), ('rootz', 'scalar', 19.0)],
        outputs=BASE + [('AO', 1, 'MP_AMBIENT_OCCLUSION'), ('Sub', 3, 'MP_SUBSURFACE_COLOR'), ('Spec', 1, 'MP_SPECULAR'), ('Wpo', 3, 'MP_WORLD_POSITION_OFFSET')], two_sided=True, foliage=True))
    # r04 picnic blankets: woven gingham (256^2 tile = 0.24 m), fringed ends (masked comb), fold shading (world-space wrinkle normal); replaces the flat M_TerrainVC2 tints (critic r3: pale / maroon slabs)
    M.append(dict(name='M_TerrainBlanket', include=None, code='''
float2 t2 = float2(uv0.x * 7.5, uv0.y * 6.25);
float4 wv = Texture2DSample(tWeave, tWeaveSampler, t2);
float3 pw = wpos * 0.01;
float a1 = pw.x * 5.3 + 1.7 * sin(pw.y * 3.1); float b1 = pw.y * 7.9 - pw.x * 2.3;
float fx = 0.5 * 5.3 * cos(a1) - 0.3 * 2.3 * cos(b1);
float fy = 0.5 * cos(a1) * 1.7 * 3.1 * cos(pw.y * 3.1) + 0.3 * 7.9 * cos(b1);
float top = step(0.5, wn.z);
float3 nf = normalize(float3(-fx * 0.05, -fy * 0.05, 1.0));
NormalW = lerp(wn, nf, top);
float3 col = lerp(tintA, tintB, wv.g) * (0.74 + 0.4 * wv.r) * (0.9 + 0.2 * wv.b);
col *= 0.9 + 0.1 * cos(a1);
float eu = min(uv0.x, 1.0 - uv0.x) * 1.8;
float cell = floor(uv0.y * 1.5 / 0.007);
float hl = 0.014 + 0.026 * frac(sin(cell * 12.9898) * 43758.5453);
float strand = step(0.4, frac(uv0.y * 1.5 / 0.007));
float inFr = step(eu, 0.04);
Op = lerp(1.0, strand * step(0.04 - eu, hl), inFr * top);
Rough = 0.92;
return lerp(col * 0.6, col, top) * gain;''',
        inputs=[('tWeave', 'tex', 'blanket_weave'), ('uv0', 'uv', 0), ('wn', 'wn', None), ('wpos', 'wpos', None), ('tintA', 'vector', (0.5, 0.45, 0.35, 1)), ('tintB', 'vector', (0.3, 0.05, 0.04, 1)), ('gain', 'scalar', 1.0)],
        outputs=[('', 3, 'MP_BASE_COLOR'), ('Op', 1, 'MP_OPACITY_MASK'), ('Rough', 1, 'MP_ROUGHNESS'), ('NormalW', 3, 'MP_NORMAL')], two_sided=True, blend='masked'))
    # ez-tree leaf cards (eztrees.js ezLeafMaterial): the photo spray becomes a value map + twig mask, recoloured per instance with the autumn palette (aTintA -> aTintB,
    # custom data 0..2 / 3..5), crown self-occlusion from the per-leaf exposure (uv1.x), the odd dry brown spray; two-sided foliage (light passes through the leaves)
    M.append(dict(name='M_TerrainLeaves', include=FOLI_INC, code='''
float4 tx = Texture2DSample(tLeaf, tLeafSampler, float2(uv0.x, 1.0 - uv0.y));
float lum = dot(tx.rgb, float3(0.3, 0.59, 0.11));
float twig = 1.0 - smoothstep(-0.03, 0.02, tx.g - max(tx.r, tx.b) - 0.015);
float hsel = uv1.y * 0.7 + lum * 0.6 - 0.2;
float3 leaf = lerp(tfSummer(float3(a0, a1, a2)), tfSummer(float3(b0, b1, b2)), smoothstep(0.15, 0.85, hsel));   // r05 summer palette (Foliage.ush tfSummer)
float odd = frac(uv1.y * 13.7);
leaf = lerp(leaf, float3(0.13, 0.06, 0.025), step(0.98, odd));
leaf *= 0.5 + 1.25 * lum;
float expo = saturate(uv1.x);
float occ = lerp(0.36, 1.05, pow(expo, 1.3));
float3 c = lerp(leaf, float3(0.085, 0.06, 0.042), twig) * occ * gain * lerp(1.0, leafk, saturate(nightk));   // night: dark soft canopy (MPC LeafNightK), albedo and transmission
float bnd = tfBand(length(wpos - cam) * 0.01f, band, Parameters.SvPosition.xy, t);   // r02: the ez-tree LOD band (L0 < 20 m, L1 20-44 m): UE drew L1 out to 520 m
float eb = min(min(uv0.x, 1.0 - uv0.x), min(uv0.y, 1.0 - uv0.y));   // r03 pass 2: ragged quad borders (straight leaf-card edges against the sky in p10)
Op = tx.a * bnd * smoothstep(0.0, 0.07, eb + 0.04 * (lum - 0.5)); Sub = c * 0.85; Rough = 0.78;
float dcam = length(wpos - cam) * 0.01;
AO = lerp(0.7, 1.0, expo);   // r03: sky light through the leaf exposure (Lumen indirect / sky only; the sun is untouched)
Emis = c * fill * tfFillW(expo, wn, sun, dcam) * (1.0 - saturate(nightk));   // x (1 - NightK): this day fill (FILL cd/m2 per unit albedo) is 650 cd/m2 x albedo, ~12 display units at the night exposure (EV 5.5)   // r03: the r02 constant fill (c * 1800 * (0.4 + 0.6 expo)) is gone; residual fill only in shade, 0 within 10 m (Foliage.ush tfFillW). Units: sunlit albedo A radiates ~10000 A cd/m2 under the golden rig
return c;''',
        inputs=[('tLeaf', 'texparam', 'leaf_oak'), ('uv0', 'uv', 0), ('uv1', 'uv', 1), ('a0', 'pcd', 0), ('a1', 'pcd', 1), ('a2', 'pcd', 2), ('b0', 'pcd', 3), ('b1', 'pcd', 4), ('b2', 'pcd', 5),
                ('wpos', 'wpos', None), ('cam', 'cam', None), ('band', 'vector', (0, 0, 0, 0)), ('t', 'time', None), ('gain', 'scalar', 1.0),
                ('wn', 'wn', None), ('sun', 'sun', 0), ('fill', 'scalar', FILL), ('nightk', 'mpc', 'NightK'), ('leafk', 'mpc', 'LeafNightK')],
        outputs=[('', 3, 'MP_BASE_COLOR'), ('Op', 1, 'MP_OPACITY_MASK'), ('Sub', 3, 'MP_SUBSURFACE_COLOR'), ('Rough', 1, 'MP_ROUGHNESS'), ('Emis', 3, 'MP_EMISSIVE_COLOR'), ('AO', 1, 'MP_AMBIENT_OCCLUSION')], two_sided=True, blend='masked', foliage=True, nanite=True))
    # ez-tree bark / park trunks (vertex colour = ambient occlusion, flat bark tint) with the same LOD band clip
    M.append(dict(name='M_TerrainBark', include=FOLI_INC, code='''
float3 c = lerp(tint.rgb, vc.rgb * tint.rgb, usevc);
// r05 bark (r04 critic: t4 passes untextured trunks 320-460 px wide): vertical furrows + ridges + fine grain, projected on the two horizontal axes by the normal
float3 pw = wpos * 0.01f;
float2 an = abs(wn.xy) / max(abs(wn.x) + abs(wn.y), 0.001f);
float hu = pw.y * an.x + pw.x * an.y;
float f1 = Texture2DSample(tNoise, tNoiseSampler, float2(hu * 3.1f, pw.z * 0.32f)).r;
float f2 = Texture2DSample(tNoise, tNoiseSampler, float2(hu * 9.0f + 0.37f, pw.z * 1.3f)).g;
float f3 = Texture2DSample(tNoise, tNoiseSampler, float2(hu * 23.0f, pw.z * 6.0f + 0.5f)).b;
float furrow = smoothstep(0.3f, 0.7f, f1 * 0.65f + f2 * 0.35f);
c *= (0.42f + 0.85f * furrow) * (0.85f + 0.3f * f3);
c = lerp(c, c * float3(0.75f, 0.85f, 0.6f), smoothstep(0.62f, 0.8f, f2) * 0.5f);   // lichen / moss tint in a few ridges
Op = tfBand(length(wpos - cam) * 0.01f, band, Parameters.SvPosition.xy, t);
Rough = roughp; return c;''',
        inputs=[('vc', 'vc', None), ('tint', 'vector', (0.33, 0.29, 0.25, 1)), ('usevc', 'scalar', 1.0), ('roughp', 'scalar', 0.92), ('wpos', 'wpos', None), ('cam', 'cam', None),
                ('band', 'vector', (0, 0, 0, 0)), ('t', 'time', None), ('wn', 'wn', None), ('tNoise', 'tex', 'noise')],
        outputs=[('', 3, 'MP_BASE_COLOR'), ('Op', 1, 'MP_OPACITY_MASK'), ('Rough', 1, 'MP_ROUGHNESS')], blend='masked', nanite=True))
    # near leaf-card canopies (browser pool `trees-*-near`, 44-165 m, casts shadows): the city's leaf atlas + the lobe-fitted card / core geometry, per-instance autumn tints
    M.append(dict(name='M_TerrainCards', include=FOLI_INC, code='''
float op; float3 sub;
float3 c = TerrainLeafCards(tAtlas, tAtlasSampler, uv0, uv1, float3(a0, a1, a2), float3(b0, b1, b2), wn, wpos, cam, band, Parameters.SvPosition.xy, t, op, sub);
float lnk = lerp(1.0, leafk, saturate(nightk));   // night: dark soft canopy (MPC LeafNightK)
Op = op; Sub = sub * gain * lnk; Rough = 0.78;
float ex = saturate(uv1.x >= 1.5 ? uv1.x - 2.0 : uv1.x);
AO = lerp(0.7, 1.0, ex);   // r03: sky light through the card exposure
Emis = c * gain * fill * tfFillW(ex, wn, sun, length(wpos - cam) * 0.01) * (1.0 - saturate(nightk));   // x (1 - NightK), see M_TerrainLeaves   // r03: shade- and distance-weighted residual fill (was the constant c * 1800 * (0.4 + 0.6 ex))
return c * gain * lnk;''',
        inputs=[('tAtlas', 'tex', 'leaf_atlas'), ('uv0', 'uv', 0), ('uv1', 'uv', 1), ('a0', 'pcd', 0), ('a1', 'pcd', 1), ('a2', 'pcd', 2), ('b0', 'pcd', 3), ('b1', 'pcd', 4), ('b2', 'pcd', 5),
                ('wn', 'wn', None), ('wpos', 'wpos', None), ('cam', 'cam', None), ('band', 'vector', (0, 0, 0, 0)), ('t', 'time', None), ('gain', 'scalar', 1.0),
                ('sun', 'sun', 0), ('fill', 'scalar', FILL), ('nightk', 'mpc', 'NightK'), ('leafk', 'mpc', 'LeafNightK')],
        outputs=[('', 3, 'MP_BASE_COLOR'), ('Op', 1, 'MP_OPACITY_MASK'), ('Sub', 3, 'MP_SUBSURFACE_COLOR'), ('Rough', 1, 'MP_ROUGHNESS'), ('Emis', 3, 'MP_EMISSIVE_COLOR'), ('AO', 1, 'MP_AMBIENT_OCCLUSION')], two_sided=True, blend='masked', foliage=True))
    # lumpy clump crowns (browser pool `trees-*-crown`; r03: drawn only >= 520 m, the 165-520 m band is the leaf-card LOD1 `trees-*-lod1` on M_TerrainCards): procedural clumps of leaf speckle, ragged see-through silhouette, normal from the clump height field
    M.append(dict(name='M_TerrainClump', include=FOLI_INC, code='''
float op; float3 nW;
float3 c = TerrainClumpCrown(wpos, cam, wn, uv1, float3(a0, a1, a2), float3(b0, b1, b2), rnd, band, Parameters.SvPosition.xy, t, bump, op, nW);
Op = op; NormalW = nW; Rough = 0.88;
return c * gain;''',
        inputs=[('uv1', 'uv', 1), ('a0', 'pcd', 0), ('a1', 'pcd', 1), ('a2', 'pcd', 2), ('b0', 'pcd', 3), ('b1', 'pcd', 4), ('b2', 'pcd', 5), ('rnd', 'pir', None),
                ('wn', 'wn', None), ('wpos', 'wpos', None), ('cam', 'cam', None), ('band', 'vector', (0, 0, 0, 0)), ('t', 'time', None), ('gain', 'scalar', 1.0), ('bump', 'scalar', 1.0)],
        outputs=[('', 3, 'MP_BASE_COLOR'), ('Op', 1, 'MP_OPACITY_MASK'), ('Rough', 1, 'MP_ROUGHNESS'), ('NormalW', 3, 'MP_NORMAL')], blend='masked'))
    # far crowns: the city's opaque canopy-mass blobs. They are ONLY wanted beyond the ez-tree range (browser: 520 m); per-instance cull distances did not hide them in UE (v1 / v2 stills),
    # so the material clips them by camera distance (fade-in 480 .. 560 m) and tints them with the tree's own autumn palette (custom data = aTintA / aTintB)
    M.append(dict(name='M_TerrainCrown', include=FOLI_INC, code='''
float d = length(wpos - cam) * 0.01;
Op = tfBand(d, band, Parameters.SvPosition.xy, t);   // r02: the browser's dithered hand-over (crown -> crownfar over 478-520 m), nothing nearer
float nz = 0.5 + 0.5 * sin(wpos.x * 0.011 + 1.7 * sin(wpos.y * 0.0093)) * cos(wpos.y * 0.0127);
float3 c = lerp(tfSummer(float3(a0, a1, a2)), tfSummer(float3(b0, b1, b2)), 0.5) * lerp(0.7, 1.15, nz) * gain;   // r05 summer palette
Rough = 0.95;
return c;''',
        inputs=[('wpos', 'wpos', None), ('cam', 'cam', None), ('a0', 'pcd', 0), ('a1', 'pcd', 1), ('a2', 'pcd', 2), ('b0', 'pcd', 3), ('b1', 'pcd', 4), ('b2', 'pcd', 5),
                ('band', 'vector', (520, 3200, 0, 0)), ('t', 'time', None), ('gain', 'scalar', 1.0)],
        outputs=[('', 3, 'MP_BASE_COLOR'), ('Op', 1, 'MP_OPACITY_MASK'), ('Rough', 1, 'MP_ROUGHNESS')], blend='masked', nanite=True))
    return M

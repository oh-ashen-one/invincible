# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Piece P3 (traversal), round 25: /Game/Traversal/Materials/M_TravWeb -- the web strand look.
#
# Critic r24 biggest gap (SPEC T5 / T6): the rope must read on every web_on frame of the swing chain, 2-4 px wide, its mean luminance
# >= 25/255 off a 6 px band either side, over dark glass AND pale facades. History: r07 emissive beam bloomed, r08 pale lit line vanished on
# pale facades, r09-r24 dark lit line vanished on dark glass.
#
# M_TravWeb: an UNLIT, translucent (opacity 1 inside the strand, a soft half-pixel edge) two-tone strand on the cylinder segments the pawn
# draws (AWebTravCharacter::UpdateWebs). Across the strand the cylinder's view-facing coordinate u (0 at the centre line, 1 at the silhouette)
# picks a bright CORE (u < c) or a dark RIM. The core share c follows the luminance of the scene behind the strand, sampled UNIFORMLY for
# the whole strand (final round 13: 4 taps at two fixed screen points along the strand, 35 % / 70 % hand -> anchor, passed as the BgUV0 /
# BgUV1 vector params per strand per frame -- the r08-r12 per-pixel taps beaded / flickered against mixed facades, critic r12): over a dark
# background (glass, shadow) the bright core fills CoreDark of the width, over a bright one (sky, pale stone) only CoreBright and the dark
# rim carries the line; the step is biased BRIGHT (Pivot x 1.2-1.4) so every facade below a genuinely bright background gets the
# bright-carrying line (a mid plateau resolved the strand's mean to the facade's own level -- r13 build 2). The output is divided by the
# eye adaptation (EyeAdaptationInverse), so the displayed level is CoreLvl / RimLvl whatever the exposure: no HDR emissive, no bloom.
# No fog on the strand (Apply Fogging off), responsive AA (thin moving line), not lit, casts no shadow (set on the component).
#
# Run from build_traversal.py (materials section), or alone as a commandlet with your editor closed:
#   UnrealEditor <abs uproject> -run=pythonscript -script=<abs path to this file> -unattended -nullrhi
import os
import unreal

MAT_DIR = "/Game/Traversal/Materials"
NAME = "M_TravWeb"

WEB_CODE = r"""
float3 a = normalize(A);
float3 v = normalize(V);
float3 vp = v - a * dot(v, a);
float lv = length(vp);
float u = 0.0;
if (lv > 1e-3)
{
	vp /= lv;
	float nv = saturate(abs(dot(normalize(N), vp)));
	u = sqrt(saturate(1.0 - nv * nv));
}
float inv = max(Inv.x, 1e-8);
// final round 13 (critic r12 gap 1, orchestrator-verified: the strand renders BEADED/DASHED in daylight -- s3 t=14.2, s4
// t=15.6-15.8): the r08 adaptation evaluated the background luminance PER PIXEL (4 taps ~5 px out of each fragment), so a
// checkerboard facade flipped the core share pixel-by-pixel into alternating dark/bright beads, and any background motion
// flickered the tone frame to frame. Now the taps sit at two FIXED points along the strand (35 % / 70 % hand -> anchor,
// passed per strand per frame as BgUV0 / BgUV1 vector parameters by AWebTravCharacter::UpdateWebs): lb is one value for
// every fragment of the strand, so the tone is UNIFORM hand -> anchor and evolves smoothly (no dashes, no flicker).
float lb = dot((S0.rgb + S1.rgb + S2.rgb + S3.rgb) * 0.25, float3(0.2126, 0.7152, 0.0722)) / inv;
// the core share is binary in the strand-average lb, biased BRIGHT (step at Pivot x 1.2-1.4, displayed ~160-170): every facade
// below that gets the bright-carrying line (its mean ~230 sits >= 45 off both dark windows AND pale grid), only genuinely
// bright backgrounds (sky, sunlit stone) get the dark-carrying line. (r13 build 1's ~0.68 mid plateau resolved the strand's
// mean to ~126-150/255 over mid facades of 140-145 -- locally invisible.) lb is one value per strand, so the line is
// uniform hand -> anchor and flips polarity only as a whole, when its average background crosses the step
float dark = 1.0 - smoothstep(Pivot * 1.20, Pivot * 1.40, lb);
float c = lerp(CoreBright, CoreDark, dark);
float lvl;
if (Solid > 0.5)
{
	// build 2: ONE tone across the whole strand -- bright over a dark background, near-black over a bright one
	lvl = lerp(RimLvl, CoreLvl, dark);
}
else
{
	float core = 1.0 - smoothstep(c - 0.05, c + 0.05, u);
	lvl = lerp(RimLvl, CoreLvl, core);
}
float alpha = 1.0 - smoothstep(0.92, 1.0, u);
// build 2: the strand draws after motion blur (no engine depth test there) -- test against the opaque scene depth by hand
alpha *= (SD < PD - Occ) ? 0.0 : 1.0;
return float4(lvl, lvl, lvl, alpha);
"""

PARAMS = [("CoreBright", 0.15), ("CoreDark", 0.90), ("Pivot", 0.30), ("CoreLvl", 1.15), ("RimLvl", 0.03), ("Solid", 0.0), ("Occ", 45.0)]


FAILED = []   # strict mode (SM2_STRICT=1): properties that could not be set; the calling build reports them


def _set(obj, prop, value):
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception as e:  # noqa: BLE001 -- report and go on (an engine-version property rename must not abort the content build)
        unreal.log_warning(f"TRAVWEB: could not set {prop} on {obj.get_name()}: {e}")
        if os.environ.get('SM2_STRICT') == '1':
            FAILED.append(f"TRAVWEB {prop} on {obj.get_name()}")
        return False


def build(eal=None, mel=None, tools=None):
    eal = eal or unreal.EditorAssetLibrary
    mel = mel or unreal.MaterialEditingLibrary
    tools = tools or unreal.AssetToolsHelpers.get_asset_tools()
    path = f"{MAT_DIR}/{NAME}"
    if not eal.does_directory_exist(MAT_DIR):
        eal.make_directory(MAT_DIR)
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    m = tools.create_asset(NAME, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    _set(m, "blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    _set(m, "shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    # build 2: after motion blur -- before DOF the camera-speed blur of the background smeared the 3 px strand into it
    if not _set(m, "translucency_pass", unreal.MaterialTranslucencyPass.MTP_AFTER_MOTION_BLUR):
        _set(m, "translucency_pass", unreal.MaterialTranslucencyPass.MTP_BEFORE_DOF)
    _set(m, "use_translucency_vertex_fog", False)   # "Apply Fogging"
    _set(m, "enable_responsive_aa", True)
    _set(m, "two_sided", False)

    def expr(cls, x, y):
        return mel.create_material_expression(m, cls, x, y)

    nrm = expr(unreal.MaterialExpressionVertexNormalWS, -1200, -300)
    cam = expr(unreal.MaterialExpressionCameraVectorWS, -1200, -180)
    zc = expr(unreal.MaterialExpressionConstant3Vector, -1400, -60)
    _set(zc, "constant", unreal.LinearColor(0.0, 0.0, 1.0, 0.0))
    ax = expr(unreal.MaterialExpressionTransform, -1200, -60)
    _set(ax, "transform_source_type", unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL)
    _set(ax, "transform_type", unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
    mel.connect_material_expressions(zc, "", ax, "")
    # final round 13: background taps at two FIXED screen points along the strand (BgUV0 / BgUV1 vector params, set per
    # strand per frame from C++) instead of 4 per-pixel offsets -- the tone is uniform over the whole strand (the per-pixel
    # taps beaded / flickered, critic r12). The SceneColor nodes keep OFFSET_FRACTION mode: feeding (BgUVn - ScreenPosition)
    # as the offset lands the sample exactly on BgUVn.
    spos = expr(unreal.MaterialExpressionScreenPosition, -1600, 300)
    uvp = []
    for i, n in enumerate(("BgUV0", "BgUV1")):
        vp = expr(unreal.MaterialExpressionVectorParameter, -1600, 420 + i * 130)
        _set(vp, "parameter_name", n)
        _set(vp, "default_value", unreal.LinearColor(0.4 + 0.2 * i, 0.5, 0.0, 0.0))
        rg = expr(unreal.MaterialExpressionComponentMask, -1400, 420 + i * 130)
        _set(rg, "r", True); _set(rg, "g", True); _set(rg, "b", False); _set(rg, "a", False)
        mel.connect_material_expressions(vp, "", rg, "")
        uvp.append(rg)
    # taps: at BgUV0 (+0 / +0.006 x), at BgUV1 (+0 / -0.006 x) -- a 4-tap average around the two strand points
    taps = []
    for i, (k, ox) in enumerate(((0, 0.0), (0, 0.006), (1, 0.0), (1, -0.006))):
        off = expr(unreal.MaterialExpressionConstant, -1400, 700 + i * 90)
        _set(off, "r", ox)
        app = expr(unreal.MaterialExpressionAppendVector, -1250, 700 + i * 90)
        mel.connect_material_expressions(off, "", app, "A")
        z0 = expr(unreal.MaterialExpressionConstant, -1400, 760 + i * 90)
        mel.connect_material_expressions(z0, "", app, "B")
        add = expr(unreal.MaterialExpressionAdd, -1100, 700 + i * 90)
        mel.connect_material_expressions(uvp[k], "", add, "A")
        mel.connect_material_expressions(app, "", add, "B")
        sub = expr(unreal.MaterialExpressionSubtract, -950, 700 + i * 90)
        mel.connect_material_expressions(add, "", sub, "A")
        mel.connect_material_expressions(spos, "", sub, "B")
        sc = expr(unreal.MaterialExpressionSceneColor, -1200, 850 + i * 90)
        _set(sc, "input_mode", unreal.MaterialSceneAttributeInputMode.OFFSET_FRACTION)
        mel.connect_material_expressions(sub, "", sc, "")
        taps.append(sc)
    inv = expr(unreal.MaterialExpressionEyeAdaptationInverse, -1200, 600)
    sd = expr(unreal.MaterialExpressionSceneDepth, -1200, 1500)
    pd = expr(unreal.MaterialExpressionPixelDepth, -1200, 1600)
    pars = {}
    for i, (n, d) in enumerate(PARAMS):
        p = expr(unreal.MaterialExpressionScalarParameter, -1200, 720 + i * 90)
        _set(p, "parameter_name", n)
        _set(p, "default_value", d)
        pars[n] = p
    cu = expr(unreal.MaterialExpressionCustom, -700, 0)
    _set(cu, "code", WEB_CODE)
    _set(cu, "output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    names = ["N", "V", "A", "S0", "S1", "S2", "S3", "Inv", "SD", "PD"] + [n for n, _ in PARAMS]
    ins = []
    for n in names:
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", n)
        ins.append(ci)
    _set(cu, "inputs", ins)
    ok = True
    ok &= mel.connect_material_expressions(nrm, "", cu, "N")
    ok &= mel.connect_material_expressions(cam, "", cu, "V")
    ok &= mel.connect_material_expressions(ax, "", cu, "A")
    for i, sc in enumerate(taps):
        ok &= mel.connect_material_expressions(sc, "", cu, f"S{i}")
    ok &= mel.connect_material_expressions(inv, "", cu, "Inv")
    ok &= mel.connect_material_expressions(sd, "", cu, "SD")
    ok &= mel.connect_material_expressions(pd, "", cu, "PD")
    for n, p in pars.items():
        ok &= mel.connect_material_expressions(p, "", cu, n)
    rgb = expr(unreal.MaterialExpressionComponentMask, -450, 0)
    for c, v in (("r", True), ("g", True), ("b", True), ("a", False)):
        _set(rgb, c, v)
    al = expr(unreal.MaterialExpressionComponentMask, -450, 200)
    for c, v in (("r", False), ("g", False), ("b", False), ("a", True)):
        _set(al, c, v)
    ok &= mel.connect_material_expressions(cu, "", rgb, "")
    ok &= mel.connect_material_expressions(cu, "", al, "")
    # displayed level = CoreLvl / RimLvl at any exposure: divide by the eye adaptation
    inv2 = expr(unreal.MaterialExpressionEyeAdaptationInverse, -250, 0)
    ok &= mel.connect_material_expressions(rgb, "", inv2, "")
    ok &= mel.connect_material_property(inv2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    ok &= mel.connect_material_property(al, "", unreal.MaterialProperty.MP_OPACITY)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    unreal.log(f"TRAVWEB: built {path} connections_ok={bool(ok)} expressions={mel.get_num_material_expressions(m)} pass={m.get_editor_property('translucency_pass')}")
    return m


if __name__ == "__main__":
    build()

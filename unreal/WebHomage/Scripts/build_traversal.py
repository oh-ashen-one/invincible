# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Piece P3 (traversal + camera): rebuilds /Game/Traversal (materials) and /Game/Tests/Traversal/Trav_Canyon from scratch.
# Idempotent: deletes both folders first. Run headless with your own editor closed:
#   UnrealEditor <abs uproject> -run=pythonscript -script=<abs path to this file> -unattended -nullrhi
# Needs the WebHomage C++ module built (the map's World Settings use /Script/WebHomage.WebTravGameMode).
#
# Trav_Canyon: a 1.6 km avenue canyon along +X (building lines at y = +-15 m), 98 m blocks (80 m + 18 m cross streets),
# 80-300 m towers (about 40 % on 25-60 m podiums with a 10 m setback, so there are perchable roof edges), a second row of
# 40-150 m blocks behind a parallel street, water towers on low roofs. Deterministic (fixed seed).
import json
import math
import os
import random
import sys
import unreal

sys.path.insert(0, os.environ.get('SM2_SCRIPTS_DIR') or os.path.dirname(os.path.abspath(globals().get('__file__') or '.')))
import sm2_common
_B = sm2_common.Build('build_traversal.py')

MAT_DIR = "/Game/Traversal/Materials"
MAP_DIR = "/Game/Tests/Traversal"
MAP = MAP_DIR + "/Trav_Canyon"

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()

# Map packages are not removed by delete_directory in a commandlet: reuse the map (cleared) when it exists.
if eal.does_asset_exist(MAP):
    assert les.load_level(MAP), "load_level failed"
    for a in eas.get_all_level_actors():
        eas.destroy_actor(a)
    les.save_current_level()
    MAP_EXISTS = True
else:
    MAP_EXISTS = False
if eal.does_directory_exist("/Game/Traversal"):
    eal.delete_directory("/Game/Traversal")
eal.make_directory(MAT_DIR)
eal.make_directory(MAP_DIR)


# ------------------------------------------------------------------ materials
def new_material(name):
    return tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())


def custom_node(mat, code, inputs, out_type, x, y):
    c = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, x, y)
    c.set_editor_property("code", code)
    c.set_editor_property("output_type", out_type)
    ins = []
    for n in inputs:
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", n)
        ins.append(ci)
    c.set_editor_property("inputs", ins)
    return c


FACADE_COMMON = r"""
float3 p = WP / 100.0;
float3 o = floor(OP / 700.0);
float h = frac(sin(dot(o.xy, float2(12.9898, 78.233))) * 43758.5453);
float h2 = frac(h * 91.7);
float ax = abs(N.x) > abs(N.y) ? p.y : p.x;
float u = frac(ax / 3.4);
float v = frac(p.z / 3.9);
float win = step(0.16, u) * step(u, 0.84) * step(0.30, v) * step(v, 0.88);
if (abs(N.z) > 0.5 || p.z < 5.0) win = 0.0;
"""
FACADE_COLOR = FACADE_COMMON + r"""
float3 wall = lerp(float3(0.16, 0.14, 0.13), float3(0.45, 0.38, 0.30), h);
wall = lerp(wall, float3(0.12, 0.16, 0.20), step(0.72, h2));
wall = lerp(wall, float3(0.38, 0.20, 0.14), step(0.86, frac(h2 * 13.1)));
float lit = frac(sin(dot(floor(float2(ax / 3.4, p.z / 3.9)), float2(3.1, 17.7)) + h * 7.0) * 9173.1);
float3 glass = lerp(float3(0.02, 0.03, 0.045), float3(0.12, 0.15, 0.19), lit);
float3 c = lerp(wall, glass, win);
if (p.z < 5.0 && abs(N.z) < 0.5) c = lerp(float3(0.09, 0.09, 0.10), float3(0.34, 0.29, 0.21), step(0.5, frac(ax / 6.0)));
if (N.z > 0.5) c = wall * 0.55;
return c;
"""
FACADE_ROUGH = FACADE_COMMON + r"""
return lerp(0.85, 0.12, win);
"""

facade = new_material("M_TravFacade")
wp = mel.create_material_expression(facade, unreal.MaterialExpressionWorldPosition, -900, 0)
op = mel.create_material_expression(facade, unreal.MaterialExpressionObjectPositionWS, -900, 150)
nn = mel.create_material_expression(facade, unreal.MaterialExpressionVertexNormalWS, -900, 300)
fc = custom_node(facade, FACADE_COLOR, ["WP", "OP", "N"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, 0)
fr = custom_node(facade, FACADE_ROUGH, ["WP", "OP", "N"], unreal.CustomMaterialOutputType.CMOT_FLOAT1, -500, 250)
for node in (fc, fr):
    mel.connect_material_expressions(wp, "", node, "WP")
    mel.connect_material_expressions(op, "", node, "OP")
    mel.connect_material_expressions(nn, "", node, "N")
mel.connect_material_property(fc, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(fr, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.recompile_material(facade)

GROUND = r"""
float3 p = WP / 100.0;
float n = frac(sin(dot(floor(p.xy * 2.0), float2(12.9898, 78.233))) * 43758.5453);
float3 c = float3(0.045, 0.045, 0.05) + 0.015 * n;
float ay = abs(p.y);
if (ay > 11.0 && ay < 15.0) c = float3(0.27, 0.26, 0.25);
if (ay < 0.25 && ay > 0.08) c = float3(0.60, 0.45, 0.05);
float dash = step(0.5, frac(p.x / 9.0));
if (abs(ay - 3.6) < 0.08 || abs(ay - 7.2) < 0.08) c = lerp(c, float3(0.7, 0.7, 0.7), dash);
return c;
"""
ground_m = new_material("M_TravGround")
gwp = mel.create_material_expression(ground_m, unreal.MaterialExpressionWorldPosition, -700, 0)
gc = custom_node(ground_m, GROUND, ["WP"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -400, 0)
mel.connect_material_expressions(gwp, "", gc, "WP")
mel.connect_material_property(gc, "", unreal.MaterialProperty.MP_BASE_COLOR)
grough = mel.create_material_expression(ground_m, unreal.MaterialExpressionConstant, -400, 200)
grough.set_editor_property("r", 0.8)
mel.connect_material_property(grough, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.recompile_material(ground_m)

# M_TravColor: flat colour + emissive (placeholder hero, web strands). Params: Color (vector), Emissive (scalar).
color_m = new_material("M_TravColor")
cp = mel.create_material_expression(color_m, unreal.MaterialExpressionVectorParameter, -600, 0)
cp.set_editor_property("parameter_name", "Color")
cp.set_editor_property("default_value", unreal.LinearColor(0.8, 0.8, 0.8, 1.0))
ep = mel.create_material_expression(color_m, unreal.MaterialExpressionScalarParameter, -600, 200)
ep.set_editor_property("parameter_name", "Emissive")
ep.set_editor_property("default_value", 0.0)
mul = mel.create_material_expression(color_m, unreal.MaterialExpressionMultiply, -300, 200)
mel.connect_material_expressions(cp, "", mul, "A")
mel.connect_material_expressions(ep, "", mul, "B")
mel.connect_material_property(cp, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
crough = mel.create_material_expression(color_m, unreal.MaterialExpressionConstant, -300, 350)
crough.set_editor_property("r", 0.5)
mel.connect_material_property(crough, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.recompile_material(color_m)

for m in (facade, ground_m, color_m):
    eal.save_loaded_asset(m)

# round 25: M_TravWeb, the unlit two-tone web strand (traversal_web_material.py, also runnable alone)
import importlib, sys as _sys
_sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts"))  # (__file__ is unset under build_manhattan's exec wrapper)
import traversal_web_material
importlib.reload(traversal_web_material)
traversal_web_material.build(eal, mel, tools)
for _f in traversal_web_material.FAILED: _B.fail(_f)


# ------------------------------------------------------------------ HeroDev: dev proxy of the real hero (round 04)
# public/assets/spiderman.glb (58 bones, 79 clips at 30 fps) -> /Game/Traversal/HeroDev. P2 owns the final hero in
# /Game/Characters; bone and clip names are kept unchanged so the swap is a path change. Interchange's glTF reader does not
# support EXT_texture_webp, so the textures are converted to PNG (macOS sips) into Saved/ first.
import struct
import subprocess
import tempfile

def convert(src, dst):
    """Rewrite a GLB so every EXT_texture_webp image becomes an embedded PNG (sips), extension removed."""
    b = open(src, "rb").read()
    L = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + L])
    off = 20 + L
    BL = struct.unpack("<I", b[off:off + 4])[0]
    binc = b[off + 8: off + 8 + BL]
    views = j["bufferViews"]
    blobs = {i: binc[v.get("byteOffset", 0): v.get("byteOffset", 0) + v["byteLength"]] for i, v in enumerate(views)}
    tmp = tempfile.mkdtemp()
    for ii, im in enumerate(j.get("images", [])):
        if im.get("mimeType") == "image/webp":
            wp, pp = os.path.join(tmp, "i%d.webp" % ii), os.path.join(tmp, "i%d.png" % ii)
            open(wp, "wb").write(blobs[im["bufferView"]])
            subprocess.run(["sips", "-s", "format", "png", wp, "--out", pp], check=True, capture_output=True)
            blobs[im["bufferView"]] = open(pp, "rb").read()
            im["mimeType"] = "image/png"
    for t in j.get("textures", []):
        ext = t.get("extensions", {}).pop("EXT_texture_webp", None)
        if ext is not None:
            t["source"] = ext["source"]
        if "extensions" in t and not t["extensions"]:
            del t["extensions"]
    for k in ("extensionsUsed", "extensionsRequired"):
        if k in j:
            j[k] = [e for e in j[k] if e != "EXT_texture_webp"]
            if not j[k]:
                del j[k]
    out = bytearray()
    for i, v in enumerate(views):
        while len(out) % 4:
            out.append(0)
        v["byteOffset"] = len(out)
        v["byteLength"] = len(blobs[i])
        out += blobs[i]
    while len(out) % 4:
        out.append(0)
    j["buffers"][0]["byteLength"] = len(out)
    js = json.dumps(j, separators=(",", ":")).encode()
    while len(js) % 4:
        js += b" "
    total = 12 + 8 + len(js) + 8 + len(out)
    with open(dst, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack("<II", len(out), 0x004E4942)); f.write(out)
    return dst



HERO_DIR = "/Game/Traversal/HeroDev"
_proj_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
_hero_src = os.path.normpath(os.path.join(_proj_dir, "..", "..", "public", "assets", "spiderman.glb"))
_hero_tmp = os.path.join(_proj_dir, "Saved", "HeroDev.glb")
convert(_hero_src, _hero_tmp)
# round 11 (FLIPS_BRIEF): gymnast shape clips keyed in Blender on the hero rig (headless, CPU only), spliced into the hero GLB
# (rotation channels matched by bone name, after a Blender round-trip check on 'airApex'); clip assets HeroDev/flip<Shape>
_flip_dir = os.path.normpath(os.path.join(_proj_dir, "..", "..", "docs", "night1", "traversal", "blender"))
_flip_glb = os.path.join(_proj_dir, "Saved", "HeroFlips.glb")
_blender = os.environ.get("SM2_BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender")
_r = subprocess.run([_blender, "-b", "--factory-startup", "-P", os.path.join(_flip_dir, "make_flip_shapes.py"), "--", _hero_src, _flip_glb,
                     os.path.join(_proj_dir, "Saved", "HeroFlips_report.json")], capture_output=True, text=True)
assert "FLIPSHAPES_OK" in _r.stdout, "Blender flip shapes failed:\n" + _r.stdout[-3000:] + _r.stderr[-2000:]
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("splice_flips", os.path.join(_flip_dir, "splice_flips.py"))
_sf = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_sf)
_rt, _nb, _added = _sf.splice(_hero_tmp, _flip_glb)
unreal.log("HERO_FLIPS_OK roundtrip_max=%.5f bones=%d clips=%s" % (_rt, _nb, [a[0] for a in _added]))
_task = unreal.AssetImportTask()
_task.set_editor_property("filename", _hero_tmp)
_task.set_editor_property("destination_path", HERO_DIR)
_task.set_editor_property("automated", True)
_task.set_editor_property("replace_existing", True)
_task.set_editor_property("save", True)
tools.import_asset_tasks([_task])
_n_anim = 0
for _a in eal.list_assets(HERO_DIR, recursive=True):
    _name = _a.split("/")[-1].split(".")[0]
    if _name.startswith("HeroDev") and len(_name) > len("HeroDev"):
        _clip = _name[len("HeroDev"):]
        eal.rename_asset(_a.split(".")[0], HERO_DIR + "/" + _clip)
        _n_anim += 1
unreal.log("HERODEV_OK assets=%d clips_renamed=%d" % (len(eal.list_assets(HERO_DIR, recursive=True)), _n_anim))

# ------------------------------------------------------------------ map
if MAP_EXISTS:
    assert les.load_level(MAP), "reload failed"
else:
    assert les.new_level(MAP), "new_level failed"
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")


def spawn(cls, loc=(0, 0, 0), rot=(0, 0, 0), label=None):
    a = eas.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(*rot))
    if label:
        a.set_actor_label(label)
    return a


LAYOUT = []


def box(x0, y0, z0, x1, y1, z1, label, mat=facade, mesh=CUBE):
    """Axis-aligned box in METRES (min / max corners)."""
    LAYOUT.append({"label": label, "min": [round(x0, 2), round(y0, 2), round(z0, 2)], "max": [round(x1, 2), round(y1, 2), round(z1, 2)]})
    a = spawn(unreal.StaticMeshActor, ((x0 + x1) * 50.0, (y0 + y1) * 50.0, (z0 + z1) * 50.0), label=label)
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    c.set_material(0, mat)
    a.set_actor_scale3d(unreal.Vector(x1 - x0, y1 - y0, z1 - z0))
    a.set_folder_path("Canyon")
    return a


rng = random.Random(20260929)
counts = {"buildings": 0, "towers": 0, "podiums": 0, "water_towers": 0}

# ground: 2.4 km x 0.6 km slab, top at z = 0 (tag WHGround: bare ground never holds a web)
g = box(-300, -300, -1, 2100, 300, 0, "Ground", ground_m)
g.tags = [unreal.Name("WHGround")]


def water_tower(cx, cy, roof, label):
    box(cx - 2.2, cy - 2.2, roof, cx + 2.2, cy + 2.2, roof + 3.0, label + "_Stand")
    box(cx - 2.6, cy - 2.6, roof + 3.0, cx + 2.6, cy + 2.6, roof + 9.0, label + "_Tank", mesh=CYL)
    counts["water_towers"] += 1


BLOCK, CROSS = 80.0, 18.0
X_START, X_END = -120.0, 1560.0
AVE_HALF = 15.0          # building line at |y| = 15 m (30 m avenue incl. sidewalks)
DEPTH = 45.0             # row 1 depth
PAR_STREET = 18.0        # parallel street behind row 1
DEPTH2 = 45.0

blk = 0
x = X_START
while x < X_END:
    for side in (-1, 1):
        # ---- row 1 (the canyon walls): 2-3 buildings along the block
        n = rng.choice([2, 2, 3])
        cuts = sorted(rng.uniform(0.28, 0.72) * BLOCK for _ in range(n - 1)) if n > 1 else []
        edges = [0.0] + cuts + [BLOCK]
        for k in range(n):
            bx0, bx1 = x + edges[k], x + edges[k + 1]
            y_in, y_out = AVE_HALF, AVE_HALF + DEPTH
            if side < 0:
                y0, y1 = -y_out, -y_in
            else:
                y0, y1 = y_in, y_out
            h = rng.choice([rng.uniform(80, 140), rng.uniform(110, 200), rng.uniform(160, 300)])
            label = "B%02d_%s%d" % (blk, "S" if side < 0 else "N", k)
            if rng.random() < 0.4:
                # podium + setback tower (10 m back from the avenue): perchable roof edge over the street
                ph = rng.uniform(25, 60)
                box(bx0, y0, 0, bx1, y1, ph, label + "_Podium")
                inset = 10.0
                ty0, ty1 = (y0, y1 - inset) if side < 0 else (y0 + inset, y1)
                tx0, tx1 = bx0 + 3.0, bx1 - 3.0
                if tx1 - tx0 > 12:
                    box(tx0, ty0, ph, tx1, ty1, h, label + "_Tower")
                    counts["towers"] += 1
                counts["podiums"] += 1
                if rng.random() < 0.6:
                    wy = (y1 - 5.0) if side < 0 else (y0 + 5.0)
                    water_tower((bx0 + bx1) * 0.5 + rng.uniform(-6, 6), wy, ph, label + "_WT")
            else:
                box(bx0, y0, 0, bx1, y1, h, label)
            counts["buildings"] += 1
        # ---- row 2 (behind the parallel street): lower skyline depth
        y_in2 = AVE_HALF + DEPTH + PAR_STREET
        y0, y1 = (-(y_in2 + DEPTH2), -y_in2) if side < 0 else (y_in2, y_in2 + DEPTH2)
        m = rng.choice([1, 2])
        for k in range(m):
            bx0 = x + BLOCK * k / m + (1.5 if k else 0)
            bx1 = x + BLOCK * (k + 1) / m
            h2 = rng.uniform(40, 150)
            box(bx0, y0, 0, bx1, y1, h2, "R2_%02d_%s%d" % (blk, "S" if side < 0 else "N", k))
            counts["buildings"] += 1
            if h2 < 90 and rng.random() < 0.5:
                water_tower((bx0 + bx1) * 0.5, (y0 + y1) * 0.5, h2, "R2_%02d_%s%d_WT" % (blk, "S" if side < 0 else "N", k))
    x += BLOCK + CROSS
    blk += 1

# ---- lighting (same stack as Foundation_Test): low morning sun down the avenue for long canyon shadows
sun = spawn(unreal.DirectionalLight, (0, 0, 50000), (0, -32, 25), "Sun")
sc = sun.get_component_by_class(unreal.DirectionalLightComponent)
sc.set_editor_property("intensity", 10.0)
sc.set_editor_property("atmosphere_sun_light", True)
sc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
spawn(unreal.SkyAtmosphere, (0, 0, 0), label="SkyAtmosphere")
sky = spawn(unreal.SkyLight, (0, 0, 1000), label="SkyLight")
skc = sky.get_component_by_class(unreal.SkyLightComponent)
skc.set_editor_property("real_time_capture", True)
skc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
fog = spawn(unreal.ExponentialHeightFog, (0, 0, 0), label="HeightFog")
fog.get_component_by_class(unreal.ExponentialHeightFogComponent).set_editor_property("fog_density", 0.006)
spawn(unreal.VolumetricCloud, (0, 0, 0), label="VolumetricCloud")
spawn(unreal.PostProcessVolume, (0, 0, 0), label="GlobalPPV").set_editor_property("unbound", True)

# player start on the avenue at the south end, facing +X (scripts override the spawn)
spawn(unreal.PlayerStart, (-6000, 0, 120), (0, 0, 0), "PlayerStart")

# game mode override: traversal pawn
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
gm = unreal.load_class(None, "/Script/WebHomage.WebTravGameMode")
assert gm, "WebTravGameMode class missing: build the C++ module first"
world.get_world_settings().set_editor_property("default_game_mode", gm)

assert les.save_current_level(), "save failed"
# layout dump (metres) for scripting capture sequences: docs/night1/traversal/trav_canyon_layout.json
_proj = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
_out = os.path.normpath(os.path.join(_proj, "..", "..", "docs", "night1", "traversal", "trav_canyon_layout.json"))
os.makedirs(os.path.dirname(_out), exist_ok=True)
with open(_out, "w") as f:
    json.dump({"units": "m", "axes": "UE (X along the avenue, Z up)", "boxes": LAYOUT}, f, indent=0)
unreal.log("TRAV_CANYON_OK actors=%d %s" % (len(eas.get_all_level_actors()), counts))
_B.finish()

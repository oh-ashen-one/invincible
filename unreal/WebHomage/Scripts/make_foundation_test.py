# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Builds the gray-box map /Game/Maps/Foundation_Test (piece F1).
# Run headless (editor closed):
#   UnrealEditor <uproject> -run=pythonscript -script=<this file> -unattended -nullrhi
# or inside the editor: py <this file>
import unreal

MAP = "/Game/Maps/Foundation_Test"
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
PLANE = unreal.load_asset("/Engine/BasicShapes/Plane.Plane")

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    unreal.EditorAssetLibrary.delete_asset(MAP)
assert les.new_level(MAP), "new_level failed"


def spawn(cls, loc=(0, 0, 0), rot=(0, 0, 0), label=None):
    a = eas.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(*rot))
    if label:
        a.set_actor_label(label)
    return a


def mesh(sm, loc, scale, label):
    a = spawn(unreal.StaticMeshActor, loc, label=label)
    c = a.static_mesh_component
    c.set_static_mesh(sm)
    a.set_actor_scale3d(unreal.Vector(*scale))
    return a


# 2 km x 2 km ground (Plane mesh is 100 cm square).
mesh(PLANE, (0, 0, 0), (2000, 2000, 1), "Ground")

# Buildings: (x, y, width_m, depth_m, height_m). Cube is 100 cm, pivot at centre.
blocks = [
    (6000, -4000, 40, 40, 120),
    (6000, 4000, 30, 50, 200),
    (12000, 0, 50, 50, 300),
    (-5000, 6000, 35, 35, 150),
    (-8000, -6000, 45, 30, 250),
    (2000, 12000, 30, 30, 100),
    (15000, 9000, 40, 40, 180),
    (-14000, 2000, 60, 40, 220),
]
for i, (x, y, w, d, h) in enumerate(blocks):
    mesh(CUBE, (x, y, h * 50.0), (w, d, h), f"Building_{i:02d}_{h}m")

sun = spawn(unreal.DirectionalLight, (0, 0, 50000), (0, -40, -35), "Sun")
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
fc = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
fc.set_editor_property("fog_density", 0.01)
spawn(unreal.VolumetricCloud, (0, 0, 0), label="VolumetricCloud")
spawn(unreal.PostProcessVolume, (0, 0, 0), label="GlobalPPV").set_editor_property("unbound", True)

# Player starts at origin facing +X (toward the tallest block).
spawn(unreal.PlayerStart, (0, 0, 200), (0, 0, 0), "PlayerStart")

assert les.save_current_level(), "save failed"
unreal.log("FOUNDATION_TEST_OK actors=%d" % len(eas.get_all_level_actors()))

"""Import the authoritative hero and preserve every original Action for comparison."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
scene = bpy.context.scene
assert scene.get("session_owner") == "sm2-astra-anim"
assert scene.get("mcp_port") == 19891
assert not any(o.type == "ARMATURE" for o in scene.objects), "Refusing duplicate import"
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT / "public/assets/spiderman.glb"))
rigs = [o for o in scene.objects if o.type == "ARMATURE"]
assert len(rigs) == 1
rig = rigs[0]
for action in bpy.data.actions:
    action.use_fake_user = True
rig.animation_data_create()
for track in rig.animation_data.nla_tracks:
    track.mute = True
idle = bpy.data.actions.get("idle")
rig.animation_data.action = idle
if idle and len(idle.slots):
    rig.animation_data.action_slot = idle.slots[0]
scene.render.fps = 24
scene.frame_set(1)
rig.show_in_front = True
bpy.context.view_layer.objects.active = rig
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
for area in bpy.context.screen.areas:
    if area.type == "VIEW_3D":
        space = area.spaces.active
        space.shading.type = 'MATERIAL'
        space.region_3d.view_distance = 3.8
        space.region_3d.view_location = Vector((0, 0, 0.95))
        space.region_3d.view_rotation = Vector((3, -5, 2)).to_track_quat('Z','Y')
audit = {
 "file": str(ROOT / "art/anim/hero.blend"),
 "owner": scene["session_owner"],
 "port": scene["mcp_port"],
 "blender_version": bpy.app.version_string,
 "rig": rig.name,
 "rig_matrix": [list(row) for row in rig.matrix_world],
 "bones": [{"name": b.name,"parent": b.parent.name if b.parent else None,"head": list(b.head_local),"tail":list(b.tail_local),"rest": [list(row) for row in b.matrix_local]} for b in rig.data.bones],
 "actions": [{"name": a.name,"frames":list(a.frame_range),"slots":[s.identifier for s in a.slots]} for a in bpy.data.actions],
 "meshes": [{"name": o.name, "vertices": len(o.data.vertices),"dimensions":list(o.dimensions),"materials":[m.name if m else None for m in o.data.materials]} for o in scene.objects if o.type=="MESH"],
}
out = ROOT / "docs/anim/hero/rig-audit.json"
out.write_text(json.dumps(audit,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "art/anim/hero.blend"))
print(json.dumps({"owner":scene["session_owner"],"path":bpy.data.filepath,"bones":len(rig.data.bones),"actions":len(bpy.data.actions),"meshes":len(audit["meshes"])}))

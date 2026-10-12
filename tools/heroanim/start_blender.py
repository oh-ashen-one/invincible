"""Start only this task's Blender MCP instance; run with --factory-startup."""
import importlib.util
import os
from pathlib import Path
import sys
import bpy

ROOT = Path(__file__).resolve().parents[2]
PORT = 19891
ADDON = Path(os.environ["SM2_BLENDER_ADDON"])
spec = importlib.util.spec_from_file_location("sm2_anim_blender_mcp", ADDON)
addon = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = addon
spec.loader.exec_module(addon)
start = addon.BlenderMCPServer.start
addon.BlenderMCPServer.start = lambda self: None
try:
    addon.register()
finally:
    addon.BlenderMCPServer.start = start
if hasattr(bpy.types, "blendermcp_server"):
    del bpy.types.blendermcp_server
scene = bpy.context.scene
scene.name = "SM2_Hero_Animation"
scene["session_owner"] = "sm2-astra-anim"
scene["mcp_port"] = PORT
scene.blendermcp_port = PORT
bpy.types.blendermcp_server = addon.BlenderMCPServer(host="127.0.0.1", port=PORT)
bpy.types.blendermcp_server.start()
scene.blendermcp_server_running = True
path = ROOT / "art/anim/hero.blend"
path.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(path))
print(f"SESSION_OWNED_BLENDER_MCP_READY port={PORT}", flush=True)

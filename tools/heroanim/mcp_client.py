"""Actual stdio MCP client for the dedicated Studio Blender server (1.9.1)."""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[2]
async def main():
    p = argparse.ArgumentParser()
    p.add_argument("tool", help="catalog or an MCP tool name")
    p.add_argument("--args", default="{}")
    p.add_argument("--script", type=Path)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    env = dict(os.environ, BLENDER_HOST="127.0.0.1", BLENDER_PORT="19891", BLENDER_MCP_DISABLE_TELEMETRY="1")
    server = StdioServerParameters(command="/opt/homebrew/bin/uvx", args=["--from", "blender-mcp==1.9.1", "blender-mcp"], env=env)
    async with stdio_client(server) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            if a.tool == "catalog":
                result = (await session.list_tools()).model_dump(mode="json")
            else:
                args = json.loads(a.args)
                if a.script:
                    path = str(a.script.resolve())
                    args["code"] = f"exec(compile(open({path!r}).read(), {path!r}, 'exec'), {{'__name__': '__main__', '__file__': {path!r}}})"
                response = await session.call_tool(a.tool, arguments=args)
                result = response.model_dump(mode="json")
                if a.output and any(c.type == "image" for c in response.content):
                    c = next(c for c in response.content if c.type == "image")
                    a.output.parent.mkdir(parents=True, exist_ok=True)
                    a.output.write_bytes(base64.b64decode(c.data))
                    print(json.dumps({"image": str(a.output), "isError": response.isError}))
                    return
            if a.output:
                a.output.parent.mkdir(parents=True, exist_ok=True)
                a.output.write_text(json.dumps(result, indent=2))
            print(json.dumps(result))
asyncio.run(main())

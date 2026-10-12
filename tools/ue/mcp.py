#!/usr/bin/env python3
"""Minimal client for the Unreal Editor MCP server (WebHomage instance, 127.0.0.1:8765/mcp).

Usage:
  tools/ue/mcp.py toolsets                       # list toolsets
  tools/ue/mcp.py describe <toolset>             # tool names + schemas
  tools/ue/mcp.py call <toolset> <tool> '<json>' # call a toolset tool
Env: UE_MCP_URL overrides the endpoint.
"""
import json, os, sys, urllib.request

URL = os.environ.get("UE_MCP_URL", "http://127.0.0.1:8765/mcp")
_sid = None

def rpc(method, params=None, notify=False):
    global _sid
    body = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        body["params"] = params
    if not notify:
        body["id"] = 1
    req = urllib.request.Request(URL, json.dumps(body).encode(), {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        **({"Mcp-Session-Id": _sid} if _sid else {}),
    })
    with urllib.request.urlopen(req, timeout=600) as r:
        _sid = r.headers.get("Mcp-Session-Id", _sid)
        raw = r.read().decode()
    return json.loads(raw) if raw.strip() else None

def connect():
    rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "ue-mcp-cli", "version": "1"}})
    rpc("notifications/initialized", notify=True)

def tool(name, args):
    res = rpc("tools/call", {"name": name, "arguments": args})
    if "error" in res:
        raise SystemExit(json.dumps(res["error"], indent=1))
    return "\n".join(c.get("text", "") for c in res["result"]["content"])

if __name__ == "__main__":
    connect()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "toolsets"
    if cmd == "toolsets":
        print(tool("list_toolsets", {}))
    elif cmd == "describe":
        print(tool("describe_toolset", {"toolset_name": sys.argv[2]}))
    elif cmd == "call":
        args = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        print(tool("call_tool", {"toolset_name": sys.argv[2], "tool_name": sys.argv[3], "arguments": args}))
    else:
        raise SystemExit(__doc__)

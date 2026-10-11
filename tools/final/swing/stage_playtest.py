#!/usr/bin/env python3
"""Stage the tested WebHomage runtime for a local owner playtest (no engine launch).

Requires macOS/APFS clonefile via `cp -cR`; the destination must be new. The
staged game still requires this Mac's installed Unreal Engine 5.8.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "unreal/WebHomage"
UE = Path("/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor")
MAP_ASSET = "Content/Showcase/Maps/Manhattan_Island.umap"
RUNTIME_DIRS = ("Config", "Binaries", "Content", "Shaders")
KEY_FILES = {
    "module_manifest": "WebHomage/Binaries/Mac/UnrealEditor.modules",
    "web_material": "WebHomage/Content/Traversal/Materials/M_TravWeb.uasset",
    "playable_settings": "WebHomage/Config/PerfPlayableFast.cvars",
    "default_engine_settings": "WebHomage/Config/DefaultEngine.ini",
    "default_game_settings": "WebHomage/Config/DefaultGame.ini",
    "input_settings": "WebHomage/Config/DefaultInput.ini",
    "project": "WebHomage/WebHomage.uproject",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def source_ready(source_commit):
    commit = git("rev-parse", "--verify", source_commit + "^{commit}")
    if subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", commit, "HEAD"]).returncode:
        raise ValueError("tested source commit is not an ancestor of this checkout")
    modules = json.loads((PROJECT / "Binaries/Mac/UnrealEditor.modules").read_text())
    dylib_name = modules["Modules"]["WebHomage"]
    if Path(dylib_name).name != dylib_name or not re.fullmatch(r"libUnrealEditor-WebHomage(?:-[0-9]+)?\.dylib", dylib_name):
        raise ValueError("unsafe or unexpected WebHomage module name")
    key_files = dict(KEY_FILES, dylib="WebHomage/Binaries/Mac/" + dylib_name)
    required = [PROJECT / MAP_ASSET, *(ROOT / path for path in ("DISCLAIMER.md", "LICENSE")),
                ROOT / "tools/m5/guarded_preview.py",
                *(ROOT / "unreal" / path for path in key_files.values())]
    missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise ValueError("missing or empty runtime inputs: " + ", ".join(missing))
    for name in RUNTIME_DIRS:
        directory = PROJECT / name
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError("missing or symlinked runtime directory: " + str(directory))
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise ValueError("runtime directory contains a symlink: " + str(path))
            if path.is_file() and (path.name.startswith(".env") or path.suffix.lower() in {".pem", ".p12", ".p8", ".key"}
                                   or path.name.lower() in {"credentials.json", "secrets.json"}):
                raise ValueError("credential-like file cannot be staged: " + str(path))
    if not UE.is_file():
        raise ValueError("installed Unreal Engine 5.8 executable is missing: " + str(UE))
    key_hashes = {name: sha256(ROOT / "unreal" / rel) for name, rel in key_files.items()}
    return commit, key_files, key_hashes


def destination(value):
    raw = Path(value).expanduser()
    if not raw.is_absolute():
        raise ValueError("--dest must be absolute")
    if raw.exists() or raw.is_symlink():
        raise ValueError("destination already exists: " + str(raw))
    dest = raw.resolve()
    source = ROOT.resolve()
    if dest == source or dest in source.parents or source in dest.parents:
        raise ValueError("destination must be outside the source checkout")
    if not dest.parent.is_dir():
        raise ValueError("destination parent must already exist: " + str(dest.parent))
    return dest


def clone(src, dst):
    subprocess.run(["cp", "-cR", str(src), str(dst)], check=True)


def play_command():
    return '''#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
UE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
if [ ! -x "$UE" ]; then echo "Unreal Engine 5.8 is missing: $UE" >&2; exit 1; fi
mkdir -p "$HERE/Saved/OwnerPlaytest/User" "$HERE/Saved/OwnerPlaytest/logs"
export GPU_SLOT_DIR="$HOME/.cache/gpu-slot"
unset SM2_COEXIST_HOLDER
exec /usr/bin/env python3 "$HERE/tools/m5/guarded_preview.py" -- \
  "$UE" "$HERE/WebHomage/WebHomage.uproject" /Game/Showcase/Maps/Manhattan_Island \
  -game -windowed -ResX=1920 -ResY=1080 -ForceRes -NoVSync \
  -WHProfile=playable -WHResScale=100 \
  "-WHPerfPreset=$HERE/WebHomage/Config/PerfPlayableFast.cvars" -WHSuit=tessera \
  "-UserDir=$HERE/Saved/OwnerPlaytest/User/" -NoCrashReports -notraceserver \
  "-ExecCmds=t.MaxFPS 60,r.ScreenPercentage 100,r.AntiAliasingMethod 4" \
  "-abslog=$HERE/Saved/OwnerPlaytest/logs/play.log"
'''


def readme(source_commit):
    return f'''# Round 13 owner playtest

Local playable checkpoint from source commit `{source_commit}`. This is an Unreal
Editor `-game` launch on the same Mac, with Unreal Engine 5.8 installed; it is
not a standalone packaged game. Double-click `Play.command` when the shared
GPU is free. Its guarded launcher honors the shared PAUSED state, GPU locks,
holders, other renderer processes and the live desktop requirement. It never
stops another process. Logs and settings go into this folder's `Saved/`.

Window: 1920 × 1080; playable profile at 100% internal resolution, Fast preset,
Tessera suit, 60 fps cap. Map: Manhattan_Island.

Controls (from the project's traversal HANDOFF): WASD move, mouse look, right
mouse button swing, Space jump, Shift sprint, E zip, C drop, Q quick boost,
F trick. Gamepad: left stick move, right stick look, R2/RT swing. On a
DualSense, Cross jumps and Square triggers tricks; Xbox equivalents are A and X.

To verify every staged file without the source checkout, run from this folder:
`shasum -a 256 -c SHA256SUMS`. `STAGE.json` records the source commit, checkout
commit, selected runtime hashes and the hash of `SHA256SUMS`. This file check
does not prove gameplay quality or replace the owner's playtest.

See `DISCLAIMER.md` and `LICENSE`. This is an unofficial, non-commercial fan
homage for local evaluation; do not redistribute this folder.
'''


def write_manifest(dest):
    entries = []
    for path in sorted(dest.rglob("*")):
        if path.is_symlink():
            raise ValueError("staged file is a symlink: " + str(path))
        if path.is_file():
            rel = path.relative_to(dest).as_posix()
            entries.append((rel, sha256(path)))
    manifest = dest / "SHA256SUMS"
    manifest.write_text("".join(f"{digest}  {rel}\n" for rel, digest in entries))
    return manifest, entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", required=True, help="new absolute local deliverable folder")
    parser.add_argument("--source-commit", required=True, help="tested runtime source commit")
    parser.add_argument("--check-only", action="store_true", help="check inputs and destination without creating files")
    args = parser.parse_args()
    try:
        if sys.platform != "darwin":
            raise ValueError("APFS clonefile staging requires macOS")
        dest = destination(args.dest)
        commit, key_files, source_key_hashes = source_ready(args.source_commit)
    except (ValueError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
    if args.check_only:
        print(json.dumps({"ready_to_stage": True, "destination": str(dest),
                          "source_commit": commit, "checkout_commit": git("rev-parse", "HEAD"),
                          "runtime_project": str(PROJECT), "installed_unreal": str(UE),
                          "key_sha256": source_key_hashes}, indent=2))
        return
    dest.mkdir()
    (dest / "WebHomage").mkdir()
    for name in RUNTIME_DIRS:
        clone(PROJECT / name, dest / "WebHomage" / name)
    clone(PROJECT / "WebHomage.uproject", dest / "WebHomage/WebHomage.uproject")
    (dest / "tools/m5").mkdir(parents=True)
    clone(ROOT / "tools/m5/guarded_preview.py", dest / "tools/m5/guarded_preview.py")
    for name in ("DISCLAIMER.md", "LICENSE"):
        clone(ROOT / name, dest / name)
    launcher = dest / "Play.command"
    launcher.write_text(play_command())
    launcher.chmod(0o755)
    (dest / "README.md").write_text(readme(commit))
    manifest, entries = write_manifest(dest)
    key_hashes = {name: sha256(dest / rel) for name, rel in key_files.items()}
    if key_hashes != source_key_hashes:
        raise ValueError("a key runtime input changed while staging; deliverable is incomplete: " + str(dest))
    stage = {"tested_source_commit": commit, "staging_checkout_commit": git("rev-parse", "HEAD"),
             "created_utc": datetime.now(timezone.utc).isoformat(), "engine": "UE 5.8 on this Mac",
             "map": "/Game/Showcase/Maps/Manhattan_Island", "runtime_verified": False,
             "files": len(entries), "bytes": sum((dest / rel).stat().st_size for rel, _ in entries),
             "key_sha256": key_hashes, "sha256_manifest": sha256(manifest)}
    (dest / "STAGE.json").write_text(json.dumps(stage, indent=2) + "\n")
    print(json.dumps({"staged": str(dest), **stage}, indent=2))


if __name__ == "__main__":
    main()

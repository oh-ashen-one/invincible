#!/usr/bin/env python3
"""Make an anonymised A/B pack for a critic.

  python3 tools/night1/abpack.py <pack_dir> <pairs.json>

pairs.json: [{"id": "street-canyon", "x": "<path ours>", "y": "<path other>", "note": "camera/view description"}]
For each pair the two files are copied to <pack_dir>/<id>/A.<ext> and B.<ext> in random
order. The key (which of A/B was x) goes to <pack_dir>.key.json, OUTSIDE the pack, so the
critic never sees it. <pack_dir>/PAIRS.md lists ids + neutral view notes only.
"""
import json, os, random, subprocess, sys

pack, pairs = sys.argv[1], json.load(open(sys.argv[2]))
os.makedirs(pack, exist_ok=True)
key, lines = {}, ["# Pairs", "", "Each folder holds A and B for the same view or movement. Judge each on its own merits.", ""]
for p in pairs:
    d = os.path.join(pack, p["id"])
    os.makedirs(d, exist_ok=True)
    order = [("x", p["x"]), ("y", p["y"])]
    random.shuffle(order)
    for slot, (who, src) in zip("AB", order):
        ext = os.path.splitext(src)[1].lower()
        dst = os.path.join(d, slot + ext)
        # Re-encode so the critic can't identify files by hash or metadata, and centre-crop 84% on both
        # sides so HUD/logos at the frame edges of reference footage don't give the answer away.
        if ext in (".mp4", ".mov", ".webm", ".mkv"):
            dst = os.path.join(d, slot + ".mp4")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-map_metadata", "-1", "-an",
                            "-vf", "crop=iw*0.84:ih*0.84,scale='min(1920,iw)':-2", "-c:v", "libx264", "-crf", "20", "-preset", "fast", dst], check=True)
        else:
            dst = os.path.join(d, slot + ".jpg")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-map_metadata", "-1", "-vf", "crop=iw*0.84:ih*0.84", "-q:v", "3", dst], check=True)
        key.setdefault(p["id"], {})[slot] = who
    lines.append(f"- `{p['id']}/` — {p.get('note', '')}")
open(os.path.join(pack, "PAIRS.md"), "w").write("\n".join(lines) + "\n")
json.dump(key, open(pack.rstrip("/") + ".key.json", "w"), indent=1)
print(f"packed {len(pairs)} pairs -> {pack}")

#!/usr/bin/env python3
"""Read-only GLB inspector for the supplied M3 props (PA, phase 1).

Parses each GLB directly (no Blender, no GPU): triangle count, vertex count, bounds,
pivot offset, embedded image size/format, basic texture stats, and a geometry
fingerprint so "(1)" pairs can be compared.  Never writes next to the source files.

usage: glb_inspect.py <glb_dir> <out_json>
"""
import hashlib, io, json, struct, sys
from pathlib import Path

import numpy as np
from PIL import Image

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def load(path):
    data = path.read_bytes()
    magic, ver, length = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67, path
    off, js, binc = 12, None, b""
    while off < length:
        clen, ctype = struct.unpack_from("<II", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk)
        elif ctype == 0x004E4942:
            binc = chunk
        off += 8 + clen
    return js, binc


def accessor(js, binc, idx):
    a = js["accessors"][idx]
    bv = js["bufferViews"][a["bufferView"]]
    n, comps = a["count"], NC[a["type"]]
    dt = np.dtype(CT[a["componentType"]])
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride", 0)
    if stride and stride != dt.itemsize * comps:
        raw = np.frombuffer(binc, dtype=np.uint8, count=stride * (n - 1) + dt.itemsize * comps, offset=start)
        out = np.lib.stride_tricks.as_strided(raw, shape=(n, dt.itemsize * comps), strides=(stride, 1)).copy()
        return out.view(dt).reshape(n, comps)
    return np.frombuffer(binc, dtype=dt, count=n * comps, offset=start).reshape(n, comps)


def inspect(path):
    js, binc = load(path)
    rec = {"file": path.name, "bytes": path.stat().st_size, "generator": js.get("asset", {}).get("generator")}
    node = js["nodes"][0]
    rec["node_transform"] = {k: node[k] for k in ("matrix", "translation", "rotation", "scale") if k in node}
    tris = verts = 0
    allpos = []
    attrs = set()
    geo_h = hashlib.sha256()
    for mesh in js["meshes"]:
        for prim in mesh["primitives"]:
            attrs |= set(prim["attributes"])
            pos = accessor(js, binc, prim["attributes"]["POSITION"]).astype(np.float64)
            verts += len(pos)
            allpos.append(pos)
            if "indices" in prim:
                ind = accessor(js, binc, prim["indices"]).ravel()
                tris += len(ind) // 3
            else:
                tris += len(pos) // 3
            geo_h.update(np.round(pos, 4).tobytes())
    P = np.concatenate(allpos)
    mn, mx = P.min(0), P.max(0)
    ext = mx - mn
    rec.update(
        triangles=int(tris), vertices=int(verts), attributes=sorted(attrs),
        bbox_min=[round(float(v), 4) for v in mn], bbox_max=[round(float(v), 4) for v in mx],
        extent_xyz=[round(float(v), 4) for v in ext],
        pivot_note=(
            "origin at bbox centre" if np.all(np.abs((mn + mx) / 2) < 0.02 * max(ext.max(), 1e-6)) else
            "origin at base centre (Y-min)" if abs(mn[1]) < 0.02 * ext.max() else "origin offset"
        ),
        pivot_offset_from_bbox_centre=[round(float(v), 4) for v in (mn + mx) / 2],
        geometry_sha256=geo_h.hexdigest()[:16],
        tallest_axis="XYZ"[int(np.argmax(ext))],
    )
    mats = js.get("materials", [])
    rec["material"] = mats[0] if mats else None
    imgs = []
    for im in js.get("images", []):
        bv = js["bufferViews"][im["bufferView"]]
        raw = binc[bv.get("byteOffset", 0): bv.get("byteOffset", 0) + bv["byteLength"]]
        pil = Image.open(io.BytesIO(raw))
        small = pil.convert("RGB").resize((256, 256), Image.BILINEAR)
        a = np.asarray(small).astype(np.float32)
        imgs.append({
            "mime": im.get("mimeType"), "size": list(pil.size), "mode": pil.mode, "bytes": len(raw),
            "mean_rgb": [round(float(v), 1) for v in a.reshape(-1, 3).mean(0)],
            "image_sha256": hashlib.sha256(raw).hexdigest()[:16],
        })
    rec["images"] = imgs
    rec["vertex_colors"] = "COLOR_0" in attrs
    return rec


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    recs = []
    for p in sorted(src.glob("*.glb")):
        try:
            recs.append(inspect(p))
        except Exception as e:  # keep going; record the failure
            recs.append({"file": p.name, "error": repr(e)})
        r = recs[-1]
        print(f"{r['file'][:44]:44s} tris={r.get('triangles')} ext={r.get('extent_xyz')} "
              f"img={[i['size'] for i in r.get('images', [])]} vc={r.get('vertex_colors')} geo={r.get('geometry_sha256')} {r.get('pivot_note')}")
    out.write_text(json.dumps(recs, indent=1))


if __name__ == "__main__":
    main()

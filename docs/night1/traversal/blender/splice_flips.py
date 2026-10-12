# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 11: splice the Blender-keyed flip shape actions (make_flip_shapes.py output) into the hero GLB.
#   python3 splice_flips.py <hero.glb (in/out)> <HeroFlips.glb>
# Rotation channels only, matched by node NAME. Before splicing, the untouched 'airApex' action of the Blender export is
# compared with the hero GLB's own 'airApex' (same bones, same keys): the Blender round trip must reproduce every
# rotation within ROUNDTRIP_TOL (quaternion component), or the splice refuses (the new clips would be in a different
# bone space). All existing bytes / clips of the hero GLB are kept; the new animations are appended.
import json
import struct
import sys

ROUNDTRIP_TOL = 2e-3
COMP = {5126: ("f", 4)}
NCOMP = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}


def load(path):
    b = open(path, "rb").read()
    L = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + L])
    off = 20 + L
    BL = struct.unpack("<I", b[off:off + 4])[0]
    return j, bytearray(b[off + 8: off + 8 + BL])


def save(path, j, binc):
    while len(binc) % 4:
        binc.append(0)
    j["buffers"][0]["byteLength"] = len(binc)
    js = json.dumps(j, separators=(",", ":")).encode()
    while len(js) % 4:
        js += b" "
    total = 12 + 8 + len(js) + 8 + len(binc)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack("<II", len(binc), 0x004E4942)); f.write(bytes(binc))


def read_acc(j, binc, ai):
    a = j["accessors"][ai]
    assert a["componentType"] == 5126, "float accessors only"
    v = j["bufferViews"][a["bufferView"]]
    n = NCOMP[a["type"]]
    start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = v.get("byteStride", 4 * n)
    out = []
    for i in range(a["count"]):
        o = start + i * stride
        out.append(struct.unpack_from("<%df" % n, binc, o))
    return out


def rot_tracks(j, binc, anim):
    """node name -> (times, quats) for the rotation channels of one animation."""
    res = {}
    for ch in anim["channels"]:
        if ch["target"].get("path") != "rotation":
            continue
        s = anim["samplers"][ch["sampler"]]
        name = j["nodes"][ch["target"]["node"]].get("name")
        res[name] = ([t[0] for t in read_acc(j, binc, s["input"])], read_acc(j, binc, s["output"]), s.get("interpolation", "LINEAR"))
    return res


def sample(times, quats, t):
    if t <= times[0]:
        return quats[0]
    for i in range(1, len(times)):
        if t <= times[i]:
            k = (t - times[i - 1]) / max(1e-9, times[i] - times[i - 1])
            a, b = quats[i - 1], quats[i]
            if sum(x * y for x, y in zip(a, b)) < 0:
                b = tuple(-x for x in b)
            q = tuple(x + (y - x) * k for x, y in zip(a, b))
            n = sum(x * x for x in q) ** 0.5
            return tuple(x / n for x in q)
    return quats[-1]


def add_acc(j, binc, data, typ, minmax=False):
    n = NCOMP[typ]
    while len(binc) % 4:
        binc.append(0)
    off = len(binc)
    for row in data:
        binc += struct.pack("<%df" % n, *row)
    j["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": len(binc) - off})
    acc = {"bufferView": len(j["bufferViews"]) - 1, "componentType": 5126, "count": len(data), "type": typ}
    if minmax:
        acc["min"] = [min(r[i] for r in data) for i in range(n)]
        acc["max"] = [max(r[i] for r in data) for i in range(n)]
    j["accessors"].append(acc)
    return len(j["accessors"]) - 1


def splice(hero_path, flips_path, prefix="flip"):
    hj, hb = load(hero_path)
    fj, fb = load(flips_path)
    hanims = {a["name"]: a for a in hj.get("animations", [])}
    fanims = {a["name"]: a for a in fj.get("animations", [])}
    # ---- round-trip check on airApex
    assert "airApex" in hanims and "airApex" in fanims, "airApex missing (hero %s, flips %s)" % ("airApex" in hanims, "airApex" in fanims)
    H = rot_tracks(hj, hb, hanims["airApex"])
    B = rot_tracks(fj, fb, fanims["airApex"])
    worst, nb = 0.0, 0
    for name, (tt, qq, _) in H.items():
        if name not in B:
            continue
        nb += 1
        bt, bq, _ = B[name]
        for t, q in zip(tt, qq):
            r = sample(bt, bq, t)
            if sum(x * y for x, y in zip(q, r)) < 0:
                r = tuple(-x for x in r)
            worst = max(worst, max(abs(x - y) for x, y in zip(q, r)))
    assert nb >= 50, "round trip: only %d bones matched" % nb
    assert worst <= ROUNDTRIP_TOL, "Blender round trip changed airApex rotations by %.4f (> %.4f)" % (worst, ROUNDTRIP_TOL)
    # ---- append the flip actions (replace same-named ones from an earlier splice)
    node_idx = {n.get("name"): i for i, n in enumerate(hj["nodes"])}
    hj["animations"] = [a for a in hj.get("animations", []) if not a["name"].startswith(prefix)]
    added = []
    for name, anim in sorted(fanims.items()):
        if not name.startswith(prefix):
            continue
        tr = rot_tracks(fj, fb, anim)
        new = {"name": name, "channels": [], "samplers": []}
        for bone, (tt, qq, interp) in sorted(tr.items()):
            if bone not in node_idx:
                continue
            ia = add_acc(hj, hb, [(t,) for t in tt], "SCALAR", minmax=True)
            oa = add_acc(hj, hb, qq, "VEC4")
            new["samplers"].append({"input": ia, "output": oa, "interpolation": interp})
            new["channels"].append({"sampler": len(new["samplers"]) - 1, "target": {"node": node_idx[bone], "path": "rotation"}})
        hj["animations"].append(new)
        added.append((name, len(new["channels"])))
    save(hero_path, hj, hb)
    return worst, nb, added


if __name__ == "__main__":
    w, nb, added = splice(sys.argv[1], sys.argv[2])
    print("SPLICE_OK roundtrip_max=%.5f bones=%d added=%s" % (w, nb, added))

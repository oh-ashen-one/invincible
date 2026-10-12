#!/usr/bin/env python3
"""Strip textures from a game GLB so Unreal's Interchange glTF importer accepts it (it rejects EXT_texture_webp).
Geometry, skin, joints, inverse binds and animations are copied byte-for-byte; materials keep their names
(= UE material slots) but lose texture refs. Textures go to UE separately as PNG (art/night1/characters/*/tex).
usage: strip_glb.py in.glb out.glb        (fan homage project; not official Marvel/Sony/Insomniac)"""
import json, struct, sys

def main(src, dst):
    b = open(src, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    g = json.loads(b[20:20 + n])
    binchunk = b[20 + n:]
    for m in g.get('materials', []):
        pb = m.get('pbrMetallicRoughness', {})
        for k in ('baseColorTexture', 'metallicRoughnessTexture'):
            pb.pop(k, None)
        for k in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
            m.pop(k, None)
        m.pop('extensions', None)
    for k in ('images', 'textures', 'samplers'):
        g.pop(k, None)
    for k in ('extensionsUsed', 'extensionsRequired'):
        if k in g:
            g[k] = [e for e in g[k] if e not in ('EXT_texture_webp', 'KHR_texture_transform')]
            if not g[k]:
                g.pop(k)
    js = json.dumps(g, separators=(',', ':')).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    out = b'glTF' + struct.pack('<II', 2, 12 + 8 + len(js) + len(binchunk)) + struct.pack('<I', len(js)) + b'JSON' + js + binchunk
    open(dst, 'wb').write(out)
    print(dst, len(out))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 06 (CH18, root cause): refit the crowd citizens from the raw Tripo meshes with WELDED skin weights.

Why: `tools/crowdfit/crowdfit.py` (which made public/assets/city/npc/citizens.bin for the browser game) transfers skin weights per glTF vertex and
then un-poses each vertex with its own weights.  glTF vertices are split at every uv seam / normal seam, so the two halves of a seam got different
weights, were un-posed to different places and the mesh came out of the pipeline as hundreds of loose shells (3000-4400 open boundary edges
after a position weld; the raw mesh has 100-215).  Every crack, sleeve tear, coat flap and finger claw of rounds 04-05 comes from that.

This tool repeats the crowdfit steps (orient + pose fit + weight transfer + exact inverse-LBS un-pose) on the raw mesh, but the transfer and
the un-pose run on the position-welded vertices, so a seam stays closed.  It also keeps every raw triangle (no decimation) and the 8192 px
texture (resized to TEX px).

  python3 tools/ue_char/eval/refit.py NAME [NAME ...] [--smooth N]      -> <scratch>/eval/refit/NAME.npz  + NAME_tex.png
npz: pos (nv,3) rest pose in the crowd frame (Y up, +Z forward, metres), nrm (nv,3), uv (nv,2) glTF uv (origin top-left, 0..1), idx (nt,3),
     dense (nv,18) skin weights (welded vertices share them), fit_x, fit_rms, welded (nv,) index of the position-welded vertex.
"""
import json, os, subprocess, sys, tempfile, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from p2paths import WT, scr  # noqa: E402
sys.path.insert(0, os.path.join(WT, 'tools', 'crowdfit')); sys.path.insert(0, os.path.join(WT, 'tools', 'skinfit'))
import crowdfit as CF  # noqa: E402
from skinfit import read_glb, image_bytes  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

NPC = os.path.join(WT, 'public/assets/city/npc')
MAN = json.load(open(os.path.join(WT, 'tools/crowdfit/manifest_citizens.json')))['citizens']
TEX = int(os.environ.get('REFIT_TEX', '2048'))
OUT = scr('eval', 'refit')


def raw_lod(glb, wd, yaw):
    """Blender: import, join, orient, triangulate, export WITHOUT decimation (targets above the triangle count)."""
    out = os.path.join(wd, 'lod')
    r = subprocess.run([CF.BLENDER, '-b', '--factory-startup', '--python', os.path.join(WT, 'tools/crowdfit/decimate_lods.py'), '--',
                        glb, out, '1000000', str(yaw)], capture_output=True, text=True)
    if not os.path.exists(out + '0.glb'):
        raise RuntimeError('blender failed: ' + (r.stderr or r.stdout)[-600:])
    return CF.read_lod(out + '0.glb')


def weld(P, tol=1e-5):
    key = np.round(P / tol).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    return first, inv.reshape(-1)


def transfer_welded(crowd, S, P, N, F, welded, k=12, smooth=3, keep=0.5):
    """crowdfit.transfer on the welded vertices: nearest normal-compatible posed source vertices (inverse squared distance), smoothing over the
    WELDED connectivity (uv-seam duplicates are one vertex, so they can never differ), no cross-body borrowing, prop bone folded into its parent."""
    nu = welded.max() + 1
    cnt = np.bincount(welded, minlength=nu).astype(float)
    Pu = np.zeros((nu, 3)); np.add.at(Pu, welded, P); Pu /= cnt[:, None]
    Nu = np.zeros((nu, 3)); np.add.at(Nu, welded, N); Nu /= np.linalg.norm(Nu, axis=1, keepdims=True) + 1e-12
    Fu = welded[F]
    Pd, Nd = crowd.deform(S, None, crowd.N)
    dist, idx = cKDTree(Pd).query(Pu, k=k)
    nb = len(crowd.names)
    dense = np.zeros((nu, nb))
    ok = np.einsum('vkc,vc->vk', Nd[idx], Nu) > 0.2; ok[~ok.any(1), 0] = True
    w = np.where(ok, 1.0 / (dist + 1e-4) ** 2, 0.0)
    for kk in range(k):
        np.add.at(dense, (np.arange(nu)[:, None], crowd.J[idx[:, kk]]), w[:, kk:kk + 1] * crowd.W[idx[:, kk]])
    dense /= np.maximum(dense.sum(1, keepdims=True), 1e-9)
    e = np.concatenate([Fu[:, [0, 1]], Fu[:, [1, 2]], Fu[:, [2, 0]]]); e = np.concatenate([e, e[:, ::-1]])
    e = np.unique(e[e[:, 0] != e[:, 1]], axis=0)
    deg = np.bincount(e[:, 0], minlength=nu).astype(float)[:, None]
    for _ in range(smooth):
        acc = np.zeros_like(dense); np.add.at(acc, e[:, 0], dense[e[:, 1]])
        dense = keep * dense + (1 - keep) * acc / np.maximum(deg, 1)
    side = np.array([1 if n.endswith('L') else -1 if n.endswith('R') else 0 for n in crowd.names])
    cx = Pu[:, 0]
    dense[np.ix_(cx > 0.03, side < 0)] = 0.0
    dense[np.ix_(cx < -0.03, side > 0)] = 0.0
    pi = crowd.names.index('prop')
    dense[:, crowd.parent[pi]] += dense[:, pi]; dense[:, pi] = 0.0
    dead = dense.sum(1) < 1e-6; dense[dead, 0] = 1.0
    dense /= dense.sum(1, keepdims=True)
    return dense, Pu


def top4(dense):
    top = np.argsort(-dense, axis=1)[:, :4]
    tw = np.take_along_axis(dense, top, 1); tw /= np.maximum(tw.sum(1, keepdims=True), 1e-9)
    out = np.zeros_like(dense); np.put_along_axis(out, top, tw, 1)
    return out


def refit(item, log=print, smooth=3):
    name = item['name']; glb = os.path.expanduser(item['glb']); female = bool(item.get('female'))
    crowd = CF.Crowd(NPC, 'f_casual' if female else 'm_tee')
    with tempfile.TemporaryDirectory() as wd:
        P, N, UV, F = raw_lod(glb, wd, item.get('yaw', -90))
    log(f'{name}: raw {len(P)} verts {len(F)} tris')
    Pn = CF.normalise_like(P, P, crowd)
    fx = os.path.join(OUT, name + '_fit.json')
    if os.path.exists(fx):
        d = json.load(open(fx)); x = np.array(d['x']); rms = d['rms']
    else:
        x, rms = CF.fit_pose(crowd, Pn, log)
        json.dump({'x': x.tolist(), 'rms': rms}, open(fx, 'w'))
    S = crowd.skin_mats(CF.pose_from(x))
    first, welded = weld(Pn)
    dense_u, Pu = transfer_welded(crowd, S, Pn, N, F, welded, smooth=smooth)
    dense_u = top4(dense_u)
    # un-pose each WELDED vertex with its own blended matrix; corner normals use their welded vertex's matrix
    B = np.einsum('vb,bij->vij', dense_u, S)
    Bi = np.linalg.inv(B)
    Rw = np.einsum('vij,vj->vi', Bi[:, :3, :3], Pu) + Bi[:, :3, 3]
    R = Rw[welded]
    RN = np.einsum('vji,vj->vi', B[welded][:, :3, :3], N); RN /= np.linalg.norm(RN, axis=1, keepdims=True) + 1e-12
    dense = dense_u[welded]
    np.savez_compressed(os.path.join(OUT, name + '.npz'), pos=R, nrm=RN, uv=UV, idx=F, dense=dense, fit_x=x, fit_rms=rms, welded=welded,
                        pos_posed=Pn)
    log(f'{name}: fit rms {rms * 100:.1f} cm, welded {len(P)} -> {welded.max() + 1} verts, height {R[:, 1].max() - R[:, 1].min():.3f} m')
    # texture: the raw 8192 px base colour at TEX px
    j, b = read_glb(glb)
    ti = j['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']
    import io
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(io.BytesIO(image_bytes(j, b, j['images'][j['textures'][ti]['source']]))).convert('RGB').resize((TEX, TEX), Image.LANCZOS)
    im.save(os.path.join(OUT, name + '_tex.png'))
    return name


if __name__ == '__main__':
    a = sys.argv[1:]
    smooth = 3
    if '--smooth' in a:
        k = a.index('--smooth'); smooth = int(a[k + 1]); a = a[:k] + a[k + 2:]
    os.makedirs(OUT, exist_ok=True)
    byname = {c['name']: c for c in MAN}
    for n in a:
        t = time.time()
        refit(byname[n], smooth=smooth)
        print(f'{n} done in {time.time() - t:.0f}s', flush=True)

"""Measure baked-in lighting in a Tripo suit basecolor (per colour cluster, luminance vs surface normal / height).

    python3 tools/ue_char/suitmaps/analyze.py <suit>

Homage fan project, not an official Marvel/Sony/Insomniac product.
"""
import os, sys, json
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SCRATCH
Image.MAX_IMAGE_PIXELS = None


def load(suit, res=1024):
    d = os.path.join(SCRATCH, suit)
    bc = np.array(Image.open(os.path.join(SCRATCH, f'{suit}_src8k.png')).resize((res, res), Image.BOX)).astype(np.float32) / 255
    rd = lambda f: cv2.resize(cv2.imread(os.path.join(d, f), cv2.IMREAD_UNCHANGED), (res, res), interpolation=cv2.INTER_NEAREST)
    m = rd('mask.png')[..., 0] > 127
    m = cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    pos = rd('pos.exr')[..., ::-1]; nrm = rd('onrm.exr')[..., ::-1]
    ao = rd('ao.png')[..., 0].astype(np.float32) / 255
    return bc, m, pos, nrm, ao


def main(suit):
    bc, m, pos, nrm, ao = load(suit)
    lab = cv2.cvtColor(bc, cv2.COLOR_RGB2LAB)
    X = lab[m]; N = nrm[m]; Pp = pos[m]; A = ao[m]
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2)
    feat = np.stack([X[:, 0] * 0.35, X[:, 1], X[:, 2]], 1).astype(np.float32)  # cluster mostly by chroma
    _, lab_i, cen = cv2.kmeans(feat, 6, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    lab_i = lab_i.ravel()
    res = []
    for k in range(6):
        s = lab_i == k
        if s.sum() < 500: continue
        L = X[s, 0]
        rgb = cv2.cvtColor(np.array([[[L.mean(), X[s, 1].mean(), X[s, 2].mean()]]], np.float32), cv2.COLOR_LAB2RGB)[0, 0]
        # regress L on up (n.y), front (n.z), side (n.x), height (y) and AO
        D = np.stack([np.ones(s.sum()), N[s, 1], N[s, 2], N[s, 0], Pp[s, 1], A[s]], 1)
        coef, *_ = np.linalg.lstsq(D, L, rcond=None)
        pred = D @ coef; r2 = 1 - ((L - pred) ** 2).sum() / max(((L - L.mean()) ** 2).sum(), 1e-9)
        res.append(dict(k=k, frac=round(float(s.mean()), 3), rgb=[round(float(c), 3) for c in rgb], L=round(float(L.mean()), 1),
                        Lstd=round(float(L.std()), 1), up=round(float(coef[1]), 2), front=round(float(coef[2]), 2),
                        side=round(float(coef[3]), 2), height_per_m=round(float(coef[4]), 2), ao=round(float(coef[5]), 2), r2=round(float(r2), 3)))
    for r in sorted(res, key=lambda r: -r['frac']): print(suit, r)
    return res


if __name__ == '__main__':
    out = {s: main(s) for s in sys.argv[1:]}
    json.dump(out, open(os.path.join(SCRATCH, 'analyze_' + '_'.join(sys.argv[1:]) + '.json'), 'w'), indent=1)

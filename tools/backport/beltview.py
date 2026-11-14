"""Offline textured preview of a 2K19 title belt prop (pac/prop), flat and in a wrapped "worn" pose.
The pose bends every chain bone about the belt's vertical axis (z) so the strap closes into a loop, which exercises
the skin weights the way wearing it in game does. Usage: beltview.py PAC [PAC...] OUT.png"""
import os, sys, io, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import belt_port as bp, jboy, texpack, ddsread
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

def load(pac):
    P = bp.read_prop(pac); E = P['entries']
    jb = max((e for e in E if e['raw'][:4] == b'JBOY'), key=lambda e: len(e['raw']))
    tp = [e for e in E if e['raw'][:4] == b'\x03\x00\x00\x00'][0]['raw']
    T, _, _ = texpack.parse(tp); tex = {t['name']: ddsread.decode(tp[t['off']:])[1] for t in T}
    j = jboy.JBOY(jb['raw']); o = j.objs[0]
    import struct
    raw = np.frombuffer(j.b, np.dtype([('s', 'u1'), ('z', 'u1'), ('p', '>u2'), ('w', '>f4')]), o['vc'] * o['ninf'], o['f'][27] + 8).reshape(o['vc'], o['ninf'])
    bi = np.where(raw['s'] == 255, 0, raw['s']); bones = np.array([j.palette[s] for s in bi.ravel()]).reshape(bi.shape)
    tris = jboy.strip_to_tris(jboy.obj_indices(j, o)[1])
    return j, o, bones, raw['w'].astype('f8'), tris, tex

def world(j, local_rot):
    """Rest rotations are zero for belt rigs; local_rot: {bone index: 3x3}. Returns (rest pos, posed R, posed t)."""
    n = len(j.bones); rp = np.zeros((n, 3)); R = [np.eye(3)] * n; t = np.zeros((n, 3))
    for i, b in enumerate(j.bones):
        p = b['parent']; lt = np.array(b['t'], float); lr = local_rot.get(i, np.eye(3))
        if p < 0: rp[i] = lt; R[i] = lr; t[i] = lt
        else: rp[i] = rp[p] + lt; R[i] = R[p] @ lr; t[i] = t[p] + R[p] @ lt
    return rp, np.array(R), t

def rz(a): c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def rx(a): c, s = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def pose(j, o, bones, w, kind):
    if kind == 'flat': return o['pos'].astype('f8')
    names = [b['name'] for b in j.bones]; rot = {}
    for i, nm in enumerate(names):
        if nm.startswith(('bone', 'L_bone', 'R_bone')) and nm[-2:].isdigit() and int(nm[-2:]) <= 12:
            k = int(nm[-2:]); side = (1 if k <= 6 else -1) if nm.startswith('bone') else (1 if nm.startswith('L') else -1)
            rot[i] = rz(side * np.radians(28))   # 2 x 6 bones x 28 deg ~ wraps into a loop
    rp, R, t = world(j, rot)
    P = o['pos'].astype('f8'); out = np.zeros_like(P)
    for k in range(bones.shape[1]):
        b = bones[:, k]; v = P - rp[b]; out += w[:, k:k + 1] * (np.einsum('nij,nj->ni', R[b], v) + t[b])
    return out

def draw(ax, P, tris, uv, tex, view, title):
    M = {'front': np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]]), 'top': np.array([[1, 0, 0], [0, 1, 0], [0, 0, -1]]),
         'persp': rx(np.radians(-60)) @ np.eye(3)}[view]
    Q = P[tris] @ M.T
    h, wd = tex.shape[:2]; c = uv[tris].mean(1); px = np.clip((c[:, 0] * wd).astype(int), 0, wd - 1); py = np.clip((c[:, 1] * h).astype(int), 0, h - 1)
    col = tex[py, px, :3] / 255.0
    n = np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-9)[:, None]
    sh = 0.45 + 0.55 * np.abs(n[:, 2]); order = np.argsort(Q[:, :, 2].mean(1))
    ax.add_collection(PolyCollection(Q[order][:, :, :2], facecolors=np.clip(col[order] * sh[order][:, None], 0, 1), edgecolors='none', antialiaseds=False))
    ax.set_xlim(Q[:, :, 0].min() - 3, Q[:, :, 0].max() + 3); ax.set_ylim(Q[:, :, 1].min() - 3, Q[:, :, 1].max() + 3)
    ax.set_aspect('equal'); ax.set_facecolor((0.85, 0.85, 0.9)); ax.set_title(title, fontsize=9); ax.set_xticks([]); ax.set_yticks([])

def main(pacs, out):
    fig, axs = plt.subplots(len(pacs), 3, figsize=(18, 4.2 * len(pacs)), dpi=100, squeeze=False)
    for r, pac in enumerate(pacs):
        j, o, bones, w, tris, tex = load(pac); nm = os.path.basename(os.path.dirname(pac)) + '/' + os.path.basename(pac)
        cut = any(b['name'].startswith('L_bone') for b in j.bones)
        draw(axs[r][0], pose(j, o, bones, w, 'flat'), tris, o['uv'], tex['belt'], 'front', f'{nm} flat ({o["vc"]} v)')
        draw(axs[r][1], pose(j, o, bones, w, 'flat'), tris, o['uv'], tex['belt'], 'top' if cut else 'persp', 'flat, other view')
        draw(axs[r][2], pose(j, o, bones, w, 'wrap'), tris, o['uv'], tex['belt'], 'top', 'chain bent 28 deg/bone (weights test)')
    fig.tight_layout(); fig.savefig(out)

if __name__ == '__main__': main(sys.argv[1:-1], sys.argv[-1])

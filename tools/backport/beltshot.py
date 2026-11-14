"""Per-pixel renderer for 2K19 title belt props (main pac, flat pose): z-buffer, barycentric UV interpolation, back-face
culling with the 2K19 convention (normals/winding point INTO the belt, so a face is visible when its stored normal points
away from the camera), Lambert + Blinn specular from belt_p (R metal, G roughness). Used for menu images and previews.
  beltshot.py PAC OUT.png [--w 512 --h 256 --bg 0,0,0]   (writes RGBA PNG; alpha = belt coverage)"""
import sys, os, argparse, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import belt_port as bp, jboy, texpack, ddsread
from PIL import Image

def load(pac):
    P = bp.read_prop(pac); E = P['entries']
    jb = max((e for e in E if e['raw'][:4] == b'JBOY'), key=lambda e: len(e['raw']))
    tp = [e for e in E if e['raw'][:4] == b'\x03\x00\x00\x00'][0]['raw']
    tex = {t['name']: ddsread.decode(tp[t['off']:])[1].astype('f4') / 255 for t in texpack.parse(tp)[0]}
    j = jboy.JBOY(jb['raw']); o = j.objs[0]
    return o['pos'].astype('f8'), o['nrm'].astype('f8'), o['uv'].astype('f8'), jboy.strip_to_tris(jboy.obj_indices(j, o)[1]), tex

def sample(t, uv):
    h, w = t.shape[:2]; x = np.clip((uv[..., 0] % 1.0) * w, 0, w - 1).astype(int); y = np.clip((uv[..., 1] % 1.0) * h, 0, h - 1).astype(int)
    return t[y, x]

def render(pac, W=512, H=256, margin=0.04, view='front'):
    P, N, UV, T, tex = load(pac)
    # camera looks along +y (belt front faces sit at -y); screen x = world x, screen y = -world z
    S = np.c_[P[:, 0], -P[:, 2]]; depth = P[:, 1]
    lo, hi = S.min(0), S.max(0); sc = min((W * (1 - 2 * margin)) / (hi[0] - lo[0]), (H * (1 - 2 * margin)) / (hi[1] - lo[1]))
    S = (S - (lo + hi) / 2) * sc + np.array([W / 2, H / 2])
    col = np.zeros((H, W, 3)); zb = np.full((H, W), np.inf); cov = np.zeros((H, W))
    L = np.array([-0.35, -0.8, -0.45]); L /= np.linalg.norm(L); V = np.array([0, -1.0, 0]); Hh = (L + V) / np.linalg.norm(L + V)
    for a, b, c in T:
        n_face = (N[a] + N[b] + N[c])
        if n_face[1] < 0: continue                      # 2K19 convention: visible when stored normal points away (+y)
        xs, ys = S[[a, b, c], 0], S[[a, b, c], 1]
        x0, x1 = int(max(np.floor(xs.min()), 0)), int(min(np.ceil(xs.max()), W - 1)); y0, y1 = int(max(np.floor(ys.min()), 0)), int(min(np.ceil(ys.max()), H - 1))
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-12: continue
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d; w2 = 1 - w0 - w1
        m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if not m.any(): continue
        z = w0 * depth[a] + w1 * depth[b] + w2 * depth[c]
        sub = zb[y0:y1 + 1, x0:x1 + 1]; m &= z < sub
        if not m.any(): continue
        uv = (w0[..., None] * UV[a] + w1[..., None] * UV[b] + w2[..., None] * UV[c])[m]
        n = -(w0[..., None] * N[a] + w1[..., None] * N[b] + w2[..., None] * N[c])[m]; n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        base = sample(tex['belt'], uv)[:, :3]; pm = sample(tex['belt_p'], uv); metal = pm[:, 0:1]; rough = np.clip(pm[:, 1:2], 0.04, 1)
        lam = np.clip(n @ L * -1, 0, 1)[:, None]; spec = np.clip(n @ Hh * -1, 0, 1)[:, None] ** (2 / rough ** 2 * 0.25 + 4)
        diffuse = base * (1 - metal) * (0.35 + 0.75 * lam)
        f0 = 0.04 * (1 - metal) + base * metal
        env = base * metal * (0.55 + 0.45 * lam)                    # crude environment term so metal isn't black
        c_ = diffuse + env + f0 * spec * 2.5 * (1 - rough)
        sub[m] = z[m]; col[y0:y1 + 1, x0:x1 + 1][m] = np.clip(c_, 0, 1); cov[y0:y1 + 1, x0:x1 + 1][m] = 1
    return col, cov

if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('pac'); a.add_argument('out'); a.add_argument('--w', type=int, default=512); a.add_argument('--h', type=int, default=256)
    a = a.parse_args(); ss = 2
    col, cov = render(a.pac, a.w * ss, a.h * ss)
    img = Image.fromarray((np.dstack([col, cov]) * 255).astype('u1'), 'RGBA').resize((a.w, a.h), Image.LANCZOS); img.save(a.out)

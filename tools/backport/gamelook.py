"""In-game look emulator for 2K19 title props (2026-11-14, built at Matthew's request after 12 in-game rounds on the AEW belt).
Unlike beltshot.py (flat diffuse preview), this renders the way 2K19 shades props:
  - per-pixel normal mapping (belt_n, BC5 RG tangent-space, tangents from UVs),
  - metal/roughness from belt_p (R = metal, G = roughness),
  - GGX-ish specular + image-based reflections of a synthetic ARENA environment (dark ceiling, bright overhead rig spots, crowd band,
    bright ring canvas below), prefiltered by roughness; diffuse from the same environment + a key light,
  - filmic tone map.
The point is to compare a mod against stock belts *under the same lighting*, so problems show up here instead of in game.
  gamelook.py OUT.png A.pac[:label] B.pac[:label] ... [--w 900] [--cols 2] [--tilt 18]"""
import sys, os, argparse, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beltshot as bs
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------- arena environment (equirect, +z up, camera looks along +y at the belt front)
EW, EH = 256, 128
CROWD = float(os.environ.get("GL_CROWD", "1.0"))
CAMLIGHT = float(os.environ.get("GL_CAMLIGHT", "0.15"))   # light behind the camera; in-game arenas are dark there
def make_env(seed=3):
    rng = np.random.default_rng(seed)
    u = (np.arange(EW) + 0.5) / EW; v = (np.arange(EH) + 0.5) / EH
    phi, th = np.meshgrid(u * 2 * np.pi - np.pi, (0.5 - v) * np.pi)          # th = elevation
    env = np.zeros((EH, EW, 3))
    ceil = th > np.radians(32)
    env[ceil] = [0.015, 0.016, 0.022]
    for _ in range(18):                                                       # lighting rig spots
        pe, pp = np.radians(rng.uniform(40, 80)), rng.uniform(-np.pi, np.pi)
        d = np.arccos(np.clip(np.sin(th) * np.sin(pe) + np.cos(th) * np.cos(pe) * np.cos(phi - pp), -1, 1))
        env += np.exp(-(d / np.radians(2.2)) ** 2)[..., None] * np.array([1.0, 0.95, 0.85]) * rng.uniform(6, 14)
    band = (th <= np.radians(32)) & (th > np.radians(2))                      # crowd: dark, speckled colour
    noise = (rng.uniform(0, 1, (EH // 8, EW // 8, 3)) ** 2 * 0.16 + 0.05) * CROWD   # crowd: low-frequency, not pixel noise
    noise = np.stack([np.asarray(Image.fromarray((noise[..., c] * 255).astype('u1')).resize((EW, EH), Image.BILINEAR), 'f4') / 255 for c in range(3)], -1)
    env[band] = noise[band]
    led = (th > np.radians(8)) & (th < np.radians(11)); env[led] += np.array([0.5, 0.08, 0.06]) * (rng.uniform(0.5, 1, (EH, EW))[led][:, None])
    # broadcast / hard-camera lighting behind the camera (direction -y), soft and bright: what makes belts glow on TV
    dcam = np.arccos(np.clip(np.cos(th) * np.cos(phi - np.pi) * 1.0, -1, 1))   # angle from the -y horizon direction
    dcam = np.arccos(np.clip(np.sin(th) * np.sin(np.radians(25)) + np.cos(th) * np.cos(np.radians(25)) * np.cos(phi - np.pi), -1, 1))
    env += np.exp(-(dcam / np.radians(28)) ** 2)[..., None] * np.array([1.0, 0.97, 0.92]) * CAMLIGHT
    floor = th <= np.radians(2)                                               # ring canvas / apron: bright, lit from above
    env[floor] = np.array([0.55, 0.55, 0.58]) * np.clip(1.2 - (-th[floor]) / np.radians(90) * 0.8, 0.3, 1)[:, None]
    return env

def prefilter(env, levels=(0.0, 0.06, 0.12, 0.25, 0.45, 0.8)):
    out = []
    for r in levels:
        if r == 0: out.append(env); continue
        rad = max(0.6, r * r * 60 + r * 8)          # rough cone width in env pixels
        k = np.stack([np.asarray(Image.fromarray(np.clip(env[..., c] / 16 * 255, 0, 255).astype('u1')).filter(ImageFilter.GaussianBlur(rad)), 'f4') / 255 * 16 for c in range(3)], -1)
        # keep energy of the hot spots (8-bit clamp above) roughly: mix in a float blur of a downsampled map
        out.append(k)
    return np.array(levels), out

def env_lookup(maps, levels, dirs, rough):
    x, y, z = dirs[..., 0], dirs[..., 1], dirs[..., 2]
    phi = np.arctan2(x, y); th = np.arcsin(np.clip(z, -1, 1))
    ui = ((phi + np.pi) / (2 * np.pi) * EW).astype(int) % EW; vi = np.clip(((0.5 - th / np.pi) * EH).astype(int), 0, EH - 1)
    li = np.clip(np.interp(rough, levels, np.arange(len(levels))), 0, len(levels) - 1); l0 = np.floor(li).astype(int); l1 = np.minimum(l0 + 1, len(levels) - 1); f = (li - l0)[..., None]
    out = np.zeros(dirs.shape)
    for L in range(len(levels)):
        m0 = l0 == L; m1 = l1 == L
        if m0.any(): out[m0] += maps[L][vi[m0], ui[m0]] * (1 - f[m0])
        if m1.any(): out[m1] += maps[L][vi[m1], ui[m1]] * f[m1]
    return out

def irradiance(env, n):
    # cheap: heavy blur of env as diffuse lighting
    return env_lookup(IRR, np.array([0.0]), n, np.zeros(n.shape[:-1]))

# ---------------- raster
def gbuffer(pac, W, H, tilt_deg=18, margin=0.04):
    P, N, UV, T, tex = bs.load(pac)
    Ng = -N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)       # 2K19 stores inward normals
    # view: rotate belt about x so the camera looks slightly down on it (like a held-up belt), camera along +y
    t = np.radians(tilt_deg); Rx = np.array([[1, 0, 0], [0, np.cos(t), -np.sin(t)], [0, np.sin(t), np.cos(t)]])
    Pv = P @ Rx.T; Nv = Ng @ Rx.T
    S = np.c_[Pv[:, 0], -Pv[:, 2]]; depth = Pv[:, 1]
    lo, hi = S.min(0), S.max(0); sc = min(W * (1 - 2 * margin) / (hi[0] - lo[0]), H * (1 - 2 * margin) / (hi[1] - lo[1]))
    S = (S - (lo + hi) / 2) * sc + np.array([W / 2, H / 2])
    G = dict(uv=np.zeros((H, W, 2)), n=np.zeros((H, W, 3)), t=np.zeros((H, W, 3)), b=np.zeros((H, W, 3)))
    zb = np.full((H, W), np.inf); cov = np.zeros((H, W), bool)
    for a, b, c in T:
        if (Nv[a] + Nv[b] + Nv[c])[1] > 0: continue                            # back-facing (normal away from camera at -y)
        xs, ys = S[[a, b, c], 0], S[[a, b, c], 1]
        x0, x1 = int(max(np.floor(xs.min()), 0)), int(min(np.ceil(xs.max()), W - 1)); y0, y1 = int(max(np.floor(ys.min()), 0)), int(min(np.ceil(ys.max()), H - 1))
        if x1 < x0 or y1 < y0: continue
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-12: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d; w2 = 1 - w0 - w1
        m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        z = w0 * depth[a] + w1 * depth[b] + w2 * depth[c]; sub = zb[y0:y1 + 1, x0:x1 + 1]; m &= z < sub
        if not m.any(): continue
        # triangle tangent frame from UVs
        e1, e2 = Pv[b] - Pv[a], Pv[c] - Pv[a]; du1, dv1 = UV[b] - UV[a]; du2, dv2 = UV[c] - UV[a]
        r = du1 * dv2 - du2 * dv1; r = 1 / r if abs(r) > 1e-12 else 0
        tg = (e1 * dv2 - e2 * dv1) * r; bt = (e2 * du1 - e1 * du2) * r
        win = (slice(y0, y1 + 1), slice(x0, x1 + 1)); sub[m] = z[m]; cov[win][m] = True
        G['uv'][win][m] = (w0[..., None] * UV[a] + w1[..., None] * UV[b] + w2[..., None] * UV[c])[m]
        G['n'][win][m] = (w0[..., None] * Nv[a] + w1[..., None] * Nv[b] + w2[..., None] * Nv[c])[m]
        G['t'][win][m] = tg; G['b'][win][m] = bt
    return G, cov, tex

def shade(G, cov, tex, nsign=(1, 1), expo=1.0):
    uv = G['uv'][cov]
    base = bs.sample(tex['belt'], uv)[:, :3] ** 2.2                             # sRGB -> linear
    pm = bs.sample(tex['belt_p'], uv); metal = pm[:, 0:1]; rough = np.clip(pm[:, 1:2], 0.03, 1)
    nt = bs.sample(tex['belt_n'], uv); tx = (nt[:, 0] * 2 - 1) * nsign[0]; ty = (nt[:, 1] * 2 - 1) * nsign[1]
    tz = np.sqrt(np.clip(1 - tx ** 2 - ty ** 2, 0, 1))
    n = G['n'][cov]; n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    t = G['t'][cov]; t = t - n * (t * n).sum(1, keepdims=True); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-9
    b = G['b'][cov]; hand = np.sign((np.cross(n, t) * b).sum(1, keepdims=True)); bb = np.cross(n, t) * hand
    nn = t * tx[:, None] + bb * ty[:, None] + n * tz[:, None]; nn /= np.linalg.norm(nn, axis=1, keepdims=True) + 1e-9
    V = np.array([0, -1.0, 0])                                                  # towards camera
    ndv = np.clip((nn * V).sum(1, keepdims=True), 1e-3, 1)
    R = 2 * ndv * nn - V
    F0 = 0.04 * (1 - metal) + base * metal
    F = F0 + (1 - F0) * (1 - ndv) ** 5 * (1 - rough)                          # Schlick, damped by roughness
    spec = env_lookup(PRE, LEV, R, rough[:, 0]) * F
    # key light (overhead rig, slightly in front) - adds sharp GGX highlight
    L = np.array([0.25, -0.55, 0.8]); L /= np.linalg.norm(L); H = (L + V) / np.linalg.norm(L + V)
    a2 = rough ** 4 + 1e-4; nh = np.clip((nn * H).sum(1, keepdims=True), 0, 1); nl = np.clip((nn * L).sum(1, keepdims=True), 0, 1)
    D = a2 / (np.pi * (nh ** 2 * (a2 - 1) + 1) ** 2)
    spec += np.clip(D, 0, 60) * F * nl * 2.2 * 0.25
    diff = base * (1 - metal) * (env_lookup(IRRM, np.array([0.0]), nn, np.zeros(len(nn))) + nl * 2.0) * 0.9
    c = (diff + spec) * expo
    c = (c * (2.51 * c + 0.03)) / (c * (2.43 * c + 0.59) + 0.14)               # ACES-ish filmic
    out = np.zeros(G['uv'].shape[:2] + (3,)); out[cov] = np.clip(c, 0, 1) ** (1 / 2.2)
    return out

ENV = make_env(); LEV, PRE = prefilter(ENV)
IRRM = [np.stack([np.asarray(Image.fromarray(np.clip(ENV[..., k] / 16 * 255, 0, 255).astype('u1')).resize((16, 8), Image.BOX).resize((EW, EH), Image.BILINEAR), 'f4') / 255 * 16 for k in range(3)], -1)]

def main():
    a = argparse.ArgumentParser(); a.add_argument('out'); a.add_argument('pacs', nargs='+'); a.add_argument('--w', type=int, default=900)
    a.add_argument('--cols', type=int, default=2); a.add_argument('--tilt', type=float, default=18); a.add_argument('--nsign', default='1,1')
    a.add_argument('--expo', type=float, default=1.0); a = a.parse_args()
    ns = tuple(int(x) for x in a.nsign.split(',')); W = a.w; H = W // 2
    tiles = []
    for spec in a.pacs:
        p, _, lab = spec.partition(':')
        G, cov, tex = gbuffer(p, 2 * W, 2 * H, a.tilt); img = shade(G, cov, tex, ns, a.expo)
        bg = np.zeros((2 * H, 2 * W, 3)) + np.array([0.09, 0.09, 0.11]); img = np.where(cov[..., None], img, bg)
        im = Image.fromarray((img * 255).astype('u1')).resize((W, H), Image.LANCZOS); d = ImageDraw.Draw(im)
        try: F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', max(14, W // 40))
        except Exception: F = ImageFont.load_default()
        d.text((10, 8), lab or os.path.basename(p), font=F, fill=(235, 235, 235)); tiles.append(im); print('rendered', lab or p, flush=True)
    rows = (len(tiles) + a.cols - 1) // a.cols; sheet = Image.new('RGB', (W * a.cols, H * rows), (20, 20, 24))
    for i, im in enumerate(tiles): sheet.paste(im, ((i % a.cols) * W, (i // a.cols) * H))
    sheet.save(a.out); print('wrote', a.out)

if __name__ == '__main__': main()

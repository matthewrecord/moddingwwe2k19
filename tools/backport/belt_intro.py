"""Title-match intro video for a backported belt: the belt rendered from its own 2K19 prop (front view), relit every frame
with a sweeping light, slow push-in, light flare, title name fading in. Writes a 1920x1080 30 fps H.264 MP4 (default 10 s =
300 frames, the length of the stock bel_NNNN intros) for Matthew to convert to Bink2 (movies/titantron/bel_NNNN_0_0.bk2).
  belt_intro.py MAIN.pac OUT.mp4 --name "AEW UNITED STATES CHAMPIONSHIP" [--seconds 10]
G-buffer is rasterised once (beltshot's geometry/culling), shading is redone per frame in numpy."""
import sys, os, argparse, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beltshot as bs
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def gbuffer(pac, W, H, margin=0.03):
    P, N, UV, T, tex = bs.load(pac)
    S = np.c_[P[:, 0], -P[:, 2]]; depth = P[:, 1]
    lo, hi = S.min(0), S.max(0); sc = min((W * (1 - 2 * margin)) / (hi[0] - lo[0]), (H * (1 - 2 * margin)) / (hi[1] - lo[1]))
    S = (S - (lo + hi) / 2) * sc + np.array([W / 2, H / 2])
    G = {k: np.zeros((H, W, c)) for k, c in (('base', 3), ('n', 3), ('pm', 2))}; zb = np.full((H, W), np.inf); cov = np.zeros((H, W))
    for a, b, c in T:
        if (N[a] + N[b] + N[c])[1] < 0: continue
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
        z = w0 * depth[a] + w1 * depth[b] + w2 * depth[c]; sub = zb[y0:y1 + 1, x0:x1 + 1]; m &= z < sub
        if not m.any(): continue
        uv = (w0[..., None] * UV[a] + w1[..., None] * UV[b] + w2[..., None] * UV[c])[m]
        n = -(w0[..., None] * N[a] + w1[..., None] * N[b] + w2[..., None] * N[c])[m]; n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        sub[m] = z[m]; win = (slice(y0, y1 + 1), slice(x0, x1 + 1))
        G['base'][win][m] = bs.sample(tex['belt'], uv)[:, :3]; G['pm'][win][m] = bs.sample(tex['belt_p'], uv)[:, :2]
        G['n'][win][m] = n; cov[win][m] = 1
    return G, cov

def shade(G, L, gain=1.0):
    L = np.asarray(L, 'f8'); L /= np.linalg.norm(L); V = np.array([0, -1.0, 0]); Hh = (L + V) / np.linalg.norm(L + V)
    n = G['n']; base = G['base']; metal = G['pm'][..., 0:1]; rough = np.clip(G['pm'][..., 1:2], 0.04, 1)
    lam = np.clip(-(n @ L), 0, 1)[..., None]; spec = np.clip(-(n @ Hh), 0, 1)[..., None] ** (2 / rough ** 2 * 0.25 + 4)
    c = base * (1 - metal) * (0.3 + 0.8 * lam) + base * metal * (0.75 + 0.6 * lam) + (0.04 * (1 - metal) + base * metal) * spec * 3.2 * (1 - rough)
    return np.clip(c * gain, 0, 1)

def ease(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)

def font(sz):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf'):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()

def main():
    a = argparse.ArgumentParser(); a.add_argument('pac'); a.add_argument('out'); a.add_argument('--name', required=True)
    a.add_argument('--seconds', type=float, default=10); a.add_argument('--fps', type=int, default=30); a.add_argument('--preview', type=int, nargs='*')
    a = a.parse_args()
    W, H = 1920, 1080; BW, BH = 2400, 1200                       # belt rendered larger than needed so the push-in stays sharp
    G, cov = gbuffer(a.pac, BW, BH)
    nf = int(a.seconds * a.fps)
    yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot((xx - W / 2) / W, (yy - H * 0.45) / H)
    bgbase = np.clip(0.16 - 0.22 * r, 0, 1)[..., None] * np.array([1.0, 0.82, 0.55])   # warm spotlight falloff on black
    title = a.name.upper(); F = font(64)
    frames = a.preview if a.preview is not None else range(nf)
    if a.preview is None:
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(a.fps), '-i', '-',
                               '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', a.out], stdin=subprocess.PIPE)
    for f in frames:
        t = f / (nf - 1)
        # light sweeps left -> right across the plate, then settles front-high
        ang = -1.1 + 2.2 * ease(t / 0.75)
        L = [np.sin(ang) * 0.9, -0.75, -0.35 - 0.15 * np.cos(ang)]
        fade_in = ease(t / 0.12); fade_out = 1 - ease((t - 0.94) / 0.06)
        belt = shade(G, L, gain=1.45 + 0.3 * ease((t - 0.6) / 0.3))
        img = np.dstack([belt, cov])
        scale = 0.84 + 0.08 * ease(t)                                    # slow push-in
        bw = int(W * scale); bh = int(bw * BH / BW)
        pil = Image.fromarray((img * 255).astype('u1'), 'RGBA').resize((bw, bh), Image.LANCZOS)
        cy = int(H * 0.44 - bh / 2)
        canvas = Image.fromarray((bgbase * 255 * fade_in).astype('u1'), 'RGB')
        # soft glow behind the belt
        glow = pil.split()[3].resize((bw // 8, bh // 8)).filter(ImageFilter.GaussianBlur(6)).resize((bw, bh))
        g = np.asarray(glow, 'f4')[..., None] / 255 * 0.35 * fade_in
        cv = np.asarray(canvas, 'f4') / 255; x0 = (W - bw) // 2
        cv[cy:cy + bh, x0:x0 + bw] = np.clip(cv[cy:cy + bh, x0:x0 + bw] + g * np.array([1.0, 0.72, 0.35]), 0, 1)
        canvas = Image.fromarray((cv * 255).astype('u1'))
        bel = Image.fromarray((np.asarray(pil, 'f4')[..., :3] * fade_in).astype('u1')); canvas.paste(bel, (x0, cy), pil.split()[3])
        # light flare travelling with the sweep
        fx = W / 2 + np.sin(ang) * W * 0.32; fy = cy + bh * 0.5
        fl = np.exp(-(((xx - fx) / 260) ** 2 + ((yy - fy) / 26) ** 2)) * 0.55 + np.exp(-((xx - fx) ** 2 + (yy - fy) ** 2) / 70 ** 2) * 0.5
        fl *= np.sin(np.clip(t / 0.75, 0, 1) * np.pi) * fade_in
        cv = np.asarray(canvas, 'f4') / 255 + fl[..., None] * np.array([1.0, 0.9, 0.7])
        # title text
        ta = ease((t - 0.45) / 0.15) * fade_out
        txt = Image.new('L', (W, 140)); d = ImageDraw.Draw(txt); tw = d.textlength(title, font=F)
        d.text(((W - tw) / 2, 30), title, font=F, fill=255)
        ln = Image.new('L', (W, 140)); dl = ImageDraw.Draw(ln); half = tw / 2 * ease((t - 0.4) / 0.2)
        dl.rectangle([W / 2 - half, 118, W / 2 + half, 121], fill=255)
        tm = (np.asarray(txt, 'f4') + np.asarray(ln, 'f4'))[..., None] / 255 * ta; ty = int(H * 0.80)
        cv[ty:ty + 140] = cv[ty:ty + 140] * (1 - tm) + tm * np.array([1.0, 0.86, 0.55])
        cv *= fade_out
        out = (np.clip(cv, 0, 1) * 255).astype('u1')
        if a.preview is not None: Image.fromarray(out).save('%s_%03d.png' % (a.out, f))
        else: ff.stdin.write(out.tobytes())
    if a.preview is None: ff.stdin.close(); ff.wait(); print('wrote', a.out, nf, 'frames')

if __name__ == '__main__': main()

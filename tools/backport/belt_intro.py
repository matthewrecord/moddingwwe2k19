"""Title-match intro video for a backported belt: the belt rendered from its own 2K19 prop (front view), relit every frame
with a sweeping light, slow push-in, light flare, title name fading in. Writes RGBA PNG frames + a PNG-codec .mov with alpha
(the stock bel_NNNN intros are Bink2 WITH alpha, flags 0x100012), 1920x1080 30 fps (default 10 s = 300 frames, the length of the stock bel_NNNN intros) for Matthew to convert to Bink2 (movies/titantron/bel_NNNN_0_0.bk2).
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
    c = base * (1 - metal) * (0.5 + 0.75 * lam) + base * metal * (0.75 + 0.6 * lam) + (0.04 * (1 - metal) + base * metal) * spec * 3.2 * (1 - rough)
    return np.clip(c * gain, 0, 1)

def saturate(c, k):
    g = (c @ np.array([0.299, 0.587, 0.114]))[..., None]
    c = np.clip(g + (c - g) * k, 0, 1)
    return np.clip((c - 0.5) * 1.08 + 0.5, 0, 1)            # a touch of contrast

def ease(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)

def font(sz):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf'):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()

def main():
    a = argparse.ArgumentParser(); a.add_argument('pac'); a.add_argument('out'); a.add_argument('--name', required=True)
    a.add_argument('--seconds', type=float, default=10); a.add_argument('--fps', type=int, default=30); a.add_argument('--sat', type=float, default=1.6); a.add_argument('--strap-soft', type=float, default=0.0); a.add_argument('--preview', type=int, nargs='*')
    a = a.parse_args()
    W, H = 1920, 1080; BW, BH = 2400, 1200                       # belt rendered larger than needed so the push-in stays sharp
    G, cov = gbuffer(a.pac, BW, BH)
    if a.strap_soft:
        # video only: smooth, clean white strap. Strap = non-metal, unsaturated, bright texels; replace their colour by a heavily
        # blurred copy lifted toward white, and make them evenly glossy.
        b = G['base']; mx = b.max(-1); mn = b.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
        m = (G['pm'][..., 0] < 0.3) & (sat < 0.18) & (mx > 0.45) & (cov > 0)
        mf = np.asarray(Image.fromarray((m * 255).astype('u1')).filter(ImageFilter.GaussianBlur(1.5)), 'f4')[..., None] / 255
        bl = np.dstack([np.asarray(Image.fromarray((b[..., k] * 255).astype('u1')).filter(ImageFilter.GaussianBlur(10)), 'f4') / 255 for k in range(3)])
        lum = bl.mean(-1, keepdims=True); smooth = np.clip(0.93 + (lum - lum[m].mean()) * 0.35, 0, 1) * np.array([1.0, 0.985, 0.955])
        G['base'] = b * (1 - mf * a.strap_soft) + smooth * mf * a.strap_soft
        G['pm'][..., 1] = G['pm'][..., 1] * (1 - mf[..., 0] * a.strap_soft) + 0.22 * mf[..., 0] * a.strap_soft
    nf = int(a.seconds * a.fps)
    yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot((xx - W / 2) / W, (yy - H * 0.45) / H)
    bgbase = np.clip(0.16 - 0.22 * r, 0, 1)[..., None] * np.array([1.0, 0.82, 0.55])   # warm spotlight falloff on black
    title = a.name.upper(); F = font(64)
    frames = a.preview if a.preview is not None else range(nf)
    if a.preview is None:
        os.makedirs(a.out, exist_ok=True)
    if False:
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(a.fps), '-i', '-',
                               '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', a.out], stdin=subprocess.PIPE)
    for f in frames:
        t = f / (nf - 1)
        ang = -1.1 + 2.2 * ease(t / 0.62)                           # light sweep left -> right
        L = [np.sin(ang) * 0.9, -0.75, -0.35 - 0.15 * np.cos(ang)]
        fade_in = ease(t / 0.12); fade_out = 1 - ease((t - 0.94) / 0.06)
        belt = saturate(shade(G, L, gain=1.45 + 0.3 * ease((t - 0.6) / 0.3)), a.sat)
        scale = 0.84 + 0.08 * ease(t)
        bw = int(W * scale); bh = int(bw * BH / BW); x0 = (W - bw) // 2; cy = int(H * 0.44 - bh / 2)
        pil = Image.fromarray((np.dstack([belt, cov]) * 255).astype('u1'), 'RGBA').resize((bw, bh), Image.LANCZOS)
        C = np.zeros((H, W, 3), 'f4'); A = np.zeros((H, W), 'f4')
        def over(c, al, win=(slice(None), slice(None))):
            C[win] = C[win] * (1 - al[..., None]) + c * al[..., None]; A[win] = A[win] + al * (1 - A[win])
        win = (slice(cy, cy + bh), slice(x0, x0 + bw))
        glow = np.asarray(pil.split()[3].resize((bw // 8, bh // 8)).filter(ImageFilter.GaussianBlur(6)).resize((bw, bh)), 'f4') / 255
        over(np.array([1.0, 0.62, 0.18], 'f4'), glow * 0.45 * fade_in, win)
        bp = np.asarray(pil, 'f4') / 255; over(bp[..., :3], bp[..., 3] * fade_in, win)
        fx = W / 2 + np.sin(ang) * W * 0.32; fy = cy + bh * 0.5
        fl = np.exp(-(((xx - fx) / 260) ** 2 + ((yy - fy) / 26) ** 2)) * 0.55 + np.exp(-((xx - fx) ** 2 + (yy - fy) ** 2) / 70 ** 2) * 0.5
        fl = np.clip(fl * np.sin(np.clip(t / 0.62, 0, 1) * np.pi) * fade_in, 0, 1)
        over(np.array([1.0, 0.88, 0.6], 'f4'), fl.astype('f4'))
        ta = ease((t - 0.42) / 0.15) * fade_out
        txt = Image.new('L', (W, 140)); d = ImageDraw.Draw(txt); tw = d.textlength(title, font=F)
        d.text(((W - tw) / 2, 30), title, font=F, fill=255); half = tw / 2 * ease((t - 0.37) / 0.2)
        d.rectangle([W / 2 - half, 118, W / 2 + half, 121], fill=255)
        ty = int(H * 0.80); tm = np.asarray(txt, 'f4') / 255 * ta
        sh = np.asarray(txt.filter(ImageFilter.GaussianBlur(8)), 'f4') / 255 * ta * 0.7
        over(np.zeros(3, 'f4'), sh, (slice(ty, ty + 140), slice(None)))
        over(np.array([1.0, 0.80, 0.30], 'f4'), tm, (slice(ty, ty + 140), slice(None)))
        A *= fade_out
        out = np.dstack([np.clip(C, 0, 1), np.clip(A, 0, 1)])
        out = (out * 255 + 0.5).astype('u1')
        if a.preview is not None:
            Image.fromarray(out, 'RGBA').save('%s_%03d.png' % (a.out, f))
            chk = Image.new('RGBA', (W, H), (90, 90, 90, 255)); chk.alpha_composite(Image.fromarray(out, 'RGBA')); chk.convert('RGB').save('%s_%03d_ongray.jpg' % (a.out, f))
        else: Image.fromarray(out, 'RGBA').save(os.path.join(a.out, 'frame_%03d.png' % f))
    if a.preview is None:
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(a.fps), '-i', os.path.join(a.out, 'frame_%03d.png'),
                        '-c:v', 'png', '-pix_fmt', 'rgba', os.path.join(a.out, 'intro_alpha.mov')], check=True)
        print('wrote', nf, 'RGBA frames + intro_alpha.mov to', a.out)

if __name__ == '__main__': main()

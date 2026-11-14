"""Title intro video from a cut-out PHOTO of the belt (Matthew's reference photo of the real IWGP US belt, 2026-11-14), instead of a
render of the 2K19 prop. RGBA in -> 300 RGBA PNG frames (1920x1080, 30 fps) + PNG-codec .mov, for RAD's Bink2 converter with alpha
(stock bel_NNNN intros are Bink2 with alpha).
Animation: fade/scale in, slow push-in, specular light sweep across metal (gold + silver, detected by colour), travelling flare
with coloured streaks, soft drop shadow, title + underline fade-in, fade out.
Cut-out: rembg isnet mask + hand strap polygons -> GrabCut; display stand removed (cv2 inpaint) - see writeup/Belt_backport.md 29.
  photo_intro.py CUTOUT.png OUTDIR --name "AEW UNITED STATES CHAMPIONSHIP" [--preview 60 230]"""
import os, argparse, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def ease(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)

def font(sz):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf'):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()

def main():
    a = argparse.ArgumentParser(); a.add_argument('cut'); a.add_argument('out'); a.add_argument('--name', required=True)
    a.add_argument('--seconds', type=float, default=10); a.add_argument('--fps', type=int, default=30)
    a.add_argument('--width', type=float, default=0.80, help='belt width as a fraction of the frame at the end of the push-in')
    a.add_argument('--preview', type=int, nargs='*'); a = a.parse_args()
    W, H = 1920, 1080
    src = Image.open(a.cut).convert('RGBA'); bb = src.getbbox(); src = src.crop(bb)
    S = np.asarray(src, 'f4') / 255; rgb, al = S[..., :3], S[..., 3]
    mx = rgb.max(-1); mn = rgb.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]; d = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    gold = (hue > 12) & (hue < 45) & (sat > 0.35) & (mx > 0.35)
    silver = (sat < 0.12) & (mx > 0.55) & (mx < 0.92)
    metal = np.asarray(Image.fromarray(((gold | silver) * 255).astype('u1')).filter(ImageFilter.GaussianBlur(1.5)), 'f4') / 255 * al
    # slight richness + lift (the photo is already well lit; keep it bright, never shadowed)
    lum = rgb.mean(-1, keepdims=True); rgb = np.clip(lum + (rgb - lum) * 1.12, 0, 1); rgb = np.clip((rgb - 0.5) * 1.05 + 0.53, 0, 1)
    sh_, sw_ = rgb.shape[:2]; yy0, xx0 = np.mgrid[0:sh_, 0:sw_]
    ALB = np.asarray(Image.fromarray((al * 255).astype('u1')).filter(ImageFilter.GaussianBlur(25)), 'f4') / 255
    nf = int(a.seconds * a.fps); title = a.name.upper(); F = font(64)
    yy, xx = np.mgrid[0:H, 0:W]
    frames = a.preview if a.preview is not None else range(nf)
    if a.preview is None: os.makedirs(a.out, exist_ok=True)
    for f in frames:
        t = f / (nf - 1); fade_in = ease(t / 0.10); fade_out = 1 - ease((t - 0.94) / 0.06)
        # specular sweep: a soft diagonal band crossing the belt left -> right by 62% of the clip
        p = 0.06 + 0.88 * ease(t / 0.62)                     # stays on the belt (6-94% of its width)
        band_x = p * sw_ - (yy0 - sh_ / 2) * 0.35
        spec = np.exp(-((xx0 - band_x) / (sw_ * 0.06)) ** 2)[..., None]
        glint = spec * metal[..., None] * np.array([1.0, 0.92, 0.80]) * 0.75
        belt = np.clip(rgb + glint + spec * al[..., None] * 0.06, 0, 1)
        scale = (a.width - 0.06 + 0.06 * ease(t)) * (0.97 + 0.03 * fade_in)
        bw = int(W * scale); bh = int(bw * sh_ / sw_); x0 = (W - bw) // 2; cy = int(H * 0.44 - bh / 2)
        pil = Image.fromarray((np.dstack([belt, al]) * 255).astype('u1'), 'RGBA').resize((bw, bh), Image.LANCZOS)
        C = np.zeros((H, W, 3), 'f4'); A = np.zeros((H, W), 'f4')
        def over(c, alp, win=(slice(None), slice(None))):
            C[win] = C[win] * (1 - alp[..., None]) + c * alp[..., None]; A[win] = A[win] + alp * (1 - A[win])
        win = (slice(max(cy, 0), cy + bh), slice(x0, x0 + bw)); off = max(-cy, 0)
        sm = np.asarray(pil.split()[3].resize((max(bw // 6, 1), max(bh // 6, 1))).filter(ImageFilter.GaussianBlur(5)).resize((bw, bh)), 'f4') / 255
        sh = np.zeros((H, W), 'f4'); oy = int(bh * 0.05); ya, yb = cy + oy, min(H, cy + oy + bh); sh[max(ya, 0):yb, x0:x0 + bw] = sm[max(-ya, 0):yb - ya]
        over(np.zeros(3, 'f4'), sh * 0.45 * fade_in)
        bp = np.asarray(pil, 'f4')[off:] / 255; over(bp[..., :3], bp[..., 3] * fade_in, win)
        # flare riding the sweep at plate height, with coloured streaks
        fx = x0 + (p * sw_) / sw_ * bw; fy = cy + bh * 0.42; amp = np.sin(np.clip(t / 0.62, 0, 1) * np.pi) * fade_in
        # only flare where there is belt under it: sample the blurred belt alpha at the flare centre
        ix = int(np.clip(p * sw_, 0, sw_ - 1)); iy = int(sh_ * 0.42); amp *= float(ALB[iy, ix])
        core = np.exp(-((xx - fx) ** 2 + (yy - fy) ** 2) / 90 ** 2)
        streak = np.exp(-(((xx - fx) / 520) ** 2 + ((yy - fy) / 9) ** 2))
        diag1 = np.exp(-((((xx - fx) * 0.94 + (yy - fy) * 0.34) / 380) ** 2 + (((yy - fy) * 0.94 - (xx - fx) * 0.34) / 6) ** 2))
        diag2 = np.exp(-((((xx - fx) * 0.94 - (yy - fy) * 0.34) / 380) ** 2 + (((yy - fy) * 0.94 + (xx - fx) * 0.34) / 6) ** 2))
        over(np.array([1.0, 0.95, 0.85], 'f4'), np.clip(core * 0.85 * amp, 0, 1).astype('f4'))
        over(np.array([1.0, 0.75, 0.40], 'f4'), np.clip(streak * 0.55 * amp, 0, 1).astype('f4'))
        over(np.array([0.85, 0.45, 1.0], 'f4'), np.clip(diag1 * 0.45 * amp, 0, 1).astype('f4'))
        over(np.array([1.0, 0.55, 0.25], 'f4'), np.clip(diag2 * 0.40 * amp, 0, 1).astype('f4'))
        ta = ease((t - 0.42) / 0.15) * fade_out
        txt = Image.new('L', (W, 140)); dr = ImageDraw.Draw(txt); tw = dr.textlength(title, font=F)
        dr.text(((W - tw) / 2, 30), title, font=F, fill=255); half = tw / 2 * ease((t - 0.37) / 0.2)
        dr.rectangle([W / 2 - half, 118, W / 2 + half, 121], fill=255)
        ty = int(H * 0.82); tm = np.asarray(txt, 'f4') / 255 * ta
        shd = np.asarray(txt.filter(ImageFilter.GaussianBlur(8)), 'f4') / 255 * ta * 0.7
        over(np.zeros(3, 'f4'), shd, (slice(ty, ty + 140), slice(None)))
        over(np.array([0.97, 0.62, 0.36], 'f4'), tm, (slice(ty, ty + 140), slice(None)))     # copper, like the plate
        A *= fade_out
        out = (np.dstack([np.clip(C, 0, 1), np.clip(A, 0, 1)]) * 255 + 0.5).astype('u1')
        if a.preview is not None:
            Image.fromarray(out, 'RGBA').save('%s_%03d.png' % (a.out, f))
            chk = Image.new('RGBA', (W, H), (90, 90, 90, 255)); chk.alpha_composite(Image.fromarray(out, 'RGBA')); chk.convert('RGB').save('%s_%03d_ongray.jpg' % (a.out, f))
        else: Image.fromarray(out, 'RGBA').save(os.path.join(a.out, 'frame_%03d.png' % f))
    if a.preview is None:
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(a.fps), '-i', os.path.join(a.out, 'frame_%03d.png'),
                        '-c:v', 'png', '-pix_fmt', 'rgba', os.path.join(a.out, 'intro_alpha.mov')], check=True)
        print('wrote', nf, 'frames to', a.out)

if __name__ == '__main__': main()

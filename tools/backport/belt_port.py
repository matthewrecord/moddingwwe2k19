"""Backport a 2K22+ title belt mod (community .mdl + DDS) into a WWE 2K19 title belt prop pair.

2K19 title belts (pac/prop): <20xx>.pac = main belt (flat, bone01..bone14 chain), <50xx>.pac = cutscene belt
(L_bone01..12 / R_bone01..12). Both are HSPC -> SHDC -> Oodle blocks: JBOY model, texture pack (belt, belt_n,
belt_p), [nameplate JBOY + texture, font data], 800-byte block, Havok, mask texture. The 2K23 mod's Default.mdl
and Cutscene.mdl use the same bone names and nearly the same rest layout, so each mesh replaces the stock object
in place; every other block is kept. Replaced blocks are written as ZLIB (the game's loader takes ZLIB and Oodle).

Usage: python3 -I belt_port.py --mod <mod dir> --stock <prop dir> --main 2003 --cut 5003 --out <dir>
"""
import argparse, os, struct, sys, zlib, json, hashlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
import oodl, jboy, jbuild, mdl, texpack, texconv
from yukes import HSPC
import etcpak
from PIL import Image

# ---------------------------------------------------------------- containers
def shdc_files(s):
    """SHDC of a prop pac: 16-byte file entries (id, off, size, 0); table located by the first entry's offset."""
    n = struct.unpack_from('<I', s, 56)[0]
    for t in range(0x40, 0x4000, 4):
        ok = True; E = []
        for i in range(n):
            fid, off, sz, z = struct.unpack_from('<4I', s, t + 16 * i)
            if z != 0 or off < 0x40 or off + sz > len(s): ok = False; break
            E.append((fid, off, sz))
        if ok and E and E[0][1] == t + 16 * n + ((-(t + 16 * n)) % 16) and s[E[0][1]:E[0][1] + 4] in (b'OODL', b'ZLIB'):
            return t, E
    raise ValueError('SHDC table not found')
def unpack_block(blk):
    if blk[:4] == b'OODL':
        r = oodl.blocks(blk); assert r and r[0][1] is not None; return r[0][1]
    if blk[:4] == b'ZLIB': return zlib.decompress(blk[16:16 + struct.unpack_from('<I', blk, 8)[0]])
    raise ValueError(blk[:4])
CODEC = 'zlib'   # 'zlib' (small files; v1/v2 loaded every time) or 'stored' (Oodle wrapper, uncompressed: 2-3x stock size)
def oodl_block(raw):
    """Stock-style Oodle block ('OODL', 0, 0x2e060030, 'KRKN', raw size, stream size) holding a Kraken stream made of
    stored (uncompressed) 256 KB chunks: chunk header 0xCC 0x06 = restart | uncompressed | 0xC magic, decoder 6 (Kraken).
    v1/v2 used ZLIB blocks: the model loaded but the texture pack did not (belt showed the stock textures)."""
    st = b''.join(bytes([0xCC, 0x06]) + raw[i:i + 0x40000] for i in range(0, len(raw), 0x40000))
    return b'OODL' + struct.pack('<2I', 0, 0x2e060030) + b'KRKN' + struct.pack('<2I', len(raw), len(st)) + st
def zlib_block(raw):
    c = zlib.compress(raw, 9); return b'ZLIB' + struct.pack('<3I', 0x1230, len(c), len(raw)) + c
def read_prop(path):
    b = open(path, 'rb').read(); H = HSPC(b); s = H.files[0]['data']; t, E = shdc_files(s)
    return dict(H=H, s=s, table=t, entries=[dict(id=f, raw=unpack_block(s[o:o + z]), blk=s[o:o + z]) for f, o, z in E])
def write_prop(P, replaced):
    """replaced: {index: new raw bytes}. Other blocks keep their original compressed bytes."""
    s = P['s']; t = P['table']; E = P['entries']; first = struct.unpack_from('<I', s, t + 4)[0]
    out = bytearray(s[:first])
    for i, e in enumerate(E):
        out += b'\0' * ((-len(out)) % 16)
        blk = (zlib_block if CODEC == 'zlib' else oodl_block)(replaced[i]) if i in replaced else e['blk']
        struct.pack_into('<4I', out, t + 16 * i, e['id'], len(out), len(blk), 0); out += blk
    # SHDC word 15 = (end of last block - start of first block) rounded up to 4 (checked on 2001-2006, 2905 stock)
    span = len(out) - first; struct.pack_into('<I', out, 60, (span + 3) & ~3)
    H = P['H']; H.files[0]['data'] = bytes(out); return H.build()[0]

# ---------------------------------------------------------------- textures
def mips(a):
    L = [a]
    while min(L[-1].shape[:2]) > 1:
        h, w = L[-1].shape[:2]; L.append(texconv.resize(L[-1], max(1, w // 2), max(1, h // 2)))
    return L
def dds(rgba, kind):
    """kind: 'DXT1' | 'ATI2' (BC5 from R,G). Full mip chain, legacy header like the stock files."""
    data = bytearray(); L = mips(np.ascontiguousarray(rgba, dtype='u1'))
    for m in L:
        h, w = m.shape[:2]
        if w < 4 or h < 4:
            pad = np.zeros((max(4, h), max(4, w), 4), 'u1'); pad[:h, :w] = m; m = pad; h, w = m.shape[:2]
        buf = np.ascontiguousarray(m).tobytes()
        data += etcpak.compress_bc1(buf, w, h) if kind == 'DXT1' else etcpak.compress_bc5(buf, w, h)
    h, w = rgba.shape[:2]; hdr = bytearray(128); hdr[0:4] = b'DDS '
    blk = 8 if kind == 'DXT1' else 16
    struct.pack_into('<7I', hdr, 4, 124, 0x1007 | 0x80000 | 0x20000, h, w, (w // 4) * (h // 4) * blk, 0, len(L))
    struct.pack_into('<2I', hdr, 76, 32, 4); hdr[84:88] = kind.encode(); struct.pack_into('<I', hdr, 108, 0x401008)
    return bytes(hdr) + bytes(data)
def load_dds(path):
    sys.path.insert(0, HERE); import ddsread; return ddsread.decode(open(path, 'rb').read())[1]
def gold_hue(rgb, target=35.0):
    """Shift gold pixels (hue 25-70 deg, saturation > 0.2) to `target` hue, with a soft mask so silver, enamel and dark leather are
    untouched. Measured 2026-11-14: stock 2K19 gold (Stone Cold skull / Brahma Bull menu pictures) = hue 35, IWGP mod = hue 50."""
    a = rgb.astype('f4') / 255; mx = a.max(-1); mn = a.min(-1); d = mx - mn; s = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; dd = np.maximum(d, 1e-6)
    h = np.where(mx == r, ((g - b) / dd) % 6, np.where(mx == g, (b - r) / dd + 2, (r - g) / dd + 4)) * 60
    w = np.clip((s - 0.15) / 0.15, 0, 1) * np.clip(1 - np.maximum(0, np.abs(h - 47.5) - 17.5) / 10, 0, 1)
    hn = np.where(w > 0, h + (target - 50.0) * w, h)
    # HSV -> RGB with original s, v
    c = mx * s; x = c * (1 - np.abs((hn / 60) % 2 - 1)); m0 = mx - c; k = (hn // 60).astype(int) % 6
    out = np.zeros_like(a); z = np.zeros_like(c)
    for i, (p, q, t) in enumerate(((c, x, z), (x, c, z), (z, c, x), (z, x, c), (x, z, c), (c, z, x))):
        sel = k == i; out[sel] = np.stack([p[sel], q[sel], t[sel]], -1)
    out += m0[..., None]
    return np.clip(np.where(w[..., None] > 0, out, a) * 255 + 0.5, 0, 255).astype('u1')
def rgb2hsv(a):
    mx = a.max(-1); mn = a.min(-1); d = mx - mn; s = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; dd = np.maximum(d, 1e-6)
    h = np.where(mx == r, ((g - b) / dd) % 6, np.where(mx == g, (b - r) / dd + 2, (r - g) / dd + 4)) * 60
    return h, s, mx

def hsv2rgb(h, s, v):
    c = v * s; x = c * (1 - np.abs((h / 60) % 2 - 1)); m0 = v - c; k = (h // 60).astype(int) % 6
    out = np.zeros(h.shape + (3,), 'f4'); z = np.zeros_like(c)
    for i, (p, q, t) in enumerate(((c, x, z), (x, c, z), (z, c, x), (z, x, c), (x, z, c), (c, z, x))):
        sel = k == i; out[sel] = np.stack([p[sel], q[sel], t[sel]], -1)
    return out + m0[..., None]

# Colour grade toward Matthew's reference photo of the real IWGP US belt (measured 2026-11-14): gold = rose/copper hue 29,
# sat 0.66; stripes = magenta-red hue ~336, fully saturated; blue = hue 206, sat 0.8. Rules: (centre, half width, min sat,
# target hue or None, saturation multiplier, value multiplier).
GRADE_REF = [(35, 22, 0.18, 28, 1.35, 1.08), (350, 22, 0.30, 338, 1.35, 1.05), (215, 30, 0.25, 208, 1.3, 1.08)]

def color_grade(rgb, rules=GRADE_REF, strength=1.0):
    a = rgb.astype('f4') / 255; h, s, v = rgb2hsv(a); hn, sn, vn = h.copy(), s.copy(), v.copy()
    for c, hw, smin, th, sm, vm in rules:
        dh = (h - c + 180) % 360 - 180
        w = np.clip(1 - np.maximum(0, np.abs(dh) - hw) / 10, 0, 1) * np.clip((s - smin) / 0.12, 0, 1) * strength
        if th is not None: hn = hn + w * ((th - c + 180) % 360 - 180 + 0) * 0 + w * (((th - h + 180) % 360 - 180) * 0.85)
        sn = sn * (1 + w * (sm - 1)); vn = vn * (1 + w * (vm - 1))
    out = hsv2rgb(hn % 360, np.clip(sn, 0, 1), np.clip(vn, 0, 1))
    return np.clip(out * 255 + 0.5, 0, 255).astype('u1')

def build_textures(tex_dir, size, strap=None, gloss=1.0, hue=None, metalize=False, strap_smooth=0.0, grade=0.0, stock_metal=None, leather_rough=None, stock_enamel=False, banner_letters=False, cavity=0.0, metal_rough=None, nstrength=1.0, clean=False):
    def L(n): return texconv.resize(load_dds(os.path.join(tex_dir, n)), size, size)
    col = L('belt_color.DDS').copy(); col[..., 3] = 255; ORIG = col[..., :3].copy()
    if hue is not None: col[..., :3] = gold_hue(col[..., :3], hue)
    if grade:
        pl = int(0.234 * size); col[pl:, :, :3] = color_grade(col[pl:, :, :3], strength=grade)   # plates/keepers only, not the strap
    if strap is not None:
        # strap front = the flat leather band at the top of the mod's colour map (v 0..0.234, mean RGB 73,25,19). Recolour it,
        # keeping the leather grain as relative brightness variation.
        band = col[:int(0.234 * size), :, :3].astype('f4'); lum = band.mean(-1, keepdims=True); rel = lum / max(lum.mean(), 1)
        if strap_smooth:
            # smooth leather: keep the broad shading (blurred), shrink the fine grain by strap_smooth (0 = mod grain, 1 = flat)
            from PIL import Image, ImageFilter
            r8 = Image.fromarray(np.clip(rel[..., 0] * 128, 0, 255).astype('u1'))
            broad = np.asarray(r8.filter(ImageFilter.GaussianBlur(size / 256)), 'f4')[..., None] / 128
            rel = broad + (rel - broad) * (1 - strap_smooth)
            rel = 1 + (rel - 1) * (1 - 0.5 * strap_smooth)
        col[:int(0.234 * size), :, :3] = np.clip(np.array(strap, 'f4') * rel, 0, 255).astype('u1')
    N = L('belt_normal.DDS').astype(int); M = L('belt_metal.DDS')[..., 0].astype(float); R = L('belt_roughness.DDS')[..., 0].astype(float)
    if strap is not None and strap_smooth:
        hb = int(0.234 * size)                     # flatten the leather-grain bumps on the strap front toward neutral (128,128)
        N[:hb, :, :2] = np.round(128 + (N[:hb, :, :2] - 128) * (1 - strap_smooth)).astype(int)
        R[:hb] = R[:hb].mean() + (R[:hb] - R[:hb].mean()) * (1 - strap_smooth)   # even sheen, no speckle
    if metalize:
        # Match stock 2K19 plates (measured 2026-11-14 on 2905): 61% of the plate fully metallic, metal base colour mean lum ~204
        # (251,214,148). The mod marks only 26% metal with a darker photo base (lum ~174 on metal, 96 overall) -> dull brown in game.
        # Gold (hue 25-70, sat > .2) and the mod's own metal become metal 255; their base colour is scaled up to stock brightness.
        a = col[..., :3].astype('f4') / 255; mx = a.max(-1); mn = a.min(-1); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]; d = np.maximum(mx - mn, 1e-6)
        h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
        plate = np.zeros(M.shape, bool); plate[int(0.46 * size):, :] = True                  # plate/keeper photos; strap bands above
        gold = plate & (h > 20) & (h < 70) & (sat > 0.2) & (mx > 0.12)
        metal = gold | (plate & (M > 100))
        if clean:   # clean hand-made source (2K22 Grix): flat gold is gold; black inlays, logos and flags are enamel/paint, not metal
            metal = gold; M = np.where(plate & ~gold, 0.0, M)
        M = np.where(metal, 255.0, M)
        lum = a.mean(-1); cur = lum[metal & (lum > 0.08)].mean() if metal.any() else 1
        gain = np.clip(0.80 / max(cur, 1e-3), 1, 2.2)                                          # target mean lum 0.80 (stock 204/255)
        col[..., :3] = np.where(metal[..., None], np.clip(a * gain, 0, 1) * 255, col[..., :3]).astype('u1')
    if stock_metal is not None and metalize:
        # Stock 2K19 belts use a FLAT metal albedo: 2003/2010/2915 metal texels are (252,221,164) +-3 (5th-95th pct), all
        # engraving lives in the normal map. The 2K23 photo albedo has lighting/grime baked in (high-frequency contrast 45 vs
        # stock 2-8, 10% dark metal texels vs 0-2%), which read as black, dirty metal in game (v10/v11, 2026-11-14).
        # Metal texels -> flat stock colour, only very low-frequency shading (+-6%) kept; unsaturated metal -> flat silver.
        from PIL import Image, ImageFilter
        a = col[..., :3].astype('f4') / 255; mx = a.max(-1); mn = a.min(-1); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        met = M > 127; lum = a.mean(-1)
        lo = np.asarray(Image.fromarray((np.clip(lum, 0, 1) * 255).astype('u1')).filter(ImageFilter.GaussianBlur(size / 64)), 'f4') / 255
        ref = lo[met].mean() if met.any() else 1
        shade = np.clip(1 + 0.06 * (lo / max(ref, 1e-3) - 1) / 0.25, 0.94, 1.06)[..., None]
        goldc = np.array(stock_metal, 'f4') / 255; silv = np.array([0.88, 0.88, 0.90], 'f4')
        # silver = unsaturated metal that is NOT photo glare: glare in the 2K23 gold photo is bright and desaturated (v > .8),
        # which turned into white blotches on the gold (v14/v15, seen with the real arena IBL in gamelook). Majority-filter the
        # silver mask so it follows real silver parts (banners, medallion), not specks.
        silver = (sat < 0.18) & (mx < 0.8)
        silver = np.asarray(Image.fromarray((silver * 255).astype('u1')).filter(ImageFilter.ModeFilter(9)), 'u1') > 127
        tgt = np.where(silver[..., None], silv, goldc) * shade
        col[..., :3] = np.where(met[..., None], np.clip(tgt, 0, 1) * 255, col[..., :3]).astype('u1')
    ENAMEL = None
    if stock_enamel:
        # Stock enamel (WWE US 2003, measured 2026-11-14): red (222,48,49) v .87, blue (60,98,167) v .65, white (255,255,255),
        # non-metal, roughness ~0.10-0.15. The mod's enamel was 3-4x darker (red v .32, blue v .18), partly metal, rough .34.
        # Classify on the ORIGINAL mod colours: red/blue by hue, enamel white = bright unsaturated texels next to red/blue.
        from PIL import Image, ImageFilter
        a0 = ORIG.astype('f4') / 255; mx = a0.max(-1); mn = a0.min(-1); sat0 = (mx - mn) / np.maximum(mx, 1e-6)
        r, g, b = a0[..., 0], a0[..., 1], a0[..., 2]; d = np.maximum(mx - mn, 1e-6)
        hh = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
        plate = np.zeros(mx.shape, bool); plate[int(0.46 * size):, :] = True
        red = plate & ((hh > 330) | (hh < 12)) & (sat0 > 0.35) & (mx > 0.12)
        # only red that sits next to white stripes / stars (the maroon leather behind the plate photo is not enamel)
        whiteish = plate & (mx > 0.6) & (sat0 < 0.2)
        red &= np.asarray(Image.fromarray((whiteish * 255).astype('u1')).filter(ImageFilter.MaxFilter(15)), 'f4') > 0
        blue = plate & (hh > 195) & (hh < 255) & (sat0 > 0.3) & (mx > 0.06)
        near = np.asarray(Image.fromarray(((red | blue) * 255).astype('u1')).filter(ImageFilter.MaxFilter(13)), 'f4') > 0
        white = plate & near & (sat0 < 0.2) & (mx > 0.45) & ~red & ~blue
        lo = np.asarray(Image.fromarray((np.clip(a0.mean(-1), 0, 1) * 255).astype('u1')).filter(ImageFilter.GaussianBlur(size / 128)), 'f4') / 255
        for msk, c in ((red, (222, 48, 49)), (blue, (60, 98, 167)), (white, (250, 250, 252))):
            if not msk.any(): continue
            sh = np.clip(1 + 0.25 * (lo / max(lo[msk].mean(), 1e-3) - 1), 0.85, 1.08)[..., None]
            col[..., :3] = np.where(msk[..., None], np.clip(np.array(c, 'f4') * sh, 0, 255), col[..., :3]).astype('u1')
            M = np.where(msk, 0.0, M)
        ENAMEL = red | blue | white
    BANNER = None
    if banner_letters:
        # Black banners with raised letters (IWGP / UNITED STATES / CHAMPION, keeper 'UNITED STATES CHAMPION'): in the mod photo the
        # banner field is near-black and the letters are grey. Banner = closed region of near-black, unsaturated texels; inside it,
        # letters (grey) -> polished silver metal, field -> glossy black enamel (non-metal). Classified on the ORIGINAL mod colours.
        from PIL import Image, ImageFilter
        from scipy import ndimage
        a0 = ORIG.astype('f4') / 255; mx = a0.max(-1); mn = a0.min(-1); sat0 = (mx - mn) / np.maximum(mx, 1e-6)
        plate = np.zeros(mx.shape, bool); plate[int(0.46 * size):, :] = True
        dark = plate & (mx < 0.20) & (sat0 < 0.35)
        # banner = where near-black dominates the neighbourhood (letters are islands inside it); gold/enamel areas have few dark texels
        k = max(9, size // 64) | 1
        frac = ndimage.uniform_filter(dark.astype('f4'), size=k)
        band = plate & (frac > 0.38)
        bg_region = np.zeros(mx.shape, bool); bg_region[int(0.46 * size):int(0.54 * size), :] = True
        band &= ~bg_region
        letters = band & (mx > 0.26) & (sat0 < 0.28)
        letters = ndimage.binary_opening(letters, iterations=1)
        band = band & (dark | letters)                      # field = the dark texels themselves, nothing else
        field = band & ~letters
        col[..., :3] = np.where(letters[..., None], np.array([228, 228, 234], 'f4'), col[..., :3]).astype('u1')
        col[..., :3] = np.where(field[..., None], np.array([12, 12, 14], 'f4'), col[..., :3]).astype('u1')
        M = np.where(letters, 255.0, np.where(field, 0.0, M))
        BANNER = (letters, field)
    cav = None
    if cavity and stock_metal is not None:
        # Engraving definition like the community 'Big Gold New' (2009) texture: flat bright gold fields, with the engraving's
        # crevices darkened in the base colour (baked cavity/AO). Height is integrated from the mod normal map (FFT Poisson),
        # cavity = height below its local (size/128) average; only metal texels are darkened, by up to `cavity` (0..1).
        nx = N[..., 0].astype('f4') / 127.5 - 1; ny = -(N[..., 1].astype('f4') / 127.5 - 1)
        H_, W_ = nx.shape; fy = np.fft.fftfreq(H_)[:, None]; fx = np.fft.fftfreq(W_)[None, :]
        den = (2j * np.pi * fx) ** 2 + (2j * np.pi * fy) ** 2; den[0, 0] = 1
        hgt = np.real(np.fft.ifft2((np.fft.fft2(-nx) * 2j * np.pi * fx + np.fft.fft2(-ny) * 2j * np.pi * fy) / den))
        from PIL import Image, ImageFilter
        def blur(a, r): 
            lo_, hi_ = a.min(), a.max(); u8 = Image.fromarray(((a - lo_) / max(hi_ - lo_, 1e-6) * 255).astype('u1'))
            return np.asarray(u8.filter(ImageFilter.GaussianBlur(r)), 'f4') / 255 * (hi_ - lo_) + lo_
        cav = blur(hgt, size / 384) - hgt                       # > 0 in crevices (fine engraving lines)
        cav = np.clip(cav / (np.percentile(cav[M > 127], 97) + 1e-6), 0, 1)
        dark = 1 - cavity * cav * (M > 127)
        col[..., :3] = np.clip(col[..., :3].astype('f4') * dark[..., None], 0, 255).astype('u1')
    if nstrength != 1.0:   # deeper relief like the Ultra Deluxe belts (metal normal tilt ~1.5x stock)
        N = np.clip(127.5 + (N - 127.5) * nstrength, 0, 255).astype(int)
    # 2K19 belt_n: BC5, R = same sign as 2K23, G inverted (measured on stock 2003 vs mod metal edges, writeup/Belt_backport.md)
    n = np.zeros(N.shape, 'u1'); n[..., 0] = N[..., 0]; n[..., 1] = 255 - N[..., 1]; n[..., 3] = 255
    # 2K19 belt_p: R = metalness, G = roughness in the stock range (metal ~25, leather ~50), B = 255
    g = (50 - 25 * (M / 255) + 0.15 * (R - R.mean())) / gloss   # gloss > 1 = shinier (lower roughness)
    if leather_rough is not None:   # stock leather roughness 0.18-0.6 (mean ~0.4); stock metal ~0.10 (byte 25)
        g = np.where(M > 127, 25 + 0.1 * (R - R.mean()), leather_rough * 255 + 0.15 * (R - R.mean()))
    if metal_rough is not None:   # Ultra Deluxe: metal ~0.18, rougher in recesses, smoother on raised relief
        var = (0.75 + 0.6 * cav) if cav is not None else 1.0
        g = np.where(M > 127, metal_rough * 255 * var, g)
    if ENAMEL is not None: g = np.where(ENAMEL, 30.0, g)          # glossy enamel like stock (~0.12)
    if BANNER is not None: g = np.where(BANNER[0], 18.0, np.where(BANNER[1], 90.0, g))   # mirror-polished letters; satin black field (0.35) so it reads black, not a canvas mirror
    p = np.stack([M, np.clip(g, 6, 160), np.full_like(M, 255), np.full_like(M, 255)], -1).astype('u1')
    return [('belt', dds(col, 'DXT1')), ('belt_n', dds(n, 'ATI2')), ('belt_p', dds(p, 'DXT1'))]

# ---------------------------------------------------------------- mesh
def mod_mesh(path, shift):
    m = mdl.MDL(path); st = m.meshes[0]['streams']; T = m.lods()[0][0].astype(np.int64)
    P = st['POSITION'].astype('f8') + np.asarray(shift)
    Nn = st['NORMAL'][:, :3].astype('f8'); Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-9)
    Tg = st['TANGENT'][:, :3].astype('f8'); Tg /= np.maximum(np.linalg.norm(Tg, axis=1, keepdims=True), 1e-9)
    UV = st['TEXCOORD'].astype('f8'); BI = st['BI'].astype(int); BW = st['BW'].astype('f8')
    # 2K19 props store normals (and winding) pointing INTO the belt: stock 2905 front faces sit at y~-3 with normal +y,
    # 5038 front at z<0 with normal +z. The 2K23 mesh is the geometric opposite; unflipped, the game culled the plate's
    # front and showed its back faces (near-constant UVs = flat colour, v1-v3 and every diag). put_object derives the
    # winding from these normals, so negating them flips both.
    Nn = -Nn
    if len(np.unique(np.round(Tg, 3), axis=0)) < 4:   # 2K22 mdl: TANGENT stream is a constant placeholder -> derive dP/du from UVs
        Tg = uv_tangents(P, Nn, UV, T)
    names = [m.S[i] if i < len(m.S) else None for i in range(BI.max() + 1)]
    return dict(P=P, N=Nn, T=Tg, UV=UV, BI=BI, BW=BW, tris=T, names=names)
def uv_tangents(P, N, UV, T):
    p0, p1, p2 = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]; u0, u1, u2 = UV[T[:, 0]], UV[T[:, 1]], UV[T[:, 2]]
    e1, e2 = p1 - p0, p2 - p0; d1, d2 = u1 - u0, u2 - u0
    r = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]; r = np.where(np.abs(r) < 1e-12, 1e-12, r)
    t = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / r[:, None]
    acc = np.zeros_like(P); [np.add.at(acc, T[:, k], t) for k in range(3)]
    acc -= N * (acc * N).sum(1, keepdims=True); n = np.linalg.norm(acc, axis=1, keepdims=True)
    fb = np.cross(N, [0, 0, 1.0]); acc = np.where(n > 1e-9, acc / np.maximum(n, 1e-9), fb / np.maximum(np.linalg.norm(fb, axis=1, keepdims=True), 1e-9))
    return acc
def unwrap_uv(M):
    """Move every triangle's UVs into [0,1] (no triangle straddles a tile edge in the mod) by duplicating vertices."""
    T = M['tris']; tu = M['UV'][T]; off = np.floor(tu.min(1) + 1e-6)
    assert (np.floor(tu.max(1) - 1e-6) == off).all(), 'triangle crosses a UV tile edge'
    key = {}; newT = np.empty_like(T); src = []
    for t in range(len(T)):
        for c in range(3):
            k = (T[t, c], off[t, 0], off[t, 1])
            if k not in key: key[k] = len(src); src.append(k)
            newT[t, c] = key[k]
    src = np.array(src); v = src[:, 0].astype(int)
    out = {k: M[k][v] for k in ('P', 'N', 'T', 'UV', 'BI', 'BW')}; out['UV'] = out['UV'] - src[:, 1:3]
    out['tris'] = newT; out['names'] = M['names']; return out
def decimate(M, max_verts):
    """meshoptimizer simplify (keeps original vertices, so UV/normal/weight seams survive), then drop unused vertices.
    2K19 title props are 0.3-0.5 MB JBOYs (~3-6k vertices); the full 29k-vertex mod mesh (2.8 MB) froze match loading."""
    import meshoptimizer as mo
    if len(M['P']) <= max_verts: return M
    pos = np.ascontiguousarray(M['P'], 'f4'); idx = np.ascontiguousarray(M['tris'].ravel(), 'u4'); ratio = max_verts / len(M['P'])
    for _ in range(12):
        dst = np.zeros_like(idx); n = mo.simplify(dst, idx, pos, target_index_count=int(len(idx) * ratio) // 3 * 3, target_error=0.05)
        T = dst[:n].reshape(-1, 3); used = np.unique(T)
        if len(used) <= max_verts: break
        ratio *= 0.85
    remap = np.full(len(M['P']), -1); remap[used] = np.arange(len(used))
    out = {k: M[k][used] for k in ('P', 'N', 'T', 'UV', 'BI', 'BW')}; out['tris'] = remap[T].astype(np.int64); out['names'] = M['names']
    return out
def split_long(M, max_dx=3.0):
    """Split edges spanning more than max_dx cm along x (the bend axis) at their midpoint, until none is left. Decimation left
    strap triangles up to 27 cm long (stock max 3.2 cm, bones ~6-10 cm apart), which can't follow the wrap: the strap end stuck out
    at the back in game (2026-11-14). Attributes are interpolated; skin weights are merged by bone and renormalised."""
    P, N, Tg, UV = [list(M[k]) for k in ('P', 'N', 'T', 'UV')]; BI, BW = list(M['BI']), list(M['BW'])
    tris = [tuple(t) for t in M['tris']]; cache = {}
    def mid(a, b):
        k = (min(a, b), max(a, b))
        if k in cache: return cache[k]
        P.append((P[a] + P[b]) / 2); n = N[a] + N[b]; N.append(n / max(np.linalg.norm(n), 1e-9)); t = Tg[a] + Tg[b]; Tg.append(t / max(np.linalg.norm(t), 1e-9))
        UV.append((UV[a] + UV[b]) / 2); acc = {}
        for bi, bw in ((BI[a], BW[a]), (BI[b], BW[b])):
            for i, w in zip(bi, bw):
                if w > 0: acc[int(i)] = acc.get(int(i), 0) + 0.5 * w
        top = sorted(acc.items(), key=lambda x: -x[1])[:len(BI[a])]; tot = sum(w for _, w in top) or 1
        bi = np.zeros(len(BI[a]), BI[a].dtype); bw = np.zeros(len(BW[a])); 
        for q, (i, w) in enumerate(top): bi[q] = i; bw[q] = w / tot
        BI.append(bi); BW.append(bw); cache[k] = len(P) - 1; return cache[k]
    for _ in range(12):
        out = []; changed = False
        for a, b, c in tris:
            e = [(abs(P[a][0] - P[b][0]), 0), (abs(P[b][0] - P[c][0]), 1), (abs(P[c][0] - P[a][0]), 2)]; L, k = max(e)
            if L <= max_dx: out.append((a, b, c)); continue
            changed = True; v = [a, b, c]; i, j = v[k], v[(k + 1) % 3]; o = v[(k + 2) % 3]; m = mid(i, j)
            out += [(i, m, o), (m, j, o)]        # keeps winding
        tris = out
        if not changed: break
    R = dict(M); R.update(P=np.array(P), N=np.array(N), T=np.array(Tg), UV=np.array(UV), BI=np.array(BI), BW=np.array(BW), tris=np.array(tris, np.int64)); return R
def skin(M, j, ninf):
    pal = list(j.palette); slot = {j.bones[b]['name']: s for s, b in enumerate(pal)}
    parent = {b['name']: (j.bones[b['parent']]['name'] if b['parent'] >= 0 else None) for b in j.bones}
    def slot_of(nm):
        while nm is not None and nm not in slot: nm = parent.get(nm)
        return slot.get(nm, slot.get('root'))
    vc = len(M['P']); I = np.full((vc, ninf), 0xFF, int); W = np.zeros((vc, ninf))
    miss = set()
    for v in range(vc):
        acc = {}
        for b, w in zip(M['BI'][v], M['BW'][v]):
            if w <= 0: continue
            nm = M['names'][b]
            if nm not in slot: miss.add(nm)
            s = slot_of(nm); acc[s] = acc.get(s, 0) + w
        top = sorted(acc.items(), key=lambda x: -x[1])[:ninf]; tot = sum(w for _, w in top) or 1
        for k, (s, w) in enumerate(top): I[v, k] = s; W[v, k] = w / tot
    return I, W, miss
def put_object(model, j, M, I, W):
    """Write object 0 like the stock prop: skin entries = u8 palette slot, u8 0, u16 0, f32 weight (unused slot 0xFF)."""
    tris = M['tris']
    # winding: keep the stock convention (face normal agrees with vertex normals after strip decode)
    strip = jbuild.tris_to_strip(tris); back = jboy.strip_to_tris(strip)
    fn = np.cross(M['P'][back[:, 1]] - M['P'][back[:, 0]], M['P'][back[:, 2]] - M['P'][back[:, 0]])
    agree = (np.einsum('ij,ij->i', fn, M['N'][back].sum(1)) > 0).mean()
    if agree < 0.5: strip = jbuild.tris_to_strip(tris[:, [0, 2, 1]]); back = jboy.strip_to_tris(strip)
    assert len(back) == len(tris) and strip.max() < 65536
    vc = len(M['P']); ninf = W.shape[1]
    jbuild.set_object(model, 0, M['P'], M['N'], np.full((vc, 4), 255, 'u1'), M['UV'], M['T'], np.zeros((vc, ninf), int), W, strip,
                      bbox_sphere=tuple(((M['P'].min(0) + M['P'].max(0)) / 2).tolist()) + (float(np.linalg.norm(M['P'].max(0) - M['P'].min(0)) / 2),))
    S = np.zeros((vc, ninf), dtype=[('s', 'u1'), ('z', 'u1'), ('p', '>u2'), ('w', '>f4')]); S['s'] = I; S['w'] = W
    model.data[model.chunk(0, 'skin')] = bytearray(S.tobytes())
    return agree
def collapse(raw):
    """Hide a JBOY (nameplate) by putting all its vertices at the origin (degenerate, never drawn)."""
    j = jboy.JBOY(raw); b = bytearray(raw)
    for o in j.objs:
        for p in o['vptr']:
            V = np.frombuffer(b, '>f4', o['vc'] * 7, p + 8).reshape(o['vc'], 7).copy(); V[:, 0:3] = 0
            b[p + 8:p + 8 + V.nbytes] = V.astype('>f4').tobytes()
    return bytes(b)

def auto_shift(j, mdl_path):
    """Translation (x kept 0) that best aligns the mod's per-bone vertex clusters with the stock object's."""
    o = j.objs[0]; vc, ni = o['vc'], o['ninf']
    raw = np.frombuffer(j.b, np.dtype([('s', 'u1'), ('z', 'u1'), ('p', '>u2'), ('w', '>f4')]), vc * ni, o['f'][27] + 8).reshape(vc, ni)
    dom = raw['s'][np.arange(vc), raw['w'].argmax(1)]
    C = {j.bones[j.palette[s]]['name']: o['pos'][dom == s].mean(0) for s in np.unique(dom) if s != 255}
    m = mdl.MDL(mdl_path); st = m.meshes[0]['streams']; BI = st['BI'].astype(int); d = BI[np.arange(len(BI)), st['BW'].argmax(1)]
    D = [C[m.S[x]] - st['POSITION'][d == x].mean(0) for x in np.unique(d) if m.S[x] in C and m.S[x] != 'root']
    sh = np.median(np.array(D), 0); sh[0] = 0; return sh
def write_pack16(entries, head):
    """Texture pack like the stock props: every DDS starts on a 16-byte boundary (texconv.write_pack does not align)."""
    n = len(entries); out = bytearray(head[:0x10]); recs = bytearray(); data = bytearray(); base = 0x10 + 32 * n
    base += (-base) % 16
    for nm, d in entries:
        data += b'\0' * ((-len(data)) % 16)
        recs += nm.encode()[:15].ljust(16, b'\0') + b'dds\0' + struct.pack('<3I', len(d), base + len(data), 0); data += d
    data += b'\0' * ((-(base + len(data))) % 16)
    return bytes(out + recs + b'\0' * (base - 0x10 - 32 * n) + data)
def pillow_normals(M, textures, strength):
    """Stock 2K19 plates are shaded like domes: front-facing metal vertex normals spread ~40-46 deg (median) radially around each
    plate, so a plate facing the camera still catches overhead/side lights. The 2K23 plate faces are flat (median 8 deg): facing
    the camera, flat polished gold mirrors the dark arena behind the camera and reads dark/muddy in game (v10-v12, 2026-11-14;
    measured in writeup/Belt_backport.md 34). Bend each plate's front normals toward its rim: stored (inward) normal
    = normalize((-u*s, 1, -v*s)) with u, v = position relative to the plate centre / half-extent."""
    import ddsread
    bp_tex = [d for n, d in textures if n == 'belt_p'][0]; met = ddsread.decode(bp_tex)[1][..., 0] > 127
    H, W = met.shape; P, N, UV = M['P'], M['N'].copy(), M['UV']
    u = np.clip((UV[:, 0] % 1) * W, 0, W - 1).astype(int); v = np.clip((UV[:, 1] % 1) * H, 0, H - 1).astype(int)
    nn = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    mv = met[v, u]
    fa = 1 if np.abs(nn[mv, 1]).mean() >= np.abs(nn[mv, 2]).mean() else 2   # main prop faces +y, cutscene prop +z (stored)
    sg = np.sign(nn[mv, fa].sum()) or 1.0; va = 3 - fa                        # vertical axis = the other of y/z
    platetex = (UV[:, 1] % 1) >= 0.46                     # plate/keeper photos live in the lower part of the atlas (strap above)
    front = (nn[:, fa] * sg > 0.7) & platetex             # front-facing plate geometry only (not the strap)
    if not front.any(): return M, 0
    # plates along x: 1 cm bins of front plate geometry; the main plate is the run around x=0 that is much taller than the strap;
    # keepers are the remaining runs, split where the profile dips (thin bridges) or is empty
    X = P[:, 0]; Zv = P[:, va]; xb = np.floor(X).astype(int); bins = np.arange(int(X[front].min()) - 1, int(X[front].max()) + 2)
    ext = np.zeros(len(bins)); cnt = np.zeros(len(bins), int)
    for k, xv in enumerate(bins):
        sb = front & (xb == xv); cnt[k] = sb.sum()
        if sb.any(): ext[k] = Zv[sb].max() - Zv[sb].min()
    lab = np.zeros(len(bins), int); cur = 0; tall = ext >= 0.55 * ext.max()
    k0 = int(np.argmin(np.abs(bins)))
    lo_k = k0
    while lo_k > 0 and tall[lo_k - 1]: lo_k -= 1
    hi_k = k0
    while hi_k < len(bins) - 1 and tall[hi_k + 1]: hi_k += 1
    cur = 1; lab[lo_k:hi_k + 1] = cur
    dip = (cnt < 6) | (ext < 0.45 * np.median(ext[cnt >= 6]))
    for side in (range(lo_k - 1, -1, -1), range(hi_k + 1, len(bins))):
        open_seg = False
        for k in side:
            if dip[k]: open_seg = False; continue
            if not open_seg: cur += 1; open_seg = True
            lab[k] = cur
    roots = np.full(len(P), -1); idx = np.clip(xb - bins[0], 0, len(bins) - 1); roots[front] = lab[idx[front]]
    n_pl = 0
    for r in np.unique(roots[front]):
        if r <= 0: continue
        sel = front & (roots == r)
        if sel.sum() < 12: continue
        lo, hi = P[sel].min(0), P[sel].max(0); c = (lo + hi) / 2
        hx = (hi[0] - lo[0]) / 2; hz = (hi[va] - lo[va]) / 2
        if hx < 1.0 or hz < 1.0 or hx > 30: continue      # grommets / slivers / the strap itself: leave flat
        if not met[v[sel], u[sel]].any(): continue        # no metal: not a plate
        uu = (P[sel, 0] - c[0]) / hx; vv = (P[sel, va] - c[va]) / hz
        nv = np.zeros((sel.sum(), 3)); nv[:, 0] = -uu * strength; nv[:, fa] = sg; nv[:, va] = -vv * strength
        N[sel] = nv / np.linalg.norm(nv, axis=1, keepdims=True) * np.linalg.norm(N[sel], axis=1, keepdims=True); n_pl += 1
    out = dict(M); out['N'] = N; return out, n_pl

def port(stock_path, mdl_path, shift, textures, keep_nameplate=False, max_verts=6000, pillow=0.0):
    P = read_prop(stock_path); rep = {}; info = {}
    jb = [(i, e) for i, e in enumerate(P['entries']) if e['raw'][:4] == b'JBOY']
    main_i, main_e = max(jb, key=lambda x: len(x[1]['raw']))
    j = jboy.JBOY(main_e['raw']); model = jbuild.Model(j)
    assert model.build() == main_e['raw'], 'round trip failed'
    if shift is None: shift = auto_shift(j, mdl_path); info['shift'] = [round(float(x), 2) for x in shift]
    M = split_long(decimate(unwrap_uv(mod_mesh(mdl_path, shift)), max_verts))
    if pillow: M, info['pillow_plates'] = pillow_normals(M, textures, pillow)
    I, W, miss = skin(M, j, j.objs[0]['ninf'])
    info['winding_agree'] = round(float(put_object(model, j, M, I, W)), 3)
    rep[main_i] = model.build(); info.update(vc=len(M['P']), tris=len(M['tris']), unmapped_bones=sorted(x for x in miss if x))
    for i, e in enumerate(P['entries']):
        if i == main_i: continue
        if e['raw'][:4] == b'JBOY' and not keep_nameplate: rep[i] = collapse(e['raw']); info.setdefault('collapsed', []).append(i)
        if e['raw'][:4] == b'\x03\x00\x00\x00':
            names = [t['name'] for t in texpack.parse(e['raw'])[0]]
            assert names == ['belt', 'belt_n', 'belt_p'], names
            head, _ = texconv.read_pack(e['raw']); rep[i] = write_pack16(textures, head)
    return write_prop(P, rep), rep, info
def quality(pac_bytes_path):
    """Checks that caught real in-game problems (2026-11-14). Returns dict + list of warnings.
    - plate metal fraction / base brightness: stock 2905 = 0.61 / lum 204 on metal. Below ~0.45 the plate renders dull brown.
    - strap triangle span along x: stock max 3.2 cm; longer triangles can't follow the wrap (strap sticks out at the back).
    - pac size must not exceed the stock pac (oversized pacs froze match loading)."""
    import ddsread
    P = read_prop(pac_bytes_path); E = P['entries']; tp = [e for e in E if e['raw'][:4] == b'\x03\x00\x00\x00'][0]['raw']
    T = {t['name']: ddsread.decode(tp[t['off']:])[1].astype('f4') for t in texpack.parse(tp)[0]}
    j = jboy.JBOY(max((e for e in E if e['raw'][:4] == b'JBOY'), key=lambda e: len(e['raw']))['raw']); o = j.objs[0]
    tri = jboy.strip_to_tris(jboy.obj_indices(j, o)[1]); Pp, N, UV = o['pos'], o['nrm'], o['uv']
    ax = 1 if abs(Pp[:, 1]).max() < abs(Pp[:, 2]).max() and (Pp[:, 1].max() - Pp[:, 1].min()) < (Pp[:, 2].max() - Pp[:, 2].min()) else 2
    c = Pp[tri].mean(1); vis = N[tri].sum(1)[:, ax] > 0; plate = vis & (abs(c[:, 0]) < 14)
    uv = UV[tri[plate]].mean(1); h, w = T['belt'].shape[:2]; px = (np.clip(uv[:, 1], 0, .999) * h).astype(int), (np.clip(uv[:, 0], 0, .999) * w).astype(int)
    base, pm = T['belt'][px][:, :3], T['belt_p'][px]; met = pm[:, 0] > 128
    dx = Pp[tri][:, :, 0].max(1) - Pp[tri][:, :, 0].min(1); strap = abs(c[:, 0]) > 14
    q = dict(metal_fraction=round(float(met.mean()), 2), metal_base_lum=round(float(base[met].mean()), 0) if met.any() else 0,
             strap_max_span_cm=round(float(dx[strap].max()), 2), pac_bytes=os.path.getsize(pac_bytes_path))
    warn = []
    if q['metal_fraction'] < 0.45: warn.append('plate metal fraction %.2f < 0.45 (stock 0.61): will look dull -> --metalize' % q['metal_fraction'])
    if q['metal_base_lum'] < 160: warn.append('metal base colour lum %d < 160 (stock 204): dull' % q['metal_base_lum'])
    if q['strap_max_span_cm'] > 3.3: warn.append('strap triangle spans %.1f cm (stock max 3.2): strap will not wrap cleanly' % q['strap_max_span_cm'])
    return q, warn
def main():
    a = argparse.ArgumentParser(); a.add_argument('--mod', required=True); a.add_argument('--stock', required=True)
    a.add_argument('--main', default='2003'); a.add_argument('--cut', default='5003'); a.add_argument('--out', required=True)
    a.add_argument('--size', type=int, default=1024); a.add_argument('--keep-nameplate', action='store_true'); a.add_argument('--max-verts', type=int, default=6000); a.add_argument('--strap', default=None, help='R,G,B for the strap front, e.g. 235,232,225'); a.add_argument('--gloss', type=float, default=1.0); a.add_argument('--gold-hue', type=float, default=None); a.add_argument('--metalize', action='store_true'); a.add_argument('--grade', type=float, default=0.0, help='0..1 colour grade toward the reference photo (copper gold, magenta-red, vivid blue)'); a.add_argument('--stock-enamel', action='store_true'); a.add_argument('--banner-letters', action='store_true'); a.add_argument('--cavity', type=float, default=0.0); a.add_argument('--metal-rough', type=float, default=None); a.add_argument('--nstrength', type=float, default=1.0); a.add_argument('--clean', action='store_true', help='clean flat-colour source: only gold texels are metal'); a.add_argument('--pillow', type=float, default=0.0, help='dome plate normals like stock (try 1.0)'); a.add_argument('--stock-metal', default=None, help='R,G,B flat metal albedo like stock belts (stock gold 252,221,164)'); a.add_argument('--leather-rough', type=float, default=None); a.add_argument('--strap-smooth', type=float, default=0.0, help='0..1: reduce strap leather grain (colour, bumps, sheen)')
    a = a.parse_args(); os.makedirs(a.out, exist_ok=True)
    mods = {f.split('_')[-1][:-4].lower(): os.path.join(a.mod, f) for f in os.listdir(a.mod) if f.lower().endswith('.mdl')}
    tex = build_textures(os.path.join(a.mod, 'Textures'), a.size, tuple(int(x) for x in a.strap.split(',')) if a.strap else None, a.gloss, a.gold_hue, a.metalize, a.strap_smooth, a.grade, tuple(int(x) for x in a.stock_metal.split(',')) if a.stock_metal else None, a.leather_rough, a.stock_enamel, a.banner_letters, a.cavity, a.metal_rough, a.nstrength, a.clean); man = {}
    # offsets: align the mod rest layout to the stock one (per-bone cluster centroids, writeup/Belt_backport.md)
    for pid, key, shift in ((a.main, 'default', None), (a.cut, 'cutscene', None)):
        out, rep, info = port(os.path.join(a.stock, pid + '.pac'), mods[key], shift, tex, a.keep_nameplate, a.max_verts, a.pillow)
        open(os.path.join(a.out, pid + '.pac'), 'wb').write(out)
        for i, raw in rep.items(): open(os.path.join(a.out, f'{pid}_block{i}.bin'), 'wb').write(raw)
        q, warn = quality(os.path.join(a.out, pid + '.pac')); stock_size = os.path.getsize(os.path.join(a.stock, pid + '.pac'))
        if len(out) > stock_size: warn.append('pac %d bytes > stock %d: risk of load freeze' % (len(out), stock_size))
        man[pid] = dict(info, md5=hashlib.md5(out).hexdigest(), size=len(out), stock_size=stock_size, source=os.path.basename(mods[key]), quality=q, warnings=warn)
        for wmsg in warn: print('WARNING', pid, wmsg)
    print(json.dumps(man, indent=1)); open(os.path.join(a.out, 'manifest.json'), 'w').write(json.dumps(man, indent=1))
if __name__ == '__main__': main()

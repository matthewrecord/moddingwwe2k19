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
def build_textures(tex_dir, size, strap=None, gloss=1.0, hue=None):
    def L(n): return texconv.resize(load_dds(os.path.join(tex_dir, n)), size, size)
    col = L('belt_color.DDS').copy(); col[..., 3] = 255
    if hue is not None: col[..., :3] = gold_hue(col[..., :3], hue)
    if strap is not None:
        # strap front = the flat leather band at the top of the mod's colour map (v 0..0.234, mean RGB 73,25,19). Recolour it,
        # keeping the leather grain as relative brightness variation.
        band = col[:int(0.234 * size), :, :3].astype('f4'); lum = band.mean(-1, keepdims=True); rel = lum / max(lum.mean(), 1)
        col[:int(0.234 * size), :, :3] = np.clip(np.array(strap, 'f4') * rel, 0, 255).astype('u1')
    N = L('belt_normal.DDS').astype(int); M = L('belt_metal.DDS')[..., 0].astype(float); R = L('belt_roughness.DDS')[..., 0].astype(float)
    # 2K19 belt_n: BC5, R = same sign as 2K23, G inverted (measured on stock 2003 vs mod metal edges, writeup/Belt_backport.md)
    n = np.zeros(N.shape, 'u1'); n[..., 0] = N[..., 0]; n[..., 1] = 255 - N[..., 1]; n[..., 3] = 255
    # 2K19 belt_p: R = metalness, G = roughness in the stock range (metal ~25, leather ~50), B = 255
    g = (50 - 25 * (M / 255) + 0.15 * (R - R.mean())) / gloss   # gloss > 1 = shinier (lower roughness)
    p = np.stack([M, np.clip(g, 6, 90), np.full_like(M, 255), np.full_like(M, 255)], -1).astype('u1')
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
    names = [m.S[i] if i < len(m.S) else None for i in range(BI.max() + 1)]
    return dict(P=P, N=Nn, T=Tg, UV=UV, BI=BI, BW=BW, tris=T, names=names)
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
def port(stock_path, mdl_path, shift, textures, keep_nameplate=False, max_verts=6000):
    P = read_prop(stock_path); rep = {}; info = {}
    jb = [(i, e) for i, e in enumerate(P['entries']) if e['raw'][:4] == b'JBOY']
    main_i, main_e = max(jb, key=lambda x: len(x[1]['raw']))
    j = jboy.JBOY(main_e['raw']); model = jbuild.Model(j)
    assert model.build() == main_e['raw'], 'round trip failed'
    if shift is None: shift = auto_shift(j, mdl_path); info['shift'] = [round(float(x), 2) for x in shift]
    M = decimate(unwrap_uv(mod_mesh(mdl_path, shift)), max_verts)
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
def main():
    a = argparse.ArgumentParser(); a.add_argument('--mod', required=True); a.add_argument('--stock', required=True)
    a.add_argument('--main', default='2003'); a.add_argument('--cut', default='5003'); a.add_argument('--out', required=True)
    a.add_argument('--size', type=int, default=1024); a.add_argument('--keep-nameplate', action='store_true'); a.add_argument('--max-verts', type=int, default=6000); a.add_argument('--strap', default=None, help='R,G,B for the strap front, e.g. 235,232,225'); a.add_argument('--gloss', type=float, default=1.0); a.add_argument('--gold-hue', type=float, default=None)
    a = a.parse_args(); os.makedirs(a.out, exist_ok=True)
    mods = {f.split('_')[-1][:-4].lower(): os.path.join(a.mod, f) for f in os.listdir(a.mod) if f.lower().endswith('.mdl')}
    tex = build_textures(os.path.join(a.mod, 'Textures'), a.size, tuple(int(x) for x in a.strap.split(',')) if a.strap else None, a.gloss, a.gold_hue); man = {}
    # offsets: align the mod rest layout to the stock one (per-bone cluster centroids, writeup/Belt_backport.md)
    for pid, key, shift in ((a.main, 'default', None), (a.cut, 'cutscene', None)):
        out, rep, info = port(os.path.join(a.stock, pid + '.pac'), mods[key], shift, tex, a.keep_nameplate, a.max_verts)
        open(os.path.join(a.out, pid + '.pac'), 'wb').write(out)
        for i, raw in rep.items(): open(os.path.join(a.out, f'{pid}_block{i}.bin'), 'wb').write(raw)
        man[pid] = dict(info, md5=hashlib.md5(out).hexdigest(), size=len(out), source=os.path.basename(mods[key]))
    print(json.dumps(man, indent=1)); open(os.path.join(a.out, 'manifest.json'), 'w').write(json.dumps(man, indent=1))
if __name__ == '__main__': main()

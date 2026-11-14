"""Read a 2K19 arena IBL pac (pac/arena/ibl/ariblNNNNN.pac): SHDC -> Oodle blocks -> two BC6H cube arrays (DX10 DDS):
64x64 irradiance (1 mip) and 256x256 prefiltered specular (9 mips, one per roughness level), 35 cubes each, plus a JSON probe
layout (name IBL_NN, position/size in cm). Writes equirect float maps (npz) for gamelook.py.  (2026-11-14)
  arenaibl.py ARIBL.pac OUT.npz [--probe IBL_12]"""
import sys, os, struct, json, re, argparse, numpy as np, texture2ddecoder as t
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib')]
import oodl, yukes

def cube_array(x, o):
    h, w = struct.unpack_from('<2I', x, o + 12); mips = struct.unpack_from('<I', x, o + 28)[0]; fmt, dim, misc, arr, _ = struct.unpack_from('<5I', x, o + 128)
    assert fmt == 95 and misc & 4, (fmt, misc)
    sizes = [((max(1, w >> m) + 3) // 4) * ((max(1, h >> m) + 3) // 4) * 16 for m in range(mips)]
    p = o + 148; faces = []
    for a in range(arr * 6):
        fm = []
        for m in range(mips): fm.append((p, max(4, w >> m), max(4, h >> m), max(1, w >> m))); p += sizes[m]
        faces.append(fm)
    return dict(w=w, mips=mips, arr=arr, faces=faces, end=p)

def face(x, C, a, f, mip):
    p, ww, hh, real = C['faces'][a * 6 + f][mip]
    raw = t.decode_bc6(x[p:p + (ww // 4) * (hh // 4) * 16], ww, hh)
    img = np.frombuffer(raw, 'u1').reshape(hh, ww, 4)[..., [2, 1, 0]].astype('f4') / 255 if len(raw) == ww * hh * 4 else np.frombuffer(raw, 'f4').reshape(hh, ww, -1)[..., :3]
    return img[:real, :real]

def to_equirect(faces, W=256, H=128):
    """faces in D3D order +X,-X,+Y,-Y,+Z,-Z (left-handed, +Y up). Output equirect over (phi, theta) in the CUBE's frame."""
    u = (np.arange(W) + 0.5) / W; v = (np.arange(H) + 0.5) / H
    phi, th = np.meshgrid(u * 2 * np.pi - np.pi, (0.5 - v) * np.pi)
    d = np.stack([np.cos(th) * np.sin(phi), np.sin(th), np.cos(th) * np.cos(phi)], -1)   # x, y(up), z
    ax = np.abs(d); out = np.zeros((H, W, 3), 'f4')
    for fi, (axis, sgn) in enumerate([(0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)]):
        m = (ax.argmax(-1) == axis) & (np.sign(d[..., axis]) == sgn)
        if not m.any(): continue
        x, y, z = d[m, 0], d[m, 1], d[m, 2]; ma = ax[m, axis]
        if fi == 0: sc, tc = -z, -y
        elif fi == 1: sc, tc = z, -y
        elif fi == 2: sc, tc = x, z
        elif fi == 3: sc, tc = x, -z
        elif fi == 4: sc, tc = x, -y
        else: sc, tc = -x, -y
        F = faces[fi]; n = F.shape[0]
        uu = np.clip(((sc / ma + 1) / 2 * n).astype(int), 0, n - 1); vv = np.clip(((tc / ma + 1) / 2 * n).astype(int), 0, n - 1)
        out[m] = F[vv, uu]
    return out

def load(pac):
    d = yukes.HSPC(open(pac, 'rb').read()).files[0]['data']; blobs = [b for _, b in oodl.blocks(d) if b is not None]
    x = max(blobs, key=len); js = [b for b in blobs if b[:1] == b'['][0]
    offs = [m.start() for m in re.finditer(rb'DDS ', x)]
    C = [cube_array(x, o) for o in offs]; irr = min(C, key=lambda c: c['w']); pre = max(C, key=lambda c: c['w'])
    return x, irr, pre, json.loads(js)

if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('pac'); a.add_argument('out'); a.add_argument('--index', type=int, default=None); a.add_argument('--probe', default='IBL_12')
    a = a.parse_args()
    x, irr, pre, J = load(a.pac)
    names = [p['name'] for p in J]; idx = a.index if a.index is not None else int(a.probe.split('_')[1])
    print('probes', len(J), 'cubes', pre['arr'], 'using array index', idx, 'for', a.probe)
    spec = [to_equirect([face(x, pre, idx, f, m) for f in range(6)]) for m in range(pre['mips'])]
    ir = to_equirect([face(x, irr, idx, f, 0) for f in range(6)])
    np.savez_compressed(a.out, spec=np.array(spec), irr=ir, layout=json.dumps(J))
    print('wrote', a.out, 'spec mips', len(spec), 'mean radiance mip0 %.3f max %.2f' % (spec[0].mean(), spec[0].max()))

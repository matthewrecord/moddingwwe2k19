"""Control build: STOCK belt pac, only the colour texture ('belt') replaced (default: UV gradient from belt_diag).
Everything else (mesh, belt_n, belt_p, mask, havok) byte-identical. Writes OUT/<pid>.pac and a prediction render.
Usage: belt_control.py STOCK_PAC OUT_DIR"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import belt_port as bp, texconv, texpack
def uvgrad(n=1024):
    y, x = np.mgrid[0:n, 0:n]; c = np.zeros((n, n, 4), 'u1'); c[..., 0] = x * 255 // (n - 1); c[..., 1] = y * 255 // (n - 1); c[..., 3] = 255
    g = (x % (n // 16) < 4) | (y % (n // 16) < 4); c[g, :3] = 0; return c
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
P = bp.read_prop(src); rep = {}
for i, e in enumerate(P['entries']):
    if e['raw'][:4] == b'\x03\x00\x00\x00':
        T = texpack.parse(e['raw'])[0]; ents = []
        for t in T:
            d = e['raw'][t['off']:t['off'] + t['raw'][0]] if False else None
            ents.append((t['name'], bp.dds(uvgrad(), 'DXT1') if t['name'] == 'belt' else None))
        # keep stock belt_n / belt_p bytes exactly
        import struct
        recs = [(e['raw'][0x10 + 32 * k:0x10 + 32 * k + 16].split(b'\0')[0].decode(),) + struct.unpack_from('<3I', e['raw'], 0x10 + 32 * k + 20) for k in range(len(T))]
        ents = [(nm, bp.dds(uvgrad(), 'DXT1') if nm == 'belt' else e['raw'][off:off + sz]) for nm, sz, off, _ in recs]
        head, _ = texconv.read_pack(e['raw']); rep[i] = bp.write_pack16(ents, head)
pid = os.path.basename(src)[:-4]
open(os.path.join(out, pid + '.pac'), 'wb').write(bp.write_prop(P, rep)); print('written', pid, {i: len(r) for i, r in rep.items()})

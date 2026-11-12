"""Row-level editors for the four arena tables (all: HSPC > SHDC). Field layouts: WrestleMINUS MiscShowView.vb /
MiscArenaView.vb and writeup/Arena_inventory.md."""
import json, re, struct, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from yukes import HSPC, SHDC

def _open(b, fid):
    H = HSPC(b); S = SHDC(H.files[0]['data']); f = [x for x in S.files if x['id'] == fid][0]; return H, S, f
def _close(H, S):
    return H.replace(0, S.build())

# misc01_start.pac, SHDC file 2: 12-byte header, 124-byte rows. (name, offset, kind)
M01 = {'name': (0, 'I'), 'select1': (4, 'H'), 'select2': (6, 'H'), 'A1': (8, 'H'), 'A2': (10, 'H'), 'B1': (12, 'H'),
       'B2': (14, 'H'), 'B3': (16, 'H'), 'C1': (25, 'B'), 'C2': (26, 'B'), 'C3': (27, 'B'), 'C4': (28, 'B'), 'C5': (29, 'B'),
       'C6': (30, 'B'), 'C7': (31, 'B'), 'C8': (34, 'B'), 'Stage': (35, 'B'), 'D1': (38, 'B'), 'D2': (39, 'B'), 'D3': (40, 'B'),
       'D4': (41, 'B'), 'D5': (43, 'B'), 'Ref': (44, 'B'), 'F1': (56, 'I'), 'F2': (60, 'B'), 'F3': (64, 'B'), 'F4': (66, 'B'),
       'H1': (68, 'B'), 'H2': (69, 'B'), 'H3': (70, 'B'), 'H4': (71, 'B'), 'Bar': (73, 'B'), 'I1': (111, 'B'), 'I2': (112, 'B'),
       'I3': (114, 'B'), 'Live': (117, 'B'), 'J': (120, 'B')}
def misc01_rows(b):
    H, S, f = _open(b, 2); d = f['data']; return [(i, d[12 + 124 * i:12 + 124 * (i + 1)]) for i in range((len(d) - 12) // 124)]
def misc01_get(b, slot):
    for i, r in misc01_rows(b):
        if struct.unpack_from('<H', r, 4)[0] == slot:
            out = {k: struct.unpack_from('<' + t, r, o)[0] for k, (o, t) in M01.items()}; out['Filter'] = r[45:51].hex().upper(); return out
def misc01_set(b, slot, vals):
    H, S, f = _open(b, 2); d = bytearray(f['data']); hit = 0
    for i in range((len(d) - 12) // 124):
        o = 12 + 124 * i
        if struct.unpack_from('<H', d, o + 4)[0] != slot: continue
        for k, v in vals.items():
            if k == 'Filter': d[o + 45:o + 51] = bytes.fromhex(v); continue
            off, t = M01[k]; struct.pack_into('<' + t, d, o + off, v)
        hit += 1
    assert hit == 1, ('misc01 rows for slot', slot, hit)
    f['data'] = bytes(d); return _close(H, S)

# misc04_arena.pac, SHDC file 920: u32 count, 16-byte header, 32-byte entries (name16, type4, size, offset); JSON texts
def _m04_entries(d):
    n = struct.unpack_from('<I', d, 0)[0]; out = []
    for i in range(n):
        o = 16 + 32 * i; size, off = struct.unpack_from('<II', d, o + 20); out.append([d[o:o + 20], d[off:off + size]])
    return out
def misc04_get(b, slot):
    H, S, f = _open(b, 920)
    for hdr, txt in _m04_entries(f['data']):
        if hdr[:16].split(b'\0')[0] == b'arenaInfo%05d' % slot: return json.loads(txt.decode('latin1'))
def misc04_set(b, slot, vals):
    H, S, f = _open(b, 920); d = f['data']; E = _m04_entries(d); hit = 0
    for e in E:
        if e[0][:16].split(b'\0')[0] != b'arenaInfo%05d' % slot: continue
        t = e[1].decode('latin1')
        for k, v in vals.items():
            t, n = re.subn(r'("%s":)\s*-?\d+' % re.escape(k), lambda m: m.group(1) + str(v), t); assert n == 1, (k, n)
        e[1] = t.encode('latin1'); hit += 1
    assert hit == 1, ('misc04 entries for slot', slot, hit)
    # rebuild: same header, entries in the same order, data packed in the same order with the original alignment
    first = min(struct.unpack_from('<I', d, 16 + 32 * i + 24)[0] for i in range(len(E))); out = bytearray(d[:first]); align = 16
    offs = sorted((struct.unpack_from('<I', d, 16 + 32 * i + 24)[0], i) for i in range(len(E)))
    gaps = [b - a - len(E[i][1]) for (a, i), (b, _) in zip(offs, offs[1:])]
    for k, (_, i) in enumerate(offs):
        while len(out) % align: out.append(0)
        struct.pack_into('<II', out, 16 + 32 * i + 20, len(E[i][1]), len(out)); out += E[i][1] + b'\0'
    while len(out) % align: out.append(0)
    f['data'] = bytes(out); return _close(H, S)

# initposition.pac, SHDC file 0: 'WPAR', ver, count, size, then (slot, i2, i3, i4) u32 rows
def initpos_set(b, slot, i2, i3, i4):
    H, S, f = _open(b, 0); d = bytearray(f['data']); n = struct.unpack_from('<I', d, 8)[0]
    for i in range(n):
        if struct.unpack_from('<I', d, 16 + 16 * i)[0] == slot:
            struct.pack_into('<III', d, 16 + 16 * i + 4, i2, i3, i4); f['data'] = bytes(d); return _close(H, S)
    raise KeyError(('initposition has no row for', slot))
def initpos_get(b, slot):
    H, S, f = _open(b, 0); d = f['data']; n = struct.unpack_from('<I', d, 8)[0]
    for i in range(n):
        r = struct.unpack_from('<4I', d, 16 + 16 * i)
        if r[0] == slot: return r[1:]

# prm_ar_lg_color.pac, SHDC file 0: NIBJ table, 10 colour columns x 1000 slots, column-major from 0x170
def light_get(b, slot):
    H, S, f = _open(b, 0); d = f['data']; return [d[0x170 + c * 4000 + slot * 4:0x170 + c * 4000 + slot * 4 + 4].hex().upper() for c in range(10)]
def light_set(b, slot, colors):
    H, S, f = _open(b, 0); d = bytearray(f['data']); assert d[:4] == b'NIBJ' and len(colors) == 10
    for c, h in enumerate(colors): d[0x170 + c * 4000 + slot * 4:0x170 + c * 4000 + slot * 4 + 4] = bytes.fromhex(h)
    f['data'] = bytes(d); return _close(H, S)

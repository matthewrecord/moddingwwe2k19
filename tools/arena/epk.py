"""EPK8 / EPAC containers (per WrestleMINUS FilePartHandlers.vb): u32 magic, u32 header length; directory at 0x800:
per directory 12 bytes (4-char tag, u16 count-field, ...) then entries: EPK8 16 bytes (8-char name, u32 offset in
0x800 units, u32 size in 0x100 units), EPAC 12 bytes (4-char name, u32 offset, u32 size). count-field = n*4 (EPK8)
or n*3 (EPAC)."""
import struct
def parse(b):
    magic = b[:4]; hl = struct.unpack_from('<I', b, 4)[0]; es = 16 if magic == b'EPK8' else 12; div = 4 if es == 16 else 3
    dirs = []; i = 0
    while i < hl - 1:
        o = 0x800 + i; tag = b[o:o + 4]; n = struct.unpack_from('<H', b, o + 4)[0] // div; i += 12; ents = []
        for _ in range(n):
            o = 0x800 + i; nl = 8 if es == 16 else 4
            name = b[o:o + nl]; off, size = struct.unpack_from('<II', b, o + nl); ents.append({'pos': o, 'name': name, 'off': off, 'size': size}); i += es
        dirs.append({'pos': 0x800 + i, 'tag': tag, 'ents': ents})
    return {'magic': magic, 'hl': hl, 'es': es, 'dirs': dirs}
def rename(b, names):
    """Return a copy of b whose entry names are replaced, in order, by names (list of bytes)."""
    b = bytearray(b); p = parse(b); k = 0; nl = 8 if p['es'] == 16 else 4
    for d in p['dirs']:
        for e in d['ents']:
            b[e['pos']:e['pos'] + nl] = names[k].ljust(nl, b'\0')[:nl]; k += 1
    assert k == len(names), (k, len(names)); return bytes(b)
def names(b):
    return [e['name'] for d in parse(b)['dirs'] for e in d['ents']]
def tags(b):
    return [d['tag'] for d in parse(b)['dirs']]

def payload(b):
    """Inner data of a single-entry container (HSPC, EPK8 or EPAC)."""
    if b[:4] == b'HSPC':
        import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
        from yukes import HSPC
        return HSPC(b).files[0]['data']
    p = parse(b); e = p['dirs'][0]['ents'][0]; o = 0x4000 + e['off'] * 0x800
    return b[o:o + e['size'] * 0x100]

def build_single(magic, tag, name, data, tail=b"\0" * 0x800):
    """Single-entry EPK8/EPAC laid out like the game's own (directory at 0x800, data at 0x4000, 0x800 tail)."""
    es = 16 if magic == b'EPK8' else 12; nl = 8 if es == 16 else 4; div = 4 if es == 16 else 3
    pad = lambda n, a: (n + a - 1) // a * a
    d = data + b'\0' * (pad(len(data), 0x100) - len(data))
    h = bytearray(0x4000); h[0:4] = magic; struct.pack_into('<II', h, 4, 0x1c if magic == b'EPK8' else 0x18, pad(len(d), 0x800)); struct.pack_into('<I', h, 12, 7)
    h[0x800:0x804] = tag; struct.pack_into('<H', h, 0x804, div)
    if magic == b'EPK8': h[0x806] = 1
    h[0x80c:0x80c + nl] = name.ljust(nl, b'\0')[:nl]; struct.pack_into('<II', h, 0x80c + nl, 0, len(d) // 0x100)
    return bytes(h) + d + b'\0' * (pad(len(d), 0x800) - len(d)) + tail

TAIL = b''  # set by caller from a stock file of the same kind when building from scratch

def rewrap(target, data):
    """Keep the target container (and its internal name), swap its single payload."""
    if target[:4] == b'HSPC':
        import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
        from yukes import HSPC
        return HSPC(target).replace(0, data)
    p = parse(target); e = p['dirs'][0]['ents'][0]; nl = 8 if p['es'] == 16 else 4
    old_end = 0x4000 + struct.unpack_from('<I', target, 8)[0]; tail = target[old_end:]
    pad = lambda n, a: (n + a - 1) // a * a
    d = data + b'\0' * (pad(len(data), 0x100) - len(data)); body = d + b'\0' * (pad(len(d), 0x800) - len(d))
    h = bytearray(target[:0x4000]); struct.pack_into('<I', h, 8, len(body)); struct.pack_into('<I', h, e['pos'] + nl + 4, len(d) // 0x100)
    return bytes(h) + body + tail

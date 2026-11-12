"""SHDC variant used by menu match_up (match card) pacs: header 0x40, directory at w2+w3 (20-byte entries, w6 bytes),
file table at the next 16-byte boundary (w14 entries of id, offset, size, 0), files 16-aligned (seen)."""
import struct
def parse(d):
    w = list(struct.unpack_from('<16I', d, 0)); t = w[2] + w[3] + w[6]; t = (t + 15) // 16 * 16
    E = [list(struct.unpack_from('<4I', d, t + 16 * i)) for i in range(w[14])]
    return w, t, E
def files(d):
    w, t, E = parse(d); return {e[0]: d[e[1]:e[1] + e[2]] for e in E}
def build(d, repl):
    """Copy of SHDC d with files replaced ({id: bytes}); keeps header/dir/table, re-lays files in id order 16-aligned."""
    w, t, E = parse(d); first = min(e[1] for e in E); out = bytearray(d[:first])
    for i, e in sorted(enumerate(E), key=lambda x: x[1][1]):
        data = repl.get(e[0], d[e[1]:e[1] + e[2]])
        while len(out) % 16: out.append(0)
        struct.pack_into('<4I', out, t + 16 * i, e[0], len(out), len(data), e[3]); out += data
    while len(out) % 16: out.append(0)
    end_old = max(e[1] + e[2] for e in E); struct.pack_into('<I', out, 60, (w[15] + len(out) - ((end_old + 15) // 16 * 16)) & 0xffffffff)
    return bytes(out)

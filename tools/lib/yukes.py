"""Yuke's containers (WWE 2K19): HSPC (outer pac) and SHDC (inner), read + write.
Format notes: writeup/Formats.md. Writers keep every header word they do not need to change (crc is not checked).

HSPC file table entry: (offset in 2048-byte sectors, size in 256-byte units, extension tag).
SHDC file table entry: (id, byte offset, byte size, 0).
"""
import struct

def u32s(b, o, n):
    return list(struct.unpack_from('<%dI' % n, b, o))

class HSPC:
    def __init__(self, b):
        assert b[:4] == b'HSPC', 'not HSPC'
        self.raw = bytes(b)
        self.h = u32s(b, 0, 16)
        al = self.h[3]; n = self.h[14]
        if not (0 < n < 100000):
            raise ValueError('HSPC file count %d implausible' % n)
        self.dir_off = self.h[5] * al; self.tab_off = self.h[7] * al
        self.dir = [b[self.dir_off + 20 * i: self.dir_off + 20 * i + 20] for i in range(n)]
        self.files = []
        for i in range(n):
            off, sz, ext = struct.unpack_from('<3I', b, self.tab_off + 12 * i)
            self.files.append({'sector': off, 'size256': sz, 'ext': ext,
                               'data': bytes(b[off * 2048: off * 2048 + sz * 256])})
        last = max(f['sector'] * 2048 + f['size256'] * 256 for f in self.files) if self.files else 0
        self.tail_off = (last + 2047) // 2048 * 2048
        self.tail = bytes(b[self.tail_off:])

    def build(self):
        """Re-lay out files (2048-aligned, in original sector order), keep directory, tail and header words."""
        b = bytearray(self.raw[:min(f['sector'] for f in self.files) * 2048])
        order = sorted(range(len(self.files)), key=lambda i: self.files[i]['sector'])
        for i in order:
            f = self.files[i]; d = f['data']
            sector = len(b) // 2048
            pad = (-len(d)) % 256
            struct.pack_into('<3I', b, self.tab_off + 12 * i, sector, (len(d) + pad) // 256, f['ext'])
            b += d + b'\0' * pad
            b += b'\0' * ((-len(b)) % 2048)
        tail_shift = len(b) - self.tail_off
        b += self.tail
        return bytes(b), tail_shift

class SHDC:
    def __init__(self, b):
        assert b[:4] == b'SHDC', 'not SHDC'
        self.raw = bytes(b)
        self.h = u32s(b, 0, 16)
        n = self.h[14]
        if not (0 < n < 100000 and self.h[7] + 16 * n <= len(b)):
            raise ValueError('SHDC file count %d implausible' % n)
        self.dir = b[self.h[5]: self.h[5] + self.h[6]]
        self.files = []
        for i in range(n):
            fid, off, sz, z = struct.unpack_from('<4I', b, self.h[7] + 16 * i)
            self.files.append({'id': fid, 'off': off, 'data': bytes(b[off: off + sz]), 'z': z})

    def build(self):
        """Keep header/dir/table area as is up to the first file; append files in original offset order, 4-aligned
        like the originals; rewrite table offsets/sizes and total size (word 15)."""
        first = min(f['off'] for f in self.files)
        b = bytearray(self.raw[:first])
        for i in sorted(range(len(self.files)), key=lambda i: self.files[i]['off']):
            f = self.files[i]
            off = len(b)
            struct.pack_into('<4I', b, self.h[7] + 16 * i, f['id'], off, len(f['data']), f['z'])
            b += f['data']
        struct.pack_into('<I', b, 60, len(b))
        return bytes(b)

def string_table_parse(d):
    """String-table file: u32 0, u32 0, u32 count, count x (offset, length incl NUL, id), pool. -> (prefix, [(id, bytes)])"""
    pre = d[:8]; n = struct.unpack_from('<I', d, 8)[0]
    out = []
    for j in range(n):
        off, ln, i = struct.unpack_from('<3I', d, 12 + 12 * j)
        out.append((i, d[off: off + ln]))
    return pre, out

def string_table_build(pre, entries):
    """entries: [(id, bytes incl NUL)] in the order the index should have. Pool order follows index order."""
    n = len(entries); idx = bytearray(); pool = bytearray()
    base = 12 + 12 * n
    for i, s in entries:
        idx += struct.pack('<3I', base + len(pool), len(s), i); pool += s
    return bytes(pre) + struct.pack('<I', n) + bytes(idx) + bytes(pool)

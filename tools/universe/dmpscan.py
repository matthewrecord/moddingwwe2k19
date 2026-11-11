"""Scan a full-memory minidump (slots_full_*.dmp from the slots DLL test3) for the Universe per-superstar table:
records of STRIDE bytes with a character id (u32) at ID_OFF, up to CAP records.
usage: python3 dmpscan.py <dmp> [stride hex] [id_off hex] [ids comma list]"""
import mmap, struct, sys
dmp = sys.argv[1]
STRIDE = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x450
IDOFF = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x38c
MINREC = int(sys.argv[5]) if len(sys.argv) > 5 else 300
IDS = [int(v) for v in sys.argv[4].split(',')] if len(sys.argv) > 4 else [938, 939, 940, 941, 942]
f = open(dmp, 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
n, sdir = struct.unpack_from('<II', m, 8)
ranges = []
for i in range(n):
    t, sz, rva = struct.unpack_from('<III', m, sdir + 12 * i)
    if t == 9:  # Memory64ListStream
        cnt, base_rva = struct.unpack_from('<QQ', m, rva)
        off = base_rva
        for j in range(cnt):
            va, ln = struct.unpack_from('<QQ', m, rva + 16 + 16 * j)
            ranges.append((va, ln, off)); off += ln
print('ranges', len(ranges))
def u32(off): return struct.unpack_from('<I', m, off)[0]
def ok(v): return v < 1024 or v == 0x400
seen = set()
for va, ln, off in ranges:
    for want in IDS:
        p = struct.pack('<I', want); s = off
        while True:
            h = m.find(p, s, off + ln)
            if h < 0: break
            s = h + 4
            # walk back/forward along the stride while ids look plausible
            b = h
            while b - STRIDE >= off and ok(u32(b - STRIDE)): b -= STRIDE
            e = h
            while e + STRIDE + 4 <= off + ln and ok(u32(e + STRIDE)): e += STRIDE
            cnt = (e - b) // STRIDE + 1
            if cnt >= MINREC and b not in seen and len(set(u32(b + k * STRIDE) for k in range(cnt))) > cnt // 2:
                seen.add(b)
                ids = [u32(b + k * STRIDE) for k in range(cnt)]
                start_va = va + (b - off) - IDOFF
                print(f'table? va {start_va:#x} records {cnt} id {want} at rec {(h - b)//STRIDE}; '
                      f'first {ids[:8]} overflow ids {[(k, i) for k, i in enumerate(ids) if 937 <= i < 1024]} '
                      f'none(0x400) {ids.count(0x400)}')

"""WWE 2K19 PC save (Steam app 817130, userdata/<id>/817130/remote/SAVEDATA) decoder.
Layer 1: XOR with a 128-byte key indexed by file offset mod 128 (derived 2026-11-10 from zero-filled regions).
Layer 2: chunk directory of 12-byte tags (4 letters group + 4 letters kind + 4 digits, e.g. UNVSBODY0001) each followed
by u32 size; BODY chunks hold 'ZLIB' + u32 + u32 csize + u32 usize + zlib stream. Universe = UNVS* chunks.
usage: python3 savedecode.py SAVEDATA outdir   -> outdir/decoded.bin, outdir/<TAG>.bin for every ZLIB chunk, index.txt"""
import os, re, struct, sys, zlib
KEY = bytes.fromhex(
    '37363536313139383035333731373736343635363736353637363536373635363736353637363536373635363736353637363536373635'
    '363736353637363536575745324b31372a2855594844414b4a5e6b6a6864616733616a686461763531303531305e3134666e6378616'
    '43b346a705b5b5b646c73613969726e787a342d')
assert len(KEY) == 128
def decode(raw): return bytes(b ^ KEY[i & 127] for i, b in enumerate(raw))
def chunks(d):
    for m in re.finditer(rb'[A-Z0-9]{4}[A-Z]{4}\d{4}', d):
        o = m.start(); tag = m.group().decode(); size = struct.unpack_from('<I', d, o + 12)[0]
        body = None
        if d[o + 16:o + 20] == b'ZLIB':
            csize, usize = struct.unpack_from('<II', d, o + 24)
            try: body = zlib.decompress(d[o + 32:o + 32 + csize])
            except zlib.error: body = None
        yield o, tag, size, body
if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
    d = decode(open(src, 'rb').read()); assert d[:4] == b'VCGD', 'bad magic'
    open(os.path.join(out, 'decoded.bin'), 'wb').write(d)
    with open(os.path.join(out, 'index.txt'), 'w') as ix:
        for o, tag, size, body in chunks(d):
            ix.write(f'{o:#x} {tag} {size:#x} {"zlib " + hex(len(body)) if body else ""}\n')
            if body and tag.startswith('UNVS'): open(os.path.join(out, tag + '.bin'), 'wb').write(body)
    print('ok', out)

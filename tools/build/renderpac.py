r"""Build a CCT-style render pac (superstar select/matchup portrait) for character id <id> from an .OODL or .dds.

Render pac (EPK8, measured 2026-11-10 on mods\CCT\renders\...\custom_typea|b\0<id>00.pac):
  0x0000 EPK8 header: u32 0x1C, u32 size256 (= ceil(len(SHDC)/256)), u32 7 ...
  0x0800 entry 'LTSA', u16 4, u16 1, 4 x 0, name[8] = %08X of the 3rd LE u32 of MD5(
         "wwe19_singleread/texture/ssface/type{a|b}<id>"), 4 x 0, u32 size256 (same value)
  0x4000 SHDC with 2 files: 0 = BPE name list "0999_custom.dds" (constant), 1 = OODL blob of the DDS.
OODL blob (= Oodle Tools output): 'OODL', u32 0, u32 0x2E060030, 'KRKN', u32 len(dds)+0x14, u32 len(stream),
  Kraken stream, zero-padded to a multiple of 0x40. Without Oodle we write a valid Kraken stream of STORED blocks
  (per 0x40000 bytes: 2-byte block header 0xCC 0x06 + raw data); larger file, same picture.
"""
import hashlib, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'lib')]
from yukes import SHDC

def render_name(kind, cid):
    d = hashlib.md5(('wwe19_singleread/texture/ssface/type%s%d' % (kind, cid)).encode()).digest()
    return b'%08X' % struct.unpack('<4I', d)[2]

def oodl_from_dds(dds):
    assert dds[:4] == b'DDS ', 'not a DDS file'
    stream = b''.join(bytes([0xCC, 0x06]) + dds[i:i + 0x40000] for i in range(0, len(dds), 0x40000))
    b = b'OODL' + struct.pack('<II', 0, 0x2E060030) + b'KRKN' + struct.pack('<II', len(dds) + 0x14, len(stream)) + stream
    return b + b'\0' * (-len(b) % 0x40)

def build(template, oodl, kind, cid):
    assert template[:4] == b'EPK8' and template[0x800:0x804] == b'LTSA' and oodl[:4] == b'OODL'
    S = SHDC(template[0x4000:]); assert len(S.files) == 2 and S.files[1]['data'][:4] == b'OODL'
    # keep everything up to the OODL (file 0 is followed by alignment padding) and swap the OODL + its size
    off1 = S.files[1]['off']; sh = bytearray(template[0x4000:0x4000 + off1]) + oodl
    struct.pack_into('<I', sh, S.h[7] + 16 * 1 + 8, len(oodl)); sh = bytes(sh); n256 = (len(sh) + 255) // 256
    hdr = bytearray(template[:0x4000])
    struct.pack_into('<I', hdr, 0x08, n256); struct.pack_into('<I', hdr, 0x818, n256)
    hdr[0x80C:0x814] = render_name(kind, cid)
    return bytes(hdr) + sh

if __name__ == '__main__':   # self-test: rebuild a template from its own OODL
    t = open(sys.argv[1], 'rb').read(); kind, cid = sys.argv[2], int(sys.argv[3])
    o = SHDC(t[0x4000:]).files[1]['data']
    r = build(t, o, kind, cid); print('identical' if r == t else 'DIFFERENT', len(r), len(t))

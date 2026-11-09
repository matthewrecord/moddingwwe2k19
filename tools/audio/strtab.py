"""String tables: pac/string/win/string_win.pac = HSPC holding one SHDC per language (6 in SuperString's copy).
SHDC layout (measured 2026-11-09): u32 count at SHDC+0x68; then count x (offset, length, id) u32 triples;
offsets are from (index_start - 8) = SHDC+0x64; length includes the NUL; pool follows the index contiguously.
Music names: string id 13000 + music id (for music ids < 1000).
Usage: python3 -I strtab.py <string_win.pac> [id ...]"""
import struct,sys
def tables(b):
    o=0
    while True:
        o=b.find(b'SHDC',o)
        if o<0: return
        n=struct.unpack('<I',b[o+0x68:o+0x6c])[0]; e=o+0x6c
        if 0<n<500000:
            L=e-8; d={}
            for j in range(n):
                off,ln,i=struct.unpack('<3I',b[e+12*j:e+12*j+12])
                d[i]=b[L+off:L+off+ln-1].decode('latin1')
            yield o,d
        o+=4
if __name__=='__main__':
    b=open(sys.argv[1],'rb').read()
    for o,d in tables(b):
        print(hex(o),len(d),' '.join(f"{i}={d.get(int(i))!r}" for i in sys.argv[2:]))

"""Parse a Wwise AKPK package (.pck): returns (version, banks, streams, n_externals).
Each bank/stream entry = (file_id, block_size, size, start_block, lang_id); data offset = start_block*block_size.
Usage: python3 -I akpk.py <file.pck>...   (WWE 2K19 uses AKPK v1, 5-dword header after AKPK+size)"""
import struct,sys
def parse(p):
    f=open(p,'rb'); h=f.read(8); assert h[:4]==b'AKPK',p; hs=struct.unpack('<I',h[4:])[0]
    d=f.read(hs); ver,lsz,bsz,ssz,esz=struct.unpack('<5I',d[:20]); off=20+lsz
    def table(raw):
        n=struct.unpack('<I',raw[:4])[0]
        return [struct.unpack('<5I',raw[4+20*i:24+20*i]) for i in range(n)]
    b=table(d[off:off+bsz]); off+=bsz; s=table(d[off:off+ssz]); off+=ssz
    e=d[off:off+esz]; ne=struct.unpack('<I',e[:4])[0] if esz>=4 else 0
    return ver,b,s,ne
if __name__=='__main__':
    for p in sys.argv[1:]:
        try:
            ver,b,s,ne=parse(p); print(f"{p.split('/')[-1]:32s} banks={len(b):4d} streams={len(s):5d} ext={ne}")
        except Exception as x: print(p.split('/')[-1],'ERR',x)

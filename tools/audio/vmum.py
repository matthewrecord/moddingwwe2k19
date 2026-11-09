"""Read the VMUM music/movie table (WWE2K_MusicMovie.bin inside pac/audio/assetconv[_pNN].pac).
Header: 'VMUM', 16, 1000, n_records; then n x 64-byte records (16 x u32); then a C-string pool.
String offsets (fields 6, 7) are relative to the 'VMUM' magic. Field meanings: writeup/Music_map.md section 4.
Usage: python3 -I vmum.py <assetconv*.pac>..."""
import struct,sys
def load(p):
    b=open(p,'rb').read(); o=b.find(b'VMUM'); hdr=struct.unpack('<4I',b[o:o+16]); n=hdr[3]
    recs=[struct.unpack('<16I',b[o+16+64*i:o+80+64*i]) for i in range(n)]
    return b,o,hdr,recs
def cstr(b,a):
    e=b.find(b'\0',a); return b[a:e].decode('latin1')
if __name__=='__main__':
    for p in sys.argv[1:]:
        b,o,h,r=load(p); named=sum(1 for x in r if x[1])
        print(p.split('/')[-1],'records',len(r),'named',named,'music ids',min(x[2] for x in r),'-',max(x[2] for x in r))

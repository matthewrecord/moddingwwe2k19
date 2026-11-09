"""Unpack the ZLIB blocks of a Yuke's HSPC pac (e.g. pac/audio/sound*.pac).
Block = 'ZLIB', u32 ?, u32 compressed size, u32 uncompressed size, zlib stream.
Usage: python3 -I hspc.py <file.pac> [out_prefix]   (writes <out_prefix>_<offset>.bin)"""
import struct,sys,zlib
def blocks(b):
    o=0;out=[]
    while True:
        i=b.find(b'ZLIB',o)
        if i<0: break
        x,c,a=struct.unpack('<III',b[i+4:i+16])
        try: d=zlib.decompressobj().decompress(b[i+16:i+16+c]); out.append((i,a,len(d),d))
        except Exception: out.append((i,a,-1,b''))
        o=i+4
    return out
if __name__=='__main__':
    p=sys.argv[1]; b=open(p,'rb').read(); print('hdr',struct.unpack('<16I',b[:64]))
    for i,a,n,d in blocks(b):
        print(hex(i),'usize',a,'got',n,d[:16])
        if len(sys.argv)>2 and n>0: open(f"{sys.argv[2]}_{i:x}.bin",'wb').write(d)

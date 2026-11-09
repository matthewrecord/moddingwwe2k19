"""Yield every decompressible blob in a pac: ('raw',0,file), each ZLIB block, each BPE block.
Usage: python3 -I unpackall.py <file.pac> [out_prefix]"""
import struct,sys,zlib,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from bpe import expand
def blobs(b):
    yield 'raw',0,b
    o=0
    while True:
        i=b.find(b'ZLIB',o)
        if i<0: break
        try:
            x,c,a=struct.unpack('<III',b[i+4:i+16]); d=zlib.decompressobj().decompress(b[i+16:i+16+c]); yield 'zlib',i,d
        except Exception: pass
        o=i+4
    o=0
    while True:
        i=b.find(b'BPE ',o)
        if i<0: break
        try:
            h=struct.unpack('<4I',b[i+4:i+20])
            if h[0]==0x100 and 0<h[2]<20_000_000:
                d,_=expand(b,i+16,h[2]); yield 'bpe',i,d
        except Exception: pass
        o=i+4
if __name__=='__main__':
    b=open(sys.argv[1],'rb').read()
    for k,o,d in blobs(b):
        print(k,hex(o),len(d),d[:16])
        if len(sys.argv)>2 and k!='raw': open(f"{sys.argv[2]}_{k}_{o:x}.bin",'wb').write(d)

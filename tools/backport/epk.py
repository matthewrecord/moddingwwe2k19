import struct,zlib,re,sys,os
def blocks(path):
    b=open(path,'rb').read(); out=[]
    for m in re.finditer(rb'ZLIB',b):
        i=m.start(); a,c,u=struct.unpack_from('<3I',b,i+4)
        try: d=zlib.decompress(b[i+16:i+16+c])
        except Exception: continue
        if len(d)==u: out.append(d)
    return out
if __name__=='__main__':
    src,dst=sys.argv[1],sys.argv[2]; os.makedirs(dst,exist_ok=True)
    for k,d in enumerate(blocks(src)):
        ext='jboy' if d[:4]==b'JBOY' else 'bin'
        open(f'{dst}/{k:02d}.{ext}','wb').write(d)

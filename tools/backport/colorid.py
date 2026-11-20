"""DIAGNOSTIC: rewrite a built pac so every diffuse texture is one flat colour (alpha kept, so cut-outs stay).
Whatever colour an in-game artefact turns names the object that draws it. Usage: colorid.py IN.pac OUT.pac"""
import sys,os,io,zlib,struct,numpy as np;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import epkwrite,texconv
from PIL import Image
COL={'outfit':(255,0,0),'nets':(0,80,255),'metal':(255,230,0),'brassiere':(0,255,255),'all_color':(0,255,0),'hair':(255,255,255),
     'l_kneepad':(255,128,0),'r_kneepad':(255,128,0),'shoes':(255,128,0),'l_wrist':(255,0,255),'r_wrist':(255,0,255)}
hdr,bl=epkwrite.raw_blocks(sys.argv[1]); out=[]
for fid,b in bl:
    if fid==0xa:
        raw=zlib.decompress(b[16:]) if b[:4]==b'ZLIB' else b; head,E=texconv.read_pack(raw); NE=[]
        for n,d in E:
            if n in COL:
                a=np.asarray(Image.open(io.BytesIO(d)).convert('RGBA')).copy(); a[...,:3]=COL[n]; n2=texconv.dds_dxt5(a); assert len(n2)==len(d); d=d[:128]+n2[128:]   # keep the original DDS header byte-for-byte (a rewritten header hung the game)
            NE.append((n,d))
        nb=texconv.write_pack(NE,head); b=epkwrite.zblock(nb,struct.unpack_from('<I',b,4)[0]) if b[:4]==b'ZLIB' else nb
    out.append((fid,b))
open(sys.argv[2],'wb').write(epkwrite.build_raw(hdr,out)); print('wrote',sys.argv[2])

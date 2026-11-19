"""decode.py RAWDIR OUTROOT : write Characters/<id>_<Name>/... from pick.js dumps; textures get a DDS header from the archive's T_DB."""
import json,struct,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import payload
T=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'tdb.json')))
FMT={0x7fd9cd97:('DXT1',8),0x6c893e63:('DXT3',16),0x9ee2bd60:('DXT5',16),0x4a28d98b:('ATI1',8),0xb8435a88:('ATI2',16),0x59782a7f:('DXT5',16),0x85121088:('DXT5',16)}
def fnv(s):
    h=0xcbf29ce484222325
    for c in s.encode(): h=((h^c)*0x100000001b3)&((1<<64)-1)
    return h
def dds_header(w,h,mips,fourcc,block):
    top=max(1,(w+3)//4)*max(1,(h+3)//4)*block
    hd=bytearray(128); hd[0:4]=b'DDS '
    # matches the earlier AuroraForge extractions: fourcc by block size only (8 -> DXT1, 16 -> DXT5), mip flags only when mips > 1
    fourcc='DXT1' if block==8 else 'DXT5'
    struct.pack_into('<7I',hd,4,124,0x0A1007 if mips>1 else 0x081007,h,w,top,0,mips)
    struct.pack_into('<2I',hd,76,32,4); hd[84:88]=fourcc.encode(); struct.pack_into('<I',hd,108,0x400008 if mips>1 else 0x1000)
    return bytes(hd)
def run(rawdir,outroot):
    M=json.load(open(os.path.join(rawdir,'meta.json'))); bad=[]
    for m in M:
        d=payload.payload(open(os.path.join(rawdir,m['file']),'rb').read(),m)
        rel=m['name'][len('Characters/'):]
        if rel.lower().endswith('.dds'):
            r=T[m['arc']].get(str(fnv(m['native'].lower())))
            if not r: bad.append(rel); continue
            r=bytes.fromhex(r); w,h=struct.unpack_from('<HH',r,10); fmt=struct.unpack_from('<I',r,36)[0]; mips=r[41]   # T_DB: width @10, height @12 (AuroraForge's own extraction swaps portrait textures)
            fc,blk=FMT.get(fmt,('DXT5',16)); d=dds_header(w,h,mips,fc,blk)+d
        p=os.path.join(outroot,rel); os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'wb').write(d)
    return len(M),bad
if __name__=='__main__':
    n,bad=run(sys.argv[1],sys.argv[2]); print('files',n,'no-header',len(bad),bad[:5])

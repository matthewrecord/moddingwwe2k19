"""Reader for WWE 2K19 JBOY (big-endian YOBJ) character models. Reverse-engineered 2026-11-12. Offsets are +8."""
import struct, numpy as np
class JBOY:
    def __init__(s, path_or_bytes, verbose=False):
        b = s.b = open(path_or_bytes,'rb').read() if isinstance(path_or_bytes,str) else path_or_bytes
        assert b[:4]==b'JBOY'; B=8; s.h=struct.unpack_from('>16I',b,0)
        nobj=s.h[6]; nbone=s.h[8]; s.nmat=s.h[9]; bone_off=s.h[10]+B
        s.bones=[]
        for i in range(nbone):
            r=bone_off+i*80; name=b[r:r+16].split(b'\0')[0].decode('latin1')
            t=struct.unpack_from('>3f',b,r+16); rot=struct.unpack_from('>3f',b,r+32); par,=struct.unpack_from('>i',b,r+48)
            sph=struct.unpack_from('>4f',b,r+64)
            s.bones.append(dict(name=name,t=t,r=rot,parent=par,world=sph[:3]))
        npal,palp=struct.unpack_from('>2I',b,0x50); s.palette=None
        if npal:
            n,lp=struct.unpack_from('>2I',b,palp+B); s.palette=np.array(struct.unpack_from('>%dI'%n,b,lp+B))
        s.objs=[]; o=0x58
        for k in range(nobj):
            f=struct.unpack_from('>46I',b,o+k*184)
            vc=f[0]; ninf=f[23]; pos,skin,uv,uv2=f[26:30]; shader=b[o+k*184+124:o+k*184+140].split(b'\0')[0].decode()
            P=np.frombuffer(b,'>f4',vc*7,pos+B).reshape(vc,7)
            sk=np.frombuffer(b,np.dtype([('i','>u2'),('pad','>u2'),('w','>f4')]),vc*ninf,skin+B).reshape(vc,ninf) if skin else None
            UV=np.frombuffer(b,'>f4',vc*2,uv+B).reshape(vc,2) if uv else None
            s.objs.append(dict(vc=vc,ninf=ninf,shader=shader,pos=P[:,1:4].astype('f4'),nrm=P[:,4:7].astype('f4'),
                 bi=None if sk is None else s.remap(s.fix_order(sk['i'].astype(int),sk['w'])),bw=None if sk is None else sk['w'].astype('f4'),uv=UV,
                 f=f,palette=f[3:23],idx_ptr=f[39],mat=f[36]))
            if verbose: print(k,vc,ninf,shader,f[1],f[2],f[24],f[25],hex(f[29]),f[30],f[35:42])

    def fix_order(s,bi,w):
        n=len(s.palette) if s.palette is not None else len(s.bones)
        m=w>0
        if m.any() and bi[m].max()>=n:
            sw=((bi&0xff)<<8)|(bi>>8)
            if sw[m].max()<n: return sw
        return bi
    def remap(s,bi):
        if s.palette is None: return bi
        p=np.append(s.palette,[10**6]); return p[np.minimum(bi,len(s.palette))]
def strip_to_tris(ix):
    t=[]
    for k in range(len(ix)-2):
        a,b,c=ix[k],ix[k+1],ix[k+2]
        if a==b or b==c or a==c: continue
        t.append((a,b,c) if k%2==0 else (b,a,c))
    return np.array(t,dtype=np.int64).reshape(-1,3)
def obj_indices(j,o):
    b=j.b; p=o['f'][39]+8; prim=b[p]; n,ptr=struct.unpack_from('>2I',b,p+4)
    ix=np.frombuffer(b,'>u2',n,ptr+8).astype(np.int64)
    return prim,ix
JBOY.indices=lambda s,o: obj_indices(s,o)
def tex_names(j):
    b=j.b; h=j.h; return [b[h[11]+8+16*i:h[11]+8+16*i+16].split(b'\0')[0].decode() for i in range(h[9])]
def obj_params(j,o):
    b=j.b; f=o['f']; n=f[37]; ptrs=struct.unpack_from('>%dI'%n,b,f[38]+8); TN=tex_names(j); out={}
    for p in ptrs:
        r=b[p+8:p+8+24]; nm=r[:16].split(b'\0')[0].decode(); t,sz=struct.unpack_from('>2H',r,16)
        if t==10: out[nm]=round(struct.unpack_from('>f',r,20)[0],4)
        elif t==15: i,=struct.unpack_from('>I',r,20); out[nm]='tex:'+(TN[i] if i<len(TN) else str(i))
        else: out[nm]=f'type{t}'
    return out
def morphs(j,o):
    """Return (n_morph, vc, 3) positions of the morph targets stored after the base vertices (objects with f[25]>1)."""
    f=o['f']; nm=f[25]-1
    if nm<=0: return None
    vc=f[0]; a=np.frombuffer(j.b,'>f4',vc*7*nm,f[26]+8+vc*28).reshape(nm,vc,7)
    return a[:,:,1:4].astype('f4')

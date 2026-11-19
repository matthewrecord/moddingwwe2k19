"""2K24 material textures -> 2K19 DXT5 set (<mat>, <mat>_mr, <mat>_n) by his rules, and the texture-pack writer."""
import io,struct,numpy as np,etcpak
from PIL import Image
def load(path):
    a=np.asarray(Image.open(path).convert('RGBA'))
    if path.lower().endswith('.dds'):
        b=open(path,'rb').read(84+4)
        if b[84:88]==b'DXT5' and noisy(a):   # 2K26 extraction: BC7 data under a DXT5 header (normal maps) -> decodes as noise
            a=load_bc7(path)
    return a
def is_bc7_in_dxt5(path):
    b=open(path,'rb').read(88)
    return b[84:88]==b'DXT5' and noisy(np.asarray(Image.open(path).convert('RGBA')))
def noisy(a):
    s=a[::4,::4,:3].astype(np.int16); return float(np.abs(np.diff(s,axis=1)).mean())>35
def load_bc7(path):
    import texture2ddecoder
    b=open(path,'rb').read(); h,w=struct.unpack_from('<2I',b,12)
    a=np.frombuffer(texture2ddecoder.decode_bc7(b[128:128+w*h],w,h),'u1').reshape(h,w,4)[...,[2,1,0,3]].copy()
    if a[...,3].max()==0: a[...,3]=255
    return a
def resize(a,w,h):
    """per-channel resize: PIL resizes RGBA premultiplied, which zeroes RGB wherever alpha is 0 (2K24/25 _nrm maps!)"""
    if a.shape[1]==w and a.shape[0]==h: return a
    if a.ndim==2: return np.asarray(Image.fromarray(a).resize((w,h),Image.LANCZOS))
    return np.dstack([np.asarray(Image.fromarray(np.ascontiguousarray(a[...,c])).resize((w,h),Image.LANCZOS)) for c in range(a.shape[2])])
def dds_dxt5(rgba):
    h,w=rgba.shape[:2]; data=etcpak.compress_bc3(np.ascontiguousarray(rgba).tobytes(),w,h)
    hdr=bytearray(128); hdr[0:4]=b'DDS '
    struct.pack_into('<7I',hdr,4,124,0x1007|0x80000,h,w,len(data),0,1)   # size, flags(caps|h|w|pf|linearsize), h, w, linear size, depth, mips
    struct.pack_into('<2I',hdr,76,32,4); hdr[84:88]=b'DXT5'; struct.pack_into('<I',hdr,108,0x1000)
    return bytes(hdr)+data
def target_size(w,h,cap=2048,keep_big=False):
    if keep_big: return w,h
    s=max(1,max(w,h)//cap); return w//s,h//s
def convert(color_path,nrm_path,skin=False,keep_big=False):
    C=load(color_path); N=load(nrm_path); w,h=target_size(C.shape[1],C.shape[0],keep_big=keep_big)
    C=resize(C,w,h); N=resize(N,w,h).astype(np.int32)
    col=C.copy(); col[...,3]=255
    n=np.stack([255-N[...,0],255-N[...,1],np.full(N.shape[:2],255),np.full(N.shape[:2],255)],-1).astype('u1')
    mr=np.stack([np.zeros(N.shape[:2],int) if skin else N[...,3],N[...,2],255-N[...,2],np.full(N.shape[:2],255)],-1).astype('u1')
    return {'':dds_dxt5(col),'_mr':dds_dxt5(mr),'_n':dds_dxt5(n)}
def hair(flow_path,rai_path,tint=(210,173,119),size=None):
    R=load(rai_path); 
    if size: R=resize(R,*size)
    a=R[...,1]; h,w=a.shape
    col=np.zeros((h,w,4),'u1'); col[...,:3]=tint; col[...,3]=a
    n=np.zeros((h,w,4),'u1'); n[...]=(123,0,140,0); n[...,3]=a
    mr=np.zeros((h,w,4),'u1'); mr[...]=(0,174,0,255)
    return {'':dds_dxt5(col),'_n':dds_dxt5(n),'_mr':dds_dxt5(mr)}
def hair_color(color_path,size=None):
    """hair-shader maps from a real colour texture (alpha = cutout), e.g. a mask with wig strands"""
    c=load(color_path)
    if size: c=resize(c,*size)
    w,h=target_size(c.shape[1],c.shape[0]); c=resize(c,w,h).copy(); a=c[...,3]
    n=np.zeros_like(c); n[...]=(123,0,140,0); n[...,3]=a
    mr=np.zeros_like(c); mr[...]=(0,174,0,255)
    return {'':dds_dxt5(c),'_n':dds_dxt5(n),'_mr':dds_dxt5(mr)}
def read_pack(b):
    n,=struct.unpack_from('<I',b,0); E=[]
    for k in range(n):
        r=0x10+32*k; name=b[r:r+16].split(b'\0')[0].decode(); size,off=struct.unpack_from('<2I',b,r+20); E.append((name,b[off:off+size]))
    return b[:0x10],E
def write_pack(entries,head=None):
    """entries: list of (name, dds bytes). Layout: count,0x100,0,0x10 | n x (name[16],'dds\\0',size,off,0) | data."""
    n=len(entries); out=bytearray(struct.pack('<4I',n,0x100,0,0x10) if head is None else head)
    off=0x10+32*n; recs=bytearray(); data=bytearray()
    for nm,d in entries:
        recs+=nm.encode()[:15].ljust(16,b'\0')+b'dds\0'+struct.pack('<3I',len(d),off+len(data),0); data+=d
    return bytes(out+recs+data)

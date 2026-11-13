"""Textured preview of a built pac using its own texture pack (what the game will sample), hide table applied.
Optional morph/bone pose for the head. Usage: preview.py PAC OUTPREFIX"""
import sys,io,zlib,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import jboy,epkwrite,hidetable,texconv,render,pose,jlayout
from PIL import Image
def textures(B):
    hd,E=texconv.read_pack(B[0xa]); out={}
    for n,d in E:
        try: out[n]=np.asarray(Image.open(io.BytesIO(d)).convert('RGBA'))
        except Exception: pass
    return out
def tris(pac,morph=None):
    hdr,bl=epkwrite.raw_blocks(pac); B={f:zlib.decompress(b[16:]) for f,b in bl}; TX=textures(B); out=[]
    w,pairs,tail=hidetable.parse(B[0xce]); h1=set();[h1.update(range(s,e+1)) for s,e in pairs]; hide={1:h1,2:set(range(tail[-2],tail[-1]+1))}
    for fid,d in B.items():
        if d[:4]!=b'JBOY': continue
        j=jboy.JBOY(d)
        for k,o in enumerate(j.objs):
            if o['shader']=='yCS_eyeOv': continue
            img=TX.get(jboy.obj_params(j,o).get('g_mDiffusePrm','tex:?').split(':')[1])
            P=pose.pose(j,k,morph=morph) if (morph and fid==0 and o['f'][25]>1) else o['pos']
            for st,t in hidetable.strip_tri_starts(j.indices(o)[1]):
                if fid==0 and st in hide.get(k,()): continue
                if img is None: c=np.array([1,0,1.]); 
                else:
                    u,v=o['uv'][list(t)].mean(0); hh,ww=img.shape[:2]; px=img[min(hh-1,max(0,int(v*hh))),min(ww-1,max(0,int(u*ww)))]
                    if o['shader']=='yCS_hair' and px[3]<60: continue
                    c=px[:3]/255
                out.append((P[list(t)],c))
    return out
def unweighted(pac):
    """vertices with no skin weight (the game drags them to the origin: spikes)"""
    import jcheck
    hdr,bl=epkwrite.raw_blocks(pac); bad={}
    for f,b in bl:
        d=zlib.decompress(b[16:])
        if d[:4]!=b'JBOY': continue
        j=jboy.JBOY(d)
        for k,o in enumerate(j.objs):
            n=int((jcheck.raw_skin(j,o)['w'].sum(1)<1e-6).sum())
            if n: bad[f'{hex(f)}/{k}']=n
    return bad
def aligned(pac):
    hdr,bl=epkwrite.raw_blocks(pac); bad={}
    for f,b in bl:
        d=zlib.decompress(b[16:])
        if d[:4]==b'JBOY':
            x=[n for n,a,_ in jlayout.regions(jboy.JBOY(d)) if n in('bones','texnames','palhdr','objtable') and (a-8)%16]
            if x: bad[hex(f)]=x
    return bad
if __name__=='__main__':
    pac,pre=sys.argv[1],sys.argv[2]; print('misaligned:',aligned(pac) or 'none'); print('unweighted vertices:',unweighted(pac) or 'none')
    t=tris(pac)
    for v in ('front','back','left'): render.render(t,v,f'{pre}_{v}.png',size=(6,9),title=v)
    hd=[x for x in t if x[0][:,1].min()<-150]
    render.render(hd,'front',f'{pre}_face.png',size=(5,6),xlim=(-14,14),ylim=(158,198),title='face')
    t2=[x for x in tris(pac,morph={114:1.0}) if x[0][:,1].min()<-160]
    render.render(t2,'front',f'{pre}_mouth.png',size=(5,5),xlim=(-8,8),ylim=(164,182),title='mouth open (morph 114)')

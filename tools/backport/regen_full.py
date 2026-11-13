"""Regenerate all non-face objects of a port from the 2K24 files, keeping his face objects. First full-character test."""
import sys,glob,collections,numpy as np;sys.path.insert(0,'/home/claude/scripts')
import jboy,jbuild,regen,epkwrite,zlib
from scipy.spatial import cKDTree
from tmpl import cloud,stock
def mesh_obj(S,T,tri_mask):
    T=T[tri_mask]; used=np.unique(T); remap=-np.ones(len(S['POSITION']),int); remap[used]=np.arange(len(used))
    n=S['NORMAL'][used][:,:3].astype('f4')/127; n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-6)
    return dict(pos=S['POSITION'][used].astype('f4'),nrm=-n,uv=S['TEXCOORD'][used],tris=remap[T])
def template_weights(pos,donor,slot):
    Ps,Ns,Ws=donor; d,si=cKDTree(Ps).query(pos); vc=len(pos)
    sl=np.full((vc,7),0xFFFF); w=np.zeros((vc,7),'f4')
    for v in range(vc):
        acc=collections.defaultdict(float)
        for nm,ww in zip(Ns[si[v]],Ws[si[v]]):
            if ww>0 and nm in slot: acc[nm]+=float(ww)
        it=sorted(acc.items(),key=lambda x:-x[1])[:7]; s=sum(x for _,x in it) or 1
        for q,(nm,ww) in enumerate(sorted(it,key=lambda x:slot[x[0]])): sl[v,q]=slot[nm]; w[v,q]=ww/s
    return sl,w
def put(m,k,G,sl,w,col,tan):
    vc=len(G['pos']); jbuild.set_object(m,k,G['pos'],G['nrm'],np.tile(np.array(col,'u1'),(vc,1)),G['uv'],tan,sl,w,jbuild.tris_to_strip(G['tris']))

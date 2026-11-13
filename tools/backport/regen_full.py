"""Regenerate all non-face objects of a port from the 2K24 files, keeping his face objects. First full-character test."""
import sys,glob,collections,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
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

def body_donor(stock_j):
    """Donor cloud from the stock model's body skin objects only (no head/face objects: those carry morphs or are
    mouth/teeth/tongue/eye parts)."""
    from tmpl import cloud
    keep=[o for o in stock_j.objs if o['shader']=='yCS_skin' and o['f'][25]<=1 and o['vc'] not in (1974,341,352,446,24)]
    class J: pass
    jj=J(); jj.bones=stock_j.bones; jj.objs=keep
    return cloud(jj)
def smooth_outliers(tris,sl,w,palette_names,thresh=0.9):
    """Vertices whose weight distribution is (almost) disjoint from the average of their mesh neighbours get that average."""
    import collections
    vc=len(sl); nb=[set() for _ in range(vc)]
    for a,b,c in tris: nb[a].update((b,c)); nb[b].update((a,c)); nb[c].update((a,b))
    def dist(v): 
        d=collections.defaultdict(float)
        for i,x in zip(sl[v],w[v]):
            if i!=0xFFFF and x>0: d[int(i)]+=float(x)
        return d
    D=[dist(v) for v in range(vc)]; fixed=0; sl2=sl.copy(); w2=w.copy()
    for v in range(vc):
        if not nb[v]: continue
        avg=collections.defaultdict(float)
        for u in nb[v]:
            for i,x in D[u].items(): avg[i]+=x/len(nb[v])
        l1=0.5*sum(abs(D[v].get(i,0)-avg.get(i,0)) for i in set(D[v])|set(avg))
        if l1>thresh:
            it=sorted(avg.items(),key=lambda x:-x[1])[:7]; s=sum(x for _,x in it) or 1
            sl2[v,:]=0xFFFF; w2[v,:]=0
            for q,(i,x) in enumerate(sorted(it)): sl2[v,q]=i; w2[v,q]=x/s
            fixed+=1
    return sl2,w2,fixed

import sys,glob,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)));import jboy,oodl,mdlfmt
from scipy.spatial import cKDTree
def closest_bary(P,V,T):
    """closest point on triangle mesh (V,T) for each P via candidate triangles near nearest vertices. returns tri idx, bary."""
    vt=[[] for _ in range(len(V))]
    for ti,(a,b,c) in enumerate(T): vt[a].append(ti); vt[b].append(ti); vt[c].append(ti)
    _,nv=cKDTree(V).query(P,k=4)
    TI=np.zeros(len(P),int); BC=np.zeros((len(P),3)); D=np.full(len(P),1e9)
    for pi,p in enumerate(P):
        cand=set()
        for v in nv[pi]: cand.update(vt[v])
        for ti in cand:
            a,b,c=V[T[ti]]; bc,d=_cp(p,a,b,c)
            if d<D[pi]: D[pi]=d; TI[pi]=ti; BC[pi]=bc
    return TI,BC,D
def _cp(p,a,b,c):
    ab=b-a; ac=c-a; ap=p-a; d1=ab@ap; d2=ac@ap
    if d1<=0 and d2<=0: return np.array([1,0,0.]),np.linalg.norm(p-a)
    bp=p-b; d3=ab@bp; d4=ac@bp
    if d3>=0 and d4<=d3: return np.array([0,1,0.]),np.linalg.norm(p-b)
    vc=d1*d4-d3*d2
    if vc<=0 and d1>=0 and d3<=0: v=d1/(d1-d3); return np.array([1-v,v,0]),np.linalg.norm(p-(a+v*ab))
    cp=p-c; d5=ab@cp; d6=ac@cp
    if d6>=0 and d5<=d6: return np.array([0,0,1.]),np.linalg.norm(p-c)
    vb=d5*d2-d1*d6
    if vb<=0 and d2>=0 and d6<=0: w=d2/(d2-d6); return np.array([1-w,0,w]),np.linalg.norm(p-(a+w*ac))
    va=d3*d6-d5*d4
    if va<=0 and (d4-d3)>=0 and (d5-d6)>=0: w=(d4-d3)/((d4-d3)+(d5-d6)); return np.array([0,1-w,w]),np.linalg.norm(p-(b+w*(c-b)))
    den=1/(va+vb+vc); v=vb*den; w=vc*den; return np.array([1-v-w,v,w]),np.linalg.norm(p-(a+ab*v+ac*w))
def transfer(P,V,T,D):
    TI,BC,dist=closest_bary(P,V,T); tri=T[TI]
    return np.einsum('pk,mpkc->mpc',BC,D[:,tri,:]),dist
def relerr(pred,truth):
    mag=np.linalg.norm(truth,axis=2); m=mag>0.05; e=np.linalg.norm(pred-truth,axis=2)
    return e[m].mean()/mag[m].mean(), (e[m]<0.05).mean()
def fit_head(V,T,target,iters=12,smooth=0.5,region=None):
    """Non-rigid fit of donor head vertices V (tris T) onto target point cloud: each step pulls every donor vertex to its
    nearest target point, then Laplacian-smooths the displacement. Rigid+scale pre-alignment by matching centroids/extent."""
    import scipy.sparse as sp
    tgt=cKDTree(target)
    W=V.copy()
    # similarity pre-align using the eye/face region bounding boxes
    s=(target.std(0)/W.std(0)).mean(); W=(W-W.mean(0))*s+target.mean(0)
    n=len(V); E=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]); E=np.concatenate([E,E[:,::-1]])
    Adj=sp.coo_matrix((np.ones(len(E)),(E[:,0],E[:,1])),shape=(n,n)).tocsr(); Adj.data[:]=1
    deg=np.asarray(Adj.sum(1)).ravel(); deg[deg==0]=1; L=sp.diags(1/deg)@Adj
    for it in range(iters):
        d,i=tgt.query(W); disp=target[i]-W
        disp[d>3]=0        # ignore donor parts far from the 2K24 head (interior parts)
        for _ in range(3): disp=(1-smooth)*disp+smooth*(L@disp)
        W=W+disp
    return W
def part_landmarks(parts):
    """parts: dict name->(N,3) points. Returns landmark points: centroid + 6 axis extremes per part."""
    L=[]
    for k in sorted(parts):
        P=parts[k]; c=P.mean(0); L.append(c)
        for ax in range(3):
            L.append(P[P[:,ax].argmin()]); L.append(P[P[:,ax].argmax()])
    return np.array(L)
def landmark_warp(V,src_L,dst_L):
    from scipy.interpolate import RBFInterpolator
    f=RBFInterpolator(src_L,dst_L-src_L,kernel='thin_plate_spline',smoothing=1.0)
    return V+f(V)

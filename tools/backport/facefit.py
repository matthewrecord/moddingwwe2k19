"""Fit a stock 2K19 head (with its 119 morphs) onto a 2K24 head using matched boundary loops (neck, mouth, eyes)."""
import numpy as np,collections
from scipy.spatial import cKDTree
from scipy.interpolate import RBFInterpolator
import loops,facexfer as fx
def arclen_resample(Q,n):
    Q=np.vstack([Q,Q[:1]]); d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(Q,axis=0),axis=1))]; t=np.linspace(0,d[-1],n,endpoint=False)
    return np.stack([np.interp(t,d,Q[:,k]) for k in range(3)],1)
def match_loop(A,B):
    """A: stock loop points (ordered), B: target loop points (ordered). Returns target point for every A point (same order)."""
    Bn=arclen_resample(B,len(A)); best=None
    for rev in (False,True):
        Bc=Bn[::-1] if rev else Bn
        for s in range(len(A)):
            e=np.linalg.norm(A-A.mean(0)-(np.roll(Bc,-s,0)-Bc.mean(0)),axis=1).mean()
            if best is None or e<best[0]: best=(e,np.roll(Bc,-s,0))
    return best[1],best[0]
def pair_loops(LA,PA,LB,PB,n=4):
    pairs=[]; used=set()
    for la in LA[:n]:
        ca=PA[la].mean(0); cand=[(np.linalg.norm(PB[lb].mean(0)-ca),i) for i,lb in enumerate(LB[:n]) if i not in used]
        d,i=min(cand); used.add(i); pairs.append((la,LB[i],d))
    return pairs
def fit(PS,TS,PT,TT,iters=3):
    LA=loops.boundary_loops(TS,PS); LB=loops.boundary_loops(TT,PT)
    src=[];dst=[];report=[]
    for la,lb,d in pair_loops(LA,PS,LB,PT):
        tgt,err=match_loop(PS[la],PT[lb]); src.append(PS[la]); dst.append(tgt); report.append((len(la),len(lb),round(float(d),2),round(float(err),2)))
        fixed_idx=la
    src=np.concatenate(src); dst=np.concatenate(dst)
    f=RBFInterpolator(src,dst-src,kernel='thin_plate_spline',smoothing=0.01)
    W=PS+f(PS)
    # pin loop verts exactly (and their welded duplicates)
    pin=np.zeros(len(PS),bool); tp=cKDTree(src); d,i=tp.query(PS); pin=d<1e-4; W[pin]=dst[i[pin]]
    # snap free vertices to the target surface (closest point), then smooth the snap displacement once
    for it in range(iters):
        TI,BC,dist=fx.closest_bary(W[~pin],PT,TT); proj=np.einsum('pk,pkc->pc',BC,PT[TT[TI]])
        W[~pin]=proj
    return W,pin,report

def vnormals(P,T):
    n=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]); N=np.zeros_like(P)
    for k in range(3): np.add.at(N,T[:,k],n)
    return N/np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-12)
def fit_reg(PS,TS,PT,TT,lams=(50,20,8,4,2),iters_per=2,tps_smooth=1.0,free_radius=0.0):
    import scipy.sparse as sp, scipy.sparse.linalg as spl
    LA=loops.boundary_loops(TS,PS); LB=loops.boundary_loops(TT,PT); src=[];dst=[]
    for la,lb,d in pair_loops(LA,PS,LB,PT):
        tgt,err=match_loop(PS[la],PT[lb]); src.append(PS[la]); dst.append(tgt)
    src=np.concatenate(src); dst=np.concatenate(dst)
    W0=PS+RBFInterpolator(src,dst-src,kernel='thin_plate_spline',smoothing=tps_smooth)(PS)
    d,i=cKDTree(src).query(PS); pin=d<1e-4; W0[pin]=dst[i[pin]]
    near_loop=(d>=1e-4)&(d<free_radius)
    n=len(PS); E=np.concatenate([TS[:,[0,1]],TS[:,[1,2]],TS[:,[2,0]]]); E=np.unique(np.sort(E,1),axis=0)
    A=sp.coo_matrix((np.ones(2*len(E)),(np.r_[E[:,0],E[:,1]],np.r_[E[:,1],E[:,0]])),shape=(n,n)).tocsr()
    deg=np.asarray(A.sum(1)).ravel(); L=sp.diags(deg)-A
    NT=vnormals(PT,TT); tT=cKDTree(PT); W=W0.copy()
    for lam in lams:
        for _ in range(iters_per):
            NW=vnormals(W,TS); TI,BC,dist=fx.closest_bary(W,PT,TT); C=np.einsum('pk,pkc->pc',BC,PT[TT[TI]])
            Nc=np.einsum('pk,pkc->pc',BC,NT[TT[TI]]); ok=((NW*Nc).sum(1)>0.5)&(dist<2.0)&(~pin)&(~near_loop)
            w=ok.astype(float)
            M=(sp.diags(w)+lam*(L.T@L)).tolil()
            rhs=w[:,None]*C+lam*(L.T@L)@(W0)   # smoothness of displacement relative to the TPS warp
            # hard pins
            M=M.tocsr(); P_=np.where(pin)[0]
            M=M.tolil()
            for p in P_: M.rows[p]=[p]; M.data[p]=[1.0]
            rhs[pin]=W0[pin]
            M=M.tocsc(); W=np.stack([spl.spsolve(M,rhs[:,k]) for k in range(3)],1)
    return W,pin
def quality(PS,W,T):
    def nrm(P): n=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]); a=np.linalg.norm(n,axis=1); return n/np.maximum(a,1e-12)[:,None],a/2
    n0,a0=nrm(PS); n1,a1=nrm(W); flip=(n0*n1).sum(1)<0; r=a1/np.maximum(a0,1e-9)
    return int(flip.sum()),int((r<0.05).sum())

def untangle(PS,W,T,pin,rounds=200,step=0.5):
    n0=np.cross(PS[T[:,1]]-PS[T[:,0]],PS[T[:,2]]-PS[T[:,0]])
    nb=[set() for _ in range(len(W))]
    for a,b,c in T: nb[a].update((b,c)); nb[b].update((a,c)); nb[c].update((a,b))
    W=W.copy()
    for r in range(rounds):
        n1=np.cross(W[T[:,1]]-W[T[:,0]],W[T[:,2]]-W[T[:,0]]); bad=(n0*n1).sum(1)<0
        if not bad.any(): break
        vs=set(T[bad].ravel())
        # grow by one ring so the repair has room
        vs|=set(u for v in list(vs) for u in nb[v])
        for v in vs:
            if pin[v] or not nb[v]: continue
            W[v]=(1-step)*W[v]+step*W[list(nb[v])].mean(0)
    n1=np.cross(W[T[:,1]]-W[T[:,0]],W[T[:,2]]-W[T[:,0]])
    return W,int(((n0*n1).sum(1)<0).sum()),r

def split_uv_seam(T,uv,extra_arrays,span=0.5):
    """Triangles whose U (or V) span > span straddle a wrap seam: duplicate their low-side vertices with U shifted to the
    high side (clamped to [0,1]), so each triangle samples one side. extra_arrays: list of per-vertex arrays to copy."""
    T=T.copy(); uv=uv.copy(); add_uv=[]; add_src=[]; cache={}
    nv=len(uv)
    for t in range(len(T)):
        for ax in (0,1):
            vals=uv[T[t],ax] if all(v<nv for v in T[t]) else np.array([ (uv[v,ax] if v<nv else add_uv[v-nv][ax]) for v in T[t]])
            if vals.max()-vals.min()<=span: continue
            hi=vals.mean()>0.5
            for q in range(3):
                v=T[t,q]; val=vals[q]
                if (hi and val<0.5) or ((not hi) and val>0.5):
                    key=(int(v),ax,hi)
                    if key not in cache:
                        base=v if v<nv else add_src[v-nv]
                        u2=(uv[base] if v<nv else add_uv[v-nv]).copy(); u2[ax]=np.clip(u2[ax]+(1 if hi else -1),0,1)
                        cache[key]=nv+len(add_uv); add_uv.append(u2); add_src.append(base)
                    T[t,q]=cache[key]
    src=np.array(add_src,int)
    uv2=np.vstack([uv,np.array(add_uv).reshape(-1,2)]) if add_uv else uv
    ex=[np.concatenate([a,a[src]],axis=0) if len(src) else a for a in extra_arrays]
    return T,uv2,ex,len(src)

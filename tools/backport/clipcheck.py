import sys; sys.path.insert(0,'/home/claude/moddingwwe2k19/tools/backport'); import numpy as np, beltshot as bs
from scipy.spatial import cKDTree
def check(pac, ax=1, bend=0.0):
    P,N,UV,T,tex=bs.load(pac); P=P.copy()
    if bend:   # wrap: bend around a vertical cylinder of radius R (cm) like a worn belt
        R=bend; th=P[:,0]/R; r=R+P[:,ax]*(1 if ax==1 else 1)
        P=np.c_[r*np.sin(th), r*np.cos(th)-R, P[:,2]] if ax==1 else P
    plate=UV[:,1]>=0.46; n=N/np.linalg.norm(N,axis=1,keepdims=True)
    front=plate&(n[:,ax]>0.5)          # stored normals point INTO the belt: front faces have +axis normal (see belt_port)
    c=P[T].mean(1); tv=UV[T][:,:,1].mean(1); strap=tv<0.46
    other=[i for i in range(3) if i!=ax]
    kd=cKDTree(P[front][:,other]); d,j=kd.query(c[strap][:,other])
    ins=d<0.4; dy=c[strap][ins,ax]-P[front][j[ins],ax]
    return (dy< -0.02).sum(), ins.sum(), np.percentile(dy,[1,50]) if len(dy) else None
for p in sys.argv[1:]:
    for b in (0,30):
        print(p.split('/')[-2], 'bend R=%s'%b if b else 'rest', check(p,1,b))

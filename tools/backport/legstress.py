"""Hip/leg stress gate: under hip-flex / split / knee poses, (1) attire vertices (on the legs/hips) that cross to the
inside of the body, (2) body+attire edge stretch around hips and legs (p99.9 / max ratio). Usage: legstress.py PAC..."""
import sys,zlib,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import jboy,epkwrite,pose
from scipy.spatial import cKDTree
POSES=[('bend over 90',{'J_Leg_L':([1,0,0],-90),'J_Leg_R':([1,0,0],-90)}),
       ('split 45',{'J_Leg_L':([0,0,1],45),'J_Leg_R':([0,0,1],-45)}),
       ('knee 120',{'J_Leg_L':([1,0,0],-60),'J_Knee_L':([1,0,0],120)}),
       ('kick back',{'J_Leg_R':([1,0,0],40),'J_Knee_R':([1,0,0],90)})]
def objs(B):
    for fid in (0,0x5601,0x5602):
        if fid not in B: continue
        j=jboy.JBOY(B[fid])
        for k,o in enumerate(j.objs):
            if o['shader'] in ('yCS_skin','yCS_gear','yCS_trans') and not (fid==0 and k==0) and o['vc']>10: yield fid,j,k,o
def run(pac):
    B={f:zlib.decompress(b[16:]) for f,b in epkwrite.raw_blocks(pac)[1]}; L=list(objs(B))
    body=[x for x in L if x[0]==0]; att=[x for x in L if x[0]!=0]
    Pb0=np.concatenate([o['pos'] for _,_,_,o in body]).astype(float); out=[]
    Pa0=np.concatenate([o['pos'] for _,_,_,o in att]).astype(float) if att else np.zeros((0,3))
    d0,nn=cKDTree(Pb0).query(Pa0); sel=(d0<3)&(d0>0.02)&(Pa0[:,1]>-115); n0=(Pa0-Pb0[nn])/np.maximum(d0,1e-6)[:,None]
    for name,rots in POSES:
        Pb=np.concatenate([pose.pose_fk(j,k,rots) for _,j,k,_ in body]); Pa=np.concatenate([pose.pose_fk(j,k,rots) for _,j,k,_ in att]) if att else Pa0
        s=((Pa-Pb[nn])*n0).sum(1); cross=int((sel&(s<-0.2)).sum())
        st=[]
        for _,j,k,o in L:
            if o['pos'][:,1].max()<-115: continue
            T=jboy.strip_to_tris(j.indices(o)[1]); E=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]); P0=o['pos'].astype(float); P=pose.pose_fk(j,k,rots)
            low=P0[E[:,0],1]>-115; L0=np.linalg.norm(P0[E[:,0]]-P0[E[:,1]],axis=1); L1=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1); ok=low&(L0>0.05)
            if ok.any(): st.append(L1[ok]/L0[ok])
        r=np.concatenate(st) if st else np.ones(1)
        out.append((name,cross,round(float(np.percentile(r,99.9)),2),round(float(r.max()),1)))
    return out
if __name__=='__main__':
    for p in sys.argv[1:]:
        print(p.split('/')[-1]); [print('  %-14s cross %4d  stretch p99.9 %.2f max %.1f'%r) for r in run(p)]

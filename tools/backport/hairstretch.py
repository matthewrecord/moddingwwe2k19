"""Hair stretch under head turns (99.9th pct / max edge-length ratio). Usage: hairstretch.py PAC..."""
import sys,zlib,numpy as np;sys.path.insert(0,'/home/claude/moddingwwe2k19/tools/backport')
import jboy,epkwrite,pose
def run(pac):
    B={f:zlib.decompress(b[16:]) for f,b in epkwrite.raw_blocks(pac)[1]}; jh=jboy.JBOY(B[0x2715]); o=jh.objs[0]
    T=jboy.strip_to_tris(jh.indices(o)[1]); E=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]); P0=o['pos'].astype(float); L0=np.linalg.norm(P0[E[:,0]]-P0[E[:,1]],axis=1)
    out=[]
    for name,rots in [('head turn 45',{'J_Neck':([0,1,0],20),'J_Head':([0,1,0],25)}),('head tilt 30',{'J_Neck':([0,0,1],15),'J_Head':([0,0,1],15)}),('look down 30',{'J_Neck':([1,0,0],15),'J_Head':([1,0,0],15)})]:
        P=pose.pose_fk(jh,0,rots); L=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1); r=L/np.maximum(L0,1e-4); ok=L0>0.05
        out.append((name,round(float(np.percentile(r[ok],99.9)),2),round(float(r[ok].max()),2)))
    return out
for p in sys.argv[1:]: print(p.split('/')[-1],run(p))

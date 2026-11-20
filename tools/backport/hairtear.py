"""Hair tearing gate: rotate every physics chain root (Hair_bNN) by a random ±25° (as the sim might, chains moving
independently) and report hair edge stretch p99.9 / max (mean of 5 seeds). Usage: hairtear.py PAC..."""
import sys,zlib,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import jboy,epkwrite,pose,re
def run(pac):
    B={f:zlib.decompress(b[16:]) for f,b in epkwrite.raw_blocks(pac)[1]}; j=jboy.JBOY(B[0x2715]); o=j.objs[0]
    T=jboy.strip_to_tris(j.indices(o)[1]); E=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]); P0=o['pos'].astype(float); L0=np.linalg.norm(P0[E[:,0]]-P0[E[:,1]],axis=1); ok=L0>0.05
    roots=[b['name'] for b in j.bones if re.fullmatch(r'Hair_b\d\d',b['name'])]; res=[]
    for seed in range(5):
        rng=np.random.default_rng(seed); rots={n:(rng.normal(size=3),rng.uniform(-25,25)) for n in roots}
        P=pose.pose_fk(j,0,rots); r=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1)[ok]/L0[ok]; res.append((np.percentile(r,99.9),r.max()))
    a=np.array(res).mean(0); return len(roots),round(float(a[0]),2),round(float(a[1]),1)
if __name__=='__main__':
    for p in sys.argv[1:]: print(p.split('/')[-1],'chains %d  stretch p99.9 %.2f  max %.1f'%run(p))

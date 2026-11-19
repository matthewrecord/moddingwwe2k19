"""See notes/builds/backport_test10_psycho_clown.md"""
"""Mask gate: head vertices under the head-locked mask (hair fid 0x2715) that pass through it at full morph weight.
Usage: maskpoke.py PAC  -> per-morph poke counts (vertices whose morph delta along the normal exceeds the head-mask gap)"""
import sys,zlib,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import epkwrite,jboy,build_port as bp
hdr,bl=epkwrite.raw_blocks(sys.argv[1]); B={f:zlib.decompress(b[16:]) for f,b in bl}
j=jboy.JBOY(B[0]); o=j.objs[0]; P=o['pos'].astype(float); T=jboy.strip_to_tris(j.indices(o)[1]); M=np.asarray(jboy.morphs(j,o))
jm=jboy.JBOY(B[0x2715]); om=jm.objs[0]; Q=om['pos'].astype(float); TQ=np.array(jboy.strip_to_tris(jm.indices(om)[1]))
N=-bp.vnormals(P,np.array(T))   # built head winding: flip so normals point out
if (N[:,2]<0).mean()<0.3: N=-N
tri=Q[TQ]; e1=tri[:,1]-tri[:,0]; e2=tri[:,2]-tri[:,0]; gap=np.full(len(P),np.inf)
from scipy.spatial import cKDTree
C=tri.mean(1); kd=cKDTree(C); rad=np.linalg.norm(tri-C[:,None],axis=2).max()
for i,nb in enumerate(kd.query_ball_point(P+N*2,2+rad)):
    if not nb: continue
    nb=np.array(nb); d=N[i]; o_=P[i]-d*0.05
    h=np.cross(d,e2[nb]); a=(e1[nb]*h).sum(1); ok=np.abs(a)>1e-9; f=np.where(ok,1/np.where(ok,a,1),0)
    s=o_-tri[nb,0]; u=f*(s*h).sum(1); q=np.cross(s,e1[nb]); v=f*(q@d); t=f*(e2[nb]*q).sum(1)
    hit=ok&(u>=0)&(v>=0)&(u+v<=1)&(t>0)&(t<4)
    if hit.any(): gap[i]=t[hit].min()-0.05
cov=np.isfinite(gap); print('head verts under mask',cov.sum(),'of',len(P),' gap median %.2f min %.2f'%(np.median(gap[cov]),gap[cov].min()))
worst=[]
for m in range(len(M)):
    push=(M[m]*N).sum(1); p=cov&(push>gap+0.05); worst.append((p.sum(),m+1,push[cov].max()))
worst.sort(reverse=True); print('morphs poking (count, morph, max push cm):',[(a,b,round(c,2)) for a,b,c in worst[:10]])
print('total morphs with any poke',sum(1 for a,_,_ in worst if a))
# jaw: J_Jaw rotations (the mask is head-locked; the chin moves)
import pose
for deg in (-22,-15,8,15,22):
    Pj=pose.pose(j,0,bones={'J_Jaw':((1,0,0),deg)}); push=((Pj-P)*N).sum(1); p=cov&(push>gap+0.05)
    print('jaw %d deg: poke %d (max push %.2f)'%(deg,p.sum(),push[cov].max()))

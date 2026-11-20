"""Hair-on-body clipping gate: for hair verts resting within 4 cm of body/attire (below y=-165), count how many cross to the other side of the body under body poses. Usage: hairclip.py PAC..."""
import sys,zlib,numpy as np;sys.path.insert(0,'/home/claude/moddingwwe2k19/tools/backport')
import jboy,epkwrite,pose
from scipy.spatial import cKDTree
POSES=[('rest',{}),('arms down',{'J_Shoulder_L':([0,0,1],65),'J_Shoulder_R':([0,0,1],-65)}),('arms down+shrug',{'J_Shoulder_L':([0,0,1],65),'J_Shoulder_R':([0,0,1],-65),'J_Clavicle_L':([0,0,1],-15),'J_Clavicle_R':([0,0,1],15)}),('arms fwd',{'J_Shoulder_L':([0,1,0],80),'J_Shoulder_R':([0,1,0],-80)}),('lean',{'J_Spine2':([1,0,0],20),'J_Chest':([1,0,0],15)}),('lean back',{'J_Spine2':([1,0,0],-20),'J_Chest':([1,0,0],-15)}),('twist',{'J_Spine2':([0,1,0],25),'J_Chest':([0,1,0],20)})]
def body(B,rots):
    bod=[]
    for fid in (0,0x5601,0x5602):
        j=jboy.JBOY(B[fid])
        for k,o in enumerate(j.objs):
            if o['shader'] in ('yCS_skin','yCS_gear','yCS_trans') and not (fid==0 and k==0) and o['vc']>10: bod.append(pose.pose_fk(j,k,rots) if rots else o['pos'].astype(float))
    return np.concatenate(bod)
def run(pac):
    B={f:zlib.decompress(b[16:]) for f,b in epkwrite.raw_blocks(pac)[1]}; jh=jboy.JBOY(B[0x2715]); H0=jh.objs[0]['pos'].astype(float)
    B0=body(B,{}); d0,nn=cKDTree(B0).query(H0); sel=(d0<4)&(H0[:,1]>-165)&(d0>0.05); n0=(H0-B0[nn])/d0[:,None]; out=[]
    for name,rots in POSES[1:]:
        B1=body(B,rots); H1=pose.pose_fk(jh,0,rots); s=((H1-B1[nn])*n0).sum(1)
        out.append((name,int((sel&(s<0)).sum()),round(float(np.clip(-s[sel],0,None).max()),1)))
    return int(sel.sum()),out
for p in sys.argv[1:]: print(p.split('/')[-1],run(p))

"""Hair-limit experiments for FMW: rebuild the 0x2715/0x2716 blocks of fmw_v1 with split hair."""
import sys,zlib,pickle,numpy as np;sys.path.insert(0,'/home/claude/scripts')
import jboy,jbuild,epkwrite,oodl,mdlfmt
from regen_full import mesh_obj,body_donor
from build_fmw import put,meshes,PORT,U,WHITE
hdr,bl=epkwrite.raw_blocks(sys.argv[1] if len(sys.argv)>1 else '/home/claude/out/fmw_v1_ch50602.pac'); B={f:zlib.decompress(b[16:]) for f,b in bl}
_,pb=epkwrite.raw_blocks(PORT); O={f:zlib.decompress(b[16:]) for f,b in pb}
G=pickle.load(open('/home/claude/ext/fletcher_full_jboys_v2.pkl','rb'))
MA=meshes(mdlfmt.MDL('/home/claude/ext/fmw/attire.mdl')); S,T=MA['M_Hair']
C=S['POSITION'][T].mean(1); half=C[:,0]>np.median(C[:,0])
HA=mesh_obj(S,T,half); HB=mesh_obj(S,T,~half); print('halves',len(HA['pos']),len(HB['pos']))
s=jboy.JBOY(oodl.blocks(open(U+'ch68702.pac','rb').read())[0][1]); donor=body_donor(s)
def one(fid,Gm):
    jh=jboy.JBOY(O[fid]); m=jbuild.Model(jh); put(m,0,jh,Gm,donor,col=WHITE,hair=True); return m.build()
def two(fid,G1,G2):
    jh=jboy.JBOY(O[fid]); m=jbuild.Model(jh); k=m.clone_object(0); put(m,0,jh,G1,donor,col=WHITE,hair=True); put(m,k,jh,G2,donor,col=WHITE,hair=True); return m.build()
V={'E_hairsplit':{0x2715:two(0x2715,HA,HB)},
   'F_hairhalves_nobeard':{0x2715:one(0x2715,HA),0x2716:one(0x2716,HB)},
   'G_beardonly':{0x2715:G[0x2715]}}
for n,rep in V.items():
    J=dict(B); J.update(rep)
    for f in rep: jj=jboy.JBOY(J[f]); print(n,hex(f),[o['vc'] for o in jj.objs])
    open('/home/claude/out/fmw_v2%s_ch50602.pac'%n,'wb').write(epkwrite.build_raw(hdr,[(f,epkwrite.zblock(J[f])) for f,_ in bl]))

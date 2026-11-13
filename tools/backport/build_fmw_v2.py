"""From-scratch port of Flash Morgan Webster (2K25 .mcd) onto the Fletcher port container (male, Andrade-based palette).
Usage: python3 build_fmw.py OUT.pac [tint_r tint_g tint_b]"""
import sys,glob,pickle,zlib,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from regen_full import mesh_obj,template_weights,body_donor,smooth_outliers
import jboy,jbuild,epkwrite,oodl,mdlfmt,facexfer as fx,facefit,jcheck,hidetable,hpl,texconv
from scipy.spatial import cKDTree
SRC='/home/claude/pairs/FMW/'; EXT='/home/claude/ext/fmw/'
U='/mnt/user-data/uploads/WWE 2K19 - modded/pac/ch/'
PORT='/home/claude/pairs/Kyle Fletcher JKxBNB 2K24 PORT/ch50602.pac'
RED=(245,0,0,255); WHITE=(255,255,255,255)

def mcd_to_mdl(src,dst):
    b=open(src,'rb').read(); assert b[:4]==b'MCD!' and b[12:16]==b'MDL!'; open(dst,'wb').write(b[16:]); return mdlfmt.MDL(dst)
def meshes(M):
    L=M.lods()[0]; return {m['name']:(m['streams'],L[i].reshape(-1,3).astype(int)) for i,m in enumerate(M.meshes)}
def palette_slot(j): bn=[x['name'] for x in j.bones]; return {bn[b]:i for i,b in enumerate(j.palette)}
def degenerate(m,k,j,donor,at=(0,-100,0)):
    p=np.array(at,'f4')+np.array([[0,0,0],[0.001,0,0],[0,0.001,0]],'f4'); sl,w=template_weights(p,donor,palette_slot(j))
    jbuild.set_object(m,k,p,np.tile(np.array([0,0,1],'f4'),(3,1)),np.tile(np.array(RED,'u1'),(3,1)),np.zeros((3,2),'f4'),np.zeros((3,3),'f4'),sl,w,[0,1,2])
def put(m,k,j,G,donor,col=RED,hair=False):
    vc=len(G['pos']); tan=np.zeros((vc,3),'f4')
    if hair:
        tan[0::2]=(0,1,0); tan[1::2]=(1,0,1); sl=np.zeros((vc,4),int); w=np.ones((vc,4),'f4')
    else:
        sl,w=template_weights(G['pos'],donor,palette_slot(j)); sl,w,_=smooth_outliers(G['tris'],sl,w,None)
    jbuild.set_object(m,k,G['pos'],G['nrm'].astype('f4'),np.tile(np.array(col,'u1'),(vc,1)),G['uv'].astype('f4'),tan,sl,w,jbuild.tris_to_strip(G['tris']))

def build(outpath,tint=(45,35,30)):
    BM=mcd_to_mdl(SRC+'BaseModel/baseModel.mcd',EXT+'base.mdl'); AM=mcd_to_mdl(SRC+'159_Default_Attire/159_Attire.mcd',EXT+'attire.mdl')
    MB=meshes(BM); MA=meshes(AM)
    s=jboy.JBOY(oodl.blocks(open(U+'ch68702.pac','rb').read())[0][1]); donor=body_donor(s)
    hdr,blocks=epkwrite.raw_blocks(PORT); B={f:zlib.decompress(b[16:]) for f,b in blocks}; J={}
    # ---------- main JBOY ----------
    j=jboy.JBOY(B[0]); m=jbuild.Model(j); slot=palette_slot(j)
    # head: Andrade topology + morphs fitted to Flash's M_Head
    so=s.objs[0]; SD=jboy.morphs(s,so); ST=jboy.strip_to_tris(s.indices(so)[1])
    St,TT=MB['M_Head']; PT=St['POSITION']
    W=np.load(EXT+'fit_W.npy') if len(glob.glob(EXT+'fit_W.npy')) else facefit.fit_welded(so['pos'].astype(float),ST,PT.astype(float),TT,init='similarity',free_radius=0.6)[0]
    TI,BC,_=fx.closest_bary(W,PT,TT); tri=TT[TI]; uv=np.einsum('pk,pkc->pc',BC,St['TEXCOORD'][tri]).astype('f4')
    N=St['NORMAL'][:,:3].astype('f4')/127; N/=np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-6); nrm=-np.einsum('pk,pkc->pc',BC,N[tri]); nrm/=np.linalg.norm(nrm,axis=1,keepdims=True)
    bns=[x['name'] for x in s.bones]; sk=jcheck.raw_skin(s,so); raw=s.fix_order(sk['i'].astype(int),sk['w']); vc=len(W)
    sl=np.full((vc,7),0xFFFF); w=np.zeros((vc,7),'f4')
    for v in range(vc):
        q=0
        for i,ww in zip(raw[v],sk['w'][v]):
            if ww<=0 or i>=len(s.palette): continue
            nm=bns[s.palette[i]]
            if nm in slot: sl[v,q]=slot[nm]; w[v,q]=ww; q+=1
        w[v]/=max(w[v].sum(),1e-6)
    T2,uv2,(P2,N2,SI,SW,MD2),nadd=facefit.split_uv_seam(ST,uv,[W,nrm,sl,w,np.transpose(SD,(1,0,2))]); vc=len(P2)
    jbuild.set_object(m,0,P2,N2,np.tile(np.array(RED,'u1'),(vc,1)),uv2.astype('f4'),np.zeros((vc,3),'f4'),SI,SW,jbuild.tris_to_strip(T2))
    for n in range(1,120):
        V=np.zeros(vc,dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]); V['p']=MD2[:,n-1,:]; m.data[m.chunk(0,f'vset{n}')]=bytearray(V.tobytes())
    # body split upper/lower
    S,T=MB['M_Body']; C=S['POSITION'][T].mean(1); up=(C[:,1]<-108)|(np.abs(C[:,0])>26)
    Gu=mesh_obj(S,T,up); Gl=mesh_obj(S,T,~up); put(m,1,j,Gu,donor); put(m,2,j,Gl,donor)
    # eyes / eye overlay / mouth parts: his Fletcher objects, translated by the local face change Fletcher -> Flash
    WF=np.load('/home/claude/ext/fit_weld2.npy'); tF=cKDTree(WF); D=W-WF; shifts={}
    for k in range(3,9):
        o=j.objs[k]; _,nn=tF.query(o['pos'],k=20); d=D[nn].reshape(-1,3).mean(0); shifts[k]=d.round(2).tolist()
        for n in range(o['f'][25]):  # base set + morph sets: morph sets hold offsets? only base gets shifted when sets are offsets
            if n>0: break
            ch=m.chunk(k,f'vset{n}'); V=np.frombuffer(bytes(m.data[ch][:o['vc']*28]),dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]).copy()
            V['p']+=d; m.data[ch][:len(V.tobytes())]=V.tobytes()
    J[0]=m.build()
    # ---------- hair (0x2715) + beard/"combinations" (0x2716) ----------
    for fid,name in ((0x2715,'M_Hair'),(0x2716,'M_Combinations')):
        jh=jboy.JBOY(B[fid]); mh=jbuild.Model(jh); S,T=MA[name]; put(mh,0,jh,mesh_obj(S,T,np.ones(len(T),bool)),donor,col=WHITE,hair=True); J[fid]=mh.build()
    # ---------- attire 0x5601: 0 necklace(off) 1 l_wrist 2 r_wrist 3 bottoms 4 shoes ; 0x5602 all off ----------
    ja=jboy.JBOY(B[0x5601]); ma=jbuild.Model(ja)
    S,T=MA['M_Wrist']; cx=S['POSITION'][T].mean(1)[:,0]
    degenerate(ma,0,ja,donor); put(ma,1,ja,mesh_obj(S,T,cx>0),donor); put(ma,2,ja,mesh_obj(S,T,cx<=0),donor)
    S,T=MA['M_Bottoms']; put(ma,3,ja,mesh_obj(S,T,np.ones(len(T),bool)),donor)
    S,T=MA['M_Shoes']; put(ma,4,ja,mesh_obj(S,T,np.ones(len(T),bool)),donor); J[0x5601]=ma.build()
    jb=jboy.JBOY(B[0x5602]); mb=jbuild.Model(jb)
    for k in range(len(jb.objs)): degenerate(mb,k,jb,donor)
    J[0x5602]=mb.build()
    # ---------- hide table from .hpl (any vertex hidden) + skin within 1 cm of attire ----------
    H=hpl.parse(SRC+'159_Default_Attire/159_Attire.hpl')['M_Body'][0]; th=cKDTree(MB['M_Body'][0]['POSITION'][H])
    ta=cKDTree(np.concatenate([MA[n][0]['POSITION'] for n in ('M_Bottoms','M_Shoes','M_Wrist')]))
    our=jboy.JBOY(J[0]); res={}
    for oi in (1,2):
        o=our.objs[oi]; st=hidetable.strip_tri_starts(our.indices(o)[1]); h=th.query(o['pos'])[0]<0.05; a=ta.query(o['pos'])[0]<1.0
        res[oi]=([s_ for s_,t in st if h[list(t)].any() or a[list(t)].all()],len(st),len(our.indices(o)[1]))
    lo_frac=len(res[2][0])/res[2][1]
    hide=hidetable.rebuild(B[0xce],hidetable.to_ranges(res[1][0]),(0,res[2][2]-3) if lo_frac>0.9 else (0,0))
    J[0xce]=hide
    # ---------- textures ----------
    hd,E=texconv.read_pack(B[0xa]); E=dict(E); T_=SRC+'BaseModel/Textures/'; A_=SRC+'159_Default_Attire/Textures/'
    def setm(base,c,n,skin=False,nname=None):
        r=texconv.convert(c,n,skin=skin); E[base]=r['']; E[base+'_mr']=r['_mr']; E[nname or base+'_n']=r['_n']
    setm('all_color',T_+'body_color.dds',T_+'body_nrm.dds',skin=True,nname='all_n')
    setm('head',T_+'head_color.dds',T_+'head_nrm.dds',skin=True)
    setm('eye',T_+'eye_color.dds',T_+'eye_nrm.dds')
    setm('bottoms',A_+'bottoms_color.dds',A_+'bottoms_nrm.dds'); setm('shoes',A_+'shoes_color.dds',A_+'shoes_nrm.dds')
    setm('l_wrist',A_+'wrist_color.dds',A_+'wrist_nrm.dds'); setm('r_wrist',A_+'wrist_color.dds',A_+'wrist_nrm.dds')
    for base,rai in (('hair',A_+'hair_rai.dds'),('hair2',A_+'combinations_rai.dds')):
        r=texconv.hair(None,rai,tint); E[base]=r['']; E[base+'_n']=r['_n']; E[base+'_mr']=r['_mr']
    J[0xa]=texconv.write_pack(list(E.items()),hd)
    pac=epkwrite.build_raw(hdr,[(fid,epkwrite.zblock(J[fid]) if fid in J else blk) for fid,blk in blocks]); open(outpath,'wb').write(pac)
    return dict(size=len(pac),seam_dups=nadd,shifts=shifts,hide_upper=len(res[1][0]),lower_frac=round(lo_frac,3),objs={f:len(jboy.JBOY(J[f]).objs) for f in (0,0x2715,0x2716,0x5601,0x5602)})
if __name__=='__main__':
    t=tuple(int(x) for x in sys.argv[2:5]) if len(sys.argv)>4 else (45,35,30)
    print(build(sys.argv[1],t))

"""From-scratch port of Flash Morgan Webster (2K25 .mcd) onto the Fletcher port container (male, Andrade-based palette).
Usage: python3 build_fmw.py OUT.pac [tint_r tint_g tint_b]"""
import sys,glob,pickle,zlib,numpy as np;sys.path.insert(0,'/home/claude/scripts')
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
def welded_weights(P,T,donor,slot):
    key=np.round(P,3); _,g,inv=np.unique(key,axis=0,return_index=True,return_inverse=True); inv=inv.ravel()
    sl,w=template_weights(P[g],donor,slot); sl,w,_=smooth_outliers(inv[T],sl,w,None); return sl[inv],w[inv]
def hist_match(src,ref):
    s=np.sort(src.ravel()); r=np.sort(ref.ravel()); q=np.searchsorted(s,src.ravel(),side='left')/len(s)
    return np.interp(q,np.linspace(0,1,len(r)),r).reshape(src.shape).round().clip(0,255).astype('u1')
KYLE='/home/claude/pairs/Kyle Fletcher by JakeyAttires & BANbantam - WWE2K24 ORIGINAL/1070_Kyle_Fletcher/BaseModel/Textures/'
def fixed_nrm(flash_path,kyle_path,out):
    from PIL import Image
    a=texconv.load(flash_path).copy(); k=texconv.load(kyle_path); a[...,2]=hist_match(a[...,2],k[...,2]); a[...,3]=255
    Image.fromarray(a).save(out); return out
def xfer(Pt,Ps,Ts,sl,w,MD=None):
    """closest-point transfer of skin (slot,weight) and morph offsets MD(nsets,vc,3) from mesh (Ps,Ts) to points Pt"""
    TI,BC,dist=fx.closest_bary(Pt,Ps,Ts); tri=Ts[TI]; vc=len(Pt); SL=np.full((vc,7),0xFFFF); W=np.zeros((vc,7),'f4')
    for v in range(vc):
        acc={}
        for c in range(3):
            for q in range(7):
                if w[tri[v,c],q]>0: acc[sl[tri[v,c],q]]=acc.get(sl[tri[v,c],q],0)+BC[v,c]*w[tri[v,c],q]
        it=sorted(sorted(acc.items(),key=lambda x:-x[1])[:7]); t=sum(x for _,x in it) or 1
        for q,(a,b) in enumerate(it): SL[v,q]=a; W[v,q]=b/t
    M=None if MD is None else np.einsum('vc,ncvd->nvd' if False else 'vc,nvcd->nvd',BC,MD[:,tri,:])
    return SL,W,M,dist
def put(m,k,j,G,donor,col=RED,hair=False,weights=None):
    vc=len(G['pos']); tan=np.zeros((vc,3),'f4')
    if hair:
        tan[0::2]=(0,1,0); tan[1::2]=(1,0,1); sl=np.zeros((vc,4),int); w=np.ones((vc,4),'f4')
    else:
        sl,w=weights if weights is not None else welded_weights(G['pos'],G['tris'],donor,palette_slot(j))
    jbuild.set_object(m,k,G['pos'],G['nrm'].astype('f4'),np.tile(np.array(col,'u1'),(vc,1)),G['uv'].astype('f4'),tan,sl,w,jbuild.tris_to_strip(G['tris']))

def build(outpath,tint=(45,35,30)):
    BM=mcd_to_mdl(SRC+'BaseModel/baseModel.mcd',EXT+'base.mdl'); AM=mcd_to_mdl(SRC+'159_Default_Attire/159_Attire.mcd',EXT+'attire.mdl')
    MB=meshes(BM); MA=meshes(AM)
    s=jboy.JBOY(oodl.blocks(open(U+'ch68702.pac','rb').read())[0][1]); donor=body_donor(s)
    hdr,blocks=epkwrite.raw_blocks(PORT); B={f:zlib.decompress(b[16:]) for f,b in blocks}; J={}
    # ---------- main JBOY ----------
    j=jboy.JBOY(B[0]); m=jbuild.Model(j); slot=palette_slot(j)
    # head: Flash's own M_Head; Andrade morphs + skin carried over via the fitted Andrade surface W
    so=s.objs[0]; SD=jboy.morphs(s,so); ST=jboy.strip_to_tris(s.indices(so)[1])
    St,TT=MB['M_Head']; PT=St['POSITION']
    W=np.load(EXT+'fit_W.npy') if len(glob.glob(EXT+'fit_W.npy')) else facefit.fit_welded(so['pos'].astype(float),ST,PT.astype(float),TT,init='similarity',free_radius=0.6)[0]
    bns=[x['name'] for x in s.bones]; sk=jcheck.raw_skin(s,so); raw=s.fix_order(sk['i'].astype(int),sk['w']); va=len(W)
    asl=np.full((va,7),0xFFFF); aw=np.zeros((va,7),'f4')
    for v in range(va):
        q=0
        for i,ww in zip(raw[v],sk['w'][v]):
            if ww<=0 or i>=len(s.palette): continue
            nm=bns[s.palette[i]]
            if nm in slot: asl[v,q]=slot[nm]; aw[v,q]=ww; q+=1
        aw[v]/=max(aw[v].sum(),1e-6)
    MDa=np.asarray(SD)  # (119, va, 3)
    HS,HW,HM,hd=xfer(PT.astype(float),W,ST,asl,aw,MDa)
    # neck seam: head vertices that coincide with body vertices take the body's weights
    Sb,Tb=MB['M_Body']; bsl,bw=welded_weights(Sb['POSITION'],Tb,donor,slot)
    tb=cKDTree(Sb['POSITION']); dd,ii=tb.query(PT); seam=dd<1e-3; HS[seam]=bsl[ii[seam]]; HW[seam]=bw[ii[seam]]
    G=mesh_obj(St,TT,np.ones(len(TT),bool)); assert len(G['pos'])==len(PT)
    vc=len(PT); jbuild.set_object(m,0,G['pos'],G['nrm'].astype('f4'),np.tile(np.array(RED,'u1'),(vc,1)),G['uv'].astype('f4'),np.zeros((vc,3),'f4'),HS,HW,jbuild.tris_to_strip(G['tris']))
    for n in range(1,120):
        V=np.zeros(vc,dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]); V['p']=HM[n-1]; m.data[m.chunk(0,f'vset{n}')]=bytearray(V.tobytes())
    nadd=int(seam.sum())
    # body split upper/lower
    S,T=MB['M_Body']; C=S['POSITION'][T].mean(1); up=(C[:,1]<-108)|(np.abs(C[:,0])>26)
    for k_,msk in ((1,up),(2,~up)):
        used=np.unique(T[msk]); put(m,k_,j,mesh_obj(S,T,msk),donor,weights=(bsl[used],bw[used]))
    # eyes: Flash's own M_EYE split by side, rigid on J_Eye_L (x>0) / J_Eye_R
    S,T=MB['M_EYE']; cx=S['POSITION'][T].mean(1)[:,0]
    for k_,msk,bone in ((3,cx>0,'J_Eye_L'),(4,cx<=0,'J_Eye_R')):
        Ge=mesh_obj(S,T,msk); n_=len(Ge['pos']); esl=np.full((n_,7),0xFFFF); esl[:,0]=slot[bone]; ew=np.zeros((n_,7),'f4'); ew[:,0]=1
        put(m,k_,j,Ge,donor,weights=(esl,ew))
    # eye overlay + mouth parts (his objects): shift by Flash-minus-Kyle centroid of the matching 2K24/2K25 part
    KM=meshes(mdlfmt.MDL(glob.glob('/home/claude/pairs/Kyle*ORIG*/**/baseModel.mdl',recursive=True)[0]))
    ctr=lambda D,n:D[n][0]['POSITION'].mean(0)
    sides=lambda D:[D['M_EYE'][0]['POSITION'][D['M_EYE'][0]['POSITION'][:,0]*sg>0].mean(0) for sg in (1,-1)]
    dEye=(np.array(sides(MB))-np.array(sides(KM))).mean(0); dTeeth=ctr(MB,'M_Teeth')-ctr(KM,'M_Teeth'); dTong=ctr(MB,'M_Tongue')-ctr(KM,'M_Tongue'); dBag=ctr(MB,'M_MouthBag')-ctr(KM,'M_MouthBag')
    shifts={5:dEye,6:(dTeeth+dBag)/2,7:dTeeth,8:dTong}
    for k_,d in shifts.items():
        o=j.objs[k_]; ch=m.chunk(k_,'vset0'); V=np.frombuffer(bytes(m.data[ch][:o['vc']*28]),dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]).copy()
        V['p']+=d; m.data[ch][:len(V.tobytes())]=V.tobytes()
    shifts={k_:np.round(d,2).tolist() for k_,d in shifts.items()}
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
    setm('all_color',T_+'body_color.dds',fixed_nrm(T_+'body_nrm.dds',KYLE+'body_nrm.DDS','/home/claude/ext/fmw/body_nrm_fix.png'),skin=True,nname='all_n')
    setm('head',T_+'head_color.dds',fixed_nrm(T_+'head_nrm.dds',KYLE+'head_nrm.DDS','/home/claude/ext/fmw/head_nrm_fix.png'),skin=True)
    setm('eye',T_+'eye_color.dds',T_+'eye_nrm.dds')
    setm('bottoms',A_+'bottoms_color.dds',A_+'bottoms_nrm.dds'); setm('shoes',A_+'shoes_color.dds',A_+'shoes_nrm.dds')
    setm('l_wrist',A_+'wrist_color.dds',A_+'wrist_nrm.dds'); setm('r_wrist',A_+'wrist_color.dds',A_+'wrist_nrm.dds')
    for base,rai in (('hair',A_+'hair_rai.dds'),('hair2',A_+'combinations_rai.dds')):
        r=texconv.hair(None,rai,tint); E[base]=r['']; E[base+'_n']=r['_n']; E[base+'_mr']=r['_mr']
    J[0xa]=texconv.write_pack(list(E.items()),hd)
    pac=epkwrite.build_raw(hdr,[(fid,epkwrite.zblock(J[fid]) if fid in J else blk) for fid,blk in blocks]); open(outpath,'wb').write(pac)
    return dict(size=len(pac),neck_seam_verts=nadd,shifts=shifts,hide_upper=len(res[1][0]),lower_frac=round(lo_frac,3),objs={f:len(jboy.JBOY(J[f]).objs) for f in (0,0x2715,0x2716,0x5601,0x5602)})
if __name__=='__main__':
    t=tuple(int(x) for x in sys.argv[2:5]) if len(sys.argv)>4 else (45,35,30)
    print(build(sys.argv[1],t))

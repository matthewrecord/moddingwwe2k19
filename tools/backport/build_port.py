"""General backport builder (2K24 .mdl / 2K25 .mcd -> 2K19 pac on the Fletcher-port container, Andrade donor).
A character is described by a config dict (see configs at the bottom). Everything Flash v4 validated is kept:
own head mesh + Andrade morphs/skin via the fitted surface (lip split), own eyes, his mouth parts shifted by
part centroids, welded body weights, 2K24/25 nrm blue matched to Kyle, hide table from .hpl.
New: texture atlases (several source meshes in one 2K19 slot), hidden-first triangle order for body objects."""
import sys,os,glob,zlib,numpy as np;sys.path.insert(0,'/home/claude/scripts')
from build_fmw import (mesh_obj,template_weights,body_donor,welded_weights,hist_match,KYLE,xfer,lip_class,put,degenerate,
                       meshes,palette_slot,PORT,U,RED,WHITE)
import jboy,jbuild,epkwrite,oodl,mdlfmt,facexfer as fx,facefit,jcheck,hidetable,hpl,texconv
from scipy.spatial import cKDTree
from PIL import Image

def ci(path):
    """case-insensitive file lookup (sources mix .dds/.DDS)"""
    d,f=os.path.split(path)
    for x in os.listdir(d):
        if x.lower()==f.lower(): return os.path.join(d,x)
    return None
def open_model(path,cache):
    if path.endswith('.mcd'):
        b=open(path,'rb').read(); assert b[:4]==b'MCD!' and b[12:16]==b'MDL!'; open(cache,'wb').write(b[16:]); path=cache
    return mdlfmt.MDL(path)
def mats(C,N,skin=False,kyle_nrm=None):
    """color/nrm arrays -> 2K19 (<mat>, _mr, _n) DXT5 by the 2K24 rules; optional blue-channel match to Kyle"""
    N=N.copy()
    if kyle_nrm is not None: N[...,2]=hist_match(N[...,2],texconv.load(kyle_nrm)[...,2])
    N=N.astype(np.int32); col=C.copy(); col[...,3]=255
    n=np.stack([255-N[...,0],255-N[...,1],np.full(N.shape[:2],255),np.full(N.shape[:2],255)],-1).astype('u1')
    mr=np.stack([np.zeros(N.shape[:2],int) if skin else N[...,3],N[...,2],255-N[...,2],np.full(N.shape[:2],255)],-1).astype('u1')
    return {'':texconv.dds_dxt5(col),'_mr':texconv.dds_dxt5(mr),'_n':texconv.dds_dxt5(n)}
def load_pair(tdir,stem,cap=2048):
    c=texconv.load(ci(f'{tdir}/{stem}_color.dds')); np_=ci(f'{tdir}/{stem}_nrm.dds')
    n=texconv.load(np_) if np_ else np.dstack([np.full(c.shape[:2],128,'u1')]*2+[np.full(c.shape[:2],128,'u1'),np.zeros(c.shape[:2],'u1')])
    w,h=texconv.target_size(c.shape[1],c.shape[0],cap); return texconv.resize(c,w,h),texconv.resize(n,w,h)
def atlas(tdir,stems,size=2048):
    """2x2 atlas (tile i at col i%2,row i//2); returns color, nrm arrays and per-stem (col,row)"""
    t=size//2; C=np.zeros((size,size,4),'u1'); N=np.zeros((size,size,4),'u1'); N[...,:3]=128; pos={}
    for i,st in enumerate(stems):
        c,n=load_pair(tdir,st); cx,ry=i%2,i//2
        C[ry*t:(ry+1)*t,cx*t:(cx+1)*t]=texconv.resize(c,t,t); N[ry*t:(ry+1)*t,cx*t:(cx+1)*t]=texconv.resize(n,t,t); pos[st]=(cx,ry)
    return C,N,pos
def concat(objs):
    P=[];N=[];UV=[];T=[];o=0
    for G in objs: P.append(G['pos']);N.append(G['nrm']);UV.append(G['uv']);T.append(G['tris']+o);o+=len(G['pos'])
    return dict(pos=np.concatenate(P),nrm=np.concatenate(N),uv=np.concatenate(UV),tris=np.concatenate(T))
def whole(D,name): S,T=D[name]; return mesh_obj(S,T,np.ones(len(T),bool))

def build(cfg,outpath,PROP=None):
    W_=cfg['work']; os.makedirs(W_,exist_ok=True)
    BM=open_model(cfg['base'],W_+'/base.mdl'); AM=open_model(cfg['attire_model'],W_+'/attire.mdl'); MB=meshes(BM); MA=meshes(AM)
    TB,TA=cfg['tex_base'],cfg['tex_attire']
    s=jboy.JBOY(oodl.blocks(open(U+'ch68702.pac','rb').read())[0][1]); donor=body_donor(s)
    hdr,blocks=epkwrite.raw_blocks(PORT); B={f:zlib.decompress(b[16:]) for f,b in blocks}; J={}; info={}
    j=jboy.JBOY(B[0]); m=jbuild.Model(j); slot=palette_slot(j)
    # ---------------- head ----------------
    so=s.objs[0]; MDa=np.asarray(jboy.morphs(s,so)); ST=jboy.strip_to_tris(s.indices(so)[1])
    St,TT=MB['M_Head']; PT=St['POSITION'].astype(float)
    fc=W_+'/fit_W.npy'
    if os.path.exists(fc): W=np.load(fc)
    else: W=facefit.fit_welded(so['pos'].astype(float),ST,PT,TT,init='similarity',free_radius=0.6)[0]; np.save(fc,W)
    info['fit_mean_cm']=round(float(fx.closest_bary(W,PT,TT)[2].mean()),3)
    bns=[x['name'] for x in s.bones]; sk=jcheck.raw_skin(s,so); raw=s.fix_order(sk['i'].astype(int),sk['w']); va=len(W)
    asl=np.full((va,7),0xFFFF); aw=np.zeros((va,7),'f4')
    for v in range(va):
        q=0
        for i,ww in zip(raw[v],sk['w'][v]):
            if ww>0 and i<len(s.palette) and bns[s.palette[i]] in slot: asl[v,q]=slot[bns[s.palette[i]]]; aw[v,q]=ww; q+=1
        aw[v]/=max(aw[v].sum(),1e-6)
    HS,HW,HM,_=xfer(PT,W,ST,asl,aw,MDa)
    cF=lip_class(PT,TT); cA0=lip_class(np.asarray(W,float),ST); dy=MDa[113][:,1]; near=cA0!=0
    cA=np.zeros(va,int); cA[near&(dy>0.5*dy[near].max())]=-1; cA[near&(dy<=0.5*dy[near].max())]=1; tc=cA[ST]
    for side in (1,-1):
        vs=np.where(cF==side)[0]; ts=ST[(tc==side).all(1)]
        if len(vs) and len(ts): a,b_,c_,_=xfer(PT[vs],W,ts,asl,aw,MDa); HS[vs]=a; HW[vs]=b_; HM[:,vs]=c_
    info['lip']=(int((cF==1).sum()),int((cF==-1).sum()))
    Sb,Tb=MB['M_Body']; bsl,bw=welded_weights(Sb['POSITION'],Tb,donor,slot)
    dd,ii=cKDTree(Sb['POSITION']).query(PT); seam=dd<1e-3; HS[seam]=bsl[ii[seam]]; HW[seam]=bw[ii[seam]]; info['neck_seam']=int(seam.sum())
    G=mesh_obj(St,TT,np.ones(len(TT),bool)); vc=len(PT)
    jbuild.set_object(m,0,G['pos'],G['nrm'].astype('f4'),np.tile(np.array(RED,'u1'),(vc,1)),G['uv'].astype('f4'),np.zeros((vc,3),'f4'),HS,HW,jbuild.tris_to_strip(G['tris']))
    for n in range(1,120):
        V=np.zeros(vc,dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]); V['p']=HM[n-1]; m.data[m.chunk(0,f'vset{n}')]=bytearray(V.tobytes())
    # ---------------- body: hidden-first triangle order so each hide range is one block ----------------
    H=hpl.parse(cfg['hpl'])['M_Body'][0]; hid_v=np.zeros(len(Sb['POSITION']),bool); hid_v[H]=True
    att=np.concatenate([MA[n][0]['POSITION'] for n in cfg['cover']]); near_att=cKDTree(att).query(Sb['POSITION'])[0]<1.0
    hid_t=hid_v[Tb].any(1)|near_att[Tb].all(1)
    C=Sb['POSITION'][Tb].mean(1); up=(C[:,1]<-108)|(np.abs(C[:,0])>26); hide_n={}
    for k_,msk in ((1,up),(2,~up)):
        order=np.concatenate([np.where(msk&hid_t)[0],np.where(msk&~hid_t)[0]]); hide_n[k_]=int((msk&hid_t).sum())
        Tm=Tb[order]; used=np.unique(Tm); G=mesh_obj(Sb,Tm,np.ones(len(Tm),bool))
        put(m,k_,j,G,donor,weights=(bsl[used],bw[used]))
    # ---------------- eyes (own), eye overlay + mouth parts (his, shifted) ----------------
    S,T=MB['M_EYE']; cx=S['POSITION'][T].mean(1)[:,0]
    sides=lambda D:[D['M_EYE'][0]['POSITION'][D['M_EYE'][0]['POSITION'][:,0]*sg>0].mean(0) for sg in (1,-1)]
    hisE=[j.objs[3]['pos'].mean(0),j.objs[4]['pos'].mean(0)]
    for k_,msk,bone in ((3,cx>0,'J_Eye_L'),(4,cx<=0,'J_Eye_R')):
        Ge=mesh_obj(S,T,msk); n_=len(Ge['pos']); esl=np.full((n_,7),0xFFFF); esl[:,0]=slot[bone]; ew=np.zeros((n_,7),'f4'); ew[:,0]=1
        put(m,k_,j,Ge,donor,weights=(esl,ew))
    KM=meshes(mdlfmt.MDL(glob.glob('/home/claude/pairs/Kyle*ORIG*/**/baseModel.mdl',recursive=True)[0]))
    ctr=lambda D,n:D[n][0]['POSITION'].mean(0)
    dT=ctr(MB,'M_Teeth')-ctr(KM,'M_Teeth'); dB=ctr(MB,'M_MouthBag')-ctr(KM,'M_MouthBag'); dG=ctr(MB,'M_Tongue')-ctr(KM,'M_Tongue')
    def shift(k_,fn):
        o=j.objs[k_]; ch=m.chunk(k_,'vset0'); V=np.frombuffer(bytes(m.data[ch][:o['vc']*28]),dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]).copy()
        V['p']=fn(V['p']); m.data[ch][:len(V.tobytes())]=V.tobytes()
    fE=sides(MB)
    def ov(p):
        p=p.copy(); L=p[:,0]>0; p[L]+=fE[0]-hisE[0]; p[~L]+=fE[1]-hisE[1]; return p
    shift(5,ov); shift(6,lambda p:p+(dT+dB)/2); shift(7,lambda p:p+dT); shift(8,lambda p:p+dG)
    info['mouth_shift']=np.round(dT,2).tolist()
    J[0]=m.build()
    # ---------------- hair slots ----------------
    for fid in (0x2715,0x2716):
        jh=jboy.JBOY(B[fid]); mh=jbuild.Model(jh); spec=cfg['hair'].get(fid)
        if spec: put(mh,0,jh,whole(MA,spec[0]),donor,col=WHITE,hair=True)
        else:
            p=np.array([[0,-185,0],[0.001,-185,0],[0,-185.001,0]],'f4'); put(mh,0,jh,dict(pos=p,nrm=np.tile(np.array([0,0,1],'f4'),(3,1)),uv=np.zeros((3,2),'f4'),tris=np.array([[0,1,2]])),donor,col=WHITE,hair=True)
        J[fid]=mh.build()
    # ---------------- attire slots (single mesh, split by side, or 2x2 atlas) ----------------
    tex={}
    for fid in (0x5601,0x5602):
        ja=jboy.JBOY(B[fid]); ma=jbuild.Model(ja)
        for k_ in range(len(ja.objs)):
            spec=cfg['attire'].get((fid,k_)); texname=jboy.obj_params(ja,ja.objs[k_])['g_mDiffusePrm'].split(':')[1]
            if spec is None: degenerate(ma,k_,ja,donor); continue
            kind=spec[0]
            if kind=='mesh':
                _,name,stem=spec[:3]; S,T=MA[name]; msk=np.ones(len(T),bool)
                if len(spec)>3: cxs=S['POSITION'][T].mean(1)[:,0]; msk=cxs>0 if spec[3]=='L' else cxs<=0
                put(ma,k_,ja,mesh_obj(S,T,msk),donor); tex[texname]=load_pair(TA,stem)
            else:   # ('atlas', [(mesh, stem), ...])
                Cc,Nn,pos=atlas(TA,[st for _,st in spec[1]]); parts=[]
                for name,st in spec[1]:
                    G=whole(MA,name); u=G['uv'].astype(float); info.setdefault('uv_out',{})[name]=round(float(((u<-0.01)|(u>1.01)).any(1).mean()),3)
                    cx_,ry=pos[st]; e=8/1024; G['uv']=(((np.clip(u,0,1)*(1-2*e)+e)+[cx_,ry])/2).astype('f4'); parts.append(G)
                put(ma,k_,ja,concat(parts),donor); tex[texname]=(Cc,Nn)
        J[fid]=ma.build()
    # ---------------- hide table ----------------
    our=jboy.JBOY(J[0]); ranges={}
    for k_ in (1,2):
        o=our.objs[k_]; st=hidetable.strip_tri_starts(our.indices(o)[1]); P=o['pos']
        # starts of the first hide_n[k_] real triangles (degenerate joins don't count as triangles in hide_n)
        real=[s_ for s_,t in st if len(set(t))==3]; ranges[k_]=real[:hide_n[k_]]
    lo=ranges[2]; n_lo=len(hidetable.strip_tri_starts(our.indices(our.objs[2])[1]))
    up_r=[(ranges[1][0],ranges[1][-1])] if ranges[1] else []
    J[0xce]=hidetable.rebuild(B[0xce],up_r,(0,lo[-1]) if lo else (0,0))
    info['hide']={'upper':(hide_n[1],int(up.sum())),'lower':(hide_n[2],int((~up).sum()))}
    # ---------------- textures ----------------
    hd,E=texconv.read_pack(B[0xa]); E=dict(E)
    def setm(base,C,N,skin=False,nname=None,kyle=None):
        r=mats(C,N,skin,kyle); E[base]=r['']; E[base+'_mr']=r['_mr']; E[nname or base+'_n']=r['_n']
    c,n=load_pair(TB,'body'); setm('all_color',c,n,True,'all_n',KYLE+'body_nrm.DDS')
    c,n=load_pair(TB,'head'); setm('head',c,n,True,None,KYLE+'head_nrm.DDS')
    c=texconv.load(ci(TB+'/eye_color.dds')); w,h=texconv.target_size(c.shape[1],c.shape[0]); col=texconv.resize(c,w,h).copy(); col[...,3]=255; E['eye']=texconv.dds_dxt5(col)
    if ci(TB+'/eye_nrm.dds'): c,n=load_pair(TB,'eye'); setm('eye',c,n)
    for name,(C,N) in tex.items(): setm(name,C,N)
    for fid,spec in cfg['hair'].items():
        if spec: base={0x2715:'hair',0x2716:'hair2'}[fid]; r=texconv.hair(None,ci(f"{TA}/{spec[1]}_rai.dds"),cfg.get('tint',(45,35,30))); E[base]=r['']; E[base+'_n']=r['_n']; E[base+'_mr']=r['_mr']
    J[0xa]=texconv.write_pack(list(E.items()),hd)
    pac=epkwrite.build_raw(hdr,[(fid,epkwrite.zblock(J[fid]) if fid in J else blk) for fid,blk in blocks]); open(outpath,'wb').write(pac)
    info['size']=len(pac); return info

R='/home/claude/pairs/MB/'
BRISCOE=dict(work='/home/claude/ext/mb',base=R+'BaseModel/baseModel.mdl',attire_model=R+'159_Default_Attire/159_Attire.mdl',
    tex_base=R+'BaseModel/Textures',tex_attire=R+'159_Default_Attire/Textures',hpl=R+'159_Default_Attire/159_Attire.hpl',
    cover=['M_Jacket','M_Bottoms','M_Leg','M_Shoes','M_L_Hand','M_Rwrist','M_Lelbow','M_Lknee','M_Rknee','M_Rpad'],
    hair={0x2715:None,0x2716:('M_Combinations','combinations')},tint=(40,30,25),
    attire={(0x5601,0):('mesh','M_H_Other','h_other'),(0x5601,1):('mesh','M_L_Hand','l_hand'),(0x5601,2):('mesh','M_Rwrist','rwrist'),
            (0x5601,3):('atlas',[('M_Jacket','jacket'),('M_Bottoms','bottoms'),('M_Leg','leg'),('M_Rpad','rpad')]),
            (0x5601,4):('mesh','M_Shoes','shoes'),
            (0x5602,0):('mesh','M_Lelbow','lelbow'),(0x5602,1):('mesh','M_Lknee','lknee'),(0x5602,2):('mesh','M_Rknee','rknee')})
if __name__=='__main__':
    print(build(BRISCOE,sys.argv[1]))

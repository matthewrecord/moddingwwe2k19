"""General backport builder (2K24 .mdl / 2K25 .mcd -> 2K19 pac on the Fletcher-port container, Andrade donor).
A character is described by a config dict (see configs at the bottom). Everything Flash v4 validated is kept:
own head mesh + Andrade morphs/skin via the fitted surface (lip split), own eyes, his mouth parts shifted by
part centroids, welded body weights, 2K24/25 nrm blue matched to Kyle, hide table from .hpl.
New: texture atlases (several source meshes in one 2K19 slot), hidden-first triangle order for body objects."""
import sys,os,glob,zlib,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
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

def lip_class_topo(P,T,band=3.5):
    """upper/lower lip classes from mesh topology: split the mouth hole loop at its corners into an upper and a lower
    arc, then label nearby vertices by surface (edge-graph) distance to the nearer arc."""
    import loops
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra
    c0=lip_class(P,T,band=band,xf=1.3)   # height-based classes; trust only the clear ones as seeds
    L=[l for l in loops.boundary_loops(T,P) if 30<=len(l)<=80]
    mouth=min(L,key=lambda l:abs(P[l,1].mean()+174)+abs(P[l,0].mean())*3); Q=P[mouth]
    xs=np.linspace(Q[:,0].min(),Q[:,0].max(),41); ly=np.array([Q[np.abs(Q[:,0]-x)<=max(0.5,(xs[1]-xs[0])),1].mean() for x in xs]); lip=np.interp(P[:,0],xs,ly)
    up=np.where((c0==1)&(P[:,1]<lip-0.8))[0]; lo=np.where((c0==-1)&(P[:,1]>lip+0.8))[0]
    E=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]); w=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1)
    G=coo_matrix((np.r_[w,w],(np.r_[E[:,0],E[:,1]],np.r_[E[:,1],E[:,0]])),shape=(len(P),len(P))).tocsr()
    du=dijkstra(G,indices=up,min_only=True,limit=band); dl=dijkstra(G,indices=lo,min_only=True,limit=band)
    zone=c0!=0
    c=np.zeros(len(P),int); c[zone&(du<=dl)]=1; c[zone&(dl<du)]=-1; return c
def meshes_all(M):
    L=M.lods()[0]; return [(m['name'],m['streams'],L[i].reshape(-1,3).astype(int)) for i,m in enumerate(M.meshes)]
def degenerate_m(m,k,j,donor):
    """collapse an object (incl. its morph sets) to one hidden triangle"""
    degenerate(m,k,j,donor,at=(0,-175,-8)); o=j.objs[k]
    for n in range(1,o['f'][25]):
        V=np.zeros(3,dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]); m.data[m.chunk(k,f'vset{n}')]=bytearray(V.tobytes())
KYLE_DIR=os.path.dirname(glob.glob('/home/claude/pairs/Kyle*ORIG*/**/baseModel.mdl',recursive=True)[0])
WILLOW_DIR='/home/claude/pairs/Willow_Nightingale 2k24 ORIGINAL/969_Doudrop/BaseModel'
TEMPLATES={
 'male':dict(pac=PORT,donor='ch68702',ref=KYLE_DIR,body=[(1,'upper'),(2,'lower')],eyes=(3,4),ov=5,mouth=(6,7,8),off=[],
             hair={0x2715:'hair',0x2716:'hair2'},lash=None,hide_objs=[1,2]),
 'female':dict(pac=glob.glob('/home/claude/pairs/Willow*PORT*/*.pac')[0],donor='ch75602',ref=WILLOW_DIR,
             body=[(1,'upper'),(2,'hands'),(3,'lower')],hands_x=66,eyes=(4,5),ov=6,mouth=(7,8,9),off=[10],
             hair={0x2715:'hair'},lash=0x4e22,hide_objs=[1,3]),
}
def bone_world(j):
    """true bone transforms: chain local t/r from the root (extrinsic xyz Euler). Returns {name:(R,p)}"""
    from scipy.spatial.transform import Rotation as Rot
    bs=j.bones; Wm={}; Wp={}
    def w(i):
        if i in Wm: return
        b=bs[i]; R=Rot.from_euler('xyz',b['r']).as_matrix()
        if b['parent']<0: Wm[i]=R; Wp[i]=np.array(b['t'],float)
        else: w(b['parent']); Wm[i]=Wm[b['parent']]@R; Wp[i]=Wp[b['parent']]+Wm[b['parent']]@np.array(b['t'],float)
    for i in range(len(bs)): w(i)
    return {b['name']:(Wm[i],Wp[i]) for i,b in enumerate(bs)}
def move_bones(jb,targets):
    """rewrite local t (and the +64 sphere centre, by the same world delta) so the named bones sit at target world positions"""
    import struct
    j=jboy.JBOY(jb); b=bytearray(jb); W=bone_world(j); off=j.h[10]+8; names=[x['name'] for x in j.bones]; done={}
    for nm,tgt in targets.items():
        if nm not in names: continue
        i=names.index(nm); bb=j.bones[i]; Rp,pp=W[j.bones[bb['parent']]['name']]
        old=W[nm][1]; newt=Rp.T@(np.asarray(tgt,float)-pp); r=off+i*80
        struct.pack_into('>3f',b,r+16,*newt); sph=np.array(struct.unpack_from('>3f',b,r+64))+(np.asarray(tgt)-old); struct.pack_into('>3f',b,r+64,*sph)
        done[nm]=np.round(np.asarray(tgt)-old,2).tolist()
    return bytes(b),done
def eye_forward(P,c):
    """forward axis of an eyeball: centre -> centroid of the cornea cap (vertices within 0.3 cm of the front)"""
    cap=P[P[:,2]<P[:,2].min()+0.3].mean(0); v=cap-c; return v/np.linalg.norm(v)
def sphere_ctr(P):
    A=np.c_[2*P,np.ones(len(P))]; c=np.linalg.lstsq(A,(P**2).sum(1),rcond=None)[0]; return c[:3]
def lighten_undereye(C,MB,strength):
    """blend the band just below each eye (head texture) toward the surrounding cheek colour"""
    from PIL import ImageDraw,ImageFilter
    S,T=MB['M_Head']; P=S['POSITION']; UV=S['TEXCOORD']; E=MB['M_EYE'][0]['POSITION']; h,w=C.shape[:2]
    mask=Image.new('L',(w,h),0); dr=ImageDraw.Draw(mask); cheek=[]
    for sg in (1,-1):
        e=E[E[:,0]*sg>0]; cx,cy=e[:,0].mean(),e[:,1].max()     # lower edge of the eyeball (y down = larger)
        band=(np.abs(P[:,0]-cx)<2.0)&(P[:,1]>cy-0.2)&(P[:,1]<cy+1.4)&(P[:,2]<-8)
        ch_=(np.abs(P[:,0]-cx)<2.0)&(P[:,1]>cy+2.0)&(P[:,1]<cy+3.0)&(P[:,2]<-8)
        for t in T[band[T].all(1)]: dr.polygon([(UV[v,0]*w,UV[v,1]*h) for v in t],fill=255)
        cheek+=[C[min(h-1,int(UV[v,1]*h)),min(w-1,int(UV[v,0]*w)),:3] for v in np.where(ch_)[0]]
    m=np.asarray(mask.filter(ImageFilter.GaussianBlur(w/256)),float)[...,None]/255*strength
    out=C.copy().astype(float); tgt=np.median(np.array(cheek),0); out[...,:3]=out[...,:3]*(1-m)+tgt*m
    return out.clip(0,255).astype('u1')
def opening_class(P,T,loop,band,thr,topo=True):
    """generic upper/lower classes around a face opening (eye or mouth) given its boundary loop. +1 upper (smaller y),
    -1 lower. topo=True: clear seeds (|dy| > thr from the opening's mid-line) propagated by surface distance; False: by height."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra
    Q=P[loop]; x0=Q[:,0].mean(); hw=np.abs(Q[:,0]-x0).max(); xs=np.linspace(Q[:,0].min(),Q[:,0].max(),25)
    ly=np.array([Q[np.abs(Q[:,0]-x)<=max(0.25,xs[1]-xs[0]),1].mean() for x in xs]); line=np.interp(P[:,0],xs,ly)
    zone=(np.abs(P[:,0]-x0)<hw*1.3)&(np.abs(P[:,1]-line)<band)&(P[:,2]<Q[:,2].max()+2)
    c=np.zeros(len(P),int)
    if not topo: c[zone&(P[:,1]<line)]=1; c[zone&(P[:,1]>=line)]=-1; return c,x0,hw
    up=np.where(zone&(P[:,1]<line-thr))[0]; lo=np.where(zone&(P[:,1]>line+thr))[0]
    E=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]); w=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1)
    G=coo_matrix((np.r_[w,w],(np.r_[E[:,0],E[:,1]],np.r_[E[:,1],E[:,0]])),shape=(len(P),len(P))).tocsr()
    du=dijkstra(G,indices=up,min_only=True,limit=band*2); dl=dijkstra(G,indices=lo,min_only=True,limit=band*2)
    c[zone&(du<=dl)&np.isfinite(du)]=1; c[zone&(dl<du)&np.isfinite(dl)]=-1; return c,x0,hw
def eye_loops(P,T):
    import loops
    L=[l for l in loops.boundary_loops(T,P) if 20<=len(l)<=60 and abs(P[l,1].mean()+181)<4 and 2<abs(P[l,0].mean())<6]
    return sorted(L,key=lambda l:-P[l,0].mean())   # [left (+x), right]
def build(cfg,outpath,PROP=None):
    W_=cfg['work']; os.makedirs(W_,exist_ok=True)
    BM=open_model(cfg['base'],W_+'/base.mdl'); AM=open_model(cfg['attire_model'],W_+'/attire.mdl'); MB=meshes(BM); MA=meshes(AM)
    TB,TA=cfg['tex_base'],cfg['tex_attire']
    TP=TEMPLATES[cfg.get('template','male')]
    s=jboy.JBOY(oodl.blocks(open(U+TP['donor']+'.pac','rb').read())[0][1]); donor=body_donor(s)
    hdr,blocks=epkwrite.raw_blocks(TP['pac']); B={f:zlib.decompress(b[16:]) for f,b in blocks}; J={}; info={}
    MAL=meshes_all(AM)
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
    cF=lip_class_topo(PT,TT); cA0=lip_class(np.asarray(W,float),ST); dy=MDa[113][:,1]; near=cA0!=0
    cA=np.zeros(va,int); cA[near&(dy>0.5*dy[near].max())]=-1; cA[near&(dy<=0.5*dy[near].max())]=1; tc=cA[ST]
    for side in (1,-1):
        vs=np.where(cF==side)[0]; ts=ST[~(tc==-side).any(1)]
        if len(vs) and len(ts): a,b_,c_,_=xfer(PT[vs],W,ts,asl,aw,MDa); HS[vs]=a; HW[vs]=b_; HM[:,vs]=c_
    info['lip']=(int((cF==1).sum()),int((cF==-1).sum()))
    # eyelids: same split-transfer as the lips, per eye opening (source: topological; donor: by height at its lid hole)
    opid=np.where(cF!=0,1,0); eyeinfo=[]; eyecent=np.zeros(len(PT),bool)
    if cfg.get('lid_split',False):
        LF=eye_loops(PT,TT); LA=eye_loops(np.asarray(W,float),ST)
        for e_,(lf,la) in enumerate(zip(LF,LA)):
            cE,x0e,hwe=opening_class(PT,TT,lf,1.6,0.35); cD,_,_=opening_class(np.asarray(W,float),ST,la,1.6,0,topo=False)
            cE[cF!=0]=0; tcD=cD[ST]
            for side in (1,-1):
                vs=np.where(cE==side)[0]; ts=ST[~(tcD==-side).any(1)]
                if len(vs) and len(ts): a,b_,c_,_=xfer(PT[vs],W,ts,asl,aw,MDa); HS[vs]=a; HW[vs]=b_; HM[:,vs]=c_
            cF=np.where(cE!=0,cE,cF); opid[cE!=0]=2+e_; eyecent|=(cE!=0)&(np.abs(PT[:,0]-x0e)<0.75*hwe)
            eyeinfo.append((int((cE==1).sum()),int((cE==-1).sum())))
    info['lids']=eyeinfo
    z=HW.sum(1)<1e-6; info['head_unweighted_fixed']=int(z.sum())
    if z.any():
        ok=np.where(~z)[0]; _,nn=cKDTree(PT[ok]).query(PT[z]); HS[z]=HS[ok[nn]]; HW[z]=HW[ok[nn]]
    # smooth morph offsets in the lip zone on the WELDED mesh; only upper<->lower edges are blocked
    from scipy.sparse import coo_matrix,diags
    _,g,inv=np.unique(np.round(PT,3),axis=0,return_index=True,return_inverse=True); inv=inv.ravel(); ng=len(g)
    cg=np.zeros(ng,int); np.maximum.at(cg,inv,np.where(cF==1,1,0)); lo_=np.zeros(ng,int); np.maximum.at(lo_,inv,np.where(cF==-1,1,0)); cg=np.where(cg==1,1,np.where(lo_==1,-1,0))
    E=inv[np.concatenate([TT[:,[0,1]],TT[:,[1,2]],TT[:,[2,0]]])]; E=np.concatenate([E,E[:,::-1]]); E=E[E[:,0]!=E[:,1]]
    import loops
    Lm=[l for l in loops.boundary_loops(TT,PT) if 30<=len(l)<=80]; mq=PT[min(Lm,key=lambda l:abs(PT[l,1].mean()+174)+abs(PT[l,0].mean())*3)]
    xc=0.75*np.abs(mq[:,0]-mq[:,0].mean()).max(); x0=mq[:,0].mean(); info['corner_x']=round(float(xc/0.75),2)
    Pg=PT[g]; mid=np.abs((Pg[E[:,0],0]+Pg[E[:,1],0])/2-x0)<xc
    ecg=np.zeros(ng,bool); np.logical_or.at(ecg,inv,eyecent); eop=np.zeros(ng,int); np.maximum.at(eop,inv,opid)
    eyeblk=ecg[E[:,0]]&ecg[E[:,1]]&(eop[E[:,0]]==eop[E[:,1]])&(eop[E[:,0]]>=2)
    E=E[~((cg[E[:,0]]*cg[E[:,1]]==-1)&(mid&(eop[E[:,0]]<2)|eyeblk))]
    A=coo_matrix((np.ones(len(E)),(E[:,0],E[:,1])),shape=(ng,ng)).tocsr(); A.data[:]=1; A=A+diags(np.ones(ng)); A=diags(1/np.asarray(A.sum(1)).ravel())@A
    zone=cg!=0
    for k in range(HM.shape[0]):
        Hg=np.zeros((ng,3)); np.add.at(Hg,inv,HM[k]); Hg/=np.bincount(inv,minlength=ng)[:,None]
        for it in range(15): Hg[zone]=(A@Hg)[zone]
        HM[k]=Hg[inv]
    Sb,Tb=MB['M_Body']; bsl,bw=welded_weights(Sb['POSITION'],Tb,donor,slot)
    dd,ii=cKDTree(Sb['POSITION']).query(PT); seam=dd<1e-3; HS[seam]=bsl[ii[seam]]; HW[seam]=bw[ii[seam]]; info['neck_seam']=int(seam.sum())
    headW=(PT.copy(),HS.copy(),HW.copy())
    ct=np.where(opid==1,cF,0)[TT]; keep=~((ct==1).any(1)&(ct==-1).any(1)&(np.abs(PT[TT][:,:,0].mean(1)-x0)<xc)); info['mouth_bridge_tris_removed']=int((~keep).sum())
    used=np.unique(TT[keep]); G=mesh_obj(St,TT,keep); vc=len(used); HS,HW,HM=HS[used],HW[used],HM[:,used]
    jbuild.set_object(m,0,G['pos'],G['nrm'].astype('f4'),np.tile(np.array(RED,'u1'),(vc,1)),G['uv'].astype('f4'),np.zeros((vc,3),'f4'),HS,HW,jbuild.tris_to_strip(G['tris']))
    for n in range(1,120):
        V=np.zeros(vc,dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]); V['p']=HM[n-1]; m.data[m.chunk(0,f'vset{n}')]=bytearray(V.tobytes())
    # ---------------- body: hidden-first triangle order so each hide range is one block ----------------
    H=hpl.parse(cfg['hpl'])['M_Body'][0]; hid_v=np.zeros(len(Sb['POSITION']),bool); hid_v[H]=True
    att=np.concatenate([MA[n][0]['POSITION'] for n in cfg['cover']]); near_att=cKDTree(att).query(Sb['POSITION'])[0]<1.0
    hid_t=hid_v[Tb].any(1)|near_att[Tb].all(1)
    C=Sb['POSITION'][Tb].mean(1); hands=(np.abs(C[:,0])>TP['hands_x']) if TP.get('hands_x') else np.zeros(len(C),bool)
    up=((C[:,1]<-108)|(np.abs(C[:,0])>26))&~hands; parts={'upper':up,'lower':~up&~hands,'hands':hands}; hide_n={}
    for k_,role in TP['body']:
        msk=parts[role]
        order=np.concatenate([np.where(msk&hid_t)[0],np.where(msk&~hid_t)[0]]); hide_n[k_]=int((msk&hid_t).sum())
        Tm=Tb[order]; used=np.unique(Tm); G=mesh_obj(Sb,Tm,np.ones(len(Tm),bool))
        put(m,k_,j,G,donor,weights=(bsl[used],bw[used]))
    # ---------------- eyes (own), eye overlay + mouth parts (his, shifted) ----------------
    S,T=MB['M_EYE']; cx=S['POSITION'][T].mean(1)[:,0]
    sides=lambda D:[D['M_EYE'][0]['POSITION'][D['M_EYE'][0]['POSITION'][:,0]*sg>0].mean(0) for sg in (1,-1)]
    eL,eR=TP['eyes']
    if j.objs[eL]['pos'][:,0].mean()<0: eL,eR=eR,eL
    hisE=[j.objs[eL]['pos'].mean(0),j.objs[eR]['pos'].mean(0)]
    for k_,msk,bone in ((eL,cx>0,'J_Eye_L'),(eR,cx<=0,'J_Eye_R')):
        Ge=mesh_obj(S,T,msk); n_=len(Ge['pos']); esl=np.full((n_,7),0xFFFF); esl[:,0]=slot[bone]; ew=np.zeros((n_,7),'f4'); ew[:,0]=1
        # straighten a splayed/crossed eyeball: turn it about its centre so its forward axis points straight ahead (-z)
        Pe=Ge['pos'].astype(float); c_=sphere_ctr(Pe); f_=eye_forward(Pe,c_); ang0=np.arctan2(f_[0],-f_[2])
        if abs(np.degrees(ang0))>cfg.get('eye_straighten_deg',2.0):
            Nn=Ge['nrm'].astype(float)
            for it in range(8):                     # iterate: the cornea cap is re-selected after each turn
                f_=eye_forward(Pe,c_); ang=np.arctan2(f_[0],-f_[2])
                if abs(np.degrees(ang))<0.3: break
                ca,sa=np.cos(ang),np.sin(ang); R_=np.array([[ca,0,sa],[0,1,0],[-sa,0,ca]])   # rotate about y by -ang
                Pe=(Pe-c_)@R_.T+c_; Nn=Nn@R_.T
            Ge['pos']=Pe.astype('f4'); Ge['nrm']=Nn.astype('f4')
            info.setdefault('eye_straightened_deg',[]).append(round(float(np.degrees(ang0)),1))
        put(m,k_,j,Ge,donor,weights=(esl,ew))
    KM=meshes(mdlfmt.MDL(TP['ref']+'/baseModel.mdl'))
    ctr=lambda D,n:D[n][0]['POSITION'].mean(0)
    dT=ctr(MB,'M_Teeth')-ctr(KM,'M_Teeth'); dB=ctr(MB,'M_MouthBag')-ctr(KM,'M_MouthBag'); dG=ctr(MB,'M_Tongue')-ctr(KM,'M_Tongue')
    def shift(k_,fn):
        o=j.objs[k_]; ch=m.chunk(k_,'vset0'); V=np.frombuffer(bytes(m.data[ch][:o['vc']*28]),dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]).copy()
        V['p']=fn(V['p']); m.data[ch][:len(V.tobytes())]=V.tobytes()
    fE=sides(MB)
    def ov(p):
        p=p.copy(); L=p[:,0]>0; p[L]+=fE[0]-hisE[0]; p[~L]+=fE[1]-hisE[1]; return p
    kb,kt,kg=TP['mouth']; shift(TP['ov'],ov); shift(kb,lambda p:p+(dT+dB)/2); shift(kt,lambda p:p+dT); shift(kg,lambda p:p+dG)
    for k_ in TP.get('off',[]): degenerate_m(m,k_,j,donor)
    info['mouth_shift']=np.round(dT,2).tolist()
    J[0]=m.build()
    # ---------------- hair slots (one or more meshes; several textures -> 2x2 rai atlas) ----------------
    hairtex={}
    for fid,base in TP['hair'].items():
        jh=jboy.JBOY(B[fid]); mh=jbuild.Model(jh); spec=cfg['hair'].get(fid)
        if spec and isinstance(spec,tuple): spec=[spec]
        if spec:
            stems=list(dict.fromkeys(st for _,st in spec)); parts=[]; seen=[]
            for name,st in spec:
                for G in [mesh_obj(S_,T_,np.ones(len(T_),bool)) for n_,S_,T_ in MAL[::-1] if n_==name]:   # last copy of exact duplicates wins
                    if any(len(x)==len(G['pos']) and np.allclose(x,G['pos']) for x in seen): continue   # exact duplicate mesh
                    seen.append(G['pos'])
                    if len(stems)>1:
                        i_=stems.index(st); e=8/1024; G['uv']=(((np.clip(G['uv'].astype(float),0,1)*(1-2*e)+e)+[i_%2,i_//2])/2).astype('f4')
                    parts.append(G)
            put(mh,0,jh,concat(parts) if len(parts)>1 else parts[0],donor,col=WHITE,hair=True); hairtex[base]=stems
            info.setdefault('hair_verts',{})[hex(fid)]=sum(len(G['pos']) for G in parts)
        else:
            p=np.array([[0,-185,0],[0.001,-185,0],[0,-185.001,0]],'f4'); put(mh,0,jh,dict(pos=p,nrm=np.tile(np.array([0,0,1],'f4'),(3,1)),uv=np.zeros((3,2),'f4'),tris=np.array([[0,1,2]])),donor,col=WHITE,hair=True)
        J[fid]=mh.build()
    # ---------------- eyelash model (female template): own lashes, morphs + skin from the built head ----------------
    if TP.get('lash') and 'M_transB_eyelash' in MB:
        jl=jboy.JBOY(B[TP['lash']]); ml=jbuild.Model(jl); S,T=MB['M_transB_eyelash']; Gl=mesh_obj(S,T,np.ones(len(T),bool))
        Hp=jboy.JBOY(J[0]).objs[0]; HT=jboy.strip_to_tris(jboy.JBOY(J[0]).indices(Hp)[1])
        a_,b_,Ml,dl=xfer(Gl['pos'].astype(float),Hp['pos'].astype(float),HT,HS,HW,HM)
        mainp=[j.bones[b]['name'] for b in j.palette]; sl2=palette_slot(jl)
        for v in range(len(a_)):
            row=[(sl2.get(mainp[x]),y) for x,y in zip(a_[v],b_[v]) if y>0 and x<len(mainp)]; row=[(x,y) for x,y in row if x is not None] or [(sl2['J_Head'],1.0)]
            t=sum(y for _,y in row); a_[v]=0xFFFF; b_[v]=0
            for q,(x,y) in enumerate(sorted(row)[:7]): a_[v,q]=x; b_[v,q]=y/t
        put(ml,0,jl,Gl,donor,col=WHITE,weights=(a_,b_)); vc_=len(Gl['pos'])
        for n in range(1,jl.objs[0]['f'][25]):
            V=np.zeros(vc_,dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]); V['p']=Ml[n-1]; ml.data[ml.chunk(0,f'vset{n}')]=bytearray(V.tobytes())
        J[TP['lash']]=ml.build(); info['lash']=(vc_,round(float(dl.max()),2))
    # ---------------- attire slots (single mesh, split by side, or 2x2 atlas) ----------------
    tex={}
    hp,hs,hw=headW; th=cKDTree(hp); tb=cKDTree(Sb['POSITION'])
    def att_w(G,ja):
        """attire weights: body donor, except points whose nearest skin is the head take the head's own weights"""
        sl,w=welded_weights(G['pos'],G['tris'],donor,palette_slot(ja)); dh,ih=th.query(G['pos']); db,_=tb.query(G['pos']); onh=dh<db
        if onh.any():
            # main-model slots -> this attire model's slots, by bone name
            mainp=[j.bones[b]['name'] for b in j.palette]; sl2=palette_slot(ja)
            for v in np.where(onh)[0]:
                row=[(sl2.get(mainp[a]),b) for a,b in zip(hs[ih[v]],hw[ih[v]]) if b>0 and a<len(mainp)]
                row=[(a,b) for a,b in row if a is not None] or [(sl2['J_Head'],1.0)]
                t=sum(b for _,b in row); sl[v]=0xFFFF; w[v]=0
                for q,(a,b) in enumerate(sorted(row)[:7]): sl[v,q]=a; w[v,q]=b/t
        info.setdefault('attire_on_head',{})[len(info.get('attire_on_head',{}))]=int(onh.sum())
        return sl,w
    for fid in (0x5601,0x5602):
        ja=jboy.JBOY(B[fid]); ma=jbuild.Model(ja)
        for k_ in range(len(ja.objs)):
            spec=cfg['attire'].get((fid,k_)); texname=jboy.obj_params(ja,ja.objs[k_])['g_mDiffusePrm'].split(':')[1]
            if spec is None: degenerate(ma,k_,ja,donor); continue
            kind=spec[0]
            if kind=='mesh':
                _,name,stem=spec[:3]; S,T=MA[name]; msk=np.ones(len(T),bool)
                if len(spec)>3: cxs=S['POSITION'][T].mean(1)[:,0]; msk=cxs>0 if spec[3]=='L' else cxs<=0
                G=mesh_obj(S,T,msk); put(ma,k_,ja,G,donor,weights=att_w(G,ja)); tex[texname]=load_pair(TA,stem)
            else:   # ('atlas', [(mesh, stem), ...])
                Cc,Nn,pos=atlas(TA,[st for _,st in spec[1]]); parts=[]
                for name,st in spec[1]:
                    G=whole(MA,name); u=G['uv'].astype(float); info.setdefault('uv_out',{})[name]=round(float(((u<-0.01)|(u>1.01)).any(1).mean()),3)
                    cx_,ry=pos[st]; e=8/1024; G['uv']=(((np.clip(u,0,1)*(1-2*e)+e)+[cx_,ry])/2).astype('f4'); parts.append(G)
                G=concat(parts); put(ma,k_,ja,G,donor,weights=att_w(G,ja)); tex[texname]=(Cc,Nn)
        J[fid]=ma.build()
    # ---------------- hide table: one hidden span per template hide object ----------------
    our=jboy.JBOY(J[0]); blocks_={}
    for k_ in TP['hide_objs']:
        o=our.objs[k_]; st=hidetable.strip_tri_starts(our.indices(o)[1]); real=[s_ for s_,t in st if len(set(t))==3][:hide_n.get(k_,0)]
        blocks_[k_-1]=[(real[0],real[-1])] if real else []
    J[0xce]=hidetable.build_blocks(B[0xce],blocks_)
    info['hide']={k_:hide_n.get(k_,0) for k_ in TP['hide_objs']}
    # ---------------- textures ----------------
    hd,E=texconv.read_pack(B[0xa]); E=dict(E)
    def setm(base,C,N,skin=False,nname=None,kyle=None):
        r=mats(C,N,skin,kyle); E[base]=r['']; E[base+'_mr']=r['_mr']; E[nname or base+'_n']=r['_n']
    c,n=load_pair(TB,'body'); setm('all_color',c,n,True,'all_n',ci(TP['ref']+'/Textures/body_nrm.dds'))
    c,n=load_pair(TB,'head')
    if cfg.get('undereye_lighten'): c=lighten_undereye(c,MB,cfg['undereye_lighten']); info['undereye_lighten']=cfg['undereye_lighten']
    setm('head',c,n,True,None,ci(TP['ref']+'/Textures/head_nrm.dds'))
    c=texconv.load(ci(TB+'/eye_color.dds')); w,h=texconv.target_size(c.shape[1],c.shape[0]); col=texconv.resize(c,w,h).copy(); col[...,3]=255; E['eye']=texconv.dds_dxt5(col)
    # eye_n / eye_mr are NOT converted: the 2K19 eye shader needs the container's masks (eye_n alpha = iris mask for
    # g_fEyePa iris depth; eye_mr = cornea/sclera gloss mask). Source eye maps are flat -> 'dead' eyes. Colour only.
    for name,(C,N) in tex.items(): setm(name,C,N)
    for base,stems in hairtex.items():
        if len(stems)==1: r=texconv.hair(None,ci(f"{TA}/{stems[0]}_rai.dds"),cfg.get('tint',(45,35,30)))
        else:
            Rr=np.zeros((2048,2048,4),'u1')
            for i_,st in enumerate(stems): Rr[(i_//2)*1024:(i_//2+1)*1024,(i_%2)*1024:(i_%2+1)*1024]=texconv.resize(texconv.load(ci(f"{TA}/{st}_rai.dds")),1024,1024)
            Image.fromarray(Rr).save(W_+'/hair_atlas_rai.png'); r=texconv.hair(None,W_+'/hair_atlas_rai.png',cfg.get('tint',(45,35,30)))
        E[base]=r['']; E[base+'_n']=r['_n']; E[base+'_mr']=r['_mr']
    if TP.get('lash') and ci(TB+'/eyelash_color.dds'):
        c=texconv.load(ci(TB+'/eyelash_color.dds')); w,h=texconv.target_size(c.shape[1],c.shape[0]); E['eyelash']=texconv.dds_dxt5(texconv.resize(c,w,h))
    J[0xa]=texconv.write_pack(list(E.items()),hd)
    # eye pivots -> eyeball sphere centres, in every model that carries the eye bones
    if cfg.get('eye_pivots',True):
        jj=jboy.JBOY(J[0]); tg={}
        for k_ in TP['eyes']:
            P=jj.objs[k_]['pos'].astype(float); tg['J_Eye_L' if P[:,0].mean()>0 else 'J_Eye_R']=sphere_ctr(P)
        for fid,blk in blocks:
            d=J.get(fid) or zlib.decompress(blk[16:])
            if d[:4]==b'JBOY':
                J[fid],done=move_bones(d,tg)
                if fid==0: info['eye_pivot_moved']=done
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

F='/home/claude/pairs/FMW/'
FLASH=dict(work='/home/claude/ext/fmw2',base=F+'BaseModel/baseModel.mcd',attire_model=F+'159_Default_Attire/159_Attire.mcd',
    tex_base=F+'BaseModel/Textures',tex_attire=F+'159_Default_Attire/Textures',hpl=F+'159_Default_Attire/159_Attire.hpl',
    cover=['M_Bottoms','M_Shoes','M_Wrist'],hair={0x2715:('M_Hair','hair'),0x2716:('M_Combinations','combinations')},tint=(45,35,30),
    attire={(0x5601,1):('mesh','M_Wrist','wrist','L'),(0x5601,2):('mesh','M_Wrist','wrist','R'),
            (0x5601,3):('mesh','M_Bottoms','bottoms'),(0x5601,4):('mesh','M_Shoes','shoes')})
T_='/home/claude/pairs/TS/817_Toni_Storm_AEWRev25/'
TONI=dict(template='female',undereye_lighten=0.45,work='/home/claude/ext/ts',base=T_+'BaseModel/basemodel.mcd',attire_model=T_+'817_Default_Attire/817_Attire.mcd',
    tex_base=T_+'BaseModel/Textures',tex_attire=T_+'817_Default_Attire/Textures',hpl=T_+'817_Default_Attire/817_Attire.hpl',
    cover=['M_Outfit','M_Outfit_Belt','M_Tights','M_Shoes','M_Tape'],
    hair={0x2715:[('M_Hair','hair'),('M_Hair2','hair2')]},tint=(232,214,178),
    attire={(0x5602,0):('mesh','M_Outfit','outfit'),(0x5601,3):('mesh','M_Tights','tights'),(0x5601,4):('mesh','M_Shoes','shoes'),
            (0x5601,1):('mesh','M_Tape','tape','L'),(0x5601,2):('mesh','M_Tape','tape','R'),
            (0x5601,0):('atlas',[('M_Outfit_Belt','outfit_belt'),('M_Rose','rose'),('M_Nails','nails')])})
CONFIGS={'briscoe':BRISCOE,'flash':FLASH,'toni':TONI}

if __name__=='__main__':
    print(build(CONFIGS[sys.argv[1]],sys.argv[2]))

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
    if path.lower().endswith('.mcd'):
        # 2K25: MCD! hdr, MDL! at 12. 2K26: MCD! wrapper with CTG!/MDL!/HPL! chunks -> the MDL file starts at 'MDL!MDL!'+4
        b=open(path,'rb').read(); assert b[:4]==b'MCD!'
        i=b.find(b'MDL!MDL!'); assert i>=0, 'no MDL! chunk in '+path
        open(cache,'wb').write(b[i+4:]); path=cache
    return mdlfmt.MDL(path)
def mats(C,N,skin=False,kyle_nrm=None,keep_alpha=False):
    """color/nrm arrays -> 2K19 (<mat>, _mr, _n) DXT5 by the 2K24 rules; optional blue-channel match to Kyle"""
    N=N.copy()
    if kyle_nrm is not None and N[...,2].std()>1: N[...,2]=hist_match(N[...,2],texconv.load(kyle_nrm)[...,2])   # constant (2K26) gloss: keep, rank-matching a flat channel makes noise
    N=N.astype(np.int32); col=C.copy()
    if not keep_alpha: col[...,3]=255
    n=np.stack([255-N[...,0],255-N[...,1],np.full(N.shape[:2],255),np.full(N.shape[:2],255)],-1).astype('u1')
    mr=np.stack([np.zeros(N.shape[:2],int) if skin else N[...,3],N[...,2],255-N[...,2],np.full(N.shape[:2],255)],-1).astype('u1')
    return {'':texconv.dds_dxt5(col),'_mr':texconv.dds_dxt5(mr),'_n':texconv.dds_dxt5(n)}
NRM2K26_GLOSS=124   # median of the 2K24 _nrm blue (gloss) channel (Kyle body)
def load_pair(tdir,stem,cap=2048):
    c=texconv.load(ci(f'{tdir}/{stem}_color.dds')); np_=ci(f'{tdir}/{stem}_nrm.dds')
    n=texconv.load(np_) if np_ else np.dstack([np.full(c.shape[:2],128,'u1')]*2+[np.full(c.shape[:2],128,'u1'),np.zeros(c.shape[:2],'u1')])
    if np_ and texconv.is_bc7_in_dxt5(np_):   # 2K26: pure tangent normal (B = z, no gloss/metal) -> neutral 2K24-style gloss, no metal
        n=n.copy(); n[...,2]=NRM2K26_GLOSS; n[...,3]=0
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
 'female':dict(pac=(glob.glob('/home/claude/pairs/Willow*PORT*/*.pac')+[None])[0],donor='ch75602',ref=WILLOW_DIR,
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
def lid_gaps(P,T,M):
    """per side: (rest gap, [gap under each morph]) at the eye centre (as lidcheck.py)"""
    out={}
    for side,l in zip('LR',eye_loops(P,T)):
        Q=P[l]; x0=Q[:,0].mean(); hw=np.abs(Q[:,0]-x0).max(); c=np.abs(Q[:,0]-x0)<0.3*hw; ymid=Q[:,1].mean()
        up=np.array(l)[c&(Q[:,1]<ymid)]; lo=np.array(l)[c&(Q[:,1]>=ymid)]
        g=lambda X:(X[lo,1].mean()-X[up,1].mean()); out[side]=(g(P),np.array([g(P+M[n]) for n in range(M.shape[0])]),Q.mean(0),hw)
    return out
def lid_fit(P,T,HM,DP,DT,DM,thr=0.4,iters=3):
    """scale eye-closing morph travel around each eye so the remaining lid gap matches the donor's (bigger source eye openings close short)"""
    D=lid_gaps(DP,DT,DM); log={}
    for _ in range(iters):
        O=lid_gaps(P,T,HM)
        for side in 'LR':
            g0,gm,_,_=D[side]; o0,om,ctr,hw=O[side]; rd=gm/g0; ro=om/o0
            w=np.clip(1-np.linalg.norm(P-ctr,axis=1)/(1.6*hw),0,1)**0.5
            for n in np.where(rd<thr)[0]:
                k=float(np.clip((1-rd[n])/max(1-ro[n],1e-3),0.85,1.25)); HM[n]*=(1+(k-1)*w)[:,None]
                log[f'{side}{n+1}']=(round(100*rd[n]),round(100*ro[n]))
    O=lid_gaps(P,T,HM); return HM,{k_:(v[0],v[1],round(100*O[k_[0]][1][int(k_[1:])-1]/O[k_[0]][0])) for k_,v in log.items()}
def smooth_skin(sl,w,T,npal,iters,keep=None):
    """Laplacian-smooth skin weights over mesh edges (dense over palette slots), then top-7 per vertex.
    Slots are written weight-descending (stock hair order); unused = 0xFFFF / 0."""
    import scipy.sparse as sp_
    n=len(sl); ns=sl.shape[1]; real=(sl!=0xFFFF)&(w>0)
    D=sp_.csr_matrix((w[real].astype(float),(np.repeat(np.arange(n),ns).reshape(n,ns)[real],sl[real])),shape=(n,npal+1)).toarray()
    E=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]); A=sp_.coo_matrix((np.ones(len(E)*2),(np.r_[E[:,0],E[:,1]],np.r_[E[:,1],E[:,0]])),shape=(n,n)).tocsr()
    deg=np.asarray(A.sum(1)).ravel()+1
    for _ in range(iters): D=(A@D+D)/deg[:,None]
    o=np.argsort(-D,axis=1)[:,:ns]; ww=np.take_along_axis(D,o,1); ww[ww<1e-4]=0; ww/=np.maximum(ww.sum(1,keepdims=True),1e-9)
    sl2=np.where(ww>0,o,0xFFFF); return sl2.astype(int),ww.astype('f4')
def hair_body_blend(Jh,Jbody_list,y0=-160.0,y1=-150.0,dfull=2.0,dzero=8.0,smooth=0,post_smooth=0,a_max=1.0):
    """Hair strands resting on the shoulders/chest: blend their skin toward the nearest body/attire vertex's bones, so the
    shoulders carry them instead of the head/physics chain (no clipping when the body moves under the hair).
    Appends the needed body bones to the hair JBOY's palette."""
    import jcheck,struct as st_
    jh=jboy.JBOY(Jh); o=jh.objs[0]; P=o['pos'].astype(float); sk=jcheck.raw_skin(jh,o).copy(); ns=sk.shape[1]
    names=[b_['name'] for b_ in jh.bones]; pal=list(jh.palette)
    BP=[];BS=[]
    for jb_,ks in Jbody_list:
        jb=jboy.JBOY(jb_)
        for k in ks:
            ob=jb.objs[k]; s2=jcheck.raw_skin(jb,ob); BP.append(ob['pos'].astype(float))
            Wb_={n_:p_ for n_,(R_,p_) in bone_world(jb).items()}
            def up(bi):   # nearest ancestor that the hair skeleton also has (body twist/helper bones are not in it);
                b0=bi       # rootless donor helpers (m###) take the nearest J_ bone by position, not J_Head
                while bi>=0 and jb.bones[bi]['name'] not in names: bi=jb.bones[bi]['parent']
                if bi>=0: return jb.bones[bi]['name']
                c_=Wb_.get(jb.bones[b0]['name'])
                if c_ is None: return 'J_Head'
                return min((np.linalg.norm(Wb_[n_]-c_),n_) for n_ in Wb_ if n_.startswith('J_') and n_ in names)[1]
            BS.append([[ (up(int(jb.palette[i])),w) for i,w in zip(r['i'],r['w']) if w>0 and i<len(jb.palette)] for r in s2])
    BP=np.concatenate(BP); BS=sum(BS,[])
    d,nn=cKDTree(BP).query(P)
    a=np.clip((P[:,1]-y0)/(y1-y0),0,1)*np.clip((dzero-d)/(dzero-dfull),0,1)
    if smooth:   # spread the blend along the strands so neighbouring vertices don't pull apart (stretch on head turns)
        import scipy.sparse as sp_
        T_=jboy.strip_to_tris(jh.indices(o)[1]); E_=np.concatenate([T_[:,[0,1]],T_[:,[1,2]],T_[:,[2,0]]]); n_=len(P)
        A_=sp_.coo_matrix((np.ones(len(E_)*2),(np.r_[E_[:,0],E_[:,1]],np.r_[E_[:,1],E_[:,0]])),shape=(n_,n_)).tocsr(); deg=np.asarray(A_.sum(1)).ravel()+1
        for _ in range(smooth): a=(A_@a+a)/deg
    a=np.minimum(a,a_max)   # keep some physics share (a fully body-held strand looks frozen)
    nb=0
    for v in np.where(a>0.01)[0]:
        acc={}
        for i,w in zip(sk['i'][v],sk['w'][v]):
            if w>0: acc[int(i)]=acc.get(int(i),0)+float(w)*(1-a[v])
        for nm,w in BS[nn[v]]:
            bi=names.index(nm)
            if bi not in pal: pal.append(bi)
            sl=pal.index(bi); acc[sl]=acc.get(sl,0)+float(w)*a[v]
        top=[t for t in sorted(acc.items(),key=lambda t:-t[1])[:ns] if t[1]>1e-6]; tot=sum(w for _,w in top)   # weight-descending, like the stock hair
        sk['i'][v]=0xFFFF; sk['w'][v]=0; sk['p'][v]=0
        for q,(sl,w) in enumerate(top): sk['i'][v,q]=sl; sk['w'][v,q]=w/tot
        nb+=1
    if post_smooth:   # smooth the final (chain + body) skin along the strands
        T_=jboy.strip_to_tris(jh.indices(o)[1]); s2,w2=smooth_skin(sk['i'].astype(int),sk['w'].astype('f4'),T_,len(pal),post_smooth)
        sk['i']=s2; sk['w']=w2; sk['p']=0
    m=jbuild.Model(jh); m.data[m.chunk(0,'skin')]=bytearray(sk.tobytes())
    pc=[c for c in m.order if m.name[c]=='pal'][0]; m.data[pc]=bytearray(st_.pack('>%dI'%len(pal),*pal))
    hc=[c for c in m.order if m.name[c]=='palhdr'][0]; st_.pack_into('>I',m.data[hc],0,len(pal))
    return m.build(),dict(blended=int(nb),full=int((a>0.99).sum()),pal_added=len(pal)-len(jh.palette))
def closest_on_mesh(P,T,Q,k=12):
    """closest point on triangle mesh (P,T) for each query: (triangle index, barycentrics (n,3))"""
    tri=P[T]; C=tri.mean(1); _,cand=cKDTree(C).query(Q,k=min(k,len(T)))
    best=np.full(len(Q),np.inf); bt=np.zeros(len(Q),int); bb=np.zeros((len(Q),3))
    for c in range(cand.shape[1]):
        t=cand[:,c]; A=tri[t,0];B_=tri[t,1];C_=tri[t,2]
        e0=B_-A;e1=C_-A;v=Q-A; d00=(e0*e0).sum(1);d01=(e0*e1).sum(1);d11=(e1*e1).sum(1);d20=(v*e0).sum(1);d21=(v*e1).sum(1)
        den=np.maximum(d00*d11-d01*d01,1e-12); bv=(d11*d20-d01*d21)/den; bw_=(d00*d21-d01*d20)/den
        bv=np.clip(bv,0,1); bw_=np.clip(bw_,0,1); s_=bv+bw_; over=s_>1; bv[over]/=s_[over]; bw_[over]/=s_[over]; bu=1-bv-bw_
        X=A*bu[:,None]+B_*bv[:,None]+C_*bw_[:,None]; d=np.linalg.norm(Q-X,axis=1); better=d<best
        best[better]=d[better]; bt[better]=t[better]; bb[better]=np.stack([bu,bv,bw_],1)[better]
    return bt,bb,best
def blend_skin(sl1,w1,sl2,w2,a):
    """per-vertex mix of two skins (a=0 -> first, 1 -> second), 7 slots, weight-sorted then slot-ascending"""
    sl=sl1.copy(); w=w1.copy()
    for v in np.where(a>1e-3)[0]:
        acc={}
        for s_,x in zip(sl1[v],w1[v]):
            if x>0: acc[int(s_)]=acc.get(int(s_),0)+x*(1-a[v])
        for s_,x in zip(sl2[v],w2[v]):
            if x>0: acc[int(s_)]=acc.get(int(s_),0)+x*a[v]
        it=sorted(sorted(acc.items(),key=lambda t:-t[1])[:7]); t=sum(x for _,x in it) or 1
        sl[v]=0xFFFF; w[v]=0
        for q,(s_,x) in enumerate(it): sl[v,q]=s_; w[v,q]=x/t
    return sl,w
def legs_ramp(P,cfg):
    """donor_legs=(y_top,y_full): 0 above y_top, 1 below y_full (y grows downward)"""
    y0,y1=cfg['donor_legs']; return np.clip((P[:,1]-y0)/(y1-y0),0,1)
def missing_frac(S,bones,slot,idx=None):
    """per vertex: share of the source weight on bones the 2K19 skeleton doesn't have (2K26 jiggle/volume helpers,
    the rootless cloth 'vector'); ancestor fallback misplaces them (a thigh jiggle bone hangs off J_Hips)"""
    miss=np.array([b['name'] not in slot for b in bones]); BI=S['BI'] if idx is None else S['BI'][idx]; BW=S['BW'] if idx is None else S['BW'][idx]
    BW=BW.astype(float)/(255.0 if BW.dtype==np.uint8 else 1.0); return (miss[BI.astype(int)]*BW).sum(1)/np.maximum(BW.sum(1),1e-9)
def source_weights(S,bones,slot,idx=None,drop_unmapped=False):
    """the mod's own skin weights (BI/BW, by its bone names) -> 2K19 palette slots; bones missing from the palette
    hand their weight to the nearest ancestor that exists. idx: subset of vertices."""
    names=[b['name'] for b in bones]; par=[b['parent'] for b in bones]; memo={}
    def to_slot(i):
        if i in memo: return memo[i]
        k=i
        while k>=0 and names[k] not in slot: k=par[k]
        memo[i]=slot[names[k]] if k>=0 else (None if drop_unmapped else slot['J_Head']); return memo[i]   # drop: rootless bones (2K26 'vector') give no weight
    BI=S['BI'] if idx is None else S['BI'][idx]; BW=S['BW'] if idx is None else S['BW'][idx]
    BW=BW.astype(float)/(255.0 if BW.dtype==np.uint8 else 1.0); vc=len(BI); sl=np.full((vc,7),0xFFFF); w=np.zeros((vc,7),'f4')
    for v in range(vc):
        acc={}
        for i,x in zip(BI[v],BW[v]):
            if x>0:
                a=to_slot(int(i))
                if a is not None: acc[a]=acc.get(a,0)+x
        it=sorted(sorted(acc.items(),key=lambda t:-t[1])[:7]); t=sum(x for _,x in it) or 1
        for q,(a,x) in enumerate(it): sl[v,q]=a; w[v,q]=x/t
    return sl,w
def vnormals(P,T):
    fn=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]); N=np.zeros_like(P)
    for k in range(3): np.add.at(N,T[:,k],fn)
    return N/np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-9)
def opaque_cover(S,T,tex_dir,stem,thr=128,frac=0.1):
    """drop cover triangles that sample transparent texels (cut-outs, mesh panels): the body under them shows in game"""
    try: c,_=load_pair(tex_dir,stem)
    except Exception: return T
    if c.shape[2]<4: return T
    uv=np.asarray(S['TEXCOORD'] if 'TEXCOORD' in S else S['UV'])[:,:2].astype(float); h,w=c.shape[:2]
    def a(u): return c[np.clip((u[:,1]%1)*h,0,h-1).astype(int),np.clip((u[:,0]%1)*w,0,w-1).astype(int),3]
    rng=np.random.default_rng(0); B_=rng.dirichlet((1,1,1),24); U=uv[T]   # 24 samples per triangle: lace/cut-out strips are thinner than the triangles
    tr=np.mean([a((U*b_[None,:,None]).sum(1))<thr for b_ in B_],axis=0); keep=tr<frac
    return T[keep]
def geom_hidden(P,T,cover,depth=8.0,N=None):
    """body vertices whose outward normal ray hits a cover-mesh triangle within 'depth' cm (start 0.3 cm inside the skin)"""
    tri=np.concatenate([S_['POSITION'][:,:3].astype(float)[T_] for S_,T_ in cover]); C=tri.mean(1)
    rad=np.linalg.norm(tri-C[:,None],axis=2).max(); kd=cKDTree(C); P=P.astype(float)
    if N is None: N=vnormals(P,T)
    N=N[:,:3].astype(float); N/=np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-9); hid=np.zeros(len(P),bool)
    e1=tri[:,1]-tri[:,0]; e2=tri[:,2]-tri[:,0]
    for i,nb in enumerate(kd.query_ball_point(P+N*depth/2,depth/2+rad+0.3)):
        if not nb: continue
        nb=np.array(nb); o=P[i]-N[i]*0.3; d=N[i]
        h=np.cross(d,e2[nb]); a=(e1[nb]*h).sum(1); ok=np.abs(a)>1e-9; f=np.where(ok,1/np.where(ok,a,1),0)
        s_=o-tri[nb,0]; u=f*(s_*h).sum(1); q=np.cross(s_,e1[nb]); v=f*(q@d); t=f*(e2[nb]*q).sum(1)
        hid[i]=bool((ok&(u>=0)&(v>=0)&(u+v<=1)&(t>0)&(t<depth+0.3)).any())
    return hid
def mask_clamp(P,T,mask,HM,recess=0.3,margin=0.1,keep=None,feather=1.0):
    """head verts whose outward ray hits the mask within 4 cm: recess them, and clamp each morph's outward push to the gap"""
    S_,T_=mask; tri=S_['POSITION'][:,:3].astype(float)[T_]; C=tri.mean(1); kd=cKDTree(C); rad=np.linalg.norm(tri-C[:,None],axis=2).max()
    e1=tri[:,1]-tri[:,0]; e2=tri[:,2]-tri[:,0]; N=vnormals(P,np.asarray(T))
    c0=P.mean(0); N=N if ((P-c0)*N).sum(1).mean()>0 else -N   # point outward
    gap=np.full(len(P),np.inf)
    for i,nb in enumerate(kd.query_ball_point(P+N*2,2+rad)):
        if not nb: continue
        nb=np.array(nb); d=N[i]; o=P[i]-d*0.05
        h=np.cross(d,e2[nb]); a=(e1[nb]*h).sum(1); ok=np.abs(a)>1e-9; f=np.where(ok,1/np.where(ok,a,1),0)
        s_=o-tri[nb,0]; u=f*(s_*h).sum(1); q=np.cross(s_,e1[nb]); v=f*(q@d); t=f*(e2[nb]*q).sum(1)
        hit=ok&(u>=0)&(v>=0)&(u+v<=1)&(t>0)&(t<4)
        if hit.any(): gap[i]=t[hit].min()-0.05
    cov=np.isfinite(gap); rc=cov&~keep if keep is not None else cov   # keep: no recess there (eyelids), but morphs still clamped
    r=np.zeros(len(P))
    if recess>0 and rc.any() and (~rc).any():   # feather the recess to 0 over 'feather' cm toward the mask openings (no step at the rim)
        d=cKDTree(P[~rc]).query(P[rc])[0]; r[rc]=recess*np.clip(d/feather,0,1)
    P=P.copy(); P-=N*r[:,None]; room=np.where(cov,gap+r-margin,np.inf)
    HM=HM.copy()
    for k in range(HM.shape[0]):
        push=(HM[k]*N).sum(1); over=cov&(push>room)
        HM[k,over]-=N[over]*(push[over]-room[over])[:,None]
    return P,HM,int(cov.sum())
def hair_from(pac,head_pos):
    """donor hair JBOY (fid 0x2715) + its 0x2580 + referenced textures; vertices moved onto our scalp by a radial correspondence field"""
    hdr_,bl_=epkwrite.raw_blocks(pac); D_={}
    for f,b in bl_:
        try: D_[f]=zlib.decompress(b[16:])
        except Exception: pass
    jh=jboy.JBOY(D_[0x2715]); m=jbuild.Model(jh)
    dh=jboy.JBOY(D_[0]).objs[0]['pos'].astype(float); oh=np.asarray(head_pos,float)
    ds=dh[dh[:,1]<-168]; os_=oh[oh[:,1]<-168]; c=np.array([0,-180.0,-3.0])
    u=lambda P:(P-c)/np.linalg.norm(P-c,axis=1,keepdims=True)
    _,nn=cKDTree(u(os_)).query(u(ds)); delta=os_[nn]-ds    # same direction from the head centre
    # keep only the radial part (no sliding along the scalp)
    r=u(ds); delta=(delta*r).sum(1,keepdims=True)*r
    kd=cKDTree(ds); names=set()
    for k,o in enumerate(jh.objs):
        P=o['pos'].astype(float); d,i=kd.query(P,8); w=1/np.maximum(d,0.3)**2; w/=w.sum(1,keepdims=True)
        P2=P+(delta[i]*w[...,None]).sum(1)
        ch=m.chunk(k,'vset0'); buf=m.data[ch]; vc=o['vc']
        V=np.frombuffer(bytes(buf[:28*vc]),dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]).copy(); V['p']=P2
        m.data[ch]=bytearray(V.tobytes())+buf[28*vc:]
        for v in jboy.obj_params(jh,o).values():
            if isinstance(v,str) and v.startswith('tex:'): names.add(v[4:])
    tex={}
    for f in (0xa,0xc,0x11):
        if f in D_:
            try: _,E_=texconv.read_pack(D_[f])
            except Exception: continue
            for n_,d_ in E_:
                if n_ in names and n_ not in tex and not n_.startswith('_a_'): tex[n_]=d_
    return m.build(),D_[0x2580],tex
def rig_dreads(G,jh,head_pos,lock=0.35,tip=0.8,min_piece=20):
    """Skin rope-like strands (dreads) to a donor hair rig: each connected piece follows ONE Hair_bNN chain, locked to J_Head
    over the first 'lock' of its length, physics share ramping to 'tip' at the end. Small pieces (hairline, crown) = J_Head."""
    import re
    from collections import defaultdict
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    W=bone_world(jh); slot={jh.bones[b]['name']:i for i,b in enumerate(jh.palette)}
    ch=defaultdict(list)
    for b in jh.bones:
        m=re.match(r'Hair_b(\d+)(?:_(\d+))?$',b['name'])
        if m and b['name'] in slot: ch[int(m.group(1))].append((int(m.group(2)) if m.group(2) else -1,b['name']))
    chains=[[n for _,n in sorted(v)] for v in ch.values() if len(v)>=2]
    CP=[np.array([W[n][1] for n in c]) for c in chains]
    P=G['pos'].astype(float); T=G['tris']; vc=len(P)
    _,inv=np.unique(np.round(P,3),axis=0,return_inverse=True); inv=inv.ravel(); Tw=inv[T]
    e=np.concatenate([Tw[:,[0,1]],Tw[:,[1,2]],Tw[:,[2,0]]]); m_=inv.max()+1
    _,lab=connected_components(coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(m_,m_))); lab=lab[inv]
    hc=np.asarray(head_pos,float); hk=cKDTree(hc)
    sl=np.zeros((vc,4),int); w=np.zeros((vc,4),'f4'); sl[:,0]=slot['J_Head']; w[:,0]=1; stats=[0,0]
    for c in np.unique(lab):
        idx=np.where(lab==c)[0]
        if len(idx)<=min_piece: stats[1]+=1; continue
        Q=P[idx]; dh=hk.query(Q)[0]; root=Q[dh<=np.percentile(dh,5)].mean(0)
        far=Q[np.argmax(np.linalg.norm(Q-root,axis=1))]; ax=far-root; Ld=np.linalg.norm(ax)
        if Ld<6: stats[1]+=1; continue   # short tuft: stays on the head
        ax/=Ld; sv=np.clip(((Q-root)@ax)/Ld,0,1)
        sc=[np.linalg.norm(cp[0]-root)+0.5*np.linalg.norm(cp[min(1,len(cp)-1)]-(root+ax*min(Ld,12))) for cp in CP]; k=int(np.argmin(sc)); cp=CP[k]; names=chains[k]
        seg=np.r_[0,np.cumsum(np.linalg.norm(np.diff(cp,axis=0),axis=1))]; seg=seg/seg[-1]   # joint positions along the chain, 0..1
        f=tip*np.clip((sv-lock)/(1-lock),0,1)**1.5   # physics share: none on the locked top, heavier toward the tip
        for q,v in enumerate(idx):
            u=sv[q]; i=min(np.searchsorted(seg,u,side='right')-1,len(seg)-2); a=(u-seg[i])/max(seg[i+1]-seg[i],1e-6)
            b1,b2=slot[names[i]],slot[names[i+1]] if i+1<len(names)-1 else slot[names[i]]
            wb2=0.5*max(a-0.6,0)/0.4 if b2!=b1 else 0
            sl[v]=[slot['J_Head'],b1,b2,slot['J_Head']]; w[v]=[1-f[q],f[q]*(1-wb2),f[q]*wb2,0]
        stats[0]+=1
    return sl,w,{'dreads_rigged':stats[0],'pieces_on_head':stats[1],'chains':len(chains)}
def cap_small_holes(T,P,maxlen=8):
    """close tiny boundary holes (source modelling gaps -> pinholes of light in game). Real openings (neck, mouth,
    eyes) are far longer than maxlen. Cap winding follows the neighbouring triangle."""
    import loops
    E={}
    for t in T:
        for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])): E[(a,b)]=1
    add=[]
    for l in loops.boundary_loops(T,P):
        if len(l)>maxlen: continue
        l=list(l); fwd=(l[0],l[1]) in E           # loop runs along existing edges -> cap must run the other way
        for i in range(1,len(l)-1):
            add.append((l[0],l[i+1],l[i]) if fwd else (l[0],l[i],l[i+1]))
    return (np.concatenate([T,np.array(add,int)]) if add else T),len(add)
def build(cfg,outpath,PROP=None):
    W_=cfg['work']; os.makedirs(W_,exist_ok=True)
    BM=open_model(cfg['base'],W_+'/base.mdl'); AM=open_model(cfg['attire_model'],W_+'/attire.mdl'); MB=meshes(BM); MA=meshes(AM)
    TB,TA=cfg['tex_base'],cfg['tex_attire']
    TP=TEMPLATES[cfg.get('template','male')]
    s=jboy.JBOY(oodl.blocks(open(U+TP['donor']+'.pac','rb').read())[0][1])
    sw=jboy.JBOY(oodl.blocks(open(U+cfg['weight_donor']+'.pac','rb').read())[0][1]) if cfg.get('weight_donor') else s
    donor=body_donor(sw)
    hdr,blocks=epkwrite.raw_blocks(TP['pac']); B={f:zlib.decompress(b[16:]) for f,b in blocks}; J={}; info={}
    MAL=meshes_all(AM); info['weight_donor']=cfg.get('weight_donor',TP['donor'])
    j=jboy.JBOY(B[0]); m=jbuild.Model(j); slot=palette_slot(j)
    # ---------------- head ----------------
    so=s.objs[0]; MDa=np.asarray(jboy.morphs(s,so)); ST=jboy.strip_to_tris(s.indices(so)[1])
    St,TT=MB['M_Head']; PT=St['POSITION'].astype(float); TT,nh=cap_small_holes(TT,PT); info['head_holes_capped']=nh
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
    Sb,Tb=MB['M_Body']; Tb,nb=cap_small_holes(Tb,Sb['POSITION']); info['body_holes_capped']=nb
    if cfg.get('weights')=='source':
        bsl,bw=source_weights(Sb,BM.bones,slot,drop_unmapped=True)   # 2K26 rootless 'vector' (cloth) bone: drop it, don't hand it to J_Head
        bad=bw.sum(1)<1e-6
        if bad.any():
            _,nn=cKDTree(Sb['POSITION'][~bad]).query(Sb['POSITION'][bad]); g_=np.where(~bad)[0][nn]; bsl[bad]=bsl[g_]; bw[bad]=bw[g_]
        info['body_vector_dropped']=int(bad.sum())
        if cfg.get('donor_for_missing',True):
            mf=missing_frac(Sb,BM.bones,slot)*np.clip((Sb['POSITION'][:,1].astype(float)+125)/10,0,1)   # hips and legs only (upper-body helpers were fine in game)
            if (mf>0.01).any(): dsl,dw=welded_weights(Sb['POSITION'],Tb,donor,slot); bsl,bw=blend_skin(bsl,bw,dsl,dw,mf); info['body_missing_to_donor']=int((mf>0.01).sum())
        if cfg.get('donor_legs'):   # 2K26 hip/knee helper bones are driven differently in 2K19: take the donor's skin on hips and legs
            a_=legs_ramp(Sb['POSITION'].astype(float),cfg); dsl,dw=welded_weights(Sb['POSITION'],Tb,donor,slot); bsl,bw=blend_skin(bsl,bw,dsl,dw,a_); info['donor_legs_body']=int((a_>0).sum())
    else: bsl,bw=welded_weights(Sb['POSITION'],Tb,donor,slot)
    dd,ii=cKDTree(Sb['POSITION']).query(PT); seam=dd<1e-3; HS[seam]=bsl[ii[seam]]; HW[seam]=bw[ii[seam]]; info['neck_seam']=int(seam.sum())
    headW=(PT.copy(),HS.copy(),HW.copy())
    ct=np.where(opid==1,cF,0)[TT]; keep=~((ct==1).any(1)&(ct==-1).any(1)&(np.abs(PT[TT][:,:,0].mean(1)-x0)<xc)); info['mouth_bridge_tris_removed']=int((~keep).sum())
    used=np.unique(TT[keep]); G=mesh_obj(St,TT,keep); vc=len(used); HS,HW,HM=HS[used],HW[used],HM[:,used]
    if cfg.get('mask'):   # head-locked mask: morphs move only the head, so keep covered skin behind the mask
        eyez=cKDTree(MB['M_EYE'][0]['POSITION'][:,:3]).query(G['pos'])[0]<cfg.get('mask_eye_keep',1.5)   # lids stay put
        G['pos'],HM,nc=mask_clamp(G['pos'].astype(float),G['tris'],MA[cfg['mask']],HM,cfg.get('mask_recess',0.3),keep=eyez); G['pos'],HM,_=mask_clamp(G['pos'],G['tris'],MA[cfg['mask']],HM,0.0,0.15,keep=eyez); G['pos']=G['pos'].astype('f4'); info['mask_covered_head_verts']=nc
    if cfg.get('lid_fit'): HM,info['lid_fit']=lid_fit(G['pos'].astype(float),G['tris'],np.asarray(HM,float),np.asarray(so['pos'],float),ST,MDa)
    jbuild.set_object(m,0,G['pos'],G['nrm'].astype('f4'),np.tile(np.array(RED,'u1'),(vc,1)),G['uv'].astype('f4'),np.zeros((vc,3),'f4'),HS,HW,jbuild.tris_to_strip(G['tris']))
    for n in range(1,120):
        V=np.zeros(vc,dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]); V['p']=HM[n-1]; m.data[m.chunk(0,f'vset{n}')]=bytearray(V.tobytes())
    # ---------------- body: hidden-first triangle order so each hide range is one block ----------------
    att=np.concatenate([MA[n][0]['POSITION'] for n in cfg['cover']]); near_att=cKDTree(att).query(Sb['POSITION'])[0]<1.0
    if cfg.get('hide','hpl')=='geom':
        # 2K26: attire HPL! lists index the game's generic body, not the character's own M_Body -> unusable.
        # Hide a body vertex when a cover mesh lies just outside it along its normal (within 'hide_depth' cm).
        hid_v=geom_hidden(Sb['POSITION'][:,:3],Tb,[(MA[n][0],opaque_cover(MA[n][0],MA[n][1],cfg['tex_attire'],n[2:].lower())) for n in cfg['cover']],cfg.get('hide_depth',8.0),N=Sb['NORMAL'])
        # keep the skin drawn under see-through parts (lace, cut-outs): body verts within reach of a dropped (transparent) cover triangle
        Ctr=[]
        for n_ in cfg['cover']:
            S_,T_=MA[n_]; T2_=opaque_cover(S_,T_,cfg['tex_attire'],n_[2:].lower()); k_=set(map(tuple,np.asarray(T2_)))
            D_=np.array([t for t in np.asarray(T_) if tuple(t) not in k_])
            if len(D_): Ctr.append(S_['POSITION'][:,:3].astype(float)[D_].mean(1))
        if Ctr:
            dC,_=cKDTree(np.concatenate(Ctr)).query(Sb['POSITION'][:,:3].astype(float)); seen=hid_v&(dC<cfg.get('seethrough_reach',3.0)); hid_v=hid_v&~seen; info['seethrough_unhidden']=int(seen.sum()); info['geom_body_verts']=int(hid_v.sum())
        hid_t=hid_v[Tb].all(1)
    else:
        H=hpl.parse(cfg['hpl']).get('M_Body',[[]])[0]; hid_v=np.zeros(len(Sb['POSITION']),bool); hid_v[H]=True; info['hpl_body_verts']=len(H)
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
        if cfg.get('eye_recess'): Ge['pos']=(Ge['pos'].astype(float)+[0,0,cfg['eye_recess']]).astype('f4'); info['eye_recess']=cfg['eye_recess']   # +z = back into the socket
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
    hairtex={}; hairtex_from={}
    for fid,base in TP['hair'].items():
        if fid==0x2715 and cfg.get('hair_from'):   # whole in-game-proven hair (model + 0x2580 physics + its textures) from another 2K19 pac, fitted to our scalp
            J[fid],J[0x2580],donor_tex=hair_from(cfg['hair_from'],jboy.JBOY(J[0]).objs[0]['pos']); info['hair_from']=(os.path.basename(cfg['hair_from']),len(J[0x2580]))
            hairtex_from=donor_tex; continue
        hr_=cfg.get('hair_rig') if fid==0x2715 else None   # dict(pac=<2K19 pac with physics hair>, lock=, tip=): OUR strands on its rig
        hp_=cfg.get('hair_physics') if fid==0x2715 else None   # (stock pac id): its hair model (Hair_b physics bones) + 0x2580 sim block
        if hp_:
            Hd=[d for _,d in oodl.blocks(open(U+hp_+'.pac','rb').read()) if d and d[:4]==b'JBOY' and jboy.JBOY(d).objs[0]['shader']=='yCS_hair' and any(b_['name'].startswith('Hair_b') for b_ in jboy.JBOY(d).bones)][0]
            S80=[d for _,d in oodl.blocks(open(U+hp_+'.pac','rb').read()) if d and d[:8]==bytes.fromhex('0000000020000000')][0]
            jh=jboy.JBOY(Hd); J[0x2580]=S80; info['hair_physics']=(hp_,len(S80))
        elif hr_:
            if hr_['pac'].startswith('ch'):   # stock Oodle pac (standard skin-slot layout; mod hair may use another layout the game reads differently)
                bk=[d for _,d in oodl.blocks(open(U+hr_['pac']+'.pac','rb').read()) if d]
                jh=jboy.JBOY([d for d in bk if d[:4]==b'JBOY' and jboy.JBOY(d).objs[0]['shader']=='yCS_hair' and any(b_['name'].startswith('Hair_b') for b_ in jboy.JBOY(d).bones)][0])
                J[0x2580]=[d for d in bk if d[:8]==bytes.fromhex('0000000020000000')][0]
            else:
                hdr2,bl2=epkwrite.raw_blocks(hr_['pac']); D2={f_:zlib.decompress(b_[16:]) for f_,b_ in bl2 if f_ in (0x2715,0x2580)}
                jh=jboy.JBOY(D2[0x2715]); J[0x2580]=D2[0x2580]
            info['hair_rig']=os.path.basename(hr_['pac'])
        else: jh=jboy.JBOY(B[fid])
        mh=jbuild.Model(jh); spec=cfg['hair'].get(fid)
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
            Gh=concat(parts) if len(parts)>1 else parts[0]
            if hr_:
                slh,wh,st=rig_dreads(Gh,jh,jboy.JBOY(J[0]).objs[0]['pos'],hr_.get('lock',0.35),hr_.get('tip',0.8)); info['hair_rig_stats']=st
                put(mh,0,jh,Gh,donor,col=WHITE,hair=True)
                vc=len(Gh['pos']); tan=np.zeros((vc,3),'f4'); tan[0::2]=(0,1,0); tan[1::2]=(1,0,1)
                jbuild.set_object(mh,0,Gh['pos'],Gh['nrm'].astype('f4'),np.tile(np.array(WHITE,'u1'),(vc,1)),Gh['uv'].astype('f4'),tan,slh,wh,jbuild.tris_to_strip(Gh['tris']))
            elif hp_:   # skin each strand vertex like the nearest physics-hair vertex (same palette: J_Head + Hair_b*)
                ho=jh.objs[0]; sk=jcheck.raw_skin(jh,ho); _,nn=cKDTree(ho['pos']).query(Gh['pos'])
                put(mh,0,jh,Gh,donor,col=WHITE,hair=True)
                vc=len(Gh['pos']); tan=np.zeros((vc,3),'f4'); tan[0::2]=(0,1,0); tan[1::2]=(1,0,1)
                hsl,hw_=sk['i'][nn].astype(int),sk['w'][nn].astype('f4')
                if cfg.get('hair_smooth'):   # smooth the chain weights along each strand card so one triangle doesn't span two chains (tears when the chains move apart)
                    hsl,hw_=smooth_skin(hsl,hw_,Gh['tris'],len(jh.palette),cfg['hair_smooth']); info['hair_smooth']=cfg['hair_smooth']
                jbuild.set_object(mh,0,Gh['pos'],Gh['nrm'].astype('f4'),np.tile(np.array(WHITE,'u1'),(vc,1)),Gh['uv'].astype('f4'),tan,hsl,hw_,jbuild.tris_to_strip(Gh['tris']))
            else: put(mh,0,jh,Gh,donor,col=WHITE,hair=True)
            hairtex[base]=stems
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
    tex={}; texstem={}
    hp,hs,hw=headW; th=cKDTree(hp); tb=cKDTree(Sb['POSITION'])
    def att_w(G,ja,src=None):
        """attire weights: the mod's own (cfg weights='source'), else body donor with head-nearest points taking the head's weights"""
        if cfg.get('weights')=='source' and src is not None:
            parts_=[source_weights(S_,AM.bones,palette_slot(ja),u_,drop_unmapped=True) for S_,u_ in src]
            sl,w=np.concatenate([p[0] for p in parts_]),np.concatenate([p[1] for p in parts_])
            if cfg.get('donor_for_missing',True):
                mf=np.concatenate([missing_frac(S_,AM.bones,palette_slot(ja),u_) for S_,u_ in src])*np.clip((G['pos'][:,1].astype(float)+125)/10,0,1)
                if (mf>0.01).any():
                    dsl,dw=welded_weights(G['pos'],G['tris'],donor,palette_slot(ja)); zero=w.sum(1)<1e-6; w[zero]=dw[zero]; sl[zero]=dsl[zero]
                    sl,w=blend_skin(sl,w,dsl,dw,mf); info['attire_missing_to_donor']=info.get('attire_missing_to_donor',0)+int((mf>0.01).sum())
            bad=w.sum(1)<1e-6
            if bad.any() and (~bad).any():   # source vertices with no weight: take the nearest weighted vertex's skin
                _,nn=cKDTree(G['pos'][~bad]).query(G['pos'][bad]); good=np.where(~bad)[0][nn]; sl[bad]=sl[good]; w[bad]=w[good]
                info['attire_unweighted_fixed']=info.get('attire_unweighted_fixed',0)+int(bad.sum())
            tf=cfg.get('tight_follow',1.5)
            if tf:   # tight gear on hips/legs moves exactly with the skin under it (else the hidden skin shows through the gap)
                Pb_=Sb['POSITION'][:,:3].astype(float); tB,bB,dB=closest_on_mesh(Pb_,np.asarray(Tb),G['pos'][:,:3].astype(float))
                at=np.clip((2*tf-dB)/tf,0,1)*np.clip((G['pos'][:,1].astype(float)+125)/10,0,1)
                if (at>0).any():
                    mainp=[j.bones[b]['name'] for b in j.palette]; sl2=palette_slot(ja); fs=np.full(sl.shape,0xFFFF); fw=np.zeros(w.shape,'f4')
                    Tb_=np.asarray(Tb)
                    for v in np.where(at>0)[0]:
                        acc={}
                        for vv,bc in zip(Tb_[tB[v]],bB[v]):   # barycentric mix of the 3 body vertices' skins (continuous, no steps)
                            for a_,b_ in zip(bsl[vv],bw[vv]):
                                if b_>0 and a_<len(mainp) and sl2.get(mainp[a_]) is not None: acc[sl2[mainp[a_]]]=acc.get(sl2[mainp[a_]],0)+bc*b_
                        row=sorted(acc.items(),key=lambda t:-t[1])[:7]; t_=sum(b_ for _,b_ in row) or 1
                        for q,(a_,b_) in enumerate(row[:7]): fs[v,q]=a_; fw[v,q]=b_/t_
                    ok_=fw.sum(1)>0; at=at*ok_; sl,w=blend_skin(sl,w,fs,fw,at); info['tight_follow']=info.get('tight_follow',0)+int((at>0).sum())
            if cfg.get('donor_legs'):
                a_=legs_ramp(G['pos'].astype(float),cfg)
                if (a_>0).any(): dsl,dw=welded_weights(G['pos'],G['tris'],donor,palette_slot(ja)); sl,w=blend_skin(sl,w,dsl,dw,a_); info['donor_legs_attire']=info.get('donor_legs_attire',0)+int((a_>0).sum())
            return sl,w
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
                if stem in cfg.get('alpha_cut',()):   # 2K19 gear shader is opaque: drop triangles in transparent texture areas (fringe)
                    A=texconv.load(ci(f"{TA}/{stem}_color.dds"))[...,3]; h_,w_=A.shape; UV=S['TEXCOORD'][:,:2].astype(float)%1.0
                    smp=np.concatenate([UV[T],UV[T].mean(1,keepdims=True)],1)
                    av=A[np.clip((smp[...,1]*h_).astype(int),0,h_-1),np.clip((smp[...,0]*w_).astype(int),0,w_-1)]
                    keep=av.max(1)>=128; info.setdefault('alpha_cut',{})[name]=int((msk&~keep).sum()); msk&=keep
                G=mesh_obj(S,T,msk); put(ma,k_,ja,G,donor,weights=att_w(G,ja,None if name in cfg.get('donor_weights',()) else [(S,np.unique(T[msk]))])); tex[texname]=load_pair(TA,stem); texstem[texname]=stem   # donor_weights: 2K19 body skin (legs)
            else:   # ('atlas', [(mesh, stem), ...])
                Cc,Nn,pos=atlas(TA,[st for _,st in spec[1]]); parts=[]; srcs=[(MA[n_][0],np.unique(MA[n_][1])) for n_,_ in spec[1]]
                for name,st in spec[1]:
                    G=whole(MA,name); u=G['uv'].astype(float); info.setdefault('uv_out',{})[name]=round(float(((u<-0.01)|(u>1.01)).any(1).mean()),3)
                    cx_,ry=pos[st]; e=8/1024; G['uv']=(((np.clip(u,0,1)*(1-2*e)+e)+[cx_,ry])/2).astype('f4'); parts.append(G)
                G=concat(parts); put(ma,k_,ja,G,donor,weights=att_w(G,ja,srcs)); tex[texname]=(Cc,Nn)
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
    def setm(base,C,N,skin=False,nname=None,kyle=None,keep_alpha=False):
        r=mats(C,N,skin,kyle,keep_alpha); E[base]=r['']; E[base+'_mr']=r['_mr']; E[nname or base+'_n']=r['_n']
    c,n=load_pair(TB,'body')
    if cfg.get('diag_paint'):   # DIAGNOSTIC: paint the body texels under given boxes (|x| lo,hi, y lo,hi) a flat colour
        from PIL import ImageDraw
        c=c.copy(); h_,w_=c.shape[:2]; im_=Image.fromarray(c); dr_=ImageDraw.Draw(im_); Pb_=Sb['POSITION'][:,:3].astype(float); uv_=np.asarray(Sb['TEXCOORD'])[:,:2]
        for (x0,x1,y0,y1),rgb in cfg['diag_paint']:
            m_=(np.abs(Pb_[:,0])>=x0)&(np.abs(Pb_[:,0])<=x1)&(Pb_[:,1]>=y0)&(Pb_[:,1]<=y1)
            for t in np.asarray(Tb)[m_[np.asarray(Tb)].any(1)]:
                dr_.polygon([((uv_[v,0]%1)*w_,(uv_[v,1]%1)*h_) for v in t],fill=tuple(rgb)+(255,))
        c=np.asarray(im_); info['diag_paint']=len(cfg['diag_paint'])
    setm('all_color',c,n,True,'all_n',ci(TP['ref']+'/Textures/body_nrm.dds'))
    c,n=load_pair(TB,'head')
    if cfg.get('undereye_lighten'): c=lighten_undereye(c,MB,cfg['undereye_lighten']); info['undereye_lighten']=cfg['undereye_lighten']
    setm('head',c,n,True,None,ci(TP['ref']+'/Textures/head_nrm.dds'))
    c=texconv.load(ci(TB+'/eye_color.dds')); w,h=texconv.target_size(c.shape[1],c.shape[0]); col=texconv.resize(c,w,h).copy(); col[...,3]=255; E['eye']=texconv.dds_dxt5(col)
    # eye_n / eye_mr are NOT converted: the 2K19 eye shader needs the container's masks (eye_n alpha = iris mask for
    # g_fEyePa iris depth; eye_mr = cornea/sclera gloss mask). Source eye maps are flat -> 'dead' eyes. Colour only.
    sheer=cfg.get('sheer',{}); ka=set(cfg.get('keep_alpha',()))
    skin_rgb=np.median(load_pair(TB,'body')[0][...,:3].reshape(-1,3),axis=0)
    for name,(C,N) in tex.items():
        st_=texstem.get(name,name)
        if st_ in sheer:   # 2K26 sheer fabric (shader opacity, colour alone reads as solid dark): paint skin through it
            C=C.copy(); col_,tol_,mix_=sheer[st_]; d_=np.abs(C[...,:3].astype(int)-np.array(col_)).max(-1)<tol_
            C[...,:3][d_]=(mix_*(np.array(cfg['diag_sheer_rgb']) if cfg.get('diag_sheer_rgb') else skin_rgb)+(1-mix_)*C[...,:3][d_].astype(float)).astype('u1'); info.setdefault('sheer',{})[st_]=int(d_.sum())
        setm(name,C,N,keep_alpha=st_ in ka)
    for base,stems in hairtex.items():
        if len(stems)==1 and not ci(f"{TA}/{stems[0]}_rai.dds") and ci(f"{TA}/{stems[0]}_color.dds"):
            r=texconv.hair_color(ci(f"{TA}/{stems[0]}_color.dds"))   # 2K26 mask/wig: real colour + alpha on the head-locked hair slot
        elif len(stems)==1: r=texconv.hair(None,ci(f"{TA}/{stems[0]}_rai.dds"),cfg.get('tint',(45,35,30)))
        else:
            Rr=np.zeros((2048,2048,4),'u1')
            for i_,st in enumerate(stems): Rr[(i_//2)*1024:(i_//2+1)*1024,(i_%2)*1024:(i_%2+1)*1024]=texconv.resize(texconv.load(ci(f"{TA}/{st}_rai.dds")),1024,1024)
            Image.fromarray(Rr).save(W_+'/hair_atlas_rai.png'); r=texconv.hair(None,W_+'/hair_atlas_rai.png',cfg.get('tint',(45,35,30)))
        E[base]=r['']; E[base+'_n']=r['_n']; E[base+'_mr']=r['_mr']
    if TP.get('lash') and ci(TB+'/eyelash_color.dds'):
        c=texconv.load(ci(TB+'/eyelash_color.dds')); w,h=texconv.target_size(c.shape[1],c.shape[0]); E['eyelash']=texconv.dds_dxt5(texconv.resize(c,w,h))
    E.update(hairtex_from)
    J[0xa]=texconv.write_pack(list(E.items()),hd)
    if cfg.get('prop_from'): J[0x50]=[d for _,d in oodl.blocks(open(U+cfg['prop_from']+'.pac','rb').read()) if len(d)==3056][0]; info['prop_from']=cfg['prop_from']
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
    if cfg.get('emd'): hdr=hdr[:0x80C]+cfg['emd'].encode()+hdr[0x814:]
    if cfg.get('hair_body_blend') and 0x2715 in J:
        jb0=jboy.JBOY(J[0]); L=[(J[0],[k for k,o in enumerate(jb0.objs) if o['shader']=='yCS_skin' and k>0])]
        for f_ in (0x5601,0x5602):
            if f_ in J: L.append((J[f_],list(range(len(jboy.JBOY(J[f_]).objs)))))
        J[0x2715],info['hair_body_blend']=hair_body_blend(J[0x2715],L,**cfg['hair_body_blend'])
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
K_='/home/claude/pairs/KL/710_Noam_Dar/'
KEITH=dict(template='male',weights='source',work='/home/claude/ext/kl',base=K_+'BaseModel/BaseModel.mdl',attire_model=K_+'710_Default_Attire/710_Attire.mdl',
    tex_base=K_+'BaseModel/Textures',tex_attire=K_+'710_Default_Attire/Textures',hpl=K_+'710_Default_Attire/710_Attire.hpl',
    cover=['M_Jacket','M_Underwear','M_Shoes','M_L_Kneepad','M_R_Kneepad','M_L_Elbowpad'],prop_from='ch23802',
    hair={0x2715:None,0x2716:[('M_Combinations','combinations')]},tint=(25,20,18),
    attire={(0x5601,0):('mesh','M_Jacket','jacket'),(0x5601,3):('mesh','M_Underwear','underwear'),(0x5601,4):('mesh','M_Shoes','shoes'),
            (0x5602,0):('mesh','M_L_Elbowpad','l_elbowpad'),(0x5602,1):('mesh','M_L_Kneepad','l_kneepad'),(0x5602,2):('mesh','M_R_Kneepad','r_kneepad')})
KEITH_RING=dict(KEITH,work='/home/claude/ext/kl',emd='00050602',cover=['M_Underwear','M_Shoes','M_L_Kneepad','M_R_Kneepad','M_L_Elbowpad'],
    attire={k:v for k,v in KEITH['attire'].items() if v[1]!='M_Jacket'})
KEITH_ENT=dict(KEITH,work='/home/claude/ext/kl',emd='00050604')
# ---- 2K26 sources (extracted with Aurora CAK Foundry; .mcd with embedded HPL!, hide table read from the attire .mcd) ----
JE_='/home/claude/pairs/JE/1235_JeVon_Evans/'
JEVON=dict(template='male',hair_rig=dict(pac='ch36802',lock=0.09,tip=0.8),donor_weights=['M_L_Kneepad','M_R_Kneepad'],weights='source',hide='geom',eye_straighten_deg=0.5,work='/home/claude/ext/je',emd='00050602',
    base=JE_+'BaseModel/baseModel.mcd',attire_model=JE_+'1235_Default_Attire/1235_Attire.mcd',
    tex_base=JE_+'BaseModel/Textures',tex_attire=JE_+'1235_Default_Attire/Textures',hpl=JE_+'1235_Default_Attire/1235_Attire.mcd',
    cover=['M_Tops','M_Tights','M_Shoes','M_L_Kneepad','M_R_Kneepad','M_L_Wrist','M_R_Wrist'],
    hair={0x2715:('M_Hair','hair'),0x2716:('M_Combinations','combinations')},tint=(28,21,17),
    attire={(0x5601,0):('atlas',[('M_U_Acce','u_acce'),('M_Pierce','pierce'),('M_R_A_Acce','r_a_acce')]),
            (0x5601,1):('mesh','M_L_Wrist','l_wrist'),(0x5601,2):('mesh','M_R_Wrist','r_wrist'),
            (0x5601,3):('mesh','M_Tights','tights'),(0x5601,4):('mesh','M_Shoes','shoes'),
            (0x5602,0):('mesh','M_Tops','tops'),(0x5602,1):('mesh','M_L_Kneepad','l_kneepad'),(0x5602,2):('mesh','M_R_Kneepad','r_kneepad')})
PC_='/home/claude/pairs/PC/1505_Psycho_Clown/'
PSYCHO=dict(template='male',weights='source',hide='geom',eye_straighten_deg=0.5,work='/home/claude/ext/pc',emd='00050602',
    base=PC_+'BaseModel/baseModel.mcd',attire_model=PC_+'Default_Attire/Attire.mcd',
    tex_base=PC_+'BaseModel/Textures',tex_attire=PC_+'Default_Attire/Textures',hpl=PC_+'Default_Attire/Attire.mcd',
    cover=['M_Jacket','M_Tops','M_Bottoms','M_Shoes'],alpha_cut=['jacket'],
    hair={0x2715:('M_Mask','mask')},mask='M_Mask',
    attire={(0x5601,0):('atlas',[('M_L_A_Acce','l_a_acce'),('M_R_A_Acce','r_a_acce')]),
            (0x5601,3):('mesh','M_Bottoms','bottoms'),(0x5601,4):('mesh','M_Shoes','shoes'),
            (0x5602,0):('mesh','M_Jacket','jacket'),(0x5602,1):('mesh','M_Tops','tops')})
PSYCHO_RING=dict(PSYCHO,emd='00050602',cover=['M_Tops','M_Bottoms','M_Shoes'],alpha_cut=[],
    attire={k:v for k,v in PSYCHO['attire'].items() if k!=(0x5602,0)})   # wrestles without the fringe jacket
JEVON_RING=dict(JEVON,emd='00050602',cover=[c for c in JEVON['cover'] if c!='M_Tops'],
    attire={k:v for k,v in JEVON['attire'].items() if k!=(0x5602,0)})   # wrestles without the tank top
RH_='/home/claude/pairs/RH/1163_Rhea_Ripley/'
RHEA=dict(template='female',lid_fit=True,eye_recess=0.05,hair_physics='ch43402',weights='source',hide='geom',donor_weights=['M_L_Kneepad','M_R_Kneepad'],eye_straighten_deg=0.5,work='/home/claude/ext/rh',emd='00050602',
    base=RH_+'BaseModel/baseModel.mcd',attire_model=RH_+'1163_Deluxe_Edition/1163_Attire.mcd',
    tex_base=RH_+'BaseModel/Textures',tex_attire=RH_+'1163_Deluxe_Edition/Textures',hpl=RH_+'1163_Deluxe_Edition/1163_Attire.mcd',
    cover=['M_Tops','M_Tights','M_Shoes','M_L_Kneepad','M_R_Kneepad','M_L_Wrist','M_R_Wrist','M_R_Elbowpad'],
    hair={0x2715:('M_Hair','hair')},tint=(20,18,18),
    attire={(0x5601,0):('atlas',[('M_U_Acce','u_acce'),('M_Pierce','pierce'),('M_Pierce1','pierce1'),('M_R_Elbowpad','r_elbowpad')]),
            (0x5601,1):('mesh','M_L_Wrist','l_wrist'),(0x5601,2):('mesh','M_R_Wrist','r_wrist'),
            (0x5601,3):('mesh','M_Tights','tights'),(0x5601,4):('mesh','M_Shoes','shoes'),
            (0x5602,0):('mesh','M_Tops','tops'),(0x5602,1):('mesh','M_L_Kneepad','l_kneepad'),(0x5602,2):('mesh','M_R_Kneepad','r_kneepad')})
R2_='/home/claude/pairs/RH2/816_Rhea_Ripley_2019/'
RHEA_RING=dict(template='female',lid_fit=True,eye_recess=0.05,hair_physics='ch43402',hair_body_blend=dict(y0=-180.0,y1=-160.0,dfull=3.0,dzero=12.0,smooth=100,post_smooth=60),
    weights='source',hide='geom',eye_straighten_deg=0.5,work='/home/claude/ext/rh2',emd='00050602',
    base=R2_+'BaseModel/BaseModel.mcd',attire_model=R2_+'816_Default_Attire/816_Attire.mcd',
    tex_base=R2_+'BaseModel/Textures',tex_attire=R2_+'816_Default_Attire/Textures',hpl=R2_+'816_Default_Attire/816_Attire.mcd',
    cover=['M_Brassiere','M_Tights','M_Shoes','M_L_Wrist','M_R_Wrist'],
    hair={0x2715:('M_Hair','hair')},tint=(20,18,18),
    attire={(0x5601,0):('atlas',[('M_U_Acce','U_acce'),('M_Pierce','pierce'),('M_L_A_Acce','l_a_acce'),('M_R_A_Acce','r_a_acce')]),
            (0x5601,1):('mesh','M_L_Wrist','l_wrist'),(0x5601,2):('mesh','M_R_Wrist','r_wrist'),
            (0x5601,3):('mesh','M_Tights','tights'),(0x5601,4):('mesh','M_Shoes','shoes'),
            (0x5602,0):('mesh','M_Brassiere','brassiere')})
RHEA_ENT=dict(RHEA_RING,work='/home/claude/ext/rh2e',emd='00050604',cover=RHEA_RING['cover'],   # open vest swings: body under it must stay drawn
   
    attire={**RHEA_RING['attire'],(0x5602,1):('mesh','M_Jacket','jacket')})
RQ_='/home/claude/pairs/RQ/927_Raquel_Rodriguez/'
RAQUEL_RING=dict(template='female',keep_alpha=['outfit'],lid_fit=True,eye_recess=0.15,hair_physics='ch43402',hair_body_blend=dict(y0=-180.0,y1=-160.0,dfull=3.0,dzero=12.0,smooth=100,post_smooth=60),
    weights='source',hide='geom',eye_straighten_deg=0.5,work='/home/claude/ext/rq',emd='00050602',
    base=RQ_+'BaseModel/baseModel.mcd',attire_model=RQ_+'927_Default_Attire/927_Attire.mcd',
    tex_base=RQ_+'BaseModel/Textures',tex_attire=RQ_+'927_Default_Attire/Textures',hpl=RQ_+'927_Default_Attire/927_Attire.mcd',
    cover=['M_Outfit','M_Shoes','M_R_Wrist'],hair={0x2715:('M_Hair','hair')},tint=(38,26,20),
    attire={(0x5601,0):('atlas',[('M_L_A_Acce','l_a_acce')]),(0x5601,2):('mesh','M_R_Wrist','r_wrist'),
            (0x5601,4):('mesh','M_Shoes','shoes'),(0x5602,0):('mesh','M_Outfit','outfit')})
RAQUEL_ENT=dict(RAQUEL_RING,work='/home/claude/ext/rqe',emd='00050604',
    attire={**RAQUEL_RING['attire'],(0x5601,0):('atlas',[('M_L_A_Acce','l_a_acce'),('M_Glasses','glasses')])})
TP_='/home/claude/pairs/TP/1216_Tatum_Paxley/'
TATUM_RING=dict(template='female',sheer={'socks':((70,40,30),45,0.6)},lid_fit=True,eye_recess=0.05,hair_physics='ch43402',hair_body_blend=dict(y0=-180.0,y1=-160.0,dfull=6.0,dzero=18.0,smooth=100,post_smooth=60),
    weights='source',hide='geom',donor_weights=[],eye_straighten_deg=0.5,work='/home/claude/ext/tp',emd='00050602',
    base=TP_+'BaseModel/baseModel.mcd',attire_model=TP_+'1216_Default_Attire/1216_Attire.mcd',
    tex_base=TP_+'BaseModel/Textures',tex_attire=TP_+'1216_Default_Attire/Textures',hpl=TP_+'1216_Default_Attire/1216_Attire.mcd',
    cover=['M_Brassiere','M_Underwear','M_Socks','M_Shoes','M_L_Kneepad','M_R_Kneepad'],hair={0x2715:('M_Hair','hair')},tint=(25,22,22),
    attire={(0x5601,0):('atlas',[('M_U_Acce','u_acce')]),(0x5601,1):('mesh','M_Socks','socks'),
            (0x5601,3):('mesh','M_Underwear','underwear'),(0x5601,4):('mesh','M_Shoes','shoes'),
            (0x5602,0):('mesh','M_Brassiere','brassiere'),(0x5602,1):('mesh','M_L_Kneepad','l_kneepad'),(0x5602,2):('mesh','M_R_Kneepad','r_kneepad')})
TATUM_ENT=dict(TATUM_RING,work='/home/claude/ext/tpe',emd='00050604',hair_body_blend=dict(TATUM_RING['hair_body_blend'],a_max=0.7),cover=TATUM_RING['cover']+['M_Jacket'],hair={0x2715:('M_Hair_Entrance','hair')},
    attire={**TATUM_RING['attire'],(0x5601,2):('mesh','M_Jacket','jacket')})
RAQUEL_DIAG=dict(RAQUEL_ENT,work='/home/claude/ext/rqd',diag_paint=[((0,32,-112,-55),(0,255,0))])
TATUM_DIAG=dict(TATUM_ENT,work='/home/claude/ext/tpd',diag_paint=[((2,20,-82,-45),(0,255,0))],sheer={'socks':((70,40,30),45,1.0)},diag_sheer_rgb=(0,255,255))
CONFIGS={'briscoe':BRISCOE,'flash':FLASH,'toni':TONI,'keith':KEITH,'keith_ring':KEITH_RING,'keith_entrance':KEITH_ENT,'jevon':JEVON,'jevon_ring':JEVON_RING,'jevon_entrance':dict(JEVON,emd='00050604'),'psycho_clown':PSYCHO,'psycho_clown_entrance':dict(PSYCHO,emd='00050604'),'psycho_clown_ring':PSYCHO_RING,'rhea':RHEA,'rhea_ring':RHEA_RING,'rhea_entrance':RHEA_ENT,'raquel_ring':RAQUEL_RING,'raquel_entrance':RAQUEL_ENT,'tatum_ring':TATUM_RING,'tatum_entrance':TATUM_ENT,'raquel_diag':RAQUEL_DIAG,'tatum_diag':TATUM_DIAG}

if __name__=='__main__':
    print(build(CONFIGS[sys.argv[1]],sys.argv[2]))

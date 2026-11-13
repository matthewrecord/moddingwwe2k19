"""Regenerate attire objects of a port JBOY from the 2K24 MDL meshes with our rules (first pipeline test)."""
import sys,glob,collections,numpy as np;sys.path.insert(0,'/home/claude/scripts')
import jboy,jbuild,mdlfmt
from scipy.spatial import cKDTree
from tmpl import cloud,stock
def load_mdl_meshes(pattern):
    out={}
    for f in glob.glob(pattern,recursive=True):
        m=mdlfmt.MDL(f); L=m.lods()[0]
        for me,t in zip(m.meshes,L): out[(f.split('/')[-1],me['name'])]=(me['streams'],t.reshape(-1,3))
    return out
def source_meshes(o,meshes,tol=0.01):
    keys=list(meshes); P=np.concatenate([meshes[k][0]['POSITION'] for k in keys]); lab=np.concatenate([[i]*len(meshes[k][0]['POSITION']) for i,k in enumerate(keys)])
    d,i=cKDTree(P).query(o['pos']); c=collections.Counter(lab[i[d<tol]])
    return [keys[x] for x,n in c.items() if n>=0.05*len(o['pos'])]
def build_object(srcs,meshes,donor,palette_slot,hair=False,white_col=(255,255,255,255)):
    Ps,Ns,Ws=donor; t=cKDTree(Ps)
    pos=[];nrm=[];uv=[];tris=[];off=0
    for k in srcs:
        S,T=meshes[k]; pos.append(S['POSITION']); n=S['NORMAL'][:,:3].astype(np.float32)/127; n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-6)
        nrm.append(-n); uv.append(S['TEXCOORD']); tris.append(T+off); off+=len(S['POSITION'])
    pos=np.concatenate(pos).astype('f4'); nrm=np.concatenate(nrm); uv=np.concatenate(uv); tris=np.concatenate(tris)
    vc=len(pos); d,si=t.query(pos)
    slots=np.zeros((vc,7),int); w=np.zeros((vc,7),'f4')
    for v in range(vc):
        acc=collections.defaultdict(float)
        for nm,ww in zip(Ns[si[v]],Ws[si[v]]):
            if ww>0 and nm in palette_slot: acc[nm]+=float(ww)
        it=sorted(acc.items(),key=lambda x:-x[1])[:7]; s=sum(x for _,x in it) or 1
        it=sorted(it,key=lambda x:palette_slot[x[0]])          # his order: ascending palette slot
        slots[v,:]=0xFFFF                                       # his empty-slot marker
        for q,(nm,ww) in enumerate(it): slots[v,q]=palette_slot[nm]; w[v,q]=ww/s
    col=np.tile(np.array(white_col if hair else (245,0,0,255),'u1'),(vc,1))
    tan=np.zeros((vc,3),'f4')
    if hair: tan[0::2]=(0,1,0); tan[1::2]=(1,0,1)
    return dict(pos=pos,nrm=nrm,col=col,uv=uv,tan=tan,slots=slots,w=w,tris=tris,nn=d)

import sys,glob,pickle,zlib,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from regen_full import *
import oodl,facexfer as fx,facefit,jcheck,hidetable
from scipy.spatial import cKDTree
def build(W,outpath):
    U='/mnt/user-data/uploads/WWE 2K19 - modded/pac/ch/'
    s=jboy.JBOY(oodl.blocks(open(U+'ch68702.pac','rb').read())[0][1]); so=s.objs[0]; SD=jboy.morphs(s,so); ST=jboy.strip_to_tris(s.indices(so)[1])
    M=__import__('mdlfmt').MDL(glob.glob('/home/claude/pairs/Kyle*ORIG*/*/BaseModel/baseModel.mdl')[0]); k=[m['name'] for m in M.meshes].index('M_Head')
    St=M.meshes[k]['streams']; PT=St['POSITION']; TT=M.lods()[0][k].reshape(-1,3)
    TI,BC,dist=fx.closest_bary(W,PT,TT); tri=TT[TI]; uv=np.einsum('pk,pkc->pc',BC,St['TEXCOORD'][tri]).astype('f4')
    N=St['NORMAL'][:,:3].astype('f4')/127; N/=np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-6); nrm=-np.einsum('pk,pkc->pc',BC,N[tri]); nrm/=np.linalg.norm(nrm,axis=1,keepdims=True)
    out=pickle.load(open('/home/claude/ext/fletcher_full_jboys_v2.pkl','rb')); j=jboy.JBOY(out[0]); m=jbuild.Model(j)
    bnp=[x['name'] for x in j.bones]; slot={bnp[b]:i for i,b in enumerate(j.palette)}; bns=[x['name'] for x in s.bones]
    sk=jcheck.raw_skin(s,so); raw=s.fix_order(sk['i'].astype(int),sk['w']); vc=len(W)
    sl=np.full((vc,7),0xFFFF); w=np.zeros((vc,7),'f4')
    for v in range(vc):
        q=0
        for i,ww in zip(raw[v],sk['w'][v]):
            if ww<=0 or i>=len(s.palette): continue
            nm=bns[s.palette[i]]
            if nm in slot: sl[v,q]=slot[nm]; w[v,q]=ww; q+=1
        w[v]/=max(w[v].sum(),1e-6)
    MD=np.transpose(SD,(1,0,2))
    T2,uv2,(P2,N2,SI,SW,MD2),nadd=facefit.split_uv_seam(ST,uv,[W,nrm,sl,w,MD]); vc=len(P2)
    jbuild.set_object(m,0,P2,N2,np.tile(np.array((245,0,0,255),'u1'),(vc,1)),uv2.astype('f4'),np.zeros((vc,3),'f4'),SI,SW,jbuild.tris_to_strip(T2))
    for n in range(1,120):
        V=np.zeros(vc,dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]); V['p']=MD2[:,n-1,:]; m.data[m.chunk(0,f'vset{n}')]=bytearray(V.tobytes())
    out[0]=m.build()
    hdr,blocks=epkwrite.raw_blocks('/home/claude/pairs/Kyle Fletcher JKxBNB 2K24 PORT/ch50602.pac'); B={fid:zlib.decompress(b[16:]) for fid,b in blocks}
    # hide table regenerated for OUR body objects
    his=jboy.JBOY(B[0]); w_,pairs,tail=hidetable.parse(B[0xce]); hidden=set(); [hidden.update(range(s_,e+1)) for s_,e in pairs]
    ho=his.objs[1]; htri=[t for k_,t in hidetable.strip_tri_starts(his.indices(ho)[1]) if k_ in hidden]; hc=np.array([ho['pos'][list(t)].mean(0) for t in htri])
    our=jboy.JBOY(out[0]); oo=our.objs[1]; ost=hidetable.strip_tri_starts(our.indices(oo)[1]); OC=np.array([oo['pos'][list(t)].mean(0) for _,t in ost])
    d,i=cKDTree(OC).query(hc); dh,_=cKDTree(hc).query(OC); sel=set(i.tolist())|set(np.where(dh<0.6)[0].tolist())
    R=hidetable.to_ranges([ost[x][0] for x in sel]); n2=len(our.indices(our.objs[2])[1]); hide=hidetable.rebuild(B[0xce],R,(0,n2-3))
    J=dict(out); J[0xa]=open('/home/claude/ext/fletcher_texpack.bin','rb').read(); J[0xce]=hide
    pac=epkwrite.build_raw(hdr,[(fid,epkwrite.zblock(J[fid]) if fid in J else blk) for fid,blk in blocks]); open(outpath,'wb').write(pac)
    return len(pac),nadd

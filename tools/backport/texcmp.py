import sys,io,glob,numpy as np;sys.path.insert(0,'.');import texpack
from PIL import Image
def load_dds(b):
    return np.asarray(Image.open(io.BytesIO(b)).convert('RGBA')).astype(np.float32)
def port_tex(pack,name):
    b=open(pack,'rb').read(); T,_,_=texpack.parse(b); offs=[t['off'] for t in T]+[len(b)]
    for k,t in enumerate(T):
        if t['name']==name: return load_dds(b[t['off']:offs[k+1]])
def orig_tex(path): return load_dds(open(path,'rb').read())
def resize(a,shape):
    return np.asarray(Image.fromarray(a.astype(np.uint8)).resize((shape[1],shape[0]),Image.BILINEAR)).astype(np.float32)
if __name__=='__main__':
    pack,odir,mat=sys.argv[1],sys.argv[2],sys.argv[3]
    C=orig_tex(glob.glob(f'{odir}/{mat}_color.*')[0]); N=orig_tex(glob.glob(f'{odir}/{mat}_nrm.*')[0])
    for suf in ['','_mr','_n']:
        P=port_tex(pack,mat+suf)
        if P is None: print(mat+suf,'missing'); continue
        Cs=resize(C,P.shape); Ns=resize(N,P.shape)
        print(f'== port {mat+suf} {P.shape}; channel mean {P.reshape(-1,4).mean(0).round(1)} std {P.reshape(-1,4).std(0).round(1)}')
        src={'C.'+c:Cs[...,i] for i,c in enumerate('RGBA')}; src.update({'N.'+c:Ns[...,i] for i,c in enumerate('RGBA')})
        for i,c in enumerate('RGBA'):
            p=P[...,i].ravel()
            if p.std()<1: print(f'   {c}: constant {p.mean():.1f}'); continue
            best=sorted(((abs(np.corrcoef(p,v.ravel())[0,1]),k,np.corrcoef(p,v.ravel())[0,1],np.abs(p-v.ravel()).mean(),np.abs(p-(255-v.ravel())).mean()) for k,v in src.items() if v.std()>1),reverse=True)[:2]
            print(f'   {c}: '+'; '.join(f'{k} r={r:+.3f} |d|={d:.1f} |inv|={di:.1f}' for _,k,r,d,di in best))
    print('orig nrm channel mean',N.reshape(-1,4).mean(0).round(1),'std',N.reshape(-1,4).std(0).round(1))

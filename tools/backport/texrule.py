import sys,glob,numpy as np;sys.path.insert(0,'.');import texcmp
def rule(C,N):
    n=np.stack([255-N[...,0],255-N[...,1],np.full(N.shape[:2],255.),np.full(N.shape[:2],255.)],-1)
    mr=np.stack([N[...,3],N[...,2],255-N[...,2],np.full(N.shape[:2],255.)],-1)
    return {'':C,'_n':n,'_mr':mr}
def check(pack,cpath,npath,pname):
    C=texcmp.orig_tex(cpath); N=texcmp.orig_tex(npath); R=rule(C,N); out={}
    for suf,pred in R.items():
        P=texcmp.port_tex(pack,pname+suf)
        if P is None: out[suf]='missing'; continue
        Q=texcmp.resize(pred,P.shape); e=np.abs(P-Q)[...,:3].mean(); out[suf]=f'{e:.1f} ({P.shape[1]}x{P.shape[0]} from {N.shape[1]}x{N.shape[0]})'
    return out
if __name__=='__main__':
    pack=sys.argv[1]; od=sys.argv[2]
    for o,p in [x.split(':') for x in sys.argv[3:]]:
        c=glob.glob(f'{od}/**/{o}_color.*',recursive=True)[0]; n=glob.glob(f'{od}/**/{o}_nrm.*',recursive=True)[0]
        print(f'{o:12s} -> {p:12s}', check(pack,c,n,p))

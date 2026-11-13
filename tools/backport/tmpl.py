import sys,collections,numpy as np;sys.path.insert(0,'/home/claude/scripts')
import jboy,oodl,epk
from scipy.spatial import cKDTree
from bonemap import wdict,score
def cloud(j,shaders=('yCS_skin',)):
    bn=np.array([x['name'] for x in j.bones]+['?'])
    P=[];N=[];W=[]
    for o in j.objs:
        if o['shader'] not in shaders or o['bi'] is None: continue
        k=o['bi'].shape[1]; bi=np.minimum(o['bi'],len(bn)-1)
        pad=7-k
        P.append(o['pos']); N.append(np.pad(bn[bi],((0,0),(0,pad)),constant_values='?')); W.append(np.pad(o['bw'],((0,0),(0,pad))))
    return np.concatenate(P),np.concatenate(N),np.concatenate(W)
def stock(path):
    b=open(path,'rb').read(); return jboy.JBOY(oodl.blocks(b)[0][1])
def portj(path): return jboy.JBOY(epk.blocks(path)[0])
def compare(src,dst):
    Ps,Ns,Ws=src; Pd,Nd,Wd=dst; t=cKDTree(Ps); d,i=t.query(Pd)
    pairs=[(wdict(Ns[a],Ws[a]),wdict(Nd[k],Wd[k]),0,0) for k,a in enumerate(i)]
    return score(pairs,lambda x:x),np.median(d)
if __name__=='__main__':
    U='/mnt/user-data/uploads/WWE 2K19 - modded/pac/ch/'
    S={n:cloud(stock(U+n+'.pac')) for n in ['ch38402','ch73304','ch14704','ch13604','ch10002']}
    for pn,pp in [('Gabe','/home/claude/pairs/Gabe Kidd MrH 2K24 PORT/ch50602.pac'),('Fletcher','/home/claude/pairs/Kyle Fletcher JKxBNB 2K24 PORT/ch50602.pac'),('OKhan','/home/claude/pairs/Great O Khan 2K23 PORT/ch50602.pac'),('Willow',"/home/claude/pairs/Willow Nightingale AEW Dynasty '24 DB 2K24 PORT/ch50602.pac")]:
        D=cloud(portj(pp))
        for sn,s in S.items():
            (m,med,dom),dist=compare(s,D)
            print(f'{pn:8s} <- {sn}: meanL1 {m:.3f} median {med:.3f} dominant {100*dom:.1f}%  NN dist {dist:.2f}cm  stockverts {len(s[0])}')

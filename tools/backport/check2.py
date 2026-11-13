import sys,collections;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)));from pairs import *;from bonemap import wdict,score
import numpy as np
def portcloud(n):
    Q=[q for q in port(n) if q['nb']==max(x['nb'] for x in port(n))]
    def pad(a,v):
        return np.concatenate([a,np.full((len(a),7-a.shape[1]),v,dtype=a.dtype)],1) if a.shape[1]<7 else a
    P=np.concatenate([q['pos'] for q in Q]); N=np.concatenate([pad(q['bnames'],'?') for q in Q]); W=np.concatenate([pad(q['bw'],0) for q in Q]); S=np.concatenate([[q['shader']]*len(q['pos']) for q in Q])
    return P,N,W,S
C={n:portcloud(n) for n in PAIRS}
for n in ['Gabe','Fletcher']:
    P,N,W,S=C[n]; O=orig(n); on=set(np.concatenate([o['bnames'].ravel() for o in O]))
    m=W>0; tot=W[m].sum(); extra=sum(W[i,k] for i,k in zip(*np.where(m)) if N[i,k] not in on)
    print(n,'share of porter weight mass on bones the original never uses: %.1f%%'%(100*extra/tot))
    c=collections.Counter(); 
    for i,k in zip(*np.where(m)):
        if N[i,k] not in on: c[N[i,k][:4]]+=W[i,k]
    print('   by prefix',c.most_common(6))
# template test: predict each port's skin-shader verts from the OTHER characters' port weights by nearest neighbour
print('template test (skin shader only): donor = other port, nearest vertex weights')
for a in PAIRS:
    Pa,Na,Wa,Sa=C[a]; ia=np.where(Sa=='yCS_skin')[0]
    for b in PAIRS:
        if a==b: continue
        Pb,Nb,Wb,Sb=C[b]; ib=np.where(Sb=='yCS_skin')[0]; t=cKDTree(Pb[ib]); d,j=t.query(Pa[ia])
        pairs=[(wdict(Nb[ib[jj]],Wb[ib[jj]]),wdict(Na[ii],Wa[ii]),0,0) for ii,jj in zip(ia,j)]
        e=score(pairs,lambda x:x)
        print('  %-8s from %-8s meanL1 %.3f median %.3f dominant %.1f%%  (median NN dist %.2f cm)'%(a,b,e[0],e[1],100*e[2],np.median(d)))

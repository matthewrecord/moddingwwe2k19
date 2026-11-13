"""Lid closure check: for the strongest eye-closing morphs, the remaining lid gap at the eye centre as % of the open gap,
donor vs ours. Usage: lidcheck.py PAC DONOR"""
import sys,zlib,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import jboy,oodl,epkwrite,build_port as bp
U='/mnt/user-data/uploads/WWE 2K19 - modded/pac/ch/'
def gaps(J):
    o=J.objs[0]; P=o['pos'].astype(float); T=jboy.strip_to_tris(J.indices(o)[1]); M=np.asarray(jboy.morphs(J,o)); out={}
    for side,l in zip('LR',bp.eye_loops(P,T)):
        Q=P[l]; x0=Q[:,0].mean(); hw=np.abs(Q[:,0]-x0).max(); c=np.abs(Q[:,0]-x0)<0.3*hw; ymid=Q[:,1].mean()
        up=np.array(l)[c&(Q[:,1]<ymid)]; lo=np.array(l)[c&(Q[:,1]>=ymid)]
        g=lambda X:(X[lo,1].mean()-X[up,1].mean())
        out[side]=(g(P),[g(P+M[n]) for n in range(M.shape[0])])
    return out
def run(pac,donor):
    s=jboy.JBOY(oodl.blocks(open(U+donor+'.pac','rb').read())[0][1]); j=jboy.JBOY(zlib.decompress(dict(epkwrite.raw_blocks(pac)[1])[0][16:]))
    D=gaps(s); O=gaps(j); rows=[]
    for side in 'LR':
        g0,gm=D[side]; idx=np.argsort(np.array(gm)/g0)[:4]
        for n in idx: rows.append((side,n+1,round(100*gm[n]/g0),round(100*O[side][1][n]/O[side][0])))
    return rows
if __name__=='__main__':
    for side,n,d,o in run(sys.argv[1],sys.argv[2]): print('%s morph %3d  lid gap remaining: donor %4d%%  ours %4d%%'%(side,n,d,o))

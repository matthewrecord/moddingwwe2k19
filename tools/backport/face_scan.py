import sys,os,json,time,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import jboy,oodl
B=os.environ['FB']; F={n:np.load(f'{B}/face_{n}.npz') for n in ('fletcher','gabe','willow')}
out=sys.argv[1]; t=time.time()
done=set(json.loads(l)['f'] for l in open(out)) if os.path.exists(out) else set()
with open(out,'a') as fo:
    for f in [l.strip() for l in open('list2.txt')]:
        if f in done: continue
        if time.time()-t>160: break
        r={}
        try:
            j=jboy.JBOY(oodl.first_jboy(open(f,'rb').read())); o=j.objs[0]; SD=jboy.morphs(j,o)
            if SD is not None and SD.shape[0]==119:
                S=o['pos']
                for n,z in F.items():
                    P=z['pos']; D=z['d']
                    dd=((P[:,None,:]-S[None,:,:])**2).sum(2); ii=dd.argmin(1); nn=np.sqrt(dd[np.arange(len(P)),ii])
                    mag=np.linalg.norm(D,axis=2); err=np.linalg.norm(SD[:,ii,:]-D,axis=2); m=mag>0.05
                    r[n]=[round(float(err[m].mean()/mag[m].mean()),3),round(float(np.median(nn)),2)]
        except Exception as e: r={'err':repr(e)[:80]}
        fo.write(json.dumps(dict(f=f,r=r))+'\n')

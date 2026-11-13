"""Eye/brow-region morph comparison: donor stock head vs ours, for the morphs that move the eye region most.
Usage: eyemorphs.py PAC OUT.png DONOR(ch68702|ch75602)"""
import sys,zlib,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import jboy,oodl,epkwrite,render
from PIL import Image
U='/mnt/user-data/uploads/WWE 2K19 - modded/pac/ch/'
def scene(J,extra,n):
    tr=[]
    for JJ,k,col in [(J,0,(.85,.68,.58))]+extra:
        o=JJ.objs[k]; P=o['pos']+(np.asarray(jboy.morphs(JJ,o))[n-1] if n and o['f'][25]>1 else 0); T=jboy.strip_to_tris(JJ.indices(o)[1])
        tr+=[(P[list(t)],np.array(col)) for t in T]
    return tr
def grid(pac,out,donor,top=None):
    s=jboy.JBOY(oodl.blocks(open(U+donor+'.pac','rb').read())[0][1]); B={f:zlib.decompress(b[16:]) for f,b in epkwrite.raw_blocks(pac)[1]}; j=jboy.JBOY(B[0])
    A=np.asarray(jboy.morphs(s,s.objs[0])); Pa=s.objs[0]['pos']; ey=(np.abs(np.abs(Pa[:,0])-3.6)<3)&(Pa[:,1]>-186)&(Pa[:,1]<-178)&(Pa[:,2]<-8)
    top=top or (np.argsort(-np.linalg.norm(A[:,ey],axis=2).max(1))[:12]+1).tolist()
    se=[(s,k,(1,1,1)) for k,o in enumerate(s.objs) if o['shader']=='yCS_eye']
    oe=[(j,k,(1,1,1)) for k,o in enumerate(j.objs) if o['shader']=='yCS_eye']
    if 0x4e22 in B and '--lashes' in sys.argv: oe.append((jboy.JBOY(B[0x4e22]),0,(0,0,0)))
    rows=[]
    for n in top:
        ims=[]
        for nm,J,ex in (('donor',s,se),('ours',j,oe)):
            f='/tmp/em_%s.png'%nm; render.render(scene(J,ex,n),'front',f,size=(3.2,1.6),xlim=(-7,7),ylim=(177,184),title='%d %s'%(n,nm)); ims.append(Image.open(f))
        r=Image.new('RGB',(ims[0].width*2,ims[0].height)); r.paste(ims[0],(0,0)); r.paste(ims[1],(ims[0].width,0)); rows.append(r)
    W,H=rows[0].width,rows[0].height; g=Image.new('RGB',(W*2,H*6),'white')
    for i,r in enumerate(rows): g.paste(r,((i%2)*W,(i//2)*H))
    g.save(out); return top
if __name__=='__main__': print(grid(sys.argv[1],sys.argv[2],sys.argv[3]))

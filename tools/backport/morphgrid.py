"""Andrade stock vs built head for the 12 morphs that move the mouth most (shaded geometry). Usage: morphgrid.py PAC OUT"""
import sys,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)));import jboy,oodl,pose,render
from PIL import Image
U='/mnt/user-data/uploads/WWE 2K19 - modded/pac/ch/'
def grid(pac,out,top=None):
    s=jboy.JBOY(oodl.blocks(open(U+'ch68702.pac','rb').read())[0][1]); j=pose.load(pac)
    A=np.asarray(jboy.morphs(s,s.objs[0])); Pa=s.objs[0]['pos']; mouth=(np.abs(Pa[:,0])<5)&(np.abs(Pa[:,1]+175)<4)&(Pa[:,2]<-8)
    if top is None: top=(np.argsort(-np.linalg.norm(A[:,mouth],axis=2).max(1))[:12]+1).tolist()
    Ta=jboy.strip_to_tris(s.indices(s.objs[0])[1]); Tm=jboy.strip_to_tris(j.indices(j.objs[0])[1]); rows=[]
    for n in top:
        ims=[]
        for nm,J,T in (('andrade',s,Ta),('ours',j,Tm)):
            P=J.objs[0]['pos']+np.asarray(jboy.morphs(J,J.objs[0]))[n-1]; f='/tmp/g_%s.png'%nm
            render.render([(P[list(t)],np.array([.85,.68,.58])) for t in T],'front',f,size=(2.4,2.4),xlim=(-7,7),ylim=(166,181),title='%d %s'%(n,nm)); ims.append(Image.open(f))
        r=Image.new('RGB',(ims[0].width*2,ims[0].height)); r.paste(ims[0],(0,0)); r.paste(ims[1],(ims[0].width,0)); rows.append(r)
    W=rows[0].width; H=rows[0].height; g=Image.new('RGB',(W*3,H*((len(rows)+2)//3)),'white')
    for i,r in enumerate(rows): g.paste(r,((i%3)*W,(i//3)*H))
    g.save(out)
if __name__=='__main__': grid(sys.argv[1],sys.argv[2])

"""Eye stress test: aim both eyes together (as the game does) and check how they behave.
Usage: eyegaze.py PAC OUT.png [eyeL eyeR]   (eye object indices default from the male/female layout)
Per gaze: textured render of the eye region, and metrics:
  drift  = how far the eyeball centre moves when it turns (cm; should be ~0: pivot on the eyeball centre)
  verg   = angle between the two eyes' lines of sight (deg; ~0 = parallel, >0 crossed, <0 wall-eyed)
  poke   = eyeball vertices pushed in front of the face surface, beyond the rest pose (should be ~0)"""
import sys,zlib,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import jboy,epkwrite,pose,render,preview,build_port as bp
from scipy.spatial import cKDTree
from PIL import Image
GAZES=[('rest',None,0),('left 25',[0,1,0],25),('right 25',[0,1,0],-25),('up 15',[1,0,0],15),('down 15',[1,0,0],-15)]
def run(pac,out):
    B={f:zlib.decompress(b[16:]) for f,b in epkwrite.raw_blocks(pac)[1]}; j=jboy.JBOY(B[0])
    eyes=[k for k,o in enumerate(j.objs) if o['shader']=='yCS_eye']; side={('L' if j.objs[k]['pos'][:,0].mean()>0 else 'R'):k for k in eyes}
    Wb=bp.bone_world(j); H=j.objs[0]; th=cKDTree(H['pos'])
    base=[x for x in preview.tris(pac) if x[0][:,1].min()<-170 and x[0][:,2].min()<-7]
    eyeset={tuple(np.round(x[0].ravel(),4)) for k in eyes for x in []}
    rows=[]; ims=[]
    for name,ax,deg in GAZES:
        P={}; ctr={}; gaze={}
        for s,k in side.items():
            o=j.objs[k]; p=pose.pose(j,k,bones={'J_Eye_'+s:(ax,deg)}) if ax else o['pos'].astype(float)
            P[k]=p; c0=bp.sphere_ctr(o['pos'].astype(float)); c=bp.sphere_ctr(p); ctr[s]=np.linalg.norm(c-c0)
            front=o['pos'][:,2].argmin(); gaze[s]=(p[front]-c)/np.linalg.norm(p[front]-c)
        verg=np.degrees(np.arctan2(gaze['L'][0],-gaze['L'][2])-np.arctan2(gaze['R'][0],-gaze['R'][2]))
        poke=0
        for k in eyes:
            d,i=th.query(P[k]); n=-H['nrm'][i]; poke+=int((((P[k]-H['pos'][i])*n).sum(1)>0.15).sum())
        if name=='rest': poke0=poke
        rows.append((name,round(max(ctr.values()),2),round(float(-verg),1),poke-poke0))
        tr=[x for x in base]
        for k in eyes:
            o=j.objs[k]; img=preview.textures(B).get('eye'); T=jboy.strip_to_tris(j.indices(o)[1])
            for t in T:
                u,v=o['uv'][list(t)].mean(0); hh,ww=img.shape[:2]; tr.append((P[k][list(t)]-np.array([0,0,0.01]),img[min(hh-1,int(v*hh)),min(ww-1,int(u*ww)),:3]/255))
        f='/tmp/eg_%d.png'%len(ims); render.render(tr,'front',f,size=(3.2,1.6),xlim=(-7,7),ylim=(176,183),title=f'{name}  drift {rows[-1][1]}  verg {rows[-1][2]}°'); ims.append(Image.open(f))
    W,Hh=ims[0].width,ims[0].height; g=Image.new('RGB',(W,Hh*len(ims)),'white')
    for i,im in enumerate(ims): g.paste(im,(0,i*Hh))
    g.save(out); return rows
if __name__=='__main__':
    for r in run(sys.argv[1],sys.argv[2]): print('%-9s drift %.2f cm  vergence %+.1f deg  poke %d'%r)

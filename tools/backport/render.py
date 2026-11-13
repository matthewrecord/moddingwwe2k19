"""Offline preview: render every object of a character pac (rest pose), with the M_Body hide table applied.
Painter's algorithm with flat Lambert shading; background magenta so holes stand out."""
import sys,zlib,struct,numpy as np;sys.path.insert(0,'/home/claude/scripts')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import jboy,epkwrite,hidetable
COL={'yCS_skin':(0.86,0.66,0.55),'yCS_hair':(0.95,0.85,0.4),'yCS_gear':(0.3,0.3,0.35),'yCS_trans':(0.35,0.2,0.2),'yCS_eye':(1,1,1),'yCS_eyeOv':None}
def load(pac):
    hdr,blocks=epkwrite.raw_blocks(pac); B={fid:zlib.decompress(b[16:]) for fid,b in blocks}; tris=[]
    hide={}
    if 0xce in B:
        w,pairs,tail=hidetable.parse(B[0xce]); h1=set();[h1.update(range(s,e+1)) for s,e in pairs]; hide[1]=h1; hide[2]=set(range(tail[-2],tail[-1]+1))
    for fid,d in B.items():
        if d[:4]!=b'JBOY': continue
        j=jboy.JBOY(d)
        for k,o in enumerate(j.objs):
            c=COL.get(o['shader'],(0.6,0.6,0.6))
            if c is None: continue
            ix=j.indices(o)[1]; hs=hide.get(k,set()) if fid==0 else set()
            for st,t in hidetable.strip_tri_starts(ix):
                if st in hs: continue
                tris.append((o['pos'][list(t)],c))
    return tris
def render(tris,view,out,size=(7,10),xlim=None,ylim=None,title=''):
    # view: 'front' looks along +z (game front is -z), 'back', 'left', 'right'
    R={'front':np.array([[1,0,0],[0,-1,0],[0,0,1]]),'back':np.array([[-1,0,0],[0,-1,0],[0,0,-1]]),
       'left':np.array([[0,0,1],[0,-1,0],[-1,0,0]]),'right':np.array([[0,0,-1],[0,-1,0],[1,0,0]])}[view]
    P=np.array([t for t,_ in tris])@R.T; C=np.array([c for _,c in tris])
    n=np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0]); nl=np.linalg.norm(n,axis=1); n/=np.maximum(nl,1e-9)[:,None]
    shade=0.35+0.65*np.abs(n[:,2])
    order=np.argsort(P[:,:,2].mean(1))[::-1]   # far first (camera looks toward -z after rotation)
    fig=plt.figure(figsize=size,dpi=110); ax=fig.add_axes([0,0,1,1]); ax.set_facecolor((1,0,1))
    pc=PolyCollection(P[order][:,:,:2],facecolors=C[order]*shade[order][:,None],edgecolors='none',antialiaseds=False)
    ax.add_collection(pc); ax.set_aspect('equal')
    if xlim: ax.set_xlim(*xlim)
    else: ax.set_xlim(P[:,:,0].min()-5,P[:,:,0].max()+5)
    if ylim: ax.set_ylim(*ylim)
    else: ax.set_ylim(P[:,:,1].min()-5,P[:,:,1].max()+5)
    ax.text(0.02,0.98,title,transform=ax.transAxes,va='top',color='k'); ax.axis('off'); fig.savefig(out); plt.close(fig)

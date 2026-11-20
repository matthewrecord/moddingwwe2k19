"""Per-pixel game-like render of a built pac, to reproduce in-game artefacts offline.
Unlike preview.py (one colour per triangle), this rasterises every triangle with interpolated UVs, samples the pac's
own textures per pixel, applies the hide table, and alpha-tests (alpha<128 discarded) on the shaders that can cut out
(yCS_trans, yCS_hair; gear is opaque unless --gear-alpha). Holes show the magenta background.
Usage: gamerender.py PAC OUT.png [--view front|back|left|right|q3] [--box x0 x1 y0 y1] [--px 900] [--gear-alpha] [--pose NAME]"""
import os,sys,io,zlib,struct,argparse,numpy as np;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import jboy,epkwrite,hidetable,texconv,pose
from PIL import Image
CULL=True
VIEWS={'front':(0,0),'back':(180,0),'left':(90,0),'right':(-90,0),'q3':(35,0),'q3r':(-35,0),'q3b':(145,0)}
def load(pac):
    hdr,bl=epkwrite.raw_blocks(pac); B={f:(zlib.decompress(b[16:]) if b[:4]==b'ZLIB' else b) for f,b in bl}
    hd,E=texconv.read_pack(B[0xa]); TX={}
    for n,d in E:
        try: TX[n]=np.asarray(Image.open(io.BytesIO(d)).convert('RGBA'))
        except Exception: pass
    w=struct.unpack('<%dI'%(len(B[0xce])//4),B[0xce]); i=22; hide={}
    for _ in range(w[21]):
        n=w[i+7]; hs=set()
        for k in range(n): hs.update(range(w[i+8+2*k],w[i+9+2*k]+1))
        hide[w[i+2]+1]=hs; i+=8+2*n
    return B,TX,hide
def gather(B,TX,hide,rots=None,gear_alpha=False,trans_opaque=False):
    out=[]
    for fid,d in B.items():
        if d[:4]!=b'JBOY': continue
        j=jboy.JBOY(d)
        for k,o in enumerate(j.objs):
            if o['shader'] in ('yCS_eyeOv','yDefault'): continue
            img=TX.get(jboy.obj_params(j,o).get('g_mDiffusePrm','tex:?').split(':')[1])
            P=pose.pose_fk(j,k,rots) if rots else o['pos'].astype(float)
            T=np.array([t for st,t in hidetable.strip_tri_starts(j.indices(o)[1]) if not (fid==0 and st in hide.get(k,()))],int)
            if len(T)==0: continue
            cut=o['shader']=='yCS_hair' or (o['shader']=='yCS_trans' and not trans_opaque) or (gear_alpha and o['shader']=='yCS_gear')
            Nn=o['nrm'][:,:3].astype(float) if 'nrm' in o else None
            if Nn is not None and rots: Nn=pose.pose_fk(j,k,rots,normals=True) if 'normals' in pose.pose_fk.__code__.co_varnames else Nn
            out.append((P,o['uv'][:,:2].astype(float),T,img,cut,Nn))
    return out
def rot(view):
    a,e=np.radians(VIEWS[view][0]),np.radians(VIEWS[view][1])
    Ry=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]]); return Ry
def render(objs,view,box,px,ids=None):
    R=rot(view); x0,x1,y0,y1=box; W=px; H=int(px*(y1-y0)/(x1-x0))
    img=np.zeros((H,W,3)); img[:]=(1,0,1); Z=np.full((H,W),np.inf)
    if ids is not None: ids.resize((H,W,2),refcheck=False); ids[:]=-1
    for oi,(P,UV,T,tex,cut,Nn) in enumerate(objs):
        Q=P@R.T; X=(Q[:,0]-x0)/(x1-x0)*W; Y=(Q[:,1]-y0)/(y1-y0)*H; Zc=Q[:,2]   # +z = away from camera (front faces -z)
        Nr=-(Nn@R.T) if Nn is not None else None   # 2K19 stores normals negated (stock bodies too)
        for ti,t in enumerate(T):
            if CULL and Nr is not None and Nr[t,2].mean()>0.05: continue   # back-facing (normal points away from the camera): the game culls it
            xs,ys=X[t],Y[t]
            mnx,mxx=int(max(0,np.floor(xs.min()))),int(min(W-1,np.ceil(xs.max()))); mny,mxy=int(max(0,np.floor(ys.min()))),int(min(H-1,np.ceil(ys.max())))
            if mnx>mxx or mny>mxy: continue
            gx,gy=np.meshgrid(np.arange(mnx,mxx+1)+.5,np.arange(mny,mxy+1)+.5)
            d=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
            if abs(d)<1e-9: continue
            l0=((ys[1]-ys[2])*(gx-xs[2])+(xs[2]-xs[1])*(gy-ys[2]))/d; l1=((ys[2]-ys[0])*(gx-xs[2])+(xs[0]-xs[2])*(gy-ys[2]))/d; l2=1-l0-l1
            m=(l0>=0)&(l1>=0)&(l2>=0)
            if not m.any(): continue
            z=l0*Zc[t[0]]+l1*Zc[t[1]]+l2*Zc[t[2]]; yy,xx=np.where(m); zz=z[m]; zb=Z[mny+yy,mnx+xx]; m2=zz<zb
            if not m2.any(): continue
            yy,xx,zz=yy[m2],xx[m2],zz[m2]; a0,a1,a2=l0[m][m2],l1[m][m2],l2[m][m2]
            if tex is None: col=np.tile([.5,.5,.5],(len(yy),1)); keep=np.ones(len(yy),bool)
            else:
                uv=a0[:,None]*UV[t[0]]+a1[:,None]*UV[t[1]]+a2[:,None]*UV[t[2]]; h,w=tex.shape[:2]
                s=tex[np.clip((uv[:,1]%1)*h,0,h-1).astype(int),np.clip((uv[:,0]%1)*w,0,w-1).astype(int)]
                keep=(s[:,3]>=128) if cut else np.ones(len(yy),bool); col=s[:,:3]/255
            yy,xx,zz,col=yy[keep],xx[keep],zz[keep],col[keep]
            Z[mny+yy,mnx+xx]=zz; img[mny+yy,mnx+xx]=col
            if ids is not None: ids[mny+yy,mnx+xx]=(oi,ti)
    return (img*255).astype('u1')
POSES={'rest':None,'arms down':{'J_Shoulder_L':([0,0,1],65),'J_Shoulder_R':([0,0,1],-65)},
       'walk':{'J_Shoulder_L':([0,0,1],65),'J_Shoulder_R':([0,0,1],-65),'J_Leg_L':([1,0,0],-25),'J_Leg_R':([1,0,0],15),'J_Knee_L':([1,0,0],30)},
       'bend over':{'J_Leg_L':([1,0,0],-80),'J_Leg_R':([1,0,0],-80),'J_Shoulder_L':([0,0,1],65),'J_Shoulder_R':([0,0,1],-65)}}
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('pac'); ap.add_argument('out'); ap.add_argument('--view',default='front'); ap.add_argument('--box',nargs=4,type=float,default=[-40,40,-190,0])
    ap.add_argument('--px',type=int,default=700); ap.add_argument('--gear-alpha',action='store_true'); ap.add_argument('--trans-opaque',action='store_true'); ap.add_argument('--pose',default='rest'); a=ap.parse_args()
    B,TX,hide=load(a.pac); Image.fromarray(render(gather(B,TX,hide,POSES[a.pose],a.gear_alpha,a.trans_opaque),a.view,a.box,a.px)).save(a.out); print('wrote',a.out)

"""Hair rig check: rotate every Hair_bNN chain root (and its segments) to fake a physics swing; render rest vs swung, front+side.
Usage: hairswing.py PAC OUT.png [deg]"""
import sys,zlib,re,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import epkwrite,jboy,pose,render,hidetable,build_port as bp
pac,out=sys.argv[1],sys.argv[2]; deg=float(sys.argv[3]) if len(sys.argv)>3 else 30
B={f:zlib.decompress(b[16:]) for f,b in epkwrite.raw_blocks(pac)[1]}
jm=jboy.JBOY(B[0]); jh=jboy.JBOY(B[0x2715])
head=[]
o=jm.objs[0]
for st,t in hidetable.strip_tri_starts(jm.indices(o)[1]): head.append((o['pos'][list(t)],(0.55,0.42,0.35)))
W=bp.bone_world(jh); names=[b['name'] for b in jh.bones if re.match(r'Hair_b\d+(_\d+)?$',b['name'])]
ims=[]
for lab,ang in (('rest',0),('swing',deg)):
    o=jh.objs[0]
    if ang:
        # rotate about each strand's ROOT for all its segments (approximates propagated chain rotation)
        S=pose.skin(jh,o); P=o['pos'].astype(float); out_=P.copy(); R=pose.rot((1,0,0),ang)
        for v,inf in enumerate(S):
            acc=np.zeros(3)
            for n,wt in inf:
                m=re.match(r'(Hair_b\d+)',n)
                if m: c=W[m.group(1)][1]; acc+=wt*(R@(P[v]-c)+c)
                else: acc+=wt*P[v]
            out_[v]=acc
        P=out_
    else: P=o['pos']
    T=[(P[list(t)],(0.12,0.1,0.09)) for st,t in hidetable.strip_tri_starts(jh.indices(o)[1])]
    for v in ('front','left'):
        fn='/tmp/hs_%s_%s.png'%(lab,v); render.render(head+T,v,fn,size=(4,4.5),xlim=(-25,25),ylim=(130,205),title='%s %s'%(lab,v)); ims.append(fn)
from PIL import Image
I=[Image.open(f) for f in ims]; c=Image.new('RGB',(I[0].width*4,I[0].height),'white')
for k,i in enumerate(I): c.paste(i,(k*i.width,0))
c.save(out)

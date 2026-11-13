"""Body stress test: pose the whole character (hierarchical) and render. Usage: bodypose.py PAC OUT.png"""
import sys,zlib,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import pose,jboy,epkwrite,render
from PIL import Image
POSES=[('arms down',{'J_Shoulder_L':([0,0,1],65),'J_Shoulder_R':([0,0,1],-65)},'front'),
       ('arms down, elbows bent',{'J_Shoulder_L':([0,0,1],65),'J_Shoulder_R':([0,0,1],-65),'J_Elbow_L':([0,1,0],90),'J_Elbow_R':([0,1,0],-90)},'front'),
       ('arms forward',{'J_Shoulder_L':([0,1,0],80),'J_Shoulder_R':([0,1,0],-80)},'left'),
       ('squat',{'J_Hip_L':([1,0,0],-70),'J_Hip_R':([1,0,0],-70),'J_Knee_L':([1,0,0],100),'J_Knee_R':([1,0,0],100)},'left')]
COLS={'yCS_skin':(.82,.62,.5),'yCS_gear':(.25,.25,.3),'yCS_trans':(.45,.25,.25),'yCS_hair':(.15,.1,.1)}
def run(pac,out,poses=POSES):
    B={f:zlib.decompress(b[16:]) for f,b in epkwrite.raw_blocks(pac)[1]}; J=[jboy.JBOY(d) for f,d in B.items() if d[:4]==b'JBOY']; ims=[]
    for name,rots,view in poses:
        tr=[]
        for j in J:
            for k,o in enumerate(j.objs):
                if o['shader'] in ('yCS_eye','yCS_eyeOv') or o['vc']<10: continue
                P=pose.pose_fk(j,k,rots); T=jboy.strip_to_tris(j.indices(o)[1]); c=np.array(COLS.get(o['shader'],(.6,.6,.6)))
                tr+=[(P[list(t)],c) for t in T]
        f='/tmp/bp_%d.png'%len(ims); render.render(tr,view,f,size=(4,5.5),title=name); ims.append(Image.open(f))
    W,H=ims[0].width,ims[0].height; g=Image.new('RGB',(W*len(ims),H),'white')
    for i,im in enumerate(ims): g.paste(im,(i*W,0))
    g.save(out)
if __name__=='__main__': run(sys.argv[1],sys.argv[2])

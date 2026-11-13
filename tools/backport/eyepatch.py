"""Straighten the eyes of an existing 2K19 pac (any port) and move J_Eye pivots to the eyeball centres.
Usage: eyepatch.py IN.pac OUT.pac"""
import sys,os,zlib,numpy as np;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import jboy,jbuild,epkwrite
from build_port import sphere_ctr,eye_forward,move_bones
hdr,blocks=epkwrite.raw_blocks(sys.argv[1]); B={f:(zlib.decompress(b[16:]) if b[:4]==b'ZLIB' else b) for f,b in blocks}
j=jboy.JBOY(B[0]); m=jbuild.Model(j); eyes=[k for k,o in enumerate(j.objs) if o['shader']=='yCS_eye']; tg={}
for k in eyes:
    o=j.objs[k]; ch=m.chunk(k,'vset0'); n=o['vc']; assert len(m.data[ch])>=n*28
    V=np.frombuffer(bytes(m.data[ch][:n*28]),dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]).copy()
    P=V['p'].astype(float); Nn=V['n'].astype(float); c=sphere_ctr(P); a0=None
    for it in range(8):
        f=eye_forward(P,c); a=np.arctan2(f[0],-f[2]); a0=a if a0 is None else a0
        if abs(np.degrees(a))<0.3: break
        ca,sa=np.cos(a),np.sin(a); R=np.array([[ca,0,sa],[0,1,0],[-sa,0,ca]]); P=(P-c)@R.T+c; Nn=Nn@R.T
    V['p']=P; V['n']=Nn; m.data[ch][:n*28]=V.tobytes()
    tg['J_Eye_L' if c[0]>0 else 'J_Eye_R']=c; print('obj',k,'turned',round(float(np.degrees(a0)),1),'deg')
J={0:m.build()}
for f,b in blocks:
    d=J.get(f) or B[f]
    if d[:4]==b'JBOY': J[f],done=move_bones(d,tg); print(f,done) if f==0 else None
open(sys.argv[2],'wb').write(epkwrite.build_raw(hdr,[(f,epkwrite.zblock(J[f]) if f in J else b) for f,b in blocks]))

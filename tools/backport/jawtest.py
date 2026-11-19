"""Jaw gate: J_Jaw 15 deg + morph 114 at 0.6, head region front/left. Usage: jawtest.py PAC OUT.png"""
import sys,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import pose,jboy,render,hidetable
j=pose.load(sys.argv[1]); out=sys.argv[2]; tris=[]
for k,o in enumerate(j.objs):
    if o['pos'][:,1].mean()<-150 or k==0:
        P=pose.pose(j,k,bones={'J_Jaw':((1,0,0),15)},morph={114:0.6} if k==0 else {})
        if k!=0 and o['pos'][:,1].mean()>-150: continue
        for st,t in hidetable.strip_tri_starts(j.indices(o)[1]): tris.append((P[list(t)],(0.8,0.65,0.55) if k==0 else (0.9,0.9,0.95)))
for v in ('front','left'):
    render.render(tris,v,out.replace('.png','_%s.png'%v),size=(6,6),xlim=(-15,15),ylim=(150,200),title='jaw 15 + m114 0.6 '+v)
print(len(tris))

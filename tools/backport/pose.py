"""Offline posing for built pacs: linear-blend skinning with simple bone rotations about world axes through bone
world positions, plus morph weights. Textured rendering of the face via facecheck.tex_tris."""
import sys,zlib,numpy as np;sys.path.insert(0,'/home/claude/scripts')
import jboy,epkwrite,jcheck,texconv,render,facecheck
def rot(axis,deg):
    a=np.radians(deg); c,s=np.cos(a),np.sin(a); x,y,z=np.asarray(axis,float)/np.linalg.norm(axis)
    return np.array([[c+x*x*(1-c),x*y*(1-c)-z*s,x*z*(1-c)+y*s],[y*x*(1-c)+z*s,c+y*y*(1-c),y*z*(1-c)-x*s],[z*x*(1-c)-y*s,z*y*(1-c)+x*s,c+z*z*(1-c)]])
def load(pac):
    hdr,bl=epkwrite.raw_blocks(pac); return jboy.JBOY(zlib.decompress(dict(bl)[0][16:]))
def skin(j,o):
    sk=jcheck.raw_skin(j,o); i=sk['i'].astype(int); w=sk['w']; pal=[j.bones[b]['name'] for b in j.palette]
    return [[(pal[a],b) for a,b in zip(i[v],w[v]) if b>0 and a<len(pal)] for v in range(o['vc'])]
def pose(j,k,bones={},morph={}):
    """bones: name -> (axis, degrees) rotation about the bone's world position (children not propagated)."""
    o=j.objs[k]; P=o['pos'].astype(float).copy()
    if morph:
        M=np.asarray(jboy.morphs(j,o))
        for n,a in morph.items(): P+=a*M[n-1]
    W={b['name']:np.array(b['world']) for b in j.bones}; out=P.copy()
    if bones:
        S=skin(j,o); T={n:(rot(ax,d),W[n]) for n,(ax,d) in bones.items()}
        for v,inf in enumerate(S):
            acc=np.zeros(3)
            for n,w in inf:
                if n in T: R,c=T[n]; acc+=w*(R@(P[v]-c)+c)
                else: acc+=w*P[v]
            out[v]=acc
    return out
def jaw_weight(j,k):
    return np.array([sum(w for n,w in inf if n=='J_Jaw') for inf in skin(j,k and j.objs[k] or j.objs[0])])

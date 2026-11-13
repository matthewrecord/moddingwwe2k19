"""Textured face comparison: Flash 2K25 M_Head (+M_EYE) vs our fitted head (+ eye objects as built)."""
import sys,zlib,numpy as np;sys.path.insert(0,'/home/claude/scripts')
import mdlfmt,jboy,epkwrite,texconv,render
F='/home/claude/pairs/FMW/BaseModel/Textures/'
def tex_tris(P,T,UV,img):
    h,w=img.shape[:2]; out=[]
    for t in T:
        u,v=UV[list(t)].mean(0); c=img[min(h-1,max(0,int(v*h))),min(w-1,max(0,int(u*w))),:3]/255
        out.append((P[list(t)],c))
    return out
def source():
    M=mdlfmt.MDL('/home/claude/ext/fmw/base.mdl'); L=M.lods()[0]; out=[]
    for i,m in enumerate(M.meshes):
        img={'M_Head':'head_color.dds','M_EYE':'eye_color.dds'}.get(m['name'])
        if img: S=m['streams']; out+=tex_tris(S['POSITION'],L[i].reshape(-1,3),S['TEXCOORD'],texconv.load(F+img))
    return out
def ours(pac):
    hdr,bl=epkwrite.raw_blocks(pac); j=jboy.JBOY(zlib.decompress(dict(bl)[0][16:])); out=[]
    for k,img in ((0,'head_color.dds'),(3,'eye_color.dds'),(4,'eye_color.dds')):
        o=j.objs[k]; out+=tex_tris(o['pos'],jboy.strip_to_tris(j.indices(o)[1]),o['uv'],texconv.load(F+img))
    return out
if __name__=='__main__':
    pac,tag=sys.argv[1],sys.argv[2]
    for nm,t in (('src',source()),(tag,ours(pac))):
        for v in ('front','left'): render.render(t,v,f'/home/claude/out/face_{nm}_{v}.png',size=(5,6),xlim=(-13,13),ylim=(160,195),title=f'{nm} {v}')

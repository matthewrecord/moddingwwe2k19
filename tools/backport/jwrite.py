"""Relocating JBOY writer: chunks = [region start, next region start); any chunk may be replaced by new bytes;
all pointer words (found by jlayout.pointers) and the header size words are re-patched."""
import sys,struct;sys.path.insert(0,'/home/claude/scripts');import jboy,jlayout
class Writer:
    def __init__(s,j):
        s.j=j; b=j.b; R=jlayout.regions(j); s.P=jlayout.pointers(j,R)
        starts=sorted({a for _,a,_ in R}|{len(b)}); s.names={}
        for nm,a,e in R: s.names.setdefault(a,nm)
        s.chunks=[[a,b[a:starts[i+1]]] for i,a in enumerate(starts[:-1])]
        s.byname={s.names[a]:i for i,(a,_) in enumerate(s.chunks) if a in s.names}
        s.align={a:(16 if a%16==0 else 4) for a,_ in s.chunks}
    def replace(s,name,data):
        s.chunks[s.byname[name]][1]=bytes(data)
    def build(s):
        out=bytearray(); newpos={}
        for a,d in s.chunks:
            al=s.align[a]
            if a>0: out+=b'\0'*((-len(out))%al)
            newpos[a]=len(out); out+=d
        old=s.j.b
        # map pointer word locations: a pointer word at old offset p lives in the chunk that contains p
        starts=[a for a,_ in s.chunks]
        import bisect
        for p in s.P:
            c=starts[bisect.bisect_right(starts,p)-1]; np_=newpos[c]+(p-c)
            v,=struct.unpack_from('>I',old,p); struct.pack_into('>I',out,np_,newpos[v+8]-8)
        total=len(out)-8; struct.pack_into('>I',out,4,total); struct.pack_into('>I',out,12,total)
        return bytes(out)

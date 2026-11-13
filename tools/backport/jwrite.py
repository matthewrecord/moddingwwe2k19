"""Relocating JBOY writer (v2). Pointer list = the file's own POF0 table. Every pointer target is a region start, so any
region (chunk = region start .. next region start) can be replaced by bytes of a different length."""
import sys,struct,bisect;sys.path.insert(0,'/home/claude/scripts');import jboy,jlayout,pof0
class Writer:
    def __init__(s,j,style='porter'):
        s.limit=0x3000 if style=='porter' else 0x4000
        s.j=j; b=j.b; R=jlayout.regions(j); s.P,s.pof_at=jlayout.pof_list(j)
        starts=sorted({a for _,a,_ in R}|{s.pof_at})
        s.names={}
        for nm,a,e in R: s.names.setdefault(a,nm)
        s.chunks=[[a,b[a:starts[i+1]]] for i,a in enumerate(starts[:-1])]
        s.byname={s.names[a]:i for i,(a,_) in enumerate(s.chunks) if a in s.names}
        s.starts=[a for a,_ in s.chunks]; s.tail=b[s.pof_at:]
        bad=[p for p in s.P if (struct.unpack_from('>I',b,p)[0]+8) not in set(s.starts)]
        s.inner_targets=bad   # pointers whose target is not a region start (must be empty for safe edits)
    def replace(s,name,data): s.chunks[s.byname[name]][1]=bytes(data)
    def build(s):
        out=bytearray(); newpos={}
        for a,d in s.chunks:
            if a%16==0 and a>0: out+=b'\\0'*((-len(out))%16)
            elif a>0: out+=b'\\0'*((-len(out))%4)
            newpos[a]=len(out); out+=d
        old=s.j.b; newP=[]
        for p in s.P:
            c=s.starts[bisect.bisect_right(s.starts,p)-1]; q=newpos[c]+(p-c)
            v,=struct.unpack_from('>I',old,p); t=v+8
            tc=s.starts[bisect.bisect_right(s.starts,t)-1]
            struct.pack_into('>I',out,q,newpos[tc]+(t-tc)-8); newP.append(q-8)
        size=len(out)-8; struct.pack_into('>I',out,4,size); struct.pack_into('>I',out,12,size)
        return bytes(out)+pof0.encode(newP,s.limit)+s.tail[8+struct.unpack_from('>I',s.tail,4)[0]:]

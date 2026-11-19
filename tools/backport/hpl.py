"""2K24/2K25 .hpl hide lists: HPL! LOD! ... MESH <u32 len><name, pad4> <u32 n> <n x u32 vertex index> ... (first list per mesh = LOD0)."""
import struct
def parse(path):
    b=open(path,'rb').read(); out={}; o=0
    if b[:4]==b'MCD!':  # 2K26: hide lists live in the HPL! chunk embedded in the attire .mcd
        o=b.find(b'HPL!HPL!'); assert o>=0, 'no HPL! chunk in '+path
        b=b[:b.find(b'END!',o)]
        # 2K26 lists a mesh several times per LOD (one list per hiding attire group): union them per LOD
        lods=[]; p=o
        while True:
            p=b.find(b'LOD!',p)
            if p<0: break
            lods.append(p); p+=4
        lods.append(len(b))
        for a,z in zip(lods,lods[1:]):
            sub={}; q=a
            while True:
                q=b.find(b'MESH',q,z)
                if q<0: break
                n,=struct.unpack_from('<I',b,q+4); name=b[q+8:q+8+n].decode(); r=q+8+n; r+=(-r)%4
                c,=struct.unpack_from('<I',b,r); sub.setdefault(name,set()).update(struct.unpack_from('<%dI'%c,b,r+4)); q=r+4+4*c
            for k,v in sub.items(): out.setdefault(k,[]).append(sorted(v))
        return out
    while True:
        o=b.find(b'MESH',o)
        if o<0: break
        n,=struct.unpack_from('<I',b,o+4); name=b[o+8:o+8+n].decode(); p=o+8+n; p+=(-p)%4
        c,=struct.unpack_from('<I',b,p); idx=struct.unpack_from('<%dI'%c,b,p+4)
        out.setdefault(name,[]).append(list(idx)); o=p+4+4*c
    return out

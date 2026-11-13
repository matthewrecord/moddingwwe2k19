"""2K24/2K25 .hpl hide lists: HPL! LOD! ... MESH <u32 len><name, pad4> <u32 n> <n x u32 vertex index> ... (first list per mesh = LOD0)."""
import struct
def parse(path):
    b=open(path,'rb').read(); out={}; o=0
    while True:
        o=b.find(b'MESH',o)
        if o<0: break
        n,=struct.unpack_from('<I',b,o+4); name=b[o+8:o+8+n].decode(); p=o+8+n; p+=(-p)%4
        c,=struct.unpack_from('<I',b,p); idx=struct.unpack_from('<%dI'%c,b,p+4)
        out.setdefault(name,[]).append(list(idx)); o=p+4+4*c
    return out

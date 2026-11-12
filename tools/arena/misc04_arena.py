import sys,struct,json
sys.path.insert(0,'/home/claude/moddingwwe2k19/tools/lib')
from yukes import HSPC,SHDC
def f920(path):
    S=SHDC(HSPC(open(path,'rb').read()).files[0]['data'])
    return [x for x in S.files if x['id']==920][0]['data']
def entries(d):
    n=struct.unpack_from('<I',d,0)[0]; out=[]
    for i in range(n):
        o=16+32*i
        name=d[o:o+16].split(b'\0')[0].decode(); typ=d[o+16:o+20].split(b'\0')[0].decode(); size,off=struct.unpack_from('<II',d,o+20)
        out.append((name,typ,size,off,d[off:off+size]))
    return out
if __name__=='__main__':
    d=f920(sys.argv[1]); print(d[:16].hex()); E=entries(d); print(len(E),E[0][:4],E[-1][:4])
    print(E[0][4][:700])

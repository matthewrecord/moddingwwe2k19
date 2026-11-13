"""Map a JBOY into regions and find every pointer word (value+8 = a region start)."""
import sys,struct,numpy as np;sys.path.insert(0,'/home/claude/scripts');import jboy
def regions(j):
    b=j.b; h=j.h; R=[]
    R.append(('hdr',0,0x58)); R.append(('objtable',0x58,0x58+184*h[6]))
    for k,o in enumerate(j.objs):
        f=o['f']; vc=f[0]; ninf=f[23]; nm=max(f[25],1)
        vp=o['vptr']; R.append((f'o{k}.vptr',f[26]+8,f[26]+8+4*len(vp)))
        for si,p in enumerate(vp): R.append((f'o{k}.vset{si}',p+8,p+8+vc*28))
        R+= [(f'o{k}.skin',f[27]+8,f[27]+8+vc*ninf*8),
             (f'o{k}.uv',f[28]+8,f[28]+8+vc*8),(f'o{k}.tan',f[29]+8,f[29]+8+vc*12),(f'o{k}.plist',f[38]+8,f[38]+8+4*f[37])]
        p=f[39]+8; n,ptr=struct.unpack_from('>2I',b,p+4); R+=[(f'o{k}.ixhdr',p,p+12),(f'o{k}.ix',ptr+8,ptr+8+2*n)]
        for q in struct.unpack_from('>%dI'%f[37],b,f[38]+8): R.append((f'o{k}.par',q+8,q+8+24))
    R+=[('bones',h[10]+8,h[10]+8+80*h[8]),('texnames',h[11]+8,h[11]+8+16*h[9]),('meshnames',h[12]+8,h[12]+8+32*h[13])]
    m=struct.unpack_from('>8I',b,0x40); R+=[('morphnames',m[3]+8,m[3]+8+16*m[2]),('palhdr',m[5]+8,m[5]+16)]
    n,lp=struct.unpack_from('>2I',b,m[5]+8); R.append(('pal',lp+8,lp+8+4*n))
    return sorted(R,key=lambda x:x[1])
DATA=('.vset','.skin','.uv','.tan','.ix')
def pointers(j,R):
    b=j.b; starts={a for _,a,_ in R}; P=[]
    scan=[(a,e) for nm,a,e in R if not any(x in nm for x in DATA) and nm!='bones']
    for a,e in scan:
        for o in range(a - a%4, e, 4):
            if o+4>len(b): break
            v,=struct.unpack_from('>I',b,o)
            if v+8 in starts and v>0: P.append(o)
    return sorted(set(P))
if __name__=='__main__':
    j=jboy.JBOY(sys.argv[1]); R=regions(j); P=pointers(j,R)
    cover=np.zeros(len(j.b),bool)
    for _,a,e in R: cover[a:e]=True
    print('regions',len(R),'pointers',len(P),'uncovered bytes',(~cover).sum(),'nonzero uncovered',np.count_nonzero(np.frombuffer(j.b,'u1')[~cover]))
    # where are nonzero uncovered bytes
    idx=np.where((~cover)&(np.frombuffer(j.b,'u1')!=0))[0]
    runs=[];s=None
    for i in idx:
        if s is None or i!=prev+1:
            if s is not None: runs.append((s,prev+1))
            s=i
        prev=i
    if s is not None: runs.append((s,prev+1))
    print('nonzero uncovered runs',len(runs)); [print(hex(a),hex(e),e-a,j.b[a:min(e,a+24)].hex(' ')) for a,e in runs[:15]]

def pof_list(j):
    import pof0
    b=j.b; i=b.rfind(b'POF0'); return [x+8 for x in pof0.decode(b[i:])], i

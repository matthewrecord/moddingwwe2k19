"""Reader for WWE 2K22+ community .mdl (MDL!) files. Reverse-engineered 2026-11-12."""
import struct, numpy as np
FMT={('R32_G32_B32','float'):('<f4',3),('R32_G32','float'):('<f4',2),('R32_G32_B32_A32','float'):('<f4',4),
     ('R8_G8_B8_A8','snorm'):('i1',4),('R8_G8_B8_A8','unorm'):('u1',4),('R8','unorm'):('u1',1),('R8','snorm'):('i1',1),
     ('R16_G16_B16_A16','uint'):('<u2',4),('R8_G8_B8_A8','uint'):('u1',4),('R16_G16','float'):('<f2',2),('R16_G16_B16_A16','float'):('<f2',4)}
class MDL:
    def __init__(s,path,verbose=False):
        b=s.b=open(path,'rb').read(); assert b[:4]==b'MDL!'
        s.ch={}; o=0x24
        while o+8<=len(b):
            t=b[o:o+4]; sz,=struct.unpack_from('<I',b,o+4); s.ch[t]=(o+8,sz); o+=8+sz
            if t==b'END!': break
        to,_=s.ch[b'TEXT']; n,=struct.unpack_from('<I',b,to)
        offs=struct.unpack_from('<%dI'%n,b,to+4); base=to+4+4*n
        s.S=[b[base+x:b.index(b'\0',base+x)].decode('latin1') for x in offs]
        bo,_=s.ch[b'BONE']; nb,=struct.unpack_from('<I',b,bo+8); s.bones=[]
        for i in range(nb):
            r=bo+12+i*33; fl,idx,par=struct.unpack_from('<Ihh',b,r)
            s.bones.append(dict(name=s.S[idx],parent=par,t=struct.unpack_from('<3f',b,r+8),r=struct.unpack_from('<3f',b,r+20)))
        s.parse_meshes(verbose)
    def parse_meshes(s,verbose):
        b=s.b; mo,ms=s.ch[b'MBfD']; nm,=struct.unpack_from('<I',b,mo); o=mo+4; s.meshes=[]
        for m in range(nm):
            nameidx,flags,_,x=struct.unpack_from('<IIHI',b,o); bbox=struct.unpack_from('<6f',b,o+14)
            vc,ns,_=struct.unpack_from('<IHH',b,o+38); o+=46; st={}
            for k in range(ns):
                a,f,t,sem=struct.unpack_from('<4H',b,o+12); key=(s.S[f],s.S[t]); dt,c=FMT[key]; o+=20; o+=(-o)%4
                arr=np.frombuffer(b,dtype=dt,count=vc*c,offset=o).reshape(vc,c); o+=arr.nbytes; o+=(-o)%4
                name=s.S[a]
                while name in st: name+='_'
                st[name]=arr
            nbn,ninf=struct.unpack_from('<2H',b,o); o+=4; o+=(-o)%4
            st['BI']=np.frombuffer(b,'<u2',vc*ninf,o).reshape(vc,ninf); o+=vc*ninf*2
            st['BW']=np.frombuffer(b,'u1',vc*ninf,o).reshape(vc,ninf)/255.0; o+=vc*ninf
            e=b.index(b'ENDM',o); o=e+8
            s.meshes.append(dict(name=s.S[nameidx],vc=vc,bbox=bbox,streams=st))
            if verbose: print(m,s.S[nameidx],vc,list(st),ninf)
        lo,ls=s.ch[b'LODs']; nl,nm2=struct.unpack_from('<2I',b,lo); s.lodraw=(lo,ls,nl,nm2)
    def lods(s, verbose=False):
        b=s.b; lo,ls,nl,nm=s.lodraw; o=lo+8; out=[]
        for l in range(nl):
            L=[]
            for m in range(nm):
                z,n=struct.unpack_from('<HI',b,o); o+=6
                vc=s.meshes[m]['vc']; dt='<u2' if vc<65536 else '<u4'
                ix=np.frombuffer(b,dt,n,o); o+=ix.nbytes; o=b.index(b'ENDM',o)+8
                if verbose: print(l,m,z,n,n%3,ix.max() if n else -1,vc)
                L.append(ix.reshape(-1,3) if n%3==0 else ix)
            out.append(L)
        if verbose: print('consumed',o-lo,'of',ls)
        return out

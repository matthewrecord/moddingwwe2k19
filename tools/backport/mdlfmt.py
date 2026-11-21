"""Reader for WWE 2K22+ community .mdl (MDL!) files. Reverse-engineered 2026-11-12."""
import struct, numpy as np
FMT={('R32_G32_B32','float'):('<f4',3),('R32_G32','float'):('<f4',2),('R32_G32_B32_A32','float'):('<f4',4),
     ('R8_G8_B8_A8','snorm'):('i1',4),('R8_G8_B8_A8','unorm'):('u1',4),('R8','unorm'):('u1',1),('R8','snorm'):('i1',1),
     ('R16_G16_B16_A16','uint'):('<u2',4),('R8_G8_B8_A8','uint'):('u1',4),('R16_G16','float'):('<f2',2),('R16_G16_B16_A16','float'):('<f2',4),('R32','uint'):('<u4',1),('R32','float'):('<f4',1),('R16_G16','uint'):('<u2',2),('R16','uint'):('<u2',1),('R8_G8','unorm'):('u1',2),('R16_G16','unorm'):('<u2',2),('R16_G16','snorm'):('<i2',2),('R10_G10_B10_A2','unorm'):('<u4',1)}
class MDL:
    def __init__(s,path,verbose=False):
        b=s.b=open(path,'rb').read(); assert b[:4]==b'MDL!'
        s.ch={}; o=0x24; s._bi0=0; s.ver=struct.unpack_from('<I',b,4)[0]
        while o+8<=len(b):
            t=b[o:o+4]; sz,=struct.unpack_from('<I',b,o+4); s.ch[t]=(o+8,sz); o+=8+sz
            if t==b'END!': break
        to,_=s.ch[b'TEXT']; n,=struct.unpack_from('<I',b,to)
        offs=struct.unpack_from('<%dI'%n,b,to+4); base=to+4+4*n
        s.S=[b[base+x:b.index(b'\0',base+x)].decode('latin1') for x in offs]
        bo,_=s.ch[b'BONE']; nb,=struct.unpack_from('<I',b,bo+8); s.bones=[]
        r=bo+12
        for i in range(nb):
            # 2K25 (v0x29) inserts padding blocks between some records: resync on name index == i+? 
            fl,idx,par=struct.unpack_from('<Ihh',b,r)
            if not (0<=idx<len(s.S) and par<i):
                p=r
                while not (struct.unpack_from('<H',b,p+4)[0]==s._bi0+i and struct.unpack_from('<h',b,p+6)[0]<i): p+=1
                r=p; fl,idx,par=struct.unpack_from('<Ihh',b,r)
            if i==0: s._bi0=idx
            s.bones.append(dict(name=s.S[idx],parent=par,t=struct.unpack_from('<3f',b,r+8),r=struct.unpack_from('<3f',b,r+20))); r+=33
        s.parse_meshes(verbose)
    def parse_meshes(s,verbose):
        b=s.b; mo,ms=s.ch[b'MBfD']; nm,=struct.unpack_from('<I',b,mo); o=mo+4; s.meshes=[]
        for m in range(nm):
            if s.ver>=0x29:
                nameidx,flags=struct.unpack_from('<II',b,o); bbox=struct.unpack_from('<6f',b,o+16)
                vc,ns,_=struct.unpack_from('<IHH',b,o+40); o+=48; st={}
            else:
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
        # 2K26 (v0x2f): LOD0 has the 2K25 layout; LOD1+ records carry an extra field (not decoded). Only LOD0 is used.
        for l in range(1 if s.ver>=0x2f else nl):
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

def lod0_materials(M):
    """LOD0 per-mesh material ranges -> {mesh name: per-triangle material name}. Tail after each mesh's index data:
    u16 0, u32 n, then n x (u32 mat, u32 start_index, u32 index_count, u32 max_vertex), u32 0 -- mat indexes MTL! entries
    (u16 string index + u32 hash each)."""
    b=M.b; mo,ms=M.ch[b'MTL!']; nmat,=struct.unpack_from('<I',b,mo); mats=[M.S[struct.unpack_from('<H',b,mo+4+6*i)[0]] for i in range(nmat)]
    lo,ls,nl,nm=M.lodraw; o=lo+8; out={}
    for m in range(nm):
        z,n=struct.unpack_from('<HI',b,o); o+=6; vc=M.meshes[m]['vc']; e=o+n*(2 if vc<65536 else 4)
        per=None
        for pad in (2,0,1,3):   # alignment pad before the count varies; keep the layout whose ranges add up to n
            try:
                k,=struct.unpack_from('<I',b,e+pad); recs=[struct.unpack_from('<4I',b,e+pad+4+16*r) for r in range(k)] if 0<k<64 else []
            except struct.error: continue
            if recs and sum(r[2] for r in recs)==n and recs[0][1]==0:
                per=np.empty(n//3,object)
                for mat,st,cnt,_ in recs: per[st//3:(st+cnt)//3]=mats[mat] if mat<len(mats) else str(mat)
                break
        if per is not None: out[M.meshes[m]['name']]=per
        o=b.index(b'ENDM',e)+8
    return out

"""Object-level JBOY builder on top of the region/POF0 model.
Chunks have ids; pointers are (loc_chunk, loc_off) -> (tgt_chunk). Objects can be cloned (all their chunks + their
184-byte record + their pointers) and their chunk contents replaced."""
import sys,struct,bisect;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)));import jboy,jlayout,pof0
class Model:
    def __init__(s,j,style='porter'):
        s.j=j; b=j.b; s.limit=0x3000 if style=='porter' else 0x4000
        R=jlayout.regions(j); P,s.pof_at=jlayout.pof_list(j)
        starts=sorted({a for _,a,_ in R}|{s.pof_at}); nm={}
        for n,a,e in R: nm.setdefault(a,n)
        s.order=[]; s.data={}; s.name={}
        for i,a in enumerate(starts[:-1]):
            cid=a; s.order.append(cid); s.data[cid]=bytearray(b[a:starts[i+1]]); s.name[cid]=nm.get(a,'?')
        st=starts[:-1]; s.ptr=[]
        for p in P:
            lc=st[bisect.bisect_right(st,p)-1]; v,=struct.unpack_from('>I',b,p)
            s.ptr.append([lc,p-lc,v+8])
        s.tail=b[s.pof_at:]; s.tail=s.tail[8+struct.unpack_from('>I',s.tail,4)[0]:]
        s.objtab=[c for c in s.order if s.name[c]=='objtable'][0]
        s.next_id=10**9
    def obj_chunks(s,k):
        return [c for c in s.order if s.name[c].startswith(f'o{k}.')]
    def _hdrword(s,off=0x18):
        c=max(c for c in s.order if c<10**9 and c<=off); return c,off-c
    def nobj(s): c,o=s._hdrword(); return struct.unpack_from('>I',s.data[c],o)[0]
    def clone_object(s,k):
        """Append a copy of object k (new index = old count). Returns new index."""
        new=s.nobj(); mp={}
        src=s.obj_chunks(k)
        # insert cloned chunks right after the last chunk of the last object
        last=max(i for i,c in enumerate(s.order) if s.name[c].startswith('o') and '.' in s.name[c] and s.name[c][1:].split('.')[0].isdigit())
        ins=last+1
        for c in src:
            nid=s.next_id; s.next_id+=1; mp[c]=nid
            s.data[nid]=bytearray(s.data[c]); s.__dict__.setdefault('src',{})[nid]=c; s.name[nid]=f'o{new}.'+s.name[c].split('.',1)[1]
            s.order.insert(ins,nid); ins+=1
        # object record
        T=s.data[s.objtab]; rec_off=0x58-0x58  # objtable chunk starts at 0x58
        rec=bytearray(T[184*k:184*k+184]); struct.pack_into('>I',rec,30*4,new)
        tabend=184*new; T[tabend:tabend]=rec   # insert after existing records (table chunk may carry padding after)
        # pointers: inside cloned chunks, and inside the source record
        add=[]
        for lc,lo,t in s.ptr:
            if lc in mp: add.append([mp[lc],lo,mp.get(t,t)])
            elif lc==s.objtab and 184*k<=lo<184*k+184: add.append([s.objtab,tabend+(lo-184*k),mp.get(t,t)])
        s.ptr+=add
        c,o=s._hdrword(); struct.pack_into('>I',s.data[c],o,new+1)
        return new
    def chunk(s,k,part):
        return [c for c in s.order if s.name[c]==f'o{k}.{part}'][0]
    def build(s):
        out=bytearray(); pos={}
        for c in s.order:
            a=c if c<10**9 else getattr(s,'src',{}).get(c)
            # keep every chunk at its original address mod 16 (bones/matrices need 16-byte alignment relative to base 8)
            if out:
                if a is not None and a%4==0: out+=b'\0'*((a-len(out))%16)
                else: out+=b'\0'*((-len(out))%4)
            pos[c]=len(out); out+=s.data[c]
        newP=[]
        starts=sorted(c for c in pos if c<10**9)
        for lc,lo,t in s.ptr:
            q=pos[lc]+lo
            if t in pos: tv=pos[t]
            else:
                tc=starts[bisect.bisect_right(starts,t)-1]; tv=pos[tc]+(t-tc)
            struct.pack_into('>I',out,q,tv-8); newP.append(q-8)
        size=len(out)-8; struct.pack_into('>I',out,4,size); struct.pack_into('>I',out,12,size)
        return bytes(out)+pof0.encode(newP,s.limit)+s.tail

import numpy as np
def tris_to_strip(T):
    """Encode a triangle list as one strip with degenerate joins; preserves winding under jboy.strip_to_tris."""
    S=[]
    for a,b,c in T:
        if not S: S=[a,b,c]; continue
        # bring length parity so the next real triangle starts at an even position
        S+= [S[-1], a]
        if len(S)%2==1: S.append(a)
        S+=[a,b,c]
    return np.array(S,dtype=np.int64)
def _cyc(t):
    t=list(t); i=t.index(min(t)); return tuple(t[i:]+t[:i])
def same_tris(A,B):
    return sorted(map(_cyc,A))==sorted(map(_cyc,B))
def set_object(m,k,pos,nrm,col,uv,tan,bi_slots,bw,strip,bbox_sphere=None):
    """Replace object k's geometry. bi_slots are PALETTE SLOT indices (as stored in the file)."""
    vc=len(pos); ninf=bw.shape[1]
    V=np.zeros(vc,dtype=[('p','>f4',3),('n','>f4',3),('c','u1',4)]); V['p']=pos; V['n']=nrm; V['c']=col
    vp=m.chunk(k,'vptr'); assert len(m.data[vp])>=4
    m.data[m.chunk(k,'vset0')]=bytearray(V.tobytes()+b'\0'*4)
    S=np.zeros((vc,ninf),dtype=[('i','>u2'),('p','>u2'),('w','>f4')]); S['i']=bi_slots; S['w']=bw
    m.data[m.chunk(k,'skin')]=bytearray(S.tobytes())
    m.data[m.chunk(k,'uv')]=bytearray(np.asarray(uv,'>f4').tobytes())
    m.data[m.chunk(k,'tan')]=bytearray(np.asarray(tan,'>f4').tobytes())
    ix=np.asarray(strip,'>u2'); m.data[m.chunk(k,'ix')]=bytearray(ix.tobytes())
    h=m.data[m.chunk(k,'ixhdr')]; struct.pack_into('>I',h,4,len(ix))
    T=m.data[m.objtab]; r=184*k
    struct.pack_into('>I',T,r,vc); struct.pack_into('>I',T,r+23*4,ninf); struct.pack_into('>I',T,r+40*4,vc)
    if bbox_sphere is not None: struct.pack_into('>4f',T,r+42*4,*bbox_sphere)

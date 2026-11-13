"""Block 0xCE (M_Body hide table): per body object, ranges of strip START positions whose triangles are hidden.
Layout (Fletcher): ...0x74: list for body object 1 = u32 n, n x (u32 start, u32 end); tail ... u32 n2, (start,end) for
object 2. Size fields that grow with list 1: word 4 (entry size), and two sub sizes found at 0x5C and 0x6C."""
import struct,numpy as np
def strip_tri_starts(ix):
    out=[]
    for k in range(len(ix)-2):
        a,b,c=ix[k],ix[k+1],ix[k+2]
        if a==b or b==c or a==c: continue
        out.append((k,(a,b,c) if k%2==0 else (b,a,c)))
    return out
def parse(b):
    w=list(struct.unpack('<%dI'%(len(b)//4),b)); i=0x74//4; n=w[i]; pairs=np.array(w[i+1:i+1+2*n]).reshape(-1,2); tail=w[i+1+2*n:]
    return w,pairs,tail
def rebuild(b,new_pairs1,new_range2):
    w,pairs,tail=parse(b); i=0x74//4; d=(len(new_pairs1)-len(pairs))*8
    head=w[:i]; head[4]+=d; head[0x5C//4]+=d; head[0x6C//4]+=d
    tail=list(tail); tail[-2],tail[-1]=new_range2
    out=head+[len(new_pairs1)]+[int(x) for p in new_pairs1 for x in p]+tail
    return struct.pack('<%dI'%len(out),*out)
def to_ranges(starts):
    starts=sorted(set(starts)); R=[]
    for s in starts:
        if R and s==R[-1][1]+1: R[-1][1]=s
        else: R.append([s,s])
    return R
def build_blocks(b,blocks):
    """General writer. blocks: {object_index_minus_1: [(start,end),...]}. Header words 0..20 kept; word 4 = size-12;
    word 21 = number of blocks; each block = [16, 8n+32, idx, 1, 16, 8n+16, 0, n, pairs...]."""
    w=list(struct.unpack('<%dI'%(len(b)//4),b)); out=w[:21]+[len(blocks)]
    for idx in sorted(blocks):
        p=blocks[idx]; n=len(p); out+=[16,8*n+32,idx,1,16,8*n+16,0,n]+[int(x) for q in p for x in q]
    out[4]=len(out)*4-12
    return struct.pack('<%dI'%len(out),*out)

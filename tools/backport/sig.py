"""Per-pac skin-weight signature: weight mass per bone name over yCS_skin objects of the main JBOY. Resumable."""
import sys,os,struct,zlib,json,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import jboy,numpy as np
def first_jboy(path):
    with open(path,'rb') as f: b=f.read()
    i=b.find(b'ZLIB')
    while i>=0:
        a,c,u=struct.unpack_from('<3I',b,i+4)
        try:
            d=zlib.decompressobj().decompress(b[i+16:i+16+c],32)
            if d[:4]==b'JBOY': return zlib.decompress(b[i+16:i+16+c])
        except Exception: pass
        i=b.find(b'ZLIB',i+4)
def sig(path):
    d=first_jboy(path)
    if d is None: return None
    j=jboy.JBOY(d); bn=[x['name'] for x in j.bones]; S={}; nv=0
    for o in j.objs:
        if o['shader']!='yCS_skin' or o['bi'] is None: continue
        nv+=o['vc']
        for i,w in zip(o['bi'].ravel(),o['bw'].ravel()):
            if w>0 and i<len(bn): S[bn[i]]=S.get(bn[i],0)+float(w)
    return dict(nb=len(bn),nv=nv,s={k:round(v,2) for k,v in S.items()})
if __name__=='__main__':
    out=sys.argv[1]; files=sys.argv[2:]; t=time.time()
    done=set(json.loads(l)['f'] for l in open(out)) if os.path.exists(out) else set()
    with open(out,'a') as fo:
        for f in files:
            if f in done: continue
            if time.time()-t>150: break
            try: r=sig(f)
            except Exception as e: r={'err':repr(e)}
            fo.write(json.dumps(dict(f=f,r=r))+'\n'); fo.flush()

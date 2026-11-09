"""Match Wwise event IDs (FNV-1 32-bit of the lower-case name) against Play_MUS_%04d_%02d_%d_%d.
Usage: python3 -I evmatch.py <sound dir> <out.txt>   (sound dir = <install>/sound)"""
import sys,os,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from bnk import banks,hirc,objs
def fnv(s):
    h=2166136261
    for c in s.lower().encode(): h=(h*16777619)&0xffffffff; h^=c
    return h
if __name__=='__main__':
    D=sys.argv[1]; ev={}
    for pck in ['music_e_s.pck','patch_10.pck','patch_20.pck','patch_30.pck','patch_day1.pck']:
        for fid,data in banks(os.path.join(D,pck)):
            for body in hirc(data).get('HIRC',[]):
                for t,oid,_ in objs(body):
                    if t==4: ev[oid]=(pck,fid)
    hits=collections.defaultdict(list)
    for mid in range(10000):
      for var in range(20):
        for a in range(4):
          for m in range(4):
            n=f"Play_MUS_{mid:04d}_{var:02d}_{a}_{m}"
            if fnv(n) in ev: hits[ev[fnv(n)]].append(n)
    for k,v in hits.items(): print(k,len(v))
    open(sys.argv[2],'w').write('\n'.join(f"{k[0]} {k[1]} {n}" for k,v in hits.items() for n in v)+'\n')

"""Decode the two 2K26 moveset tables (FlatBuffers .jsfb from bakedfile02, payloads via tools/cak26/payload.py).
Usage: decode26.py CHAR.jsfb CMOV.jsfb OUTDIR
 CHAR (file id 'Char', bakedfile02 file 204) -> char_movesets.json {wrestler_id: [358 raw u16 move ids]}
   root f0 -> vector of wrestler records (f0 u16 id, f1 -> wrapper); wrapper f0 -> vector of slot tables (f0 u16 move id).
 CMOV (file id 'CMov', bakedfile02 file 179) -> move_catalog26.json {raw_id: [name, tag]}  (record f0 = name string, f1 = u16 id)
Raw 2K26 ids are 2K19 ids byte-swapped."""
import sys,struct,json,os
def fb(d):
    u32=lambda o:struct.unpack_from('<I',d,o)[0]; u16=lambda o:struct.unpack_from('<H',d,o)[0]
    def table(t):
        vt=t-struct.unpack_from('<i',d,t)[0]; return [u16(vt+4+2*i) for i in range((u16(vt)-4)//2)]
    deref=lambda o:o+u32(o)
    return u32,u16,table,deref
def char(d):
    u32,u16,table,deref=fb(d); root=u32(0); v=deref(root+table(root)[0]); per={}
    for k in range(u32(v)):
        t=deref(v+4+4*k); f=table(t)
        if len(f)<2 or not f[0] or not f[1]: continue
        wr=deref(t+f[1]); wf=table(wr); sv=deref(wr+wf[0]); ids=[]
        for s in range(u32(sv)):
            st=deref(sv+4+4*s); sf=table(st); ids.append(u16(st+sf[0]) if sf and sf[0] else 0)
        per[u16(t+f[0])]=ids
    return per
def cmov(d):
    u32,u16,table,deref=fb(d)
    def string(o):
        p=deref(o); n=u32(p)
        if 0<n<300:
            s=d[p+4:p+4+n]
            if all(32<=c<127 for c in s): return s.decode()
    root=u32(0); v=deref(root+table(root)[0]); cat={}
    for k in range(u32(v)):
        t=deref(v+4+4*k); f=table(t)
        if len(f)<2 or not f[0] or not f[1]: continue
        nm=string(t+f[0])
        if nm: cat[u16(t+f[1])]=(nm,string(t+f[14]) if len(f)>14 and f[14] else None)
    return cat
if __name__=='__main__':
    c=char(open(sys.argv[1],'rb').read()); m=cmov(open(sys.argv[2],'rb').read())
    json.dump(c,open(os.path.join(sys.argv[3],'char_movesets.json'),'w')); json.dump(m,open(os.path.join(sys.argv[3],'move_catalog26.json'),'w'))
    print('wrestlers',len(c),'moves',len(m))

"""Histogram of Sound codec plugin ids / stream types across all banks. Usage: python3 -I codecs.py <sound dir>"""
import sys,os,struct,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from bnk import banks,hirc,objs
if __name__=='__main__':
    D=sys.argv[1]; c=collections.Counter(); ex={}
    for f in sorted(os.listdir(D)):
        if not f.endswith('.pck') or 'dialogue' in f: continue
        for fid,data in banks(os.path.join(D,f)):
            for body in hirc(data).get('HIRC',[]):
                for t,oid,b in objs(body):
                    if t==2:
                        pid,st=struct.unpack('<IB',b[:5]); k=(hex(pid),st); c[k]+=1; ex.setdefault(k,(f,fid,oid))
    for k,v in c.most_common(): print(k,v,ex[k])

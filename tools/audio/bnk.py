"""Extract soundbanks from an AKPK and summarise HIRC object types (Wwise bank version 128 in WWE 2K19).
Usage: python3 -I bnk.py <file.pck>..."""
import struct,sys,os,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from akpk import parse
HT={1:'State',2:'Sound',3:'Action',4:'Event',5:'RanSeq',6:'Switch',7:'ActorMixer',8:'Bus',9:'Layer',10:'MusicSegment',11:'MusicTrack',12:'MusicSwitch',13:'MusicRanSeq',14:'Attenuation',15:'DialogueEvent'}
def banks(p):
    ver,b,s,ne=parse(p); f=open(p,'rb')
    for fid,mul,sz,start,lang in b:
        f.seek(start*mul); yield fid,f.read(sz)
def hirc(data):
    o=0; res={}
    while o<len(data):
        tag=data[o:o+4]; ln=struct.unpack('<I',data[o+4:o+8])[0]; body=data[o+8:o+8+ln]
        res.setdefault(tag.decode('latin1'),[]).append(body); o+=8+ln
    return res
def objs(h):
    out=[]; n=struct.unpack('<I',h[:4])[0]; o=4
    for i in range(n):
        t=h[o]; ln=struct.unpack('<I',h[o+1:o+5])[0]; oid=struct.unpack('<I',h[o+5:o+9])[0]
        out.append((t,oid,h[o+9:o+5+ln])); o+=5+ln
    return out
if __name__=='__main__':
    for p in sys.argv[1:]:
        for fid,data in banks(p):
            ch=hirc(data); bk=ch.get('BKHD',[b''])[0]; c=collections.Counter()
            for body in ch.get('HIRC',[]):
                for t,oid,_ in objs(body): c[HT.get(t,t)]+=1
            print(f"{os.path.basename(p):18s} bank {fid:>10d} {len(data):>8d}B ver={struct.unpack('<I',bk[:4])[0] if bk else '?'} chunks={list(ch)} {dict(c)}")

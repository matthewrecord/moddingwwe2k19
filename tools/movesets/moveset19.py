"""2K19 .moveset (3464 bytes) reader/writer.
Layout: tools/movesets/layout_2k19.json = [offset, kind, field] in file order, derived from the Data Editor 2k19's own
reader (dataEditor.DataEditorPopulateMovesetData_2k19, javap; padding sizes from DataEditor.<clinit> byte arrays).
Move ids are BIG-endian u16; names/ids from the Data Editor's DataLists/(Original|Modded)/MovesID.data ("HHHH Name").
Validated: 97% of move slots hold a valid id over all 303 template movesets (AJ Styles: Calf Crusher / Fireman's Carry
Neckbreaker signatures, Phenomenal Forearm 2 / Styles Clash 1 finishers).
Usage: moveset19.py FILE.moveset [MovesID.data]  -> prints every move slot."""
import sys,json,struct,os
HERE=os.path.dirname(os.path.abspath(__file__))
LAYOUT=json.load(open(os.path.join(HERE,'layout_2k19.json')))
SLOTS=[(o,n) for o,k,n in LAYOUT if k=='S' and n.startswith('move') and not any(x in n for x in ('EMPTY','UNKNOWN','Unknown'))]
def load_names(path):
    d={}
    for l in open(path,encoding='latin1'):
        p=l.rstrip('\r\n').split(' ',1)
        if len(p)==2 and len(p[0])==4:
            try: d[int(p[0],16)]=p[1]
            except ValueError: pass
    return d
def read(path):
    b=open(path,'rb').read(); assert len(b)==3464, len(b)
    return {n:struct.unpack_from('>H',b,o)[0] for o,n in SLOTS}
def write(base_path,moves,out_path):
    """copy base .moveset and overwrite the named move slots (values = 2K19 move ids)"""
    b=bytearray(open(base_path,'rb').read()); off={n:o for o,n in SLOTS}
    for n,v in moves.items(): struct.pack_into('>H',b,off[n],v)
    open(out_path,'wb').write(b)
if __name__=='__main__':
    names=load_names(sys.argv[2]) if len(sys.argv)>2 else {}
    for n,v in read(sys.argv[1]).items(): print('%-45s %04X %s'%(n,v,names.get(v,'')))

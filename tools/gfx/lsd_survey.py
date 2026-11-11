import sys,struct,zlib,re
sys.path.insert(0,'/home/claude/moddingwwe2k19/tools/lib')
from yukes import HSPC,SHDC
def lists(p):
    b=open(p,'rb').read(); H=HSPC(b); S=SHDC(H.files[0]['data'])
    names=[]
    try:
        for m in re.finditer(rb'[\w/]+\.lsd',zlib.decompressobj().decompress(H.tail[H.tail.find(b'\x78'):]) if b'\x78' in H.tail else b''): names.append(m.group().decode())
    except Exception as e: pass
    return S,names,H
U='/mnt/user-data/uploads/common/'
for pat in ['','_p10','_p20','_p30']:
    for inst in ['WWE 2K19','WWE 2K19 - unmodded']:
        S,names,H=lists(f'{U}{inst}/pac/menu/cae_item{pat}.pac')
        row=[]
        for f in S.files:
            d=f['data']
            if len(d)>=4:
                n,t=struct.unpack_from('<HH',d,0); es=(len(d)-4)//n if n else 0
                row.append(f"{f['id']}:{n}/{t}x{es}")
        print(inst[-8:],pat or 'base',len(S.files),' '.join(row)); 
        if inst=='WWE 2K19' and pat=='': print('dir',S.dir[:600]); print('tail',H.tail[:80])

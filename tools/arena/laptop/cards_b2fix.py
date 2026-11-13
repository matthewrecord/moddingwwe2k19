import shdc2,hashlib,shutil,os,struct,zlib,sys,glob
from yukes import HSPC
from epk import payload
G='../../WWE 2K19/'; C=G+'../WWE2K19_arena_work/cards/'; MU='pac/menu/win/Assets/wwe19_anime/match_up/'
def zw(d): z=zlib.compress(d,6); return b'ZLIB'+struct.pack('<III',0x1230,len(z),len(d))+z
card=lambda n: shdc2.files(HSPC(open(C+n,'rb').read()).files[0]['data'])
NN=open(C+'layout_noname.zlib','rb').read()
for s in map(int,sys.argv[1:]):
    rel=MU+os.path.basename(glob.glob(G+MU+'ltag_%03d_*_win.pac'%s)[0]); b=G+'../WWE2K19_arena_work/backup_batch2/'+rel
    os.makedirs(os.path.dirname(b),exist_ok=True)
    if not os.path.exists(b): shutil.copy2(G+rel,b)
    b2=G+'../WWE2K19_arena_work/backup_b2fix/'+os.path.basename(rel)
    if not os.path.exists(b2): shutil.copy2(G+rel,b2)
    if s in (139,149): mv=zw(payload(open(glob.glob(G+'pac/mov/ar_mini/0*%d.pac'%s)[0],'rb').read()))
    elif s in (159,107): mv=card('card_003dyn.pac')[1]
    elif s==112: mv=card('card_010rev.pac')[1]
    elif s==133: mv=card('card_014fg.pac')[1]
    rep={1:mv,3:open(C+'fg_%d.zlib'%s,'rb').read()}
    rep[7]=NN
    H=HSPC(open(b,'rb').read()); out=H.replace(0,shdc2.build(H.files[0]['data'],rep)); open(G+rel,'wb').write(out); print(s,hashlib.md5(out).hexdigest()[:8],len(out))

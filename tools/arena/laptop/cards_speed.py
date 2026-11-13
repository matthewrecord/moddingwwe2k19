"""Change a match card's movie playback rate by editing the Bink header fps (0x1C num, 0x20 den). usage: cards_speed.py slot=fps_num/den ..."""
import shdc2,os,struct,zlib,sys,glob,shutil,hashlib
from yukes import HSPC
G='../../WWE 2K19/'; MU='pac/menu/win/Assets/wwe19_anime/match_up/'; BK='../backup_aewfx/'
def zw(d): z=zlib.compress(d,6); return b'ZLIB'+struct.pack('<III',0x1230,len(z),len(d))+z
for a in sys.argv[1:]:
    s,f=a.split('='); s=int(s); n,d=map(int,f.split('/'))
    rel=MU+os.path.basename(glob.glob(G+MU+'ltag_%03d_*_win.pac'%s)[0]); b=BK+rel
    os.makedirs(os.path.dirname(b),exist_ok=True)
    if not os.path.exists(b): shutil.copy2(G+rel,b)
    H=HSPC(open(b,'rb').read()); fs=shdc2.files(H.files[0]['data']); m=fs[1]
    raw=bytearray(zlib.decompress(m[16:]) if m[:4]==b'ZLIB' else m); fr,=struct.unpack_from('<I',raw,8)
    struct.pack_into('<II',raw,0x1C,n,d)
    out=H.replace(0,shdc2.build(H.files[0]['data'],{1:zw(bytes(raw)) if m[:4]==b'ZLIB' else bytes(raw)}))
    open(G+rel,'wb').write(out); print(s,'fps',n/d,'dur %.2fs'%(fr*d/n),hashlib.md5(out).hexdigest()[:8])

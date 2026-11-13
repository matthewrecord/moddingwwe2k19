import shdc2,os,struct,zlib,sys,glob
from yukes import HSPC
from epk import payload
G='../../WWE 2K19/'; MU='pac/menu/win/Assets/wwe19_anime/match_up/'
def unz(d): return zlib.decompress(d[16:]) if d[:4]==b'ZLIB' else d
def info(d):
    sig=d[:4]; fr,=struct.unpack_from('<I',d,8); w,h,n,den=struct.unpack_from('<IIII',d,0x14)
    return f'{sig} frames={fr} {w}x{h} fps={n}/{den}={n/den:.2f} dur={fr*den/n:.2f}s'
for s in map(int,sys.argv[1:]):
    f=glob.glob(G+MU+'ltag_%03d_*_win.pac'%s)[0]
    fs=shdc2.files(HSPC(open(f,'rb').read()).files[0]['data'])
    print(s,'card',info(unz(fs[1])))
    for t in ('transition',):
        for p in glob.glob(G+'pac/mov/%s/0*%d.pac'%(t,s)): print('   ',t,os.path.basename(p),info(unz(payload(open(p,'rb').read()))))

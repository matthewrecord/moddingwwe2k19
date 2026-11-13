import sys,struct,zlib,ooz; sys.path[:0]=['/home/claude/moddingwwe2k19/tools/arena','/home/claude/moddingwwe2k19/tools/lib']
import shdc2; from yukes import HSPC
def inner(f):
    m=f[:4]
    if m==b'ZLIB': return m,zlib.decompress(f[16:])
    if m==b'OODL': raw,cl=struct.unpack_from('<II',f,0x10); return m,ooz.decompress(f[0x18:0x18+cl],raw)
    return b'raw',f
def desc(f):
    m,x=inner(f); t=x[:4]
    if t==b'DDS ': t+=b' %dx%d'%struct.unpack_from('<II',x,12)[::-1]
    if t[:3] in (b'BIK',b'KB2'): t+=b' %dx%d f%d'%(struct.unpack_from('<II',x,0x14)+struct.unpack_from('<I',x,8))
    return '%s/%s/%d'%(m.decode(),t.decode('latin1'),len(x))
if __name__=='__main__':
 for n in sys.argv[1:]:
    H=HSPC(open(n,'rb').read()); print(n.split('/')[-1],len(H.files))
    for k,f in shdc2.files(H.files[0]['data']).items(): print('  ',k,desc(f))

"""Batch 4 card builder: cardb4.py <template card> <movie: path|'keep'|card.pac:id> <fg image | card.pac:id> <out.pac>
Template file 3 (OODL/ZLIB DDS) is the foreground strip: fg cropped to its alpha>16 rows, padded/cropped to the
template aspect, resized, BC7 with the template's DDS header. Movie goes into file 1 (ZLIB-wrapped)."""
import sys,io,zlib,struct,numpy as np,etcpak; sys.path[:0]=['/home/claude/moddingwwe2k19/tools/arena','/home/claude/moddingwwe2k19/tools/lib']
import shdc2; from yukes import HSPC; from PIL import Image; from cardinfo import inner
import texture2ddecoder as t2
def zw(d): z=zlib.compress(d,6); return b'ZLIB'+struct.pack('<III',0x1230,len(z),len(d))+z
def cardfile(spec):
    p,i=spec.rsplit(':',1); return inner(shdc2.files(HSPC(open(p,'rb').read()).files[0]['data'])[int(i)])[1]
def img(spec):
    if spec.endswith('.png'): return Image.open(spec).convert('RGBA')
    x=cardfile(spec)
    if x[:4]==b'\x89PNG': return Image.open(io.BytesIO(x)).convert('RGBA')
    h,w=struct.unpack_from('<II',x,12); f=x[84:88]; off=128
    if f==b'DX10': f=struct.unpack_from('<I',x,128)[0]; off=148
    dec={b'DXT5':t2.decode_bc3,b'DXT1':t2.decode_bc1,98:t2.decode_bc7,99:t2.decode_bc7,77:t2.decode_bc3}[f]
    return Image.frombytes('RGBA',(w,h),dec(x[off:],w,h),'raw','BGRA')
tp,mv,fg,out=sys.argv[1:5]
H=HSPC(open(tp,'rb').read()); d=H.files[0]['data']; F=shdc2.files(d)
t=inner(F[3])[1]; th,tw=struct.unpack_from('<II',t,12); assert t[84:88]==b'DX10' and struct.unpack_from('<I',t,128)[0] in (98,99), t[84:88]
A=tw/th; im=img(fg); a=np.array(im)[:,:,3]; rows=np.where((a>16).any(1))[0]; im=im.crop((0,rows[0],im.width,rows[-1]+1))
W,Hh=im.size
if W/Hh<A: c=Image.new('RGBA',(round(Hh*A),Hh),(0,0,0,0)); c.paste(im,((c.width-W)//2,0)); im=c
else: im=im.crop((0,Hh-round(W/A),W,Hh))
im=im.resize((tw,th),Image.LANCZOS); im.save(out+'.fg.png')
rep={3:zw(t[:148]+etcpak.compress_bc7(np.array(im).tobytes(),tw,th))}
if mv!='keep': rep[1]=zw(cardfile(mv) if mv.endswith(tuple(':%d'%i for i in range(9))) else open(mv,'rb').read())
res=H.replace(0,shdc2.build(d,rep)); open(out,'wb').write(res); print(out,len(res))

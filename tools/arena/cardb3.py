"""Batch 3 card builder: cardb3.py <template card.pac> <movie.bik> <fg image> <fg template .zlib> <out.pac>
Card file 1 = ZLIB-wrapped Bink movie; file 3 = foreground: crop to the alpha bounding box (fit2), pad to 6.7:1
(centred), resize to the template DDS size, BC7. Other files (layout with names, fonts) stay as in the template."""
import sys,zlib,struct,numpy as np,etcpak; sys.path[:0]=['/home/claude/moddingwwe2k19/tools/arena','/home/claude/moddingwwe2k19/tools/lib']
import shdc2; from yukes import HSPC; from PIL import Image
def zw(d): z=zlib.compress(d,6); return b'ZLIB'+struct.pack('<III',0x1230,len(z),len(d))+z
tp,mv,fgp,ft,out=sys.argv[1:6]; A=6.7
im=Image.open(fgp).convert('RGBA'); x0,y0,x1,y1=im.getbbox(); im=im.crop((0,y0,im.width,y1))
W,H=im.size
if W/H<A: c=Image.new('RGBA',(round(H*A),H),(0,0,0,0)); c.paste(im,((c.width-W)//2,0)); im=c
else: im=im.crop((0,H-round(W/A),W,H))
t=zlib.decompress(open(ft,'rb').read()[16:]); th,tw=struct.unpack_from('<II',t,12)
im=im.resize((tw,th),Image.LANCZOS); im.save(out+'.fg.png')
dds=t[:148]+etcpak.compress_bc7(np.array(im).tobytes(),tw,th)
H=HSPC(open(tp,'rb').read()); res=H.replace(0,shdc2.build(H.files[0]['data'],{1:zw(open(mv,'rb').read()),3:zw(dds)}))
open(out,'wb').write(res); print(out,len(res))

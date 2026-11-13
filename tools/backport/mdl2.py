import struct,sys
b=open(sys.argv[1],'rb').read()
ch={};o=0x24
while o+8<=len(b):
    t=b[o:o+4]; sz,=struct.unpack_from('<I',b,o+4); ch[t]=(o+8,sz); o+=8+sz
    if t==b'END!':break
mo,ms=ch[b'MBfD']
for k in range(0,0x180,16):
    w=b[mo+k:mo+k+16]
    print(hex(k),w.hex(' '),struct.unpack('<4I',w),['%.3g'%x for x in struct.unpack('<4f',w)])
lo,ls=ch[b'LODs']; print('LODs'); 
for k in range(0,0x60,16): print(b[lo+k:lo+k+16].hex(' '))

import struct,sys
b=open(sys.argv[1],'rb').read()
o=0x24
while o+8<=len(b):
    t=b[o:o+4]; sz,=struct.unpack_from('<I',b,o+4)
    print(hex(o),t,sz, b[o+8:o+56].hex(' '))
    if not all(32<=c<127 for c in t): break
    o+=8+sz
print('end',hex(o),len(b))

import struct,re,sys
def parse(b):
    n,=struct.unpack_from('<I',b,0); E=[]
    for k in range(n):
        r=4+k*32; name=b[r+16:r+28].split(b'\0')[0].decode() if False else b[r+12:r+28].split(b'\0')[0].decode()
        E.append((name,)+struct.unpack_from('<3I',b,r))
    dds=[m.start() for m in re.finditer(rb'DDS \x7c\x00\x00\x00',b)]
    out=[]
    for e,o in zip(E,dds):
        h,w=struct.unpack_from('<2I',b,o+12); mips,=struct.unpack_from('<I',b,o+28); fourcc=b[o+84:o+88]
        out.append(dict(name=e[0],off=o,w=w,h=h,mips=mips,fmt=fourcc.decode('latin1'),raw=e[1:]))
    return out,len(E),len(dds)
if __name__=='__main__':
    T,ne,nd=parse(open(sys.argv[1],'rb').read()); print(ne,'entries',nd,'dds')
    for t in T: print('%-18s %5dx%-5d %-4s mips %2d  %s'%(t['name'],t['w'],t['h'],t['fmt'],t['mips'],[hex(x) for x in t['raw']]))

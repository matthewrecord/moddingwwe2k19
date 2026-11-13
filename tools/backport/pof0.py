import struct
def decode(t):
    assert t[:4]==b'POF0'; n,=struct.unpack_from('>I',t,4); d=t[8:8+n]; i=0; pos=0; out=[]
    while i<len(d):
        c=d[i]; ty=c&0xC0
        if ty==0x40: v=c&0x3F; i+=1
        elif ty==0x80: v=((c&0x3F)<<8)|d[i+1]; i+=2
        elif ty==0xC0: v=((c&0x3F)<<24)|(d[i+1]<<16)|(d[i+2]<<8)|d[i+3]; i+=4
        else: break
        pos+=v*4; out.append(pos)
    return out
def encode(offs,two_byte_limit=0x3000):
    d=bytearray(); prev=0
    for o in sorted(offs):
        v=(o-prev)//4; assert (o-prev)%4==0 and v>0; prev=o
        if v<0x3F: d.append(0x40|v)
        elif v<two_byte_limit: d+=bytes([0x80|(v>>8),v&0xFF])
        else: d+=bytes([0xC0|(v>>24),(v>>16)&0xFF,(v>>8)&0xFF,v&0xFF])
    d+=b'\0'*((-len(d))%4)
    return b'POF0'+struct.pack('>I',len(d))+bytes(d)

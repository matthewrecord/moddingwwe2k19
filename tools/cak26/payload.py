"""2K26 .cak payload recovery (Python port of AuroraForge NT100 cak-foundry/tools/aur-39d/Program.cs, GPL-3.0-or-later,
VikingStudios / Dave Granlet). Catalog (keys, file table, chunk ends, flags) comes from AuroraForge's cak-reader.js run on
the PC (tools/cak26/cakindex.js, cakdump.js). Here: per-file key derivation, first-256-byte unscramble, chunked Oodle (ooz)."""
import struct,ooz
M64=(1<<64)-1
def crc32c_word(seed,value):
    crc=seed&0xffffffff
    for i in range(4):
        crc^=(value>>(i*8))&0xff
        for _ in range(8): crc=(crc>>1)^(0x82f63b78 if crc&1 else 0)
    return crc
def fnv_byte(h,b):
    sb=b-256 if b>=128 else b
    return ((h^(sb&M64))*0x100000001b3)&M64
def s64(v32): v32&=0xffffffff; return (v32-(1<<32) if v32&0x80000000 else v32)&M64
def derive_key(archive_key,stored_size,offset):
    ak=archive_key&0xffffffff
    mixed=(~((~ak&M64)^offset))&M64
    h=0xcbf29ce484222325
    for i in range(4): h=fnv_byte(h,(ak>>(i*8))&0xff)
    inv=(~stored_size)&0xffffffff
    for i in range(4): h=fnv_byte(h,(inv>>(i*8))&0xff)
    for i in range(4): h=fnv_byte(h,(mixed>>(i*8))&0xff)
    sm=mixed-(1<<64) if mixed>>63 else mixed
    second=((sm>>32)&M64)^h
    for i in range(4): second=fnv_byte(second,0)
    for v in (s64(inv),s64(ak),s64(crc32c_word(inv,ak)),s64(crc32c_word(mixed&0xffffffff,(sm>>32)&0xffffffff))):
        for i in range(4): second=fnv_byte(second,(v>>(i*8))&0xff)
    b=second.to_bytes(8,'little')
    f=(b[1]+(b[0]<<4))<<4; f=(f+b[2])<<4; f=(f+b[3])<<4; f=(f+b[4])<<4; f+=b[5]; f&=0xffffffff
    high=(f>>24)&0xf0; nxt=((((f^high)<<4)&0xffffffff)+b[6])&0xffffffff
    high=(nxt>>24)&0xf0; final=((((nxt^high)<<4)&0xffffffff)+b[7])&0xffffffff
    fh=(final>>24)&0xf0; low=((~(fh<<24))&(final^fh)&0xffffffff)^(second&0xffffffff)
    return ((~(second>>32))&0xffffffff)^low
def rol8(v,c): c&=7; return ((v<<c)|(v>>((8-c)&7)))&0xff
def ror8(v,c): c&=7; return ((v>>c)|(v<<((8-c)&7)))&0xff
def recover(data,key):
    inv=(~key)&0xffffffff; d=bytearray(data)
    for i in range(min(256,len(d))):
        r=ror8(d[i],~(i+1)); mask=((((inv>>(((i-1)&3)*8))&0xff)+1+i)&0xff)
        d[i]=rol8(mask^r,(i-1)&7)
    return bytes(d)
def payload(raw,m):
    d=raw
    if m['protected']: d=recover(d,derive_key(m['key'],m['storedSize'],int(m['offset'])))
    if not m['compressed']: return d
    exp=m['expandedSize']; ch=m['chunks']
    if len(ch)<=1: return ooz.decompress(d,exp)
    out=[];start=0;rem=exp
    for c in ch:
        end=c['end']; n=min(0x100000,rem); seg=d[start:end]
        out.append(seg if len(seg)==n else ooz.decompress(seg,n)); start=end; rem-=n
    return b''.join(out)

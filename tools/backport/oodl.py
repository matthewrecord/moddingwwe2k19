import struct,re,ooz
def blocks(b):
    out=[]
    for m in re.finditer(rb'OODL\x00\x00\x00\x00',b):
        i=m.start(); fl,tag,rl,sl=struct.unpack_from('<I4sII',b,i+8)
        if tag!=b'KRKN': continue
        for raw in (rl-0x14,rl):
            try:
                d=ooz.decompress(b[i+24:i+24+sl],raw)
                if d and len(d)==raw: out.append((i,d)); break
            except Exception as e: pass
        else: out.append((i,None))
    return out

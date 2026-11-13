"""Write a 2K19 character pac the way his ports are built: EPK8 header + EMD entry (virtual name) + PACH table of
ZLIB blocks. Layout measured on his 6 ports (2026-11-13)."""
import struct,zlib
def read(path):
    b=open(path,'rb').read(); assert b[:4]==b'EPK8' and b[0x800:0x804]==b'EMD '
    n,=struct.unpack_from('<I',b,0x4004); E=[struct.unpack_from('<3I',b,0x4008+12*i) for i in range(n)]; base=0x4008+12*n
    files=[]
    for fid,o,s in E:
        blk=b[base+o:base+o+s]; assert blk[:4]==b'ZLIB'; a,c,u=struct.unpack_from('<3I',blk,4)
        files.append((fid,zlib.decompress(blk[16:16+c]),a))
    return dict(header=b[:0x4000],files=files,name=b[0x80C:0x814])
def build(header,files,name=None,level=6):
    """header: the first 0x4000 bytes of a template pac; files: list of (id, raw bytes[, zlib tag word])."""
    n=len(files); body=bytearray(); E=[]
    for f in files:
        fid,raw=f[0],f[1]; tag=f[2] if len(f)>2 else 0x1230
        body+=b'\0'*((-len(body))%4); comp=zlib.compress(raw,level)
        blk=b'ZLIB'+struct.pack('<3I',tag,len(comp),len(raw))+comp
        E.append((fid,len(body),len(blk))); body+=blk
    pach=b'PACH'+struct.pack('<I',n)+b''.join(struct.pack('<3I',*e) for e in E)
    out=bytearray(header[:0x4000])+pach+body
    out+=b'\0'*((-len(out))%0x800)
    sz=len(out)-0x4800
    struct.pack_into('<I',out,8,sz); struct.pack_into('<I',out,0x818,sz//256)
    if name is not None: out[0x80C:0x814]=name
    return bytes(out)

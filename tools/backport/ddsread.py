"""Decode a DDS (DXT1/DXT5/ATI1/ATI2/BC7, legacy or DX10 header) to RGBA uint8 (top mip)."""
import struct,numpy as np,texture2ddecoder as t
def decode(dds):
    h,w=struct.unpack_from('<2I',dds,12); fc=dds[84:88]; o=128
    if fc==b'DX10': fmt,=struct.unpack_from('<I',dds,128); o=148; fc={98:'BC7',71:'BC1',80:'BC4',83:'BC5',77:'BC3'}.get(fmt,fmt)
    else: fc=fc.decode()
    f={'DXT1':(t.decode_bc1,8),'BC1':(t.decode_bc1,8),'DXT5':(t.decode_bc3,16),'BC3':(t.decode_bc3,16),'ATI2':(t.decode_bc5,16),'BC5':(t.decode_bc5,16),
       'ATI1':(t.decode_bc4,8),'BC4':(t.decode_bc4,8),'BC7':(t.decode_bc7,16)}[fc]
    n=(w//4)*(h//4)*f[1]; raw=f[0](dds[o:o+n],w,h)
    a=np.frombuffer(raw,'u1').reshape(h,w,4)[...,[2,1,0,3]]   # BGRA -> RGBA
    return fc,a

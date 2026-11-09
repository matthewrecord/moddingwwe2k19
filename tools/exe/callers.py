# Call sites of imported functions. Usage: python3 callers.py <exe> <IAT-VA-hex>...
import sys,pefile,struct
exe=sys.argv[1]; iats=[int(x,16) for x in sys.argv[2:]]
pe=pefile.PE(exe,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
t=[s for s in pe.sections if s.Name.startswith(b'.text')][0]; code=t.get_data(); tva=base+t.VirtualAddress
for i in range(len(code)-6):
    if code[i]==0xff and code[i+1]==0x15:
        d=struct.unpack('<i',code[i+2:i+6])[0]; tgt=tva+i+6+d
        if tgt in iats: print(hex(tva+i),'call',hex(tgt))

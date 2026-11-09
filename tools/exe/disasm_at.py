# Disassemble with string annotations. Usage: python3 disasm_at.py <exe> <VA-hex> <len-hex>
import sys,pefile,capstone
exe=sys.argv[1]; a=int(sys.argv[2],16); n=int(sys.argv[3],16)
pe=pefile.PE(exe,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
b=open(exe,'rb').read()
def va2off(va):
    rva=va-base
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+s.Misc_VirtualSize: return s.PointerToRawData+rva-s.VirtualAddress
def cstr(va):
    o=va2off(va)
    if o is None: return None
    e=b.find(b'\0',o); s=b[o:e]
    if 2<len(s)<80 and all(32<=c<127 for c in s): return s.decode()
    try:
        t=b[o:o+120].decode('utf-16le').split('\0')[0]
        if 2<len(t)<60 and t.isprintable(): return 'L"'+t+'"'
    except Exception: pass
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
o=va2off(a)
for ins in md.disasm(b[o:o+n],a):
    note=''
    if 'rip +' in ins.op_str:
        try:
            d=int(ins.op_str.split('rip + ')[1].split(']')[0],16); t=ins.address+ins.size+d; s=cstr(t); note=f'  ; {hex(t)} {s!r}' if s else f'  ; {hex(t)}'
        except Exception: pass
    print(hex(ins.address),ins.mnemonic,ins.op_str,note)

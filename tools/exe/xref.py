# Find code that references data at given file offsets (RIP-relative). Usage: python3 xref.py <exe> <fileoff-hex>...
import sys,pefile,capstone,struct
exe=sys.argv[1]; targets=[int(x,16) for x in sys.argv[2:]]
pe=pefile.PE(exe,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
text=[s for s in pe.sections if s.Name.startswith(b'.text')][0]
code=text.get_data(); tva=base+text.VirtualAddress
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData<=o<s.PointerToRawData+s.SizeOfRawData: return base+s.VirtualAddress+o-s.PointerToRawData
tv=[off2va(t) for t in targets]; print('target VAs',[hex(x) for x in tv])
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
hits=[]
for i in range(len(code)-7):
    d=struct.unpack('<i',code[i:i+4])[0]
    for L in (0,1,2,3,4):
        va_end=tva+i+4+L
        if va_end+d in tv: hits.append((tva+i,va_end+d))
print('candidate refs',len(hits)); seen=set()
for h,t in hits[:12]:
    start=h-0x80
    for ins in md.disasm(code[start-tva:start-tva+0x140],start):
        if h-12<=ins.address<=h and 'rip' in ins.op_str and ins.address not in seen:
            seen.add(ins.address); print('REF',hex(ins.address),ins.mnemonic,ins.op_str,'->',hex(t))

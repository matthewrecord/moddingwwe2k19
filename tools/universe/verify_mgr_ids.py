import sys,struct
sys.path.insert(0,'/home/claude/moddingwwe2k19/tools/universe')
from savedecode import decode,chunks
def body(p):
    d=decode(open(p,'rb').read())
    for o,t,s,b in chunks(d):
        if t.startswith('MAINBODY') and b: return b
for p in sys.argv[1:]:
    b=body(p); base=0x88e5b0-170*0xD88; pb=0x117f0-148*484
    n=sum(1 for i in range(509) if any(struct.unpack_from('<I',b,base+i*0xD88+0x58+4*k)[0] not in (1024,0xffffffff,0) and struct.unpack_from('<I',b,base+i*0xD88+0x58+4*k)[0]<1100 for k in range(3)))
    ids={i:struct.unpack_from('<I',b,pb+i*484)[0] for i in (112,125,129,138,141,156)}
    mg=lambda i:[struct.unpack_from('<I',b,base+i*0xD88+0x58+4*k)[0] for k in range(3)]
    print(p.split('/')[-1],'records w/ managers',n,'ids',ids,'Cass',mg(112),'Sky',mg(141),'Trent',mg(170))

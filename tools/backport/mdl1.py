import struct,sys
b=open(sys.argv[1],'rb').read()
ch={};o=0x24
while o+8<=len(b):
    t=b[o:o+4]; sz,=struct.unpack_from('<I',b,o+4); ch[t]=(o+8,sz); o+=8+sz
    if t==b'END!':break
to,ts=ch[b'TEXT']; n,=struct.unpack_from('<I',b,to)
offs=struct.unpack_from('<%dI'%n,b,to+4); base=to+4+4*n
S=[b[base+x:b.index(b'\0',base+x)].decode() for x in offs]
print(n,S[:40]); print(S[-60:])
bo,bs=ch[b'BONE']; print(b[bo:bo+12].hex(' '))
for k in range(4): print(b[bo+12+k*33:bo+12+k*33+33].hex(' '))
print('---bones')
n=struct.unpack_from('<I',b,bo+8)[0]; R=[]
for i in range(n):
    r=bo+12+i*33
    fl,idx,par=struct.unpack_from('<Ihh',b,r); f=struct.unpack_from('<6f',b,r+8); x=b[r+32]
    R.append((idx,par,f,x,fl))
for i in [0,1,2,12,13,14,15,16,17] + list(range(n-5,n)): print(i,S[i+1],R[i][0],R[i][1],['%.3f'%v for v in R[i][2]],R[i][3],hex(R[i][4]))

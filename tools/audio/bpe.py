"""Decode Yuke's 'BPE ' compression (Philip Gage byte-pair encoding, little-endian block sizes), as used in
pac/root/_startup_audio_pNN.pac (SHDC). Header: 'BPE ', u32 0x100, u32 compressed, u32 uncompressed, u32 checksum;
data starts at BPE+0x10. Verified 2026-11-09: _startup_audio_p30.pac -> 441,685 bytes (= header size).
Usage: python3 -I bpe.py <file> <out.bin>"""
import struct,sys
def expand(src,pos,outsize):
    out=bytearray(); n=len(src)
    while pos<n and len(out)<outsize:
        left=list(range(256)); right=[0]*256; c=0
        while True:
            count=src[pos]; pos+=1
            if count>127: c+=count-127; count=0
            if c==256: break
            for _ in range(count+1):
                left[c]=src[pos]; pos+=1
                if left[c]!=c: right[c]=src[pos]; pos+=1
                c+=1
            if c==256: break
        size=src[pos]|src[pos+1]<<8; pos+=2
        stack=[]; i=0
        while i<size or stack:
            if stack: c=stack.pop()
            else: c=src[pos]; pos+=1; i+=1
            if c==left[c]: out.append(c)
            else: stack.append(right[c]); stack.append(left[c])
    return bytes(out),pos
if __name__=='__main__':
    b=open(sys.argv[1],'rb').read(); o=b.find(b'BPE ')
    h=struct.unpack('<4I',b[o+4:o+20]); d,p=expand(b,o+16,h[2])
    print('BPE',[hex(x) for x in h],'out',len(d),'ok' if len(d)==h[2] else 'SIZE MISMATCH')
    open(sys.argv[2],'wb').write(d)

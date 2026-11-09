"""Dump every HIRC object of one bank inside a .pck. Usage: python3 -I bankdump.py <pck> <bank_id> [event names...]"""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from bnk import banks,hirc,objs,HT
from evmatch import fnv
if __name__=='__main__':
    pck=sys.argv[1]; want=int(sys.argv[2]); names=sys.argv[3:]
    for fid,data in banks(pck):
        if fid!=want: continue
        ch=hirc(data); print('chunks',list(ch)); print('BKHD',ch['BKHD'][0].hex())
        nm={fnv(n):n for n in names}
        for t,oid,b in objs(ch['HIRC'][0]):
            print(f"{HT.get(t,t):11s} {oid:>10d} {nm.get(oid,''):24s} len={len(b):4d} {b.hex()}")

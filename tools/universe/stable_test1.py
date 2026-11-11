"""Experiment 1 for the team import (option A): put #DIY (Johnny Gargano 691 + Tommaso Ciampa 461) into the empty
entry 23 of the default Universe team list in pac/universe/wunistable.pac (LBTS table stored uncompressed at
0x1864: 'LBTS', u32 0x110 entry size, u32 100 entries, pad; entries of 0x110 bytes). Entry copied from entry 2
(THE REVIVAL) with members replaced, logo 0xFFFF. Same file length, in-place.
Question it answers: which field gives the team its name (+0x18 = 1343 kept from THE REVIVAL)."""
import struct, sys
src, dst = sys.argv[1], sys.argv[2]
b = bytearray(open(src, 'rb').read()); B, E = 0x1864 + 16, 0x110
assert b[0x1864:0x1868] == b'LBTS'
e = bytearray(b[B + 2 * E:B + 3 * E])
for k, m in enumerate([691, 461, 0x400, 0x400, 0x400]): struct.pack_into('<H', e, 2 * k, m)
struct.pack_into('<H', e, 0x10, 0xFFFF)
b[B + 23 * E:B + 24 * E] = e
open(dst, 'wb').write(b)

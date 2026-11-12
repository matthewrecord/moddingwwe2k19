"""Re-stamp a crowd mod (arcrowdNNNNN.pac) so it loads as a different crowd id.
usage: crowd_reslot.py <mod.pac> <stock target crowd.pac> <out.pac>
A crowd file carries its id in 5 places: the HSPC header u32 @0x10, two 8-byte name hashes @0x800 and @0x814,
and the id u32 @+0x10 of each of the two inner SHDC packs. All are copied from the stock file of the target id.
Confirmed in game 2026-11-12 (AEW Crowd Shirts, crowd 10 -> 3)."""
import re, sys
mod, tgt, out = sys.argv[1:4]
s = open(tgt, 'rb').read(); b = bytearray(open(mod, 'rb').read()); old = b[0x10:0x14]
b[0x10:0x14] = s[0x10:0x14]; b[0x800:0x808] = s[0x800:0x808]; b[0x814:0x81c] = s[0x814:0x81c]
for x, y in zip([m.start() for m in re.finditer(rb'SHDC', b)], [m.start() for m in re.finditer(rb'SHDC', s)]):
    b[x + 0x10:x + 0x14] = s[y + 0x10:y + 0x14]
assert old == s[0x10:0x14] or b.count(old) == 0, 'old id still present'
open(out, 'wb').write(b)

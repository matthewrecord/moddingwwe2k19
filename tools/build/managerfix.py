"""Clear stale manager links in profile_pro.pac (NGlobalData::InitCharProfile source; 0x488-byte records,
header u16 8, u16 0x488, i16 index, u16 flag (index += 0x1cb when set); managers = 3 x u32 at +0x3B8, 0x400 = none).
Rule (Matthew 2026-11-11): clear when either side's slot was replaced (CCT data.xml vs replaced_data.xml), plus the
extra pairs; keep the keep pairs.
usage: managerfix.py profile_pro.pac pofo_live.bin cct_slots.tsv out.pac > report.tsv"""
import sys, re, struct
pac, pofo, slots, out = sys.argv[1:5]
d = bytearray(open(pac, 'rb').read()); P = open(pofo, 'rb').read()
ids = [struct.unpack_from('<H', P, x * 484)[0] for x in range(509)]
rep, name = {}, {}
for l in open(slots, encoding='utf-8'):
    s, i, o, c = (l.rstrip('\n').split('\t') + [''] * 4)[:4]
    rep[int(i)] = bool(c) and c.strip().lower() != o.strip().lower(); name[int(i)] = c or o
keep = {frozenset(p) for p in [(386, 387), (429, 578), (143, 620), (734, 737), (801, 802), (ids[215], 145)]}
extra = {frozenset(p) for p in [(398, 113), (275, 278), (279, 359)]}
print('index\towner\tslot\tmanager\taction')
for m in re.finditer(re.escape(bytes.fromhex('08008804')), d):
    h = m.start(); idx, fl = struct.unpack_from('<hH', d, h + 4)
    if idx < 0: continue
    if fl: idx += 0x1cb
    if idx >= 509: continue
    me = ids[idx]
    for k, off in enumerate((0x3b8, 0x3bc, 0x3c0)):
        v = struct.unpack_from('<I', d, h + off)[0]
        if v in (0x400, 0xffffffff, 0) or v > 2000: continue
        pr = frozenset((me, v))
        clear = pr not in keep and (rep.get(me) or rep.get(v) or pr in extra)
        if clear: struct.pack_into('<I', d, h + off, 0x400)
        print(f'{idx}\t{name.get(me, me)}\t{k}\t{name.get(v, v)}\t{"clear" if clear else "keep"}')
open(out, 'wb').write(d)

"""List arena slots from pac/root/misc01_start.pac.   python3 arena_slots.py <misc01_start.pac> <string_win.pac>
Table = SHDC file id 2 ('STG\\0', u32, u32, then 124-byte rows): u32 name string id, u16 arena slot, u16 select
number, u16 a1, u16 a2, ... (rest not decoded yet). Rows are stored in name order."""
import struct, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from yukes import HSPC, SHDC, string_table_parse
def rows(p):
    S = SHDC(HSPC(open(p, 'rb').read()).files[0]['data']); f = [x for x in S.files if x['id'] == 2][0]['data']
    return [f[12 + 124 * i:12 + 124 * (i + 1)] for i in range((len(f) - 12) // 124)]
def strings(p):
    S = SHDC(HSPC(open(p, 'rb').read()).files[0]['data']); _, e = string_table_parse(S.files[0]['data'])
    return {i: s.rstrip(b'\0').decode('latin1') for i, s in e}
if __name__ == '__main__':
    d = strings(sys.argv[2])
    for r in sorted(rows(sys.argv[1]), key=lambda r: struct.unpack_from('<H', r, 4)[0]):
        sid = struct.unpack_from('<I', r, 0)[0]; slot, sel, a1, a2 = struct.unpack_from('<4H', r, 4)
        print(f'{slot}\t{sel}\t{a1}\t{a2}\t{sid}\t{d.get(sid, "?")}')

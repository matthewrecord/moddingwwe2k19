"""Test build: AEW Dynamite '22 (Titavius) into arena slot 158 (Over the Limit '11) of the clean install.
Inputs staged from the laptop (see writeup/Arena_inventory.md); output tree in OUT mirrors the game folder."""
import os, sys, json, hashlib
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); sys.path.insert(0, os.path.join(H, '..', 'lib'))
from epk import payload, rewrap, build_single, rename, names
from tables import *
from yukes import HSPC, SHDC, string_table_parse, string_table_build
G = '/mnt/user-data/uploads/common/WWE 2K19/'; I = G + '_arena_work/in/t158/'; DY = G + '_arena_work/in/dyn22/'
OUT = sys.argv[1]; SLOT = 158; rd = lambda p: open(p, 'rb').read(); files = {}
def put(rel, data): files[rel] = data
# 1 stage + videos: keep slot 158's own containers, swap payloads
put('pac/arena/entrance/arentrance00158.pac', rewrap(rd(I + 'tgt_arentrance00158.pac'), payload(rd(I + 'arentrance00017.pac'))))
put('pac/mov/ar_wall/0000158.pac', rewrap(rd(I + 'tgt_ar_wall_0000158.pac'), payload(rd(DY + '000017.pac'))))
put('pac/mov/ar_mini/0000158.pac', rewrap(rd(I + 'tgt_ar_mini_0000158.pac'), payload(rd(DY + 'mini_000017.pac'))))
put('pac/mov/ar_apron/0000158.pac', rewrap(rd(I + 'tgt_ar_apron_0000158.pac'), payload(rd(DY + 'apron_000017.pac'))))
# 2 parts, renumbered to ids no kept arena uses (pack misc04), as named EPAC containers
tail = b'\0' * 0x800
PARTS = [('apron', 75, 7, 'AP'), ('barricade', 22, 6, 'BR'), ('ceilinglight', 20, 4, 'CL'), ('cornerpost', 7, 17, 'CP'),
         ('ringmat', 2, 7, 'RM'), ('spotlight', 20, 2, 'SP'), ('stadium', 29, 1, 'ST'), ('turnbuckle', 15, 13, 'TB')]
for cat, old, new, pre in PARTS:
    src = rd(I + 'ar%s%05d.pac' % (cat, old))
    put('pac/arena/%s/ar%s%05d.pac' % (cat, cat, new), build_single(b'EPAC', b'SGSN', (pre + '%02d' % new).encode(), payload(src), tail))
for rel in ('cornerpost/arcornerpostcm00002.pac', 'rope/arropecm00002.pac', 'turnbuckle/arturnbucklecm00002.pac'):
    put('pac/arena/' + rel, rd(I + rel.split('/')[1]))           # already named containers (CC/CO/CB00002), no clash
# 3 graphics: the mod's slot-3 Dynamite '22 set, renamed to slot 158's internal names
GD = 'mods/WWE 2K19 Unpacked Arena Graphics/pac/menu/win/Assets/wwe19_singleread/'
for cat, sub, h in (('locator', 'anime', b'BFEA212E'), ('match_result', 'anime', b'21831E42'), ('nameplate', 'anime', b'CE670CC9'), ('copyright', 'texture', b'94C1B3B8')):
    put(GD + "%s/%s/158 - Over the Limit '11.pac" % (sub, cat), rename(rd(I + 'g_%s.pac' % cat), [h]))
# 4 name string
sp = rd(G + 'mods/SuperString/pac/string/win/string_win.pac'); Hs = HSPC(sp); Ss = SHDC(Hs.files[0]['data'])
pre, ents = string_table_parse(Ss.files[0]['data']); d = dict(ents); SID = 48158; assert SID not in d
d[SID] = b"AEW DYNAMITE '22\0"; Ss.files[0]['data'] = string_table_build(pre, sorted(d.items()))
put('mods/SuperString/pac/string/win/string_win.pac', Hs.replace(0, Ss.build()))
# 5 tables: v2 = the values this arena runs with in Matthew's modded game (slot 17 rows there); the creator's
#   txt values (Stage 1, Ref 8, Bar 7, Live 7, filter 0A640000050A, red light, initpos 7) gave a dark static arena
m04 = rd(G + 'pac/root/misc04_arena.pac'); base17 = misc04_get(m04, 17)
row = {k: base17[k] for k in ('Titantron', 'Minitron', 'Wall_L', 'Wall_R', 'Header', 'Floor', 'MiscObjects', 'LightingType', 'Apron_CM', 'RingMat_CM')}
row.update({'Stadium': 1, 'Advertisement': 0, 'CornerPost': 17, 'LED_CornerPost': -1, 'Rope': 3, 'Apron': 7, 'LED_Apron': -1,
            'Turnbuckle': 13, 'Barricade': 6, 'Fence': 0, 'CeilingLighting': 73, 'Spotlight': 91, 'Floor': 3,  # AEW Ceiling Light mod (needs its files) 'Stairs': 0, 'CommentarySeat': 33,
            'RingMat': 7, 'FloorMattress': 2, 'Crowd': 10, 'CrowdSeatsPlace': -1, 'CrowdSeatsModel': -1, 'IBL': 50,
            'CornerPost_CM': 2, 'Rope_CM': 2, 'Turnbuckle_CM': 2})
put('pac/root/misc04_arena.pac', misc04_set(m04, SLOT, row))
m01 = rd(G + 'pac/root/misc01_start.pac')
put('pac/root/misc01_start.pac', misc01_set(m01, SLOT, {'name': SID, 'A1': 0, 'A2': 17, 'B1': 0xC, 'B2': 0x1B, 'B3': 0xFFFF,
    'C1': 1, 'C2': 1, 'C3': 1, 'C4': 1, 'C5': 0, 'C6': 0, 'C7': 0, 'C8': 0, 'Stage': 1, 'D1': 0, 'D2': 2, 'D3': 1, 'D4': 0, 'D5': 1,
    'Ref': 4, 'Filter': '000000FFFFFF', 'F1': 0, 'F2': 0x5A, 'F3': 0, 'F4': 0, 'H1': 5, 'H2': 4, 'H3': 1, 'H4': 3, 'Bar': 6,
    'I1': 0, 'I2': 0, 'I3': 0x3A, 'Live': 0, 'J': 0}))
put('pac/prop/propdata/initposition.pac', initpos_set(rd(G + 'pac/prop/propdata/initposition.pac'), SLOT, 9, 9, 9))
put('pac/misc/parameter/light/prm_ar_lg_color.pac', light_set(rd(G + 'pac/misc/parameter/light/prm_ar_lg_color.pac'), SLOT,
    ['822D0CFF', 'FF0808FF', '00FFFBFF', '0505FFFF', '822D0CFF', 'FFFFFFFF', '0505FFFF', 'EE1C08FF', '0505FFFF', 'EE1C08FF']))
# verify by re-reading
assert misc04_get(files['pac/root/misc04_arena.pac'], SLOT)['Stadium'] == 1 and misc04_get(files['pac/root/misc04_arena.pac'], 17) == base17
assert misc01_get(files['pac/root/misc01_start.pac'], SLOT)['Bar'] == 6 and misc01_get(files['pac/root/misc01_start.pac'], 17) == misc01_get(m01, 17)
assert initpos_get(files['pac/prop/propdata/initposition.pac'], SLOT) == (9, 9, 9)
for rel in ('pac/arena/entrance/arentrance00158.pac', 'pac/mov/ar_wall/0000158.pac'): assert names(files[rel])[0].startswith(b'M')
man = {}
for rel, data in files.items():
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(data)
    man[rel] = {'size': len(data), 'md5': hashlib.md5(data).hexdigest()}
json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1); print(json.dumps(man, indent=1))

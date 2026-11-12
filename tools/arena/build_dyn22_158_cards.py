"""Follow-up for the Dynamite '22 -> 158 test: arena-select logo (ppv_logo) + match card (match_up ltag).
Match card per the community tutorial in Resources: keep slot 158's card, swap in the mod's files 1 (background
movie), 3 (foreground image), 4; the slot's own layout file (atb0, last file) stays."""
import os, sys, json, hashlib
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); sys.path.insert(0, os.path.join(H, '..', 'lib'))
from epk import rename; import shdc2
from yukes import HSPC
M = '/mnt/user-data/uploads/common/WWE 2K19/_arena_work/in/mc/'; OUT = sys.argv[1]; rd = lambda p: open(p, 'rb').read(); files = {}
files['mods/WWE 2K19 Unpacked Arena Graphics/pac/menu/win/Assets/wwe19_singleread/texture/ppv_logo/158 - Over the Limit \'11.pac'] = rename(rd(M + 'dyn_ppv_logo.pac'), [b'77868656'])
tgt = rd(M + 'ltag_158_overlimit_2011_win.pac'); Ht = HSPC(tgt); src = shdc2.files(HSPC(rd(M + 'dyn_ltag_003.pac')).files[0]['data'])
new = shdc2.build(Ht.files[0]['data'], {1: src[1], 3: src[3], 4: src[4]})
f2 = shdc2.files(new); assert f2[1] == src[1] and f2[3] == src[3] and f2[7] == shdc2.files(Ht.files[0]['data'])[7]
files['pac/menu/win/Assets/wwe19_anime/match_up/ltag_158_overlimit_2011_win.pac'] = Ht.replace(0, new)
man = {}
for rel, data in files.items():
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(data); man[rel] = {'size': len(data), 'md5': hashlib.md5(data).hexdigest()}
json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1); print(json.dumps(man, indent=1))

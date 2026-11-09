"""Diagnostic build: copy a musicslot build and add visible marker edits to EXISTING menu items.
  python3 -I tools/build/diag_markers.py --src <build dir> --out <new build dir>
Markers: (1) BGM.lsd entry for The Rock (value 100000) gets label string 3109 (our new label);
(2) string 3101 'STEVE AUSTIN' -> 'STEVE AUSTIN TEST'. manifest inputs stay the originals, so install.py works."""
import sys, os, json, struct, shutil, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
from yukes import HSPC, SHDC, string_table_parse, string_table_build
a = dict(zip(sys.argv[1::2], sys.argv[2::2])); S_, O = a['--src'], a['--out']
shutil.copytree(S_, O, dirs_exist_ok=True)
m = json.load(open(os.path.join(O, 'manifest.json')))
p = os.path.join(O, m['outputs']['cae']['path']); H = HSPC(open(p, 'rb').read()); S = SHDC(H.files[0]['data'])
f = [x for x in S.files if x['id'] == 2][0]; d = bytearray(f['data']); n = struct.unpack_from('<H', d, 0)[0]
hit = [k for k in range(n) if struct.unpack_from('<I', d, 4 + 40 * k)[0] == 100000]; assert len(hit) == 1
struct.pack_into('<I', d, 4 + 40 * hit[0] + 24, 3109); f['data'] = bytes(d)
open(p, 'wb').write(H.replace(0, S.build()))
p = os.path.join(O, m['outputs']['str']['path']); H = HSPC(open(p, 'rb').read()); S = SHDC(H.files[0]['data'])
pre, e = string_table_parse(S.files[0]['data']); e = [(i, b'STEVE AUSTIN TEST\0' if i == 3101 else s) for i, s in e]
S.files[0]['data'] = string_table_build(pre, e); open(p, 'wb').write(H.replace(0, S.build()))
for k in ('cae', 'str'):
    b = open(os.path.join(O, m['outputs'][k]['path']), 'rb').read(); m['outputs'][k].update(md5=hashlib.md5(b).hexdigest(), size=len(b))
m['diag'] = 'markers: Rock BGM label->3109; string 3101 -> STEVE AUSTIN TEST'
json.dump(m, open(os.path.join(O, 'manifest.json'), 'w'), indent=1); print('ok', m['outputs']['cae'], m['outputs']['str'])

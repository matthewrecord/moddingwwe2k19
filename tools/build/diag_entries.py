"""Append arbitrary test entries before the last BGM entry of a musicslot build's cae_item_p30.pac.
  python3 -I tools/build/diag_entries.py --src <build> --out <new> --add 100000:3109 --add 109000:3100
Each entry copies the base-style layout: (value, 0xFFFF0000|value//1000, -1, 0xFFFF, -1, -1, label, 0xFFFF0001, 0, 0)."""
import sys, os, json, struct, shutil, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
from yukes import HSPC, SHDC
args = sys.argv[1:]; src = args[args.index('--src') + 1]; O = args[args.index('--out') + 1]
adds = [tuple(int(x) for x in args[i + 1].split(':')) for i, v in enumerate(args) if v == '--add']
shutil.copytree(src, O, dirs_exist_ok=True)
m = json.load(open(os.path.join(O, 'manifest.json'))); p = os.path.join(O, m['outputs']['cae']['path'])
H = HSPC(open(p, 'rb').read()); S = SHDC(H.files[0]['data']); f = [x for x in S.files if x['id'] == 2][0]; d = f['data']
n, end = struct.unpack_from('<HH', d, 0); E = [list(struct.unpack_from('<10I', d, 4 + 40 * k)) for k in range(n)]
for val, lab in adds:
    E.insert(len(E) - 1, [val, 0xFFFF0000 | (val // 1000), 0xFFFFFFFF, 0xFFFF, 0xFFFFFFFF, 0xFFFFFFFF, lab, 0xFFFF0001, 0, 0])
k = len(adds)
f['data'] = struct.pack('<HH', n + k, end + k) + b''.join(struct.pack('<10I', *e) for e in E)
b = H.replace(0, S.build()); open(p, 'wb').write(b)
m['outputs']['cae'].update(md5=hashlib.md5(b).hexdigest(), size=len(b)); m['diag'] = 'entries added: %r' % adds
json.dump(m, open(os.path.join(O, 'manifest.json'), 'w'), indent=1)
print('BGM', (n + k, end + k), [(e[0], e[6]) for e in E[-(k + 2):]])

"""Diagnostic on a musicslot build's cae_item_p30.pac (BGM list):
  (1) Lio Rush entry (805000) label -> 3101 ('STEVE AUSTIN')  => shows whether p30 edits are read;
  (2) insert a duplicate of the base The Rock entry (100000, label 3100) before our entry => do appended entries show;
  (3) our entry stays last. Header becomes (n+1, end+1).
  python3 -I tools/build/diag_p30.py --src <build> --out <new build>"""
import sys, os, json, struct, shutil, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
from yukes import HSPC, SHDC
a = dict(zip(sys.argv[1::2], sys.argv[2::2])); O = a['--out']; shutil.copytree(a['--src'], O, dirs_exist_ok=True)
m = json.load(open(os.path.join(O, 'manifest.json'))); p = os.path.join(O, m['outputs']['cae']['path'])
H = HSPC(open(p, 'rb').read()); S = SHDC(H.files[0]['data']); f = [x for x in S.files if x['id'] == 2][0]; d = f['data']
n, end = struct.unpack_from('<HH', d, 0); E = [list(struct.unpack_from('<10I', d, 4 + 40 * k)) for k in range(n)]
lio = [e for e in E if e[0] == 805000]; assert len(lio) == 1; lio[0][6] = 3101
rock = [0x186a0, 0xffff0064, 0xffffffff, 0xffff, 0xffffffff, 0xffffffff, 0xc1c, 0xffff0001, 0, 0]
E.insert(len(E) - 1, rock)
f['data'] = struct.pack('<HH', n + 1, end + 1) + b''.join(struct.pack('<10I', *e) for e in E)
b = H.replace(0, S.build()); open(p, 'wb').write(b)
m['outputs']['cae'].update(md5=hashlib.md5(b).hexdigest(), size=len(b)); m['diag'] = 'p30: Lio Rush label->3101; dup Rock appended; ours last'
json.dump(m, open(os.path.join(O, 'manifest.json'), 'w'), indent=1)
print('BGM', (n + 1, end + 1), [(e[0], e[6]) for e in E[-4:]])

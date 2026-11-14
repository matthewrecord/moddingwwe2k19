"""Rename a championship (title index NN) in the active string_win.pac, every variant and every language table.
Variants for title NN (found 2026-11-14 for Brahma Bull = 23): 2100NN/2101NN (upper, plain / WWE-logo glyph prefix),
2102NN/2103NN (upper, line break), 2108NN/2109NN (mixed case), 2110NN/2111NN (mixed, line break), 2120NN (holder title,
'... CHAMPION'), plus extra ids passed with --extra (602003 = Brahma Bull, upper with glyph).
  titlename.py --pac string_win.pac --index 23 --name "AEW United States Championship" --holder "AEW United States Champion"
     [--extra 602003] --out OUT.pac"""
import sys, os, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'audio'), os.path.join(HERE, '..', 'lib')]
from musicslot import add_strings, string_ids
from yukes import HSPC
a = argparse.ArgumentParser(); a.add_argument('--pac', required=True); a.add_argument('--index', type=int, required=True)
a.add_argument('--name', required=True); a.add_argument('--holder', required=True); a.add_argument('--extra', type=int, nargs='*', default=[])
a.add_argument('--out', required=True); a = a.parse_args()
N, U = a.name, a.name.upper(); brk = lambda s: s.replace(' Championship', '\nChampionship').replace(' CHAMPIONSHIP', '\nCHAMPIONSHIP') if ' ' in s else s
n = a.index
new = {210000 + n: U, 210100 + n: U, 210200 + n: brk(U), 210300 + n: brk(U), 210800 + n: N, 210900 + n: N,
       211000 + n: brk(N), 211100 + n: brk(N), 212000 + n: a.holder.upper()}
for x in a.extra: new[x] = U
b = open(a.pac, 'rb').read(); nfiles = len(HSPC(b).files); done = []
for fi in range(nfiles):
    try: ids = string_ids(b, fi)
    except Exception: continue                     # not a string table (e.g. the last file)
    have = {k: v for k, v in new.items() if k in ids}
    b, _ = add_strings(b, have, fi); done.append((fi, len(have)))
open(a.out, 'wb').write(b); print('tables updated (file, strings):', done)
for k in sorted(new): print(k, repr(string_ids(b, 0)[k].rstrip(b'\0').decode('latin1')))

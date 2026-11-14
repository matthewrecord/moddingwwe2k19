"""Yuke's own "champion belt too dark" fix: pac/misc/parameter/todo/todo_wwe19_champion_belt_too_dark.pac (NIBJ param table).
Found 2026-11-14 by decoding the belt shader (yPBR_RTCS_Belt, writeup/Belt_backport.md 36). When the per-scene switch is on, the
shader applies roughness = max(rough * RoughMul, RoughMin) and multiplies the arena IBL for belts: irradiance * Belt_IrrMul (floor
Belt_IrrMin), specular reflection * Belt_SpcMul (floor Belt_SpcMin). Stock values: IrrMul 1.0, SpcMul 2.0, IrrMin 0, SpcMin 0.2,
switches Entrance=1, Winning=0, TitleMatch=0, CACMenu=0, Always=0, i.e. belts get the brightening ONLY during entrances and look
darker in title-match presentations and winner scenes (every belt, stock too).
  beltdark.py IN.pac OUT.pac --show
  beltdark.py IN.pac OUT.pac --on TitleMatch Winning [--spcmul 2.0 --spcmin 0.2]"""
import sys, os, struct, zlib, argparse
here = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(here, '..', 'lib'), here]
import yukes, titletable as T
FIELDS = ['Belt_IrrMul', 'Belt_SpcMul', 'Belt_IrrMin', 'Belt_SpcMin', 'Entrance', 'Winning', 'TitleMatch', 'CACMenu', 'Always']
VAL = 336                                                   # values start after the 9 field descriptors (measured)
a = argparse.ArgumentParser(); a.add_argument('inp'); a.add_argument('out', nargs='?'); a.add_argument('--show', action='store_true')
a.add_argument('--on', nargs='*', default=[]); a.add_argument('--off', nargs='*', default=[])
for f in ('irrmul', 'spcmul', 'irrmin', 'spcmin'): a.add_argument('--' + f, type=float)
a = a.parse_args()
raw = open(a.inp, 'rb').read(); h = yukes.HSPC(raw); s = yukes.SHDC(h.files[0]['data']); z = s.files[0]['data']
d = bytearray(zlib.decompress(z[16:])); assert d[:4] == b'NIBJ' and d[48:59] == b'Belt_IrrMul'
def show():
    v = struct.unpack_from('<4f5I', d, VAL); print(dict(zip(FIELDS, [round(x, 3) if isinstance(x, float) else x for x in v])))
show()
if a.show or not a.out: sys.exit()
for i, k in enumerate(('irrmul', 'spcmul', 'irrmin', 'spcmin')):
    if getattr(a, k) is not None: struct.pack_into('<f', d, VAL + 4 * i, getattr(a, k))
for nm in a.on: struct.pack_into('<I', d, VAL + 4 * FIELDS.index(nm), 1)
for nm in a.off: struct.pack_into('<I', d, VAL + 4 * FIELDS.index(nm), 0)
c = zlib.compress(bytes(d), 9); s.files[0]['data'] = b'ZLIB' + struct.pack('<3I', struct.unpack_from('<I', z, 4)[0], len(c), len(d)) + c
h.files[0]['data'] = T.shdc_build(s); open(a.out, 'wb').write(h.build()[0]); print('wrote', a.out); show()

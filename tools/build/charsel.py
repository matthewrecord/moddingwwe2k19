"""Make superstar slots selectable (writes to an output folder only; never touches the game).

Select-screen rule (notes/characters/survey_001, exe 0x140c40980 / 0x1404c9460 / 0x1404bef50):
  selectable = pofo byte +0x20 ("playable") == 1  AND  no unowned unlockable of type 0 (store) or 10 (showcase/tower)
  for that character id in the HID table (misc01_start.pac, SHDC file 6, 500 x 32-byte records; type = byte +6,
  character id = u32 +0x10).

  python3 -I tools/build/charsel.py --game "<install>" --out <dir> [--unlock 335 --unlock 160 ...] [--playable 274 ...]

--unlock ID: every HID record for ID whose type byte is 0 or 10 gets type 6 (a non-gating type the game already uses).
--playable ID: pofo +0x20 = 1 in the live profile_dat (mods/PerfectPlextra/pac/profile/profile_dat.pac).
Changed SHDC entries are stored uncompressed (the loader accepts raw entries: PerfectPlextra ships raw profile rows).
Outputs mirror game paths + manifest.json (inputs/outputs MD5) for install.py.
"""
import argparse, hashlib, json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..', 'audio')]
from yukes import HSPC, SHDC
from bpe import expand

PATHS = {'misc01': 'pac/root/misc01_start.pac', 'prof': 'mods/PerfectPlextra/pac/profile/profile_dat.pac'}
GATING = (0, 10)          # type bytes the unlock check honours that exist in the data (mask also has 20, 30)
NONGATING = 6

def md5(b): return hashlib.md5(b).hexdigest()

def dec(b):
    if b[:4] != b'BPE ': return b
    h = struct.unpack('<4I', b[4:20]); d = expand(b, 16, h[2])[0]; assert len(d) == h[2]; return d

def edit_shdc_file(pac, file_id, fn):
    H = HSPC(pac); S = SHDC(H.files[0]['data'])
    f = [x for x in S.files if x['id'] == file_id]; assert len(f) == 1, 'SHDC file %d not found' % file_id
    new, info = fn(bytearray(dec(f[0]['data'])))
    f[0]['data'] = bytes(new)
    return H.replace(0, S.build()), info

def unlock(pac, ids):
    def fn(d):
        assert d[:4] == b'HID\x00'; n = struct.unpack_from('<I', d, 4)[0]; assert len(d) == 8 + 32 * n
        changed = []
        for i in range(n):
            o = 8 + 32 * i; cid = struct.unpack_from('<I', d, o + 0x10)[0]
            if cid in ids and d[o + 6] in GATING:
                changed.append({'record': i, 'id': cid, 'type_before': d[o + 6], 'type_after': NONGATING})
                d[o + 6] = NONGATING
        return d, changed
    return edit_shdc_file(pac, 6, fn)

def playable(pac, ids):
    H = HSPC(pac); S = SHDC(H.files[0]['data']); changed = []
    for f in S.files:
        d = bytearray(dec(f['data'])); cid = struct.unpack_from('<H', d, 4)[0]
        if cid in ids:
            changed.append({'profile_index': f['id'], 'id': cid, 'before': d[4 + 0x20]})
            d[4 + 0x20] = 1; f['data'] = bytes(d)
    return H.replace(0, S.build()), changed

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--unlock', type=int, action='append', default=[])
    ap.add_argument('--playable', type=int, action='append', default=[])
    a = ap.parse_args()
    src = {k: open(os.path.join(a.game, v), 'rb').read() for k, v in PATHS.items()}
    out = {}; man = {'unlock': a.unlock, 'playable': a.playable,
                     'inputs': {k: {'path': PATHS[k], 'md5': md5(v)} for k, v in src.items()}}
    if a.unlock:
        out['misc01'], man['unlock_changes'] = unlock(src['misc01'], set(a.unlock))
        missing = set(a.unlock) - {c['id'] for c in man['unlock_changes']}
        if missing: print('note: no gating HID record for', sorted(missing))
    if a.playable:
        out['prof'], man['playable_changes'] = playable(src['prof'], set(a.playable))
        assert {c['id'] for c in man['playable_changes']} == set(a.playable), 'id not in profile_dat'
    for k, v in out.items():
        p = os.path.join(a.out, PATHS[k]); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(v)
    man['inputs'] = {k: man['inputs'][k] for k in out}
    man['outputs'] = {k: {'path': PATHS[k], 'md5': md5(v), 'size': len(v)} for k, v in out.items()}
    open(os.path.join(a.out, 'manifest.json'), 'w').write(json.dumps(man, indent=1))
    print(json.dumps({k: man[k] for k in man if k.endswith('changes')}, indent=1))

if __name__ == '__main__':
    main()

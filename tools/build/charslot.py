"""Build a new character in an overflow slot (profile index >= 509), for the tools/slots proxy (dinput8.dll).
Writes to an output folder only; install with install.py (modified files) + the copy list in manifest.json.

  python3 -I tools/build/charslot.py --game "<install>" --pictures "<WWE 2K19 pictures folder>" --out <dir>
         --source "Alex Shelley" --source-id 779 --index 509 --id 937 --name "Test Wrestler" --name-sid 39370

What it makes (game-relative paths):
- slots/<index>_<id>.pofo / .moveset: the CCT-exported pofo (484 bytes) / moveset (3464 bytes) of the source, with
  pofo +0 = id, +2 = profile index, name string ids (+0x08..+0x1C, +0x1D0) = name-sid. The proxy copies them into
  the overflow pofo array / relocated moveset table and registers id <-> index in the game's maps after boot.
- mods/SuperString/pac/string/win/string_win.pac: English table gains name-sid = name.
- Chunk0.def: every line naming the source id's CCT assets is duplicated for the new id (models ch<id><attire>,
  trons/renders 0<id>00), placed right after the source line.
- manifest 'copies': CCT asset files to copy source -> new id (new files; nothing overwritten).
"""
import argparse, hashlib, json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, '..', 'lib')]
from yukes import HSPC, SHDC, string_table_parse, string_table_build
NAME_FIELDS = (0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C, 0x1D0)
STR = 'mods/SuperString/pac/string/win/string_win.pac'
def md5(b): return hashlib.md5(b).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    for k in ('game', 'pictures', 'out', 'source', 'name'): ap.add_argument('--' + k, required=True)
    for k in ('source-id', 'index', 'id', 'name-sid'): ap.add_argument('--' + k, type=int, required=True)
    a = ap.parse_args(); G = a.game
    pofo = bytearray(open(os.path.join(a.pictures, a.source, a.source + '.pofo'), 'rb').read())
    mov = open(os.path.join(a.pictures, a.source, a.source + '.moveset'), 'rb').read()
    assert len(pofo) == 0x1E4 and len(mov) == 0xD88, (len(pofo), len(mov))
    assert struct.unpack_from('<H', pofo, 0)[0] == a.source_id, 'pofo id is not --source-id'
    old_sid = struct.unpack_from('<I', pofo, 8)[0]
    struct.pack_into('<HH', pofo, 0, a.id, a.index)
    for o in NAME_FIELDS:
        if struct.unpack_from('<I', pofo, o)[0] == old_sid: struct.pack_into('<I', pofo, o, a.name_sid)
    assert pofo[0x20] == 1, 'source pofo is not flagged playable (+0x20)'
    out = {}
    base = 'slots/%04d_%04d_%04d' % (a.index, a.id, a.source_id)   # 3rd number: id whose 40-byte per-slot record is cloned
    out['pofo'] = (base + '.pofo', bytes(pofo)); out['moveset'] = (base + '.moveset', mov)

    sp = open(os.path.join(G, STR), 'rb').read(); H = HSPC(sp); S = SHDC(H.files[0]['data'])
    pre, ents = string_table_parse(S.files[0]['data']); d = dict(ents)
    assert a.name_sid not in d, 'name-sid already used'
    d[a.name_sid] = a.name.encode('latin1') + b'\0'
    S.files[0]['data'] = string_table_build(pre, sorted(d.items()))
    out['str'] = (STR, H.replace(0, S.build()))

    cd = open(os.path.join(G, 'Chunk0.def'), 'rb').read().split(b'\r\n')
    s3, n3 = b'%03d' % a.source_id, b'%03d' % a.id
    new, copies = [], []
    for line in cd:
        new.append(line)
        low = line.lower(); fn = low.rsplit(b'\\', 1)[-1]
        if low.startswith(b'mods\\cct\\') and (fn.startswith(b'ch' + s3) and len(fn) == 11 or fn == b'0' + s3 + b'00.pac'):
            nl = line[:len(line) - len(fn)] + fn.replace(s3, n3, 1)
            assert nl.lower() not in (x.lower() for x in cd), 'target already registered: %r' % nl
            new.append(nl); copies.append((line.decode().replace('\\', '/'), nl.decode().replace('\\', '/')))
    assert copies, 'no CCT assets for source id'
    # Chunk0.def is kept sorted (case-insensitive) within each folder and the game appears to rely on it (lines
    # appended out of order were never found: 2026-11-10 test1). Re-insert each new line at its sorted position.
    added = [nl.replace('/', '\\').encode() for _, nl in copies]
    new = [x for x in new if x.lower() not in {a.lower() for a in added}]
    for nb in added:
        k = nb.lower(); d = k.rsplit(b'\\', 1)[0] + b'\\'
        idx = [i for i, y in enumerate(new) if y.lower().startswith(d) and y.lower().count(b'\\') == k.count(b'\\')]
        pos = next((i for i in idx if new[i].lower() > k), idx[-1] + 1)
        new.insert(pos, nb)
    out['chunk'] = ('Chunk0.def', b'\r\n'.join(new))

    man = {'args': vars(a), 'inputs': {}, 'outputs': {}, 'copies': copies}
    for k, (p, data) in out.items():
        q = os.path.join(a.out, p); os.makedirs(os.path.dirname(q) or a.out, exist_ok=True); open(q, 'wb').write(data)
        src = os.path.join(G, p)
        man['inputs'][k] = {'path': p, 'md5': md5(open(src, 'rb').read()) if os.path.exists(src) else None}
        man['outputs'][k] = {'path': p, 'md5': md5(data), 'size': len(data)}
    open(os.path.join(a.out, 'manifest.json'), 'w').write(json.dumps(man, indent=1))
    print(json.dumps({'copies': copies, 'outputs': man['outputs']}, indent=1))

if __name__ == '__main__': main()

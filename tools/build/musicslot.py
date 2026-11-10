"""Build a brand-new WWE 2K19 music slot (writes to an output folder only; never touches the game).

Route (writeup/Music_map.md section 8): the new track goes into the DLC_30_E_S bank of sound/patch_30.pck (loaded at
boot), the music table row <id> is activated in TitantronFix's assetconv_p30.pac, and the name (string 13000+id) is
added to the English table of SuperString's string_win.pac.

Usage (laptop agent shell, from the repo clone):
  python3 -I tools/build/musicslot.py --game "<install>" --wem <file.wem> --id 109 --name "Name" --out <dir>
Outputs in <dir>: sound/patch_30.pck, mods/TitantronFix/pac/audio/assetconv_p30.pac,
mods/SuperString/pac/string/win/string_win.pac, pac/menu/cae_item.pac, manifest.json (inputs, outputs, md5s).
"""
import argparse, bisect, hashlib, json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'audio')); sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
from evmatch import fnv
from vmum import load as vmum_load
from yukes import HSPC, SHDC, string_table_parse, string_table_build

DLC30_BANK = 1755985664          # DLC_30_E_S
MUSIC_MIXER = 126675442          # shared music ActorMixer
TEMPLATE = {'sound': 541437393, 'ranseq': 825486892, 'play': 1127526729}   # MUS_0805 chain

def md5(b): return hashlib.md5(b).hexdigest()

# ---------- AKPK ----------
def akpk_read(b):
    assert b[:4] == b'AKPK'
    hs = struct.unpack_from('<I', b, 4)[0]
    ver, lsz, bsz, ssz, esz = struct.unpack_from('<5I', b, 8)
    o = 28; lang = b[o:o + lsz]; o += lsz
    def tab(o, size):
        n = struct.unpack_from('<I', b, o)[0]
        return [list(struct.unpack_from('<5I', b, o + 4 + 20 * i)) for i in range(n)]
    banks = tab(o, bsz); o += bsz
    streams = tab(o, ssz); o += ssz
    ext = b[o:o + esz]
    assert o + esz == 8 + hs
    data = {}
    for kind, t in (('B', banks), ('S', streams)):
        for fid, mul, sz, start, lng in t:
            data[(kind, fid)] = b[start * mul: start * mul + sz]
    return {'ver': ver, 'lang': lang, 'banks': banks, 'streams': streams, 'ext': ext, 'data': data, 'raw': b}

def akpk_write(p):
    """Tightly packed like the originals (block size 1); data order = original order, new items appended."""
    def tabbytes(t): return struct.pack('<I', len(t)) + b''.join(struct.pack('<5I', *e) for e in t)
    banks = sorted(p['banks'], key=lambda e: e[0]); streams = sorted(p['streams'], key=lambda e: e[0])
    hdr_len = 20 + len(p['lang']) + 4 + 20 * len(banks) + 4 + 20 * len(streams) + len(p['ext'])
    pos = 8 + hdr_len
    order = sorted([('B', e) for e in banks] + [('S', e) for e in streams], key=lambda x: x[1][3])
    body = bytearray()
    for kind, e in order:
        d = p['data'][(kind, e[0])]
        e[1] = 1; e[2] = len(d); e[3] = pos + len(body); body += d
    hdr = struct.pack('<5I', p['ver'], len(p['lang']), 4 + 20 * len(banks), 4 + 20 * len(streams), len(p['ext']))
    hdr += p['lang'] + tabbytes(banks) + tabbytes(streams) + p['ext']
    assert len(hdr) == hdr_len
    return b'AKPK' + struct.pack('<I', hdr_len) + hdr + bytes(body)

# ---------- bank / HIRC ----------
def chunks(bank):
    o = 0; out = []
    while o < len(bank):
        tag = bank[o:o + 4]; ln = struct.unpack_from('<I', bank, o + 4)[0]
        out.append([tag, bank[o + 8: o + 8 + ln]]); o += 8 + ln
    return out

def hirc_objs(h):
    n = struct.unpack_from('<I', h, 0)[0]; o = 4; out = []
    for _ in range(n):
        t = h[o]; ln = struct.unpack_from('<I', h, o + 1)[0]; oid = struct.unpack_from('<I', h, o + 5)[0]
        out.append([t, oid, bytearray(h[o + 9: o + 5 + ln])]); o += 5 + ln
    assert o == len(h)
    return out

def hirc_bytes(objs):
    return struct.pack('<I', len(objs)) + b''.join(bytes([t]) + struct.pack('<II', 4 + len(b), oid) + bytes(b) for t, oid, b in objs)

def wem_info(w):
    assert w[:4] == b'RIFF' and w[8:12] == b'WAVE', 'not a RIFF/WAVE .wem'
    o = 12; fmt = None; data_off = None
    while o < len(w) - 8:
        tag = w[o:o + 4]; ln = struct.unpack_from('<I', w, o + 4)[0]
        if tag == b'fmt ': fmt = w[o + 8: o + 8 + ln]
        if tag == b'data': data_off = o + 8; break
        o += 8 + ln + (ln & 1)
    assert fmt and data_off, 'fmt/data chunk missing'
    codec, ch, sr, avg = struct.unpack_from('<HHII', fmt, 0)
    assert codec == 0xFFFF and len(fmt) == 0x42, 'expected Wwise Vorbis (fmt 0xFFFF, size 0x42) like the game'
    audio_off = struct.unpack_from('<I', fmt, 0x2C)[0]
    # uInMemoryMediaSize: game files = header + seek/setup + ~0.81 s of audio (measured on 2 tracks; see Music_map 6b)
    inmem = data_off + audio_off + int(0.81 * avg)
    return {'channels': ch, 'rate': sr, 'avg_bps': avg, 'data_off': data_off, 'audio_off': audio_off, 'inmem': inmem}

def add_track(bank, mid, src_id, inmem):
    ch = chunks(bank)
    hi = [c for c in ch if c[0] == b'HIRC'][0]
    objs = hirc_objs(hi[1]); byid = {o[1]: o for o in objs}
    ids = {
        'sound': fnv('wwe2k19mod_sound_%04d' % mid), 'ranseq': fnv('wwe2k19mod_ranseq_%04d' % mid),
        'play0': fnv('wwe2k19mod_play0_%04d' % mid), 'play1': fnv('wwe2k19mod_play1_%04d' % mid),
        'ev0': fnv('Play_MUS_%04d_00_0_0' % mid), 'ev1': fnv('Play_MUS_%04d_00_0_1' % mid)}
    for k, v in ids.items():
        assert v not in byid, 'id collision %s %d' % (k, v)
    # Sound (clone of MUS_0805's): sourceID @5, inMem @9, parent @21
    snd = bytearray(byid[TEMPLATE['sound']][2])
    struct.pack_into('<I', snd, 5, src_id); struct.pack_into('<I', snd, 9, inmem); struct.pack_into('<I', snd, 21, ids['ranseq'])
    # RanSeq: parent @7, child @0x36, play id @0x3c
    rs = bytearray(byid[TEMPLATE['ranseq']][2])
    assert struct.unpack_from('<I', rs, 7)[0] == MUSIC_MIXER and struct.unpack_from('<I', rs, 0x32)[0] == 1
    struct.pack_into('<I', rs, 0x36, ids['sound']); struct.pack_into('<I', rs, 0x3c, ids['sound'])
    # Play actions: target @2, bank @10
    def play():
        a = bytearray(byid[TEMPLATE['play']][2])
        assert struct.unpack_from('<H', a, 0)[0] == 0x0403 and struct.unpack_from('<I', a, 10)[0] == DLC30_BANK
        struct.pack_into('<I', a, 2, ids['ranseq']); return a
    ev = lambda aid: bytearray(b'\x01' + struct.pack('<I', aid))
    # ActorMixer: children list at the end: u32 n, n x id (ascending)
    mix = byid[MUSIC_MIXER][2]
    n = None
    for k in range(len(mix) - 4, 0, -1):
        cand = struct.unpack_from('<I', mix, k)[0]
        if 0 < cand < 4096 and k + 4 + 4 * cand == len(mix): n = cand; pos = k; break
    assert n, 'mixer child list not found'
    kids = list(struct.unpack_from('<%dI' % n, mix, pos + 4)); assert kids == sorted(kids)
    kids.insert(bisect.bisect(kids, ids['ranseq']), ids['ranseq'])
    byid[MUSIC_MIXER][2] = bytearray(mix[:pos] + struct.pack('<I', len(kids)) + struct.pack('<%dI' % len(kids), *kids))
    objs += [[2, ids['sound'], snd], [5, ids['ranseq'], rs], [3, ids['play0'], play()], [4, ids['ev0'], ev(ids['play0'])],
             [3, ids['play1'], play()], [4, ids['ev1'], ev(ids['play1'])]]
    hi[1] = hirc_bytes(objs)
    return b''.join(t + struct.pack('<I', len(d)) + bytes(d) for t, d in ch), ids

# ---------- music table ----------
def activate_row(pac, mid):
    """Name row <mid> (fields 0/1 = new unique indexes), give it its key (field 4 = mid*100000) and move it into the
    sorted tail. Table layout (measured): [ids 100-107 keyed][749 rows with key 0 = empty slots][sorted tail]. The game
    bsearches field 4 over all rows; probes in the zero block always go right, so keys >= the tail start are found.
    Only rows between the old and new position shift by one; no row content changes except row <mid>."""
    b = bytearray(pac); vb, o, h, recs = vmum_load_bytes(b)
    recs = [list(r) for r in recs]
    named = [r for r in recs if r[1] and r[2] < 10000]
    f0 = max(r[0] for r in named) + 1; f1 = max(r[1] for r in named) + 1
    idx = [i for i, r in enumerate(recs) if r[2] == mid and r[3] == 0]
    assert len(idx) == 1, 'row %d not found exactly once' % mid
    i = idx[0]; row = recs[i]; before = list(row)
    assert row[0] == 0 and row[1] == 0 and row[4] == 0, 'row %d is not an empty slot: %r' % (mid, row[:6])
    keys = [r[4] for r in recs]
    tail_start = next(k for k in range(len(recs)) if keys[k] > 0 and k > 0 and keys[k - 1] == 0)
    tail = keys[tail_start:]; assert tail == sorted(tail), 'tail not sorted'
    key = mid * 100000
    assert key > tail[0], 'id below the sorted tail start; bsearch could not reach it'
    row[0], row[1], row[4] = f0, f1, key
    del recs[i]
    if i < tail_start: tail_start -= 1
    tk = [r[4] for r in recs[tail_start:]]
    j = tail_start + bisect.bisect(tk, key)
    recs.insert(j, row)
    for k, r in enumerate(recs):
        struct.pack_into('<16I', b, o + 16 + 64 * k, *r)
    return bytes(b), {'old_index': i, 'new_index': j, 'f0': f0, 'f1': f1, 'key': key, 'before': before, 'after': row}

def vmum_load_bytes(b):
    o = bytes(b).find(b'VMUM'); h = struct.unpack_from('<4I', b, o)
    recs = [struct.unpack_from('<16I', b, o + 16 + 64 * i) for i in range(h[3])]
    return b, o, h, recs

# ---------- strings ----------
def add_string(pac, sid, text, file_index=0):
    H = HSPC(pac); d = H.files[file_index]['data']
    S = SHDC(d)
    pre, ents = string_table_parse(S.files[0]['data'])
    ids = [i for i, _ in ents]; assert ids == sorted(ids)
    s = text.encode('latin1') + b'\0'
    if sid in ids:
        ents[ids.index(sid)] = (sid, s)
    else:
        ents.insert(bisect.bisect(ids, sid), (sid, s))
    S.files[0]['data'] = string_table_build(pre, ents)
    return H.replace(file_index, S.build()), len(ents)

# ---------- Create-an-Entrance music menu (BGM.lsd = SHDC file id 2 in pac/menu/cae_item_pNN.pac) ----------
DLC_STYLE = False  # v10 (ID 807) works without DLC flags; v9 DLC flags suspected of the CAE hang

def add_bgm_entry(pac, mid):
    """BGM.lsd: u16 entries in this file, u16 cumulative total; entries of 10 x u32:
    value (id*1000), u16 id | u16 0xFFFF, 0xFFFFFFFF, 0xFFFF, 0xFFFFFFFF, 0xFFFFFFFF, menu string (3000+id),
    0xFFFF0001, 0, dlc flag (1 on DLC entries, 0 on base ones). We add a base-style entry."""
    H = HSPC(pac); S = SHDC(H.files[0]['data'])
    f = [x for x in S.files if x['id'] == 2]; assert len(f) == 1, 'BGM.lsd (id 2) not found'
    f = f[0]; d = f['data']
    n, total = struct.unpack_from('<HH', d, 0); assert len(d) == 4 + 40 * n
    ents = [struct.unpack_from('<10I', d, 4 + 40 * k) for k in range(n)]
    assert all(e[0] != mid * 1000 for e in ents), 'entry already present'
    new = (mid * 1000, 0xFFFF0000 | mid, 0xFFFFFFFF, 0xFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 3000 + mid, 0xFFFF0001, 0,
           1 if DLC_STYLE else 0)
    ents.append(new)
    # both header u16s +1, exactly as CAE Item Adder 0.2.1 does ('<2h' read, +1 each)
    f['data'] = struct.pack('<HH', n + 1, total + 1) + b''.join(struct.pack('<10I', *e) for e in ents)
    return H.replace(0, S.build()), {'entries': n + 1, 'total': total + 1, 'entry': list(new)}

# ---------- music info registry (MEMU, SHDC file id 6 in pac/root/misc05_save_pNN.pac) ----------
def add_memu_record(pac, mid, name_sid, title_sid):
    """MEMU: 'MEMU', u32 count, count x 32-byte records:
    (superstar/label string, song title string, album string or 99999, value, type, u16 id | u16 id2, flags, 0).
    Music records: type 0xFFFF0600, flags 0xFFFF (base) or 0x1EFFFF (DLC patch 30). Every music the CAE menu lists has a
    record; without one the menu hides the entry (v7 diagnostic, 2026-11-09)."""
    H = HSPC(pac); S = SHDC(H.files[0]['data'])
    f = [x for x in S.files if x['id'] == 6]; assert len(f) == 1, 'MEMU (id 6) not found'
    f = f[0]; d = f['data']; assert d[:4] == b'MEMU'
    n = struct.unpack_from('<I', d, 4)[0]; assert len(d) == 8 + 32 * n
    R = [struct.unpack_from('<8I', d, 8 + 32 * k) for k in range(n)]
    assert all(r[3] != mid * 1000 for r in R), 'record already present'
    rec = (name_sid, title_sid, 99999, mid * 1000, 0xFFFF0600, 0xFFFF0000 | mid, 0x1EFFFF if DLC_STYLE else 0xFFFF, 0)
    f['data'] = b'MEMU' + struct.pack('<I', n + 1) + d[8:] + struct.pack('<8I', *rec)
    return H.replace(0, S.build()), {'records': n + 1, 'record': list(rec)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', required=True); ap.add_argument('--wem', required=True)
    ap.add_argument('--id', type=int, action='append', required=True,
                    help='repeat for several new slots in one build (same wem for all)')
    ap.add_argument('--name', action='append', required=True,
                    help='one per --id, in the same order')
    ap.add_argument('--out', required=True)
    a = ap.parse_args(); G = a.game; mids = a.id
    assert len(a.name) == len(mids), 'give one --name per --id'
    assert len(set(mids)) == len(mids), 'duplicate id'
    for mid in mids: assert 0 < mid < 1000, 'ids < 1000 only (name rule 13000+id)'
    paths = {'pck': 'sound/patch_30.pck', 'vmum': 'mods/TitantronFix/pac/audio/assetconv_p30.pac',
             'str': 'mods/SuperString/pac/string/win/string_win.pac', 'cae': 'pac/menu/cae_item_p30.pac',
             'memu': 'pac/root/misc05_save_p30.pac'}
    # CAE lists are one combined index filled in order: base entries, then p10, p20, p30 (each header = (own count,
    # running end): base (304,308), p10 (3,307), p20 (1,308), p30 (7,315)). A base append lands at 304 and is
    # overwritten by p10's first entry (v2/v3/v4 evidence). New entries go at the END of the last list (p30).
    src = {k: open(os.path.join(G, v), 'rb').read() for k, v in paths.items()}
    wem = open(a.wem, 'rb').read(); wi = wem_info(wem)
    man = {'ids': mids, 'names': a.name, 'wem': a.wem, 'wem_md5': md5(wem), 'wem_info': wi,
           'inputs': {k: {'path': paths[k], 'md5': md5(v), 'size': len(v)} for k, v in src.items()}, 'slots': []}
    P = akpk_read(src['pck']); vm, st, cae, memu = src['vmum'], src['str'], src['cae'], src['memu']
    for mid, name in zip(mids, a.name):
        src_id = fnv('wwe2k19mod_wem_%04d' % mid)
        assert ('S', src_id) not in P['data']
        newbank, ids = add_track(P['data'][('B', DLC30_BANK)], mid, src_id, wi['inmem'])
        P['data'][('B', DLC30_BANK)] = newbank
        P['streams'].append([src_id, 1, len(wem), 1 << 30, 0]); P['data'][('S', src_id)] = wem
        vm, row = activate_row(vm, mid)
        st, nstr = add_string(st, 13000 + mid, name)              # name (mixed case)
        st, nstr2 = add_string(st, 3000 + mid, name.upper())      # menu label (upper case, as in BGM.lsd)
        cae, bgm = add_bgm_entry(cae, mid)
        memu, mrec = add_memu_record(memu, mid, 3000 + mid, 13000 + mid)
        man['slots'].append({'id': mid, 'name': name, 'event_ids': ids, 'source_id': src_id, 'row': row,
                             'bgm': bgm, 'memu': mrec})
    pck = akpk_write(P)
    out = {'pck': pck, 'vmum': vm, 'str': st, 'cae': cae, 'memu': memu}
    for k, v in out.items():
        p = os.path.join(a.out, paths[k]); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(v)
    man['outputs'] = {k: {'path': paths[k], 'md5': md5(v), 'size': len(v)} for k, v in out.items()}
    open(os.path.join(a.out, 'manifest.json'), 'w').write(json.dumps(man, indent=1, default=str))
    print(json.dumps({'ids': mids, 'outputs': man['outputs']}, indent=1))

if __name__ == '__main__':
    main()

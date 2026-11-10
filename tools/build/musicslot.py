"""Build a brand-new WWE 2K19 music slot (writes to an output folder only; never touches the game).

Route (writeup/Music_map.md section 8): the new track goes into the DLC_30_E_S bank of sound/patch_30.pck (loaded at
boot), the music table row <id> is activated in TitantronFix's assetconv_p30.pac, and the name (string 13000+id) is
added to the English table of SuperString's string_win.pac.

Usage (laptop agent shell, from the repo clone):
  python3 -I tools/build/musicslot.py --game <originals> --list-free
  python3 -I tools/build/musicslot.py --game <originals> --spec songs.json --out <dir>
  (songs.json: [{"name": "Song", "wem": "song.wem"}, {"name": "Other", "wem": "b.wem", "id": 123}]; ids are picked
  from the free list when omitted.) Old form still works: --wem <f> --id 109 --name "Name" [--id .. --name ..]
Outputs in <dir>: sound/patch_30.pck, mods/TitantronFix/pac/audio/assetconv_p30.pac,
mods/SuperString/pac/string/win/string_win.pac, pac/menu/cae_item_p30.pac, pac/root/misc05_save_p30.pac, manifest.json (inputs, outputs, md5s).
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
    inmem = min(data_off + audio_off + int(0.81 * avg), len(w))   # never more than the file (tiny placeholders)
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
def add_strings(pac, new, file_index=0):
    """new: {string id: text}. One parse/rebuild for any number of strings."""
    H = HSPC(pac); S = SHDC(H.files[file_index]['data'])
    pre, ents = string_table_parse(S.files[0]['data'])
    d = dict(ents); assert [i for i, _ in ents] == sorted(d)
    for sid, text in new.items(): d[sid] = text.encode('latin1') + b'\0'
    S.files[0]['data'] = string_table_build(pre, sorted(d.items()))
    return H.replace(file_index, S.build()), len(d)

def add_string(pac, sid, text, file_index=0):
    return add_strings(pac, {sid: text}, file_index)

# ---------- Create-an-Entrance music menu (BGM.lsd = SHDC file id 2 in pac/menu/cae_item_pNN.pac) ----------
NO_UNLOCK = True   # BGM entry u16 at +4..+0xC are unlock-requirement ids (-1 = none); the menu (0x140179a80 -> 0x140c1eb50/ec80) hides entries whose unlock id is locked. Using the music id there made 109 etc. hidden (2026-11-10 telemetry).
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
    new = (mid * 1000, 0xFFFFFFFF if NO_UNLOCK else (0xFFFF0000 | mid), 0xFFFFFFFF, 0xFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 3000 + mid, 0xFFFF0001, 0,
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

PATHS = {'pck': 'sound/patch_30.pck', 'vmum': 'mods/TitantronFix/pac/audio/assetconv_p30.pac',
         'str': 'mods/SuperString/pac/string/win/string_win.pac', 'cae': 'pac/menu/cae_item_p30.pac',
         'memu': 'pac/root/misc05_save_p30.pac'}

# Files in Matthew's modding folder (D:\Pictures\WWE 2K19), written only when --tools is given.
TOOL_PATHS = {'de': 'A - Data Editor 2k19/Data/DataLists/Modded/EntranceMusicID.data',
              'se': 'Z - Sound Editor New/database/WWE 2K19/custom_data.xml'}

def de_add(b, mid, name):
    """Data Editor list: lines '<id*1000> <name>', CRLF. Unused ids are blank lines '<id*1000>'; fill ours in."""
    t = b.decode('utf-8-sig' if b[:3] == b'\xef\xbb\xbf' else 'latin1'); bom = b[:3] == b'\xef\xbb\xbf'
    lines = t.split('\r\n'); key = str(mid * 1000); hit = 0
    for k, ln in enumerate(lines):
        f = ln.split(' ', 1)
        if f[0] == key:
            assert len(f) == 1 or not f[1].strip(), 'Data Editor already names %s: %r' % (key, ln)
            lines[k] = key + ' ' + name; hit += 1
    if not hit:   # not listed: insert in numeric order
        nums = [int(l.split(' ', 1)[0]) if l.split(' ', 1)[0].isdigit() else -1 for l in lines]
        k = next((i for i, v in enumerate(nums) if v > mid * 1000), len(lines))
        lines.insert(k, key + ' ' + name)
    assert hit <= 1
    out = '\r\n'.join(lines)
    return (b'\xef\xbb\xbf' + out.encode('utf-8')) if bom else out.encode('latin1')

def se_add(b, src_id, name):
    """Sound Editor custom names: <data><sounds><sound id=".." name=".." /></sounds></data> (UTF-8 BOM, CRLF)."""
    from xml.sax.saxutils import quoteattr
    t = b.decode('utf-8-sig'); nl = '\r\n' if '\r\n' in t else '\n'
    assert 'id="%d"' % src_id not in t, 'Sound Editor already has id %d' % src_id
    entry = '    <sound id="%d" name=%s />' % (src_id, quoteattr('THEME ' + name))
    if '<sounds />' in t: t = t.replace('<sounds />', '<sounds>' + nl + entry + nl + '  </sounds>', 1)
    else:
        assert t.count('</sounds>') == 1, 'unexpected custom_data.xml layout'
        t = t.replace('  </sounds>', entry + nl + '  </sounds>', 1) if '  </sounds>' in t else t.replace('</sounds>', entry + nl + '</sounds>', 1)
    return b'\xef\xbb\xbf' + t.encode('utf-8')

def string_ids(pac, file_index=0):
    H = HSPC(pac); S = SHDC(H.files[file_index]['data'])
    _, ents = string_table_parse(S.files[0]['data'])
    return {i: t for i, t in ents}

def free_ids(src, P, de=None):
    """IDs that are safe for a new slot. All must hold:
    - VMUM: exactly one row with field2 == id, and it is an empty slot (f0 = f1 = key = 0);
    - key id*100000 is above the sorted tail start (else the game's bsearch cannot reach it);
    - no Play_MUS_<id> event in the DLC_30 bank, no BGM.lsd entry, no MEMU record for id*1000;
    - strings 13000+id and 3000+id absent or empty (ID 150 was Michael Cole's string 3150: never again)."""
    _, o, h, recs = vmum_load_bytes(src['vmum'])
    keys = [r[4] for r in recs]
    tail_start = next(k for k in range(len(recs)) if keys[k] > 0 and k > 0 and keys[k - 1] == 0)
    tail0 = keys[tail_start]
    empty = {}
    for r in recs:
        empty.setdefault(r[2], []).append(r[0] == 0 and r[1] == 0 and r[4] == 0 and r[3] == 0)
    bank_ids = {oid for _, oid, _ in hirc_objs([c for c in chunks(P['data'][('B', DLC30_BANK)]) if c[0] == b'HIRC'][0][1])}
    H = HSPC(src['cae']); S = SHDC(H.files[0]['data']); d = [x for x in S.files if x['id'] == 2][0]['data']
    n = struct.unpack_from('<H', d, 0)[0]
    bgm = {struct.unpack_from('<I', d, 4 + 40 * k)[0] for k in range(n)}
    H = HSPC(src['memu']); S = SHDC(H.files[0]['data']); d = [x for x in S.files if x['id'] == 6][0]['data']
    n = struct.unpack_from('<I', d, 4)[0]
    memu = {struct.unpack_from('<I', d, 8 + 32 * k + 12)[0] for k in range(n)}
    strs = string_ids(src['str'])
    de_named = set()
    if de is not None:   # ids the Data Editor list already names (community-reserved, e.g. 179000 Mark Henry) are taken
        for ln in de.decode('latin1').split('\r\n'):
            f = ln.split(' ', 1)
            if f[0].isdigit() and len(f) == 2 and f[1].strip(): de_named.add(int(f[0]) // 1000)
    out = []
    for mid in range(100, 1000):
        if empty.get(mid) != [True]: continue
        if mid * 100000 <= tail0: continue
        if fnv('Play_MUS_%04d_00_0_0' % mid) in bank_ids: continue
        if mid * 1000 in bgm or mid * 1000 in memu or mid in de_named: continue
        if any(strs.get(s, b'\0').strip(b'\0') for s in (13000 + mid, 3000 + mid)): continue
        out.append(mid)
    return out

def load_slots(a):
    """Slots from --spec (JSON list of {"name", "wem", optional "id", optional "label"}) or the old --id/--name/--wem."""
    if a.spec:
        base = os.path.dirname(os.path.abspath(a.spec))
        sl = json.load(open(a.spec, encoding='utf-8'))
        for s in sl:
            assert s.get('name') and s.get('wem'), 'each slot needs "name" and "wem": %r' % s
            if not os.path.isabs(s['wem']): s['wem'] = os.path.join(base, s['wem'])
        return sl
    assert a.id and a.name and a.wem, 'give --spec, or --wem with --id/--name'
    assert len(a.name) == len(a.id), 'give one --name per --id'
    return [{'id': i, 'name': n, 'wem': a.wem} for i, n in zip(a.id, a.name)]

def main():
    ap = argparse.ArgumentParser(description='Build new WWE 2K19 music slots into an output folder.')
    ap.add_argument('--game', required=True, help='install (or a tree of the original files) to build from')
    ap.add_argument('--spec', help='JSON list of slots: [{"name": "Song", "wem": "song.wem", "id": 123 (optional)}]')
    ap.add_argument('--wem'); ap.add_argument('--id', type=int, action='append'); ap.add_argument('--name', action='append')
    ap.add_argument('--tools', help='modding folder holding Data Editor and Sound Editor; their name lists get the new songs')
    ap.add_argument('--menu-steps', help='e.g. 300,400,500: also write drop-in cae_item_p30.pac files listing the first N '
                    'slots in the Create-an-Entrance menu (slots with "menu": false are left out of the main build)')
    ap.add_argument('--fill', help='create every free id: "<name pattern>,<wem>,<menu count>", e.g. "Custom %03d,ph.wem,200"')
    ap.add_argument('--out'); ap.add_argument('--list-free', action='store_true', help='print free ids and exit')
    a = ap.parse_args(); G = a.game
    src = {k: open(os.path.join(G, v), 'rb').read() for k, v in PATHS.items()}
    P = akpk_read(src['pck'])
    tsrc = {k: open(os.path.join(a.tools, v), 'rb').read() for k, v in TOOL_PATHS.items()} if a.tools else {}
    free = free_ids(src, P, tsrc.get('de'))
    if a.list_free:
        print(len(free), 'free ids:', ' '.join(map(str, free))); return
    assert a.out, '--out is required'
    if a.fill:
        pat, wem, nmenu = a.fill.rsplit(',', 2); nmenu = int(nmenu)
        slots = [{'id': m, 'name': pat % (k + 1), 'wem': wem, 'menu': k < nmenu} for k, m in enumerate(free)]
    else:
        slots = load_slots(a)
    taken = [s['id'] for s in slots if s.get('id') is not None]
    assert len(set(taken)) == len(taken), 'duplicate id in spec'
    for mid in taken: assert mid in free, 'id %d is not free (see --list-free)' % mid
    pool = [m for m in free if m not in taken]
    for s in slots:
        if s.get('id') is None: s['id'] = pool.pop(0)
        for ch in s['name'] + s.get('label', ''):
            assert ord(ch) < 256, 'name must be Latin-1 (the string table is 8-bit): %r' % s['name']
    man = {'slots_spec': slots, 'inputs': {k: {'path': PATHS[k], 'md5': md5(v), 'size': len(v)} for k, v in src.items()},
           'slots': []}
    for k, v in tsrc.items(): man['inputs'][k] = {'path': TOOL_PATHS[k], 'root': 'tools', 'md5': md5(v), 'size': len(v)}
    de, se = tsrc.get('de'), tsrc.get('se')
    vm, st, cae, memu = src['vmum'], src['str'], src['cae'], src['memu']
    newstr = {}; wems = {}
    for s in slots:
        mid, name = s['id'], s['name']; label = s.get('label') or name.upper()
        if s['wem'] not in wems: wems[s['wem']] = open(s['wem'], 'rb').read()
        wem = wems[s['wem']]; wi = wem_info(wem)
        src_id = fnv('wwe2k19mod_wem_%04d' % mid)
        assert ('S', src_id) not in P['data']
        newbank, ids = add_track(P['data'][('B', DLC30_BANK)], mid, src_id, wi['inmem'])
        P['data'][('B', DLC30_BANK)] = newbank
        P['streams'].append([src_id, 1, len(wem), 1 << 30, 0]); P['data'][('S', src_id)] = wem
        vm, row = activate_row(vm, mid)
        newstr[13000 + mid] = name    # name (mixed case)
        newstr[3000 + mid] = label    # menu label (upper case, as in BGM.lsd)
        bgm = None
        if s.get('menu', True): cae, bgm = add_bgm_entry(cae, mid)
        memu, mrec = add_memu_record(memu, mid, 3000 + mid, 13000 + mid)
        if de is not None: de = de_add(de, mid, name)
        if se is not None: se = se_add(se, src_id, name)
        man['slots'].append({'id': mid, 'name': name, 'label': label, 'menu': bool(bgm), 'wem': s['wem'], 'wem_md5': md5(wem),
                             'wem_info': wi, 'event_ids': ids, 'source_id': src_id, 'row': row, 'bgm': bgm, 'memu': mrec})
    st, _ = add_strings(st, newstr)
    pck = akpk_write(P)
    out = {'pck': pck, 'vmum': vm, 'str': st, 'cae': cae, 'memu': memu}
    for k, v in out.items():
        p = os.path.join(a.out, PATHS[k]); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(v)
    man['outputs'] = {k: {'path': PATHS[k], 'md5': md5(v), 'size': len(v)} for k, v in out.items()}
    for k, v in (('de', de), ('se', se)):
        if v is None: continue
        p = os.path.join(a.out, 'tools', TOOL_PATHS[k]); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(v)
        man['outputs'][k] = {'path': TOOL_PATHS[k], 'root': 'tools', 'md5': md5(v), 'size': len(v)}
    if a.menu_steps:
        hidden = [x['id'] for x in man['slots'] if not x['menu']]; shown = len(man['slots']) - len(hidden)
        man['menu_steps'] = {}
        for n in sorted(int(v) for v in a.menu_steps.split(',')):
            n = min(n, len(man['slots'])); c = cae
            for mid in hidden[:max(0, n - shown)]: c, _ = add_bgm_entry(c, mid)
            p = os.path.join(a.out, 'menu_steps', 'menu_%03d' % n, PATHS['cae']); os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, 'wb').write(c); man['menu_steps'][n] = md5(c)
    with open(os.path.join(a.out, 'slots.csv'), 'w', encoding='utf-8', newline='') as f:
        f.write('id,music_value,name,in_menu,sound_editor_id\r\n')
        for x in man['slots']: f.write('%d,%d,"%s",%s,%d\r\n' % (x['id'], x['id'] * 1000, x['name'], 'yes' if x['menu'] else 'no', x['source_id']))
    open(os.path.join(a.out, 'manifest.json'), 'w').write(json.dumps(man, indent=1, default=str))
    print(json.dumps({'slots': [(s['id'], s['name']) for s in man['slots']], 'outputs': man['outputs']}, indent=1))

if __name__ == '__main__':
    main()

r"""Open entrance-video ("GFX") slots in Create an Entrance: add menu entries for every video set that has none.

  python3 gfxslots.py --game-copy <dir with pac/menu/cae_item*.pac and mods/SuperString/.../string_win.pac>
      --videos tron_movie_ids.txt --cct "<A - CCT folder>" --out <build dir> [--all-ids]

Facts used (writeup/GFX_slots.md): .lsd lists are concatenated base+p10+p20+p30 by their own counts (no fixed size);
an entry is listed when its five unlock ids (+4..+0xC) are all -1 and u16 +0x16 != 0 (0x140c1eb50). Entry written =
the form Matthew's Wrestleminus entries already use in game: value, -1, -1, 0x0000FFFF, -1, -1, name string,
0xFFFF0001, 0, 0. Lists: SHDC ids 1, 42, 43, 44 of cae_item_p30.pac (appended at the end of the last list).
Names: new strings 44000 + id ("<CCT name> (id)"), variants (value % 100 != 0) 47000 + running number.
--all-ids also adds every id 100-999 that has no video set yet (variant 00)."""
import argparse, hashlib, json, os, re, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from yukes import HSPC, SHDC, string_table_parse, string_table_build
LISTS = (1, 42, 43, 44); PACS = ('', '_p10', '_p20', '_p30')
md5 = lambda b: hashlib.md5(b).hexdigest()
def lst(pac, fid):
    S = SHDC(HSPC(pac).files[0]['data']); f = [x for x in S.files if x['id'] == fid]
    if not f or len(f[0]['data']) < 4: return []
    d = f[0]['data']; n = struct.unpack_from('<H', d, 0)[0]
    return [struct.unpack_from('<10I', d, 4 + 40 * k) for k in range(n)]
def names(cct):
    d = open(os.path.join(cct, 'data.xml'), encoding='utf8', errors='replace').read()
    r = open(os.path.join(cct, 'replaced_data.xml'), encoding='utf8', errors='replace').read()
    sec = lambda x: x.split('<lists>')[-1].split('<superstars>')[1].split('</superstars>')[0]
    out = {}; slot2id = {}
    for s, i, n in re.findall(r'slotNumber="(\d+)" slotId="(\d+)" name="([^"]*)"', sec(d)): slot2id[s] = int(i); out[int(i)] = n
    for s, n in re.findall(r'slotNumber="(\d+)" name="([^"]*)"', sec(r)):
        if s in slot2id and n.strip(): out[slot2id[s]] = n
    clean = lambda n: re.sub(r'\s+', ' ', re.sub(r'\|.*$|\bAVAILABLE\b|\bGFX\b|\(Selectable\)|&amp;', ' ', n)).strip(' -|')
    return {i: clean(n) for i, n in out.items()}
def main():
    a = argparse.ArgumentParser(); a.add_argument('--game-copy', required=True); a.add_argument('--videos', required=True)
    a.add_argument('--cct', required=True); a.add_argument('--out', required=True); a.add_argument('--all-ids', action='store_true')
    a = a.parse_args(); G = a.game_copy
    vids = set()
    for l in open(a.videos): vids |= {int(x) for x in l.split(':')[1].split() if x.isdigit()}
    if a.all_ids: vids |= {i * 100 for i in range(100, 1000)}
    pacs = {p: open(f'{G}/pac/menu/cae_item{p}.pac', 'rb').read() for p in PACS}
    spath = f'{G}/mods/SuperString/pac/string/win/string_win.pac'; sp = open(spath, 'rb').read()
    H = HSPC(pacs['_p30']); S = SHDC(H.files[0]['data']); nm = names(a.cct)
    need = {}; report = {'lists': {}}
    for fid in LISTS:
        have = set()
        for p in PACS: have |= {e[0] for e in lst(pacs[p], fid)}
        add = sorted(vids - have); need[fid] = add
        f = [x for x in S.files if x['id'] == fid][0]; d = f['data']; n, tot = struct.unpack_from('<HH', d, 0)
        assert len(d) == 4 + 40 * n
        report['lists'][fid] = {'before': n, 'added': len(add), 'total_all_levels': len(have) + len(add)}
        f['_n'], f['_tot'], f['_add'] = n, tot, add
    allv = sorted(set().union(*need.values())); sid = {}; k = 0; strings = {}
    for v in allv:
        i, var = divmod(v, 100)
        if var == 0: sid[v] = 44000 + i
        else: sid[v] = 47000 + k; k += 1
        base = (nm.get(i) or 'TRON').upper()
        strings[sid[v]] = f'{base} ({i})' if var == 0 else f'{base} ({i}-{var:02d})'
    Hs = HSPC(sp); Ss = SHDC(Hs.files[0]['data']); pre, ents = string_table_parse(Ss.files[0]['data']); d = dict(ents)
    clash = [s for s in strings if s in d and d[s].rstrip(b'\0').decode('latin1') != strings[s]]
    assert not clash, f'string ids in use: {clash[:5]}'
    for s, t in strings.items(): d[s] = t.encode('latin1', 'replace') + b'\0'
    Ss.files[0]['data'] = string_table_build(pre, sorted(d.items())); new_sp = Hs.replace(0, Ss.build())
    for fid in LISTS:
        f = [x for x in S.files if x['id'] == fid][0]
        ents2 = b''.join(struct.pack('<10I', v, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFF, 0xFFFFFFFF, 0xFFFFFFFF, sid[v], 0xFFFF0001, 0, 0) for v in f['_add'])
        f['data'] = struct.pack('<HH', f['_n'] + len(f['_add']), f['_tot'] + len(f['_add'])) + f['data'][4:] + ents2
        for k_ in ('_n', '_tot', '_add'): f.pop(k_)
    new_p30 = H.replace(0, S.build())
    # verify by re-parse
    for fid in LISTS:
        got = lst(new_p30, fid); assert len(got) == report['lists'][fid]['before'] + report['lists'][fid]['added']
        assert [e[0] for e in got[-len(need[fid]):]] == need[fid] if need[fid] else True
    for other in [x['id'] for x in SHDC(HSPC(pacs['_p30']).files[0]['data']).files if x['id'] not in LISTS]:
        assert lst(new_p30, other) == lst(pacs['_p30'], other), other
    _, e2 = string_table_parse(SHDC(HSPC(new_sp).files[0]['data']).files[0]['data']); d2 = dict(e2)
    assert all(d2[s].rstrip(b'\0').decode('latin1') == t.encode('latin1', 'replace').decode('latin1') for s, t in strings.items()) and len(d2) >= len(ents)
    os.makedirs(a.out + '/pac/menu', exist_ok=True); os.makedirs(a.out + '/mods/SuperString/pac/string/win', exist_ok=True)
    open(a.out + '/pac/menu/cae_item_p30.pac', 'wb').write(new_p30)
    open(a.out + '/mods/SuperString/pac/string/win/string_win.pac', 'wb').write(new_sp)
    report.update(strings=len(strings), files={
        'pac/menu/cae_item_p30.pac': {'before': md5(pacs['_p30']), 'after': md5(new_p30), 'size': len(new_p30)},
        'mods/SuperString/pac/string/win/string_win.pac': {'before': md5(sp), 'after': md5(new_sp), 'size': len(new_sp)}})
    json.dump(report, open(a.out + '/manifest.json', 'w'), indent=1)
    open(a.out + '/entries.tsv', 'w').write('value\tstring_id\tname\tlists\n' + ''.join(
        f"{v}\t{sid[v]}\t{strings[sid[v]]}\t{','.join(str(f) for f in LISTS if v in need[f])}\n" for v in allv))
    print(json.dumps(report, indent=1))
if __name__ == '__main__': main()

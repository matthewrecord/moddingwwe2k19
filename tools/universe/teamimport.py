"""Team import for Universe (option A, 2026-11-11): rebuild the game's default Universe team list from Matthew's
MyWWE team table, so every NEW Universe starts with his teams (the game's own seeding does the rest).

Files (all found 2026-11-10/11, writeup/Universe_QoL.md):
  pac/universe/wunistable.pac : HSPC; uncompressed LBTS table at 0x1864: 'LBTS', u32 0x110, u32 100, pad, then 100
      entries of 0x110 bytes: +0x00 5 x u16 members (0x400 empty), +0x0E u8 member count, +0x10 u16 team graphic
      (0xFFFF none), +0x2A.. AI/rating fields, +0x100 u32 name string id, +0x104 u32 short-name string id.
      Vanilla: entries 0-22 + 24 = the 25 default teams; the rest empty (name ids 0xFFFFFFFF).
  main team table (MyWWE, CCT 0x14287C860): 200 records of 0x1B8: +0x00 5 x u16 members, +0x0E u8 count, +0x10 u16
      graphic, +0x100 name text. Taken from a live dump (slots DLL test3+ slots_mem.request '14287c860 15800').
  mods/SuperString/pac/string/win/string_win.pac : English strings (HSPC > SHDC > string table). Team names live at
      16000+n (full) / 16100+n (short). New names go to free ids from NEW_BASE up.

Rules: vanilla default teams keep their entries. Every MyWWE team (non-empty name and >= 2 members) whose name is not
already a default entry gets a free entry. Names reuse an existing string with the same text in 16000-16199, else a
new string id. Template per member count: 2 -> entry 2 (THE REVIVAL), 3 -> entry 4 (TITUS WORLDWIDE), 4+ -> entry 22
(THE UNDISPUTED ERA); members, count, graphic and names are replaced.

usage: python3 teamimport.py --game <game dir> --main <main_teams.bin> [--out <dir>] [--dry-run]
       writes <out>/wunistable.pac and <out>/string_win.pac (install = copy over the game files, backups first)."""
import argparse, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yukes import HSPC, SHDC, string_table_parse, string_table_build

LBTS_OFF, ENT, NENT, MREC = 0x1864, 0x110, 100, 0x1B8
NEW_BASE = 39600                       # free range checked at run time (39370+ = character names)
TEMPLATE = {2: 2, 3: 4}                # member count -> template entry; 4+ -> 22

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--game', required=True); ap.add_argument('--main', required=True)
    ap.add_argument('--out', default='.'); ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--mine-only', action='store_true', help='only the MyWWE teams (no vanilla defaults kept)'); a = ap.parse_args()
    wp = os.path.join(a.game, 'pac', 'universe', 'wunistable.pac')
    orig = os.path.join(a.game, 'pac', 'universe', 'wunistable.pac.orig_teams')
    b = bytearray(open(orig if os.path.exists(orig) else wp, 'rb').read())   # always start from the vanilla file
    assert b[LBTS_OFF:LBTS_OFF + 4] == b'LBTS' and struct.unpack_from('<2I', b, LBTS_OFF + 4) == (ENT, NENT)
    B = LBTS_OFF + 16
    sp = os.path.join(a.game, 'mods', 'SuperString', 'pac', 'string', 'win', 'string_win.pac')
    H = HSPC(open(sp, 'rb').read()); S = SHDC(H.files[0]['data'])
    pre, ents = string_table_parse(S.files[0]['data']); strings = dict(ents)
    def text(i): s = strings.get(i); return s[:-1].decode('latin-1') if s else None
    # default entries and their names
    used, default_names = set(), set()
    for i in range(NENT):
        nid = struct.unpack_from('<I', b, B + i * ENT + 0x100)[0]
        if nid != 0xFFFFFFFF: used.add(i); default_names.add((text(nid) or '').upper())
    templates = {k: bytes(b[B + v * ENT:B + (v + 1) * ENT]) for k, v in list(TEMPLATE.items()) + [(4, 22)]}
    if a.mine_only:                                    # clear every entry (empty entry = vanilla entry 23's layout)
        empty = bytes(b[B + 23 * ENT:B + 24 * ENT])
        for i in range(NENT): b[B + i * ENT:B + (i + 1) * ENT] = empty
        used, default_names = set(), set()
    free = [i for i in range(NENT) if i not in used]
    # MyWWE teams
    m = open(a.main, 'rb').read(); teams = []
    for r in range(min(100 if a.mine_only else 200, len(m) // MREC)):   # mine-only: MyWWE created-team rows 0-99 (rows 100+ = vanilla leftovers)
        rec = m[r * MREC:(r + 1) * MREC]
        name = rec[0x100:0x158].split(b'\0')[0].decode('latin-1').strip()
        mem = [v for v in struct.unpack_from('<5H', rec, 0) if v != 0x400]
        if not name or not name.isprintable() or len(mem) < 2 or any(v >= 0x400 for v in mem): continue
        if name.upper() in default_names or (not a.mine_only and any(t['name'].upper() == name.upper() for t in teams)): continue
        teams.append(dict(row=r, name=name, members=mem, graphic=struct.unpack_from('<H', rec, 0x10)[0]))
    by_text = {}
    for i in list(range(16000, 16200)) + list(range(NEW_BASE, NEW_BASE + 400)):
        t = text(i)
        if t: by_text.setdefault(t.upper(), i)
    nxt = NEW_BASE; plan = []
    for t in teams[:len(free)]:
        sid = by_text.get(t['name'].upper())
        if sid is None:
            while nxt in strings: nxt += 1
            sid = nxt; strings[sid] = t['name'].encode('latin-1', 'replace') + b'\0'; nxt += 1; t['new_string'] = True
        e_i = free.pop(0)
        e = bytearray(templates[min(len(t['members']), 4)])
        for k in range(5): struct.pack_into('<H', e, 2 * k, t['members'][k] if k < len(t['members']) else 0x400)
        e[0x0E] = len(t['members']); struct.pack_into('<H', e, 0x10, t['graphic'])
        struct.pack_into('<2I', e, 0x100, sid, sid)
        b[B + e_i * ENT:B + (e_i + 1) * ENT] = e
        plan.append((e_i, t, sid))
    skipped = teams[len(plan):]
    for e_i, t, sid in plan:
        print(f"entry {e_i:2d}: {t['name']:<28} members {t['members']} graphic {t['graphic']:#x} name id {sid}"
              f"{' (new string)' if t.get('new_string') else ''}")
    print(f'{len(plan)} teams added, {len(skipped)} did not fit: {[t["name"] for t in skipped]}')
    if a.dry_run: return
    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(a.out, 'wunistable.pac'), 'wb').write(b)
    S.files[0]['data'] = string_table_build(pre, sorted(strings.items()))
    open(os.path.join(a.out, 'string_win.pac'), 'wb').write(H.replace(0, S.build()))
    print('written to', a.out)

if __name__ == '__main__':
    main()

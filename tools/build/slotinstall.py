r"""Install wrestlers from the pictures folder into overflow slots (profile index 509+, "slot 510+"), for the
tools/slots proxy dinput8.dll. Runs on Matthew's PC (plain Python 3, no packages); the game must be closed.

  python3 slotinstall.py --game "<WWE 2K19 folder>" --pictures "<pictures WWE 2K19 folder>" --spec slots_to_add.txt
  python3 slotinstall.py --game ... --list                 # installed overflow slots
  python3 slotinstall.py --game ... --dry-run --spec ...   # check everything, write nothing
  python3 slotinstall.py --game ... --remove 511 [515 ...]  # remove installed slots (slot numbers as listed)
    removal moves the slot files and the slot's model pacs to _to_delete\ in the game folder (the agent shell
    cannot delete), drops their Chunk0.def lines and the name string; the slot number and id become free again.

Spec file: one wrestler per line, fields separated by '|', only the first is required; '#' starts a comment.
  Folder | Display name | pofo file | moveset file | model files (comma separated) | render (.OODL or .dds)
  A-Kid
  Angel Garza | Angel Garza | Angel Garza [Mod] 930.pofo
Defaults: display name = folder name; the folder's only .pofo / .moveset (several -> name one, the run stops with
a list); models = every ch<5 digits>*.pac in the folder (EPK8 format; HSPC-format pacs are reported and skipped);
attire = the last two digits of the ch number (ch14502 -> 02); two files with the same attire -> name them.

Same conventions as Test Wrestler (handoff 012, notes/characters step 1j):
- slot index: next free from 509 up (Matthew's "slot 510" = index 509).
- character id: checked on every run. Free = not the id of any profile row (the PerfectPlextra rows 938-949 are
  allowed: they sit beyond the 509 cap and never load; 950-999 are Matthew's converted CAW slots 50-99 and LIVE),
  no model in pac\ch or mods\CCT, no CCT line in Chunk0.def, no unlockable (HID, misc01_start) for it, no slot.
  Order: 938-949 first (next to Test Wrestler's 937), then ascending (109, 110, 114, ...; 381 free on 2026-11-10).
- name string id = 39370 + (id - 937) (checked free).
- slots\\IIII_DDDD_SSSS.pofo/.moveset (SSSS = the pofo's original id: its 40-byte per-slot record is cloned).
- pofo: +0 id, +2 index, name string ids (every name field equal to +0x08) -> the new name string.
- models -> mods\\CCT\\characters\\pac\\ch\\ch<id><att>.pac with the internal name at 0x80C set to 000<id><att>.
- Chunk0.def: one line per new file, inserted in sorted position. Name: SuperString English table.
- Backups: <file>.orig_charslot (first original only, never overwritten). Install log: slots\\installed.json.
- render: the folder's .OODL (Oodle Tools output) if there is exactly one, else its .dds (stored, ~1 MB pac);
  several -> name one in spec field 6. Written as custom_typea and custom_typeb\0<id>00.pac (renderpac.py).
  `--renders 511 512 514=Darby_Allin_New.dds ...` adds/replaces renders for installed slots.
- `--from-game 511=925 512=799 ...`: copy the renders AND Titantrons the wrestler already has in the game (CCT id
  on the right) to the slot's id, with internal names rewritten (renders: MD5 name; trons: M0<id>00), plus the big
  Titantron videos movies\titantron\ent_<id>_*.bk2 (loose Bink files named by character id, copied as is).
  The five Titantron parts: apron, wall, mini (banner), ramp = ss_* pacs; main screen = ent_ videos. Preferred
  when the wrestler is installed with CCT: the exact in-game assets, plus Titantrons.
Titantrons from .bk2 are not built yet (MVS pac writer still to do).
"""
import argparse, glob, json, os, re, shutil, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..', 'audio')]
from yukes import HSPC, SHDC, string_table_parse, string_table_build
from bpe import expand
import renderpac

STR = 'mods/SuperString/pac/string/win/string_win.pac'
PROF = 'mods/PerfectPlextra/pac/profile/profile_dat.pac'
CH_DIR = 'mods/CCT/characters/pac/ch'
RENDER_DIR = 'mods/CCT/renders/pac/menu/win/Assets/wwe19_singleread/texture/ssface'
RENDER_TPL = os.path.join(HERE, 'render_template.pac')
NAME_OFF = 0x80C
DEAD_OK = set(range(938, 950))
def sid_for(cid): return 39370 + (cid - 937)

def die(msg): print('STOPPED, nothing written:', msg); sys.exit(1)

def backup(path):
    b = path + '.orig_charslot'
    if not os.path.exists(b): shutil.copyfile(path, b)

def parse_spec(path):
    out = []
    for ln in open(path, encoding='utf-8-sig'):
        ln = ln.split('#', 1)[0].strip()
        if not ln: continue
        f = [x.strip() for x in ln.split('|')] + [''] * 6
        out.append({'folder': f[0], 'name': f[1] or f[0], 'pofo': f[2], 'moveset': f[3],
                    'models': [m.strip() for m in f[4].split(',') if m.strip()], 'render': f[5]})
    return out

def pick(folder, ext, given, label):
    if given:
        p = os.path.join(folder, given)
        if not os.path.isfile(p): die('%s: %s not found' % (folder, given))
        return p
    c = sorted(glob.glob(os.path.join(folder, '*' + ext)))
    if len(c) == 1: return c[0]
    if not c: die('%s: no %s file' % (folder, ext))
    die('%s: several %s files, name one in the spec (field %s): %s' % (folder, ext, label, [os.path.basename(x) for x in c]))

def models_for(folder, given):
    files = [os.path.join(folder, g) for g in given] if given else \
        sorted(p for p in glob.glob(os.path.join(folder, '*.pac')) if re.search(r'ch\d{5}', os.path.basename(p).lower()))
    out, skipped = {}, []
    for p in files:
        if not os.path.isfile(p): die('%s not found' % p)
        hdr = open(p, 'rb').read(NAME_OFF + 8)
        if hdr[:4] != b'EPK8' or hdr[0x800:0x804] != b'EMD ': skipped.append(os.path.basename(p)); continue
        att = re.search(r'ch\d{3}(\d{2})', os.path.basename(p).lower()).group(1)
        if att in out: die('%s: two models for attire %s (%s, %s): name the ones to use' %
                           (folder, att, os.path.basename(out[att]), os.path.basename(p)))
        out[att] = p
    return out, skipped

def dec(b):
    if b[:4] != b'BPE ': return b
    h = struct.unpack('<4I', b[4:20]); return expand(b, 16, h[2])[0]

def id_pool(game, slots):
    """Ids safe for a new character: see the module docstring."""
    used = used_ids(game, slots)
    for f in SHDC(HSPC(open(os.path.join(game, PROF), 'rb').read()).files[0]['data']).files:
        cid = struct.unpack_from('<H', dec(f['data']), 4)[0]
        if cid not in DEAD_OK or f['id'] < 509: used.add(cid)
    for d in ('pac/ch', CH_DIR):
        for fn in os.listdir(os.path.join(game, d)):
            m = re.match(r'ch(\d{3})\d{2}', fn.lower())
            if m: used.add(int(m.group(1)))
    mp = os.path.join(game, 'pac/root/misc01_start.pac')
    hid = [dec(f['data']) for f in SHDC(HSPC(open(mp, 'rb').read()).files[0]['data']).files if f['id'] == 6][0]
    assert hid[:4] == b'HID\x00'
    for i in range(struct.unpack_from('<I', hid, 4)[0]): used.add(struct.unpack_from('<I', hid, 8 + 32 * i + 0x10)[0])
    return [i for i in sorted(DEAD_OK) if i not in used] + [i for i in range(100, 1000) if i not in used and i not in DEAD_OK]

def find_render(folder, given):
    if given:
        p = os.path.join(folder, given)
        if not os.path.isfile(p): die('%s not found' % p)
        return p
    for ext in ('.OODL', '.dds'):
        c = sorted(p for p in glob.glob(os.path.join(folder, '*')) if p.lower().endswith(ext.lower()))
        if len(c) == 1: return c[0]
        if len(c) > 1: die('%s: several %s files, name the render (spec field 6, or --renders SLOT=file): %s' % (folder, ext, [os.path.basename(x) for x in c]))
    return None

def write_renders(G, chunk, cid, src):
    data = open(src, 'rb').read()
    oodl = data if data[:4] == b'OODL' else renderpac.oodl_from_dds(data)
    if not os.path.exists(RENDER_TPL): die('render_template.pac missing next to slotinstall.py')
    tpl = open(RENDER_TPL, 'rb').read()
    for kind in 'ab':
        rel = '%s/custom_type%s/0%03d00.pac' % (RENDER_DIR, kind, cid); dst = os.path.join(G, rel)
        open(dst, 'wb').write(renderpac.build(tpl, oodl, kind, cid))
        chunk_insert(chunk, rel.replace('/', '\\').lower().encode())


def used_ids(game, slots):
    used = {s['id'] for s in slots}
    for ln in open(os.path.join(game, 'Chunk0.def'), 'rb').read().split(b'\r\n'):
        m = re.search(rb'\\ch(\d{3})\d{2}\.pac$', ln.lower()) or re.search(rb'\\0(\d{3})00\.pac$', ln.lower())
        if m and ln.lower().startswith(b'mods\\cct\\'): used.add(int(m.group(1)))
    return used

def chunk_insert(lines, new_line):
    k = new_line.lower(); d = k.rsplit(b'\\', 1)[0] + b'\\'
    if any(x.lower() == k for x in lines): return
    idx = [i for i, y in enumerate(lines) if y.lower().startswith(d) and y.lower().count(b'\\') == k.count(b'\\')]
    pos = next((i for i in idx if lines[i].lower() > k), (idx[-1] + 1) if idx else len(lines))
    lines.insert(pos, new_line)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', required=True); ap.add_argument('--pictures'); ap.add_argument('--spec')
    ap.add_argument('--list', action='store_true'); ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--remove', type=int, nargs='+', metavar='SLOT')
    ap.add_argument('--renders', nargs='+', metavar='SLOT[=file]')
    ap.add_argument('--from-game', nargs='+', metavar='SLOT=ID')
    a = ap.parse_args(); G = a.game
    sdir = os.path.join(G, 'slots'); os.makedirs(sdir, exist_ok=True)
    logp = os.path.join(sdir, 'installed.json')
    inst = json.load(open(logp)) if os.path.exists(logp) else []
    present = []
    for p in glob.glob(os.path.join(sdir, '*.pofo')):
        m = re.match(r'(\d{4})_(\d{4})(?:_(\d{4}))?\.pofo$', os.path.basename(p))
        if m: present.append({'index': int(m.group(1)), 'id': int(m.group(2))})
    if a.remove:
        try:
            for p in (os.path.join(G, STR), os.path.join(G, 'Chunk0.def')): open(p, 'r+b').close()
        except OSError: die('game files are locked: close the game first')
        for p in (STR, 'Chunk0.def'): backup(os.path.join(G, p))
        trash = os.path.join(G, '_to_delete'); os.makedirs(trash, exist_ok=True)
        sp = open(os.path.join(G, STR), 'rb').read(); H = HSPC(sp); S = SHDC(H.files[0]['data'])
        pre, ents = string_table_parse(S.files[0]['data']); strings = dict(ents)
        chunk = open(os.path.join(G, 'Chunk0.def'), 'rb').read().split(b'\r\n')
        for slot in a.remove:
            idx = slot - 1; s_ = next((x for x in present if x['index'] == idx), None)
            if not s_: die('no installed slot %d' % slot)
            cid = s_['id']
            for f in glob.glob(os.path.join(sdir, '%04d_%04d*' % (idx, cid))): shutil.move(f, os.path.join(trash, os.path.basename(f)))
            for f in glob.glob(os.path.join(G, CH_DIR, 'ch%03d??.pac' % cid)): shutil.move(f, os.path.join(trash, os.path.basename(f)))
            for kind in 'ab':
                f = os.path.join(G, RENDER_DIR, 'custom_type%s' % kind, '0%03d00.pac' % cid)
                if os.path.exists(f): shutil.move(f, os.path.join(trash, 'render_type%s_0%03d00.pac' % (kind, cid)))
            for t in ('ss_apron', 'ss_mini', 'ss_ramp', 'ss_wall'):
                f = os.path.join(G, 'mods/CCT/movies/pac/mov', t, '0%03d00.pac' % cid)
                if os.path.exists(f): shutil.move(f, os.path.join(trash, 'tron_%s_0%03d00.pac' % (t, cid)))
            for f in glob.glob(os.path.join(G, 'movies/titantron', 'ent_%04d_*.bk2' % cid)): shutil.move(f, os.path.join(trash, os.path.basename(f)))
            chunk = [l for l in chunk if not ((l.lower().startswith(b'mods\\cct\\renders\\') or l.lower().startswith(b'mods\\cct\\movies\\')) and l.lower().endswith(b'\\0%03d00.pac' % cid))]
            chunk = [l for l in chunk if not re.search(rb'\\ch%03d\d\d\.pac$' % cid, l.lower()) or not l.lower().startswith(b'mods\\cct\\characters\\')]
            info = next((x for x in inst if x['index'] == idx), {})
            if info.get('sid') in strings and info.get('sid') != 39370: del strings[info['sid']]
            inst = [x for x in inst if x['index'] != idx]
            print('removed slot %d (index %d, id %d) %s' % (slot, idx, cid, info.get('name', '')))
        S.files[0]['data'] = string_table_build(pre, sorted(strings.items()))
        open(os.path.join(G, STR), 'wb').write(H.replace(0, S.build()))
        open(os.path.join(G, 'Chunk0.def'), 'wb').write(b'\r\n'.join(chunk)); json.dump(inst, open(logp, 'w'), indent=1)
        return
    if a.from_game:
        try: open(os.path.join(G, 'Chunk0.def'), 'r+b').close()
        except OSError: die('game files are locked: close the game first')
        TRONS = ('ss_apron', 'ss_mini', 'ss_ramp', 'ss_wall'); MOV = 'mods/CCT/movies/pac/mov'
        todo = []
        for arg in a.from_game:
            slot, _, src = arg.partition('=')
            info = next((x for x in inst if x['index'] == int(slot) - 1), None)
            if not info or not src.isdigit(): die('bad %s (slot not installed, or no source id)' % arg)
            src = int(src); cid = info['id']; files = []
            for kind in 'ab':
                f = '%s/custom_type%s/0%03d00.pac' % (RENDER_DIR, kind, src)
                if os.path.exists(os.path.join(G, f)): files.append((f, f.replace('0%03d00' % src, '0%03d00' % cid), renderpac.render_name(kind, src), renderpac.render_name(kind, cid)))
            for t in TRONS:
                f = '%s/%s/0%03d00.pac' % (MOV, t, src)
                if os.path.exists(os.path.join(G, f)): files.append((f, '%s/%s/0%03d00.pac' % (MOV, t, cid), b'M0%03d00' % src, b'M0%03d00' % cid))
            ents = sorted(glob.glob(os.path.join(G, 'movies/titantron', 'ent_%04d_*.bk2' % src)))
            if not files and not ents: die('id %d has no CCT renders or Titantrons' % src)
            for f, _, old, _ in files:
                with open(os.path.join(G, f), 'rb') as fh: fh.seek(NAME_OFF); cur = fh.read(len(old))
                if cur != old: die('%s: internal name %r, expected %r' % (f, cur, old))
            todo.append((slot, info, src, files, ents))
        backup(os.path.join(G, 'Chunk0.def')); chunk = open(os.path.join(G, 'Chunk0.def'), 'rb').read().split(b'\r\n')
        for slot, info, src, files, ents in todo:
            for e in ents:
                d = os.path.join(os.path.dirname(e), os.path.basename(e).replace('ent_%04d_' % src, 'ent_%04d_' % info['id'], 1))
                if not os.path.exists(d): shutil.copyfile(e, d)
            for f, d, old, new in files:
                shutil.copyfile(os.path.join(G, f), os.path.join(G, d))
                with open(os.path.join(G, d), 'r+b') as fh: fh.seek(NAME_OFF); fh.write(new)
                chunk_insert(chunk, d.replace('/', '\\').lower().encode())
            info['assets_from_id'] = src
            print('slot %s (id %d) %s: %d files from id %d (%s) + %d big-Titantron videos' % (slot, info['id'], info['name'],
                  len(files), src, ', '.join(sorted({x[0].split('/')[-2] for x in files})), len(ents)))
        open(os.path.join(G, 'Chunk0.def'), 'wb').write(b'\r\n'.join(chunk)); json.dump(inst, open(logp, 'w'), indent=1)
        return
    if a.renders:
        if not a.pictures: die('--pictures is required')
        try: open(os.path.join(G, 'Chunk0.def'), 'r+b').close()
        except OSError: die('game files are locked: close the game first')
        backup(os.path.join(G, 'Chunk0.def')); chunk = open(os.path.join(G, 'Chunk0.def'), 'rb').read().split(b'\r\n')
        todo = []
        for arg in a.renders:                      # check everything first, then write
            slot, _, given = arg.partition('=')
            info = next((x for x in inst if x['index'] == int(slot) - 1), None)
            if not info: die('slot %s is not in slots\\installed.json' % slot)
            src = find_render(os.path.join(a.pictures, info['folder']), given)
            if not src: die('%s: no .OODL or .dds' % info['folder'])
            todo.append((int(slot), info, src))
        for slot, info, src in todo:
            write_renders(G, chunk, info['id'], src); info['render'] = os.path.basename(src)
            print('slot %d (id %d) %s: render from %s' % (slot, info['id'], info['name'], os.path.basename(src)))
        open(os.path.join(G, 'Chunk0.def'), 'wb').write(b'\r\n'.join(chunk)); json.dump(inst, open(logp, 'w'), indent=1)
        return
    if a.list or not a.spec:
        for s in sorted(present, key=lambda s: s['index']):
            info = next((x for x in inst if x['index'] == s['index']), {})
            print('slot %d (index %d)  id %d  %s' % (s['index'] + 1, s['index'], s['id'], info.get('name', '')))
        return
    if not a.pictures: die('--pictures is required')
    for p in (STR, 'Chunk0.def', CH_DIR):
        if not os.path.exists(os.path.join(G, p)): die('missing %s in the game folder' % p)
    try:
        for p in (os.path.join(G, STR), os.path.join(G, 'Chunk0.def')): open(p, 'r+b').close()
    except OSError: die('game files are locked: close the game first')

    spec = parse_spec(a.spec)
    pool = id_pool(G, present); used_idx = {s['index'] for s in present}; used = set()
    sp = open(os.path.join(G, STR), 'rb').read(); H = HSPC(sp); S = SHDC(H.files[0]['data'])
    pre, ents = string_table_parse(S.files[0]['data']); strings = dict(ents)
    chunk = open(os.path.join(G, 'Chunk0.def'), 'rb').read().split(b'\r\n')
    plan = []
    for w in spec:
        folder = os.path.join(a.pictures, w['folder'])
        if not os.path.isdir(folder): die('no folder %s' % folder)
        pofo_p = pick(folder, '.pofo', w['pofo'], 3); mov_p = pick(folder, '.moveset', w['moveset'], 4)
        pofo = bytearray(open(pofo_p, 'rb').read()); mov = open(mov_p, 'rb').read()
        if len(pofo) != 0x1E4 or len(mov) != 0xD88: die('%s: pofo/moveset sizes %d/%d' % (w['folder'], len(pofo), len(mov)))
        models, skipped = models_for(folder, w['models'])
        render = find_render(folder, w['render'])
        if not models: die('%s: no usable model pac (skipped: %s)' % (w['folder'], skipped))
        cid = next((i for i in pool if i not in used), None)
        idx = next((i for i in range(509, 1024) if i not in used_idx), None)
        if cid is None: die('no free character id left')
        sid = sid_for(cid)
        if sid in strings: die('name string %d already used' % sid)
        used.add(cid); used_idx.add(idx)
        src_id, old_sid = struct.unpack_from('<H', pofo, 0)[0], struct.unpack_from('<I', pofo, 8)[0]
        struct.pack_into('<HH', pofo, 0, cid, idx)
        for o in range(0, 0x1E4 - 3, 4):
            if o in (0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C, 0x1D0) and struct.unpack_from('<I', pofo, o)[0] == old_sid:
                struct.pack_into('<I', pofo, o, sid)
        if pofo[0x20] != 1: print('note: %s pofo is not flagged playable (+0x20 = %d): set to 1' % (w['folder'], pofo[0x20])); pofo[0x20] = 1
        plan.append({'name': w['name'], 'folder': w['folder'], 'index': idx, 'id': cid, 'source_id': src_id, 'sid': sid,
                     'pofo': bytes(pofo), 'moveset': mov, 'pofo_file': os.path.basename(pofo_p),
                     'moveset_file': os.path.basename(mov_p), 'models': models, 'skipped': skipped, 'render': render})
    for p in plan:
        print('slot %d (index %d)  id %d  "%s"  pofo %s, moveset %s, attires %s%s' % (
            p['index'] + 1, p['index'], p['id'], p['name'], p['pofo_file'], p['moveset_file'], sorted(p['models']) + ['render ' + (os.path.basename(p['render']) if p['render'] else 'NONE')],
            ('  SKIPPED (HSPC format): %s' % p['skipped']) if p['skipped'] else ''))
    if a.dry_run: print('dry run: nothing written'); return

    for p in (STR, 'Chunk0.def'): backup(os.path.join(G, p))
    for p in plan:
        strings[p['sid']] = p['name'].encode('latin1', 'replace') + b'\0'
        base = os.path.join(sdir, '%04d_%04d_%04d' % (p['index'], p['id'], p['source_id']))
        open(base + '.pofo', 'wb').write(p['pofo']); open(base + '.moveset', 'wb').write(p['moveset'])
        for att, src in sorted(p['models'].items()):
            dst_rel = '%s/ch%03d%s.pac' % (CH_DIR, p['id'], att); dst = os.path.join(G, dst_rel)
            if os.path.exists(dst): die('%s already exists (id %d in use?)' % (dst_rel, p['id']))
            shutil.copyfile(src, dst)
            with open(dst, 'r+b') as f: f.seek(NAME_OFF); f.write(b'000%03d%s' % (p['id'], att.encode()))
            chunk_insert(chunk, ('mods\\cct\\characters\\pac\\ch\\ch%03d%s.pac' % (p['id'], att)).encode())
        if p['render']: write_renders(G, chunk, p['id'], p['render'])
        inst.append({k: p[k] for k in ('name', 'folder', 'index', 'id', 'source_id', 'sid', 'pofo_file', 'moveset_file')} |
                    {'render': os.path.basename(p['render']) if p['render'] else None} |
                    {'models': {k: os.path.basename(v) for k, v in p['models'].items()}})
    S.files[0]['data'] = string_table_build(pre, sorted(strings.items()))
    open(os.path.join(G, STR), 'wb').write(H.replace(0, S.build()))
    open(os.path.join(G, 'Chunk0.def'), 'wb').write(b'\r\n'.join(chunk))
    json.dump(inst, open(logp, 'w'), indent=1)
    print('installed %d wrestler(s). Start the game; they appear in the superstar select screen.' % len(plan))

if __name__ == '__main__': main()

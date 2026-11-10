"""Rename existing music slots in place: game strings (13000+id name, 3000+id menu label), Data Editor list and Sound
Editor names. Never touches sound/patch_30.pck, so songs injected with Sound Editor are safe.

  python3 -I tools/build/rename.py --game "<install>" --tools "<modding folder>" --slots <slots.csv> \
      (--pattern "Custom %03d" | --set 109="Wrestler Name" [--set ...] | --csv names.csv) [--dry-run]

--pattern formats every slot in slots.csv by its game id. --csv: rows "id,name". Each changed file is backed up first as
<file>.bak_rename_<YYYYMMDD-HHMMSS>. Close the game, Data Editor and Sound Editor first (they cache these files).
"""
import argparse, csv, hashlib, os, re, shutil, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'audio'), os.path.join(HERE, '..', 'lib')]
from musicslot import PATHS, TOOL_PATHS, add_strings, string_ids
from xml.sax.saxutils import quoteattr

def md5(b): return hashlib.md5(b).hexdigest()

def de_rename(b, names):
    bom = b[:3] == b'\xef\xbb\xbf'
    t = b[3:].decode('utf-8') if bom else b.decode('latin1')
    lines = t.split('\r\n'); done = set()
    for k, ln in enumerate(lines):
        f = ln.split(' ', 1)
        if f[0].isdigit() and int(f[0]) % 1000 == 0 and int(f[0]) // 1000 in names:
            mid = int(f[0]) // 1000; lines[k] = f[0] + ' ' + names[mid]; done.add(mid)
    missing = set(names) - done; assert not missing, 'not in Data Editor list: %r' % sorted(missing)[:10]
    out = '\r\n'.join(lines)
    return (b'\xef\xbb\xbf' + out.encode('utf-8')) if bom else out.encode('latin1')

def se_rename(b, names_by_src):
    t = b.decode('utf-8-sig'); done = set()
    def sub(m):
        sid = int(m.group(1))
        if sid in names_by_src:
            done.add(sid); return '<sound id="%d" name=%s />' % (sid, quoteattr('THEME ' + names_by_src[sid]))
        return m.group(0)
    t = re.sub(r'<sound id="(\d+)" name="[^"]*" />', sub, t)
    missing = set(names_by_src) - done; assert not missing, 'not in Sound Editor list: %r' % sorted(missing)[:10]
    return b'\xef\xbb\xbf' + t.encode('utf-8')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', required=True); ap.add_argument('--tools', required=True); ap.add_argument('--slots', required=True)
    ap.add_argument('--pattern'); ap.add_argument('--set', action='append', default=[]); ap.add_argument('--csv')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    slots = {int(r['id']): r for r in csv.DictReader(open(a.slots, encoding='utf-8'))}
    names = {}
    if a.pattern: names.update({mid: a.pattern % mid for mid in slots})
    if a.csv: names.update({int(r[0]): r[1] for r in csv.reader(open(a.csv, encoding='utf-8')) if r and r[0].isdigit()})
    for s in a.set:
        k, v = s.split('=', 1); names[int(k)] = v
    assert names, 'nothing to rename'
    for mid, n in names.items():
        assert mid in slots, 'id %d is not one of our slots' % mid
        assert n and all(ord(c) < 256 for c in n), 'name must be non-empty Latin-1: %r' % n
    files = {'str': os.path.join(a.game, PATHS['str']), 'de': os.path.join(a.tools, TOOL_PATHS['de']),
             'se': os.path.join(a.tools, TOOL_PATHS['se'])}
    old = {k: open(p, 'rb').read() for k, p in files.items()}
    strs = string_ids(old['str'])
    for mid in names: assert strs.get(13000 + mid), 'string %d missing: slot %d not installed?' % (13000 + mid, mid)
    newstr = {}
    for mid, n in names.items(): newstr[13000 + mid] = n; newstr[3000 + mid] = n.upper()
    new = {'str': add_strings(old['str'], newstr)[0], 'de': de_rename(old['de'], names),
           'se': se_rename(old['se'], {int(slots[m]['sound_editor_id']): n for m, n in names.items()})}
    stamp = time.strftime('%Y%m%d-%H%M%S')
    for k, p in files.items():
        if new[k] == old[k]: print(k, 'unchanged'); continue
        if a.dry_run: print(k, 'would change', md5(old[k]), '->', md5(new[k])); continue
        try:
            with open(p, 'r+b'): pass
        except OSError as e:
            sys.exit('NOTHING CHANGED for %s: not writable (%s). Close the game/editors.' % (p, e.strerror))
        shutil.copyfile(p, p + '.bak_rename_' + stamp)
        open(p, 'wb').write(new[k]); assert md5(open(p, 'rb').read()) == md5(new[k])
        print(k, 'renamed', md5(old[k]), '->', md5(new[k]), 'backup', os.path.basename(p) + '.bak_rename_' + stamp)
    if not a.dry_run:   # keep slots.csv in step
        for mid, n in names.items(): slots[mid]['name'] = n
        with open(a.slots, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(next(iter(slots.values())).keys()), lineterminator='\r\n')
            w.writeheader(); [w.writerow(r) for r in slots.values()]
        print('updated', a.slots)

if __name__ == '__main__':
    main()

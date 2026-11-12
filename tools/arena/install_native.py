"""Install arena mods made for their own slot (native) into the clean game, plus table/name edits.
Run on the laptop from _arena_work/cardfix (epk/tables/yukes alongside). usage: install_native.py <plan.json>
plan: {"backup": dir, "arenas": [{"slot", "src": folder, "parts": {"misc04 key": id}, "m04": {...}, "m01_from": slot,
       "name": "TEXT", "initpos": [a,b,c], "light_from": slot}], "extra_files": [[src, rel]]}"""
import os, sys, json, re, hashlib, shutil
from epk import names, rename
import tables
from yukes import HSPC, SHDC, string_table_parse, string_table_build
G = '../../'; plan = json.load(open(sys.argv[1])); BK = G + plan['backup']; log = []
DEF = open(G + 'chunk0.def', 'rb').read().decode('latin1'); have = {l.strip().lower() for l in DEF.split('\n')}; newdef = []
def backup(rel):
    s, d = G + rel, BK + '/' + rel
    if os.path.exists(s) and not os.path.exists(d): os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy2(s, d)
def write(rel, data):
    backup(rel); os.makedirs(os.path.dirname(G + rel), exist_ok=True); open(G + rel, 'wb').write(data)
    w = rel.replace('/', '\\')
    if rel.startswith('pac/') and w.lower() not in have: newdef.append(w); have.add(w.lower())
    log.append((rel, hashlib.md5(data).hexdigest()[:8]))
def target_for(rel, slot):
    d, f = os.path.split(rel)
    if '/mov/' in rel:
        for c in sorted(os.listdir(G + d)) if os.path.isdir(G + d) else []:
            if re.fullmatch(r'0*%d\.pac' % slot, c, re.I): return d + '/' + c
    if '/wwe19_singleread/' in rel and re.match(r'%d - ' % slot, f):
        for c in os.listdir(G + 'mods/WWE 2K19 Unpacked Arena Graphics/' + d):
            if c.startswith('%d - ' % slot): return 'mods/WWE 2K19 Unpacked Arena Graphics/' + d + '/' + c
    return rel
for a in plan['arenas']:
    slot, src = a['slot'], a.get('src')
    for root, _, fs in (os.walk(src) if src else []):
        for f in fs:
            p = os.path.join(root, f); rel = os.path.relpath(p, src).replace(os.sep, '/')
            if not rel.startswith('pac/') or not f.lower().endswith('.pac') or '/match_up/' in rel: continue
            data = open(p, 'rb').read(); tgt = target_for(rel, slot)
            if tgt != rel and os.path.exists(G + tgt) and data[:4] != b'HSPC' and open(G + tgt, 'rb').read(4) != b'HSPC':
                tn = names(open(G + tgt, 'rb').read())
                if names(data) != tn: data = rename(data, tn)
            write(tgt, data)
    for s, rel in a.get('files', []): write(rel, open(s, 'rb').read())
# tables
P = {k: G + v for k, v in dict(m04='pac/root/misc04_arena.pac', m01='pac/root/misc01_start.pac', ip='pac/prop/propdata/initposition.pac', lg='pac/misc/parameter/light/prm_ar_lg_color.pac').items()}
T = {k: open(v, 'rb').read() for k, v in P.items()}
for a in plan['arenas']:
    s = a['slot']
    if 'm04' in a: T['m04'] = tables.misc04_set(T['m04'], s, a['m04'])
    if 'm01_from' in a:
        r = tables.misc01_get(T['m01'], a['m01_from']); keep = tables.misc01_get(T['m01'], s)
        r.update({k: keep[k] for k in ('name', 'select1', 'select2')}); r.update(a.get('m01', {}))
        T['m01'] = tables.misc01_set(T['m01'], s, r)
    if 'initpos' in a: T['ip'] = tables.initpos_set(T['ip'], s, *a['initpos'])
    if 'light_from' in a: T['lg'] = tables.light_set(T['lg'], s, tables.light_get(T['lg'], a['light_from']))
for k, v in P.items(): write(os.path.relpath(v, G).replace(os.sep, '/'), T[k])
# names, both string files
for rel in ('mods/SuperString/pac/string/win/string_win.pac', 'mods/SuperString/string_win.pac'):
    if not os.path.exists(G + rel): continue
    H = HSPC(open(G + rel, 'rb').read()); S = SHDC(H.files[0]['data']); pre, ents = string_table_parse(S.files[0]['data']); d = dict(ents)
    for a in plan['arenas']:
        if 'name' in a: d[tables.misc01_get(T['m01'], a['slot'])['name']] = a['name'].encode('latin1') + b'\0'
    S.files[0]['data'] = string_table_build(pre, sorted(d.items())); write(rel, H.replace(0, S.build()))
if newdef:
    backup('chunk0.def'); open(G + 'chunk0.def', 'ab').write(''.join(x + '\r\n' for x in newdef).encode('latin1'))
for a in plan['arenas']: print(a['slot'], tables.misc04_get(T['m04'], a['slot']), tables.misc01_get(T['m01'], a['slot']))
print(json.dumps(log, indent=0)); print('def+', newdef)

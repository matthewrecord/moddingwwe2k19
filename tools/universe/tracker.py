"""Universe tracker v1: capture every show's results from the WWE 2K19 save into a permanent history.

The game keeps only the latest show's cards in the save, so run this after every save (quit Universe to the menu).
Each run: decode SAVEDATA -> parse the match records -> append new matches to history.csv -> rebuild
records.csv, titles.csv and log.md. Re-running on the same save adds nothing.

People, not slots: a game id is mapped to a person *at capture time* (stored in each history row), from
 1. Matthew's 'wrestling ratings.xlsx', sheet Wrestlers: 'Character Slot' like '408 - Robert Gibson' -> id 408 is
    Dalton Castle; 'CAW' rows are matched by name against CCT's current slot names;
 2. otherwise CCT's current slot name (idnames.tsv), else the original name.
 aliases.tsv (optional, 'name<TAB>person') merges variants (e.g. "Triple H '13" -> Triple H).
Later reuse of a slot never rewrites old rows. Title names: titles.tsv ('id<TAB>name'), editable.

usage: python3 tracker.py --save SAVEDATA --out DIR --cct "A - CCT dir" [--xlsx ratings.xlsx]
"""
import argparse, csv, datetime, hashlib, os, struct, sys, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import savedecode, matches

HIST_COLS = ['capture', 'captured_at', 'save_md5', 'match_key', 'match_no', 'universe_day', 'title_id', 'title',
             'kind', 'side', 'game_id', 'slot_name', 'person', 'role', 'result', 'pinfall']

def load_idnames(cct):
    d, r = cct + '/data.xml', cct + '/replaced_data.xml'
    import xml.etree.ElementTree as ET
    cur = {it.get('slotNumber'): it.get('name') for it in ET.parse(r).getroot().iter('item') if it.get('slotNumber')}
    names = {}
    for it in ET.parse(d).getroot().iter('item'):
        s, i = it.get('slotNumber'), it.get('slotId')
        if i is not None and int(i) not in names:
            c = (cur.get(s) or '').split(' | ')[0].strip()
            if not c or c.upper().startswith('AVAILABLE'): c = (it.get('name') or '').strip()   # freed slot: original name
            names[int(i)] = c
    for i, n in ((937, 'Alex Shelley'), (938, 'Keith Lee'), (939, 'Angel Garza'), (940, 'Ace Austin'),
                 (941, 'Darby Allin'), (942, 'Moose')):
        names.setdefault(i, n)
    return names

def load_people(xlsx, names):
    people = {}
    if not xlsx or not os.path.exists(xlsx): return people
    import openpyxl
    ws = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)['Wrestlers']
    rows = list(ws.iter_rows(values_only=True)); hdr = list(rows[0])
    try: cw, cs = hdr.index('Wrestler'), hdr.index('Character Slot')
    except ValueError: return people
    cg = hdr.index('Gen') if 'Gen' in hdr else None
    byname = {}
    for i, n in names.items(): byname.setdefault(n.lower(), i)
    for r in rows[1:]:
        w, s = r[cw], r[cs]
        if not w or (cg is not None and str(r[cg] or '').strip() not in ('M', 'F')): continue   # skip non-wrestler rows (side tables)
        s = str(s or '').strip()
        if s[:3].isdigit() or s[:1].isdigit():
            try: people[int(s.split('-')[0].strip())] = str(w).strip(); continue
            except ValueError: pass
        i = byname.get(str(w).strip().lower())          # CAW / CC rows: match the slot by name
        if i is not None: people.setdefault(i, str(w).strip())
    return people

def load_tsv(path):
    if not os.path.exists(path): return {}
    with open(path, encoding='utf-8') as f:
        return {a: b for a, b in (l.rstrip('\n').split('\t', 1) for l in f if '\t' in l and not l.startswith('#'))}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--save'); ap.add_argument('--out', required=True)
    ap.add_argument('--cct', required=True); ap.add_argument('--xlsx')
    ap.add_argument('--archive', help='folder of unvs_*.bin captured by the slots DLL (processed in time order)'); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    blobs = []                                        # (source label, Universe blob)
    if a.archive and os.path.isdir(a.archive):
        done_p = os.path.join(a.out, 'processed.txt')
        done = set(open(done_p).read().split()) if os.path.exists(done_p) else set()
        for fn in sorted(f for f in os.listdir(a.archive) if f.startswith('unvs_') and f.endswith('.bin')):
            if fn in done: continue
            c = open(os.path.join(a.archive, fn), 'rb').read()
            csize = struct.unpack_from('<I', c, 24)[0]
            try: blobs.append((fn, zlib.decompress(c[32:32 + csize])))
            except zlib.error: print('skip (bad zlib):', fn)
            done.add(fn)
        open(done_p, 'w').write('\n'.join(sorted(done)))
    if a.save and os.path.exists(a.save):
        raw = open(a.save, 'rb').read()
        b = next((body for o, tag, size, body in savedecode.chunks(savedecode.decode(raw)) if tag == 'UNVSBODY0001' and body), None)
        if b is not None: blobs.append(('save ' + hashlib.md5(raw).hexdigest()[:8], b))
    if not blobs: print('no new captures'); return
    names = load_idnames(a.cct); people = load_people(a.xlsx, names)
    aliases = load_tsv(os.path.join(a.out, 'aliases.tsv'))
    tpath = os.path.join(a.out, 'titles.tsv')
    if not os.path.exists(tpath):
        open(tpath, 'w', encoding='utf-8').write('# championship id<TAB>name (edit freely)\n150\tAEW US Championship\n')
    tnames = load_tsv(tpath)
    hpath = os.path.join(a.out, 'history.csv'); hist = []
    if os.path.exists(hpath): hist = list(csv.DictReader(open(hpath, encoding='utf-8', newline='')))
    known = {h['match_key'] for h in hist}
    last_cap = max([int(h['capture']) for h in hist] or [0]); cap = last_cap + 1
    now = datetime.datetime.now().isoformat(timespec='seconds'); added = 0
    for src, blob in blobs:
      mno = 0; new_here = 0
      for start, day, title, kind, group in matches.parse(blob):
        key = hashlib.md5(repr((day, title, kind, group)).encode()).hexdigest()[:16]
        mno += 1
        if key in known: continue
        known.add(key); added += 1; new_here += 1
        for gid, role, res in group:
            slot = names.get(gid, str(gid)); person = people.get(gid) or slot
            person = aliases.get(person, person)
            hist.append(dict(capture=cap, captured_at=now, save_md5=src, match_key=key, match_no=mno,
                             universe_day=day or '', title_id='' if title is None else title,
                             title='' if title is None else tnames.get(str(title), f'title {title}'), kind=kind,
                             side=role >> 8, game_id=gid, slot_name=slot, person=person,
                             role='manager' if role & 0xFF == 2 else 'wrestler',
                             result='W' if res in (0x1FF, 0x3FF) else 'L', pinfall=int(res in (0x1FF, 0x2FF))))
      if new_here: cap += 1
    with open(hpath, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, HIST_COLS); w.writeheader(); w.writerows(hist)
    build_reports(hist, a.out)
    print(f'{added} new matches from {len(blobs)} source(s); history {len({h["match_key"] for h in hist})} matches')

def build_reports(hist, out):
    order = []; bym = {}
    for h in hist:
        if h['match_key'] not in bym: bym[h['match_key']] = []; order.append(h['match_key'])
        bym[h['match_key']].append(h)
    rec = {}
    for k in order:
        for h in bym[k]:
            if h['role'] != 'wrestler': continue
            r = rec.setdefault(h['person'], dict(person=h['person'], matches=0, W=0, L=0, pins_scored=0, pinned=0,
                                                 title_matches=0, streak='', form=''))
            r['matches'] += 1; r[h['result']] += 1
            if h['pinfall'] == '1' or h['pinfall'] == 1:
                if h['result'] == 'W': r['pins_scored'] += 1
                else: r['pinned'] += 1
            if h['title_id'] != '': r['title_matches'] += 1
            r['form'] = (r['form'] + h['result'])[-5:]
    for r in rec.values():
        f = r['form']; n = len(f) - len(f.rstrip(f[-1])) if f else 0
        r['streak'] = f'{f[-1]}{n}' if f else ''
    with open(os.path.join(out, 'records.csv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, ['person', 'matches', 'W', 'L', 'pins_scored', 'pinned', 'title_matches', 'streak', 'form'])
        w.writeheader(); w.writerows(sorted(rec.values(), key=lambda r: (-r['W'], r['L'], r['person'])))
    # title reigns: the winning side of a title match holds the title afterwards
    champ, reigns = {}, []
    for k in order:
        hs = bym[k]; h0 = hs[0]
        if h0['title_id'] == '': continue
        win = sorted({h['person'] for h in hs if h['result'] == 'W' and h['role'] == 'wrestler'})
        holder = ' & '.join(win); t = h0['title']
        cur = champ.get(t)
        if cur and cur['champion'] == holder: cur['defenses'] += 1; cur['last_match'] = k
        else:
            if cur: cur['lost_capture'] = h0['capture']; cur['lost_to'] = holder
            cur = dict(title=t, champion=holder, won_capture=h0['capture'], won_day=h0['universe_day'],
                       won_from=' & '.join(sorted({h['person'] for h in hs if h['result'] == 'L' and h['role'] == 'wrestler'})),
                       defenses=0, lost_capture='', lost_to='', last_match=k)
            champ[t] = cur; reigns.append(cur)
    with open(os.path.join(out, 'titles.csv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, ['title', 'champion', 'won_from', 'won_capture', 'won_day', 'defenses', 'lost_capture', 'lost_to'],
                           extrasaction='ignore')
        w.writeheader(); w.writerows(reigns)
    with open(os.path.join(out, 'log.md'), 'w', encoding='utf-8') as fh:
        fh.write('# Universe match log\n\n'); last = None
        for k in order:
            hs = bym[k]; h0 = hs[0]
            if h0['capture'] != last: fh.write(f"\n## Show captured {h0['captured_at']} (capture {h0['capture']}, day {h0['universe_day'] or '?'})\n\n"); last = h0['capture']
            def side(res):
                ws = [h for h in hs if h['result'] == res]
                return ' & '.join(h['person'] + ((' (pin)' if res == 'W' else ' (pinned)') if str(h['pinfall']) == '1' else '') for h in ws if h['role'] == 'wrestler') + \
                       ''.join(f" [w/ {h['person']}]" for h in ws if h['role'] == 'manager')
            fh.write(f"- {side('W')} def. {side('L')}" + (f" — **{h0['title']}**" if h0['title'] else '') + '\n')

if __name__ == '__main__':
    main()

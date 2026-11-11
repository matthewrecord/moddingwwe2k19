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

def wopen(path, encoding='utf-8', newline=None):
    """Open a report for writing; if Excel (or anything) has it open, write '<name> (new).<ext>' instead."""
    try: return open(path, 'w', encoding=encoding, newline=newline)
    except PermissionError:
        b, e = os.path.splitext(path); alt = f'{b} (new){e}'
        print(f'note: {os.path.basename(path)} is open in another program; wrote {os.path.basename(alt)}')
        return open(alt, 'w', encoding=encoding, newline=newline)

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
    names = load_idnames(a.cct); people = load_people(a.xlsx, names)
    aliases = load_tsv(os.path.join(a.out, 'aliases.tsv'))
    tpath = os.path.join(a.out, 'titles.tsv')
    if not os.path.exists(tpath):
        open(tpath, 'w', encoding='utf-8').write('# championship id<TAB>name (edit freely)\n150\tAEW US Championship\n')
    tnames = load_tsv(tpath)
    # internal per-participant store (one row per person per match); the readable files are rebuilt from it
    os.makedirs(os.path.join(a.out, '_data'), exist_ok=True)
    hpath = os.path.join(a.out, '_data', 'participants.csv'); hist = []
    old = os.path.join(a.out, 'history.csv')          # v1 layout: migrate once
    if not os.path.exists(hpath) and os.path.exists(old) and 'match_key' in open(old, encoding='utf-8').readline():
        hist = list(csv.DictReader(open(old, encoding='utf-8', newline='')))
        import shutil; shutil.copyfile(old, os.path.join(a.out, '_data', 'history_v1.csv'))   # history.csv is rewritten below as one row per match
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
    write_matches(order, bym, out)
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
    with wopen(os.path.join(out, 'records.csv'), encoding='utf-8-sig', newline='') as fh:
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
    with wopen(os.path.join(out, 'titles.csv'), encoding='utf-8-sig', newline='') as fh:
        w = csv.DictWriter(fh, ['title', 'champion', 'won_from', 'won_capture', 'won_day', 'defenses', 'lost_capture', 'lost_to'],
                           extrasaction='ignore')
        w.writeheader(); w.writerows(reigns)
    write_html(rec, reigns, order, bym, out)
    with wopen(os.path.join(out, 'log.md')) as fh:
        fh.write('# Universe match log\n\n'); last = None
        for k in order:
            hs = bym[k]; h0 = hs[0]
            if h0['capture'] != last: fh.write(f"\n## Show captured {h0['captured_at']} (capture {h0['capture']}, day {h0['universe_day'] or '?'})\n\n"); last = h0['capture']
            def side(res):
                ws = [h for h in hs if h['result'] == res]
                return ' & '.join(h['person'] + ((' (pin)' if res == 'W' else ' (pinned)') if str(h['pinfall']) == '1' else '') for h in ws if h['role'] == 'wrestler') + \
                       ''.join(f" [w/ {h['person']}]" for h in ws if h['role'] == 'manager')
            fh.write(f"- {side('W')} def. {side('L')}" + (f" — **{h0['title']}**" if h0['title'] else '') + '\n')

def _who(hs, res, role='wrestler'):
    return [h for h in hs if h['result'] == res and h['role'] == role]

def write_matches(order, bym, out):
    """history.csv: one row per match (the readable history)."""
    cols = ['show', 'captured', 'day', 'title', 'winners', 'losers', 'pinfall_by', 'pinned', 'winner_managers', 'loser_managers']
    with wopen(os.path.join(out, 'history.csv'), encoding='utf-8-sig', newline='') as fh:
        w = csv.DictWriter(fh, cols); w.writeheader()
        for k in order:
            hs = bym[k]; h0 = hs[0]
            w.writerow(dict(show=h0['capture'], captured=h0['captured_at'][:16].replace('T', ' '), day=h0['universe_day'],
                            title=h0['title'], winners=' & '.join(h['person'] for h in _who(hs, 'W')),
                            losers=' & '.join(h['person'] for h in _who(hs, 'L')),
                            pinfall_by=' & '.join(h['person'] for h in _who(hs, 'W') if str(h['pinfall']) == '1'),
                            pinned=' & '.join(h['person'] for h in _who(hs, 'L') if str(h['pinfall']) == '1'),
                            winner_managers=' & '.join(h['person'] for h in _who(hs, 'W', 'manager')),
                            loser_managers=' & '.join(h['person'] for h in _who(hs, 'L', 'manager'))))

def write_html(rec, reigns, order, bym, out):
    """standings.html: a self-contained page (open in any browser), rebuilt on every run."""
    import html as H
    e = H.escape
    rows = sorted(rec.values(), key=lambda r: (-(r['W'] / r['matches'] if r['matches'] else 0), -r['W'], r['L'], r['person']))
    def form(f): return ''.join(f'<span class="f {c}">{c}</span>' for c in f)
    st = ''.join(f"<tr><td class=n>{i}</td><td class=p>{e(r['person'])}</td><td>{r['W']}</td><td>{r['L']}</td>"
                 f"<td>{(100 * r['W'] / r['matches']):.0f}%</td><td>{r['pins_scored']}</td><td>{r['pinned']}</td>"
                 f"<td>{r['title_matches']}</td><td><b>{e(r['streak'])}</b></td><td>{form(r['form'])}</td></tr>"
                 for i, r in enumerate(rows, 1))
    cur = {}
    for rg in reigns: cur[rg['title']] = rg
    champs = ''.join(f"<div class=belt><div class=t>{e(t)}</div><div class=c>{e(rg['champion'])}</div>"
                     f"<div class=d>won from {e(rg['won_from']) or '—'} · {rg['defenses']} defense{'s' if rg['defenses'] != 1 else ''}</div></div>"
                     for t, rg in sorted(cur.items()))
    th = ''.join(f"<tr><td>{e(rg['title'])}</td><td class=p>{e(rg['champion'])}</td><td>{e(rg['won_from'])}</td>"
                 f"<td>show {rg['won_capture']}</td><td>{rg['defenses']}</td><td>{e(rg['lost_to']) or '<i>current</i>'}</td></tr>"
                 for rg in reigns)
    res, last = [], None
    for k in reversed(order):
        hs = bym[k]; h0 = hs[0]
        if h0['capture'] != last:
            res.append(f"<h3>Show {h0['capture']} <small>{e(h0['captured_at'][:16].replace('T', ' '))}"
                       f"{' · day ' + str(h0['universe_day']) if h0['universe_day'] else ''}</small></h3>"); last = h0['capture']
        def side(r):
            ws = ' & '.join(e(h['person']) + (' <small>(pin)</small>' if str(h['pinfall']) == '1' and r == 'W' else '')
                            for h in _who(hs, r))
            m = _who(hs, r, 'manager')
            return ws + (f" <small>w/ {e(' & '.join(h['person'] for h in m))}</small>" if m else '')
        res.append(f"<div class=m>{side('W')} <span class=def>def.</span> {side('L')}"
                   + (f" <span class=tt>{e(h0['title'])}</span>" if h0['title'] else '') + '</div>')
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Universe standings</title><style>
body{{font:15px/1.45 system-ui,Segoe UI,sans-serif;background:#111418;color:#e8e8e8;margin:0;padding:28px 40px}}
h1{{margin:0 0 4px;font-size:28px;letter-spacing:.5px}} h2{{margin:34px 0 10px;font-size:18px;text-transform:uppercase;letter-spacing:1.5px;color:#d4af37}}
h3{{margin:18px 0 6px;font-size:15px;color:#aab}} small{{color:#8a8f98;font-weight:normal}} .sub{{color:#8a8f98}}
table{{border-collapse:collapse;width:100%;max-width:1100px}} th,td{{padding:7px 10px;text-align:center;border-bottom:1px solid #262b33}}
th{{font-size:12px;text-transform:uppercase;color:#8a8f98;letter-spacing:1px}} td.p{{text-align:left;font-weight:600}} td.n{{color:#8a8f98}}
tr:hover td{{background:#1a1f26}} .f{{display:inline-block;width:18px;margin:0 1px;border-radius:3px;font-size:11px;font-weight:700}}
.f.W{{background:#1f6f43}} .f.L{{background:#7a2530}} .belts{{display:flex;flex-wrap:wrap;gap:14px}}
.belt{{background:linear-gradient(135deg,#2a2410,#17140a);border:1px solid #6b5a1e;border-radius:10px;padding:14px 18px;min-width:220px}}
.belt .t{{color:#d4af37;font-size:12px;text-transform:uppercase;letter-spacing:1px}} .belt .c{{font-size:20px;font-weight:700;margin:4px 0}} .belt .d{{color:#a99f80;font-size:12px}}
.m{{padding:5px 0;border-bottom:1px solid #1d2229;max-width:1100px}} .def{{color:#8a8f98;margin:0 6px}}
.tt{{margin-left:8px;font-size:11px;background:#6b5a1e;color:#fff;padding:2px 7px;border-radius:9px}}
</style></head><body><h1>Universe standings</h1><div class=sub>{len(order)} matches recorded · updated {datetime.datetime.now():%Y-%m-%d %H:%M}</div>
<h2>Champions</h2><div class=belts>{champs or '<span class=sub>No title matches yet.</span>'}</div>
<h2>Standings</h2><table><tr><th>#</th><th style="text-align:left">Superstar</th><th>W</th><th>L</th><th>Win %</th><th>Pins</th><th>Pinned</th><th>Title matches</th><th>Streak</th><th>Last 5</th></tr>{st}</table>
<h2>Title history</h2><table><tr><th>Title</th><th style="text-align:left">Champion</th><th>Won from</th><th>Won</th><th>Defenses</th><th>Lost to</th></tr>{th or '<tr><td colspan=6>—</td></tr>'}</table>
<h2>Results</h2>{''.join(res)}</body></html>"""
    with wopen(os.path.join(out, 'standings.html')) as fh: fh.write(page)

if __name__ == '__main__':
    main()


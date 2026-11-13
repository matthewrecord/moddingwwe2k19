"""Stage an arena's slot-specific files from slot S into a folder laid out for slot T (run from _arena_work/cardfix).
usage: reslot_stage.py <src_root> <S> <T> <out_dir> [--card]
Finds: pac/arena/entrance/arentrance{S}, pac/mov/*/0*S.pac, singleread GFX named 'S - ...' (pac/menu or the Unpacked
Arena Graphics mod folder). Each is fitted into the clean game's own container for slot T when one exists:
non-HSPC target -> rewrap(target, payload(src)); HSPC target + HSPC src -> re-stamp (header id, dir hashes, SHDC ids).
No target -> internal names have S replaced by T. The output is then installed with install_native.py (src = out_dir)."""
import os, re, sys, shutil
from epk import payload, rewrap, names, rename, tags, build_single
G = '../../'; src, S, T, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
MOVTAG = {'ar_apron': b'MVGA', 'ar_mini': b'MVGM', 'ar_ramp': b'MVGR', 'ar_wall': b'MVGW', 'transition': b'MOVT', 'transition_replay': b'MVTS', 'bg_apron': b'MVBA'}  # seen in pack EPK8s
UN = 'mods/WWE 2K19 Unpacked Arena Graphics/'
def restamp(mod, stock):
    b = bytearray(mod); b[0x10:0x14] = stock[0x10:0x14]; b[0x800:0x808] = stock[0x800:0x808]; b[0x814:0x81c] = stock[0x814:0x81c]
    for x, y in zip([m.start() for m in re.finditer(rb'SHDC', b)], [m.start() for m in re.finditer(rb'SHDC', stock)]): b[x + 16:x + 20] = stock[y + 16:y + 20]
    return bytes(b)
def find_target(d, pat):
    for base in (G + d, G + UN + d):
        if os.path.isdir(base):
            for c in sorted(os.listdir(base)):
                if re.fullmatch(pat, c, re.I): return os.path.relpath(base + '/' + c, G).replace(os.sep, '/')
def fit(data, tgt_rel, new_rel):
    if tgt_rel:
        t = open(G + tgt_rel, 'rb').read()
        if t[:4] != b'HSPC': return tgt_rel, rewrap(t, payload(data))
        if data[:4] == b'HSPC': return tgt_rel, restamp(data, t)
        new_rel = tgt_rel   # EPK over a stock HSPC path: worked for the AEW transitions (118/119)
    if data[:4] == b'HSPC' and '/mov/' in new_rel:   # stock video with no pack container for T: new EPK8 named M000T
        tag = MOVTAG.get(new_rel.split('/')[2])
        if tag: return new_rel, build_single(b'EPK8', tag, b'M%06d ' % T, payload(data))
    if data[:4] == b'HSPC': print('SKIP (HSPC, no target)', new_rel); return None, None
    nn = [re.sub(rb'0*%d(\s*)$' % S, lambda m: (b'%d' % T).rjust(len(m.group(0)) - len(m.group(1)), b'0') + m.group(1), n) for n in names(data)]
    return new_rel, rename(data, nn)
done = []
for root, _, fs in os.walk(src):
    for f in fs:
        p = os.path.join(root, f); rel = os.path.relpath(p, src).replace(os.sep, '/'); low = rel.lower()
        if not f.lower().endswith('.pac'): continue
        d = os.path.dirname(rel); d = d[d.lower().find('pac/'):] if 'pac/' in d.lower() else 'pac/' + d
        if 'arena/entrance/' in low and re.fullmatch(r'arentrance0*%d\.pac' % S, f, re.I):
            tr, data = fit(open(p, 'rb').read(), find_target('pac/arena/entrance', r'arentrance0*%d\.pac' % T), 'pac/arena/entrance/arentrance%05d.pac' % T)
        elif '/mov/' in '/' + low and re.fullmatch(r'0*%d\.pac' % S, f) and low.split('mov/')[1].count('/') == 1:
            md = 'pac/mov/' + low.split('mov/')[1].split('/')[0]
            tr, data = fit(open(p, 'rb').read(), find_target(md, r'0*%d\.pac' % T), md + '/%06d.pac' % T)
        elif '/wwe19_singleread/' in low and re.match(r'%d\s*-' % S, f) and '/matchcard_bg/' not in low:
            sub = 'pac/menu/win/Assets/wwe19_singleread/' + low.split('wwe19_singleread/')[1].rsplit('/', 1)[0]
            tr, data = fit(open(p, 'rb').read(), find_target(sub, r'%d\s*-.*\.pac' % T), sub + '/%d - new.pac' % T)
        else: continue
        if tr and tr.startswith(UN): tr = tr[len(UN):]
        if tr: o = os.path.join(out, tr); os.makedirs(os.path.dirname(o), exist_ok=True); open(o, 'wb').write(data); done.append(tr)
print('\n'.join(done))

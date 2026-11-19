"""2K26 -> 2K19 moveset translation.
Usage: translate.py WRESTLER_ID CHAR_MOVESETS.json TEMPLATE_DIR MovesID.data OUT.moveset [--base FILE] [--catalog move_catalog26.json]
- moves without a 2K19 id get the closest 2K19 move by name (2K26 names from the CMov catalog), flagged in the report.
- base: the 2K19 template with the most moves in common (keeps 2K19-only slots and anything untranslatable in a similar style).
- every filled 2K26 slot whose move exists in 2K19 (ids are byte-swapped 2K19 ids) is written to its learned 2K19 role
  (slot_roles_2k26.json), strongest roles first; a taken target falls back to its next voted role / a free sibling in the
  same family (e.g. Finisher1 -> Finisher2). Writes OUT.moveset and OUT.report.md."""
import sys,os,re,json,glob,collections
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import moveset19 as m19
sw=lambda i:((i>>8)|((i&255)<<8))
fam=lambda n:re.sub(r'\d+$','',n)
STOP={'the','of','a','to','and','with','from','new','dlc','mod','hidden','2k18','2k17','2k16','2k15','reversal','into','on','in','vs','left','right','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15'}
def toks(n): return [t for t in re.sub(r'\[.*?\]|\(.*?\)','',n.lower()).replace('-',' ').replace('/',' ').split() if t not in STOP and not t.isdigit()]
def substitute(name26,names,used=()):
    """closest 2K19 move by name tokens; the last token (move type: cutter, powerbomb, ddt...) weighs double"""
    A=toks(name26)
    if not A: return None,0
    best=(None,0)
    for mid,n19 in names.items():
        if mid in used: continue
        B=toks(n19)
        if not B: continue
        inter=len(set(A)&set(B)); score=(inter+(1 if A[-1] in B else 0))/(len(set(A)|set(B))+1)
        if A[-1] not in B: score*=0.5
        if score>best[1] or (score==best[1] and best[0] is not None and len(n19)<len(names[best[0]])): best=(mid,score)
    return best
def translate(wid,per,tdir,names,base=None,cat26=None):
    ids=per[wid]; want={sw(x) for x in ids if x}
    if not base:
        base=max(glob.glob(os.path.join(tdir,'*.moveset')),key=lambda f:len(want & set(m19.read(f).values())))
    B=m19.read(base); fields=list(B)
    roles={int(k):v for k,v in json.load(open(os.path.join(HERE,'slot_roles_2k26.json'))).items()}
    cand=[]
    for s,x in enumerate(ids):
        if not x or s not in roles: continue
        top=roles[s]['top']; conf=top[0][1]/max(roles[s]['seen'],1)
        cand.append((conf,s,sw(x),[f for f,_ in top]))
    cand.sort(reverse=True); out={}; log=[]; skipped=[]
    for conf,s,mid,tops in cand:
        sub=None
        if mid not in names:
            n26=(cat26 or {}).get(sw(mid),[None])[0]   # catalog keys = raw 2K26 ids
            ov=json.load(open(os.path.join(HERE,'overrides.json')))
            if n26 and n26 in ov:
                sub=(n26+' [override]',1.0); mid=int(ov[n26],16)
            elif n26:
                cand_id,score=substitute(n26,names)
                if cand_id is not None and score>=0.3: sub=(n26,score); mid=cand_id
            if sub is None: skipped.append((s,mid,tops[0],'no 2K19 equivalent (%s)'%((cat26 or {}).get(sw(mid),['?'])[0]))); continue
        tgt=None
        for f in tops:
            if f not in out: tgt=f; break
        if tgt is None:
            sib=[f for f in fields if fam(f)==fam(tops[0]) and f not in out]
            tgt=sib[0] if sib else None
        if tgt is None: skipped.append((s,mid,tops[0],'role already filled')); continue
        out[tgt]=mid; log.append((tgt,mid,s,conf,sub))
    return base,B,out,log,skipped
def report(wid,base,B,out,log,skipped,names):
    L=['# 2K26 wrestler %d -> 2K19 moveset'%wid,'','Base template (2K19-only slots, untranslated moves): `%s`'%os.path.basename(base),'',
       '%d slots set from 2K26, %d 2K26 moves not placed.'%(len(out),len(skipped)),'','| 2K19 slot | move | 2K26 slot | role confidence |','|---|---|---|---|']
    for tgt,mid,s,conf,sub in sorted(log,key=lambda r:list(B).index(r[0])):
        L.append('| %s | %s (%04X)%s | %d | %.2f |'%(tgt,names.get(mid,'?'),mid,' **substitute for 2K26 "%s" (match %.2f)**'%sub if sub else '',s,conf))
    L+=['','## Not placed','','| 2K26 slot | id | intended 2K19 slot | reason |','|---|---|---|---|']
    for s,mid,t,why in skipped: L.append('| %d | %04X | %s | %s |'%(s,mid,t,why))
    return '\n'.join(L)
if __name__=='__main__':
    a=sys.argv; wid=int(a[1]); per={int(k):v for k,v in json.load(open(a[2])).items()}; names=m19.load_names(a[4])
    base=a[a.index('--base')+1] if '--base' in a else None
    cat26={int(k):v for k,v in json.load(open(a[a.index('--catalog')+1])).items()} if '--catalog' in a else None
    base,B,out,log,sk=translate(wid,per,a[3],names,base,cat26)
    m19.write(base,out,a[5]); open(a[5][:-8]+'.report.md','w').write(report(wid,base,B,out,log,sk,names))
    print('base',os.path.basename(base),'set',len(out),'not placed',len(sk))

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
ctoks=lambda f:set(re.findall(r'[A-Z][a-z]+|\d+',f[4:] if f.startswith('move') else f))
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
NON_WRESTLER=('Cameraman','CameraMan','Crowd','Cutscene','Dad ','Dummy','Heavy Duty Worker','Highschool','Lady Accomplice','Masked Fan',
 'Medical','Mexican Security','Motion Test','Moveset Man','NPC','Photographer','Podcast','Referee','Seamstress','Security Guard','Pete Clark',
 'Jack Tice','BCW Fan','Michael Cole','Byron Saxton','Corey Graves','Renee Young','Bobby Heenan','Paul Heyman','Jo Jo','Lana','Maryse')
GIMMICK_ENTRANCE=('Undertaker','Kane','Bray Wyatt','Sting','Ultimate Warrior','Demon','Elias','Papa Shango','Goldust','Erick Rowan',
 'Luke Harper','Jake The Snake','Mr. McMahon','Velveteen','Gold ','Andre the Giant','Shane McMahon')
ENTRANCE_END=929   # bytes 0..928: entrance / music / trons / advanced entrance / victory settings (layout_2k19.json)
def candidates(tdir,want):
    fs=[f for f in glob.glob(os.path.join(tdir,'*.moveset')) if not any(x in os.path.basename(f) for x in NON_WRESTLER)]
    return sorted(fs,key=lambda f:-len(want & set(m19.read(f).values())))
def translate(wid,per,tdir,names,base=None,cat26=None):
    ids=per[wid]; want={sw(x) for x in ids if x}
    ranked=candidates(tdir,want)
    if not base: base=ranked[0]
    entrance=next(f for f in ranked if not any(x in os.path.basename(f) for x in GIMMICK_ENTRANCE))
    B=m19.read(base); fields=list(B)
    roles={int(k):v for k,v in json.load(open(os.path.join(HERE,'slot_roles_2k26.json'))).items()}
    cand=[]
    for s,x in enumerate(ids):
        if not x or s not in roles: continue
        top=roles[s]['top']; conf=top[0][1]/max(roles[s]['seen'],1)
        cand.append((conf,s,sw(x),[f for f,_ in top]))
    cand.sort(reverse=True); out={}; log=[]; skipped=[]; displaced=[]
    for conf,s,mid,tops in cand:
        sub=None; n26=(cat26 or {}).get(sw(mid),[None])[0]; ov=json.load(open(os.path.join(HERE,'overrides.json')))
        if n26 and n26 in ov and int(ov[n26],16)!=mid:   # curated mapping beats the id (2K26 reuses a few old ids for new moves)
            sub=(n26+' [override]',1.0); mid=int(ov[n26],16)
        elif mid in names and n26 and n26.strip().upper()!='TBD' and not set(toks(n26))&set(toks(names[mid])):
            sub=('2K26 name "%s" differs from the 2K19 name for this id (rename or reused id)'%n26.strip(),0.0)
        if mid not in names:
            n26=(cat26 or {}).get(sw(mid),[None])[0]   # catalog keys = raw 2K26 ids
            ov=json.load(open(os.path.join(HERE,'overrides.json')))
            if n26 and n26 in ov:
                sub=(n26+' [override]',1.0); mid=int(ov[n26],16)
            elif n26:
                cand_id,score=substitute(n26,names)
                if cand_id is not None and score>=0.3:
                    if 'Taunt' in tops[0] and cand_id in out.values():   # same generic taunt again -> next variant (Clown 1 -> Clown 2)
                        fam19=re.sub(r'\s*\d+\s*$','',names[cand_id]); alt=[k for k,v in names.items() if re.sub(r'\s*\d+\s*$','',v)==fam19 and k not in out.values()]
                        if alt: cand_id=alt[0]
                    sub=(n26,score); mid=cand_id
            if sub is None: skipped.append((s,mid,tops[0],'no 2K19 equivalent (%s)'%((cat26 or {}).get(sw(mid),['?'])[0]))); continue
        tgt=None
        for f in tops:
            if f in B and f not in out: tgt=f; break
        if tgt is None:
            sib=[f for f in fields if fam(f)==fam(tops[0]) and f not in out]
            tgt=sib[0] if sib else None
        if tgt is None:
            if mid in out.values(): skipped.append((s,mid,tops[0],'duplicate of a placed move'))
            else: displaced.append((conf,s,mid,tops))
            continue
        out[tgt]=mid; log.append((tgt,mid,s,conf,sub))
    # 2K26 often repeats Finisher1/Signature1 in the second slot (skipped as a duplicate): mirror it instead of keeping the base's move
    for a,b in (('moveFinisher1','moveFinisher2'),('moveSignature1','moveSignature2')):
        if a in out and b not in out: out[b]=out[a]; log.append((b,out[a],-1,1.0,('copy of '+a+' (2K26 repeats it)',1.0)))
    # second pass: displaced moves -> closest FREE slot of the same kind (never taunt<->move, keep vs Standing/Downed, Front/Rear)
    KEEP=('Taunt','Standing','Downed','Front','Rear','Ground','Seated','Kneeling','Apron','Ringside','Corner','Springboard','Diving','Strike','Grapple','Running','Top','Middle')
    for conf,s,mid,tops in displaced:
        if mid in out.values(): skipped.append((s,mid,tops[0],'duplicate of a placed move')); continue
        A=ctoks(tops[0]); best=(None,0)
        for f in fields:
            if f in out or f.startswith('moveWeightDetection') or 'EMPTY' in f: continue
            C=ctoks(f)
            if any((k in A)!=(k in C) for k in KEEP): continue
            sc=len(A&C)
            if sc>best[1]: best=(f,sc)
        if best[0] and best[1]>=2:
            out[best[0]]=mid; log.append((best[0],mid,s,conf,('displaced from '+tops[0],best[1]/max(len(A),1))))
        else: skipped.append((s,mid,tops[0],'role already filled, no free slot of the same kind'))
    return base,B,out,log,skipped,entrance
def report(wid,base,B,out,log,skipped,names):
    L=['# 2K26 wrestler %d -> 2K19 moveset'%wid,'','Base template (2K19-only slots, untranslated moves): `%s`'%os.path.basename(base),'',
       '%d slots set from 2K26, %d 2K26 moves not placed.'%(len(out),len(skipped)),'','| 2K19 slot | move | 2K26 slot | role confidence |','|---|---|---|---|']
    for tgt,mid,s,conf,sub in sorted(log,key=lambda r:list(B).index(r[0])):
        L.append('| %s | %s (%04X)%s | %d | %.2f |'%(tgt,names.get(mid,'?'),mid,(' **%s**'%sub[0] if sub[0].startswith(('displaced','copy','2K26 name')) else ' **substitute for 2K26 "%s" (match %.2f)**'%sub) if sub else '',s,conf))
    L+=['','## Not placed','','| 2K26 slot | id | intended 2K19 slot | reason |','|---|---|---|---|']
    for s,mid,t,why in skipped: L.append('| %d | %04X | %s | %s |'%(s,mid,t,why))
    return '\n'.join(L)
if __name__=='__main__':
    a=sys.argv; wid=int(a[1]); per={int(k):v for k,v in json.load(open(a[2])).items()}; names=m19.load_names(a[4])
    base=a[a.index('--base')+1] if '--base' in a else None
    cat26={int(k):v for k,v in json.load(open(a[a.index('--catalog')+1])).items()} if '--catalog' in a else None
    base,B,out,log,sk,ent=translate(wid,per,a[3],names,base,cat26)
    m19.write(base,out,a[5])
    b=bytearray(open(a[5],'rb').read()); b[:ENTRANCE_END]=open(ent,'rb').read()[:ENTRANCE_END]; open(a[5],'wb').write(b)   # entrance from a non-gimmick template
    open(a[5][:-8]+'.report.md','w').write(report(wid,base,B,out,log,sk,names).replace('\n\n%d slots set'%len(out),'\n\nEntrance, music, Titantron and victory settings from: `%s`\n\n%d slots set'%(os.path.basename(ent),len(out)),1))
    print('base',os.path.basename(base),'| entrance',os.path.basename(ent),'| set',len(out),'not placed',len(sk))

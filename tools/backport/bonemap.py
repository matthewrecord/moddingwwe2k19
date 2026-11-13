import sys,json,collections;sys.path.insert(0,__import__('os').path.dirname(__file__));from pairs import *
def wdict(names,ws):
    d=collections.defaultdict(float)
    for n,w in zip(names,ws):
        if w>0: d[n]+=float(w)
    return d
def run(n, tol=0.05):
    O=orig(n); Q=port(n)
    A=np.concatenate([o['pos'] for o in O]); AN=np.concatenate([o['bnames'] for o in O]); AW=np.concatenate([o['bw'] for o in O])
    AF=np.concatenate([[o['file']+'/'+o['mesh']]*len(o['pos']) for o in O])
    t=cKDTree(A); M=collections.defaultdict(lambda: collections.defaultdict(float)); pairs=[]
    for q in Q:
        if q['nb']!=max(x['nb'] for x in Q): continue   # skip separate hair rigs (67 bones) for the map
        d,i=t.query(q['pos'])
        for v in np.where(d<tol)[0]:
            do=wdict(AN[i[v]],AW[i[v]]); dp=wdict(q['bnames'][v],q['bw'][v])
            if '?' in dp: continue
            for a,wa in do.items():
                for p,wp in dp.items(): M[a][p]+=wa*wp
            pairs.append((do,dp,AF[i[v]],q['shader']))
    mp={}
    for a,row in M.items():
        tot=sum(row.values()); p=max(row,key=row.get); mp[a]=(p,row[p]/tot,tot)
    return mp,pairs
def score(pairs,f):
    err=[];dom=[]
    for do,dp,_,_ in pairs:
        t=f(do); keys=set(t)|set(dp); s=sum(t.values()) or 1
        err.append(0.5*sum(abs(t.get(k,0)/s-dp.get(k,0)) for k in keys))
        dom.append(max(t,key=t.get)==max(dp,key=dp.get) if t else False)
    return np.mean(err),np.median(err),np.mean(dom)
def via(mp,keep7=True):
    def f(do):
        t=collections.defaultdict(float)
        for a,w in do.items(): t[mp[a][0] if a in mp else a]+=w
        if keep7 and len(t)>7:
            t=dict(sorted(t.items(),key=lambda x:-x[1])[:7])
        return t
    return f
if __name__=='__main__':
    R={}
    for n in PAIRS:
        mp,pairs=run(n)
        same=[a for a in mp if mp[a][0]==a]; diff=sorted([(a,)+mp[a] for a in mp if mp[a][0]!=a],key=lambda x:-x[3])
        ident=lambda do: dict(do)
        e_id=score(pairs,ident); e_map=score(pairs,via(mp))
        print(f'== {n}: {len(pairs)} matched verts, {len(mp)} source bones; identity-name {len(same)}; remapped {len(diff)}')
        print('   naive (same names, no remap): meanL1 %.3f median %.3f dominant-bone agree %.1f%%'%(e_id[0],e_id[1],100*e_id[2]))
        print('   recovered map (one source bone -> one 2K19 bone): meanL1 %.3f median %.3f dominant agree %.1f%%'%(e_map[0],e_map[1],100*e_map[2]))
        print('   purity (mass-weighted) %.3f'%(sum(v[1]*v[2] for v in mp.values())/sum(v[2] for v in mp.values())))
        for x in diff[:25]: print('     %-26s -> %-22s purity %.2f mass %.0f'%x)
        R[n]=dict(map={a:list(v) for a,v in mp.items()},naive=e_id,mapped=e_map,nverts=len(pairs))
    json.dump(R,open('/home/claude/bonemap_results.json','w'),indent=1)

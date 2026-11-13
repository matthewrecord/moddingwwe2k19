import numpy as np,collections
def boundary_loops(T,P=None,weld=None):
    """Return list of boundary loops (vertex index lists). Vertices with identical position are welded first (seams)."""
    if P is not None:
        key={};rep=np.zeros(len(P),int)
        for i,p in enumerate(np.round(P,3)):
            k=tuple(p); rep[i]=key.setdefault(k,i)
        T=rep[T]
    E=collections.Counter()
    for a,b,c in T:
        for u,v in ((a,b),(b,c),(c,a)):
            if u==v: continue
            E[(min(u,v),max(u,v))]+=1
    nb=collections.defaultdict(list)
    for (u,v),n in E.items():
        if n==1: nb[u].append(v); nb[v].append(u)
    seen=set(); loops=[]
    for s in nb:
        if s in seen: continue
        loop=[s]; seen.add(s); prev=None; cur=s
        while True:
            nxt=[x for x in nb[cur] if x!=prev and x not in seen]
            if not nxt: break
            prev,cur=cur,nxt[0]; loop.append(cur); seen.add(cur)
        loops.append(loop)
    return sorted(loops,key=len,reverse=True)

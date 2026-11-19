"""Learn 2K26 slot -> 2K19 slot roles by voting over wrestlers present in both games.
Usage: learn_roles.py CHAR_MOVESETS.json CHARS26.txt TEMPLATE_DIR OUT.json
CHAR_MOVESETS.json = {wrestler_id: [358 u16 move ids]} (decode_char26.py); CHARS26.txt = '<id>_<Name>' lines (2K26 Characters folders);
TEMPLATE_DIR = Data Editor 2k19 Files/Moveset/Templates. Output: {slot: {"top": [[field, votes], ...5], "seen": n}}"""
import sys,json,re,glob,os,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import moveset19 as m19
sw=lambda i:((i>>8)|((i&255)<<8))
norm=lambda s:re.sub(r'[^a-z]','',s.lower())
def learn(per,chars,tdir):
    c26={}
    for l in open(chars):
        i,n=l.strip().split('_',1)
        if int(i) in per: c26.setdefault(norm(n),[]).append(int(i))
    votes=collections.defaultdict(collections.Counter); seen=collections.Counter(); pairs=0
    for f in glob.glob(os.path.join(tdir,'*.moveset')):
        k=norm(re.sub(r'\s+\d+$','',os.path.basename(f)[:-8]))
        if k not in c26: continue
        M=m19.read(f); inv=collections.defaultdict(list)
        for n,v in M.items():
            if v not in (0,0xffff): inv[v].append(n)
        best=max(c26[k],key=lambda i:sum(1 for x in per[i] if x and sw(x) in inv)); pairs+=1
        for s,x in enumerate(per[best]):
            if not x: continue
            seen[s]+=1
            for n in inv.get(sw(x),[]): votes[s][n]+=1
    return {s:{'top':votes[s].most_common(5),'seen':seen[s]} for s in votes},pairs
if __name__=='__main__':
    per={int(k):v for k,v in json.load(open(sys.argv[1])).items()}
    R,p=learn(per,sys.argv[2],sys.argv[3]); json.dump(R,open(sys.argv[4],'w'),indent=0); print('wrestlers',p,'slots',len(R))

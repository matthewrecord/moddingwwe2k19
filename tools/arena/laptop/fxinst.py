"""Copy staged files (src root, game-relative) into the game: back up existing ones to BK, add def lines for new paths."""
import os,sys,shutil,hashlib
G='../../WWE 2K19/'; src,BK=sys.argv[1],sys.argv[2]; new=[]
for r,_,fs in os.walk(src):
    for f in fs:
        rel=os.path.relpath(os.path.join(r,f),src).replace(os.sep,'/')
        if os.path.exists(G+rel):
            b=BK+'/'+rel; os.makedirs(os.path.dirname(b),exist_ok=True)
            if not os.path.exists(b): shutil.copy2(G+rel,b)
        else: new.append(rel.replace('/','\\'))
        os.makedirs(os.path.dirname(G+rel),exist_ok=True); shutil.copyfile(os.path.join(r,f),G+rel)
        print(rel,hashlib.md5(open(G+rel,'rb').read()).hexdigest()[:8])
if new:
    d=open(G+'chunk0.def','rb').read(); b=BK+'/chunk0.def'
    if not os.path.exists(b): open(b,'wb').write(d)
    have=set(l.lower() for l in d.decode('latin1').split('\r\n'))
    add=[n for n in new if n.lower() not in have]
    open(G+'chunk0.def','ab').write((('' if d.endswith(b'\r\n') else '\r\n')+''.join(x+'\r\n' for x in add)).encode('latin1')); print('def +',add)

"""Check that every part id a misc04 row references exists in pac/arena (usage: partcheck.py slot...)."""
import tables,os,sys,glob,re
G=os.path.expanduser('~/mnt/common/WWE 2K19/')
b=open(G+'pac/root/misc04_arena.pac','rb').read()
have={}
for d in os.listdir(G+'pac/arena'):
    for f in os.listdir(G+'pac/arena/'+d):
        m=re.match(r'ar([a-z_]+?)(\d{5})\.pac$',f,re.I)
        if m: have.setdefault(d.lower(),set()).add(int(m.group(2)))
K={'Stadium':'stadium','CornerPost':'cornerpost','Rope':'rope','Apron':'apron','Turnbuckle':'turnbuckle','Barricade':'barricade','Fence':'fence','CeilingLighting':'ceilinglight','Spotlight':'spotlight','Stairs':'stairs','CommentarySeat':'commentaryst','RingMat':'ringmat','FloorMattress':'floormattress','Crowd':'crowd','IBL':'ibl','Floor':'floor','Advertisement':'advertisement','MiscObjects':'miscobjects'}
for s in map(int,sys.argv[1:]):
    r=tables.misc04_get(b,s); miss=[]
    for k,d in K.items():
        v=r.get(k,-1)
        if v is None or v<0: continue
        if d not in have: miss.append(f'{k}={v}(no dir)'); continue
        if v not in have[d]: miss.append(f'{k}={v}')
    print(s,'MISSING:' if miss else 'ok',' '.join(miss))

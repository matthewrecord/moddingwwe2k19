import tables,hashlib,os,sys
C='../../WWE 2K19/';M='../../WWE 2K19 - modded/'
F={'Stadium':'stadium','CornerPost':'cornerpost','LED_CornerPost':'ledcornerpost','Rope':'rope','Apron':'apron','LED_Apron':'ledapron','Turnbuckle':'turnbuckle','Barricade':'barricade','Fence':'fence','CeilingLighting':'ceilinglight','Spotlight':'spotlight','Stairs':'stairs','CommentarySeat':'commentaryst','RingMat':'ringmat','FloorMattress':'floormattress','Crowd':'crowd','IBL':'ibl','Titantron':'titantron','Minitron':'minitron','Wall_L':'walll','Wall_R':'wallr','Header':'header','Floor':'floor','MiscObjects':'miscobjects','Advertisement':'advertisement'}
def path(k,v):
    if k.endswith('_CM'): f=k[:-3].lower(); return 'pac/arena/%s/ar%scm%05d.pac'%(f,f,v)
    return 'pac/arena/%s/ar%s%05d.pac'%(F[k],F[k],v)
md=lambda p:hashlib.md5(open(p,'rb').read()).hexdigest()[:8] if os.path.exists(p) else None
m4=open(M+'pac/root/misc04_arena.pac','rb').read()
for s in map(int,sys.argv[1:]):
    r=tables.misc04_get(m4,s); out=[]
    for k,v in r.items():
        if not isinstance(v,int) or v<0: continue
        p=path(k,v); a,b=md(C+p),md(M+p)
        if a!=b: out.append((k,v,a,b,open(M+p,'rb').read(4) if b else None))
    print(s,out)

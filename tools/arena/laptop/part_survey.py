"""Survey the arena parts a mod folder ships against the clean game: part_survey.py <src folder> [<src folder>...]
FREE = id not in the game; SAME = identical file installed; CLASH = a different file holds the id (users = misc04 rows using it)."""
import os,re,sys,hashlib,tables,epk
G=os.path.expanduser('~/mnt/common/WWE 2K19/')
K={'stadium':'Stadium','cornerpost':'CornerPost','rope':'Rope','apron':'Apron','turnbuckle':'Turnbuckle','barricade':'Barricade','fence':'Fence','ceilinglight':'CeilingLighting','spotlight':'Spotlight','stairs':'Stairs','commentaryst':'CommentarySeat','ringmat':'RingMat','floormattress':'FloorMattress','crowd':'Crowd','ibl':'IBL','floor':'Floor','ledapron':'LED_Apron','ledcornerpost':'LED_CornerPost','titantron':'Titantron','minitron':'Minitron'}
m04=open(G+'pac/root/misc04_arena.pac','rb').read()
rows={}
for s in range(0,500):
    try:
        r=tables.misc04_get(m04,s)
        if r: rows[s]=r
    except Exception: pass
md=lambda p:hashlib.md5(open(p,'rb').read()).hexdigest()[:8]
def nm(p):
    b=open(p,'rb').read()
    try: return b[:4].decode()+':'+(b','.join(epk.names(b)).decode() if b[:4]!=b'HSPC' else '')
    except Exception: return b[:4].decode('latin1')
for src in sys.argv[1:]:
    print('==',src)
    for root,_,fs in os.walk(src):
        for f in sorted(fs):
            m=re.match(r'ar([a-z]+?)(cm)?(\d{5})\.pac$',f,re.I)
            if not m or '/arena/' not in root.replace('\\','/')+'/' or m.group(1).lower()=='entrance': continue
            part,cm,i=m.group(1).lower(),m.group(2),int(m.group(3)); p=os.path.join(root,f)
            g=G+'pac/arena/%s/%s'%(os.path.basename(root),f)
            key=K.get(part,part)+('_CM' if cm else '')
            users=[s for s,r in rows.items() if r.get(key)==i]
            if not os.path.exists(g): st='FREE'
            elif md(g)==md(p): st='SAME'
            else: st='CLASH'
            print(f'  {f:28} {st:5} src={nm(p):22} game={nm(g) if os.path.exists(g) else "-":22} users={users[:12]}{"..." if len(users)>12 else ""} ({len(users)})')

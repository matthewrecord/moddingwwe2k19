"""List the arena package: every file changed/added for the arenas since the 81-arena pack install.
Pristine = earliest backup copy (by relpath, or by basename in flat backup dirs). Excludes char ports, def/arc, dumps,
new part files no misc04 row references, new GFX/videos for slots that are stock again. usage: build_pkg.py [--copy OUT]"""
import os,sys,time,hashlib,re,glob,tables,json
G='../../WWE 2K19/'; W='../'
BK=[d for d in sorted(glob.glob(W+'backup_*'),key=os.path.getmtime)]
T=time.mktime((2026,11,12,5,0,0,0,0,0))
md=lambda p:hashlib.md5(open(p,'rb').read()).hexdigest()
def pristine(rel):
    base=os.path.basename(rel)
    for d in BK:
        for c in (d+'/'+rel,d+'/'+base):
            if os.path.exists(c) and os.path.getmtime(c)<=T: return c
    return None
m04=open(G+'pac/root/misc04_arena.pac','rb').read(); used={}
K={'Stadium':'stadium','CornerPost':'cornerpost','Rope':'rope','Apron':'apron','Turnbuckle':'turnbuckle','Barricade':'barricade','Fence':'fence','CeilingLighting':'ceilinglight','Spotlight':'spotlight','Stairs':'stairs','CommentarySeat':'commentaryst','RingMat':'ringmat','FloorMattress':'floormattress','Crowd':'crowd','IBL':'ibl','Floor':'floor','LED_CornerPost':'ledcornerpost','LED_Apron':'ledapron','Header':'header'}
for s in range(500):
    try: r=tables.misc04_get(m04,s)
    except Exception: continue
    if not r: continue
    for k,d in K.items():
        if r.get(k) is not None and r[k]>=0: used.setdefault(d,set()).add(r[k])
OURS={104,115,107,112,117,118,119,123,124,125,127,128,130,132,133,134,135,138,139,143,149,158,159,160,96,53,5,141}
inc,skip=[],[]
for root,_,fs in os.walk(G):
    rr=os.path.relpath(root,G).replace(os.sep,'/')
    if rr.startswith(('CrashDump','mods/CCT','_')): continue
    for f in fs:
        rel=(rr+'/'+f if rr!='.' else f)
        if rr=='pac/prop' and f!='0158.pac': continue   # loose props = Matthew's character work; 0158 = Dynamite '22
        if os.path.getmtime(G+rel)<=T or rel.lower() in ('chunk0.def','chunk0.arc') or rel.startswith('chunk0.def'): continue
        p=pristine(rel); why=None
        if p and md(p)==md(G+rel): why='same as pristine'
        m=re.match(r'pac/arena/([a-z_]+)/ar[a-z_]+?(\d{5})\.(pac|def)$',rel)
        if not p and m and m.group(1)!='entrance' and int(m.group(2)) not in used.get(m.group(1),()): why='new part, unused'
        n=re.search(r'/(\d+)\s*-[^/]*$',rel) or re.search(r'/0*(\d+)\.pac$',rel) if ('/mov/' in rel or 'singleread' in rel) else None
        if not p and n and int(n.group(1)) not in OURS: why='new file for a stock slot'
        (skip if why else inc).append((rel,why,bool(p)))
json.dump({'include':[r for r,_,_ in inc],'skip':[(r,w) for r,w,_ in skip]},open(W+'pkg_list.json','w'),indent=0)
print('include',len(inc),'new',sum(1 for x in inc if not x[2]),'| skip',len(skip))
for r,w in [(r,w) for r,w,_ in skip]: print('SKIP',w,'|',r)
if '--copy' in sys.argv:
    import shutil; out=sys.argv[sys.argv.index('--copy')+1]; man=[]
    for r,_,_ in inc:
        os.makedirs(os.path.dirname(out+'/'+r) or out,exist_ok=True)
        if not (os.path.exists(out+'/'+r) and os.path.getsize(out+'/'+r)==os.path.getsize(G+r)): shutil.copyfile(G+r,out+'/'+r)
        man.append('%s  %s'%(md(G+r),r))
    open(out+'/MANIFEST.md5','w').write('\n'.join(man)+'\n'); print('copied',len(man))

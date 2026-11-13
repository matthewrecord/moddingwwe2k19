"""Batch 3: add an arena's parts to its staged folder (remapping clashing ids to named EPK8s) and write its plan.
b3plan.py <spec.json>  spec: {"slot":T,"S":S,"src":folder,"stage":"../in/b3_T","remap":{"apron/136":123},"rename":{"src rel":"dst rel"},
 "row_from":S (modded game) or "m04":{...}, "m04_set":{...}, "m01_from_mod":S | "m01_full":{...}, "initpos":[..], "light":[..]|"light_from_mod":S,
 "name":..., "card":path}  -> plan_b3_T.json"""
import os,sys,json,re,tables
from epk import payload,build_single
spec=json.load(open(sys.argv[1])); T=spec['slot']; st=spec['stage']; src=spec['src']
M=os.path.expanduser('~/mnt/common/WWE 2K19 - modded/'); rd=lambda k:open(M+k,'rb').read()
PFX={'apron':'AP','stadium':'ST','cornerpost':'CP','commentaryst':'CS','ceilinglight':'CL','ibl':'IA','ledcornerpost':'LC','turnbuckle':'TB','barricade':'BR','ringmat':'RM','spotlight':'SP','header':'HD','fence':'FN','floor':'FL'}
K={'stadium':'Stadium','cornerpost':'CornerPost','apron':'Apron','turnbuckle':'Turnbuckle','barricade':'Barricade','fence':'Fence','ceilinglight':'CeilingLighting','spotlight':'Spotlight','commentaryst':'CommentarySeat','ringmat':'RingMat','ibl':'IBL','floor':'Floor','ledcornerpost':'LED_CornerPost','header':'Header'}
row=dict(tables.misc04_get(rd('pac/root/misc04_arena.pac'),spec['row_from'])) if 'row_from' in spec else dict(spec['m04'])
row.pop('version',None); log=[]
for root,_,fs in os.walk(src):
    for f in fs:
        p=os.path.join(root,f); rel=os.path.relpath(p,src).replace(os.sep,'/'); rel=spec.get('rename',{}).get(rel,rel)
        m=re.search(r'pac/arena/([a-z]+)/ar([a-z]+?)(\d{5})\.pac$',rel)
        if not m or m.group(1)=='entrance': continue
        part,i=m.group(1),int(m.group(3)); data=open(p,'rb').read(); key='%s/%d'%(part,i)
        if key in spec.get('remap',{}):
            n=spec['remap'][key]; data=build_single(b'EPK8',b'SGSN',(PFX[part]+'%05d'%n).encode(),payload(data))
            if part in K and row.get(K[part])==i: row[K[part]]=n
            log.append('%s -> %d'%(key,n)); i=n
        o='%s/pac/arena/%s/ar%s%05d.pac'%(st,part,part,i); os.makedirs(os.path.dirname(o),exist_ok=True); open(o,'wb').write(data)
row.update(spec.get('m04_set',{}))
have_t=tables.misc04_get(open(os.path.expanduser('~/mnt/common/WWE 2K19/pac/root/misc04_arena.pac'),'rb').read(),T)
row={k:v for k,v in row.items() if k in have_t}
a={'slot':T,'src':st,'m04':row,'name':spec['name']}
if 'm01_from_mod' in spec: a['m01_full']=tables.misc01_get(rd('pac/root/misc01_start.pac'),spec['m01_from_mod'])
if 'm01_full' in spec: a['m01_full']=spec['m01_full']
if 'm01_set' in spec:
    G2=os.path.expanduser('~/mnt/common/WWE 2K19/'); r=tables.misc01_get(open(G2+'pac/root/misc01_start.pac','rb').read(),T); r.update(spec['m01_set']); a['m01_full']=r
if 'initpos' in spec: a['initpos']=spec['initpos']
if 'light_from_mod' in spec: a['light']=tables.light_get(rd('pac/misc/parameter/light/prm_ar_lg_color.pac'),spec['light_from_mod'])
if 'light' in spec: a['light']=spec['light']
if 'card' in spec:
    import glob; G='../../WWE 2K19/'; MU='pac/menu/win/Assets/wwe19_anime/match_up/'
    a['files']=[[spec['card'],MU+os.path.basename(glob.glob(G+MU+'ltag_%03d_*_win.pac'%T)[0])]]
json.dump({'backup':'../WWE2K19_arena_work/backup_b3_%d'%T,'exclude':spec.get('exclude','/mov/bg_|matchcard_bg|match_up/'),'arenas':[a]},open('plan_b3_%d.json'%T,'w'),indent=1)
print(log); print(json.dumps(a)[:1500])

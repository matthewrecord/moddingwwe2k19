import sys,struct
sys.path.insert(0,'/home/claude/moddingwwe2k19/tools/lib')
from yukes import HSPC,SHDC
U='/mnt/user-data/uploads/common/WWE 2K19/pac/menu/cae_item'
M={l.split(':')[0]:set(int(x) for x in l.split(':')[1].split() if x.isdigit()) for l in open('/mnt/user-data/uploads/common/WWE 2K19/_moddingwwe2k19_builds/tron_movie_ids_2026-11-11.txt')}
SCR={1:'wall',42:'mini',43:'ramp',44:'apron'}
for fid in (1,42,43,44):
    idx={}; allv=set(); tot=0
    for pat in ['','_p10','_p20','_p30']:
        S=SHDC(HSPC(open(U+pat+'.pac','rb').read()).files[0]['data'])
        d=[f for f in S.files if f['id']==fid][0]['data']; n,t=struct.unpack_from('<HH',d,0)
        for k in range(n):
            e=struct.unpack_from('<10I',d,4+40*k); idx[t-n+k]=e[0]; allv.add(e[0])
        tot+=n
    live=set(idx.values())
    print('list',fid,'entries',tot,'distinct values',len(allv),'surviving index slots',len(idx),'distinct live',len(live),
          'lost by overwrite',sorted(allv-live)[:40])
    wall=M[SCR[fid]]
    for nm,s in M.items(): print('   vs',nm,len(s),'live entries with movie',len(s&live),'movies without entry',len(s-live))
    if fid==1: print('  wall movies',len(wall),'with live entry',len(wall&live),'NO entry',len(wall-live),'entries w/o movie',len(live-wall)); print('  sample no-entry',sorted(wall-live)[:60])

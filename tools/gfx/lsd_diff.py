import sys,struct
sys.path.insert(0,'/home/claude/moddingwwe2k19/tools/lib')
from yukes import HSPC,SHDC
U='/mnt/user-data/uploads/common/'
def ents(inst,pat,fid):
    S=SHDC(HSPC(open(f'{U}{inst}/pac/menu/cae_item{pat}.pac','rb').read()).files[0]['data'])
    d=[f for f in S.files if f['id']==fid][0]['data']; n,t=struct.unpack_from('<HH',d,0)
    return [struct.unpack_from('<10I',d,4+40*k) for k in range(n)]
fid=int(sys.argv[1])
for pat in ['','_p10','_p20','_p30']:
    a=ents('WWE 2K19',pat,fid); b=ents('WWE 2K19 - unmodded',pat,fid)
    sb=set(b); new=[e for e in a if e not in sb]
    print(pat or 'base',len(a),len(b),'new',len(new))
    for e in (b[:3]+b[-2:]): print('  van',' '.join(f'{x:x}' if x>99999999 else str(x) for x in e))
    for e in new[:6]+new[-3:]: print('  NEW',' '.join(f'{x:x}' if x>99999999 else str(x) for x in e))

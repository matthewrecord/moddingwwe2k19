import sys,glob,numpy as np;sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)));import jboy,mdlfmt
from scipy.spatial import cKDTree
P='/home/claude/pairs/'; E='/home/claude/ext/'
PAIRS={'Fletcher':('Kyle Fletcher by*ORIGINAL','Kyle_Fletcher_ch50602'),'Gabe':('GabeKidd*ORIGINAL','Gabe_Kidd_ch50602'),
       'OKhan':('Great_O_Khan*ORIGINAL','Great_O_ch50602'),'Willow':('Willow_Nightingale*ORIGINAL','Willow_Nightingale_ch50602')}
def orig(name):
    out=[]
    for f in sorted(glob.glob(P+PAIRS[name][0]+'/**/*.mdl',recursive=True)):
        m=mdlfmt.MDL(f); bn=[x['name'] for x in m.bones]; part=f.split('/')[-1]
        for me in m.meshes:
            st=me['streams']; bi=st['BI'].astype(int); bw=st['BW']
            names=np.array([[ (bn[i] if bn else f'{part}#{i}') for i in r] for r in bi]) if True else None
            out.append(dict(file=part,mesh=me['name'],pos=st['POSITION'].astype('f4'),bi=bi,bw=bw,bnames=names))
    return out
def port(name):
    out=[]
    for f in sorted(glob.glob(E+PAIRS[name][1]+'/*.jboy')):
        j=jboy.JBOY(f); bn=[x['name'] for x in j.bones]
        for k,o in enumerate(j.objs):
            bi=o['bi']; ok=bi<len(bn)
            names=np.where(ok,np.array(bn+['?'])[np.minimum(bi,len(bn))],'?')
            out.append(dict(file=f.split('/')[-1],obj=k,shader=o['shader'],pos=o['pos'],bi=bi,bw=o['bw'],bnames=names,nb=len(bn)))
    return out

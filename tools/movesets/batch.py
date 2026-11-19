"""batch.py OUTDIR ID[:Name] ID[:Name] ...  -> <Name>_<id>.moveset + .report.md per wrestler, and OUTDIR/_summary.md
Paths (decoded tables, templates, move list) are the session defaults below; edit for another machine."""
import sys,os,re,json,subprocess
HERE=os.path.dirname(os.path.abspath(__file__))
CHAR='/home/claude/k26/char_movesets.json'; CAT='/home/claude/k26/move_catalog26.json'; TPL='/home/claude/k26/t19/Templates'
MOVES='/mnt/user-data/uploads/WWE 2K19/A - Data Editor 2k19/Data/DataLists/Modded/MovesID.data'
CHARS26='/mnt/user-data/uploads/WWE 2K19/A - Resources/2K26 Extracted/chars26.txt'
names26={int(l.split('_',1)[0]):l.strip().split('_',1)[1] for l in open(CHARS26)}
def headline(rep,slot):
    m=re.search(r'^\| %s \| (.*?) \| (-?\d+) \|'%slot,rep,re.M)
    if not m: return '(template)'
    t=m.group(1); flag=' [sub]' if 'substitute' in t or 'override' in t else (' [name?]' if 'differs' in t else (' [copy]' if 'copy of' in t else ''))
    return re.sub(r'\s*\*\*.*','',re.sub(r' \([0-9A-F]{4}\)','',t)).strip()+flag
out=sys.argv[1]; os.makedirs(out,exist_ok=True); rows=[]
for arg in sys.argv[2:]:
    wid,_,nm=arg.partition(':'); wid=int(wid); nm=nm or names26.get(wid,str(wid)).replace('_',' ')
    fn=os.path.join(out,'%s_%d.moveset'%(re.sub(r'[^A-Za-z0-9]+','_',nm).strip('_'),wid))
    r=subprocess.run(['python3','-I',os.path.join(HERE,'translate.py'),str(wid),CHAR,TPL,MOVES,fn,'--catalog',CAT],capture_output=True,text=True)
    if r.returncode: rows.append('| %s | %d | ERROR %s |||||||'%(nm,wid,r.stderr.strip()[-120:])); continue
    rep=open(fn[:-8]+'.report.md').read(); st=r.stdout.strip()
    base=re.search(r'base (.*?)\.moveset',st).group(1); ent=re.search(r'entrance (.*?)\.moveset',st).group(1)
    n=re.search(r'set (\d+) not placed (\d+)',st).groups()
    rows.append('| %s | %d | %s | %s | %s | %s | %s | %s | %s/%s |'%(nm,wid,headline(rep,'moveFinisher1'),headline(rep,'moveFinisher2'),
        headline(rep,'moveSignature1'),headline(rep,'moveSignature2'),base,ent,n[0],n[1]))
hdr='| Wrestler | 2K26 id | Finisher 1 | Finisher 2 | Signature 1 | Signature 2 | base template | entrance from | set/not placed |\n|---|---|---|---|---|---|---|---|---|'
open(os.path.join(out,'_summary.md'),'w').write('# 2K26 -> 2K19 movesets\n\n[sub] = 2K26 move has no 2K19 id, substituted/overridden; [name?] = same id but the 2K26 name differs (check); [copy] = mirrors slot 1.\n\n'+hdr+'\n'+'\n'.join(rows)+'\n')
print('\n'.join(rows))

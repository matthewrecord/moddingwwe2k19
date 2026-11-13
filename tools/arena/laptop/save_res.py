"""Save an installed arena back to Resources: save_res.py slot "Resources folder" "Title" log1 [log2..]
Copies the arena's own files (from the install logs, minus game-wide tables/strings) + its match card, writes files_md5.txt and
README.txt with the four table rows and the name."""
import sys,os,re,glob,shutil,hashlib,json,tables
G=os.path.expanduser('~/mnt/common/WWE 2K19/'); R=os.path.expanduser('~/mnt/A - Resources/Back - Arenas and Arena GFX/')
slot=int(sys.argv[1]); dst=R+sys.argv[2]+'/Installed - slot %d 2026-11-13/'%slot; title=sys.argv[3]
SHARED=('pac/root/','pac/prop/','pac/misc/parameter','mods/SuperString')
rels=set()
for l in sys.argv[4:]:
    for r in re.findall(r'"([a-z][^"]*\.pac)"',open(l).read()):
        if not r.startswith(SHARED): rels.add(r)
rels|={os.path.relpath(p,G) for p in glob.glob(G+'pac/menu/win/Assets/wwe19_anime/match_up/ltag_%03d_*_win.pac'%slot)}
md=[]
for r in sorted(rels):
    os.makedirs(os.path.dirname(dst+r),exist_ok=True); shutil.copy2(G+r,dst+r); md.append('%s  %s'%(hashlib.md5(open(G+r,'rb').read()).hexdigest(),r))
open(dst+'files_md5.txt','w').write('\n'.join(md)+'\n')
rd=lambda k:open(G+k,'rb').read()
m01=tables.misc01_get(rd('pac/root/misc01_start.pac'),slot)
txt=[f'{title} installed in slot {slot} (clean Genesis game), saved 2026-11-13 by Claude (repo moddingwwe2k19, writeup/Arena_inventory.md).',
 'Copy the pac/ and mods/ trees into the game folder (add new pac paths to chunk0.def), then set the table rows below.','',
 'misc04_arena row: '+json.dumps(tables.misc04_get(rd('pac/root/misc04_arena.pac'),slot)),
 'misc01_start row: '+json.dumps(m01),'initposition: '+json.dumps(tables.initpos_get(rd('pac/prop/propdata/initposition.pac'),slot)),
 'light colour: '+repr(tables.light_get(rd('pac/misc/parameter/light/prm_ar_lg_color.pac'),slot)),'Name string %d: %s'%(m01['name'],title),'','Files:']+md
open(dst+'README.txt','w').write('\n'.join(txt)+'\n'); print(dst,len(md))

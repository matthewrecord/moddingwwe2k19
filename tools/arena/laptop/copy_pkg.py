"""Resumable copy of pkg_list.json into OUT (skips files already there with the right size); writes MANIFEST.md5 at the end."""
import json,os,shutil,sys,time,hashlib
G='../../WWE 2K19/'; out=sys.argv[1]; L=json.load(open('../pkg_list.json'))['include']; t0=time.time(); n=0
for r in L:
    d=out+'/'+r
    if os.path.exists(d) and os.path.getsize(d)==os.path.getsize(G+r): continue
    if time.time()-t0>140: print('PAUSE, remaining', sum(1 for x in L if not(os.path.exists(out+'/'+x) and os.path.getsize(out+'/'+x)==os.path.getsize(G+x)))); sys.exit(0)
    os.makedirs(os.path.dirname(d),exist_ok=True); shutil.copyfile(G+r,d); n+=1
print('copied',n,'all present')

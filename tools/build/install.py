"""Install / uninstall a build made by musicslot.py, with backups and MD5 checks.

  python3 -I tools/build/install.py install   --build <dir> --game "<install>"
  python3 -I tools/build/install.py uninstall --build <dir> --game "<install>"
  python3 -I tools/build/install.py status    --build <dir> --game "<install>"

install: refuses unless every target file still has the MD5 the build was made from (manifest inputs); copies each
original once to <file>.orig_musicslot (never overwritten, so the first original survives repeated installs); copies
the new file; verifies MD5. uninstall: copies the .orig_musicslot backups back and verifies the original MD5s.
Nothing is deleted (the agent shell cannot delete in Matthew's folders anyway).
"""
import hashlib, json, os, shutil, sys
def md5f(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)
    return h.hexdigest()
def main():
    cmd = sys.argv[1]; a = dict(zip(sys.argv[2::2], sys.argv[3::2]))
    B, G = a['--build'], a['--game']
    m = json.load(open(os.path.join(B, 'manifest.json')))
    rows = []
    for k, o in m['outputs'].items():
        i = m['inputs'][k]; tgt = os.path.join(G, o['path']); bak = tgt + '.orig_musicslot'
        cur = md5f(tgt) if os.path.exists(tgt) else None
        rows.append((k, tgt, bak, i['md5'], o['md5'], cur))
    if cmd == 'status':
        for k, tgt, bak, imd5, omd5, cur in rows:
            st = 'MODDED' if cur == omd5 else 'ORIGINAL' if cur == imd5 else 'OTHER'
            print(f"{k:5s} {st:8s} backup={'yes' if os.path.exists(bak) else 'no'}  {tgt}")
        return
    if cmd in ('install', 'uninstall'):
        locked = []
        for k, tgt, *_ in rows:
            try:
                with open(tgt, 'r+b'): pass
            except OSError as e:
                locked.append((tgt, e.strerror))
        if locked:
            sys.exit('NOTHING CHANGED: files not writable (is the game running?): %r' % locked)
    if cmd == 'install':
        bad = [(k, tgt) for k, tgt, bak, imd5, omd5, cur in rows if cur not in (imd5, omd5)]
        if bad: sys.exit('REFUSED: these files changed since the build was made: %r' % bad)
        for k, tgt, bak, imd5, omd5, cur in rows:
            if cur == omd5: print(k, 'already installed'); continue
            if not os.path.exists(bak): shutil.copyfile(tgt, bak)
            assert md5f(bak) == imd5, 'backup mismatch ' + bak
            shutil.copyfile(os.path.join(B, m['outputs'][k]['path']), tgt)
            assert md5f(tgt) == omd5, 'copy mismatch ' + tgt
            print(k, 'installed', tgt)
    elif cmd == 'uninstall':
        for k, tgt, bak, imd5, omd5, cur in rows:
            if cur == imd5: print(k, 'already original'); continue
            assert os.path.exists(bak) and md5f(bak) == imd5, 'no valid backup for ' + tgt
            shutil.copyfile(bak, tgt); assert md5f(tgt) == imd5
            print(k, 'restored', tgt)
    else:
        sys.exit('install | uninstall | status')
if __name__ == '__main__':
    main()

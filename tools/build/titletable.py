"""Edit the championship table in pac/evt/evt_data.pac and evt_data_p10.pac (SHDC id 13; p10 carries a full copy, BPE-compressed text) and write the pac back.
Found 2026-11-14 (writeup/Belt_backport.md section 25). Row format, 12 columns:
  title_id  intro_video_id  intro_frames  cutscene_prop  main_prop  0  str_a  str_b  0 0 0 0
A title with video 0 never gets the title-belt scene (match-intro step 8). The video plays from
movies/titantron/bel_NNNN_0_0.bk2 (video id = 500000 + NNNN*100).
Usage: python3 -I titletable.py IN.pac OUT.pac --set "23 502300 600"   (title id, video id, frames)
       python3 -I titletable.py IN.pac --show"""
import sys, os, struct, argparse
here = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(here, '..', 'lib'), os.path.join(here, '..', 'audio')]
import yukes, bpe

ENTRY = 13

def bpe_compress(data):
    """Philip Gage byte-pair encoding, single block (data < 64 KB), in the layout tools/audio/bpe.py decodes."""
    assert len(data) < 65536
    buf = bytearray(data)
    left = list(range(256)); right = [0] * 256
    while True:
        used = set(buf) | {c for c in range(256) if left[c] != c} | {left[c] for c in range(256) if left[c] != c} | {right[c] for c in range(256) if left[c] != c}
        free = [c for c in range(256) if c not in used]
        if not free: break
        cnt = {}
        for i in range(len(buf) - 1):
            p = (buf[i], buf[i + 1]); cnt[p] = cnt.get(p, 0) + 1
        if not cnt: break
        p, n = max(cnt.items(), key=lambda kv: kv[1])
        if n < 4: break
        c = free[0]; left[c], right[c] = p
        out = bytearray(); i = 0
        while i < len(buf):
            if i + 1 < len(buf) and buf[i] == p[0] and buf[i + 1] == p[1]: out.append(c); i += 2
            else: out.append(buf[i]); i += 1
        buf = out
    # pair table: a byte >127 skips (b-127) literal codes and is followed by exactly one entry;
    # a byte n <= 127 is followed by n+1 entries. Entry = left (+ right when left != code).
    tab = bytearray(); c = 0
    def entry(c):
        tab.append(left[c])
        if left[c] != c: tab.append(right[c])
    while c < 256:
        k = 0
        while c + k < 256 and left[c + k] == c + k and k < 128: k += 1
        if k:
            tab.append(127 + k); c += k
            if c == 256: break
            entry(c); c += 1
            continue
        m = 0
        while c + m < 256 and left[c + m] != c + m and m < 128: m += 1
        tab.append(m - 1)
        for j in range(m): entry(c + j)
        c += m
    body = bytes(tab) + struct.pack('<H', len(buf)) + bytes(buf)
    return b'BPE ' + struct.pack('<3I', 0x100, len(body), len(data)) + body

def shdc_build(s):
    """Lay out like the original: entries back to back in offset order, each start 4-aligned; word 15 =
    align4(last_end - first); SHDC padded with zeros to a 256 multiple (HSPC sizes are in 256-byte units)."""
    first = min(f['off'] for f in s.files)
    b = bytearray(s.raw[:first])
    for i in sorted(range(len(s.files)), key=lambda i: s.files[i]['off']):
        f = s.files[i]; b += b'\0' * ((-len(b)) % 4); off = len(b)
        struct.pack_into('<4I', b, s.h[7] + 16 * i, f['id'], off, len(f['data']), f['z']); b += f['data']
    struct.pack_into('<I', b, 60, (len(b) - first + 3) // 4 * 4)
    b += b'\0' * ((-len(b)) % 256)
    return bytes(b)

def load(path):
    h = yukes.HSPC(open(path, 'rb').read()); s = yukes.SHDC(h.files[0]['data'])
    k = [i for i, f in enumerate(s.files) if f['id'] == ENTRY]; assert len(k) == 1, 'no table entry %d' % ENTRY
    d = s.files[k[0]]['data']; u = struct.unpack_from('<I', d, 12)[0]
    return h, s, k[0], bpe.expand(d, 16, u)[0]

if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('inp'); a.add_argument('out', nargs='?')
    a.add_argument('--set', action='append', default=[]); a.add_argument('--show', action='store_true')
    a = a.parse_args()
    h, s, k, text = load(a.inp)
    if a.show: print(text.decode()); sys.exit()
    lines = text.decode().split('\r\n')
    for spec in a.set:
        tid, vid, fr = spec.split()
        hit = [i for i, l in enumerate(lines) if l.split(' ')[0] == tid]
        assert len(hit) == 1, 'title %s rows: %d' % (tid, len(hit))
        f = lines[hit[0]].split(' '); old = lines[hit[0]]; f[1], f[2] = vid, fr; lines[hit[0]] = ' '.join(f)
        print('row', tid, ':', old, '->', lines[hit[0]])
    new = '\r\n'.join(lines).encode()
    comp = bpe_compress(new)
    assert bpe.expand(comp, 16, len(new))[0] == new, 'BPE round trip failed'
    print('entry %d: text %d -> %d bytes, BPE %d -> %d bytes' % (ENTRY, len(text), len(new), len(s.files[k]['data']), len(comp)))
    s.files[k]['data'] = comp
    h.files[0]['data'] = shdc_build(s)
    out = h.build()[0]
    open(a.out, 'wb').write(out)
    _, _, _, t2 = load(a.out); assert t2 == new
    print('wrote', a.out, len(out), 'bytes (in', len(h.raw), ')')

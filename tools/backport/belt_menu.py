"""Replace one belt picture in pac/menu/win/Assets/wwe19_texture/belt/ltag_belt_all_win.pac (the championship select images).
Entry 0 is the layout (names 000_wwe_heavy...); entries 1..90 are 512x256 BC7 DDS in the same order as the names, e.g.
'023_wwe_champ_bull' (Brahma Bull) = entry 21. The picture is rendered from a title-belt prop pac with beltshot.py.
  belt_menu.py --menu ltag_belt_all_win.pac --name 023_wwe_champ_bull --prop 2905.pac --out OUT.pac [--exposure 2.2]"""
import sys, os, re, argparse, struct, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import belt_port as bp, beltshot, etcpak
from PIL import Image
a = argparse.ArgumentParser(); [a.add_argument(k, required=True) for k in ('--menu', '--name', '--prop', '--out')]
a.add_argument('--exposure', type=float, default=2.2); a.add_argument('--zoom', type=float, default=1.65); a.add_argument('--png'); a = a.parse_args()
P = bp.read_prop(a.menu); E = P['entries']
names = [n.decode() for n in re.findall(rb'(\d{3}_[a-zA-Z0-9_]+)', E[0]['raw'])]
dds_entries = [i for i, e in enumerate(E) if e['raw'][:4] == b'DDS ']
k = dds_entries[names.index(a.name)]; old = E[k]['raw']; h, w = struct.unpack_from('<2I', old, 12)
assert struct.unpack_from('<I', old, 128)[0] == 98 and len(old) == 148 + w * h, 'expected BC7 DX10, no mips'
ss = 3; Z = a.zoom; col, cov = beltshot.render(a.prop, int(w * ss * Z), int(h * ss * Z), margin=0.02)
cy, cx = col.shape[0] // 2, col.shape[1] // 2; hh, hw = h * ss // 2, w * ss // 2      # stock framing: plate fills, strap ends cut
col = col[cy - hh:cy + hh, cx - hw:cx + hw]; cov = cov[cy - hh:cy + hh, cx - hw:cx + hw]
img = Image.fromarray((np.dstack([np.clip(col * a.exposure, 0, 1), cov]) * 255).astype('u1'), 'RGBA').resize((w, h), Image.LANCZOS)
rgba = np.asarray(img).copy(); rgba[..., :3] = (rgba[..., :3].astype('f4') * (rgba[..., 3:] / 255)).astype('u1')  # black bg like stock
if a.png: Image.fromarray(rgba).save(a.png)
data = etcpak.compress_bc7(np.ascontiguousarray(rgba).tobytes(), w, h)
new = old[:148] + data; assert len(new) == len(old)
open(a.out, 'wb').write(bp.write_prop(P, {k: new})); print('replaced entry', k, a.name, w, h)

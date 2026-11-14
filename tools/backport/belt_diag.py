"""Diagnostic belt build: same mesh as belt_port, but loud test textures, so one in-game look answers
'is the game using this pac's texture pack?'. Colour = magenta/green checker with 8 coloured bands (UV v), metal 0,
mid roughness, flat normal. Usage: belt_diag.py --mod DIR --stock DIR --main 2905 --cut 5038 --out DIR"""
import sys, os, argparse, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import belt_port as bp
def test_textures(n=1024):
    y, x = np.mgrid[0:n, 0:n]; c = np.zeros((n, n, 4), 'u1'); c[..., 3] = 255
    chk = ((x // 64 + y // 64) % 2).astype(bool); c[chk] = (255, 0, 255, 255); c[~chk] = (0, 255, 0, 255)
    bands = [(255,0,0),(255,128,0),(255,255,0),(0,255,255),(0,0,255),(255,255,255),(0,0,0),(255,0,255)]
    for k, col in enumerate(bands):   # thin stripe every 1/8 of v: tells which part of the texture a surface samples
        c[k * n // 8: k * n // 8 + 24, :, :3] = col
    nrm = np.zeros((n, n, 4), 'u1'); nrm[..., 0] = 128; nrm[..., 1] = 128; nrm[..., 3] = 255
    p = np.zeros((n, n, 4), 'u1'); p[..., 1] = 128; p[..., 2] = 255; p[..., 3] = 255
    return [('belt', bp.dds(c, 'DXT1')), ('belt_n', bp.dds(nrm, 'ATI2')), ('belt_p', bp.dds(p, 'DXT1'))]
def uv_textures(n=1024):
    """R = u, G = v (0..255), B = 0; black grid line every 1/16. Reading a colour off a screenshot gives the sampled UV."""
    y, x = np.mgrid[0:n, 0:n]; c = np.zeros((n, n, 4), 'u1'); c[..., 0] = x * 255 // (n - 1); c[..., 1] = y * 255 // (n - 1); c[..., 3] = 255
    g = (x % (n // 16) < 4) | (y % (n // 16) < 4); c[g, :3] = 0
    nrm = np.zeros((n, n, 4), 'u1'); nrm[..., 0] = 128; nrm[..., 1] = 128; nrm[..., 3] = 255
    p = np.zeros((n, n, 4), 'u1'); p[..., 1] = 128; p[..., 2] = 255; p[..., 3] = 255
    return [('belt', bp.dds(c, 'DXT1')), ('belt_n', bp.dds(nrm, 'ATI2')), ('belt_p', bp.dds(p, 'DXT1'))]
a = argparse.ArgumentParser(); a.add_argument('--uvgrad', action='store_true'); [a.add_argument(k, required=True) for k in ('--mod', '--stock', '--main', '--cut', '--out')]; a = a.parse_args()
os.makedirs(a.out, exist_ok=True); mods = {f.split('_')[-1][:-4].lower(): os.path.join(a.mod, f) for f in os.listdir(a.mod) if f.endswith('.mdl')}
import sys as _s
T = test_textures() if '--uvgrad' not in _s.argv else uv_textures()
for pid, key in ((a.main, 'default'), (a.cut, 'cutscene')):
    out, rep, info = bp.port(os.path.join(a.stock, pid + '.pac'), mods[key], None, T)
    open(os.path.join(a.out, pid + '.pac'), 'wb').write(out); print(pid, json.dumps({k: info[k] for k in ('vc', 'shift')}))

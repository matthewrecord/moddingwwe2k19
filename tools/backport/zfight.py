"""GATE: near-tie surfaces. My renderer has perfect depth precision, so where gear and visible skin sit within a few mm of each other it
quietly picks the skin, but 2K19 may pick the gear (Raquel's black lace wedges). This flags those ties instead of trusting the winner.
Renders the body alone and the gear alone from many angles incl. below; for every pixel where skin is visible, measures how far
behind it the nearest gear surface sits. FAIL if more than --max of visible-skin pixels have gear within --mm.
Usage: zfight.py PAC [--mm 5] [--max 0.03] [--box x0 x1 y0 y1]"""
import sys,os,argparse,numpy as np;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gamerender as gr
ap=argparse.ArgumentParser(); ap.add_argument('pac'); ap.add_argument('--mm',type=float,default=5); ap.add_argument('--max',type=float,default=0.03)
ap.add_argument('--box',type=float,nargs=4,default=(-45,45,-190,0)); a=ap.parse_args()
B,TX,hide=gr.load(a.pac); ob=gr.gather({0:B[0]},TX,hide); og=gr.gather({f:d for f,d in B.items() if f!=0},TX,hide); of=ob+og
G=[];worst=(0,None)
for az in range(0,360,30):
    for el in (-30,-10,15):
        gr.VIEWS['t']=(az,el)
        gr.render(of,'t',tuple(a.box),300); Zf=gr.LASTZ.copy(); gr.render(ob,'t',tuple(a.box),300); Zb=gr.LASTZ.copy()
        skin=np.isfinite(Zb)&(np.abs(Zf-Zb)<1e-4)                      # skin is the front surface here
        gr.render(og,'t',tuple(a.box),300); g=(gr.LASTZ-Zb)[skin]; g=g[np.isfinite(g)&(g>=0)]
        if len(g): G.append(g); f=(g<a.mm/10).mean(); worst=max(worst,(f,(az,el)))
g=np.concatenate(G); f=(g<a.mm/10).mean()
print(f'visible-skin px with gear <{a.mm}mm behind: {f:.3%}  (worst view {worst[1]}: {worst[0]:.3%})  ->',
      'PASS' if f<=a.max else 'FAIL: likely in-game z-fight (black/gear patches over skin); find the triangles with the ID buffer')
sys.exit(0 if f<=a.max else 1)

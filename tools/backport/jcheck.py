"""Compare an object we wrote against the conventions in his ports. Returns a list of problems."""
import numpy as np,struct
def raw_skin(j,o):
    f=o['f']; return np.frombuffer(j.b,np.dtype([('i','>u2'),('p','>u2'),('w','>f4')]),f[0]*f[23],f[27]+8).reshape(f[0],f[23])
def check_object(j,k,ref_j=None,ref_k=None):
    o=j.objs[k]; f=o['f']; P=[]; sk=raw_skin(j,o); npal=len(j.palette)
    used=sk['w']>0
    if np.any(sk['i'][~used]!=0xFFFF): P.append('empty skin slots not 0xFFFF (%d)'%int(np.sum(sk['i'][~used]!=0xFFFF)))
    real=sk['i']!=0xFFFF
    if np.any(sk['i'][real]>=npal): P.append('skin slot beyond palette')
    if np.any(sk['p']!=0): P.append('skin pad field nonzero')
    ws=sk['w'].sum(1)
    if np.any(np.abs(ws-1)>1e-3): P.append('weights do not sum to 1 (%d verts)'%int(np.sum(np.abs(ws-1)>1e-3)))
    # real slots first, ascending
    for v in range(len(sk)):
        r=sk['i'][v]; n=real[v].sum()
        if not real[v][:n].all() or np.any(np.diff(r[:n].astype(int))<=0): P.append('slot order differs from his (first at vertex %d)'%v); break
    if not np.isfinite(o['pos']).all() or not np.isfinite(o['nrm']).all(): P.append('non-finite vertex data')
    nl=np.linalg.norm(o['nrm'],axis=1)
    if np.any(np.abs(nl-1)>0.05): P.append('normals not unit length (%d)'%int(np.sum(np.abs(nl-1)>0.05)))
    import jboy
    prim,ix=j.indices(o)
    if prim!=6: P.append('primitive not strip')
    if ix.max()>=f[0]: P.append('index out of range')
    if f[0]!=f[40]: P.append('record [0] != [40]')
    if ref_j is not None:
        rf=ref_j.objs[ref_k]['f']
        for i in range(46):
            if i in (0,26,27,28,29,38,39,40): continue
            if rf[i]!=f[i]: P.append(f'record field {i} differs from his ({rf[i]} vs {f[i]})')
    return P

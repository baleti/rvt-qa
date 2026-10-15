"""Vector-vs-vector geometry diff: Revit DXF primitives (per layer) vs our SVG paths (per element id), in paper mm.
Both sides are sampled along their length (0.25 mm); translation found by FFT correlation + ICP-style median refinement (scale is known: 304.8/view scale, y flipped).
Outputs: recall per Revit layer, unmatched-length ranking per our element id (precision offenders), chamfer and Hausdorff-95 in mm."""
import re, math, collections
import numpy as np
from scipy.spatial import cKDTree

HATCH = {'cut_fill', 'surface_fill', 'symbolic_fill', 'room_fill'}

def svg_polys(svg):
    out = []
    for m in re.finditer(r'<path\b([^>]*)>', svg):
        a = m.group(1)
        if re.search(r'stroke="none"', a) and 'fill="none"' not in a: continue      # filled shapes (hatch/solid) are not linework
        d = re.search(r' d="([^"]*)"', a)
        if not d: continue
        e = re.search(r'data-e="(\d+)"', a); sw = re.search(r'stroke-width="([\d.]+)"', a)
        for sub in re.split(r'(?=M)', d.group(1)):
            v = [float(x) for x in re.findall(r'-?\d+\.?\d*(?:e-?\d+)?', sub)]
            if len(v) >= 4: out.append((e.group(1) if e else '?', float(sw.group(1)) if sw else 0.0, np.array(list(zip(v[0::2], v[1::2])))))
    return out

def dxf_polys(fn, scale):
    from .layers import dxf_layers
    S = 304.8 / scale; L = dxf_layers(fn); out = []
    import ezdxf
    k = {1: 1/12, 2: 1.0, 4: 1/304.8, 5: 1/30.48, 6: 1/0.3048}.get(ezdxf.readfile(fn).header.get('$INSUNITS', 0), 1.0)
    for lay, ps in L.items():
        for p in ps: out.append((lay, np.stack([p[:, 0] * k * S, -p[:, 1] * k * S], 1)))
    return out

def sample(polys, step=0.25):
    pts, lab = [], []
    for l, *rest in polys:
        P = rest[-1]
        for a, b in zip(P[:-1], P[1:]):
            n = max(1, int(np.hypot(*(b - a)) / step)); t = (np.arange(n) + 0.5) / n
            pts.append(a + (b - a) * t[:, None]); lab += [l] * n
    return (np.concatenate(pts) if pts else np.zeros((0, 2))), np.array(lab)

def fft_offset(A, B, cell=1.0):
    lo = np.minimum(A.min(0), B.min(0)); hi = np.maximum(A.max(0), B.max(0)); span = hi - lo
    n = np.minimum((np.ceil(span / cell).astype(int) + 1) * 2, 4096); cell = max(cell, span[0] * 2 / n[0], span[1] * 2 / n[1])
    def img(P):
        I = np.zeros((int(n[1]), int(n[0]))); ij = ((P - lo) / cell).astype(int); ij = ij[(ij[:, 0] < n[0]) & (ij[:, 1] < n[1])]
        np.add.at(I, (ij[:, 1], ij[:, 0]), 1.0); return np.minimum(I, 1.0)
    C = np.fft.irfft2(np.conj(np.fft.rfft2(img(A))) * np.fft.rfft2(img(B)), s=(int(n[1]), int(n[0])))
    y, x = np.unravel_index(np.argmax(C), C.shape); x = x - n[0] if x > n[0] / 2 else x; y = y - n[1] if y > n[1] / 2 else y
    return np.array([x * cell, y * cell], float)

def compare(svg_text, dxf, scale, tol_mm=0.6):
    ours = svg_polys(svg_text); ref = dxf_polys(dxf, scale)
    A, la = sample(ours); B, lb = sample(ref)
    if len(A) < 20 or len(B) < 20: return None
    off = fft_offset(B, A)                  # B + off ~ A
    for _ in range(5):
        d, i = cKDTree(A).query(B + off); m = d < 15 * tol_mm
        if m.sum() < 10: break
        off += np.median(A[i[m]] - (B[m] + off), 0)
    Bs = B + off; ta, tb = cKDTree(A), cKDTree(Bs)
    db = ta.query(Bs)[0]; da = tb.query(A)[0]
    res = dict(offset_mm=[round(float(off[0]), 2), round(float(off[1]), 2)], tol_mm=tol_mm,
               recall=round(float((db <= tol_mm).mean()), 3), precision=round(float((da <= tol_mm).mean()), 3),
               chamfer_mm=round(float(db.mean() + da.mean()) / 2, 2), hausdorff95_mm=round(float(max(np.percentile(db, 95), np.percentile(da, 95))), 2),
               revit_mm=round(len(B) * 0.25), ours_mm=round(len(A) * 0.25))
    per = collections.defaultdict(lambda: [0, 0])
    for l, d in zip(lb, db): per[l][0] += 1; per[l][1] += d <= tol_mm
    res['layers'] = [dict(layer=str(l), len_mm=round(n * 0.25), recall=round(float(m) / n, 3)) for l, (n, m) in sorted(per.items(), key=lambda kv: -(kv[1][0] - kv[1][1]))[:20]]
    unm = collections.Counter(); tot = collections.Counter()
    for l, d in zip(la, da): tot[l] += 1; unm[l] += d > tol_mm
    res['extra_elements'] = [dict(element=str(l), extra_mm=round(float(n) * 0.25), of_mm=round(float(tot[l]) * 0.25)) for l, n in unm.most_common(15) if n > 8]
    return res

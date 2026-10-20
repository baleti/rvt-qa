"""Vector-vs-vector geometry diff: Revit DXF primitives (per layer) vs our SVG paths (per element id), in paper mm.
Both sides are sampled along their length (0.25 mm); translation found by FFT correlation + ICP-style median refinement (scale is known: 304.8/view scale, y flipped).
Outputs: recall per Revit layer, unmatched-length ranking per our element id (precision offenders), chamfer and Hausdorff-95 in mm."""
import re, math, collections
import numpy as np
from scipy.spatial import cKDTree

HATCH = {'cut_fill', 'surface_fill', 'symbolic_fill', 'room_fill'}

def _clip_seg(a, b, r):
    """Liang-Barsky: segment a-b clipped to rect r=(x0,y0,x1,y1); None when fully outside"""
    t0, t1 = 0.0, 1.0; d = b - a
    for p, q in ((-d[0], a[0] - r[0]), (d[0], r[2] - a[0]), (-d[1], a[1] - r[1]), (d[1], r[3] - a[1])):
        if p == 0:
            if q < 0: return None
        else:
            t = q / p
            if p < 0: t0 = max(t0, t)
            else: t1 = min(t1, t)
            if t0 > t1: return None
    return a + d * t0, a + d * t1

def _clip_poly(P, r):
    """clip a polyline to rect r; returns a list of polylines"""
    out, cur = [], []
    for a, b in zip(P[:-1], P[1:]):
        c = _clip_seg(a, b, r)
        if c is None:
            if len(cur) > 1: out.append(np.array(cur))
            cur = []; continue
        if cur and np.allclose(cur[-1], c[0]): cur.append(c[1])
        else:
            if len(cur) > 1: out.append(np.array(cur))
            cur = [c[0], c[1]]
    if len(cur) > 1: out.append(np.array(cur))
    return out

def svg_polys(svg):
    out = []
    clips = {m.group(1): tuple(float(m.group(k)) for k in (2, 3, 4, 5)) for m in re.finditer(r'<clipPath id="([^"]+)"><rect x="([-\d.e]+)" y="([-\d.e]+)" width="([-\d.e]+)" height="([-\d.e]+)"', svg)}
    clips = {k: (x, y, x + w, y + h) for k, (x, y, w, h) in clips.items()}      # the SVG clip (crop region) hides ink that Revit's DXF does not contain
    for m in re.finditer(r'<path\b([^>]*)>', svg):
        a = m.group(1)
        if re.search(r'stroke="none"', a) and 'fill="none"' not in a: continue      # filled shapes (hatch/solid) are not linework
        d = re.search(r' d="([^"]*)"', a)
        if not d: continue
        e = re.search(r'data-e="(\d+)"', a); sw = re.search(r'stroke-width="([\d.]+)"', a)
        for sub in re.split(r'(?=M)', d.group(1)):
            v = [float(x) for x in re.findall(r'-?\d+\.?\d*(?:e-?\d+)?', sub)]
            if len(v) < 4: continue
            P = np.array(list(zip(v[0::2], v[1::2]))); cm = re.search(r'clip-path="url\(#([^)]+)\)"', a)
            for Q in (_clip_poly(P, clips[cm.group(1)]) if cm and cm.group(1) in clips else [P]):
                out.append((e.group(1) if e else '?', float(sw.group(1)) if sw else 0.0, Q))
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

def fft_offset(A, B, cell=1.0, k=1):
    lo = np.minimum(A.min(0), B.min(0)); hi = np.maximum(A.max(0), B.max(0)); span = hi - lo
    n = np.minimum((np.ceil(span / cell).astype(int) + 1) * 2, 4096); cell = max(cell, span[0] * 2 / n[0], span[1] * 2 / n[1])
    def img(P):
        I = np.zeros((int(n[1]), int(n[0]))); ij = ((P - lo) / cell).astype(int); ij = ij[(ij[:, 0] < n[0]) & (ij[:, 1] < n[1])]
        np.add.at(I, (ij[:, 1], ij[:, 0]), 1.0); return np.minimum(I, 1.0)
    C = np.fft.irfft2(np.conj(np.fft.rfft2(img(A))) * np.fft.rfft2(img(B)), s=(int(n[1]), int(n[0])))
    peaks = []; C = C.copy(); r = max(2, int(3.0 / cell))   # top-k peaks with suppression: a periodic hatch makes several near-equal ones
    for _ in range(k):
        y, x = np.unravel_index(np.argmax(C), C.shape)
        if C[y, x] <= 0: break
        peaks.append(np.array([(x - n[0] if x > n[0] / 2 else x) * cell, (y - n[1] if y > n[1] / 2 else y) * cell], float))
        C[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1] = 0
    return peaks if k > 1 else peaks[0]

def pick_offset(A, B, tol_mm=0.6, k=6):
    """Pick the translation aligning B to A by refined reference-point matches."""
    tA = cKDTree(A); best = None
    candidates = fft_offset(B, A, k=k)
    if isinstance(candidates, np.ndarray): candidates = [candidates]  # fft_offset returns one vector when k=1
    for off in (candidates or [np.zeros(2)]):     # B + off ~ A; keep the candidate that matches most reference ink after ICP (walls/glazing pin the true shift, hatch only repeats it)
        off = off.copy()
        for _ in range(5):
            d, i = tA.query(B + off); m = d < 15 * tol_mm
            if m.sum() < 10: break
            off += np.median(A[i[m]] - (B[m] + off), 0)
        nm = int((tA.query(B + off)[0] <= tol_mm).sum())
        if best is None or nm > best[0]: best = (nm, off)
    return best[1]

def compare(svg_text, dxf, scale, tol_mm=0.6):
    ours = svg_polys(svg_text); ref = dxf_polys(dxf, scale)
    A, la = sample(ours); B, lb = sample(ref)
    if len(A) < 20 or len(B) < 20: return None
    off = pick_offset(A, B, tol_mm=tol_mm)
    Bs = B + off; ta, tb = cKDTree(A), cKDTree(Bs)
    db = ta.query(Bs)[0]; da = tb.query(A)[0]
    res = dict(offset_mm=[round(float(off[0]), 2), round(float(off[1]), 2)], tol_mm=tol_mm,
               recall=round(float((db <= tol_mm).mean()), 3), precision=round(float((da <= tol_mm).mean()), 3),
               chamfer_mm=round(float(db.mean() + da.mean()) / 2, 2), hausdorff95_mm=round(float(max(np.percentile(db, 95), np.percentile(da, 95))), 2),
               revit_mm=round(len(B) * 0.25), ours_mm=round(len(A) * 0.25))
    per = collections.defaultdict(lambda: [0, 0])
    for l, d in zip(lb, db): per[l][0] += 1; per[l][1] += d <= tol_mm
    lbn = np.array([str(x) for x in lb]); lan = np.array([str(x) for x in la])
    def worst(P, lab, dist, name):     # unmatched sample nearest to the median of the unmatched ones (our paper mm)
        Q = P[(lab == name) & (dist > tol_mm)]
        if not len(Q): return None
        q = Q[np.argmin(np.hypot(*(Q - np.median(Q, 0)).T))]; return [round(float(q[0]), 1), round(float(q[1]), 1)]
    res['layers'] = [dict(layer=str(l), len_mm=round(n * 0.25), recall=round(float(m) / n, 3), at_mm=worst(Bs, lbn, db, str(l))) for l, (n, m) in sorted(per.items(), key=lambda kv: -(kv[1][0] - kv[1][1]))[:20]]
    unm = collections.Counter(); tot = collections.Counter()
    for l, d in zip(la, da): tot[l] += 1; unm[l] += d > tol_mm
    res['extra_elements'] = [dict(element=str(l), extra_mm=round(float(n) * 0.25), of_mm=round(float(tot[l]) * 0.25), at_mm=worst(A, lan, da, str(l))) for l, n in unm.most_common(15) if n > 8]
    return res

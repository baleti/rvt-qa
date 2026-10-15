"""Image-level diff of our view render vs Revit's export of the same view.
Steps: ink masks, bbox registration (scale+translate), SSIM, ink precision/recall, per-cell heatmap, long-line (grid) detection, bubble (circle) detection, OCR text compare.
All numeric; returns a dict of findings ranked by severity."""
import numpy as np, cv2, re
from skimage.metrics import structural_similarity as sk_ssim

def load_gray(p):
    im = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
    if im is None: raise IOError(p)
    return im

def ink(g, thr=200): return (g < thr).astype(np.uint8)

def content_bbox(m, minpix=1):
    ys, xs = np.nonzero(m)
    if len(xs) < minpix: return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())

def register(ours, ref, use_long_lines=True):
    """Return ours warped into ref's pixel frame by scale+translate matching the ink bboxes (robust: ignores 1px frame lines by trimming thin outliers)."""
    def robust_bbox(m):
        ys, xs = np.nonzero(m)
        if len(xs) == 0: return None
        return (np.percentile(xs, .2), np.percentile(ys, .2), np.percentile(xs, 99.8), np.percentile(ys, 99.8))
    a, b = robust_bbox(ink(ours)), robust_bbox(ink(ref))
    if a is None or b is None: return ours, (1, 1, 0, 0)
    sx = (b[2]-b[0])/max(a[2]-a[0], 1); sy = (b[3]-b[1])/max(a[3]-a[1], 1)
    s = (sx+sy)/2   # keep aspect
    tx = (b[0]+b[2])/2 - s*(a[0]+a[2])/2; ty = (b[1]+b[3])/2 - s*(a[1]+a[3])/2
    M = np.float32([[s, 0, tx], [0, s, ty]])
    w = cv2.warpAffine(ours, M, (ref.shape[1], ref.shape[0]), flags=cv2.INTER_AREA, borderValue=255)
    return w, (s, s, tx, ty)

def refine_shift(o, r, maxs=12):
    """phase-correlation style integer shift refinement on ink distance maps"""
    a = ink(o).astype(np.float32); b = ink(r).astype(np.float32)
    a = cv2.GaussianBlur(a, (0, 0), 2); b = cv2.GaussianBlur(b, (0, 0), 2)
    (dx, dy), resp = cv2.phaseCorrelate(b, a)
    if abs(dx) > maxs or abs(dy) > maxs: return o, (0, 0), resp
    M = np.float32([[1, 0, -dx], [0, 1, -dy]])
    return cv2.warpAffine(o, M, (o.shape[1], o.shape[0]), borderValue=255), (dx, dy), resp

def ink_pr(o, r, tol=3):
    A, B = ink(o), ink(r)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*tol+1, 2*tol+1))
    Bd, Ad = cv2.dilate(B, k), cv2.dilate(A, k)
    prec = float((A & Bd).sum()) / max(A.sum(), 1); rec = float((B & Ad).sum()) / max(B.sum(), 1)
    return prec, rec

def heatmap(o, r, cells=(8, 12), tol=3):
    """per-cell missing (ref ink with no ours within tol) and extra (ours ink with no ref) pixel fractions"""
    A, B = ink(o), ink(r)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*tol+1, 2*tol+1))
    miss = B & (1 - cv2.dilate(A, k)); extra = A & (1 - cv2.dilate(B, k))
    H, W = r.shape; ch, cw = H // cells[0], W // cells[1]; out = []
    for i in range(cells[0]):
        for j in range(cells[1]):
            y0, x0 = i*ch, j*cw; sl = (slice(y0, y0+ch), slice(x0, x0+cw))
            nb = int(B[sl].sum()); na = int(A[sl].sum())
            out.append(dict(i=i, j=j, box=(x0, y0, x0+cw, y0+ch), ref_ink=nb, our_ink=na,
                            missing=int(miss[sl].sum()), extra=int(extra[sl].sum()),
                            miss_frac=float(miss[sl].sum())/max(nb, 20), extra_frac=float(extra[sl].sum())/max(na, 20)))
    return out, miss, extra

def long_lines(g, minlen_frac=0.25):
    """detect long near-horizontal/vertical/diagonal line segments (grids) -> list of (x1,y1,x2,y2)"""
    m = ink(g, 215)*255
    H, W = g.shape; minlen = int(min(H, W)*minlen_frac)
    L = cv2.HoughLinesP(m, 1, np.pi/360, threshold=max(minlen//2, 40), minLineLength=minlen, maxLineGap=max(12, minlen//10))
    if L is None: return []
    segs = [tuple(int(v) for v in (l[0] if np.ndim(l)>1 else l)) for l in L]
    return merge_segs(segs)

def merge_segs(segs, ang_tol=2.0, dist_tol=6):
    def par(s):
        x1, y1, x2, y2 = s; a = np.degrees(np.arctan2(y2-y1, x2-x1)) % 180
        d = abs(-np.sin(np.radians(a))*x1 + np.cos(np.radians(a))*y1)
        return a, (np.cos(np.radians(a))*y1 - np.sin(np.radians(a))*x1)
    groups = []
    for s in segs:
        a, d = par(s)
        for g in groups:
            if min(abs(a-g['a']), 180-abs(a-g['a'])) < ang_tol and abs(d-g['d']) < dist_tol:
                g['s'].append(s); break
        else: groups.append(dict(a=a, d=d, s=[s]))
    out = []
    for g in groups:
        pts = [(s[0], s[1]) for s in g['s']]+[(s[2], s[3]) for s in g['s']]
        a = np.radians(g['a']); u = np.array([np.cos(a), np.sin(a)])
        t = [p[0]*u[0]+p[1]*u[1] for p in pts]; i0, i1 = int(np.argmin(t)), int(np.argmax(t))
        out.append(pts[i0]+pts[i1])
    return out

def match_lines(ours, ref, tol=8):
    """greedy match by midpoint+angle; returns matched pairs, unmatched ref (missing), unmatched ours (extra)"""
    def feat(s):
        x1, y1, x2, y2 = s; return ((x1+x2)/2, (y1+y2)/2, np.degrees(np.arctan2(y2-y1, x2-x1)) % 180, np.hypot(x2-x1, y2-y1))
    fo = [feat(s) for s in ours]; fr = [feat(s) for s in ref]; used = set(); pairs = []; miss = []
    for j, r in enumerate(fr):
        best = None
        for i, o in enumerate(fo):
            if i in used: continue
            da = min(abs(o[2]-r[2]), 180-abs(o[2]-r[2]))
            if da > 3: continue
            # perpendicular distance from o's midpoint to r's infinite line
            a = np.radians(r[2]); d = abs(-np.sin(a)*(o[0]-r[0]) + np.cos(a)*(o[1]-r[1]))
            if d <= tol and (best is None or d < best[0]): best = (d, i)
        if best: used.add(best[1]); pairs.append((best[1], j, best[0], fo[best[1]][3]-r[3]))
        else: miss.append(ref[j])
    extra = [ours[i] for i in range(len(ours)) if i not in used]
    return pairs, miss, extra

def circles(g):
    """grid bubbles / section heads: HoughCircles"""
    b = cv2.GaussianBlur(g, (5, 5), 1.2)
    c = cv2.HoughCircles(b, cv2.HOUGH_GRADIENT, dp=1.2, minDist=14, param1=120, param2=22, minRadius=7, maxRadius=24)
    return [] if c is None else [tuple(float(v) for v in x) for x in c[0]]

def match_pts(ours, ref, tol=12):
    used = set(); miss = []; pairs = []
    for r in ref:
        best = None
        for i, o in enumerate(ours):
            if i in used: continue
            d = np.hypot(o[0]-r[0], o[1]-r[1])
            if d <= tol and (best is None or d < best[0]): best = (d, i)
        if best: used.add(best[1]); pairs.append((best[1], r, best[0]))
        else: miss.append(r)
    extra = [o for i, o in enumerate(ours) if i not in used]
    return pairs, miss, extra

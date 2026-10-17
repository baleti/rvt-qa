#!/usr/bin/env python3
"""review/audit_regions.py PAIRBASE REGIONS.json OUTDIR : per-region audit of a Revit/ours pair (same size and framing, from review/build.py).
REGIONS: {name: [fx0, fy0, fx1, fy1, kind]} fractions of the image; kind = 'line' (linework: stroke width + edge F1) or 'image' (colour render: Lab delta, SSIM, background colour).
Writes OUTDIR/<name>.png (Revit above / | ours, 2x) and OUTDIR/audit.json + audit.md. Local only (Autodesk-derived)."""
import sys, os, json
import numpy as np, cv2
from skimage.metrics import structural_similarity as ssim
base, regf, out = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(out, exist_ok=True)
R = cv2.imread(base + '__revit.png'); O = cv2.imread(base + '__ours.png'); H, W = R.shape[:2]
regs = json.load(open(regf)); res = {}
def runs(mask, axis):
    m = mask if axis == 1 else mask.T; L = []
    for row in m[::2]:
        d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]])); s = np.nonzero(d == 1)[0]; e = np.nonzero(d == -1)[0]; L += list(e - s)
    L = np.array([x for x in L if x <= 14]); return float(np.percentile(L, 75)) if len(L) > 20 else None
def lab_mean(im, mask=None):
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(float); return lab.mean(0) if mask is None else lab[mask.reshape(-1)].mean(0)
for name, (fx0, fy0, fx1, fy1, kind) in regs.items():
    x0, y0, x1, y1 = int(fx0 * W), int(fy0 * H), int(fx1 * W), int(fy1 * H); a, b = R[y0:y1, x0:x1], O[y0:y1, x0:x1]
    if a.size == 0: continue
    ga, gb = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY); m = dict(box_px=[x0, y0, x1, y1])
    m['ssim'] = round(float(ssim(ga, gb)), 3); m['ink_ratio_ours_over_revit'] = round(float((gb < 160).mean() / max((ga < 160).mean(), 1e-6)), 3)
    la, lb = lab_mean(a), lab_mean(b); m['lab_mean_delta'] = round(float(np.linalg.norm(la - lb)), 1); m['mean_rgb_revit'] = [int(v) for v in a.reshape(-1, 3).mean(0)[::-1]]; m['mean_rgb_ours'] = [int(v) for v in b.reshape(-1, 3).mean(0)[::-1]]
    if kind == 'line':
        ia, ib = (ga < 150), (gb < 150)
        wa_v, wb_v, wa_h, wb_h = runs(ia, 1), runs(ib, 1), runs(ia, 0), runs(ib, 0)
        m['vline_width_px'] = [wa_v, wb_v]; m['hline_width_px'] = [wa_h, wb_h]
        ea, eb = cv2.Canny(ga, 60, 150), cv2.Canny(gb, 60, 150); k = np.ones((5, 5), np.uint8); da, db = cv2.dilate(ea, k), cv2.dilate(eb, k)
        p = float(((eb > 0) & (da > 0)).sum() / max((eb > 0).sum(), 1)); r = float(((ea > 0) & (db > 0)).sum() / max((ea > 0).sum(), 1)); m['edge_P'] = round(p, 3); m['edge_R'] = round(r, 3)
    else:
        sa = cv2.cvtColor(a, cv2.COLOR_BGR2HSV)[:, :, 1].astype(float).mean(); sb = cv2.cvtColor(b, cv2.COLOR_BGR2HSV)[:, :, 1].astype(float).mean(); m['mean_saturation'] = [round(sa, 1), round(sb, 1)]
        m['top_rows_colour_revit'] = [int(v) for v in a[:max(2, a.shape[0] // 12)].reshape(-1, 3).mean(0)[::-1]]; m['top_rows_colour_ours'] = [int(v) for v in b[:max(2, b.shape[0] // 12)].reshape(-1, 3).mean(0)[::-1]]
    sc = 2.0 if max(a.shape) < 700 else 1.0; f = lambda im: cv2.resize(im, None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC) if sc != 1 else im
    A, B = f(a), f(b); lay = np.concatenate([A, np.full((A.shape[0], 10, 3), 90, np.uint8), B], 1) if A.shape[1] < 900 else np.concatenate([A, np.full((8, A.shape[1], 3), 90, np.uint8), B], 0)
    cv2.imwrite(os.path.join(out, name + '.png'), lay); res[name] = m
json.dump(res, open(os.path.join(out, 'audit.json'), 'w'), indent=1)
md = ['| region | kind | SSIM | ink ratio ours/Revit | Lab delta | v/h line width px (Revit, ours) | edge P/R |', '|---|---|---|---|---|---|---|']
for n, m in res.items(): md.append('| %s | %s | %s | %s | %s | %s / %s | %s/%s |' % (n, regs[n][4], m['ssim'], m['ink_ratio_ours_over_revit'], m['lab_mean_delta'], m.get('vline_width_px', '-'), m.get('hline_width_px', '-'), m.get('edge_P', '-'), m.get('edge_R', '-')))
open(os.path.join(out, 'audit.md'), 'w').write('\n'.join(md)); print('\n'.join(md))

#!/usr/bin/env python3
"""review/build3d.py ROOT : pair Revit PNG exports ROOT/revit/<file>/<id>.png with viewer screenshots ROOT/viewer/<file>/<id>__ours3d.png
into ROOT/3d_<file>/<id>_<name>_3d.{revit,ours,side,diff}.png + json, and write ROOT/pairs3d.json (read by review/index.py).
Framing: viewer screenshots are 'fit to model' while Revit frames its own way, so ours is scaled uniformly and shifted so that the bounding boxes of the non-white content coincide (approximate, flagged)."""
import sys, os, json, glob, re
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from qa import imgdiff as D
root = sys.argv[1]; out = []
def bbox(img, thr=28):
    edge = np.concatenate([img[0], img[-1], img[:, 0], img[:, -1]]); bg = np.median(edge, 0)      # background = median border colour (viewer panel is not white)
    m = (np.abs(img.astype(int) - bg).max(2) > thr); ys, xs = np.nonzero(m)
    if len(xs) < 50: return (0, 0, img.shape[1] - 1, img.shape[0] - 1)
    return (np.percentile(xs, .1), np.percentile(ys, .1), np.percentile(xs, 99.9), np.percentile(ys, 99.9))
def label(img, text, h=34):
    cv2.rectangle(img, (0, 0), (img.shape[1], h), (255, 255, 255), -1); cv2.putText(img, text, (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2, cv2.LINE_AA); return img
def fit_h(img, h): return cv2.resize(img, (max(1, int(img.shape[1] * h / img.shape[0])), h), interpolation=cv2.INTER_AREA)
for fdir in sorted(glob.glob(os.path.join(root, 'revit', '*'))):
    f = os.path.basename(fdir); names = {}; cams = {}; types = {}
    ix = os.path.join(fdir, 'index.tsv')
    if os.path.exists(ix):
        for l in open(ix, encoding='utf-8', errors='replace'):
          c = l.rstrip('\n').split('\t')
          if c[0] == 'VIEW' and len(c) > 5: names[c[1]] = c[4]; types[c[1]] = c[3]
    cp = os.path.join(fdir, 'cameras.tsv')
    if os.path.exists(cp):
        for l in open(cp):
          c = l.rstrip('\n').split('\t')
          if c and c[0].isdigit(): cams[c[0]] = 'eye(%s) tgt(%s) persp=%s' % (c[2], c[3], c[5] if len(c) > 5 else '?')
    for rp in sorted(glob.glob(os.path.join(fdir, '*.png'))):
      vid = os.path.basename(rp)[:-4]
      for vsuf, vtag in (('__ours3d.png', ''), ('__ours3d_hl.png', ' (hidden line)')):
        op = os.path.join(root, 'viewer', f, vid + vsuf)
        if not os.path.exists(op): continue
        R = cv2.imread(rp, cv2.IMREAD_COLOR); O = cv2.imread(op, cv2.IMREAD_COLOR); H, W = R.shape[:2]; blank = bool((O.min(2) < 235).mean() < 0.0005)      # viewer shot without any content
        rb, ob = bbox(R), bbox(O); s = min((rb[2] - rb[0]) / max(ob[2] - ob[0], 1), (rb[3] - rb[1]) / max(ob[3] - ob[1], 1))
        tx = (rb[0] + rb[2]) / 2 - s * (ob[0] + ob[2]) / 2; ty = (rb[1] + rb[3]) / 2 - s * (ob[1] + ob[3]) / 2
        ours = cv2.warpAffine(O, np.float32([[s, 0, tx], [0, s, ty]]), (W, H), flags=cv2.INTER_AREA, borderValue=(255, 255, 255))
        t = {'ThreeD': '3d', 'FloorPlan': 'plan', 'CeilingPlan': 'plan', 'EngineeringPlan': 'plan', 'AreaPlan': 'plan', 'Elevation': 'elevation', 'Section': 'section', 'Detail': 'detail', 'DrawingSheet': 'sheet'}.get(types.get(vid), '3d'); nm = names.get(vid, vid) + vtag
        sub = os.path.join(root, '3d_' + f); os.makedirs(sub, exist_ok=True); base = os.path.join(sub, '%s_%s_%s' % (vid, re.sub(r'[^A-Za-z0-9._-]+', '_', nm)[:40], t))
        # refine the bbox alignment on ink maps (multi-scale + shift, small range), then score ink precision/recall
        gw = min(1.0, 1600.0 / max(W, H)); Rg = cv2.cvtColor(cv2.resize(R, None, fx=gw, fy=gw, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        Og = cv2.cvtColor(cv2.resize(ours, (Rg.shape[1], Rg.shape[0]), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        sc_ = np.exp(np.linspace(-0.08, 0.08, 17)); _, (rs, rdx, rdy, rscore, _M) = D.register_search(Og, Rg, scales=sc_)
        Wk, Hk = Rg.shape[1], Rg.shape[0]; c = W / float(Wk)
        ours = cv2.warpAffine(ours, np.float32([[rs, 0, ((1 - rs) * Wk / 2 + rdx) * c], [0, rs, ((1 - rs) * Hk / 2 + rdy) * c]]), (W, H), flags=cv2.INTER_AREA, borderValue=(255, 255, 255))
        Ow = cv2.cvtColor(cv2.resize(ours, (Wk, Hk), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        p6, r6 = D.ink_pr(Ow, Rg, 6); p3, r3 = D.ink_pr(Ow, Rg, 3); f6 = 2 * p6 * r6 / max(p6 + r6, 1e-6); score3 = round(100 * f6, 1)
        gd = min(1.0, 2400.0 / max(W, H)); ga = cv2.cvtColor(cv2.resize(ours, None, fx=gd, fy=gd, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY); gb = cv2.cvtColor(cv2.resize(R, (ga.shape[1], ga.shape[0]), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        A, B = D.ink(ga, 215), D.ink(gb, 215); tt = max(2, int(round(max(ga.shape) / 400.0))); kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * tt + 1, 2 * tt + 1))
        diff = np.full(ga.shape + (3,), 255, np.uint8); diff[(A | B).astype(bool) & ((A & cv2.dilate(B, kern)) | (B & cv2.dilate(A, kern))).astype(bool)] = (170, 170, 170)
        diff[(B & (1 - cv2.dilate(A, kern))).astype(bool)] = (200, 160, 0); diff[(A & (1 - cv2.dilate(B, kern))).astype(bool)] = (40, 40, 230)
        for suf, im in (('revit', R), ('ours', ours), ('diff', diff)): cv2.imwrite('%s__%s.png' % (base, suf), im, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        hh = min(1500, H); a = fit_h(R, hh); side = np.concatenate([label(a, 'REVIT  %s %s' % (nm, vid)), np.full((a.shape[0], 12, 3), 90, np.uint8), label(fit_h(ours, hh), 'OURS (rvt-viewer)  %s' % nm)], 1)
        cv2.imwrite(base + '__side.png', side, [cv2.IMWRITE_PNG_COMPRESSION, 9]); cv2.imwrite(base + '__thumb.jpg', fit_h(side, 300), [cv2.IMWRITE_JPEG_QUALITY, 80])
        m = dict(file=f, id=vid, name=nm, type=t, path='3d_%s/%s' % (f, os.path.basename(base)), reg_score=round(float(rscore), 3), approx=bool(rscore < 0.35), score=(None if blank else score3), blank=blank, ink=dict(P3=round(float(p3), 3), R3=round(float(r3), 3), P6=round(float(p6), 3), R6=round(float(r6), 3)), style=('hidden-line' if vtag else 'shaded'), size=[W, H], camera=cams.get(vid, ''), source='rvt-viewer screenshot')
        json.dump(m, open(base + '.json', 'w')); out.append(m); print('ok', m['path'])
json.dump(out, open(os.path.join(root, 'pairs3d.json'), 'w'), indent=1); print(len(out), 'pairs')
with open(os.path.join(root, 'scores3d.tsv'), 'w') as fh:
    fh.write('file\tview\tname\tstyle\tscore\tP6\tR6\n')
    for m in sorted(out, key=lambda m: (m['style'], m['score'] if m['score'] is not None else -1)): fh.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (m['file'], m['id'], m['name'], m['style'], m['score'], m['ink']['P6'], m['ink']['R6']))

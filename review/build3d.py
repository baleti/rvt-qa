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
        R = cv2.imread(rp, cv2.IMREAD_COLOR); O = cv2.imread(op, cv2.IMREAD_COLOR); H, W = R.shape[:2]
        rb, ob = bbox(R), bbox(O); s = min((rb[2] - rb[0]) / max(ob[2] - ob[0], 1), (rb[3] - rb[1]) / max(ob[3] - ob[1], 1))
        tx = (rb[0] + rb[2]) / 2 - s * (ob[0] + ob[2]) / 2; ty = (rb[1] + rb[3]) / 2 - s * (ob[1] + ob[3]) / 2
        ours = cv2.warpAffine(O, np.float32([[s, 0, tx], [0, s, ty]]), (W, H), flags=cv2.INTER_AREA, borderValue=(255, 255, 255))
        t = {'ThreeD': '3d', 'FloorPlan': 'plan', 'CeilingPlan': 'plan', 'EngineeringPlan': 'plan', 'AreaPlan': 'plan', 'Elevation': 'elevation', 'Section': 'section', 'Detail': 'detail', 'DrawingSheet': 'sheet'}.get(types.get(vid), '3d'); nm = names.get(vid, vid) + vtag
        sub = os.path.join(root, '3d_' + f); os.makedirs(sub, exist_ok=True); base = os.path.join(sub, '%s_%s_%s' % (vid, re.sub(r'[^A-Za-z0-9._-]+', '_', nm)[:40], t))
        gd = min(1.0, 2400.0 / max(W, H)); ga = cv2.cvtColor(cv2.resize(ours, None, fx=gd, fy=gd, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY); gb = cv2.cvtColor(cv2.resize(R, (ga.shape[1], ga.shape[0]), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        A, B = D.ink(ga, 215), D.ink(gb, 215); tt = max(2, int(round(max(ga.shape) / 400.0))); kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * tt + 1, 2 * tt + 1))
        diff = np.full(ga.shape + (3,), 255, np.uint8); diff[(A | B).astype(bool) & ((A & cv2.dilate(B, kern)) | (B & cv2.dilate(A, kern))).astype(bool)] = (170, 170, 170)
        diff[(B & (1 - cv2.dilate(A, kern))).astype(bool)] = (200, 160, 0); diff[(A & (1 - cv2.dilate(B, kern))).astype(bool)] = (40, 40, 230)
        for suf, im in (('revit', R), ('ours', ours), ('diff', diff)): cv2.imwrite('%s__%s.png' % (base, suf), im, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        hh = min(1500, H); a = fit_h(R, hh); side = np.concatenate([label(a, 'REVIT  %s %s' % (nm, vid)), np.full((a.shape[0], 12, 3), 90, np.uint8), label(fit_h(ours, hh), 'OURS (rvt-viewer)  %s' % nm)], 1)
        cv2.imwrite(base + '__side.png', side, [cv2.IMWRITE_PNG_COMPRESSION, 9]); cv2.imwrite(base + '__thumb.jpg', fit_h(side, 300), [cv2.IMWRITE_JPEG_QUALITY, 80])
        m = dict(file=f, id=vid, name=nm, type=t, path='3d_%s/%s' % (f, os.path.basename(base)), reg_score=0.0, approx=True, score=None, size=[W, H], camera=cams.get(vid, ''), source='rvt-viewer screenshot')
        json.dump(m, open(base + '.json', 'w')); out.append(m); print('ok', m['path'])
json.dump(out, open(os.path.join(root, 'pairs3d.json'), 'w'), indent=1); print(len(out), 'pairs')

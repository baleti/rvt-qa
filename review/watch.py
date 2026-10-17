#!/usr/bin/env python3
"""review/watch.py ROOT FILE.rvt VIEWID LABEL [--svg-dir DIR] : snapshot one tracked view (render from the dev tree, qa-view numbers, review pair) into
ROOT/history/<file>_<viewid>/<LABEL>/ ; then rebuild ROOT/history/<file>_<viewid>/before_after.png (Revit | previous snapshot | this snapshot + numbers) and ROOT/history/INDEX.html.
Use after each rvt-sheets release that touches the view (LABEL = short git hash of the dev tree)."""
import sys, os, json, glob, shutil, importlib.machinery, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); QA = os.path.dirname(HERE); sys.path.insert(0, QA); sys.path.insert(0, HERE)
import numpy as np, cv2
from qa import gt
from build import build_pair, label as lab, fit_h
ld = importlib.machinery.SourceFileLoader('qav', os.path.join(QA, 'qa-view')); sp = importlib.util.spec_from_loader('qav', ld); qav = importlib.util.module_from_spec(sp); ld.exec_module(qav)
args = [a for a in sys.argv[1:]]; root, rvt, vid, tag = args[0], os.path.abspath(args[1]), int(args[2]), args[3]
base = os.path.join(root, 'history', '%s_%d' % (os.path.basename(rvt).replace('.rvt', ''), vid)); snap = os.path.join(base, tag); os.makedirs(snap, exist_ok=True)
g = gt.find_gt(rvt); work = os.path.join(snap, 'qa'); shutil.rmtree(os.path.join(work, 'ours'), ignore_errors=True)
r = qav.run_one(rvt, vid, g, work)
svg = os.path.join(work, 'ours', '%d.svg' % vid); png = os.path.join(g, '%d.png' % vid)
m = build_pair(svg, png, os.path.join(snap, 'pair'), tag) or {}
keep = {k: r.get(k) for k in ('score', 'pass', 'summary', 'text', 'image', 'geom', 'baseline', 'fonts')}
keep['findings_top'] = [{k: v for k, v in f.items() if k in ('kind', 'what', 'score', 'at_mm', 'n', 'median_mm', 'dist_mm', 'ratio')} for f in r.get('findings', [])[:12]]
json.dump(dict(label=tag, name=r.get('name'), pair=m, **keep), open(os.path.join(snap, 'numbers.json'), 'w'), indent=1, default=str)
for f in glob.glob(os.path.join(work, 'diff', '*')): pass
snaps = sorted([d for d in glob.glob(os.path.join(base, '*')) if os.path.isdir(d)], key=os.path.getmtime)
def nums(d):
    j = json.load(open(os.path.join(d, 'numbers.json'))); s = j.get('summary') or {}; gm = j.get('geom') or {}
    return '%s  score %s  SSIM %s  ink P/R %s/%s  DXF P/R %s/%s  text %s' % (j['label'], j.get('score'), s.get('ssim'), s.get('ink_P3'), s.get('ink_R3'), gm.get('precision'), gm.get('recall'), (j.get('text') or {}).get('matched'))
if len(snaps) >= 2:
    a, b = snaps[-2], snaps[-1]; rv = cv2.imread(os.path.join(b, 'pair__revit.png')); H = min(1300, rv.shape[0])
    cols = [lab(fit_h(rv, H), 'REVIT'), lab(fit_h(cv2.imread(os.path.join(a, 'pair__ours.png')), H), 'BEFORE ' + os.path.basename(a)), lab(fit_h(cv2.imread(os.path.join(b, 'pair__ours.png')), H), 'AFTER ' + os.path.basename(b))]
    img = np.concatenate([x for c in cols for x in (c, np.full((c.shape[0], 10, 3), 90, np.uint8))][:-1], 1)
    foot = np.full((70, img.shape[1], 3), 255, np.uint8); cv2.putText(foot, 'before: ' + nums(a), (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA); cv2.putText(foot, 'after : ' + nums(b), (8, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(base, 'before_after.png'), np.concatenate([img, foot], 0))
rows = []
for d in sorted(glob.glob(os.path.join(root, 'history', '*', '')) ):
    n = os.path.basename(os.path.dirname(d)); sn = sorted([x for x in glob.glob(os.path.join(d, '*')) if os.path.isdir(x)], key=os.path.getmtime)
    rows.append('<h3>%s</h3>%s<ul>%s</ul>' % (n, '<a href="%s/before_after.png"><img src="%s/before_after.png" style="max-width:100%%"></a>' % (n, n) if os.path.exists(os.path.join(d, 'before_after.png')) else '(one snapshot so far)', ''.join('<li>%s</li>' % nums(x) for x in sn)))
open(os.path.join(root, 'history', 'INDEX.html'), 'w').write('<!doctype html><meta charset=utf-8><title>Before / after</title><body style="font:14px sans-serif;margin:16px"><h1>Tracked views: before / after</h1>' + ''.join(rows))
print(nums(snaps[-1]))

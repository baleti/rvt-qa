#!/usr/bin/env python3
"""review/build.py SPEC.json OUTDIR : build Revit-vs-ours review pairs (local only, Autodesk-derived: never commit or publish).
SPEC: list of {label, results (qa-dash dir with results.jsonl + ours/*.svg), rvt (source file, for the Revit export lookup), per_type {sheet:3, plan:3, ...}}.
For every chosen view: NAME__revit.png, NAME__ours.png (same pixel size and framing, ours re-rendered from the SVG at the output scale), NAME__side.png, NAME__diff.png, NAME.json.
Framing: our aspect-preserving raster is registered onto Revit's PNG (multi-scale ink correlation, scale+translate only); reg score < 0.35 is flagged 'framing approximate'."""
import sys, os, re, json, subprocess, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import numpy as np, cv2
from qa import gt, imgdiff as D

TYPES = {'ViewSheet': 'sheet', 'FloorPlan': 'plan', 'CeilingPlan': 'plan', 'EngineeringPlan': 'plan', 'AreaPlan': 'plan', 'Section': 'section', 'Elevation': 'elevation',
         'Detail': 'detail', 'DraftingView': 'detail', 'Schedule': 'schedule', 'Legend': 'schedule', 'ThreeD': '3d'}
ORDER = ['sheet', 'plan', 'section', 'elevation', 'detail', 'schedule', '3d']

def safe(s): return re.sub(r'[^A-Za-z0-9._-]+', '_', s).strip('_')[:40]

def label(img, text, h=34):
    cv2.rectangle(img, (0, 0), (img.shape[1], h), (255, 255, 255), -1)
    cv2.putText(img, text, (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2, cv2.LINE_AA); return img

def fit_h(img, h): return cv2.resize(img, (max(1, int(img.shape[1] * h / img.shape[0])), h), interpolation=cv2.INTER_AREA)

def build_pair(svg, png, out_base, title):
    ref_c = cv2.imread(png, cv2.IMREAD_COLOR)
    if ref_c is None: return None
    H, W = ref_c.shape[:2]; long_ = max(H, W)
    g = min(1.0, 2000.0 / long_)                                  # working frame for registration
    ref_w = cv2.cvtColor(cv2.resize(ref_c, (max(1, int(W * g)), max(1, int(H * g))), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY); Hw, Ww = ref_w.shape
    # our aspect-preserving raster inside the working frame
    tmp = out_base + '.tmp.png'
    subprocess.run(['rsvg-convert', '-w', str(max(200, int(Ww * 1.2))), '-b', 'white', svg, '-o', tmp], check=True)
    o = cv2.imread(tmp, cv2.IMREAD_GRAYSCALE); os.remove(tmp); ho, wo = o.shape
    sc0 = min(Ww / wo, Hw / ho); ax, ay = (Ww - wo * sc0) / 2, (Hw - ho * sc0) / 2
    canvas = np.full((Hw, Ww), 255, np.uint8)
    small = cv2.resize(o, (max(1, int(wo * sc0)), max(1, int(ho * sc0))), interpolation=cv2.INTER_AREA); canvas[int(ay):int(ay) + small.shape[0], int(ax):int(ax) + small.shape[1]] = small
    _, (s, dx, dy, score, M) = D.register_search(canvas, ref_w)
    # output scale: native Revit size, upscaled x2/x3 when small, capped
    k = 1 if long_ >= 2400 else min(3, int(math.ceil(2400 / long_)))
    OW, OH = W * k, H * k
    f = s * sc0 / g * k                                           # svg-raster px (width wo at sc0-scale) -> output px
    wr = max(200, int(round(wo / sc0 * f * 1.0 * 1.0)))           # raster width so that scale is exactly f
    wr = int(round(wo * f / sc0 * sc0))                           # = wo*f ; kept explicit for clarity
    wr = max(200, int(round(wo * f)))
    subprocess.run(['rsvg-convert', '-w', str(wr), '-b', 'white', svg, '-o', tmp], check=True)
    r = cv2.imread(tmp, cv2.IMREAD_COLOR); os.remove(tmp)
    # offset of the raster's top-left in the output frame
    ox = (s * ax + (1 - s) * Ww / 2 + dx) / g * k; oy = (s * ay + (1 - s) * Hw / 2 + dy) / g * k
    ours = np.full((OH, OW, 3), 255, np.uint8)
    x0, y0 = int(round(ox)), int(round(oy)); sx0, sy0 = max(0, -x0), max(0, -y0); dx0, dy0 = max(0, x0), max(0, y0)
    ww = min(r.shape[1] - sx0, OW - dx0); hh = min(r.shape[0] - sy0, OH - dy0)
    if ww > 0 and hh > 0: ours[dy0:dy0 + hh, dx0:dx0 + ww] = r[sy0:sy0 + hh, sx0:sx0 + ww]
    revit = cv2.resize(ref_c, (OW, OH), interpolation=cv2.INTER_CUBIC) if k > 1 else ref_c
    # diff heatmap on a bounded frame
    gd = min(1.0, 2400.0 / max(OW, OH)); ga = cv2.cvtColor(cv2.resize(ours, None, fx=gd, fy=gd, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    gb = cv2.cvtColor(cv2.resize(revit, (ga.shape[1], ga.shape[0]), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    A, B = D.ink(ga, 215), D.ink(gb, 215); t = max(2, int(round(max(ga.shape) / 700.0)))
    kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * t + 1, 2 * t + 1)); both = A & cv2.dilate(B, kern) | B & cv2.dilate(A, kern)
    diff = np.full(ga.shape + (3,), 255, np.uint8); diff[(A | B).astype(bool) & both.astype(bool)] = (170, 170, 170)
    diff[(B & (1 - cv2.dilate(A, kern))).astype(bool)] = (200, 160, 0)        # BGR: cyan-ish = Revit only
    diff[(A & (1 - cv2.dilate(B, kern))).astype(bool)] = (40, 40, 230)        # red = ours only
    for suf, im in (('revit', revit), ('ours', ours), ('diff', diff)): cv2.imwrite('%s__%s.png' % (out_base, suf), im, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    hh_ = min(1500, OH); side = np.concatenate([label(fit_h(revit, hh_), 'REVIT  ' + title), np.full((hh_, 12, 3), 90, np.uint8)[:, :, :] if False else np.full((fit_h(revit, hh_).shape[0], 12, 3), 90, np.uint8), label(fit_h(ours, hh_), 'OURS  ' + title)], 1)
    cv2.imwrite(out_base + '__side.png', side, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    th = fit_h(side, 300); cv2.imwrite(out_base + '__thumb.jpg', th, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return dict(reg_score=round(float(score), 3), scale=round(float(s * sc0 / g), 4), k=k, size=[OW, OH], approx=bool(score < 0.35))

def pick(rows, vs, per_type):
    by = {}
    for r in rows:
        v = vs.get(r['id']); 
        if not v or r.get('error') or not r.get('summary'): continue
        if (r.get('ref_ink_px') or 1e9) < 400: continue
        t = TYPES.get(v['vtype'], TYPES.get(v['cls'], 'other')); by.setdefault(t, []).append(r)
    out = []
    for t, n in per_type.items():
        L = sorted(by.get(t, []), key=lambda r: r['id'])
        if not L: continue
        idx = sorted({int(round(i * (len(L) - 1) / max(1, n - 1))) for i in range(n)}) if n > 1 else [0]
        out += [(t, L[i]) for i in idx]
    return out

def main():
    spec = json.load(open(sys.argv[1])); outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True); allm = []
    for sp in spec:
        rd = os.path.expanduser(sp['results']); rvt = os.path.expanduser(sp['rvt']); gd = gt.find_gt(rvt)
        if not gd: print('no gt', rvt); continue
        if not os.path.exists(os.path.join(rd, 'results.jsonl')): print('no results', rd); continue
        vs = gt.views(gd); rows = [json.loads(l) for l in open(os.path.join(rd, 'results.jsonl'))]
        sub = os.path.join(outdir, sp['label']); os.makedirs(sub, exist_ok=True)
        for t, r in pick(rows, vs, sp['per_type']):
            vid = r['id']; v = vs[vid]; svg = os.path.join(rd, 'ours', '%d.svg' % vid); png = os.path.join(gd, '%d.png' % vid)
            if not (os.path.exists(svg) and os.path.exists(png)): continue
            name = '%d_%s_%s' % (vid, safe(v['name']), t); base = os.path.join(sub, name)
            try: m = build_pair(svg, png, base, '%s %s' % (v['name'], vid))
            except Exception as ex: print('fail', vid, repr(ex)[:150]); continue
            if not m: continue
            m.update(file=sp['label'], id=vid, name=v['name'], type=t, vtype=v['vtype'], score=r.get('score'), qa_pass=r.get('pass'), path=sp['label'] + '/' + name)
            json.dump(m, open(base + '.json', 'w')); allm.append(m); print('ok', m['path'], m['reg_score'], flush=True)
    json.dump(allm, open(os.path.join(outdir, 'manifest_%s.json' % os.path.basename(sys.argv[1]).replace('.json', '')), 'w'), indent=1)
if __name__ == "__main__": main()

"""compare_view: our SVG render of a view vs Revit's PNG/DXF export -> ranked findings + crops."""
import os, subprocess, json, math, numpy as np, cv2, re
from . import imgdiff as D, vec

def raster(svg, w, out):
    subprocess.run(['rsvg-convert', '-w', str(w), '-b', 'white', svg, '-o', out], check=True)
    return D.load_gray(out)

def svg_size_mm(svg):
    m = re.search(r'viewBox="([-\d. ]+)"', open(svg).read(2000)); v = [float(x) for x in m.group(1).split()]
    return v[2], v[3]

def crop_pair(ref, warped, box, path, pad=40):
    x0, y0, x1, y1 = [int(v) for v in box]; H, W = ref.shape
    x0, y0, x1, y1 = max(0, x0-pad), max(0, y0-pad), min(W, x1+pad), min(H, y1+pad)
    a = cv2.cvtColor(ref[y0:y1, x0:x1], cv2.COLOR_GRAY2BGR); b = cv2.cvtColor(warped[y0:y1, x0:x1], cv2.COLOR_GRAY2BGR)
    ov = np.dstack([warped[y0:y1, x0:x1], warped[y0:y1, x0:x1], ref[y0:y1, x0:x1]])   # red = Revit only, cyan = ours only
    pair = np.hstack([a, b, ov]); sc = min(1.0, 1800 / pair.shape[1]); 
    if sc < 1: pair = cv2.resize(pair, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
    cv2.imwrite(path, pair)

def compare_view(svg, meta, png, dxf, outdir, vid):
    os.makedirs(outdir, exist_ok=True); res = dict(id=vid, name=meta.get('name'), findings=[]); F = res['findings']
    # ---- tier 1: vector text diff (Revit DXF vs our SVG), numeric
    tx_map = None
    if dxf and os.path.exists(dxf) and meta.get('scale'):
        ref, k = vec.dxf_texts(dxf); ours = vec.svg_texts(open(svg).read())
        S = 304.8 / meta['scale']
        R = [dict(r, x=r['x']*S, y=-r['y']*S, h=r["h"]*S*1.389) for r in ref]   # measured: DXF text height = 1.389 x our SVG font-size (Revit text size vs em)
        sc, tx, ty, nv = vec.vote_registration(ours, R)
        res['text'] = dict(revit=len(ref), ours=len(ours), votes=nv)
        if nv >= 3:
            m, mi, ex = vec.compare_texts(ours, R, sc, tx, ty); tx_map = (tx, ty)
            res['text'].update(matched=len(m), missing=len(mi), extra=len(ex))
            pe = [d for _, _, d in m]; res['text']['pos_err_mm_median'] = round(float(np.median(pe)), 2) if pe else None
            hr = [o['h']/r['h'] for r, o, _ in m if r['h'] > 0 and o['h'] > 0]; res['text']['size_ratio_median'] = round(float(np.median(hr)), 3) if hr else None
            for r in mi: F.append(dict(kind='text-missing', score=1.0 + 0.02*len(r['t']), what=r['t'], layer=r['layer'], at_mm=(round(r['mx'], 1), round(r['my'], 1))))
            for o in ex: F.append(dict(kind='text-extra', score=0.8, what=o['t'], at_mm=(round(o['x'], 1), round(o['y'], 1)), owner=o.get('e')))
            for r, o, d in m:
                if d > 6: F.append(dict(kind='text-moved', score=0.5 + min(d, 60)/60, what=r['t'], dist_mm=round(d, 1), at_mm=(round(o['x'], 1), round(o['y'], 1))))
                rr = o['h']/r['h'] if r['h'] > 0 else 1
                if abs(math.log(max(rr, 1e-3))) > math.log(1.25): F.append(dict(kind='text-size', score=0.4, what=r['t'], ratio=round(rr, 2), at_mm=(round(o['x'], 1), round(o['y'], 1))))
        else: res['text']['note'] = 'registration failed (too few common strings)'
    # ---- tier 2: image diff
    if png and os.path.exists(png):
        ref = D.load_gray(png); H, W = ref.shape
        o = raster(svg, W, os.path.join(outdir, '%s_ours.png' % vid)); o = cv2.resize(o, (W, H), interpolation=cv2.INTER_AREA)
        w, (s, dx, dy, score, M) = D.register_search(o, ref)
        res['image'] = dict(scale=round(float(s), 4), shift_px=(int(dx), int(dy)), reg_score=round(float(score), 3))
        for tol in (3, 6):
            p, r = D.ink_pr(w, ref, tol); res['image']['ink_P%d' % tol] = round(float(p), 3); res['image']['ink_R%d' % tol] = round(float(r), 3)
        a = cv2.GaussianBlur(w, (0, 0), 1.0); b = cv2.GaussianBlur(ref, (0, 0), 1.0)
        res['image']['ssim'] = round(float(D.sk_ssim(a, b, data_range=255)), 4)
        cells, miss, extra = D.heatmap(w, ref, cells=(6, 9), tol=4)
        hm = cv2.applyColorMap(cv2.resize(np.array([[min(1.0, c['miss_frac'] + c['extra_frac']) for c in cells[i*9:(i+1)*9]] for i in range(6)], np.float32)*255, (W//4, H//4), interpolation=cv2.INTER_NEAREST).astype(np.uint8), cv2.COLORMAP_JET)
        cv2.imwrite(os.path.join(outdir, '%s_heat.png' % vid), hm)
        cv2.imwrite(os.path.join(outdir, '%s_overlay.png' % vid), np.dstack([w, w, ref]))
        for c in sorted(cells, key=lambda c: -(c['missing'] + c['extra']))[:8]:
            tot = c['missing'] + c['extra']
            if tot < 150: continue
            kind = 'region-missing' if c['missing'] > 1.5*c['extra'] else 'region-extra' if c['extra'] > 1.5*c['missing'] else 'region-differs'
            F.append(dict(kind=kind, score=min(2.0, tot/4000), box_px=c['box'], missing_px=c['missing'], extra_px=c['extra'], cell=(c['i'], c['j'])))
        # crops for text findings through the same mapping (our mm -> px -> warp)
        sw, sh = svg_size_mm(svg)
        for f in F:
            if 'at_mm' in f:
                x, y = f['at_mm']; px = np.array([x*W/sw, y*H/sh, 1.0]); q = M @ px
                f['box_px'] = (q[0]-60, q[1]-30, q[0]+60, q[1]+30)
    F.sort(key=lambda f: -f['score'])
    for n, f in enumerate(F[:12]):
        if 'box_px' in f and 'image' in res:
            f['crop'] = os.path.join(outdir, '%s_f%02d_%s.png' % (vid, n, f['kind'])); crop_pair(ref, w, f['box_px'], f['crop'])
    # overall verdict
    im = res.get('image', {}); tx = res.get('text', {})
    tr = tx.get('matched', 0) / max(tx.get('revit', 1), 1) if 'matched' in tx else None
    res['summary'] = dict(ssim=im.get('ssim'), ink_P3=im.get('ink_P3'), ink_R3=im.get('ink_R3'), text_recall=round(tr, 3) if tr is not None else None)
    res['pass'] = bool(im.get('ink_R6', 0) >= 0.85 and im.get('ink_P6', 0) >= 0.85 and (tr is None or tr >= 0.9))
    return res

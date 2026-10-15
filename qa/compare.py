"""compare_view: our SVG render of a view vs Revit's PNG/DXF export -> ranked findings + crops."""
import os, subprocess, json, math, numpy as np, cv2, re
from . import imgdiff as D, vec, layers as LY, pdfvec, vecgeom

def raster(svg, w, out):
    if svg.endswith('.png'): return D.load_gray(svg)
    subprocess.run(['rsvg-convert', '-w', str(w), '-b', 'white', svg, '-o', out], check=True)
    return D.load_gray(out)

def svg_size_mm(svg):
    if svg.endswith('.png'):
        h, w = D.load_gray(svg).shape; return float(w), float(h)
    m = re.search(r'viewBox="([-\d. ]+)"', open(svg).read(4000))
    if not m: raise ValueError('our SVG has no viewBox (empty render?)')
    v = [float(x) for x in m.group(1).split()]
    return v[2], v[3]

def crop_pair(ref, warped, box, path, pad=40):
    x0, y0, x1, y1 = [int(v) for v in box]; H, W = ref.shape
    x0, y0, x1, y1 = max(0, x0-pad), max(0, y0-pad), min(W, x1+pad), min(H, y1+pad)
    if x1 - x0 < 8 or y1 - y0 < 8: return False
    a = cv2.cvtColor(ref[y0:y1, x0:x1], cv2.COLOR_GRAY2BGR); b = cv2.cvtColor(warped[y0:y1, x0:x1], cv2.COLOR_GRAY2BGR)
    ov = np.dstack([warped[y0:y1, x0:x1], warped[y0:y1, x0:x1], ref[y0:y1, x0:x1]])   # red = Revit only, cyan = ours only
    pair = np.hstack([a, b, ov]); sc = min(1.0, 1800 / pair.shape[1]); 
    if sc < 1: pair = cv2.resize(pair, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
    cv2.imwrite(path, pair); return True

def compare_view(svg, meta, png, dxf, outdir, vid, pdf=None, is_sheet=False):
    os.makedirs(outdir, exist_ok=True); res = dict(id=vid, name=meta.get('name'), findings=[]); F = res['findings']
    if svg.endswith('.svg') and (lambda t: 'viewBox' not in t or re.search(r'viewBox="[-\d.]+ [-\d.]+ [\d.]+ 0\.0+"', t) is not None)(open(svg).read(4000)):
        F.append(dict(kind='view-not-rendered', score=10.0, what='our render is an empty SVG (view type unsupported?)')); res['summary'] = {}; res['pass'] = False; return res
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
    # ---- tier 1a: vector geometry (DXF primitives vs our SVG paths, paper mm)
    if dxf and os.path.exists(dxf) and meta.get('scale') and not is_sheet and svg.endswith('.svg'):
        try:
            g = vecgeom.compare(open(svg).read(), dxf, meta['scale'])
            if g:
                res['geom'] = {k: v for k, v in g.items() if k not in ('layers', 'extra_elements')}; res['geom_layers'] = g['layers']; res['geom_extra_elements'] = g['extra_elements']
                for r in g['layers'][:8]:
                    if r['recall'] < 0.7 and r['len_mm'] > 40: F.append(dict(kind='geom-layer-missing', score=0.9 + (1 - r['recall']), what=r['layer'], recall=r['recall'], len_mm=r['len_mm'], **({'at_mm': r['at_mm']} if r.get('at_mm') else {})))
                for r in g['extra_elements'][:6]:
                    if r['extra_mm'] > 30: F.append(dict(kind='geom-extra-element', score=0.7 + min(r['extra_mm'], 400) / 400, what='element %s' % r['element'], extra_mm=r['extra_mm'], of_mm=r['of_mm'], **({'at_mm': r['at_mm']} if r.get('at_mm') else {})))
        except Exception as ex: res['geom_note'] = repr(ex)[:150]
    # ---- tier 1b: sheet PDF (paper units): text content/size/position + line-weight inventory
    if pdf and is_sheet and os.path.exists(pdf) and svg.endswith('.svg'):
        try:
            st = open(svg).read(); items = vec.svg_texts(st)
            ref, m, mi, ex, pg = pdfvec.compare(st, items, pdf)
            res['pdf_text'] = dict(revit=len(ref), ours=len(items), matched=len(m), missing=len(mi), extra=len(ex))
            for r in mi: F.append(dict(kind='text-missing', score=1.0 + 0.02 * len(r['t']), what=r['t'], font=r['font'], at_mm=(round(r['x'], 1), round(r['y'], 1))))
            for o in ex: F.append(dict(kind='text-extra', score=0.8, what=o['t'], at_mm=(round(o['x'], 1), round(o['y'], 1))))
            for r, o, d in m:
                if d > 3: F.append(dict(kind='text-moved', score=0.5 + min(d, 60) / 60, what=r['t'], dist_mm=round(d, 1), at_mm=(round(o['x'], 1), round(o['y'], 1))))
                rr = o['h'] / r['h'] if r['h'] > 0 else 1
                if o['h'] > 0 and abs(math.log(max(rr, 1e-3))) > math.log(1.15): F.append(dict(kind='text-size', score=0.45, what=r['t'], ratio=round(rr, 2), revit_pt=round(r['h'] / pdfvec.PT, 1), at_mm=(round(o['x'], 1), round(o['y'], 1))))
            wp, ws = pdfvec.pdf_weights(pdf), pdfvec.svg_weights(st)
            res['weights_mm'] = dict(revit={str(k): round(v) for k, v in sorted(wp.items())}, ours={str(k): round(v) for k, v in sorted(ws.items())})
            for k, v in wp.items():
                near = [vv for kk, vv in ws.items() if abs(kk - k) <= 0.04]
                if v > 300 and sum(near) < 0.5 * v: F.append(dict(kind='lineweight-missing', score=0.9, weight_mm=k, revit_len_mm=round(v), ours_len_mm=round(sum(near))))
        except Exception as ex: res['pdf_note'] = repr(ex)[:150]
    # ---- tier 2: image diff
    if png and os.path.exists(png):
        ref = D.load_gray(png); H, W = ref.shape
        if max(H, W) > 2200:    # work at reduced size: tall sections can be 3000x11000 px
            f = 2200.0 / max(H, W); ref = cv2.resize(ref, (max(1, int(W*f)), max(1, int(H*f))), interpolation=cv2.INTER_AREA); H, W = ref.shape
        o = raster(svg, W, os.path.join(outdir, '%s_ours.png' % vid)); o = cv2.resize(o, (W, H), interpolation=cv2.INTER_AREA)
        w, (s, dx, dy, score, M) = D.register_search(o, ref)
        res['ref_ink_px'] = int(D.ink(ref).sum())
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
        if dxf and os.path.exists(dxf):
            try:
                lyr = LY.layer_recall(dxf, w)
                if lyr and lyr['reg_score'] >= 0.3:
                    res['layers'] = lyr['layers'][:25]
                    for r in lyr['layers'][:6]:
                        if r['recall'] < 0.6 and r['ink_px'] > 400: F.append(dict(kind='layer-missing', score=0.8 + (1 - r['recall']), what=r['layer'], recall=r['recall'], ink_px=r['ink_px']))
                else: res['layers_note'] = 'dxf raster registration unreliable'
            except Exception as ex: res['layers_note'] = repr(ex)[:120]
        lr, lo = D.long_lines(ref, 0.2), D.long_lines(w, 0.2)
        pairs, lmiss, lextra = D.match_lines(lo, lr, tol=10)
        res['lines'] = dict(revit=len(lr), ours=len(lo), matched=len(pairs), missing=len(lmiss), extra=len(lextra))
        for sg in lmiss: F.append(dict(kind='longline-missing', score=1.2, box_px=(min(sg[0], sg[2]), min(sg[1], sg[3]), max(sg[0], sg[2]), max(sg[1], sg[3])), seg_px=sg))
        for sg in lextra: F.append(dict(kind='longline-extra', score=1.0, box_px=(min(sg[0], sg[2]), min(sg[1], sg[3]), max(sg[0], sg[2]), max(sg[1], sg[3])), seg_px=sg))
        for i, j, d, dl in pairs:
            if abs(dl) > 0.15*max(1.0, math.hypot(lr[j][2]-lr[j][0], lr[j][3]-lr[j][1])):
                F.append(dict(kind='longline-extent', score=0.9, length_diff_px=round(float(dl)), box_px=(min(lr[j][0], lr[j][2]), min(lr[j][1], lr[j][3]), max(lr[j][0], lr[j][2]), max(lr[j][1], lr[j][3]))))
        br, bo = D.line_end_bubbles(ref, lr), D.line_end_bubbles(w, lo)
        bp, bmiss, bextra = D.match_pts(bo, br, tol=18)
        res['bubbles'] = dict(revit=len(br), ours=len(bo), matched=len(bp), missing=len(bmiss), extra=len(bextra))
        for x, y, r in bmiss: F.append(dict(kind='bubble-missing', score=1.1, box_px=(x-30, y-30, x+30, y+30)))
        for x, y, r in bextra: F.append(dict(kind='bubble-extra', score=0.9, box_px=(x-30, y-30, x+30, y+30)))
        # crops for text findings through the same mapping (our mm -> px -> warp)
        sw, sh = svg_size_mm(svg)
        for f in F:
            if 'at_mm' in f:
                x, y = f['at_mm']; px = np.array([x*W/sw, y*H/sh, 1.0]); q = M @ px
                f['box_px'] = (q[0]-60, q[1]-30, q[0]+60, q[1]+30)
    F.sort(key=lambda f: -f['score'])
    for n, f in enumerate(F[:12]):
        if 'box_px' in f and 'image' in res:
            f['crop'] = os.path.join(outdir, '%s_f%02d_%s.png' % (vid, n, f['kind']))
            if not crop_pair(ref, w, f['box_px'], f['crop']): del f['crop']
    # overall verdict
    im = res.get('image', {}); tx = res.get('text', {})
    tr = tx.get('matched', 0) / max(tx.get('revit', 1), 1) if 'matched' in tx else None
    res['summary'] = dict(ssim=im.get('ssim'), ink_P3=im.get('ink_P3'), ink_R3=im.get('ink_R3'), text_recall=round(tr, 3) if tr is not None else None)
    # combined 0-100 score (weights renormalised over the tiers available)
    parts = []
    if im: parts += [(0.30, im.get('ink_R6', 0)), (0.20, im.get('ink_P6', 0))]
    if tr is not None: parts.append((0.25, tr))
    if res.get('lines') and res['lines']['revit']: parts.append((0.10, res['lines']['matched'] / res['lines']['revit']))
    if res.get('layers'):
        tot = sum(x['ink_px'] for x in res['layers']); parts.append((0.15, sum(x['ink_px'] * x['recall'] for x in res['layers']) / max(tot, 1)))
    res['score'] = round(100 * sum(w * v for w, v in parts) / sum(w for w, _ in parts), 1) if parts else None
    for f in F:   # owner hint so findings can be routed without anyone looking at pixels
        k = f['kind']; w = str(f.get('what', ''))
        f['area'] = ('annotations/text' if k.startswith('text') else 'grids' if k.startswith(('longline', 'bubble')) or 'GRID' in w else
                     'line weights' if k.startswith('lineweight') else 'view not rendered' if k in ('view-not-rendered', 'registration-unreliable') else
                     'layer ' + w if k in ('layer-missing', 'geom-layer-missing') else ('extra drawn ' + w) if k == 'geom-extra-element' else 'drawing content')
    res['reliable'] = bool(im.get('reg_score', 0) >= 0.35)
    if not res['reliable']: res['findings'].insert(0, dict(kind='registration-unreliable', score=9.0, reg_score=im.get('reg_score'), note='image metrics not trustworthy (3D shaded export / detail view); rely on text findings'))
    if res.get('ref_ink_px', 1e9) < 400: res['findings'].insert(0, dict(kind='trivial-view', score=0.1, note='Revit export has almost no ink; pass/fail is vacuous'))
    res['pass'] = bool(im.get('ink_R6', 0) >= 0.85 and im.get('ink_P6', 0) >= 0.85 and (tr is None or tr >= 0.9))
    return res

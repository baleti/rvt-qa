"""Revit PDF (vector) vs our SVG for SHEETS (page = paper, 1 pt = 0.3528 mm): text spans (content, size, font, position) and line weights (stroke length per weight class)."""
import re, math, collections, html
import numpy as np
PT = 25.4 / 72

def pdf_texts(fn):
    import pymupdf
    d = pymupdf.open(fn); p = d[0]; out = []
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                t = s['text'].strip()
                if not t: continue
                x0, y0, x1, y1 = [v * PT for v in s['bbox']]
                out.append(dict(t=t, x=x0, y=y1 - 0.212 * s['size'] * PT, cx=(x0 + x1) / 2, cy=(y0 + y1) / 2, h=s['size'] * PT, font=s['font'], w=x1 - x0, x1=x1))
    return out, (p.rect.width * PT, p.rect.height * PT)

def pdf_weights(fn):
    import pymupdf
    p = pymupdf.open(fn)[0]; acc = collections.Counter()
    for dr in p.get_drawings():
        w = dr.get('width')
        if not w or dr.get('color') is None: continue
        L = 0.0
        for it in dr['items']:
            if it[0] == 'l': L += math.hypot(it[2].x - it[1].x, it[2].y - it[1].y)
            elif it[0] == 're': r = it[1]; L += 2 * (r.width + r.height)
            elif it[0] == 'c': L += math.hypot(it[4].x - it[1].x, it[4].y - it[1].y)
            elif it[0] == 'qu': q = it[1]; L += math.hypot(q.ur.x - q.ul.x, q.ur.y - q.ul.y) * 2
        acc[round(w * PT, 2)] += L * PT
    return acc

def svg_weights(svg):
    acc = collections.Counter()
    for m in re.finditer(r'<(?:path|polyline|line)\b([^>]*)>', svg):
        a = m.group(1); sw = re.search(r'stroke-width="([\d.]+)"', a)
        if not sw or re.search(r'stroke="none"', a): continue
        d = re.search(r' d="([^"]*)"', a); pts = re.search(r'points="([^"]*)"', a)
        nums = [float(v) for v in re.findall(r'-?\d+\.?\d*(?:e-?\d+)?', (d or pts).group(1))] if (d or pts) else []
        if not nums: continue
        P = list(zip(nums[0::2], nums[1::2])); L = sum(math.hypot(b[0] - a_[0], b[1] - a_[1]) for a_, b in zip(P[:-1], P[1:]))
        acc[round(float(sw.group(1)), 2)] += L
    return acc

def compare(svg_text, svg_items, pdf, tol=8.0):
    ref, (pw, ph) = pdf_texts(pdf)
    used = set(); matched = []; missing = []
    from .vec import norm
    for r in ref:
        best = None
        for i, o in enumerate(svg_items):
            if i in used or norm(o['t']) != norm(r['t']): continue
            rx = r['x'] if o.get('anchor', 'start') == 'start' else (r['cx'] if o['anchor'] == 'middle' else r['x1'])   # compare at the anchor the SVG uses
            d = math.hypot(o['x'] - rx, o['y'] - r['y'])
            if best is None or d < best[0]: best = (d, i)
        if best and best[0] <= 60: used.add(best[1]); matched.append((r, svg_items[best[1]], best[0]))
        else: missing.append(r)
    extra = [o for i, o in enumerate(svg_items) if i not in used]
    return ref, matched, missing, extra, (pw, ph)

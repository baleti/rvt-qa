"""Vector-level semantic diff: text items (content, position, height, rotation) of Revit's DXF vs our SVG, registered by voting on identical strings."""
import math, re, math, collections, html
import numpy as np

def dxf_texts(fn):
    import ezdxf
    doc = ezdxf.readfile(fn); u = doc.header.get('$INSUNITS', 0)
    k = {1: 1/12, 2: 1.0, 4: 1/304.8, 5: 1/30.48, 6: 1/0.3048}.get(u, 1.0)   # to feet
    out = []
    def clean(s): return re.sub(r'\\[A-Za-z][^;]*;|[{}]', '', s).replace('\\P', ' ').replace('%%d', '°').replace('%%p', '±').strip()
    def walk(ents):
        for e in ents:
            t = e.dxftype()
            if t == 'INSERT':
                try: walk(e.virtual_entities())
                except Exception: pass
            elif t in ('TEXT', 'MTEXT'):
                try:
                    if t == 'TEXT': s = e.dxf.text; p = e.dxf.insert; h = e.dxf.height; rot = e.dxf.get('rotation', 0)
                    else: s = e.plain_text() if hasattr(e, 'plain_text') else e.text; p = e.dxf.insert; h = e.dxf.char_height; rot = e.dxf.get('rotation', 0)
                    if t == 'MTEXT' and not rot and e.dxf.hasattr('text_direction'): td = e.dxf.text_direction; rot = math.degrees(math.atan2(td.y, td.x))   # MTEXT rotation is a direction vector
                    s = clean(s)
                    if s: out.append(dict(t=s, x=p.x*k, y=p.y*k, h=h*k, rot=float(rot) % 360, layer=e.dxf.layer))
                except Exception: pass
    walk(doc.modelspace())
    return out, k

_tr = re.compile(r'<text\s+([^>]*)>(.*?)</text>', re.S)
def svg_texts(svg):
    """texts of our SVG in paper mm: (x, y, size, rot, content, owner element id)"""
    out = []
    for m in _tr.finditer(svg):
        a, body = m.group(1), m.group(2)
        tm = re.search(r'translate\(([-\d.e]+)[ ,]([-\d.e]+)\)', a); rm = re.search(r'rotate\(([-\d.e]+)', a)
        sm = re.search(r'font-size="([-\d.e]+)"', a); em = re.search(r'data-e="(\d+)"', a); an = re.search(r'text-anchor="(\w+)"', a)
        if not tm: continue
        h = float(sm.group(1)) if sm else 0; rr = float(rm.group(1)) if rm else 0
        tsp = re.findall(r'<tspan([^>]*)>(.*?)</tspan>', body, re.S)
        if len(tsp) > 1 and all('dy="' in ta for ta, _ in tsp):     # wrapped text: Revit exports one MTEXT per line, so match per line
            cy = 0.0; c, sn = math.cos(math.radians(rr)), math.sin(math.radians(rr))
            for ta, tb in tsp:
                cy += float(re.search(r'dy="([-\d.e]+)"', ta).group(1)); st = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", tb)).split())
                if st: out.append(dict(t=st, x=float(tm.group(1)) - cy * sn, y=float(tm.group(2)) + cy * c, h=h, rot=(-rr) % 360, e=em.group(1) if em else None, anchor=an.group(1) if an else 'start'))
            continue
        s = html.unescape(re.sub(r"<[^>]+>", " ", body)); s = " ".join(s.split())
        if not s: continue
        out.append(dict(t=s, x=float(tm.group(1)), y=float(tm.group(2)), h=float(sm.group(1)) if sm else 0, rot=(-float(rm.group(1))) % 360 if rm else 0, e=em.group(1) if em else None, anchor=an.group(1) if an else 'start'))
    return out

def norm(s): return re.sub(r'\s+', '', s).lower()

def vote_registration(ours, ref, tol=2.0, cands=None):
    """find translation (and scale from candidates) mapping ref -> ours coordinates by voting over identical strings. Returns (scale, tx, ty, nvotes)."""
    by = collections.defaultdict(list)
    for o in ours: by[norm(o['t'])].append(o)
    best = (None, 0, 0, 0)
    for sc in cands or [1.0]:
        votes = collections.Counter(); pts = {}
        for r in ref:
            os_ = by.get(norm(r['t']), [])
            if not os_ or len(os_) > 6: continue
            for o in os_:
                key = (round((o['x'] - sc*r['x']) / tol), round((o['y'] - sc*r['y']) / tol)); votes[key] += 1; pts.setdefault(key, []).append((o['x'] - sc*r['x'], o['y'] - sc*r['y']))
        if votes:
            key, n = votes.most_common(1)[0]
            if n > best[3]:
                a = np.array(pts[key]); best = (sc, float(np.median(a[:, 0])), float(np.median(a[:, 1])), n)
    return best

def left_edge(o):
    """SVG text x is at its anchor; DXF insert is the left edge: convert using an estimated advance width (0.5 em per char)"""
    w = 0.5 * o.get('h', 0) * len(o['t'])
    a = o.get('anchor', 'start')
    return o['x'] - (w if a == 'end' else w / 2 if a == 'middle' else 0)

def left_edge_xy(o):
    """left_edge along the text baseline for rotated text (rot is counter-clockwise in o)"""
    w = 0.5 * o.get('h', 0) * len(o['t']); a = o.get('anchor', 'start')
    sh = w if a == 'end' else w / 2 if a == 'middle' else 0
    rr = math.radians(-o.get('rot', 0))
    return o['x'] - sh * math.cos(rr), o['y'] - sh * math.sin(rr)

def compare_texts(ours, ref, sc, tx, ty, ptol=2.0, refine=2):
    """match, then re-centre the registration on the median residual of the matches (votes on repeated tags can lock onto a neighbouring copy) and match again"""
    for _ in range(refine + 1):
        res = _compare_texts(ours, ref, sc, tx, ty, ptol)
        if _ >= refine or len(res[0]) < 5: break
        dx = np.median([left_edge_xy(o)[0] - (sc * r['x'] + tx) for r, o, d in res[0]]); dy = np.median([left_edge_xy(o)[1] - (sc * r['y'] + ty) for r, o, d in res[0]])
        if math.hypot(dx, dy) < 0.5: break
        tx += dx; ty += dy
    compare_texts.last = (tx, ty)
    return res

def _compare_texts(ours, ref, sc, tx, ty, ptol=2.0):
    """ref positions mapped into our frame; greedy match by identical normalised text (or ref text contained in ours: DXF splits multi-word comments into several MTEXT) and nearest position, comparing at the left edge"""
    used = set(); matched = []; missing = []
    for r in ref:
        rx, ry = sc*r['x'] + tx, sc*r['y'] + ty; nr = norm(r['t'])
        best = None
        for i, o in enumerate(ours):
            no = norm(o['t'])
            if no != nr and not (len(nr) >= 2 and nr in no): continue
            if i in used and no == nr: continue
            lx, ly = left_edge_xy(o); d = math.hypot(lx - rx, ly - ry)
            if no != nr: d += 0.5          # prefer exact matches
            if best is None or d < best[0]: best = (d, i)
        if best and best[0] <= 40:
            if norm(ours[best[1]]['t']) == nr: used.add(best[1])
            matched.append((r, ours[best[1]], best[0]))
        else: missing.append(dict(r, mx=rx, my=ry))
    # a container text counts as used once it explained a part
    used |= {i for i, o in enumerate(ours) if any(m[1] is o for m in matched)}
    extra = [o for i, o in enumerate(ours) if i not in used]
    return matched, missing, extra

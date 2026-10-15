"""Per-Revit-layer ink recall: rasterise the view's DXF layers, register the raster to our (already aligned) render, report which layers we miss."""
import numpy as np, cv2
from . import imgdiff as D

def dxf_layers(fn):
    import ezdxf
    from ezdxf import path as zpath
    doc = ezdxf.readfile(fn); out = {}
    def walk(ents):
        for e in ents:
            t = e.dxftype()
            if t == 'INSERT':
                try: walk(e.virtual_entities())
                except Exception: pass
            elif t in ('LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC', 'CIRCLE', 'ELLIPSE', 'SPLINE'):
                try:
                    p = zpath.make_path(e); pts = np.array([[v.x, v.y] for v in p.flattening(0.02)])
                    if len(pts) >= 2: out.setdefault(e.dxf.layer, []).append(pts)
                except Exception: pass
    walk(doc.modelspace()); return out

def raster_layers(layers, H, W, margin=0.04):
    allp = np.concatenate([p for ps in layers.values() for p in ps]); lo = allp.min(0); hi = allp.max(0)
    span = np.maximum(hi - lo, 1e-6); s = min((W*(1-2*margin))/span[0], (H*(1-2*margin))/span[1])
    def mk(ps):
        im = np.full((H, W), 255, np.uint8)
        for p in ps:
            q = np.stack([(p[:, 0]-lo[0])*s + W*margin, H - ((p[:, 1]-lo[1])*s + H*margin)], 1).astype(np.int32)
            cv2.polylines(im, [q.reshape(-1, 1, 2)], False, 0, 1, cv2.LINE_8)
        return im
    return {k: mk(v) for k, v in layers.items()}, mk([p for ps in layers.values() for p in ps])

def layer_recall(dxf, ours_warped, tol=4):
    H, W = ours_warped.shape
    layers = dxf_layers(dxf)
    if not layers: return None
    per, allr = raster_layers(layers, H, W)
    _, (s, dx, dy, score, M) = D.register_search(allr, ours_warped)   # DXF raster -> our frame
    A = D.ink(ours_warped); dist = cv2.distanceTransform(1 - A, cv2.DIST_L2, 3); k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*tol+1, 2*tol+1)); Ad = cv2.dilate(A, k)
    rows = []
    for name, im in per.items():
        w = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_NEAREST, borderValue=255)
        B = D.ink(w, 128); n = int(B.sum())
        if n < 30: continue
        dd = dist[B > 0]
        rows.append(dict(layer=name, ink_px=n, recall=round(float((B & Ad).sum()) / n, 3), chamfer_px=round(float(dd.mean()), 1), hausdorff95_px=round(float(np.percentile(dd, 95)), 1)))
    rows.sort(key=lambda r: -r['ink_px'] * (1 - r['recall']))
    return dict(reg_score=round(float(score), 3), layers=rows)

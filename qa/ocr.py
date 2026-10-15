import cv2, numpy as np, pytesseract, re
def words(g, scale=2.0, conf=45):
    """OCR words with boxes in the input pixel frame. Handles rotated text by trying 0/90/270."""
    out = []
    for rot in (0, 90, 270):
        im = g if rot == 0 else cv2.rotate(g, cv2.ROTATE_90_CLOCKWISE if rot == 90 else cv2.ROTATE_90_COUNTERCLOCKWISE)
        im2 = cv2.resize(im, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        d = pytesseract.image_to_data(im2, config='--psm 11 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-@/()', output_type=pytesseract.Output.DICT)
        H, W = im.shape
        for t, c, x, y, w, h in zip(d['text'], d['conf'], d['left'], d['top'], d['width'], d['height']):
            t = t.strip()
            if not t or float(c) < conf or len(t) < 2: continue
            x, y, w, h = x/scale, y/scale, w/scale, h/scale
            if rot == 90: x, y, w, h = y, H - x - w, h, w
            elif rot == 270: x, y, w, h = W - y - h, x, h, w
            out.append(dict(t=t, x=x+w/2, y=y+h/2, w=w, h=h, rot=rot, conf=float(c)))
    # dedupe rotations: keep highest-conf at same place
    out.sort(key=lambda d: -d['conf']); keep = []
    for d in out:
        if all(abs(d['x']-k['x']) > 6 or abs(d['y']-k['y']) > 6 for k in keep): keep.append(d)
    return keep
def compare(ours, ref, tol=25):
    used = set(); matched = []; missing = []
    for r in ref:
        best = None
        for i, o in enumerate(ours):
            if i in used or o['t'] != r['t']: continue
            d = np.hypot(o['x']-r['x'], o['y']-r['y'])
            if d <= tol and (best is None or d < best[0]): best = (d, i)
        if best: used.add(best[1]); matched.append((r, ours[best[1]], best[0]))
        else: missing.append(r)
    extra = [o for i, o in enumerate(ours) if i not in used]
    return matched, missing, extra

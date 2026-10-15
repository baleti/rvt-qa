"""bench_ocr.py OURS.svg WIDTH engine... : OCR our own render (ground truth = the SVG's text items) -> recall of ground-truth words found at the right place + time. engines: tess easyocr doctr"""
import sys, time, re, subprocess, math, os
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from qa import vec
svg, W = sys.argv[1], int(sys.argv[2]); engines = sys.argv[3:]
ROT = [90, 270] if os.environ.get('ROT') else None
png = '/tmp/claude-1000/ocrbench_%d.png' % W
subprocess.run(['rsvg-convert', '-w', str(W), '-b', 'white', svg, '-o', png], check=True)
img = cv2.imread(png); H = img.shape[0]
m = re.search(r'viewBox="[-\d. ]* ([\d.]+) ([\d.]+)"', open(svg).read(4000)); sw = float(m.group(1)); k = W / sw
gt = []
for t in vec.svg_texts(open(svg).read()):
    for w in t['t'].split():
        if len(w) >= 2 and t['h'] * k >= 5: gt.append((vec.norm(w), t['x'] * k, t['y'] * k, t['h'] * k))   # skip glyphs < 5 px tall
print('gt words', len(gt), 'image', img.shape[:2])
def score(name, words, secs):
    used = set(); hit = 0
    for w, x, y, h in gt:
        for i, (t, cx, cy) in enumerate(words):
            if i in used: continue
            if (vec.norm(t) == w or (len(w) > 3 and w in vec.norm(t))) and math.hypot(cx - x, cy - y) < max(40, 6 * h): used.add(i); hit += 1; break
    print('%-8s %5.1fs words %4d  GT recall %.3f  precision(words matched/all) %.3f' % (name, secs, len(words), hit / max(len(gt), 1), len(used) / max(len(words), 1)), flush=True)
for e in engines:
    t = time.time()
    if e == 'tess':
        import pytesseract
        d = pytesseract.image_to_data(img, config='--psm 11', output_type=pytesseract.Output.DICT)
        words = [(a, x + w / 2, y + h / 2) for a, c, x, y, w, h in zip(d['text'], d['conf'], d['left'], d['top'], d['width'], d['height']) if a.strip() and float(c) > 30]
    elif e == 'easyocr':
        import easyocr, torch; torch.set_num_threads(4)
        r = easyocr.Reader(['en'], gpu=False, verbose=False); words = []
        for box, tx, c in r.readtext(img, paragraph=False, rotation_info=ROT):
            for w_ in tx.split(): words.append((w_, float(np.mean([p[0] for p in box])), float(np.mean([p[1] for p in box]))))
    elif e == 'doctr':
        from doctr.models import ocr_predictor; import torch; torch.set_num_threads(4)
        pr = ocr_predictor(pretrained=True); res = pr([cv2.cvtColor(img, cv2.COLOR_BGR2RGB)]); words = []
        for pg in res.pages:
            for b in pg.blocks:
                for l in b.lines:
                    for w_ in l.words: (x0, y0), (x1, y1) = w_.geometry; words.append((w_.value, (x0 + x1) / 2 * img.shape[1], (y0 + y1) / 2 * H))
    score(e, words, time.time() - t)

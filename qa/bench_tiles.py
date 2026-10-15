"""bench_tiles.py OVERLAY.png : per-tile (6x9) difference scores from several methods on an aligned pair (overlay = BGR [ours, ours, revit]); reports time and Spearman correlation with the ink-diff tile score (missing+extra px)."""
import sys, time, numpy as np, cv2, json
from scipy.stats import spearmanr
ov = cv2.imread(sys.argv[1]); ours = ov[:, :, 0]; ref = ov[:, :, 2]; H, W = ref.shape; R, C = 6, 9
def tiles(fn):
    out = np.zeros((R, C)); 
    for i in range(R):
        for j in range(C):
            sl = (slice(i*H//R, (i+1)*H//R), slice(j*W//C, (j+1)*W//C)); out[i, j] = fn(ours[sl], ref[sl])
    return out
res = {}
# ground tile score: ink diff
A = (ours < 200).astype(np.uint8); B = (ref < 200).astype(np.uint8); k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
d = (B & (1 - cv2.dilate(A, k))) + (A & (1 - cv2.dilate(B, k)))
gt = np.array([[d[i*H//R:(i+1)*H//R, j*W//C:(j+1)*W//C].sum() for j in range(C)] for i in range(R)], float)
def run(name, fn):
    t = time.time(); s = fn(); res[name] = dict(secs=round(time.time()-t, 2), spearman=round(float(spearmanr(s.ravel(), gt.ravel())[0]), 3)); print(name, res[name], flush=True)
from skimage.metrics import structural_similarity as ssim
run('ssim', lambda: 1 - tiles(lambda a, b: ssim(a, b, data_range=255)))
def msssim(a, b):
    v = []; 
    for s in range(3):
        if min(a.shape) < 16: break
        v.append(ssim(a, b, data_range=255, win_size=7)); a = cv2.pyrDown(a); b = cv2.pyrDown(b)
    return 1 - float(np.prod(np.clip(v, 1e-3, 1)) ** (1 / len(v)))
run('ms-ssim', lambda: tiles(msssim))
def edge_chamfer(a, b):
    ea = cv2.Canny(a, 50, 150); eb = cv2.Canny(b, 50, 150)
    if ea.sum() == 0 or eb.sum() == 0: return 0.0 if ea.sum() == eb.sum() else 20.0
    da = cv2.distanceTransform(255 - ea, cv2.DIST_L2, 3); db = cv2.distanceTransform(255 - eb, cv2.DIST_L2, 3)
    return float(min(20, da[eb > 0].mean()) + min(20, db[ea > 0].mean()))
run('edge-chamfer', lambda: tiles(edge_chamfer))
import torch; torch.set_num_threads(4)
try:
    import lpips
    net = lpips.LPIPS(net='alex', verbose=False).eval()
    def lp(a, b):
        f = lambda x: torch.from_numpy(cv2.resize(x, (128, 128), interpolation=cv2.INTER_AREA)).float().div(127.5).sub(1)[None, None].repeat(1, 3, 1, 1)
        with torch.no_grad(): return float(net(f(a), f(b)))
    run('lpips-alex', lambda: tiles(lp))
except Exception as ex: print('lpips fail', repr(ex)[:200])
try:
    from transformers import AutoImageProcessor, AutoModel
    proc = AutoImageProcessor.from_pretrained('facebook/dinov2-small'); m = AutoModel.from_pretrained('facebook/dinov2-small').eval()
    def emb(x):
        im = cv2.cvtColor(cv2.resize(x, (224, 224), interpolation=cv2.INTER_AREA), cv2.COLOR_GRAY2RGB)
        with torch.no_grad(): o = m(**proc(images=im, return_tensors='pt', do_resize=False, do_center_crop=False)).last_hidden_state[0, 0]
        return o / o.norm()
    run('dinov2-small-cls', lambda: tiles(lambda a, b: 1 - float(emb(a) @ emb(b))))
except Exception as ex: print('dino fail', repr(ex)[:200])
try:
    import open_clip
except Exception: pass
json.dump(res, open(sys.argv[1] + '.bench.json', 'w'))

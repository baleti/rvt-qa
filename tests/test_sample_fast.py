import os, sys, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qa import vecgeom as V

def ref_sample(polys, step=0.25):
    pts, lab = [], []
    for l, *rest in polys:
        P = rest[-1]
        for a, b in zip(P[:-1], P[1:]):
            n = max(1, int(np.hypot(*(b - a)) / step)); t = (np.arange(n) + 0.5) / n
            pts.append(a + (b - a) * t[:, None]); lab += [l] * n
    return (np.concatenate(pts) if pts else np.zeros((0, 2))), np.array(lab)

def polys(n, seed=0):
    rng = np.random.default_rng(seed); out = []
    for i in range(n):
        k = int(rng.integers(1, 7)); P = np.cumsum(rng.normal(0, 3, (k, 2)), 0) + rng.uniform(0, 300, 2)
        if k > 2 and i % 7 == 0: P[1] = P[0]            # zero-length segment
        out.append(('L%d' % (i % 5), i, P))
    return out

def test_matches_reference():
    p = polys(300); A, la = V.sample(p); B, lb = ref_sample(p)
    assert A.shape == B.shape and np.abs(A - B).max() < 1e-9 and list(la) == list(lb)

def test_edge_cases():
    A, la = V.sample([]); assert A.shape == (0, 2) and len(la) == 0
    A, la = V.sample([('x', np.array([[1.0, 2.0]]))]); assert A.shape == (0, 2)
    A, la = V.sample([('x', np.array([[0.0, 0.0], [0.0, 0.0]]))]); assert A.shape == (1, 2) and list(la) == ['x']
    A, la = V.sample([('x', 'tag', np.array([[0.0, 0.0], [1.0, 0.0]]))], step=0.5); assert np.allclose(A, [[0.25, 0], [0.75, 0]])

def test_speed():
    p = polys(60000, 1); fast = slow = 1e9
    for _ in range(3):    # best of 3: single timings flap under load or after other tests warm threads
        t = time.time(); V.sample(p); fast = min(fast, time.time() - t)
        t = time.time(); ref_sample(p); slow = min(slow, time.time() - t)
    assert fast < slow / 4, (fast, slow)

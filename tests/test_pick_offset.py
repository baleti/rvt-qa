import numpy as np, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qa import vecgeom as V

def seg(a, b, step=0.25):
    a, b = np.array(a, float), np.array(b, float); n = max(1, int(np.hypot(*(b - a)) / step))
    t = (np.arange(n) + 0.5) / n; return a + (b - a) * t[:, None]

def scene():
    walls = np.concatenate([seg((0, 0), (200, 0)), seg((0, 0), (0, 80)), seg((200, 0), (200, 50)), seg((60, 0), (60, 80)), seg((0, 80), (120, 80))])
    hatch = np.concatenate([seg((x, 0), (x, 80)) for x in np.arange(0, 200, 8.0)])   # periodic: period 8 mm
    return walls, hatch

def test_picks_true_shift_despite_periodic_hatch():
    walls, hatch = scene()
    B = np.concatenate([walls])                  # reference: walls only
    shift = np.array([37.0, 11.0])
    A = np.concatenate([walls + shift, hatch + shift])   # ours: walls + many hatch lines
    off = V.pick_offset(A, B, tol_mm=0.6)        # B + off ~ A
    assert np.hypot(*(off - shift)) < 0.6

def test_identity():
    walls, hatch = scene()
    off = V.pick_offset(walls, walls)
    assert np.hypot(*off) < 0.6

def test_compare_unchanged_signature():
    import inspect
    assert list(inspect.signature(V.pick_offset).parameters) == ['A', 'B', 'tol_mm', 'k']

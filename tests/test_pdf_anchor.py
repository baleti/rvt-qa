import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qa import pdfvec as P

def test_horizontal():
    r = dict(x=10.0, cx=15.0, x1=20.0, y=5.0)
    assert P.anchor_point(r, 'start') == (10.0, 5.0)
    assert P.anchor_point(r, 'middle') == (15.0, 5.0)
    assert P.anchor_point(r, 'end') == (20.0, 5.0)
    assert P.anchor_point(r) == (10.0, 5.0)

def test_rotated():
    r = dict(x=1.0, cx=2.0, x1=3.0, y=4.0, rot_pts={'start': (9.0, 9.0), 'middle': (9.0, 5.0), 'end': (9.0, 1.0)})
    assert P.anchor_point(r, 'middle') == (9.0, 5.0)
    assert P.anchor_point(r, 'end') == (9.0, 1.0)

def test_real_rotated_pdf(tmp_path):
    import pymupdf
    d = pymupdf.open(); pg = d.new_page(width=200, height=200)
    pg.insert_text((100, 150), 'ABCDEFGH', fontsize=10, rotate=90)
    fn = str(tmp_path / 't.pdf'); d.save(fn)
    items, _ = P.pdf_texts(fn)
    assert items and 'rot_pts' in items[0]
    s, m, e = (P.anchor_point(items[0], a) for a in ('start', 'middle', 'end'))
    assert abs(s[0] - m[0]) < 0.5 and abs(m[0] - e[0]) < 0.5       # vertical text: x constant
    assert abs((s[1] - e[1])) > 5 and abs((s[1] + e[1]) / 2 - m[1]) < 0.5

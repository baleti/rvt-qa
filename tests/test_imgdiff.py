import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(scope='module')
def D():
    pytest.importorskip('cv2')
    pytest.importorskip('skimage.metrics')
    from qa import imgdiff
    return imgdiff


def white(shape=(128, 128)):
    return np.full(shape, 255, dtype=np.uint8)


def pattern():
    g = white()
    g[25:45, 30:60] = 0
    g[65:90, 75:85] = 0
    g[85:90, 55:85] = 0
    return g


def test_load_gray_png(D, tmp_path):
    g = pattern()
    p = tmp_path / 'pattern.png'
    assert D.cv2.imwrite(str(p), g)
    loaded = D.load_gray(str(p))
    assert loaded.dtype == np.uint8
    np.testing.assert_array_equal(loaded, g)


def test_load_gray_missing(D, tmp_path):
    p = str(tmp_path / 'missing.png')
    with pytest.raises(IOError) as exc:
        D.load_gray(p)
    assert exc.value.args == (p,)


@pytest.mark.parametrize('threshold, expected', [(200, [1, 1, 0, 0, 0]),
                                                (201, [1, 1, 1, 0, 0])])
def test_ink_threshold_is_strict(D, threshold, expected):
    g = np.array([[0, 199, 200, 201, 255]], dtype=np.uint8)
    m = D.ink(g, threshold)
    assert m.dtype == np.uint8
    np.testing.assert_array_equal(m, [expected])


def test_ink_default(D):
    np.testing.assert_array_equal(D.ink(pattern()), (pattern() < 200).astype(np.uint8))


def test_content_bbox_empty(D):
    assert D.content_bbox(D.ink(white())) is None


def test_content_bbox_inclusive_coordinates(D):
    g = white()
    g[7:12, 20:29] = 0
    assert D.content_bbox(D.ink(g)) == (20, 7, 28, 11)


@pytest.mark.parametrize('minpix, expected', [(6, (4, 2, 6, 3)), (7, None)])
def test_content_bbox_minpix_counts_pixels(D, minpix, expected):
    g = white()
    g[2:4, 4:7] = 0
    assert D.content_bbox(D.ink(g), minpix) == expected


@pytest.mark.parametrize('dx, dy', [(0, 0), (7, -5)])
def test_register_translation(D, dx, dy):
    ref = pattern()
    ours = D.cv2.warpAffine(ref, np.float32([[1, 0, dx], [0, 1, dy]]),
                            (128, 128), borderValue=255)
    warped, transform = D.register(ours, ref)
    assert transform == pytest.approx((1, 1, -dx, -dy))
    np.testing.assert_array_equal(warped, ref)


@pytest.mark.parametrize('empty_ours', [True, False])
def test_register_empty_returns_original(D, empty_ours):
    ours, ref = (white(), pattern()) if empty_ours else (pattern(), white())
    warped, transform = D.register(ours, ref)
    assert warped is ours
    assert transform == (1, 1, 0, 0)


@pytest.mark.parametrize('dx, dy', [(0, 0), (7, -5)])
def test_refine_shift_reports_input_displacement(D, dx, dy):
    ref = pattern()
    ours = D.cv2.warpAffine(ref, np.float32([[1, 0, dx], [0, 1, dy]]),
                            (128, 128), borderValue=255)
    warped, shift, response = D.refine_shift(ours, ref)
    assert shift == pytest.approx((dx, dy), abs=0.05)
    assert response > 0.9
    np.testing.assert_allclose(warped, ref, atol=8)


def test_refine_shift_rejects_large_displacement(D):
    ref = pattern()
    ours = D.cv2.warpAffine(ref, np.float32([[1, 0, 7], [0, 1, -5]]),
                            (128, 128), borderValue=255)
    warped, shift, response = D.refine_shift(ours, ref, maxs=3)
    assert warped is ours
    assert shift == (0, 0)
    assert response > 0.9


def test_ink_pr_identical_and_empty(D):
    assert D.ink_pr(pattern(), pattern()) == (1, 1)
    assert D.ink_pr(white(), white()) == (0, 0)


def test_ink_pr_disjoint(D):
    ours, ref = white(), white()
    ours[10:20, 10:20] = 0
    ref[80:90, 80:90] = 0
    assert D.ink_pr(ours, ref) == (0, 0)


def test_ink_pr_tolerance(D):
    ours, ref = white(), white()
    ours[20:40, 20] = 0
    ref[20:40, 22] = 0
    assert D.ink_pr(ours, ref, tol=1) == (0, 0)
    assert D.ink_pr(ours, ref, tol=2) == (1, 1)


def test_ink_pr_precision_recall_direction(D):
    ref = white()
    ref[10:20, 10:20] = 0
    ours = ref.copy()
    ours[70:80, 70:80] = 0
    assert D.ink_pr(ours, ref, tol=0) == (0.5, 1)


def test_heatmap_counts_boxes_and_denominator_floor(D):
    ours, ref = white((20, 30)), white((20, 30))
    ref[1:3, 1:6] = 0  # Ten missing pixels in the first cell.
    ours[11:16, 21:26] = 0  # Twenty-five extra pixels in the last cell.
    cells, miss, extra = D.heatmap(ours, ref, cells=(2, 3), tol=0)
    assert len(cells) == 6
    assert miss.shape == extra.shape == ref.shape
    assert miss.dtype == extra.dtype == np.uint8
    np.testing.assert_array_equal(miss, D.ink(ref))
    np.testing.assert_array_equal(extra, D.ink(ours))
    for index, cell in enumerate(cells):
        i, j = divmod(index, 3)
        nb, na = (10 if index == 0 else 0), (25 if index == 5 else 0)
        assert cell == dict(i=i, j=j, box=(j*10, i*10, j*10+10, i*10+10),
                            ref_ink=nb, our_ink=na, missing=nb, extra=na,
                            miss_frac=nb/max(nb, 20), extra_frac=na/max(na, 20))


def test_heatmap_identical(D):
    cells, miss, extra = D.heatmap(pattern(), pattern())
    assert len(cells) == 96
    assert not miss.any() and not extra.any()
    assert all(c['miss_frac'] == c['extra_frac'] == 0 for c in cells)


def test_heatmap_drops_remainder_from_cells(D):
    ref = white((11, 11))
    ref[10, 10] = 0
    cells, miss, extra = D.heatmap(white((11, 11)), ref, cells=(2, 2), tol=0)
    assert miss.sum() == 1 and extra.sum() == 0
    assert sum(c['missing'] for c in cells) == 0
    assert cells[-1]['box'] == (5, 5, 10, 10)


def test_long_lines_drawn(D):
    g = white((200, 200))
    expected = [(20, 30, 180, 30), (20, 90, 180, 90), (50, 115, 50, 185)]
    for x1, y1, x2, y2 in expected:
        D.cv2.line(g, (x1, y1), (x2, y2), 0, 1)
    detected = D.long_lines(g)
    pairs, missing, extra = D.match_lines(detected, expected, tol=2)
    assert len(pairs) == 3
    assert missing == extra == []
    assert all(abs(p[3]) <= 10 for p in pairs)


def test_long_lines_empty(D):
    assert D.long_lines(white()) == []


def test_merge_segs_joins_collinear_even_across_gaps(D):
    assert D.merge_segs([(10, 20, 40, 20), (80, 20, 60, 20),
                         (10, 40, 80, 40)]) == [(10, 20, 80, 20), (10, 40, 80, 40)]
    assert D.merge_segs([]) == []


def test_merge_segs_distance_tolerance_is_strict(D):
    segs = [(10, 20, 40, 20), (10, 26, 40, 26)]
    assert D.merge_segs(segs, dist_tol=6) == segs
    assert len(D.merge_segs(segs, dist_tol=7)) == 1


@pytest.mark.parametrize('offset, matched', [(8, True), (9, False)])
def test_match_lines_tolerance(D, offset, matched):
    ref = [(10, 20, 90, 20)]
    ours = [(10, 20+offset, 90, 20+offset)]
    pairs, missing, extra = D.match_lines(ours, ref, tol=8)
    assert pairs == ([(0, 0, offset, 0)] if matched else [])
    assert missing == ([] if matched else ref)
    assert extra == ([] if matched else ours)


def test_match_lines_ignores_along_line_separation(D):
    pairs, missing, extra = D.match_lines([(150, 20, 190, 20)], [(10, 20, 90, 20)])
    assert pairs == [(0, 0, 0, -40)]
    assert missing == extra == []


def test_match_lines_rejects_angle_and_uses_each_line_once(D):
    ours = [(10, 20, 90, 20), (50, 10, 50, 90)]
    ref = [(10, 20, 90, 20), (10, 20, 90, 20)]
    pairs, missing, extra = D.match_lines(ours, ref)
    assert pairs == [(0, 0, 0, 0)]
    assert missing == [ref[1]] and extra == [ours[1]]


def test_match_pts_inclusive_tolerance_and_radius_ignored(D):
    ours, ref = [(13, 14, 20)], [(10, 10, 7)]
    assert D.match_pts(ours, ref, tol=5) == ([(0, ref[0], 5)], [], [])
    assert D.match_pts(ours, ref, tol=4) == ([], ref, ours)


def test_match_pts_nearest_and_one_use(D):
    ours = [(20, 20), (22, 20), (90, 90)]
    ref = [(21.5, 20), (20, 20), (20, 20)]
    assert D.match_pts(ours, ref, tol=3) == (
        [(1, ref[0], 0.5), (0, ref[1], 0)], [ref[2]], [ours[2]])


@pytest.mark.parametrize('detector', ['circles', 'bubbles'])
def test_drawn_circle(D, detector):
    g = white()
    D.cv2.circle(g, (64, 64), 16, 0, 2)
    detected = getattr(D, detector)(g)
    # Allow Hough quantisation; do not pin implementation-specific subpixel values.
    assert len(detected) == 1
    x, y, radius = detected[0]
    assert (x, y) == pytest.approx((64, 64), abs=2)
    assert radius == pytest.approx(16, abs=3)


@pytest.mark.parametrize('detector', ['circles', 'bubbles'])
def test_circle_detectors_empty(D, detector):
    assert getattr(D, detector)(white()) == []


def test_bubbles_radius_filter(D):
    g = white()
    D.cv2.circle(g, (64, 64), 16, 0, 2)
    assert D.bubbles(g, rmin=20, rmax=22) == []

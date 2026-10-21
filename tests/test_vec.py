import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qa import vec, vecgeom


@pytest.mark.parametrize('text, expected', [
    (' Room\tA\n 12 ', 'rooma12'), ('MiXeD-Case!', 'mixed-case!'), (' \n', ''),
])
def test_norm(text, expected):
    assert vec.norm(text) == expected


def test_svg_text_attributes_and_multiple_elements():
    svg = '''<svg>
      <text transform="translate(12.5,-3) rotate(30)" font-size="2.5"
            text-anchor="middle" data-e="42" font-family="A &amp; B"
            font-weight="700" font-style="oblique"> Room &amp; <tspan>A</tspan> </text>
      <text transform="translate(4 5)">Second</text>
    </svg>'''
    assert vec.svg_texts(svg) == [
        dict(t='Room & A', x=12.5, y=-3, h=2.5, rot=330, e='42',
             anchor='middle', font='A & B', bold=True, italic=True),
        dict(t='Second', x=4, y=5, h=0, rot=0, e=None,
             anchor='start', font='', bold=False, italic=False),
    ]


@pytest.mark.parametrize('body', ['', ' \n ', '<tspan> </tspan>'])
def test_svg_text_empty(body):
    assert vec.svg_texts(f'<text transform="translate(1,2)">{body}</text>') == []


def test_svg_text_without_translate_is_ignored():
    assert vec.svg_texts('<text x="1" y="2">Label</text>') == []


@pytest.mark.parametrize('body, expected', [
    ('<tspan dy="2">One</tspan>', [('One', 8, 20)]),
    ('<tspan dy="2">One</tspan><tspan dy="3">Two</tspan>',
     [('One', 8, 20), ('Two', 5, 20)]),
])
def test_svg_text_rotated_tspan_baselines(body, expected):
    items = vec.svg_texts(
        f'<text transform="translate(10,20) rotate(90)">{body}</text>')
    assert [o['t'] for o in items] == [t for t, _, _ in expected]
    for o, (_, x, y) in zip(items, expected):
        assert (o['x'], o['y'], o['rot']) == pytest.approx((x, y, 270))


@pytest.mark.parametrize('units, factor', [
    (1, 1 / 12), (2, 1), (4, 1 / 304.8), (5, 1 / 30.48), (6, 1 / 0.3048),
])
def test_dxf_texts_units_rotation_and_clean(tmp_path, units, factor):
    ezdxf = pytest.importorskip('ezdxf', reason='DXF fixtures require ezdxf')
    doc = ezdxf.new()
    doc.header['$INSUNITS'] = units
    model = doc.modelspace()
    model.add_text(r'{\C1;Angle %%d %%p}', dxfattribs={
        'insert': (12, 24), 'height': 3, 'rotation': -30,
        'layer': 'labels', 'width': 0.8,
    })
    model.add_mtext(r'{\C1;Room}', dxfattribs={
        'insert': (36, 48), 'char_height': 6, 'rotation': 45,
    })
    model.add_text('   ', dxfattribs={'height': 1})
    path = tmp_path / 'texts.dxf'
    doc.saveas(path)
    items, k = vec.dxf_texts(path)
    assert k == pytest.approx(factor)
    assert [o['t'] for o in items] == ['Angle ° ±', 'Room']
    assert [o['et'] for o in items] == ['TEXT', 'MTEXT']
    for o, position, height, rotation in zip(
            items, [(12, 24), (36, 48)], [3, 6], [330, 45]):
        assert (o['x'], o['y'], o['h'], o['rot']) == pytest.approx(
            (position[0] * factor, position[1] * factor, height * factor, rotation))
    assert items[0]['layer'] == 'labels'
    assert items[0]['wfactor'] == pytest.approx(0.8)


def text_items():
    return [dict(t=t, x=x, y=y, h=2, rot=0)
            for t, x, y in [('Alpha', 0, 0), ('Beta', 10, 4), ('Gamma', 3, 12)]]


def test_vote_registration_known_shift():
    ref = text_items()
    ours = [dict(o, x=o['x'] + 7, y=o['y'] - 5) for o in ref]
    assert vec.vote_registration(ours, ref) == pytest.approx((1, 7, -5, 3))


@pytest.mark.parametrize('compare', [vec.compare_texts, vec._compare_texts])
@pytest.mark.parametrize('change', ['identical', 'removed', 'moved'])
def test_compare_texts(compare, change):
    ref = text_items()
    ours = [dict(o) for o in ref]
    if change == 'removed':
        ours.pop()
    elif change == 'moved':
        ours[-1]['x'] += 6
        ours[-1]['y'] += 8
    matched, missing, extra = compare(ours, ref, 1, 0, 0, ptol=2)
    assert extra == []
    if change == 'removed':
        assert missing == [dict(ref[-1], mx=3, my=12)]
        assert len(matched) == 2
    else:
        assert missing == []
        assert len(matched) == 3
    # ptol does not reject a match: current code has a separate 40-unit cutoff.
    assert [d for _, _, d in matched] == pytest.approx(
        [0, 0, 10] if change == 'moved' else [0] * len(matched))
    assert [r['t'] for r, _, _ in matched] == [o['t'] for o in ours]


@pytest.mark.parametrize('points, expected', [
    ([(1, 2), (8, 2)], [(1, 2), (8, 2)]),
    ([(-4, 2), (-1, 2)], None),
    ([(-2, 5), (12, 5)], [(0, 5), (10, 5)]),
])
def test_clip_segment_and_polyline(points, expected):
    p = np.array(points, float)
    rect = (0, 0, 10, 10)
    segment = vecgeom._clip_seg(p[0], p[1], rect)
    polys = vecgeom._clip_poly(p, rect)
    if expected is None:
        assert segment is None
        assert polys == []
    else:
        np.testing.assert_allclose(segment, expected)
        assert len(polys) == 1
        np.testing.assert_allclose(polys[0], expected)


def test_svg_polys_path():
    polys = vecgeom.svg_polys(
        '<svg><path data-e="17" stroke-width="0.5" '
        'd="M0,0 L4,0 L4,3 M8,8 L9,8"/></svg>')
    assert [(e, w) for e, w, _ in polys] == [('17', 0.5), ('17', 0.5)]
    np.testing.assert_allclose(polys[0][2], [(0, 0), (4, 0), (4, 3)])
    np.testing.assert_allclose(polys[1][2], [(8, 8), (9, 8)])


@pytest.mark.parametrize('element', [
    '<line x1="0" y1="0" x2="4" y2="3"/>',
    '<polyline points="0,0 4,0 4,3"/>',
    '<rect x="0" y="0" width="4" height="3"/>',
])
def test_svg_polys_non_path_elements_currently_ignored(element):
    assert vecgeom.svg_polys(f'<svg>{element}</svg>') == []


@pytest.mark.parametrize('length', [2, 4, 8])
def test_sample_midpoints_spacing_and_count(length):
    points, labels = vecgeom.sample([('edge', np.array([(0, 0), (length, 0)]))], step=0.5)
    assert len(points) == length * 2
    np.testing.assert_allclose(points[:, 0], np.arange(0.25, length, 0.5))
    np.testing.assert_allclose(points[:, 1], 0)
    assert labels.tolist() == ['edge'] * len(points)


def test_sample_empty():
    points, labels = vecgeom.sample([])
    assert points.shape == (0, 2)
    assert labels.shape == (0,)


def test_fft_offset_known_shift():
    points, _ = vecgeom.sample([
        ('edge', np.array([(0, 0), (12, 0), (12, 7), (4, 9)], float))])
    shift = np.array([5, -3])
    np.testing.assert_allclose(vecgeom.fft_offset(points, points + shift, cell=0.5),
                               shift, atol=0.5, rtol=0)


def test_compare_svg_dxf_same_drawing(tmp_path):
    ezdxf = pytest.importorskip('ezdxf', reason='DXF fixtures require ezdxf')
    pytest.importorskip('qa.layers', reason='vecgeom.dxf_polys requires qa.layers, absent in source-only checkout')
    doc = ezdxf.new()
    doc.header['$INSUNITS'] = 4  # millimetres; at scale 1 the only transform is y reflection
    points = [(0, 0), (12, 0), (12, 7), (4, 9)]
    for a, b in zip(points[:-1], points[1:]):
        doc.modelspace().add_line((a[0], -a[1]), (b[0], -b[1]))
    path = tmp_path / 'drawing.dxf'
    doc.saveas(path)
    svg = '<svg><path data-e="1" d="M0,0 L12,0 L12,7 L4,9"/></svg>'
    result = vecgeom.compare(svg, path, scale=1)
    assert result is not None
    assert result['precision'] >= 0.99
    assert result['recall'] >= 0.99
    assert result['chamfer_mm'] <= 0.1

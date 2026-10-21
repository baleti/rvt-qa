import os, sys
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qa import fonts as F, layers as L


@pytest.mark.parametrize('name, expected', [
    (None, ('unknown', False, False)),
    ('  "ARIAL", sans-serif ', ('arial', False, False)),
    ('LiBeRaTiOn Sans', ('arial', False, False)),
    ('ABCDEF+TrebuchetMS-BoldItalic', ('trebuchet', True, True)),
    ('arialbd.ttf', ('arial', True, False)),
    ('arialbi.ttf', ('arial', True, True)),
    ('ariali.ttf', ('arial', False, True)),
    ('Arial-Regular.otf', ('arial', False, False)),
    ('ARchitxt.shx', ('architxt', False, False)),
    ('Arial-B', ('arialb', True, False)),
    ('Arial-It', ('arialit', False, True)),
    ('Times New Roman', ('timesnew', False, False)),
])
def test_canon(name, expected):
    # Suffix flags and family stripping are separate; even Roman is stripped.
    assert F.canon(name) == expected


@pytest.fixture
def system_family():
    path, family = F.resolve('sans-serif', False, False)
    if not path or not Path(path).is_file():
        pytest.skip('fontconfig found no usable system font file')
    return family.split(',')[0]


@pytest.mark.parametrize('bold, italic', [(False, False), (True, False), (False, True), (True, True)])
def test_resolve_known_and_unknown(system_family, bold, italic):
    for family in (system_family, 'QA_NONEXISTENT_FONT_937164'):
        path, actual = F.resolve(family, bold, italic)
        assert path and Path(path).is_file()
        assert actual
        if family == system_family:
            assert F.canon(actual)[0] == F.canon(system_family)[0]
        else:
            assert actual != family


@pytest.mark.parametrize('bold, italic', [(False, False), (True, True)])
def test_resolve_spec(monkeypatch, bold, italic):
    calls = []
    def run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(stdout='/synthetic/font.ttf|Example')
    monkeypatch.setattr(F.subprocess, 'run', run)
    # Bypass the cache so this test neither depends on nor poisons cached matches.
    assert F.resolve.__wrapped__('Example', bold, italic) == ('/synthetic/font.ttf', 'Example')
    spec = 'Example:' + (':bold' if bold else '') + (':italic' if italic else '')
    assert calls == [(['fc-match', '-f', '%{file}|%{family}', spec],
                      dict(capture_output=True, text=True, timeout=10))]


def test_advance_mm(system_family):
    def width(text, size=2):
        return F.advance_mm(text, system_family, False, False, size)
    if width('M') is None:
        pytest.skip('Pillow cannot measure the fontconfig-selected system font')
    assert width('') == 0
    widths = [width('M' * n) for n in range(1, 8)]
    assert all(a < b for a, b in zip(widths, widths[1:]))
    assert width('MMMM') > width('M')
    assert width('MMMM', 6) == pytest.approx(3 * width('MMMM', 2))


def test_advance_unresolved(monkeypatch):
    monkeypatch.setattr(F, 'resolve', lambda *args: (None, None))
    assert F.advance_mm('abc', 'missing', False, False, 2) is None


def pairs(n=3, rf='Arial', of='Arial', rh=2, oh=2, dy=0):
    return [(dict(font=rf, h=rh, x=0, y=0, w=4),
             dict(font=of, h=oh, x=0, y=dy, t='text%d' % i), 0)
            for i in range(n)]


@pytest.fixture
def matched_fonts(monkeypatch):
    monkeypatch.setattr(F, 'resolve', lambda family, bold, italic: (None, family))


def test_check_empty_and_matching(matched_fonts):
    assert F.check([], 'pdf') == ([], [])
    table, findings = F.check(pairs(), 'dxf')
    assert table == [dict(revit_font='Arial', revit_family='arial', ours_family='arial',
                          ours_renders_as='Arial', n=3, size_ratio=1.0, width_ratio=None)]
    assert findings == []


def test_check_family_and_substitution(monkeypatch):
    monkeypatch.setattr(F, 'resolve', lambda *args: (None, 'Fallback'))
    table, findings = F.check(pairs(1, of='Example'), 'dxf')
    assert table[0]['ours_renders_as'] == 'Fallback'
    assert [f['kind'] for f in findings] == ['font-family-diff', 'font-substituted']
    assert findings[0]['score'] == pytest.approx(1 + 1 / 30)
    assert findings[0]['examples'] == [dict(t='text0', at_mm=(0, 0), e=None)]
    assert findings[1]['score'] == 0.3


@pytest.mark.parametrize('flag', ['bold', 'italic'])
def test_check_style_threshold(matched_fonts, flag):
    ps = pairs()
    ps[0][1][flag] = True
    assert F.check(ps, 'dxf')[1] == []
    ps[1][1][flag] = True
    finding, = F.check(ps, 'dxf')[1]
    assert (finding['kind'], finding['n']) == ('font-style-diff', 2)
    assert finding['score'] == pytest.approx(0.85)


def test_check_pdf_ratios(monkeypatch, matched_fonts):
    monkeypatch.setattr(F, 'advance_mm', lambda *args: 8)
    table, findings = F.check(pairs(oh=4), 'pdf')
    assert table[0]['size_ratio'] == table[0]['width_ratio'] == 2.0
    assert [(f['kind'], f['n']) for f in findings] == [('font-size', 3), ('font-width', 3)]
    assert F.check(pairs(2, oh=4), 'pdf')[1] == []
    assert F.check(pairs(oh=4), 'dxf')[1] == []


def test_check_missing_heights_and_short_text(monkeypatch, matched_fonts):
    monkeypatch.setattr(F, 'advance_mm', lambda *args: 8)
    ps = pairs(rh=0)
    for r, o, d in ps:
        o['t'] = 'ab'
    table, findings = F.check(ps, 'pdf')
    assert table[0]['size_ratio'] is None and table[0]['width_ratio'] is None
    assert findings == []


def test_missing_fonts(monkeypatch):
    calls = []
    def resolve(family, bold, italic):
        calls.append((family, bold, italic))
        return None, {'Arial': 'Arial', 'Ghost': 'Fallback', 'Lost': None}[family]
    monkeypatch.setattr(F, 'resolve', resolve)
    assert F.missing_fonts(['Ghost-Bold', 'ArialMT', 'Ghost-Bold', 'Lost']) == [('Ghost-Bold', 'Fallback')]
    assert calls == [('Arial', False, False), ('Ghost', True, False), ('Lost', False, False)]


def test_baseline_pdf():
    summary, findings = F.baseline(pairs(dy=1), 'pdf')
    assert summary == dict(n=3, mismatched_over_8mm=0, mean=1.0, median=1.0,
                          max_abs=1.0, p90_abs=1.0,
                          by_type={'arial 2.0mm': dict(n=3, median=1.0, mean=1.0, max_abs=1.0, per_h=0.5)})
    finding, = findings
    assert (finding['kind'], finding['median_mm'], finding['n']) == ('text-baseline', 1.0, 3)
    assert finding['examples'][0] == dict(t='text0', at_mm=(0, 1), e=None, dn=1.0)


@pytest.mark.parametrize('fixed, expected', [(False, 0.5), (True, 2.0)])
def test_baseline_dxf_mtext(fixed, expected):
    ps = pairs(dy=5)
    for r, o, d in ps:
        r.update(et='MTEXT', top_fixed=fixed)
    assert F.baseline(ps, 'dxf') == (None, [])
    summary, findings = F.baseline(ps, 'dxf', off=(0, 3))
    assert summary['median'] == expected
    assert summary['by_type']['MTEXT arial']['n'] == 3
    assert findings[0]['median_mm'] == expected


def test_baseline_filters():
    assert F.baseline([], 'pdf') == (None, [])
    assert F.baseline(pairs(2), 'pdf') == (None, [])
    ps = pairs(7)
    for i in range(3):
        ps[i][1]['t'] = ['TAG', 't a g', ' tag '][i]
    ps[3][1]['rot'] = 45
    assert F.baseline(ps, 'pdf')[0]['n'] == 3
    ps.append((dict(font='Arial', h=2, y=0), dict(t='outlier', x=0, y=9, h=2), 0))
    summary, findings = F.baseline(ps, 'pdf')
    assert summary['n'] == 3 and summary['mismatched_over_8mm'] == 1
    assert findings == []


def test_baseline_rotated_dxf():
    ps = pairs()
    for r, o, d in ps:
        o.update(rot=90, x=2, y=7)
    summary, _ = F.baseline(ps, 'dxf', off=(1, 0))
    assert summary['median'] == 1.0


def test_dxf_layers(tmp_path):
    ezdxf = pytest.importorskip('ezdxf', reason='synthetic DXF parsing requires ezdxf')
    doc = ezdxf.new()
    doc.modelspace().add_line((0, 0), (10, 0), dxfattribs={'layer': 'walls'})
    block = doc.blocks.new('part')
    block.add_line((0, 0), (0, 5), dxfattribs={'layer': 'detail'})
    doc.modelspace().add_blockref('part', (3, 4))
    doc.modelspace().add_text('ignored', dxfattribs={'layer': 'text'})
    path = tmp_path / 'tiny.dxf'; doc.saveas(path)
    result = L.dxf_layers(path)
    assert set(result) == {'walls', 'detail'}
    np.testing.assert_allclose(result['walls'][0], [[0, 0], [10, 0]])
    np.testing.assert_allclose(result['detail'][0], [[3, 4], [3, 9]])


def test_raster_layers():
    geometry = {'bottom': [np.array([[0, 0], [10, 0]])],
                'left': [np.array([[0, 0], [0, 10]])]}
    per, combined = L.raster_layers(geometry, 100, 100, margin=0.1)
    expected = np.full((100, 100), 255, np.uint8)
    cv2.line(expected, (10, 90), (90, 90), 0, 1)
    np.testing.assert_array_equal(per['bottom'], expected)
    cv2.line(expected, (10, 90), (10, 10), 0, 1)
    np.testing.assert_array_equal(combined, expected)
    np.testing.assert_array_equal(combined, np.minimum(per['bottom'], per['left']))


def test_layer_recall_empty(monkeypatch):
    monkeypatch.setattr(L, 'dxf_layers', lambda fn: {})
    assert L.layer_recall('unused', np.full((64, 64), 255, np.uint8)) is None


@pytest.mark.parametrize('tol, recall', [(0, 0.0), (2, 1.0)])
def test_layer_recall_rows(monkeypatch, tol, recall):
    # Fix registration to test recall thresholds and ordering independently of search.
    def line(y, end=50):
        im = np.full((64, 64), 255, np.uint8)
        cv2.line(im, (5, y), (end, y), 0, 1)
        return im
    per = {'present': line(10), 'missing': line(40), 'short': line(55, 15)}
    combined = np.minimum.reduce(list(per.values()))
    monkeypatch.setattr(L, 'dxf_layers', lambda fn: {'synthetic': []})
    monkeypatch.setattr(L, 'raster_layers', lambda *args: (per, combined))
    def register(ref, ours):
        np.testing.assert_array_equal(ref, combined)
        return ref, (1, 0, 0, 0.87654, np.float32([[1, 0, 0], [0, 1, 0]]))
    monkeypatch.setattr(L.D, 'register_search', register)
    result = L.layer_recall('unused', line(12), tol=tol)
    assert result['reg_score'] == 0.877
    rows = {r['layer']: r for r in result['layers']}
    assert set(rows) == {'present', 'missing'}
    assert rows['present'] == dict(layer='present', ink_px=46, recall=recall,
                                   chamfer_px=1.9, hausdorff95_px=1.9)
    assert rows['missing'] == dict(layer='missing', ink_px=46, recall=0.0,
                                   chamfer_px=26.7, hausdorff95_px=26.7)
    assert [r['layer'] for r in result['layers']] == (['present', 'missing'] if tol == 0 else ['missing', 'present'])

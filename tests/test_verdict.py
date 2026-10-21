import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qa import verdict as V

def test_text_recall():
    assert V.text_recall({}) is None
    assert V.text_recall({'matched': 3, 'revit': 4}) == 0.75
    assert V.text_recall({'matched': 0, 'revit': 0}) == 0

def test_combined_score_image_only():
    assert V.combined_score({'ink_R6': 1.0, 'ink_P6': 0.5}, None, None, None, None) == round(100 * (0.3 * 1 + 0.2 * 0.5) / 0.5, 1)
    assert V.combined_score({}, None, None, None, None) is None

def test_combined_score_all_tiers():
    im = {'ink_R6': 0.8, 'ink_P6': 0.9}
    lines = {'revit': 10, 'matched': 5}
    layers = [{'ink_px': 100, 'recall': 1.0}, {'ink_px': 100, 'recall': 0.5}]
    s = V.combined_score(im, 1.0, lines, layers, [{'len_mm': 5, 'recall': 0.0}])
    exp = (0.3 * 0.8 + 0.2 * 0.9 + 0.25 * 1.0 + 0.1 * 0.5 + 0.15 * 0.75) / 1.0
    assert s == round(100 * exp, 1)

def test_combined_score_geom_layers_replace_raster():
    s = V.combined_score({'ink_R6': 1.0, 'ink_P6': 1.0}, None, None, None, [{'len_mm': 10, 'recall': 0.5}, {'len_mm': 10, 'recall': 0.5}])
    assert s == round(100 * (0.3 + 0.2 + 0.15 * 0.5) / 0.65, 1)

def test_vector_score():
    assert V.vector_score({'recall': 1.0, 'precision': 0.5}, None) == round(100 * (0.4 + 0.35 * 0.5) / 0.75, 1)
    assert V.vector_score({'recall': 1.0, 'precision': 1.0}, 0.0) == round(100 * 0.75, 1)

def test_reliable():
    assert V.is_reliable({'reg_score': 0.35}) and not V.is_reliable({'reg_score': 0.34}) and not V.is_reliable({})

def test_verdicts():
    im = {'ink_R6': 0.9, 'ink_P6': 0.9}; g = {'recall': 0.96, 'precision': 0.95}
    assert V.verdicts(im, g, 0.95, True) == (True, True)
    assert V.verdicts(im, g, 0.89, True) == (False, True)
    assert V.verdicts(im, g, 0.80, True) == (False, False)
    assert V.verdicts({'ink_R6': 0.1, 'ink_P6': 0.1}, g, None, False) == (True, True)
    assert V.verdicts({'ink_R6': 0.1, 'ink_P6': 0.1}, None, None, True) == (False, False)

def test_area_of():
    a = V.area_of
    assert a({'kind': 'font-missing'}) == 'fonts'
    assert a({'kind': 'text-baseline'}) == 'text baseline'
    assert a({'kind': 'text-moved'}) == 'annotations/text'
    assert a({'kind': 'longline-missing'}) == 'grids'
    assert a({'kind': 'region-extra', 'what': 'GRID-A'}) == 'grids'
    assert a({'kind': 'lineweight-missing'}) == 'line weights'
    assert a({'kind': 'registration-unreliable'}) == 'view not rendered'
    assert a({'kind': 'geom-layer-missing', 'what': 'A-WALL'}) == 'layer A-WALL'
    assert a({'kind': 'geom-extra-element', 'what': 'element 5'}) == 'extra drawn element 5'
    assert a({'kind': 'region-missing'}) == 'drawing content'

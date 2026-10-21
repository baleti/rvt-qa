"""Pure scoring, verdicts, and finding owner hints for view comparisons."""


def text_recall(tx):
    return tx.get('matched', 0) / max(tx.get('revit', 1), 1) if 'matched' in tx else None


def combined_score(im, tr, lines, layers, geom_layers):
    parts = []
    if im: parts += [(0.30, im.get('ink_R6', 0)), (0.20, im.get('ink_P6', 0))]
    if tr is not None: parts.append((0.25, tr))
    if lines and lines['revit']: parts.append((0.10, lines['matched'] / lines['revit']))
    if layers:
        tot = sum(x['ink_px'] for x in layers); parts.append((0.15, sum(x['ink_px'] * x['recall'] for x in layers) / max(tot, 1)))
    if geom_layers and not layers:   # vector per-layer recall takes the raster layer term's place (keeps the score stable when the raster term is skipped)
        tot = sum(x['len_mm'] for x in geom_layers); parts.append((0.15, sum(x['len_mm'] * x['recall'] for x in geom_layers) / max(tot, 1)))
    return round(100 * sum(w * v for w, v in parts) / sum(w for w, _ in parts), 1) if parts else None


def vector_score(g, tr):
    gp = [(0.4, g['recall']), (0.35, g['precision'])] + ([(0.25, tr)] if tr is not None else [])
    return round(100 * sum(w * v for w, v in gp) / sum(w for w, _ in gp), 1)


def is_reliable(im):
    return bool(im.get('reg_score', 0) >= 0.35)


def verdicts(im, g, tr, reliable):
    passed = bool(im.get('ink_R6', 0) >= 0.85 and im.get('ink_P6', 0) >= 0.85 and (tr is None or tr >= 0.9))
    if not reliable and g:     # image registration unreliable: judge by DXF geometry (mm, no registration needed) and text
        passed = bool(g['recall'] >= 0.85 and g['precision'] >= 0.85 and (tr is None or tr >= 0.9))
    pass_vector = bool(g and g['recall'] >= 0.95 and g['precision'] >= 0.9 and (tr is None or tr >= 0.85))   # DXF geometry+text agree even if the PNG tier disagrees (Revit's PNG carries hatch/pattern ink the DXF lacks)
    return passed, pass_vector


def area_of(finding):
    k = finding['kind']; w = str(finding.get('what', ''))
    return ('fonts' if k.startswith('font') else 'text baseline' if k == 'text-baseline' else 'annotations/text' if k.startswith('text') else 'grids' if k.startswith(('longline', 'bubble')) or 'GRID' in w else
                     'line weights' if k.startswith('lineweight') else 'view not rendered' if k in ('view-not-rendered', 'registration-unreliable') else
                     'layer ' + w if k in ('layer-missing', 'geom-layer-missing') else ('extra drawn ' + w) if k == 'geom-extra-element' else 'drawing content')

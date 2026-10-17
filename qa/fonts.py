"""Font check: per matched text pair compare font family/style (Revit DXF text style -> font file, or Revit PDF span font name, vs our SVG font-family),
size ratio and glyph advance width (PDF only: Revit gives the span bbox; ours is measured with PIL on the font fontconfig resolves for our family).
check(pairs, src) -> (table, findings): table rows per (revit font -> our font) group; findings font-family-diff / font-style-diff / font-size / font-width / font-substituted."""
import re, math, subprocess, functools, collections
import numpy as np

def canon(name):
    """-> (family, bold, italic) from 'ABCDEF+TrebuchetMS-BoldItalic', 'arial.ttf', 'Arial, sans-serif', 'ARchitxt'"""
    n = (name or '').split(',')[0].strip().strip('"\'').lower(); n = re.sub(r'^[a-z]{6}\+', '', n); n = re.sub(r'\.(ttf|ttc|otf|shx)$', '', n)
    b = bool(re.search(r'bold|black|heavy|\bbd\b|-b$', n)); i = bool(re.search(r'italic|oblique|-it$|\bi$', n))
    if re.fullmatch(r'(arial|times|calibri|verdana|tahoma|segoeui|cour)i', n): i = True; n = n[:-1]
    if re.fullmatch(r'[a-z]{4,}(bd|bi)', n) and not n.endswith('ubi'):      # windows font files: arialbd.ttf, arialbi.ttf
        b = True; i = i or n.endswith('bi'); n = n[:-2]
    n = re.sub(r'[-_ ]?(bolditalic|boldoblique|bold|italic|oblique|regular|roman|normal|black|heavy)', '', n); n = re.sub(r'(psmt|ps|mt)$', '', n); n = re.sub(r'[^a-z0-9]', '', n)
    alias = {'arialmt': 'arial', 'arialnarrow': 'arialnarrow', 'timesnewroman': 'timesnewroman', 'times': 'timesnewroman', 'trebuchetms': 'trebuchet', 'liberationsans': 'arial', 'helvetica': 'arial', 'sansserif': 'arial'}
    return alias.get(n, n) or 'unknown', b, i

@functools.lru_cache(maxsize=None)
def resolve(family, bold, italic):
    """font file fontconfig picks for a family (what rsvg / a browser falls back to on this machine) and the family it really is"""
    spec = '%s:%s%s' % (family, ':bold' if bold else '', ':italic' if italic else '')
    try:
        out = subprocess.run(['fc-match', '-f', '%{file}|%{family}', spec], capture_output=True, text=True, timeout=10).stdout
        f, fam = out.split('|', 1); return f, fam
    except Exception: return None, None

@functools.lru_cache(maxsize=None)
def _font(path):
    from PIL import ImageFont
    return ImageFont.truetype(path, 200)

def advance_mm(text, family, bold, italic, size_mm):
    p, _ = resolve(family, bold, italic)
    if not p: return None
    try: return _font(p).getlength(text) / 200.0 * size_mm
    except Exception: return None

def check(pairs, src):
    """pairs: [(r, o, dist)] with r = Revit text dict (font; PDF also w) and o = our svg_texts dict (font, bold, italic, h, x, y)"""
    groups = collections.defaultdict(list)
    for r, o, d in pairs:
        rf, rb, ri = canon(r.get('font')); of, ob, oi = canon(o.get('font')); rb = rb or ('bold' in (r.get('font') or '').lower())
        groups[(rf, of)].append((r, o, rb, ri, ob or o.get('bold', False), oi or o.get('italic', False)))
    table, F = [], []
    for (rf, of), L in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        n = len(L); hr = [o['h'] / r['h'] for r, o, *_ in L if r.get('h', 0) > 0 and o.get('h', 0) > 0]
        wr = []
        if src == 'pdf':
            for r, o, rb, ri, ob, oi in L:
                a = advance_mm(o['t'], o.get('font', 'Arial'), ob, oi, o['h'])
                if a and r.get('w', 0) > 0 and len(o['t']) >= 3: wr.append(a / r['w'])
        sub = resolve(o_first(L), L[0][4], L[0][5])[1]
        row = dict(revit_font=L[0][0].get('font'), revit_family=rf, ours_family=of, ours_renders_as=sub, n=n, size_ratio=round(float(np.median(hr)), 3) if hr else None, width_ratio=round(float(np.median(wr)), 3) if wr else None)
        table.append(row); ex = [dict(t=o['t'][:24], at_mm=(round(o['x'], 1), round(o['y'], 1)), e=o.get('e')) for r, o, *_ in L[:6]]
        if rf != of and rf not in ('unknown', '') and of not in ('unknown', ''):
            F.append(dict(kind='font-family-diff', score=1.0 + min(n, 60) / 30.0, what='%s -> %s' % (row['revit_font'], o_first(L)), n=n, examples=ex, at_mm=ex[0]['at_mm']))
        else:
            bd = sum(1 for r, o, rb, ri, ob, oi in L if rb != ob or ri != oi)
            if bd >= max(2, n // 3): F.append(dict(kind='font-style-diff', score=0.8 + min(bd, 40) / 40.0, what='%s bold/italic differs on %d of %d' % (rf, bd, n), n=bd, examples=ex, at_mm=ex[0]['at_mm']))
        if sub and of and not re.sub(r'[^a-z0-9]', '', sub.lower().split(',')[0]).startswith(of[:5]):
            F.append(dict(kind='font-substituted', score=0.3, what='%s renders as %s on this machine (fontconfig)' % (o_first(L), sub), n=n))
        if row['size_ratio'] and n >= 3 and abs(math.log(row['size_ratio'])) > math.log(1.10) and src == 'pdf':
            F.append(dict(kind='font-size', score=0.6, what='%s size ratio %.2f (n=%d)' % (rf, row['size_ratio'], n), n=n, examples=ex, at_mm=ex[0]['at_mm']))
        if row['width_ratio'] and len(wr) >= 3 and abs(math.log(row['width_ratio'])) > math.log(1.08):
            F.append(dict(kind='font-width', score=0.6 + min(abs(math.log(row['width_ratio'])), 0.5), what='%s glyph advance ratio ours/Revit %.2f (n=%d)' % (rf, row['width_ratio'], len(wr)), n=len(wr), examples=ex, at_mm=ex[0]['at_mm']))
    return table, F

def o_first(L): return L[0][1].get('font', '').split(',')[0].strip().strip('"\'') or 'Arial'

def missing_fonts(revit_fonts):
    """Revit font names whose family fontconfig cannot supply (it would silently substitute)"""
    out = []
    for f in sorted(set(revit_fonts)):
        fam, b, i = canon(f); _, got = resolve(f.split('-')[0].replace('MT', ''), b, i)
        if got and fam[:5] not in re.sub(r'[^a-z0-9]', '', got.lower()): out.append((f, got))
    return out

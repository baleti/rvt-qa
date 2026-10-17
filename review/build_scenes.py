#!/usr/bin/env python3
"""review/build_scenes.py ROOT DIRNAME... : for Revit exports in ROOT/revit/<DIRNAME>/ (index.tsv + <id>.png from c3-writer) render OUR view SVG from the source scene
(write-lab/scenes, rosetta or corpus) with rvt-sheets (dev tree) and build the same pairs as build.py into ROOT/<DIRNAME>/ (3D views are left to build3d.py)."""
import sys, os, re, json, subprocess, glob
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from build import build_pair, TYPES, safe
root = sys.argv[1]; py = os.environ.get('QA_RENDER_PY') or os.path.expanduser('~/rvt-env/bin/python')
os.environ.setdefault('RVTSHEETS_DIR', os.path.expanduser('~/src/rvt-sheets-dev'))
def source(fileline):
    base = fileline.replace('\\', '/').split('/')[-1]; cands = [base, re.sub(r'^rv_', '', base), re.sub(r'^ve_', '', base)]
    m = re.match(r'(?:rv|ve)_(.*?)_(?:rte|rvt)_(.*)$', base)
    if m: cands.append(m.group(2))
    for c in cands:
        for d in ('~/rvt-research/write-lab/scenes', '~/rvt-research/rosetta', '~/rvt-research/corpus/2024', '~/rvt-research/corpus/2026', '~/rvt-research/corpus/2020'):
            p = os.path.join(os.path.expanduser(d), c)
            if os.path.exists(p): return p
allm = []
for dn in sys.argv[2:]:
    rd = os.path.join(root, 'revit', dn); ix = os.path.join(rd, 'index.tsv')
    if not os.path.exists(ix): print('no index', dn); continue
    lines = [l.rstrip('\n').split('\t') for l in open(ix, encoding='utf-8', errors='replace')]
    src = source(lines[0][1]) if lines and lines[0][0] == 'FILE' else None
    if not src: print('no source for', dn, lines[0][1:2]); continue
    views = [l for l in lines if l[0] == 'VIEW' and len(l) > 7 and l[3] != 'ThreeD' and os.path.exists(os.path.join(rd, l[1] + '.png'))]
    sub = os.path.join(root, dn); os.makedirs(sub, exist_ok=True); cache = os.path.join(sub, '_ours'); os.makedirs(cache, exist_ok=True)
    ids = [l[1] for l in views if not os.path.exists(os.path.join(cache, l[1] + '.svg'))]
    if ids: subprocess.run([py, os.path.join(os.path.dirname(HERE), 'qa', 'render_ours.py'), src, cache] + ids, env=dict(os.environ), check=False)
    for l in views:
        vid = int(l[1]); svg = os.path.join(cache, '%d.svg' % vid); png = os.path.join(rd, '%d.png' % vid)
        if not os.path.exists(svg): print('no svg', dn, vid); continue
        t = TYPES.get(l[3], TYPES.get(l[2], 'other')); name = '%d_%s_%s' % (vid, safe(l[4]), t); base = os.path.join(sub, name)
        try: m = build_pair(svg, png, base, '%s %s' % (l[4], vid), full_sheet=(t == 'sheet'))
        except Exception as ex: print('fail', dn, vid, repr(ex)[:120]); continue
        if not m: continue
        m.update(file=dn, id=vid, name=l[4], type=t, vtype=l[3], score=None, qa_pass=None, path=dn + '/' + name)
        json.dump(m, open(base + '.json', 'w')); allm.append(m); print('ok', m['path'], m['reg_score'], flush=True)
print(len(allm), 'pairs')

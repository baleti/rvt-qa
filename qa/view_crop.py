"""rvt-env python: view_crop.py FILE.rvt VIEWID... -> crop_active / basis / bounds of the views (QA diagnosis of unclipped elevations). Run on host1 via h1run."""
import sys, os
sys.path.insert(0, os.path.expanduser(os.environ.get('RVTSHEETS_DIR', '~/src/rvt-sheets')))
from rvtsheets.decode import Decoder
dec = Decoder(sys.argv[1]); doc = dec.doc()
for i in sys.argv[2:]:
    v = doc['views'].get(int(i)) or {}; c = v.get('crop') or {}
    print(i, v.get('name'), v.get('kind'), 'crop_active', c.get('crop_active'), 'has_basis', bool(c.get('basis')), 'bounds', c.get('bounds'), 'far', {k: c[k] for k in c if 'far' in k or 'proj' in k or 'depth' in k or 'clip' in k}, 'view_far', {k: v[k] for k in v if 'far' in k or 'depth' in k or 'clip' in k}, flush=True)

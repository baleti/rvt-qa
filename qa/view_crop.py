"""rvt-env python: view_crop.py FILE.rvt VIEWID... -> crop_active / basis / bounds of the views (QA diagnosis of unclipped elevations). Run on remote-host via h1run."""
import sys, os
sys.path.insert(0, os.path.expanduser(os.environ.get('RVTSHEETS_DIR', '~/src/rvt-sheets')))
from rvtsheets.decode import Decoder
dec = Decoder(sys.argv[1]); doc = dec.doc()
for i in sys.argv[2:]:
    v = doc['views'].get(int(i)) or {}; c = v.get('crop') or {}
    print(i, v.get('name'), v.get('kind'), 'crop_active', c.get('crop_active'), 'has_basis', bool(c.get('basis')), 'bounds', c.get('bounds'), 'keys', sorted(c.keys()), flush=True)

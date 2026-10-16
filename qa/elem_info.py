"""rvt-env python: elem_info.py FILE.rvt ID... -> class and category of elements (to name the owner of QA 'extra drawn element' findings). Run on host1 via h1run."""
import sys, os
sys.path.insert(0, os.path.expanduser(os.environ.get('RVTSHEETS_DIR', '~/src/rvt-sheets')))
from rvtsheets.decode import Decoder
dec = Decoder(sys.argv[1]); cats = dec.categories()
for i in sys.argv[2:]:
    e = int(i); rs = dec.f.byid.get(e, []); c = dec._cat_of(e)
    print(e, [r['class'] for r in rs], 'cat', c, (cats.get(c) or {}).get('name') if isinstance(cats, dict) and c is not None else '', flush=True)

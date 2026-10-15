"""run with the rvt-sheets venv python: render_ours.py FILE.rvt OUTDIR VIEWID... -> OUTDIR/<id>.svg + <id>.json (kind, scale, name). Mirrors tools/fid_images.py."""
import sys, os, json, time
sys.path.insert(0, os.path.expanduser(os.environ.get('RVTSHEETS_DIR', '~/src/rvt-sheets')))   # set RVTSHEETS_DIR=~/src/rvt-sheets-dev to QA the dev tree
from rvtsheets.decode import Decoder
from rvtsheets.viewdraw import ViewDrawer
from rvtsheets.viewsvg import view_svg
from rvtsheets.compose import sheet_svg, crop_rect_uv
fn, out = sys.argv[1], sys.argv[2]; ids = [int(x) for x in sys.argv[3:]]
os.makedirs(out, exist_ok=True)
dec = Decoder(fn); doc = dec.doc(); vd = ViewDrawer(dec, doc)
for vid in ids:
    t = time.time(); v = doc['views'].get(vid) or {}
    try:
        if v.get('kind') == 'sheet' or vid in doc.get('sheets', {}):
            svg = sheet_svg(dec, vid, doc, vd, log=lambda *a: None)
        else:
            svg = view_svg(vd.draw(vid), v.get('scale') or 100, margin_mm=0, crop=crop_rect_uv(v))
        open(os.path.join(out, '%d.svg' % vid), 'w').write(svg)
        json.dump(dict(id=vid, kind=v.get('kind'), scale=v.get('scale'), name=v.get('name'), secs=round(time.time() - t, 1)), open(os.path.join(out, '%d.json' % vid), 'w'))
        print('ok', vid, round(time.time() - t, 1), flush=True)
    except Exception as ex:
        print('fail', vid, repr(ex)[:200], flush=True)

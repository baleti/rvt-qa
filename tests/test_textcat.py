import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qa import textcat as T

def test_cat():
    assert T.cat("12' 6\"") == 'dimension string'
    assert T.cat('2500') == 'number (mm dim / level / grid)'
    assert T.cat('-3.5') == 'number (mm dim / level / grid)'
    assert T.cat('A') == 'grid letter'
    assert T.cat('W14x30') == 'tag code'
    assert T.cat('Living Room') == 'other text'

def _row(i, kinds, cls='ViewPlan', matched=8):
    return dict(id=i, cls=cls, text=dict(revit=10, matched=matched), findings=[dict(kind=k, what=w) for k, w in kinds])

def test_summarise(tmp_path):
    d = tmp_path / 'out'; (d / 'fileone.rvt').mkdir(parents=True); (d / 'file2026.rvt').mkdir()
    rows = [_row(1, [('text-missing', 'A'), ('text-missing', 'B'), ('text-moved', '2500'), ('longline-missing', 'x')]),
            _row(2, [('text-extra', 'Room')]), _row(3, [('text-missing', 'Q')], cls='ViewSheet'),
            dict(id=4, cls='ViewPlan', text={}, findings=[])]
    (d / 'fileone.rvt' / 'results.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    (d / 'file2026.rvt' / 'results.jsonl').write_text(json.dumps(_row(9, [('text-missing', 'Z')])) + '\n')
    s = T.summarise(str(d))
    assert s['views'] == 2 and s['revit'] == 20 and s['matched'] == 16
    assert s['cats']['grid letter']['text-missing'] == 2
    assert s['cats']['number (mm dim / level / grid)']['text-moved'] == 1
    assert s['cats']['other text']['text-extra'] == 1
    assert 'longline-missing' not in str(s['cats'])
    assert s['worst'][('grid letter', 'text-missing')] == [('fileone.rvt:1', 2)]

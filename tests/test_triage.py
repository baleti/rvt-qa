import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qa import triage as T

def mk(tmp):
    d = tmp / 'o' / 'file_one.rvt'; d.mkdir(parents=True)
    rows = [
        dict(id=1, name='A', cls='ViewPlan', score=40, findings=[dict(kind='text-missing'), dict(kind='text-missing'), dict(kind='bubble-missing'), dict(kind='geom-extra-element')]),
        dict(id=2, name='B', cls='ViewPlan', score=90, **{'pass': True}, findings=[]),
        dict(id=3, name='C', cls='View3D', score=10, findings=None),
        dict(id=4, name='D', cls='ViewPlan', score=None),
        dict(id=5, name='E', cls='ViewPlan', score=70, pass_vector=True, findings=[]),
    ]
    with open(d / 'results.jsonl', 'w') as fh:
        for r in rows: fh.write(json.dumps(r) + '\n')
    return str(tmp / 'o')

def test_triage_basic(tmp_path):
    o = mk(tmp_path); r = T.triage(o)
    assert [x['id'] for x in r] == [3, 1] and r[1]['file'] == 'file_one.rvt'
    assert r[1]['kinds'] == [('text-missing', 2), ('geom-extra-element', 1)] and r[0]['kinds'] == []

def test_noise_and_kinds(tmp_path):
    o = mk(tmp_path)
    assert ('bubble-missing', 1) in T.triage(o, include_noise=True)[1]['kinds']
    assert T.triage(o, kinds={'geom-extra-element'})[1]['kinds'] == [('geom-extra-element', 1)]

def test_format(tmp_path):
    t = T.format_rows(T.triage(mk(tmp_path)), 5).splitlines()
    assert t[0] == '2 failing views; worst 5:' and 'text-missingx2' in t[2] and t[1].startswith(' 10.0')

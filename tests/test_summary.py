import json, os, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qa import summary as S

def mk(tmp):
    for f, rows in {'a.rvt': [dict(id=1, name='x', cls='ViewPlan', score=90, **{'pass': True}), dict(id=2, name='y', cls='ViewPlan', score=60, pass_vector=True), dict(id=3, name='z', cls='View3D', score=10, reliable=False), dict(id=4, score=None)],
                    'b.rvt': [dict(id=1, name='q', cls='ViewPlan', score=80)]}.items():
        d = tmp / f; d.mkdir(parents=True)
        (d / 'results.jsonl').write_text('\n'.join(json.dumps(r) for r in rows) + '\n')
    return str(tmp)

def test_summarise(tmp_path):
    s = S.summarise(mk(tmp_path)); a = s['a.rvt']
    assert a['n'] == 3 and a['pass'] == 1 and a['pass_vector'] == 1 and a['unreliable'] == 1
    assert a['median'] == 60 and abs(a['p10'] - 20.0) < 1e-9
    assert [w[1] for w in a['worst']] == [3, 2, 1]
    assert a['by_cls']['ViewPlan'] == (2, 75.0) and a['by_cls']['View3D'] == (1, 10)
    assert s['b.rvt']['n'] == 1

def test_markdown(tmp_path):
    t = S.to_markdown(S.summarise(mk(tmp_path))).splitlines()
    assert t[0].replace(' ', '') == '|file|n|pass|+vec|unreliable|median|p10|'
    assert any(l.startswith('| a.rvt') for l in t) and 'TOTAL' in t[-1]

def test_cli(tmp_path):
    o = mk(tmp_path); here = os.path.join(os.path.dirname(__file__), '..', 'qa-summary')
    out = subprocess.run([sys.executable, here, o, '--json'], capture_output=True, text=True, check=True).stdout
    assert json.loads(out)['a.rvt']['n'] == 3

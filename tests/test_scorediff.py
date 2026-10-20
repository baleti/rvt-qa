import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qa import scorediff as S

def tree(tmp, name, rows):
    d = tmp / name; (d / 'f1.rvt').mkdir(parents=True)
    with open(d / 'f1.rvt' / 'results.jsonl', 'w') as fh:
        for r in rows: fh.write(json.dumps(r) + '\n\n')
    return str(d)

def test_load_skips_none_and_blank(tmp_path):
    d = tree(tmp_path, 'a', [dict(id=1, score=50.0, name='x'), dict(id=2, score=None)])
    r = S.load(d); assert list(r) == [('f1.rvt', 1)]

def test_diff_flips_medians_exit(tmp_path):
    a = S.load(tree(tmp_path, 'a', [dict(id=1, score=80, **{'pass': True}), dict(id=2, score=60), dict(id=3, score=70)]))
    b = S.load(tree(tmp_path, 'b', [dict(id=1, score=70, **{'pass': False}), dict(id=2, score=65), dict(id=4, score=1)]))
    rows = S.diff(a, b)
    assert [r[1][1] for r in rows] == [1, 2] and rows[0][0] == -10
    assert [r[1][1] for r in S.flips(rows)] == [1]
    assert S.medians(rows) == {'f1.rvt': (2, 70.0, 67.5)}
    assert S.only_counts(a, b) == (1, 1)
    assert S.exit_code(rows) == 1 and S.exit_code(rows, 11) == 0 and S.exit_code([]) == 0

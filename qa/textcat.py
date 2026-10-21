"""Summarise text-tier findings by category over non-sheet views."""

import collections
import glob
import json
import os
import re


def cat(t):
    if re.fullmatch(r"[-\d' \"/]+", t) and ("'" in t or '"' in t): return 'dimension string'
    if re.fullmatch(r"-?\d+(\.\d+)?", t): return 'number (mm dim / level / grid)'
    if re.fullmatch(r"[A-Z]{1,2}", t): return 'grid letter'
    if re.search(r'\d', t) and len(t) < 10: return 'tag code'
    return 'other text'


def summarise(results_dir):
    """Return totals, category counts, and the three worst views per kind."""
    rows = collections.defaultdict(collections.Counter)
    worst = collections.defaultdict(collections.Counter)
    nv = 0
    tot = collections.Counter()
    for f in glob.glob(os.path.join(results_dir, '*', 'results.jsonl')):
        if '2026' in f:
            continue
        with open(f) as source:
            for line in source:
                r = json.loads(line)
                if r.get('cls') == 'ViewSheet' or (r.get('text') or {}).get('matched') is None:
                    continue
                nv += 1
                tot['revit'] += r['text']['revit']
                tot['matched'] += r['text']['matched']
                for x in r['findings']:
                    if x['kind'] in ('text-missing', 'text-extra', 'text-moved', 'text-size'):
                        c = cat(x['what'])
                        rows[c][x['kind']] += 1
                        label = os.path.basename(os.path.dirname(f))[:12] + ':' + str(r['id'])
                        worst[(c, x['kind'])][label] += 1
    return {
        'views': nv,
        'revit': tot['revit'],
        'matched': tot['matched'],
        'cats': {c: dict(k) for c, k in rows.items()},
        'worst': {key: counts.most_common(3) for key, counts in worst.items()},
    }

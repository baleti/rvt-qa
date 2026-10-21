"""Compare per-view scores from two result trees."""

import glob
import json
import os
import statistics


def load(d):
    """Load scored rows keyed by (file, view id), skipping blank lines."""
    rows = {}
    for path in glob.glob(os.path.join(d, '*', 'results.jsonl')):
        file = os.path.basename(os.path.dirname(path))
        with open(path) as stream:
            for line in stream:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if row.get('score') is not None:
                    rows[(file, row['id'])] = row
    return rows


def diff(a, b):
    """Return shared rows sorted by score delta, breaking ties by key."""
    rows = [
        (b[key]['score'] - a[key]['score'], key, a[key], b[key])
        for key in sorted(set(a) & set(b))
    ]
    rows.sort(key=lambda row: row[0])
    return rows


def flips(rows):
    """Return rows whose pass status changed."""
    return [
        row for row in rows
        if bool(row[2].get('pass')) != bool(row[3].get('pass'))
    ]


def medians(rows):
    """Return the count and old/new score medians for each file."""
    scores = {}
    for _, key, old, new in rows:
        scores.setdefault(key[0], []).append((old['score'], new['score']))
    return {
        file: (
            len(scores[file]),
            statistics.median(old for old, _ in scores[file]),
            statistics.median(new for _, new in scores[file]),
        )
        for file in sorted(scores)
    }


def only_counts(a, b):
    """Return counts of keys found only in the old or new tree."""
    return len(set(a) - set(b)), len(set(b) - set(a))


def exit_code(rows, min_drop=5.0):
    """Return 1 when the first sorted delta meets the drop threshold."""
    return 1 if rows and rows[0][0] <= -min_drop else 0


def is_flap(old, new):
    """True when the image-registration score moved >= 0.1 while the DXF precision/recall stayed within 0.03: the score change is a QA artefact."""
    go, gn = old.get('geom') or {}, new.get('geom') or {}
    ro, rn = (old.get('image') or {}).get('reg_score'), (new.get('image') or {}).get('reg_score')
    return bool(go and gn and ro is not None and rn is not None and abs(ro - rn) >= 0.1
                and abs(go['precision'] - gn['precision']) < 0.03 and abs(go['recall'] - gn['recall']) < 0.03)


def real_drops(rows, min_drop=5.0):
    """Rows whose drop meets min_drop and is not a registration flap."""
    return [row for row in rows if row[0] <= -min_drop and not is_flap(row[2], row[3])]

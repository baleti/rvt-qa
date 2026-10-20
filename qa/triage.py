"""Rank and format failing views from an output directory."""
from collections import Counter
import json
from pathlib import Path


NOISE = {
    'bubble-missing', 'bubble-extra', 'longline-missing',
    'longline-extra', 'longline-extent',
}


def triage(outdir, include_noise=False, kinds=None) -> list[dict]:
    """Return failing views with counts of the selected finding kinds."""
    selected = None if kinds is None else set(kinds)
    rows = []
    for path in sorted(Path(outdir).glob('*/results.jsonl')):
        with path.open() as stream:
            for line in stream:
                result = json.loads(line)
                if (result.get('pass') or result.get('pass_vector')
                        or result.get('score') is None):
                    continue
                counts = Counter(
                    finding['kind']
                    for finding in result.get('findings') or []
                    if (include_noise or finding['kind'] not in NOISE)
                    and (selected is None or finding['kind'] in selected)
                )
                rows.append({
                    'score': result['score'],
                    'file': path.parent.name,
                    'id': result['id'],
                    'name': result.get('name', ''),
                    'cls': result.get('cls', ''),
                    'kinds': sorted(counts.items(), key=lambda item: (-item[1], item[0])),
                })
    # Preserve the original text-column ordering for equal scores.
    rows.sort(key=lambda row: (
        row['score'], row['file'][:14], row['id'], row['name'][:28],
        row['cls'], _top_kinds(row),
    ))
    return rows


def _top_kinds(row):
    return ', '.join(f'{kind}x{count}' for kind, count in row['kinds'][:3])


def format_rows(rows, n) -> str:
    """Format ranked rows in the command's traditional column layout."""
    lines = [f'{len(rows)} failing views; worst {n}:']
    for row in rows[:n]:
        lines.append(
            f"{row['score']:5.1f} {row['file'][:14]:14} {row['id']:8} "
            f"{row['name'][:28]:28} {row['cls']:10} {_top_kinds(row)}"
        )
    return '\n'.join(lines)

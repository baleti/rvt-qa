"""Summarise per-file scores from a results tree."""

import json
from pathlib import Path
from statistics import median


def _percentile(scores, fraction):
    """Interpolate a percentile from a nonempty, sorted score list."""
    position = (len(scores) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(scores) - 1)
    return scores[lower] + (scores[upper] - scores[lower]) * (position - lower)


def summarise(outdir):
    """Return scored-row statistics, retaining scores for aggregate reporting.

    Files without scored rows are omitted. Every scored row counts as a view.
    """
    summary = {}
    for path in sorted(Path(outdir).glob('*/results.jsonl')):
        rows = []
        with path.open() as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get('score') is not None:
                    rows.append(row)
        if not rows:
            continue
        scores = sorted(row['score'] for row in rows)
        by_cls = {}
        for row in rows:
            by_cls.setdefault(row.get('cls', ''), []).append(row['score'])
        summary[path.parent.name] = {
            'n': len(rows),
            'pass': sum(bool(row.get('pass')) for row in rows),
            'pass_vector': sum(
                bool(row.get('pass_vector')) and not bool(row.get('pass'))
                for row in rows
            ),
            'unreliable': sum(row.get('reliable') is False for row in rows),
            'median': median(scores),
            'p10': _percentile(scores, 0.1),
            'worst': [
                (row['score'], row['id'], row.get('name', ''))
                for row in sorted(rows, key=lambda row: row['score'])[:3]
            ],
            'by_cls': {
                cls: (len(values), median(values))
                for cls, values in by_cls.items()
            },
            'scores': scores,
        }
    return summary


def to_markdown(summary):
    """Format a summary with totals computed from all individual scores."""
    lines = [
        '| file | n | pass | +vec | unreliable | median | p10 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |',
    ]

    def format_row(file, stats):
        file = file.replace('|', r'\|').replace('\n', ' ')
        mid = '-' if stats['median'] is None else f"{stats['median']:.1f}"
        p10 = '-' if stats['p10'] is None else f"{stats['p10']:.1f}"
        return (
            f"| {file} | {stats['n']} | {stats['pass']} | "
            f"{stats['pass_vector']} | {stats['unreliable']} | {mid} | {p10} |"
        )

    for file in sorted(summary):
        lines.append(format_row(file, summary[file]))
    scores = sorted(
        score for stats in summary.values() for score in stats['scores']
    )
    total = {
        key: sum(stats[key] for stats in summary.values())
        for key in ('n', 'pass', 'pass_vector', 'unreliable')
    }
    total['median'] = median(scores) if scores else None
    total['p10'] = _percentile(scores, 0.1) if scores else None
    lines.append(format_row('TOTAL', total))
    return '\n'.join(lines)

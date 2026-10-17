import os, glob
GT = os.path.expanduser('~/rvt-research/gt_views')
def find_gt(rvt):
    """find the gt_views export directory of a .rvt (matches the FILE line of index.tsv by file name)"""
    base = os.path.basename(rvt).lower()
    for ix in glob.glob(GT + '/*/index.tsv'):
        try: first = open(ix, encoding='utf-8', errors='replace').readline().rstrip('\n').split('\t')
        except OSError: continue
        if first[0] == 'FILE' and first[1].replace('\\', '/').split('/')[-1].lower().endswith(base): return os.path.dirname(ix)
    return None
def views(gtdir):
    out = {}
    for line in open(os.path.join(gtdir, 'index.tsv'), encoding='utf-8', errors='replace'):
        c = line.rstrip('\n').split('\t')
        if c[0] == 'VIEW' and len(c) > 7:
            fl = [f for f in c[7].split(',') if f]
            for ext in ('pdf', 'png', 'dxf'):      # exports added after index.tsv was written
                if '%s.%s' % (c[1], ext) not in fl and os.path.exists(os.path.join(gtdir, '%s.%s' % (c[1], ext))): fl.append('%s.%s' % (c[1], ext))
            out[int(c[1])] = dict(id=int(c[1]), cls=c[2], vtype=c[3], name=c[4], scale=c[5], files=fl)
    return out

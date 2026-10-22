#!/bin/bash
# host1: render Snowdon view 600158 on the dev tree and report peak RSS (qa-view caps renders at 3 GB)
cd ~/src/rvt-qa
RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev python3 - <<'P'
import subprocess, resource, os, sys
f = os.path.expanduser('~/rvt-research/corpus/2024/43_Snowdon_Towers_Sample_Structural.rvt')
r = subprocess.run([os.path.expanduser('~/rvt-env/bin/python'), 'qa/render_ours.py', f, '/tmp/r600158', '600158'], capture_output=True, text=True)
print(r.stdout[-300:], r.stderr[-300:])
print('peak RSS MB', resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 1024)
P

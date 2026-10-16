#!/bin/bash
# host1: full QA refresh of the current rvt-sheets-dev tree: corpus dashboards + 2026 rosetta scenes. Results in out3/ (corpus) and out4/ (rosetta).
# Usage from host3:  ./h1queue.sh qaall ./h1all.sh     then:  rsync -a --exclude ours host1:src/rvt-qa/out3/ out3/ ; rsync ... out4/ ; ./qa-textcat out3 ; ./qa-index out3
cd ~/src/rvt-qa
python3 - <<'P'
import glob, os, shutil
for f in glob.glob('out3/*/results.jsonl') + glob.glob('out4/*/results.jsonl'): os.remove(f)
for d in glob.glob('out3/*/ours') + glob.glob('out4/*/ours'): shutil.rmtree(d)    # force a re-render of every view with the current dev tree
P
./h1dash3.sh
./h1ros.sh

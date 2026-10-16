#!/bin/bash
# remote-host: full QA refresh of the current rvt-sheets-dev tree: corpus dashboards + 2026 rosetta scenes. Results in out3/ (corpus) and out4/ (rosetta).
# Usage from remote-host:  ./h1queue.sh qaall ./h1all.sh     then:  rsync -a --exclude ours remote-host:src/rvt-qa/out3/ out3/ ; rsync ... out4/ ; ./qa-textcat out3 ; ./qa-index out3
cd ~/src/rvt-qa
rm -f out3/*/results.jsonl out4/*/results.jsonl 2>/dev/null   # fresh numbers for the new code (ours/ SVG caches are re-rendered when missing: delete out3/*/ours to force)
./h1dash3.sh
./h1ros.sh

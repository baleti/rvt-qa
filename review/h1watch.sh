#!/bin/bash
# host1: snapshot a tracked view. usage: h1run run watch --env rvt --dir ~/src/rvt-qa -- review/h1watch.sh FILE.rvt VIEWID LABEL [SHEETS_TREE]
cd ~/src/rvt-qa
export QA_RENDER_PY=$HOME/rvt-env/bin/python RVTSHEETS_DIR=${4:-$HOME/src/rvt-sheets-dev}
f=$(ls ~/rvt-research/corpus/*/$1 | head -1)
.venv/bin/python review/watch.py $HOME/review-compare "$f" $2 $3

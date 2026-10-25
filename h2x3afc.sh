#!/bin/bash
# remote-host: qa-dash of the paired studyx sheets, N files in parallel: ./h2studyx.sh LISTFILE [N]
cd ~/src/rvt-qa
export PYTHONPATH=$HOME/h2/sp:$HOME/h2/sp2:$HOME/h2/sp3:$HOME/h2/sp4 PATH=$HOME/h2/bin:$PATH
export QA_RENDER_MEM=7G QA_RENDER_PY=$HOME/rvt-env/bin/python RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev QA_GT_ROOT=$HOME/review-compare-studyx/gt
R=$HOME/review-compare-studyx; mkdir -p $R/out
cat "$1" | xargs -P ${2:-3} -I{} bash -c 'f="$HOME/studyx/office/studyx/{}"; $HOME/rvt-env/bin/python qa-dash "$f" --out '$R'/out --sheets 2>&1 | tail -2 >> '$R'/qa.log'
echo DONE > $R/qa.done

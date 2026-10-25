#!/bin/bash
# remote-host: pair a studyx model's PDFs to its sheets, then QA the sheets with the dev tree: ./h2studyx.sh REL_PATH_UNDER_studyx/office/studyx
cd ~/src/rvt-qa
export PYTHONPATH=$HOME/h2/sp:$HOME/h2/sp2:$HOME/h2/sp3:$HOME/h2/sp4 PATH=$HOME/h2/bin:$PATH
export QA_RENDER_MEM=8G QA_RENDER_PY=$HOME/rvt-env/bin/python RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev
f="$HOME/studyx/office/studyx/$1"; R=$HOME/review-compare-studyx; mkdir -p $R/gt $R/out
$HOME/rvt-env/bin/python qa-studyx "$f" $R/gt || exit 1
QA_GT_ROOT=$R/gt $HOME/rvt-env/bin/python qa-dash "$f" --out $R/out --sheets 2>&1 | tail -3

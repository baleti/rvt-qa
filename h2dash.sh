#!/bin/bash
# remote-host (via ~/src/rvt-sheets-dev/tools/h2dev.sh-like h2run): QA dashboards of ONE corpus file with the dev tree: ./h2dash.sh FILE.rvt OUTDIR(under ~/src/rvt-qa)
cd ~/src/rvt-qa
export PYTHONPATH=$HOME/h2/sp:$HOME/h2/sp2:$HOME/h2/sp3:$HOME/h2/sp4 PATH=$HOME/h2/bin:$PATH
export QA_RENDER_MEM=8G QA_RENDER_PY=$HOME/rvt-env/bin/python RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev
$HOME/rvt-env/bin/python qa-dash "$1" --out "$2" --sheets 2>&1 | tail -3

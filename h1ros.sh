#!/bin/bash
# host1: QA dashboards (dev tree render) for the 2026 view rosetta scenes with Revit exports -> out4/
cd ~/src/rvt-qa
(test -x .venv/bin/python || python3 -m venv .venv) && .venv/bin/pip -q install numpy opencv-python-headless scikit-image pillow scipy ezdxf pymupdf
export QA_RENDER_PY=$HOME/rvt-env/bin/python RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev
for d in ~/rvt-research/gt_views/2026_*/; do
  [ -f $d/index.tsv ] || continue
  rte=$(head -1 $d/index.tsv | cut -f2 | sed 's/.*_rte_//'); f=~/rvt-research/rosetta/$rte
  [ -f "$f" ] || { echo NOFILE $rte; continue; }
  .venv/bin/python qa-dash $f --out out4 --sheets 2>&1 | tail -2
done

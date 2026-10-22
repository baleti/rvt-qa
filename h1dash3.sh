#!/bin/bash
# host1: render views with the dev tree (rvt-env python) and run the full-tier QA dashboards into out3/
cd ~/src/rvt-qa
(test -x .venv/bin/python || python3 -m venv .venv) && .venv/bin/pip -q install numpy opencv-python-headless scikit-image pillow scipy ezdxf pymupdf
export QA_RENDER_MEM=6G QA_RENDER_PY=$HOME/rvt-env/bin/python RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev
for f in 20_Residential_Sample_Project 19_Commercial_Sample_Project 18_rst_basic_sample_project; do
  p=$(ls ~/rvt-research/corpus/*/$f.rvt | head -1)
  .venv/bin/python qa-dash $p --out out3 --sheets 2>&1 | tail -3
done

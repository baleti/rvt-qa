#!/bin/bash
# host1: re-run QA dashboards (cached SVGs in out2/*/ours, fresh results) with all tiers
cd ~/src/rvt-qa
(test -x .venv/bin/python || python3 -m venv .venv) && .venv/bin/pip -q install numpy opencv-python-headless scikit-image pillow scipy ezdxf pymupdf
python3 - <<'P'
import glob,json,os
for f in glob.glob('out2/*/results.jsonl'):
    R=[l for l in open(f) if '"error": "' not in l]; open(f,'w').writelines(R)
P
for f in 20_Residential_Sample_Project 19_Commercial_Sample_Project 18_rst_basic_sample_project; do
  p=$(ls ~/rvt-research/corpus/*/$f.rvt | head -1)
  .venv/bin/python qa-dash $p --out out2 --sheets 2>&1 | tail -3
done

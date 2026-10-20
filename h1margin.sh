#!/bin/bash
# host1: reg_margin probe on the flap view 1292652 (cached ours svg in out3)
cd ~/src/rvt-qa
f=$(ls ~/rvt-research/corpus/*/18_rst_basic_sample_project.rvt|head -1)
.venv/bin/python qa-view $f 1292652 --out out_margin --svg out3/18_rst_basic_sample_project.rvt/ours/1292652.svg 2>&1 | tail -5
python3 -c "
import json,glob
for p in glob.glob('out_margin/**/*.json',recursive=True): print(p, json.load(open(p)).get('image'))"

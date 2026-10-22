#!/bin/bash
# owners of the biggest extra elements in Commercial elevations (29181 North, 29191 West, 29201 South)
cd ~/src/rvt-qa; export RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev
p=$(ls ~/rvt-research/corpus/*/19_Commercial_Sample_Project.rvt | head -1)
$HOME/rvt-env/bin/python qa/elem_info.py $p 148023 146778 152359 151276 157834 155712 148624 151964 146898 148081 2>&1 | tail -14

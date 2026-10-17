#!/bin/bash
cd ~/src/rvt-qa; export RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev
p=$(ls ~/rvt-research/corpus/*/19_Commercial_Sample_Project.rvt | head -1)
$HOME/rvt-env/bin/python qa/elem_info.py $p 147722 179262 182970 2>&1 | tail -8

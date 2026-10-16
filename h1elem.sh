#!/bin/bash
cd ~/src/rvt-qa; export RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev
for spec in "20_Residential_Sample_Project 158021 206435 228877 234610 234684 234150 234712 234330 9946" "19_Commercial_Sample_Project 148024 146944 146892 146898"; do
  set -- $spec; p=$(ls ~/rvt-research/corpus/*/$1.rvt | head -1); shift
  echo "== $p"; $HOME/rvt-env/bin/python qa/elem_info.py $p "$@" 2>&1 | tail -15
done

#!/bin/bash
cd ~/src/rvt-qa; export RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev
for spec in "19_Commercial_Sample_Project 147722 216070 148023 156625 157835 148624 155712 146944" "18_rst_basic_sample_project 1436861 1096421 1417473 1436528"; do
  set -- $spec; p=$(ls ~/rvt-research/corpus/*/$1.rvt | head -1); shift
  echo "== $p"; $HOME/rvt-env/bin/python qa/elem_info.py $p "$@" 2>&1 | tail -10
done

#!/bin/bash
cd ~/src/rvt-qa; export RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev
p=$(ls ~/rvt-research/corpus/*/20_Residential_Sample_Project.rvt | head -1)
$HOME/rvt-env/bin/python qa/view_crop.py $p 29154 29181 32 36 2>&1 | tail -8

#!/bin/bash
# host3-light: render missing sheet SVGs (3G cap inside qa-view) and compare, one file at a time
cd ~/src/rvt-qa
for f in 20_Residential_Sample_Project 19_Commercial_Sample_Project 18_rst_basic_sample_project; do
  p=$(ls ~/rvt-research/corpus/*/$f.rvt | head -1)
  systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0 nice -n 19 .venv/bin/python qa-dash $p --sheets 2>&1 | tail -30
done

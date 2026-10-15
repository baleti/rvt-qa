#!/bin/bash
# sequential capped host3 run of the corpus dashboards; resumable
cd ~/src/rvt-qa
for f in 20_Residential_Sample_Project 19_Commercial_Sample_Project 18_rst_basic_sample_project; do
  systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 -p CPUQuota=100% nice -n 19 .venv/bin/python qa-dash ~/rvt-research/corpus/2020/$f.rvt >> /tmp/claude-1000/dashall.log 2>&1
  echo "EXIT $f $?" >> /tmp/claude-1000/dashall.log
done

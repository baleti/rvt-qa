#!/bin/bash
# QA dashboards for the 2026 view rosetta scenes that have Revit exports
cd ~/src/rvt-qa
for d in ~/rvt-research/gt_views/2026_*/; do
  [ -f $d/index.tsv ] || continue
  n=$(head -1 $d/index.tsv | cut -f2 | sed 's/.*\\//; s/^ve_[0-9]*_//; s/_rte_.*//; s/_rvt_.*//')
  rte=$(head -1 $d/index.tsv | cut -f2 | sed 's/.*_rte_//')
  f=~/rvt-research/rosetta/$rte
  [ -f "$f" ] || { echo "NOFILE $rte" >> /tmp/claude-1000/dashros.log; continue; }
  systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 -p CPUQuota=100% nice -n 19 .venv/bin/python qa-dash $f --sheets >> /tmp/claude-1000/dashros.log 2>&1
  echo "EXIT $rte $?" >> /tmp/claude-1000/dashros.log
done
echo ALLDONE >> /tmp/claude-1000/dashros.log

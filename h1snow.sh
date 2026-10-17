#!/bin/bash
# host1: QA dashboards for the Snowdon Towers samples (2024 + 2026 exports) into out6/
cd ~/src/rvt-qa
rm -rf "$HOME/src/rvt-qa/out6"   # qa-dash skips views that already have results and reuses cached SVGs: start fresh
export QA_RENDER_PY=$HOME/rvt-env/bin/python RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev
for f in 43_Snowdon_Towers_Sample_Structural 46_Snowdon_Towers_Sample_Facades 55_Snowdon_Towers_Sample_Structural 58_Snowdon_Towers_Sample_Facades; do
  p=$(ls ~/rvt-research/corpus/*/$f.rvt 2>/dev/null | head -1); [ -z "$p" ] && continue
  .venv/bin/python qa-dash $p --out out6 --sheets 2>&1 | tail -3
done

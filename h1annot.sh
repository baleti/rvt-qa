#!/bin/bash
# host1: qa-view of Snowdon 55 sheets with the annot tree (text baseline/font numbers vs Revit PDFs)
cd ~/src/rvt-qa
export QA_RENDER_PY=$HOME/rvt-env/bin/python RVTSHEETS_DIR=$HOME/src/rvt-sheets-annot
p=$(ls ~/rvt-research/corpus/*/55_Snowdon_Towers_Sample_Structural.rvt | head -1)
rm -rf "$HOME/src/rvt-qa/out12"
for v in 921485 924500 779980 871873; do .venv/bin/python qa-view $p $v --out out12/55 2>&1 | head -2; done

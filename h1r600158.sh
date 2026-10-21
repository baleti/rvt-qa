#!/bin/bash
# host1: why does Snowdon view 600158 fail to render on the dev tree?
cd ~/src/rvt-qa
RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev $HOME/rvt-env/bin/python qa/render_ours.py $(ls ~/rvt-research/corpus/2024/43_Snowdon_Towers_Sample_Structural.rvt) /tmp/r600158 600158 2>&1 | tail -20

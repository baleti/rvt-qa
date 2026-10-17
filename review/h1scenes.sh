#!/bin/bash
# host1: render our views of the writer scenes / rosettas and build pairs against c3-writer's Revit PNGs (~/review-compare/revit)
cd ~/src/rvt-qa
export QA_RENDER_PY=$HOME/rvt-env/bin/python RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev
.venv/bin/python review/build_scenes.py $HOME/review-compare "$@" 2>&1 | tail -80

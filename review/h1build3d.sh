#!/bin/bash
# host1: pair Revit 3D PNGs with viewer shots and score (review/build3d.py) + rebuild INDEX.html
cd ~/src/rvt-qa
.venv/bin/python review/build3d.py $HOME/review-compare 2>&1 | tail -3
python3 review/index.py $HOME/review-compare

#!/bin/bash
# host1: build review pairs for spec $1 (default spec1.json) into ~/review-compare
cd ~/src/rvt-qa
.venv/bin/python review/build.py review/${1:-spec1.json} $HOME/review-compare 2>&1 | tail -80

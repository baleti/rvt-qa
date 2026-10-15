#!/bin/bash
# retry-start the QA dashboard job on host1 until it is accepted
for i in $(seq 1 60); do
  out=$(~/.local/share/offload/h1run run qa-dash20 --env rvt --dir ~/src/rvt-qa -- bash -c 'cd ~/src/rvt-qa && (test -x .venv/bin/python || python3 -m venv .venv) && .venv/bin/pip -q install numpy opencv-python-headless scikit-image pillow pytesseract scipy ezdxf pymupdf && .venv/bin/python qa-dash ~/rvt-research/corpus/2020/20_Residential_Sample_Project.rvt' 2>&1)
  echo "$out" | grep -q busy || { echo "$out"; exit 0; }
  sleep 120
done

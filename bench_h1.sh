#!/bin/bash
# host1 benchmark job: OCR engines on our own render (ground truth = SVG texts). Creates .venv-vlm on host1 if missing. Run via h1run only.
cd ~/src/rvt-qa
if [ ! -x .venv-vlm/bin/python ]; then
  python3 -m venv .venv-vlm
  .venv-vlm/bin/pip -q install torch torchvision --index-url https://download.pytorch.org/whl/cpu
  .venv-vlm/bin/pip -q install easyocr python-doctr pytesseract opencv-python-headless numpy scipy
fi
mkdir -p out/bench
for w in 3000 6000; do
  .venv-vlm/bin/python qa/bench_ocr.py out/20_Residential_Sample_Project.rvt/ours/32.svg $w tess easyocr doctr 2>&1 | grep -v -i -E 'warn|Downloading|%\|' | tee -a out/bench/ocr.txt
done

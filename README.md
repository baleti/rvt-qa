# rvt-qa: automated visual-diff QA for rvt-sheets views

Goal: find simple view/sheet defects BEFORE spending Claude tokens. Local only, no external services.

## Tools
- `qa-view FILE.rvt VIEWID [--gt DIR] [--svg OURS.svg]` : renders our view (rvt-sheets venv, capped 3 GB), compares with Revit's PNG + DXF export (default dir ~/rvt-research/gt_views/<match on FILE line of index.tsv>), prints PASS/FAIL, summary, ranked findings; crops (Revit | ours | overlay red=Revit only, cyan=ours only) in out/<file>/diff/.
- `qa-dash FILE.rvt... [--sheets] [--max N]` : all exported views of a file -> out/<file>/results.jsonl + dashboard.html. Heavy: run on remote-host (`./h1dash.sh`).

## Method (cheap numeric first)
1. Vector text diff (qa/vec.py): Revit DXF TEXT/MTEXT vs our SVG `<text>`; registration by voting on identical strings (translation only; units feet*304.8/scale, y flip). Reports missing / extra / moved / wrong-size text with layer. Calibrated: our font-size = 1.389 x DXF text height.
2. Image diff (qa/imgdiff.py): multi-scale + translation registration by correlation of blurred ink maps (our crop/margins differ from Revit's FitToPage, scale range 0.5..1.8), ink precision/recall at 3/6 px, SSIM, 6x9 cell heatmap of missing/extra ink, long-line (Hough) and circle detection helpers.
3. OCR (qa/ocr.py, tesseract): WORKS POORLY on Revit PNGs (text is 5-8 px high; 4 of 28 words matched on the L2 reference). Use the DXF text instead; OCR only for PNG-only references.

## Pass rule (provisional)
ink P/R at 6 px >= 0.85 and text recall >= 0.9.

## Status
See PROGRESS.md.

## Model survey (CPU, local)
- SmolVLM-256M-Instruct (transformers, torch CPU, 4 threads): 64 s per two-image crop, answer is generic ("plan view of a building"), cannot list missing labels. NOT useful for diffs at this size. Larger VLMs (Qwen2-VL-2B) would need remote-host and are expected to be too slow/inexact for per-crop diffs; numeric tiers (DXF text, ink maps, Hough lines) are faster and exact, so VLMs are left for final human/Claude crop review only.
- tesseract OCR on Revit PNGs (~1200 px wide): 4/28 words matched; unusable at that resolution. DXF text is the ground truth for text.

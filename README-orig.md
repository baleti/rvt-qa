# rvt-qa: automated visual-diff QA for rvt-sheets views

Goal: find simple view/sheet defects BEFORE spending Claude tokens. Local only, no external services.

## What worked, in order of value (summary)
1. Vector text diff against Revit DXF (qa/vec.py): exact, fast (<1 s), 94% of Revit texts matched on the corpus; catches missing/moved/size/wrapped-line text and attributes to layers. Needs per-line splitting of wrapped text, rotated left edge and registration re-centring (all done).
2. Vector geometry diff (qa/vecgeom.py): DXF lines/curves vs our SVG paths in mm, per-layer recall, chamfer/Hausdorff, extra ink per our element id. ~20 s, 0.6 GB. Best source of actionable "element X draws ink Revit does not".
3. Image diff with multi-scale registration (qa/imgdiff.py): ink P/R, SSIM, cell heatmap, long lines, bubbles; needed for views without usable DXF.
4. Combined 0-100 score and owner-routed ranked defect list (defects_<id>.md) with Revit | ours | overlay crops.
Did not help / skipped: OCR (tesseract/EasyOCR/docTR recall 0.4 on our own render, vector text is the reference), PaddleOCR (no wheel for Python 3.14), sheet DXFs (viewports at model scale, not comparable; use PDFs), whole-sheet line/bubble detection (noise). Embedding/VLM tiers are only for flagged tiles on host1 (see survey).

## Tools
- `qa-view FILE.rvt VIEWID [--gt DIR] [--svg OURS.svg]` : renders our view (rvt-sheets venv, capped 3 GB), compares with Revit's PNG + DXF export (default dir ~/rvt-research/gt_views/<match on FILE line of index.tsv>), prints PASS/FAIL, summary, ranked findings; crops (Revit | ours | overlay CYAN=Revit only, RED=ours only) in out/<file>/diff/.
- `qa-dash FILE.rvt... [--sheets] [--max N]` : all exported views of a file -> out/<file>/results.jsonl + dashboard.html. Heavy: run on host1 (`./h1dash.sh`).

## Method (cheap numeric first)
1. Vector text diff (qa/vec.py): Revit DXF TEXT/MTEXT vs our SVG `<text>`; registration by voting on identical strings (translation only; units feet*304.8/scale, y flip). Reports missing / extra / moved / wrong-size text with layer. Calibrated: our font-size = 1.389 x DXF text height.
2. Image diff (qa/imgdiff.py): multi-scale + translation registration by correlation of blurred ink maps (our crop/margins differ from Revit's FitToPage, scale range 0.5..1.8), ink precision/recall at 3/6 px, SSIM, 6x9 cell heatmap of missing/extra ink, long-line (Hough) and circle detection helpers.
3. OCR (qa/ocr.py, tesseract): WORKS POORLY on Revit PNGs (text is 5-8 px high; 4 of 28 words matched on the L2 reference). Use the DXF text instead; OCR only for PNG-only references.

## Pass rule (provisional)
ink P/R at 6 px >= 0.85 and text recall >= 0.9.

## Status
See PROGRESS.md.

## Model survey (CPU, local)
- SmolVLM-256M-Instruct (transformers, torch CPU, 4 threads): 64 s per two-image crop, answer is generic ("plan view of a building"), cannot list missing labels. NOT useful for diffs at this size. Larger VLMs (Qwen2-VL-2B) would need host1 and are expected to be too slow/inexact for per-crop diffs; numeric tiers (DXF text, ink maps, Hough lines) are faster and exact, so VLMs are left for final human/Claude crop review only.
- tesseract OCR on Revit PNGs (~1200 px wide): 4/28 words matched; unusable at that resolution. DXF text is the ground truth for text.

## Sheet PDF tier (qa/pdfvec.py)
For ViewSheet exports with a Revit PDF (2022+ scenes, page = paper, 1 pt = 0.3528 mm): text spans (content, size in pt, font, position compared at the SVG's own text-anchor) and line weight inventory (stroke length per width class, both sides). Findings: text-missing/extra/moved/size, lineweight-missing. 2026_view_sheet_var sheet 303711: Revit 46 text spans vs ours 26 (21 matched; title-block consultant/address blocks missing; 3 labels 0.57x size), line weights 0.10 mm and 0.25 mm present on both sides (0.25 mm length identical 5078 mm, 0.10 mm 6359 vs 7209 mm).

## Survey results (measured, host3, 4 threads, nice 19)
Tile benchmark (qa/bench_tiles.py, Residential view 32, 6x9 tiles of the aligned pair; score = Spearman rank correlation with the ink-diff (missing+extra px) tile score; cost for all 54 tiles):
| method | secs | Spearman | verdict |
|---|---|---|---|
| SSIM per tile | 0.4 | 0.33 | weak (white areas dominate) |
| MS-SSIM (3 scales) | 0.6 | 0.57 | ok |
| Canny edge chamfer | 0.2 | 0.66 | good and nearly free |
| LPIPS (AlexNet, 128 px tiles) | 3.4 | 0.79 | best tile ranker, cheap on CPU |
| DINOv2-small CLS per tile | 45 | 0.52 | slow, no better than chamfer |
Take-away: rank tiles with LPIPS + edge chamfer; DINOv2 patch embeddings not worth it at this size.
Text compare fix (2026-10-15, from c2-annot): SVG text-anchor (end/middle) is converted to a left edge and DXF texts split into several MTEXT (e.g. 'vision' 'lite') match inside our longer string: Residential view 32 matched 52 -> 110 of 126, median position error 4.2 -> 1.3 mm.

OCR benchmark (ground truth = the SVG's own text, our render of Residential view 32 at 3000 / 6000 px wide, 204 words >= 5 px tall):
| engine | width | secs | GT recall | precision |
|---|---|---|---|---|
| tesseract --psm 11 | 3000 | 3.9 | 0.28 | 0.36 |
| tesseract --psm 11 | 6000 | 6.6 | 0.39 | 0.55 |
EasyOCR and docTR exceeded the 3 GB host3 cap (OOM-killed, 3 attempts): MEMORY RULE from the orchestrator: no ML/OCR benchmarks on host3; they run on host1 via `h1run run qaocr -- ./bench_h1.sh` (results in out/bench/ocr.txt). PaddleOCR: no paddlepaddle wheel for Python 3.14 (pip: no matching distribution), skipped. Measured on host1 (CPU, our render of Residential view 32, 204 GT words from the SVG, 3000 / 6000 px wide): EasyOCR 32 s / 28 s, recall 0.41 / 0.41, precision 0.53 / 0.49; docTR 8.6 s / 6.5 s, recall 0.43 / 0.44, precision 0.70 / 0.70. Tesseract is not installed on host1 (host3 numbers above). Doubling resolution did not help; docTR is 4x faster and more precise. Conclusion: OCR stays a fallback, vector text (DXF/PDF) is the reference.

## Vector geometry tier (qa/vecgeom.py, host3-light: 0.6 GB RSS, ~20 s per view)
Revit DXF primitives (per layer) vs our SVG paths (per element id) in paper mm, both sampled every 0.25 mm; scale known (304.8/view scale), translation by FFT + median ICP. Reports recall per Revit layer, extra-ink ranking per OUR element id (precision offenders, ids can be looked up in the reader), chamfer and Hausdorff-95 in mm, overall P/R at 0.6 mm. Residential view 32: recall 0.94, precision 0.73, chamfer 1.87 mm, Hausdorff95 26 mm; weakest layers A-AREA-IDEN 0.21, S-STRS-ANNO 0.26, A-DETL-MBND 0.58; elements 234610 / 234684 / 234150 / 206435 draw 450-640 mm of ink Revit does not have. Each qa-view run also writes out/<file>/defects_<view>.md (ranked table, area, crops).

## Corpus status (dev cb53624, qaall5, host1, all tiers)
| file | views | median combined score |
|---|---|---|
| rst basic | 45 | 81.6 |
| Commercial | 28 | 78.7 |
| Residential | 29 | 78.4 |

Snowdon Towers (2024 and 2026 agree within 0.5): Structural 52 views median 69.0, Facades 10 views median 66.

Lesson: vecgeom must honour the SVG clipPath (crop region); ignoring it made detail views look 10-18x over-drawn and cost up to 40 score points. Always cross-check a QA number against an independent tool (c5-sheets compare_dxf) before reporting it.

Text tier: 1220 of 1295 Revit texts matched (94%) over 43 views; `qa-textcat out3` breaks findings down by category. Dimension strings are not in Revit's DXF, so ours-only ones are informational.

## Refreshing everything after a rvt-sheets release
1. `rsync -a --exclude '.venv*' --exclude __pycache__ ~/src/rvt-sheets-dev/ host1:src/rvt-sheets-dev/`
2. `./h1queue.sh qaall ./h1all.sh` (queues on host1, waits for 11 GB free)
3. compare with the previous run: `./qa-scorediff out_old out_new` (drops, gains, pass flips, DXF P/R).
4. pull: `rsync -a --exclude ours host1:src/rvt-qa/out3/ out3/` (same for out4), then `./qa-textcat out3`, `./qa-index out3`, `./qa-regress --dev` for the golden set.

## Latest sweep (qaall11, dev 564062d, 2026-10-18)
Medians: rst 85.7, Commercial 82.1, Residential 80.8; Snowdon 43/55 Structural 75.1/75.0, 46/58 Facades 80.1/78.5 (all up 5-12 points; Learn/How-to cover sheets now PASS at ~93). Open: Residential 258720 'at grade' -7.2 (image tier). VLM survey (Qwen2-VL, CLIP) deliberately not pursued: SmolVLM was useless and the vector tiers are exact; revisit only if host1 has 11 GB free and a concrete need.

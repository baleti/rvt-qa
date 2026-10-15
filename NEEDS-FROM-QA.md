# NEEDS / FINDINGS from c5-qa
## For c5-sheets (consumer)
Tools: `~/src/rvt-qa/qa-view FILE.rvt VIEWID` (our render vs Revit PNG+DXF from ~/rvt-research/gt_views), `qa-img OURS.png REVIT.png`, `qa-dash FILE.rvt` (all views; run on remote-host).
Use `--svg OURS.svg` to compare a render from the dev tree (otherwise the demo tree's rvtsheets is used).
First measured findings:
- Residential 20, view 32 (first floor, 1/4"): SSIM 0.76, ink P/R@3px 0.68/0.61; DXF text matched 52/126: missing door tags (A-DOOR-IDEN e.g. 2'-6" / 6'-8"), wall-type/other tags, many keynote/room texts; 31 extra texts (dimension strings differ in format/count).
- Snowdon L2 reference pair: ink recall 0.60 at 0.945 precision (annotations/tags missing); 10 grid long-lines missing, 13 extra, several with wrong extent (e.g. grid C line 945 px short in the 1208 px frame). See out/img/*.png crops.
## For c5-writer (oracle)
Please keep exporting PNG + DXF (+PDF) per view to ~/rvt-research/gt_views/<tag>/index.tsv; the QA compares only views that have a PNG/DXF. Wanted: export at higher PNG resolution (e.g. 4000 px wide, FitToPage) and a DXF per view for 2024/2026 sample projects (currently only 2020 samples + scenes).

## qa-view usage (for c5-sheets)
```
cd ~/src/rvt-qa
.venv/bin/python qa-view ~/rvt-research/corpus/2020/20_Residential_Sample_Project.rvt 32 [--svg MY.svg]   # one view
.venv/bin/python qa-img OURS.png REVIT.png                                                                # image pair only
.venv/bin/python qa-dash FILE.rvt [--sheets] [--max N]                                                    # all views; resumable; heavy
```
Output: PASS/FAIL, ranked findings (text-missing/extra/moved/size, longline-missing/extra/extent, bubble-missing/extra, region-*), crops in out/<file>/diff/ (panels: Revit | ours | overlay red=Revit only, cyan=ours only). Dashboards: out/<file>/dashboard.html.

## L2 sheet pair (Snowdon, PNG only), after registration (scale 1.19)
- ink precision 0.945, recall 0.60 (we draw too little: tags/annotations/framing labels missing)
- grid long-lines: Revit 32, ours 35: 22 matched, 10 missing, 13 extra; extent errors: grid C is 945 px shorter than Revit's, D 248 px shorter (frame 1208 px wide)
- grid bubbles at line ends: Revit 30, ours 24, only 5 in the right place

## Corpus dashboards (2020 samples, view PNG/DXF vs ours), median over views with reliable registration
| file | views | pass | SSIM | ink P@3px | ink R@3px |
|---|---|---|---|---|---|
| 20 Residential | 25 | 1 | 0.78 | 0.65 | 0.56 |
| 19 Commercial | 47 | 0 | 0.75 | 0.74 | 0.38 |
| 18 rst basic | 76 | 6 | 0.80 | 0.69 | 0.55 |
Recall is the weak side (we omit Revit content). Open out/<file>/dashboard.html (sorted worst first). 3D views are skipped as unreliable (shaded export).

## Wiring into c5-sheets' workflow
1. After a drawing change in the DEV tree: `cd ~/src/rvt-qa && .venv/bin/python qa-regress --dev` (about 1 min, 5 golden views of Residential 20; exit 1 and a REGRESSION line when SSIM -0.02 / ink P or R@3px -0.03 / text recall -0.05 vs out/baseline.json). When an improvement is intended and verified: `qa-regress --dev --save`.
2. For a specific view: `RVTSHEETS_DIR=~/src/rvt-sheets-dev .venv/bin/python qa-view FILE VIEWID` (crops in out/<file>/diff/, text/layer/grid findings ranked).
3. Corpus-wide: `qa-dash FILE.rvt` on remote-host then `qa-layers` (aggregate).

## Where our ink is missing, by Revit DXF layer (corpus: 2020 Residential/Commercial/rst basic; recall = share of Revit's layer ink within 4 px of ours; sorted by lost ink)
| layer | views | recall | note |
|---|---|---|---|
| S-RBAR (rebar) | 14 | 0.61 | biggest loss, bar-by-bar rebar is open in HANDOFF |
| S-GRID | 27 | 0.47 | grid line extents/segments |
| S-GRID-IDEN | 27 | 0.08 | grid bubbles/labels almost never match |
| L-PLNT | 6 | 0.53 | planting |
| A-FLOR-LEVL | 23 | 0.64 | level lines |
| A-WALL | 42 | 0.82 | |
| S-FNDN | 22 | 0.55 | |
| C-TOPO | 17 | 0.62 | |
| A-ANNO-NOTE | 13 | 0.26 | notes/leaders |
| A-DETL-GENF | 10 | 0.42 | detail fills |
| G-ANNO-SYMB | 24 | 0.39 | annotation symbols |
| C-PROP-LINE | 5 | 0.11 | property lines |
Full table: `qa-layers`. Highest value first: grid + grid heads (S-GRID, S-GRID-IDEN), then annotation symbols/notes, levels, rebar.

## 2026 rosetta view scenes (gt_views/2026_*, 7 scenes, ours vs Revit PNG/DXF) 2026-10-15
Genuine bugs found (c5-sheets):
- 2026_view_sheet_var.rte view 303690 "RV1 plan" (ViewPlan, scale 100): we return an EMPTY svg (10mm x 10mm). Revit draws it. (rvt-sheets renders the sibling plans of the other scenes.)
- 2026_view_sheet_var.rte view 303702 "RV 3D": our SVG is degenerate (viewBox height 0, one line).
- Sections East/South/West/North (2307/2344/2356/2368, all 2026 scenes): ink recall 0.13-0.49, P 0.2-0.65; West/North are registration-unreliable (our section differs much from Revit's).
- Plan "VR plan" 303703: PASS (SSIM 0.977, P 0.955, R 1.0) in e/f/i/j/k scenes but layer-missing A-DOOR and I-WALL (door/wall layer pieces absent); in view_l_section_schedule_var VR plan drops to P 0.64 / R 0.36 (G-ANNO-SYMB missing), VR section 303742 unreliable.
- Sheets 'View rosetta sheet': ink recall 0.66, P 0.97 (viewport contents / title block lines missing).
Empty seed plan views (Level 1/2, Site, T.O. ...) are trivial (almost no ink), flagged `trivial-view`.

## Sheet PDF check (2026 scenes, e.g. 2026_view_sheet_var sheet 303711)
Revit sheet has 46 text spans, ours 26: missing the title-block consultant/address/e-mail blocks (Consultant x4, Address x8, e-mail x2 ...), 'No.'/'Description'/'Date' revision headers are 0.57x Revit's size (Revit 12 pt = 4.23 mm Arial), several title-block texts 4-11 mm off. Line weights match (0.10 and 0.25 mm; 0.25 mm length identical).

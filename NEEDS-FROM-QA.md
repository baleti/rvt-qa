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

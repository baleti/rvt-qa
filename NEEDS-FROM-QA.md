# NEEDS / FINDINGS from c5-qa
## For c5-sheets (consumer)
Tools: `~/src/rvt-qa/qa-view FILE.rvt VIEWID` (our render vs Revit PNG+DXF from ~/rvt-research/gt_views), `qa-img OURS.png REVIT.png`, `qa-dash FILE.rvt` (all views; run on remote-host).
Use `--svg OURS.svg` to compare a render from the dev tree (otherwise the demo tree's rvtsheets is used).
First measured findings:
- Residential 20, view 32 (first floor, 1/4"): SSIM 0.76, ink P/R@3px 0.68/0.61; DXF text matched 52/126: missing door tags (A-DOOR-IDEN e.g. 2'-6" / 6'-8"), wall-type/other tags, many keynote/room texts; 31 extra texts (dimension strings differ in format/count).
- Snowdon L2 reference pair: ink recall 0.60 at 0.945 precision (annotations/tags missing); 10 grid long-lines missing, 13 extra, several with wrong extent (e.g. grid C line 945 px short in the 1208 px frame). See out/img/*.png crops.
## For c5-writer (oracle)
Please keep exporting PNG + DXF (+PDF) per view to ~/rvt-research/gt_views/<tag>/index.tsv; the QA compares only views that have a PNG/DXF. Wanted: export at higher PNG resolution (e.g. 4000 px wide, FitToPage) and a DXF per view for 2024/2026 sample projects (currently only 2020 samples + scenes).

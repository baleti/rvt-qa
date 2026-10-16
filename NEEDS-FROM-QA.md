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

## Combined score and routing (new)
`qa-view` prints `SCORE n/100` (0.30 ink recall@6px + 0.20 precision@6px + 0.25 DXF text recall + 0.10 grid-line match + 0.15 layer-ink recall, weights renormalised over available tiers) and every finding has `-> area` (annotations/text, grids, line weights, layer X, view not rendered, drawing content) so work can be routed without looking at images. Residential view 32 now: 84.5/100 (text recall 0.87, ink R/P@6px 0.79/0.94).

## Update (geometry crops)
- defects_<view>.md now lists geom-extra-element / geom-layer-missing with a Revit | ours | overlay crop. Residential view 32: elements 234610/234684/234150/234712/234330 are dimension tick/witness ink Revit does not draw there (check dimension tick and witness-line placement); layers A-AREA-IDEN, A-DETL-MBND are under-drawn.
- Full-tier dashboards (out2/, remote-host job qadash2) are queued; results land in ~/src/rvt-qa/out2/<file>/dashboard.html.

## Sheets ranked (remote-host image tier)
See ~/src/rvt-qa/sheets_ranked.md: 16 sheets, worst Column Schedules (rst basic) 54.8, Cover Sheet (Commercial) 59.7, Footing Detail 72.4. Typical defect: ink recall 0.5-0.7 (missing drawing regions) with precision 0.9+. Door tag / dimension string text on sheets needs sheet PDFs from Revit (requested in NEEDS-FROM-ORACLE.md); sheet DXFs are not comparable.

## Sheet 1457199 Column Schedules (rst basic) overlay reading (red = Revit only, cyan = ours only)
- Two graphical column schedule grids (top and left-middle) are drawn by us but appear as cyan (ours-only) against Revit's export; our output contains the placeholder text "[graphical_column_schedule view not drawn yet: Graphical Column Schedule]" at that spot, so check whether Revit actually draws those grids or an empty frame.
- The structural column schedule table at lower right is drawn twice-offset: our rows have a larger pitch than Revit's (red rows compress against cyan rows, drifting about 150 px by the bottom), so row height / text size in schedules is too big.
- Title block texts ("Column Schedules", "Sample House") sit lower and larger than Revit's.
- qa text: our wrapped text (tspan dy lines) is now split per line, matching Revit's one MTEXT per line. rst basic 1251893: 'Hollow','Sections','(AS' now matched (missing 8, text recall 0.91). Remaining: rotated multi-line tags still show 7-10 mm position offset (text-moved), under investigation.

## After annot merge (baseline re-saved)
- qa text fix: Revit MTEXT rotation (direction vector) is now read, rotated left edge, registration re-centred on match residuals: rotated beam tags in rst 1251893 now median 0.9 mm (was 6.9 mm).
- Regression vs previous baseline (Residential, fresh render of merged code): view 36 text recall 1.0 -> 0.5: Revit has 8 texts, ours 4; 'A-4' x3 and '3' at (184,56) mm are MISSING now (were present before). View 32 text 0.98 -> 0.87, ink P 0.84 -> 0.75 (more ink outside the Revit framing?). Baseline re-saved to the current numbers as requested; please check view 36 'A-4' tags.

## Text tier by category (qa-textcat, dev tree render, Residential + Commercial + partial rst basic)
- 28 views with a registered text tier: Revit 736 texts, 685 matched (93%).
- Dimension strings ("6' - 6 1/4"): Revit's DXF does not contain them (they are in the Revit PNG), so they cannot be checked numerically from DXF; QA now reports ours-only dimension strings as informational `text-extra-dim`. To verify dimensions we need Revit PDFs per view (PyMuPDF text) or visual checks of the crops.
- Worst text-moved (other text): Residential 246869, 32, 258720 (13-14 each). Worst missing: Commercial 29237 (grid letters 8, text 4). Run `./qa-textcat out3` for the live table.

## Who is the "extra drawn element" (class lookup via reader)
Repeated ink that Revit's DXF does not have at that place:
- ProfileRoof 158021 (Residential 29181, 228085, 236647 and section 'typ. eave'): roof profile drawn at ~7 m of ink in views where Revit shows almost none. Check view filtering/cut-plane for profile roofs (section/detail views) in c5-sheets.
- SWall 206435 (Residential, 2.5 m extra) and SWall 148024/146944/146892 (Commercial 32, 36, 157296 plans): structural walls drawn where Revit draws nothing or something else; likely cut-plane/view-range (wall top above cut) or discipline/visibility.
- SiteSurface 228877 (Residential 29154, 29181, 236647): topography contour/outline ink in elevations/sections that Revit omits.
- LinearDimString 234610/234684/234150/234712/234330 (Residential 32): dimension strings (tick/witness ink) offset or extra versus Revit.

## 2026 rosetta scenes (qaros, dev tree annot 3d50ef7, out4/)
- view_e/f/i/j/k scenes: 13 of 14 views pass each, median score 97.3 (was 9 of 14 before the fixes). view_sheet_var: 12 of 15. view_l_section_schedule_var: 7 of 15, median 79.5.
- Failing in view_l_section_schedule_var: plans 'VR plan' 303703 (60.2), 'Level 2' 2608/2614 and 'Site' 4664 (76.7, region-extra), sections 'East' 2307 (64.3) and 'West' 2356 (63.6, long lines missing).
- view_sheet_var: 'RV1 plan' 303690 and 'RV 3D' 303702 render as an EMPTY SVG in our output (view-not-rendered) while Revit exports content.
- All three sheets (303713, 303711): title block texts 'www.autodesk.com/revit' and the print date are missing from our sheet (PDF tier). The print date is variable, the URL text is a real gap.

## Section 'East' 2307 (view_l_section_schedule_var) overlay reading (red = Revit only, cyan = ours only), crop ~2000 px wide
- Level heads: Revit's head symbol (circle with quartered fill) sits further RIGHT than ours (ours is about 70 px / about 3.5 % of the view width to the left, overlapping the label), and the Revit label ('Level 2', 'T.O. Slab', ...) is set at larger text size and lower-right of ours, with the elevation value directly under it. Ours is smaller and offset up-left. Same for every level (Level 1/2, T.O. Fnd. Wall, T.O. Footing, B.O. Footing).
- Level lines: dash phase differs (ours dashes are offset from Revit's), minor.
- Our extra 'VR1' / '6096' level head at the top right is cyan-only where Revit has a different label position ('60..' in red).
Overlay: ~/src/rvt-qa/out4/2026_view_l_section_schedule_var.rte/diff/2307_overlay.png

## Plan 'VR plan' 303703 (rosetta view_l_section_schedule_var) overlay reading
Overlay: ~/src/rvt-qa/out4/2026_view_l_section_schedule_var.rte/diff/303703_overlay.png (red = Revit only, cyan = ours only; crop ~2000 px wide, room about 1050 px wide)
- NORTH wall: ours draws an extra outline about 190 px above Revit's north wall (outer line at the top of the crop vs Revit's at y=190; inner face agrees at y=208). The wall is drawn about 10x too thick or an extra element sits north of it. South wall: Revit draws an outer line about 20 px below the inner face, ours does not (cyan inner line only), so ours wall thickness/offset is wrong on N and S.
- Door swing: arc origin and radius differ (ours arc rises to y=580, Revit's to y=640; ours is larger), door leaf line in a different place.
- East window: ours is at y 350-410, Revit's at y 460-510 (about 110 px higher; window offset along the wall differs).
- Section head (V-100 / '2') is larger in ours; circle sits higher; the head triangle is bigger (about 1.3x).
Run: ./qa-view FILE 303703 on 2026_view_l_section_schedule_var.rte (rosetta) to reproduce.

## Plans 'Level 2' 2608 / 2614 and 'Site' 4664 (view_l_section_schedule_var): section marker missing
Overlay: ~/src/rvt-qa/out4/2026_view_l_section_schedule_var.rte/diff/2608_overlay.png. The four elevation markers at the view edges match. Revit ALSO draws a section marker in the middle of the view (section head 'V-100' with circle '2', a thin section line to the left and a thick cut-end bar); ours draws NOTHING for it (red only). In 'VR plan' 303703 the same section head is drawn by us (bigger than Revit's), so the section line/head is dropped in these plans, likely when the section's crop/extents are outside or when the section view is not placed on a sheet. 3 views, same cause.

## Section 'West' 2356 (view_l_section_schedule_var) overlay reading
Overlay: ~/src/rvt-qa/out4/2026_view_l_section_schedule_var.rte/diff/2356_overlay.png (crop 2000 px wide)
- All level lines (VR1, Level 2, Level 1, T.O. Fnd. Wall, T.O. Slab, T.O. Footing, B.O. Footing) in ours sit about 20-30 px ABOVE Revit's (e.g. VR1 line y=36 vs 67, Level 2 y=170 vs 190). In 'East' 2307 the same levels agree vertically, so this is view framing/crop (vertical offset of the section's crop) not elevations.
- Level heads and labels follow the same offset; labels are slightly to the right of Revit's.
- Revit draws a thick bar with a vertical line (red only, about x=870, y=0..115): same element missing in ours as the section cut bar in the 'Level 2' plans (see above): the section/cut mark of a referenced view.

## Possible regression in current dev (after annot 3d50ef7)
Golden views (qa-regress --dev): Residential 29154 ink R3 0.757 -> 0.567 and 29181 R3 0.735 -> 0.644 between the run at annot 3d50ef7 and the run at dev 8996ce1 (topography outlines release); P unchanged (0.72 / 0.86). Plan 32/36 are unchanged or better. Missing ink in these two views now: check what the topography outline change removed or moved in elevation/section views (qa-view FILE 29154 shows the regions). Baseline was re-saved at 8996ce1, so qa-regress will no longer flag it.

## Elevation 'east' 29154 (Residential) overlay reading: crop region not applied on the left
Overlay: ~/src/rvt-qa/out/regress_dev/20_Residential_Sample_Project.rvt/diff/29154_overlay.png (red = Revit only, cyan = ours only, crop ~2000 px wide).
- Revit's view is CLIPPED at x~=430-525 on the left (its ground hatch starts at x=430, the house wall at x=525): the left wing of the house (x 280..520: its roof, shingles, siding) is not in Revit's export. Ours draws that wing and the larger roof (cyan) plus the ground hatch out to x=160. So the crop region / far-clip of the elevation drops nothing on the left in our render (the right edge matches: wall x=1320).
- Consequence in the metrics: ink R3 0.757 -> 0.567 came with this release (extra geometry shifts registration), P unchanged.
- Section marker: ours puts the 'A-2' section head at x=610 (cyan), Revit at x=1147; level labels 'attic' / 'first floor': ours is to the RIGHT of the head and Revit's to the LEFT of it (labels sit left of the head in Revit, right of it in ours).

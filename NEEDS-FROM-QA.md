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

## Elevation 29181 (Residential) shows the same root cause as 29154
Overlay: ~/src/rvt-qa/out/regress_dev/20_Residential_Sample_Project.rvt/diff/29181_overlay.png. Revit's elevation is clipped to the main house (walls x 340..1465 in the 2000 px crop); ours also draws the side wings (x 160..340 and 1465..1640: their roof, siding, balcony rail) and the ground hatch beyond. Level heads: Revit at x~1730 (just right of the clipped extent), ours at x~1985 (about 255 px further right), labels left of the head in Revit and right of it in ours. The terrain line differs in slope/start (red = Revit's section line, cyan = ours). Hypothesis: the elevation crop region (or far clip / view depth) is ignored by the current framing logic ('all annotations' framing from annot 3d50ef7 + dev), so geometry outside the crop is drawn and the level heads are placed at the wider extent. Check crop_rect_uv usage in view_svg for elevations, and compare with the pre-3d50ef7 render (R3 0.757 / 0.735 then).
- Code pointer for the crop hypothesis (read only, not run): viewsvg.py clips MODEL_LAYERS with clip-path 'cropclip' only when crop is not None, and compose.crop_rect_uv returns None unless v['crop']['crop_active'] and basis are set. For 29154/29181 the wings are drawn unclipped, so either crop_active/basis is not read for these two elevations (Decoder.crop), or the wing/ground geometry sits on a layer outside MODEL_LAYERS.

## Result of the crop diagnostic (remote-host, dev tree, qa/view_crop.py)
- 29154 'east' and 29181 'north': crop_active True, basis present, bounds x [29.68, -11.15] ft (29154) and [42.47, -21.55] ft (29181); far_clip_active key present. Plans 32/36: crop_active False (as expected).
- So the crop IS read; the wings/ground hatch/terrain beyond it are drawn in ours although clipPath 'cropclip' should cut them: the leaking prims must be on layers not in MODEL_LAYERS (or have no 'layer') or drawn after the clip group (hatch/pattern fill of the wing roofs/siding, ground fill, terrain line, balcony rail). Suggest: list the layer names of prims whose uv lie outside the crop rect in 29154, add them to the clipped set, rerun qa-view FILE 29154 (expect ink R3 back to about 0.76).

## CORRECTION to the crop hypothesis above (far-clip diagnostic)
- far_clip_active is False for 29154/29181, so far clip is not the cause either. The clip rect in OUR 29154 svg is 259.2 mm wide at 1:48 = 40.8 ft = exactly the crop bounds read from the file (x -11.15 .. 29.68 ft), so the clipping itself works.
- But Revit's own picture is narrower: its clipped ground hatch spans about 200 mm of paper (x 430..1690 in the 2000 px overlay) = about 31.5 ft, i.e. Revit's effective crop is about 9 ft narrower than the bounds we use (wings left of x=525 are inside OUR crop but outside Revit's). Candidates: the bounds are in the crop's own basis with an offset we apply wrongly (origin/basis shift of ~9 ft along the view's right axis in the elevations), or we read the annotation crop instead of the view crop (keys annotation_crop_active / annotation_offsets exist next to bounds). Check which rectangle Revit's DXF extent matches: ~/rvt-research/gt_views/2020_20_Residential_Sample_Project/29154.dxf extents.

## FINAL on 29154/29181 (supersedes the crop/far-clip hypotheses above)
- Diagnostic: annotation_crop_active 0 (offsets 1 inch), far clip off, crop bounds consistent with our clip. The crop is NOT the problem; my '9 ft narrower' inference was wrong (Revit's ground hatch only spans where there is terrain, not the whole crop).
- The geometry tier already names the culprits for 29154: extra drawn elements 158021 (ProfileRoof), 228877 (SiteSurface), 146477, 170964 (ProfileRoof 158021 is also the top extra element in Residential 29181, 228085, 236647 and 'typ. eave'). The left wing roof/shingles in the cyan-only overlay is the ProfileRoof: Revit does not draw it in these elevations/sections (hidden by view filter / phase / visibility of that roof or it is not a visible roof type in the view), ours does. Same for the SiteSurface ground slab at the left.
- Action: check why 158021 (ProfileRoof) and 228877 (SiteSurface) are visible in our elevations (visibility graphics, phase filter, workset/design option); the ink-recall drop 0.757 -> 0.567 after the topography/roof change is consistent with these extra elements being newly drawn.

## qaall2 on dev 650fb0d (annot merge): net improvement
rst basic 8/47 pass, median 78.8 (was 76.6); Commercial 5/28, 67.5 (66.5); Residential 4/29, 76.2 (70.3); text matched 98% (1288/1309). Gains: Residential door head 237863 (+40.8), rst Section Wall 1199134 (+38.5), Residential south 29201 (+24), Commercial Site 29237 (+20.9), rst West 8237 (+14.3). One real drop: rst 'Cross Section' 1214432 (-14.9): please check (level clip / EQ dims change?). Residential 'cross section' 237764 -1.6, east 29154 -1.1 (ProfileRoof/SiteSurface extras still open).

## rst 'Cross Section' 1214432 (the -14.9 drop): grid spacing differs, likely angled section
Overlay: ~/src/rvt-qa/out3/18_rst_basic_sample_project.rvt/diff/1214432_overlay.png (crop 1965 px wide; red = Revit only, cyan = ours only).
- Levels (3000 mm apart: 9000 / 6000 / 3000) are 515 px apart in Revit (y 362 -> 877) and 489 px in ours (406 -> 895): our drawing is about 5 % smaller vertically in this overlay (the registration used one uniform scale for both axes, so a non-uniform difference shows up as offsets).
- Grids C / B / A: 451 px apart in Revit (x 460, 911, 1362) vs 490 px in ours (x 447, 937, 1426): ours is about 8.6 % WIDER horizontally. Converted to mm with the level spacing (515 px = 3000 mm): Revit shows grid spacing of about 2630 mm, ours about 3000 mm, ratio 0.875 = cos(29 degrees). Hypothesis: this section is cut at ~29 degrees to the grids and Revit shows the grid lines at their PROJECTED distance in the section plane; ours places them at their true (unprojected) spacing. Check how grid x positions are projected into the section view's right axis in rvtsheets (use dot with the view's right vector, not the distance along the grid normal).
- Consequence: everything that hangs on grids/levels in this view (heads, tags, EQ dims) lands elsewhere; the dashed callout boxes and EQ dimension chains on the roof pitch are also shifted 20-40 px in ours.
- Additional: Revit's tag texts (88.9x5.0CHS ..., SC15012 ...) have leaders to the beam; ours drop the leader line of the 88.9x5.0CHS tag (red leader to the apex has no cyan counterpart).

## !!! CORRECTION: overlay colour legend was INVERTED in all my overlay readings above !!!
Verified numerically on rst 1214432: the Revit PNG has its grid columns at x = 683/1430/2178 px, which are the CYAN lines in the overlay. So in every *_overlay.png: CYAN = Revit only (ours white there), RED = ours only. (The code comment said the opposite; fixed in qa/compare.py and README.) The numeric findings (text, geometry tier, scores, element ids) are NOT affected, only my visual readings of overlays. Corrected readings (swap who is who):
- Column Schedules 1457199: REVIT draws the two graphical column schedule grids; ours does not (only the 'view not drawn yet' placeholder text): graphical column schedule view is not implemented. In the lower-right schedule table OUR rows have the smaller pitch (ours compress against Revit's rows, drift ~150 px at the bottom) and OUR title block texts are the larger/lower ones.
- East section 2307 level heads: Revit's head symbol sits LEFT (about 70 px) of ours and overlaps its small label; OUR level labels are larger and lower-right of Revit's with the value under them, heads farther right.
- VR plan 303703 (swapped): REVIT draws the north wall outline about 190 px above the inner face (ours has no such outer line there, ours is thinner); OURS draws a south outer line ~20 px below the inner face that Revit does not; Revit's door swing arc is the larger/higher one (ours smaller and lower); Revit's east window is at y 350-410, ours at 460-510 (ours ~110 px lower); Revit's section head is about 1.3x LARGER than ours.
- Plans 'Level 2' 2608/2614 and 'Site' 4664: OURS draws the section marker (head V-100 / 2, line, cut bar) in the middle of the view; REVIT shows none there. We draw a marker Revit hides (section view not placed / marker visibility).
- West section 2356: REVIT's level lines are the ones 20-30 px ABOVE ours (ours sit lower); our level labels are larger; the thick bar + vertical line near the top is OURS only (a section cut mark Revit does not draw).
- Elevation 29154: REVIT draws the left wing (roof, shingles, siding) and the ground hatch out to the full crop width (x 160..1800 = our clip rect); OURS draws only the main house + hatch where the terrain is (x 430..1690): we are missing the wing geometry and the full-width ground fill. The roof apex differs too (ours at x=975, Revit at 870). Earlier 'extra element' ids (ProfileRoof 158021, SiteSurface 228877) are ours-only ink per the numeric geometry tier: they are drawn at a different place/shape than Revit's. The crop analysis above stays valid (crop is read and applied).
- Elevation 29181: REVIT draws the side wings and ground out to the crop; OURS clips to the main house. Revit's level heads sit ~255 px FARTHER RIGHT than ours; Revit's level labels are right of the head, ours left.
- rst Cross Section 1214432 (the -14.9 drop): Revit's grid spacing is 3000 mm (DXF: x = -3201.59, -201.59, 2798.67 mm) and its PNG is isotropic (748 px per 3000 mm on both axes). OURS (red) shows grid spacing about 12 % narrower than Revit's relative to the levels (ratio 0.876 = cos 29 degrees): our grid lines are foreshortened, i.e. our section's right vector is rotated ~29 degrees from the grid-normal (or grids are projected through a wrong axis). Check the section's view direction vs the grids for this view.

## qaall3 (dev 4c4b174 vs qaall2 650fb0d), c3-qa 2026-10-17
Medians: rst basic 78.8 (=), Commercial 67.5 -> 67.6, Residential 76.2 (=). Gains: Residential typ. wall 236647 +3.6, typ. door head 237863 +2.7. Drops: Commercial 195606 'Typ. Canopy/Flat Roof' 38.9 -> 27.9 (DXF layer S-COLS recall now 0.015, len 204 mm at (192, 391) mm paper; S-COLS-HDLN 0.18 both runs: columns / column hidden lines missing in this detail); rst 1300883 'Ref Beam system' -2.8; Residential 180203 -1.3. Tool: ./qa-scorediff out3 out5.
- c3-qa follow-up on Commercial 195606: S-COLS in Revit's DXF is ONE INSERT (about 204 mm of paper linework), so the 'recall 0.015' is a single column symbol, not a systematic gap; extras 147722 ProfileRoof, 179262 SWall, 182970 FamilyInstance (cat -2001330, Structural columns/framing). The -11 is mostly the vector-tier fallback (registration unreliable, reg_score 0.18). Low priority; the earlier 'columns missing' wording overstated it.
- c3-qa: Commercial 195606 re-registered with the 4 strongest FFT peaks: identical (recall 0.495), so the score is not registration noise. Revit's DXF holds only 3.3 m of linework (paper) for this view, ours 59 m (18x): the section draws far more than Revit exports (likely geometry beyond Revit's crop/far clip or a cut/projection difference). c5-sheets: check 195606 crop and far clip.

## Corpus-wide over-drawing ranking (qaall3, summed extra_mm of DXF unmatched ink per element)
Residential: SWall 206435 (5 views, 93 m), ProfileRoof 158021 (9, 51 m), SiteSurface 228877 (7, 30 m). Commercial: ProfileRoof 147722 (3, 61 m), Floor 216070 (7, 57 m; plans 32/193216/196766/196785), SWall 148023 (2, 46 m), BuildingPad 156625 (4, 38 m) and 157835 (8, 35 m; elevations/sections), SWall 148624, ProfileRoof 155712, SWall 146944. rst basic: FamilyInstance cat -2001320 (structural framing) 1436861 / 1096421 / 1417473 / 1436528 (2-3 views each, 21-25 m). Most missing Revit layer ink: rst S-RBAR (4 views, 84 m: rebar), S-BEAM, S-LOAD-SNOW, Commercial C-TOPO-MAJR/MINR (contours), A-WALL-PATT.
Suggestion for c5-sheets: Commercial Floor 216070 in plans and BuildingPad 156625/157835 in elevations (probably Revit hides/clips them) are the cheapest candidates after the roof/wall ones already known.

## Snowdon Towers (2026 Structural, dev 4c4b174), c3-qa
- Cover Sheet S000 (921485, score 47.6): (1) the Sheet Index table texts are 0.58x Revit's size (Revit 12.5 pt rows, 19 pt title 'Sheet Index'; ours ratio 0.57-0.58) and sit 17-60 mm off (the rows drift: error grows down the table, so the row pitch is also too small); (2) schedule/notes paragraphs wrap at different words than Revit (our lines 'This project is distributed across several Revit models in keeping with' vs Revit '...models in keeping with industry'): text-box width or font metric too narrow/wide; (3) Revit prints '10/16/2026 3:01:53 PM', ours the current date (expected, ignore).
- Details 'Beam to Beam Connection' 910139 / 'Beam to Column Connection' 916437: DXF geometry is good (recall 0.97/0.98, precision 0.88/0.84) but the image tier scores them 45-50 because of big region-extra cells (10-12 kpx) in the centre: probably surface fill / solid fills (steel section fill) that Revit's PNG shows differently. Layer A-DETL-IDEN (detail identification, 106-165 mm) is mostly missing (recall 0.07-0.12).

## CORRECTION (c3-qa, qaall5): my DXF over-drawing numbers above were inflated
qa/vecgeom.py ignored the SVG clipPath (cropclip), counting ink outside the crop that Revit's DXF never has. Fixed (clip-aware). Same dev tree cb53624, scores qaall4 -> qaall5: medians rst 78.8 -> 81.6, Commercial 67.5 -> 78.7, Residential 76.2 -> 78.4. Detail/section views: 195606 29 -> 69.5 (DXF P/R .47/.89), 196813 Typ. Parapet 50 -> 84, 195581 57 -> 86, 236726 typ. window 55 -> 81, 237841 typ. eave 51 -> 74. Drop the '18x over-drawing' claim for 195606 (retracted). Revised top over-drawn elements (extra DXF-unmatched mm): Commercial SWall 148023 (46 m, 29181 / 147034), Residential ProfileRoof 158021 (37 m, 4 elevations), Commercial SWall 148624, ProfileRoof 155712 (8 elevations), Residential SiteSurface 228877 (21 m), Floor 216070 now only 12 m. BuildingPad 156625/157835 no longer in the top list.

## REAL BUG (c3-qa, Snowdon 55 Structural details, dev cb53624): unresolved element id printed as text
Views 900694, 908972, 909827, 910139, 916437 (all 'connection' details, same in 2024 file 43): our SVG contains text `EID(18446744073709551615)` (uint64 max = invalid ElementId -1), once as a huge rotated bold 17.6 mm label (element 916444, rotate -45) and as small tags next to weld-symbol size labels (element 916482: '5/16"' left, 'EID(...)' right). Revit shows the weld symbol with just 5/16" values and no such text. So some label/tag parameter of type ElementId with value -1/invalid is being rendered through an EID(...) fallback; it should render empty. This is the main reason for the low image score (huge red region-extra cells) of 910139 / 916437 (45-50). Check where 'EID(' is produced in rvt-sheets.
- c3-qa pointer for the EID(...) text bug: the string comes from rvt_decode.EID.__repr__ ('EID(%d)'), so some label/tag text is built with str()/repr()/f"{x!r}" on a decoded value that is an EID (uint64 max = invalid) or a container holding one; the label text code should map an invalid EID to '' and resolve a valid one to its element name/parameter.

## qaall6 (dev 43af8b6 vs cb53624), c3-qa
Medians rst 81.6 -> 81.4, Commercial 78.7 (=), Residential 78.4 (=). Drops: rst 8157 'North' 74.0 -> 67.1 (DXF P/R .631/.922 -> .557/.894: both fell), Residential 29154 'east' 70.6 -> 67.9 (P .424 R .741 -> .414/.731), rst 1214432 Cross Section -2.1 (image tier only, DXF P .866->.894), Longitudinal Section 1251893 R .965 -> .944. Suspect the 0x10880e0 hidden-line gating commit (fe11d9b) on elevations/sections: check 8157 and 29154 DXF recall. Gains: Roof Peak 1383032 95.2. New pass flags (DXF-based rule when registration is unreliable): Pile cap, Continuous Footing, Roof Peak. text-garbage: none left in the corpus. Note: EID(...) Snowdon check pending (Snowdon sweep next).
- c3-qa detail on rst 8157 North (qaall5 -> qaall6): our linework 114 m -> 85 m (the hidden-line gating removed ink), DXF recall .922 -> .894 so some real lines were hidden too; precision also fell .631 -> .557 which suggests a registration/offset change, so the net -6.9 needs a DXF layer diff on c5-sheets' side (tools/compare_dxf.py 8157 before/after fe11d9b).

## c3-qa: new font check + a '?' placeholder (2026-10-17)
- qa-view now has a font tier (qa/fonts.py): per matched text pair it compares Revit's font (DXF text style -> font file; PDF span font name on sheets) with our SVG font-family, size ratio and, on sheets, glyph advance (PIL on the font fontconfig resolves). Findings: font-family-diff / font-style-diff / font-size / font-width / font-substituted (area 'fonts'), table in result['fonts'], result['missing_fonts'] (sheets). Appears from the next sweep.
- Our svg_texts now carries font, bold, italic; DXF texts carry style/font.
- Commercial 196813 'Typ. Parapet' (and probably other details): three <text> elements of owner 213149 draw the literal '?' in a blue circle (a placeholder symbol) at the level-head positions where Revit has real text (Revit DXF style arialbd.ttf, layer A-FLOR-LEVL). New text-garbage finding catches a bare '?'.

## c3-qa: text baseline check (for c3-annot)
qa-view now reports result['baseline'] = n, mean, median, max_abs, p90_abs (mm, text-normal direction, positive = ours lower on paper) and by_type, plus a text-baseline finding per biased group (|median| > 0.25 mm, n >= 3; examples carry dn per text and the review pairs get Revit|ours crops of them, largest text first = viewport titles first on sheets). Views: reference = Revit DXF insert through the exact geometry registration (absolute, not the text registration which absorbs the bias); groups 'TEXT <font>' (insert = baseline-left, directly comparable) vs 'MTEXT <font>' (insert = top-left attachment: expect a negative offset of about the ascent, 0.7-0.8 x text height, so read MTEXT groups by their spread, not their sign). Sheets: reference = Revit PDF span (baseline estimated from bbox: y1 - 0.212 x size), groups by font and size class. Smoke test: Commercial 196813 MTEXT arial median -1.29 mm, max 3.67 (n=5). Appears in the next sweep.

## c3-qa for c3-sheets: before/after tracking of detail 206124 (and any view)
Snapshot taken: Commercial 206124 'Details' at dev 7778a2a: score 79.6, SSIM 0.868, ink P/R 0.947/0.625 (images in ~/review-compare/history/19_Commercial_Sample_Project_206124/dev_7778a2a/pair__{revit,ours,side,diff}.png). After your parapet bricks / door schedule border fixes land in dev, run (remote-host, capped, ~1 min):
  cd ~/src/rvt-qa && RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev QA_RENDER_PY=$HOME/src/rvt-sheets/.venv/bin/python systemd-run --user --scope -p MemoryMax=3G -p CPUQuota=100% nice -n 19 .venv/bin/python review/watch.py $HOME/review-compare ~/rvt-research/corpus/2020/19_Commercial_Sample_Project.rvt 206124 dev_<hash>
-> ~/review-compare/history/19_Commercial_Sample_Project_206124/before_after.png (Revit | before | after + numbers) and history/INDEX.html. Any other view: same command with another file/view id. Or tell me the hash and I run it.

## Snowdon, REAL fresh run (dev 7778a2a; the earlier Snowdon numbers were stale pre-fix results) c3-qa 2026-10-17 16:00
DXF recall collapses in plans (precision fine): 581543 L2 R .873 -> .365 (both 43 and 55), 581553 L3 R .785 -> .249, 621471 M1 TOS R .869 -> .718, 627226 L3 TOS R .919 -> .869, 607489 L5 (Facades) R .79 -> .71. Candidate: family cut-profile nodes follow the cut plane in plans (fc31185) or the parent/child wall change: some linework that Revit draws in these plans is now dropped. Image-tier score of L2/L3 rises/falls only because of registration, trust DXF R. Elevations 201922 North / 201907 East / 201892 West / 4969 South: DXF P improved +0.1 (.77 -> .88) but combined score fell 4-22 (registration on the image tier; DXF R unchanged .97-.99): no real drop. 909827 'Not Used' 100 -> 50.5 (trivial/blank view, DXF P/R 1/1): ignore. Gains: 900694 Drilled Pier +26 (EID text gone), 916437 Beam to Column +10, 910139 +8.6, Parking 582085 +5.5. EID(...) text: 0 left.

## qaall9 (dev 8046930; first sweep with font / baseline / garbage tiers), c3-qa 2026-10-17 21:00
Medians rst 81.6 -> 83.3, Commercial 78.7 -> 81.6, Residential 78.4 -> 80.4. Big gains: Residential Site Plan 29237 48 -> 94 (now PASS), Commercial Cover Sheet 206143 60.5 -> 84.9, 196826 Typ. Wall at Grade 16.7 -> 47.5 (DXF R .26 -> .69), rst Column Schedules 54 -> 68, Title Sheet 82 -> 90. Small drops: rst 1251893 Longitudinal Section -4.7 (DXF P/R unchanged .988/.965: registration), rst 8176 East -2.6 (P .66 -> .81, R .874 -> .836: recall -0.04), Residential 36 first floor -1.2.
New tiers, real findings:
- text '?' placeholders: 117 views draw a literal '?' text; owners 213149 (70 views) and 1455334 (47 views, rst basic). Revit shows real text there (level heads etc.): which family/class draws '?' (c3-sheets/c3-annot please check these two element ids).
- Snowdon 908972 Details / 910139 Beam to Beam Connection (2024 + 2026): weld-symbol texts ('5/16"', '3-Sides') are drawn in font ARchitxt in ours; Revit uses Arial (ArialMT / arial.ttf).
- Trebuchet text baseline on Snowdon sheets (PDF reference): 4.5 mm -0.53 mm, 6.5 mm -0.58, 13.5 mm -0.26 (ours higher), consistent across 20+ sheets; Arial 4.5 mm +0.3..+1.8.
- font-family-diff for 'trebuc.ttf -> Trebuchet MS' (79) was a QA alias bug, fixed (not a defect).

## RULE UPDATE (c3-qa): review/watch.py renders a whole project, so run it on remote-host only
  rsync -a ~/src/rvt-qa/review/ remote-host:src/rvt-qa/review/ ; h1run run watch --env rvt --dir ~/src/rvt-qa -- review/h1watch.sh 19_Commercial_Sample_Project.rvt 206124 dev_<hash>   (4th arg = rvt-sheets tree on remote-host, default dev)
then pull: rsync -a remote-host:review-compare/history/ ~/review-compare/history/ . (the remote-host command in the earlier note is withdrawn.) Or tell me the hash and I submit it.

## qaall10 (dev 55c9b9d) c3-qa 2026-10-18
Medians rst 83.3 -> 86.6, Commercial 81.6 (=), Residential 80.4 -> 81.1. Commercial Cover Sheet 206143 84.9 -> 96.9 (PASS). Gains: rst Central Pile +5.2, Commercial Building Section 173631 +4.8 (DXF R .87 -> .99), Details 206124 +4.4, rst West 8237 +4.0, Column Schedules +3.3. Only drop: Residential typ. wall 236647 -1.0. Snowdon: no regressions beyond -3.6 (43 'Structure Only' 600158: shaded 3D, DXF meaningless); Snowdon Cover Sheet 921485 stays low (46-47): image tier (3D viewport / sheet index), text baseline now clean. Font tier: font-family-diff 0 (ARchitxt fixed), font-width 4, font-style-diff 2, text-garbage 2 (legit 'Not Used' large text), text-baseline findings 133 (mostly MTEXT groups, whose insert is top-left by definition).

## qaall11 (dev 564062d), corpus part (c6-qa)
Medians vs qaall10: rst 86.6 -> 85.7 (n=45), Commercial 81.6 -> 82.1, Residential 81.1 -> 80.8. Drops: Residential 258720 'at grade' 82.2 -> 75.0 (RETRACTED: QA flap in the raster layer check, DXF/text/ink identical; fixed in qa/compare.py, not a drawing regression), rst 1373835 'Section Wall2' -2.2, Residential 228085 'building section' -0.3 (pass flip lost). Gains: rst 1383083 +7.8, 1250103 +6.7, 1457064 +4.9. Snowdon part still running.
qaall11 Snowdon (out14 vs out6): medians 43: 68.5 -> 75.1, 55: 70.4 -> 75.0, 46: 68.3 -> 80.1, 58: 68.4 -> 78.5; 8 pass flips (Learn about this project, How to use this project 2 sheets +24..27). 4 views present only in old.

## Snowdon 3D 'Structure Only' 600158 (c6-qa, qaall11)
Only corpus view with DXF recall < 0.6: View3D, DXF recall 0.05 / precision 0.01 (Revit 120.7 m of ink, ours 784.8 m = 6.5x over-drawn, offset 2.0 m so registration is likely off too), image score 59.5, A-FLOR-LEVL and S-GRID-IDEN layers missing. Looks like a 3D view drawn without hidden-line removal / wrong camera. Same in files 43 and 55. Owner: hidden-line 3D work.

## Text baseline (c6-qa) 
Sheet text (Revit PDF origin) matches ours to 0.0-0.1 mm for all common types (trebuchet 3.5/4.5/6.5/13.5/22 mm, arial 3.5-25 mm). The earlier view-level 'MTEXT ours lower 2-5 mm' was a QA error (DXF MTEXT insert is the top of the line); corrected, no action for sheets. One outlier remains: trebuchet 3.5 mm min -5.3 mm in one view (to be traced).
Real outlier: Snowdon Structural view 871873 'Main Level' (files 43 and 55): beam tags CB18x24 / CB24x39 / CB24 x51 (elements 869866, 869868, 869870, 869890, 869892; trebuchet 3.5 mm) are 5.3-5.8 mm HIGHER than Revit's (n=11 of the view's tags, all same direction); dimension text 9'-6 1/2" is within 0.3 mm. Suggests the tag anchor/offset for structural framing tags (rotated or leader tags?) is off; please check.

## Snowdon text gaps (qaall11, files 43/55, c6-qa)
- 843511 'Top of Footing' (ViewPlan): 43 of 134 Revit texts missing, 53 extra: footing tags Cap36"x36"x24" (12), DP24"-10'/-12'/DP30" (~25), SF36"x18" (8) not matched at Revit's positions; 4 'DP24"' texts are 17-40 mm away. Looks like footing/pile tags drawn with different text or in different place (or missing tag type); ours has 10 extra.
- 594716 'L3' (ViewPlan): 209/210 matched but ~40 texts are displaced by CONSTANT amounts per tag type: beam tags W18x55/W18x86 +8.3/6.4 mm, W8x10 7.1 mm, 'W8x10 @ Max 4'-0"' and spot dims 18'-4" 13.0 mm, TOS(...) 10.9 mm. Same signature as the beam-tag offset in 871873 (5.3-5.8 mm): structural framing tag anchor/offset rule (probably tag head position vs text anchor, i.e. tag 'leader'/rotation or horizontal/vertical alignment).
- 201892/201907/201922 'West' sections: all elevation/level dimension strings displaced 6.0-6.7 mm (0" 13.6 mm) in the same direction: dimension text offset from the dimension line differs by ~6 mm.
- Snowdon 910139 (Beam to Beam Connection) and 124186: 'grid letter' texts missing (8 and 4).
- Extra texts that look like unformatted numbers (Snowdon 55/43, c6-qa): L1_43_High 579516 (108 extras), Parking 582085 (81), L2 581543 (27), L3 581553 (27), L5 581573 (20): e.g. '741','348','298','446.7125','367.2875','374.0373','200.5' (raw decimal values, not feet-inch strings). Probably dimension/spot values or tag parameters printed without the project unit format (or hidden/"reference" dimensions Revit does not draw). Please check which element class they come from (qa element lookup: h1elem.sh).
- Footing tag fragments: sheet 869612 'Foundation' and view 843511 show extras '36"x', 'xx' where Revit has 'Cap36"x36"x24"': a parameter string is being split/garbled (the 'x' joins and the leading 'Cap' / trailing '24"' are lost) - likely the same cause as the 43 missing footing tags in 843511.
- Sheets 869612 / 908972: title block date text '10/18/2026 7:32:48 PM' (our render time) vs Revit's export time: a print-date field, ignore or make it deterministic.
- Snowdon 910139 / 124186 'grid letter' text-missing = 'C' + 'L' pairs on A-ANNO-NOTE-4/-96 (1 mm apart): Revit's centerline symbol. Please check we draw the centerline symbol (L over C glyph) at those points (84.0/82.5, 84.0/102.6, 84.0/142.9 mm in 910139; 523/145, 513/165 in 124186). QA now reports it as one 'centerline symbol' finding.

## 3D 600158 visual confirmation (c7-qa)
Crop out14/43_*/diff/600158_f00_region-extra.png (Claude viewed): Revit shows a hidden-line view (occluded edges removed, floor deck solid, dashed/halftone beams behind); ours is a full wireframe with every back edge drawn, and the frame is also offset/slightly scaled against Revit (red/cyan overlay does not coincide). Needs hidden-line removal plus camera check for View3D 'Structure Only'; QA numbers for this view are not meaningful until the camera matches.

## qaall12 (dev 9cc31a8) c7-qa, out15 (corpus) / out16 (Snowdon)
No regressions >= 5. Medians vs qaall11: rst 85.7 -> 85.9, Commercial 82.1 -> 83.3, Residential 80.8 -> 81.1; Snowdon 43 75.1 -> 76.5, 46 80.1 -> 82.5, 55 75.0 -> 76.7, 58 78.5 -> 79.8. Gains: Commercial Elevations 205524 +10.4 (PASS), Restroom Elevation C +9.6, Residential gable end +7.7, 258720 'at grade' back to 81.6, Snowdon Drilled Pier 900694 +11 (PASS). One pass lost: rst 1457045 Upper House Framing 91.1 -> 89.6 (check).
Correction (c7-qa): Commercial Site 29237 -20.7 in qaall12 is a QA artefact, not a drawing change (DXF .996/.966 and image numbers identical): the raster layer term was skipped once vector layers existed. compare.py now uses vector layer recall for that term; takes effect at the next sweep. Other drops are small (Details 206124 -4.3, Column Schedules -4.1; Snowdon Longitudinal 579975 -4.6, Stair Towers -3.4, Parking 779980 -3.3).

## 2026-10-19 c7-annot -> c7-qa: registration / cache notes
- qa-view reuses out/<file>/ours/<view>.svg + .json forever (no --refresh): scores after a code change are stale unless those two files are deleted first (I got 214395 59.0 vs 79.0 fresh).
- Residential east elevation 29154: DXF A-GLAZ / A-WALL / A-ROOF extents equal ours shifted by exactly +10.4 ft in x (= 66 mm at 1:48), but vecgeom.fft_offset returns (162, 112) mm: the extra 96 mm = one period of the periodic ground / siding hatch (ours draws pattern segments as lines: ours_mm 20883 vs Revit 6260 because Revit exports hatches as HATCH entities). Please drop the pattern layers (cut_fill / surface_fill) from the vector tier, or include DXF HATCH boundaries/lines, and seed the offset from the datum/level lines before the ICP. Image tier on such views (scale 0.82) shows false misses: the overlay of 29154 / 237764 is misregistered, not a real defect (window spacing differs by the same 0.8 in the overlay but the extents match).

## c7-qa -> c7-annot (reply, 2026-10-19)
- qa-view --refresh now implemented (deletes the cached ours/<id>.svg+json, re-renders). Fresh 29154 render on the current tree re-checked.
- 29154 offset: vecgeom.fft_offset now returns the top 6 correlation peaks and compare() keeps the candidate that matches the most Revit ink after ICP. Result on a FRESH render: offset (154, 112) mm, recall .743 precision .378. Evidence against the +66 mm reading: Revit DXF extents (-162.2..154.5, -112.4..58.6 mm) shifted by +162 give 0..316.4 in x, exactly our extent 0.1..316.4, and candidate 66 matches only 9.5k of 25k Revit samples vs 18.2k at 162. So the 162 shift is probably the real registration and the misses (recall .74) are real; if you have an independent anchor (a datum line or level mark endpoint in both) please give its mm coordinates in both files and I will seed on it. Image tier on this view reg .6 at scale 0.73 is the PNG crop, separate issue.
- Pattern layers: ours_mm 20.8k vs Revit 6.3k is mostly hatch segments; Revit lacks them in DXF (HATCH entities). Not dropped yet, as precision there is informational.

## c7-annot -> c7-qa (ack, 2026-10-19)
Thanks: --refresh seen. Your extents argument for the +162 mm registration is sound (my +10.4 ft was in view coordinates before the svg margin), so I withdraw the '66 mm' claim: the 29154 misses are real until proven otherwise. No anchor request pending.

## qaall13 (dev a7c0039) c7-qa, out17 (corpus) / out18 (Snowdon)
Medians vs qaall12: rst 85.9 (=), Commercial 83.3 -> 84.2, Residential 81.1 -> 83.7; Snowdon 43 76.5 -> 79.0, 46 82.5 -> 84.1, 55 76.7 -> 78.7, 58 79.8 -> 82.6. Gains: Residential 237764 cross section +9.9, rst Central Pile +8.1, Commercial Site 29237 +10.6 (QA fix; still 57), Snowdon Not Used +10.1, Mezzanine 214385 +4.9 / 214395 +4.4, Level 1 (36) +4.7, rst Cross Section 1214432 +4.7, Typ. Wall at Grade 196826 +3.4 (DXF R .224 -> .251).
Drops: rst 1292652 'Analytical Model' 90.6 -> 19.7 is a QA registration flap (image tier scale 0.90 -> 0.73, reg_score .743 -> .293; DXF P/R .12/.25 both runs, SSIM .89 both), not a drawing regression; Residential 157966 {3D} -5.6, rst 1250376 box section -5.2, rst 1141621 Structure (Complete) -4.3, 1454508 {3D} -4.0 (all 3D, DXF meaningless). Snowdon 600158 'Structure Only' 3D -10 (3D wireframe issue, known).

## qaall14 (dev c21f314, beam tags run along the beam) c7-qa, out19 / out20
Corpus medians unchanged (85.0 / 84.2 / 83.8), Snowdon medians unchanged (79.0 / 84.1 / 78.7 / 82.6). Effect of 5f4b382 on the tag offsets I reported:
- 594716 'L3' (43/55): text-moved 38 -> 7; beam tags W18x55 (8.4 mm), C8X11.5 (9.1) and W8x10 are fixed. STILL displaced: spot dims 18'-4" 12.8-12.9 mm (x4), TOS(18'-10") 11.0, 18'-1 1/2" 7.6, 2VLI-6" 6.7 (spot elevation / TOS tags, a different tag class).
- 871873 'Main Level': CB-tags got WORSE: CB24 x51 5.8 -> 7.0 mm, CB18x24 5.3 -> 6.5, CB24x30 5.3 -> 6.5 (same direction as before?, now larger by ~1.2 mm); moved count still 91 (W14x10 x17, CB24x3.. x16, -4'-3.. x17, -6'-9" x11). The new along-the-beam rule seems right for plan beams (594716) but wrong for these CB tags (vertical/rotated beams?).
- Facades 607499 L3 (46/58) -17/-18.6 and 607489 L5 -13/-11 are QA registration flaps (image scale 0.80 -> 0.74, reg .55 -> .37; DXF P/R .804/.927 identical): not drawing changes.
- 600158 'Structure Only' -5/-6: 3D wireframe, DXF recall .053 -> .061.

## RETRACTION (c7-qa, 2026-10-20): CB beam tags on sheet 871873 'Main Level'
c7-sheets was right: the 5.3-7.0 mm 'CB24x30 / CB18x24 / CB24 x51 displaced' findings were a QA artefact. For ROTATED text qa/pdfvec.py compared our anchor point with the PDF bbox edge / origin y, which for 90-degree 'middle'-anchored text is half the string length (about 6-7 mm) away. pdfvec now walks along the writing direction from the span origin (start / middle / end by our anchor). Re-measured on the fresh qaall14 SVG: all 90-degree CB tags are 0.18-0.19 mm off, horizontal CB24x24 0.13 mm. No action for sheets there. Still real: spot dims 18'-4" (13 mm), TOS(18'-10") 11 mm on 594716 (DXF compare, not rotated).

## qaall15 (dev f7fc7b2) c7-qa, out21 / out22
No change: corpus medians 85.0 / 84.2 / 83.8, Snowdon 79.0 / 84.1 / 78.7 / 82.6; no view moves by more than 1.3 (55 R2 -1.3, 55 L5 -1.0). The annot/units/visibility/areapoly changes since c21f314 are neutral on the QA tiers (their effects are in element lists / area tags, which the visual tiers barely weigh).

## qaall16 (dev 698f5cc, merge vg 00c6525) c7-qa, out23 / out24
Identical to qaall15: no view moved by more than 1.3 (Snowdon 55 R2 +1.3, L5 +1.0 are the qaall15 drops reverting); medians 85.0 / 84.2 / 83.8 and Snowdon 79.0 / 84.1 / 78.7 / 82.6. vg element-list changes do not touch the visual tiers (no regression).

## Text-position QA fixed (c7-qa, 2026-10-20): most 'beam tag offsets' on DXF-compared plans were QA artefacts
Cause: Revit's DXF MTEXT insert is the top-left of the text box (attachment 1) and for rotated tags that corner is not on the baseline; qa/vec.py also estimated the width of centred/right-anchored text as 0.5 em per char. Both fixed (MTEXT moved to the baseline start along the text's own down vector; real font advance width). On Snowdon 594716 'L3' the beam tags W18x55, W18x86, W14x109 at every rotation (0, 45, 65, 66, 90, 278, 315, 335) now sit within 0.1-0.2 mm of Revit; Residential 32 median text position error 0.82 -> 0.13 mm.
Still REALLY displaced on 594716 (same fix applied, so these are real): spot-dimension text 18'-4" at rot 278: (dx +9, dy +13) mm = 15.7 mm; at rot 335: (+6.5, +2.5) = 7 mm; rot 90: (-1.4, +6.9) = 7 mm; 18'-1 1/2" (rot 0) dx -5.5..+8.1 mm, dy 0; TOS(18'-10") rot 65: (-8.4, -6.2) = 10.4 mm; 2VLI-6" (-2.4, -5.0) = 5.6 mm. So only spot-elevation / TOS / some level-tag classes are wrong, not framing tags. qaall17 re-baselines every text number with the corrected tier; earlier text-moved counts (e.g. 91 on 871873, 38 on 594716) are obsolete.

## qaall17 (dev d32f3d8, text-position QA fix) c8-qa, out25 / out26
Scores identical to qaall16 (corpus medians 85.0 / 84.2 / 83.8; Snowdon 79.0 / 84.1 / 78.7 / 82.6; no drops/gains/pass flips). Corpus text-moved findings 126 -> 96 (the MTEXT-origin fix removed 30 artefacts); remaining text-moved are real. 32/103 corpus views pass (+8 vector-pass).

## qaall18 (dev 41b9572) c8-qa, out27 / out28
No regressions: corpus medians unchanged (85.0/84.2/83.8), Snowdon 79.0/84.1/78.7/82.6; only Snowdon L3 582478 / L4 582488 +1.4.

## Lowest DXF recall/precision among non-3D views (qaall18, out27) c8-qa
Graphical Column Schedule 1250040 R .21/P .90 (unimplemented); Typ. Wall at Grade 196826 R .73/P .25; east 29154 R .74/P .38 (East 29154 R .83/P .50); Roof Level 417295 R .78/P .64; South 29201 R .86/P .45; typ. eave 237841 R .89/P .56; west 29191 P .67; Typ. Canopy/Flat Roof 195606 P .52. Low precision = our extra ink (mostly hatch/pattern segments that Revit's DXF carries as HATCH entities, see 29154 note); low recall = missing ink. Elevations/details are the best next targets after the column schedule.

## qaall19 (dev 583ffb8) c8-qa, out29 / out30
No regressions; corpus and Snowdon medians unchanged; only Snowdon Parapet 2 (876061) +1.2/+1.3 (DXF precision .93 -> .947).

## Still open at qaall19 (dev 583ffb8) c8-qa
Residential east 29154: SiteSurface 228877 still 4401 of 4860 mm extra, 146477 3754 of 5193 mm extra, ProfileRoof 158021 1088 of 1439 mm extra (same culprits as reported earlier; Revit omits them in this elevation). Fixing these three should lift 29154 precision from .38 toward .8+.

## qaall20 (dev 414f4bc) c8-qa, out31 / out32
No regressions. Residential median 83.8 -> 84.0; Snowdon Facades 46 84.1 -> 85.3, 58 82.6 -> 83.4 (593210/593327 sections +1.2..+4, 607489 L5 +7.9 is an image-registration flap: DXF P/R identical), Structural West 201892 +1.2 (DXF precision .866 -> .876).

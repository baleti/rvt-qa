# c3-qa -> c3-viewer (review-compare 3D pairs)
Thanks for shot3d. Findings on 2024_writer_house_lv/301641__ours3d.png: the shot has a light-blue panel background, a view cube and level tags, and the model is small in the frame, so the Revit/ours pair is hard to compare. Please for the review set:
1. use --clean and a WHITE background, no gizmo/labels, same pixel size as the Revit export (index.tsv / PNG size in ~/review-compare/revit/<file>/), hidden-line style (white faces, black edges) as a second shot per view in addition to the shaded one: name <id>__ours3d.png (shaded) and <id>__ours3d_hl.png (hidden line);
2. fill the frame the way Revit does (fit the model bbox with ~5% margin; Revit keeps the datum/level lines in the frame, so also a variant with levels hidden is fine);
3. next files (as soon as c3-writer puts Revit PNGs into ~/review-compare/revit/<file>/): same procedure for every <file> dir that appears there; I rebuild the pairs with review/build3d.py and INDEX.html.

## 2026-10-17 c3-qa -> c3-viewer: blank viewer shots (31 files, list in review/BLANK-VIEWER-SHOTS.txt)
Completely white (no ink): every 2307 East / 2608 Level 2 / 356 Level 1 shot (shaded and hl) for 2026_view_a/b/c; shaded 2608 plan for 2024_writer_house1, 2024_writer_house_lv, 2026_writer_house1; Snowdon 43/55 3D views 756118, 756235, 756593, 757090, 773839, 923315 (Structure Only roof / L4 / L2_M1 / L1 / L0 Parking / CoverSheet). They are scored as 'blank' now (no score). 3D hidden-line scores for the rest: median about 19 (framing/datum lines differ), best East elevations of tower20 (54).

## 2026-10-17 c3-qa -> c3-viewer: re-shoot after the mirrored-camera fix
All section / elevation / 3D-view shots in ~/review-compare/viewer/<dir>/ made before your fix are stale (the 194 pairs of the 3D index are built from them). Please regenerate everything (delete the old PNGs; shaded + hl) for every dir; tell me when done and I rebuild the pairs and scores with review/build3d.py. (I have no section alignment test of my own; the vctl one is c3-viewer / vctl's.)

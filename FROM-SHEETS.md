# From c5-sheets to c5-qa (2026-10-15)
- qa/vec.py svg_texts joins the tspans of one <text> into a single string, while Revit's DXF stores every wrapped line as its own TEXT/MTEXT (e.g.
  'Store fixture' / 'layout by store' / 'owner'; door-tag comment 'vision' / 'lite'). Result: wrapped notes show up as missing + extra. Suggest: emit one
  entry per tspan (dy>0 = next line) at the line's own y.
- Used qa-view on Residential 32 (text recall 0.43 -> 0.83 after door-tag fixes) and Commercial 32; very useful. Wish list: per-layer text recall
  line in the summary, and a `--svg` run that does not need the demo tree.
- Revit-side dims/spot texts are DIMENSION entities (not TEXT): the text diff cannot see them, so dimension text format (e.g. 2024 imperial vs mm)
  is invisible to qa-view; compare_dxf in ~/src/rvt-sheets-dev/tools explodes DIMENSION entities for the linework only.

## Reply to the 2026 rosetta / sheet findings (c5-sheets, 2026-10-15 20:10)
- 303690 'RV1 plan' (2026_view_sheet_var): NOT a bug. Revit's own export gt_views/2026_view_sheet_var/303690.png is a blank white page (the plan contains only a
  Viewer3d + ExtentElem); our empty svg is correct. Please mark such views as trivial-view in qa-view when the Revit PNG has no ink.
- Sheet 303711 title block: our svg has all texts (Consultant x4, Address x8, Phone x4, Fax x4, e-mail x4 ...) but as ONE <text> with several tspans per block
  (Revit's PDF has one span per line): same multi-tspan counting issue as in FROM-SHEETS.md above. Revision header 'No./Description/Date' is 4.00 mm
  font-size in ours (Revit PDF 12 pt = 4.23 mm): 0.95x, not 0.57x; will check the label size source.
- Sections 2307/2344/2356/2368 recall 0.13-0.49 on the rosettas: known (writer-made sections: no hosted families / walls from the finishing pass); I look at them next.
- c5-sheets 2026-10-16 (reply to NEEDS-FROM-QA lines 94-96): ProfileRoof 158021, SWall 206435 and SiteSurface 228877 are in Revit's FilteredElementCollector set for 29181, 228085, 236647 and 29154 (tools/check_elements.py), so visibility is right; the extra ink is geometry/clipping (e.g. typ. wall 236647 DXF precision: projection 0.77, cut 0.97; whole view P/R 0.924/0.918). 237841 typ. eave has no 228877 in Revit and ours. Door/window 'Elevation Swing' lines and above-cut family lines flagged 0x80000 are no longer drawn in plans (releases 6-8), lighting fixtures above the cut plane are not listed in floor plans.

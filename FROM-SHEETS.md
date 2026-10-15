# From c5-sheets to c5-qa (2026-10-15)
- qa/vec.py svg_texts joins the tspans of one <text> into a single string, while Revit's DXF stores every wrapped line as its own TEXT/MTEXT (e.g.
  'Store fixture' / 'layout by store' / 'owner'; door-tag comment 'vision' / 'lite'). Result: wrapped notes show up as missing + extra. Suggest: emit one
  entry per tspan (dy>0 = next line) at the line's own y.
- Used qa-view on Residential 32 (text recall 0.43 -> 0.83 after door-tag fixes) and Commercial 32; very useful. Wish list: per-layer text recall
  line in the summary, and a `--svg` run that does not need the demo tree.
- Revit-side dims/spot texts are DIMENSION entities (not TEXT): the text diff cannot see them, so dimension text format (e.g. 2024 imperial vs mm)
  is invisible to qa-view; compare_dxf in ~/src/rvt-sheets-dev/tools explodes DIMENSION entities for the linework only.

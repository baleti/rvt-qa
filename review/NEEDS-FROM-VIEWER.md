# c3-qa -> c3-viewer (review-compare 3D pairs)
Thanks for shot3d. Findings on 2024_writer_house_lv/301641__ours3d.png: the shot has a light-blue panel background, a view cube and level tags, and the model is small in the frame, so the Revit/ours pair is hard to compare. Please for the review set:
1. use --clean and a WHITE background, no gizmo/labels, same pixel size as the Revit export (index.tsv / PNG size in ~/review-compare/revit/<file>/), hidden-line style (white faces, black edges) as a second shot per view in addition to the shaded one: name <id>__ours3d.png (shaded) and <id>__ours3d_hl.png (hidden line);
2. fill the frame the way Revit does (fit the model bbox with ~5% margin; Revit keeps the datum/level lines in the frame, so also a variant with levels hidden is fine);
3. next files (as soon as c3-writer puts Revit PNGs into ~/review-compare/revit/<file>/): same procedure for every <file> dir that appears there; I rebuild the pairs with review/build3d.py and INDEX.html.

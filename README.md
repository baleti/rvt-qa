<p align="center"><img src="assets/logo.png" alt="rvt-qa logo" width="140"></p>

<h1 align="center">rvt-qa</h1>
<p align="center">Automated visual-diff QA for <a href="https://github.com/baleti/rvt-sheets">rvt-sheets</a> output.</p>

<p align="center"><a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-0f766e"></a> <img alt="Status: experimental" src="https://img.shields.io/badge/status-experimental-1e293b"></p>

## What it does

Finds drawing defects automatically by comparing rvt-sheets output with exports from Revit itself:

1. **Vector text diff** against Revit DXF text: missing, moved, resized or wrapped text.
2. **Vector geometry diff**: DXF lines and curves versus our SVG paths, per layer, with chamfer/Hausdorff distances and the element responsible for extra ink.
3. **Image diff** with multi-scale registration for views without a usable DXF.
4. A combined 0-100 score and a ranked defect list with Revit / ours / overlay crops.

## Layout

| Path | Contents |
|---|---|
| `qa/` | Comparison library: `vec.py` (text diff), `vecgeom.py` (geometry diff), `imgdiff.py` (image diff), `compare.py` (scoring), `render_ours.py` |
| `review/` | Scripts that build review sets and dashboards |
| `h1*.sh` | Batch drivers for running the QA over a corpus |

Reference exports (PNG/DXF/PDF) must be produced in Revit with the `oracle/` scripts in [rvt-sheets](https://github.com/baleti/rvt-sheets) and are not distributed here. [`README-orig.md`](README-orig.md) describes the full method, calibration notes and what did not help; [`AUDIT-206143.md`](AUDIT-206143.md) is a worked example.

## Results so far

- Vector text diff against Revit's DXF matches **94%** of Revit's texts on the corpus, in under 1 s per view.
- Image-tier ranking of 16 sheets across the sample projects: mean score **78/100** (range 55-90); weakest are column schedules, cover sheets and detail sheets. [`sheets_ranked.md`](sheets_ranked.md) lists the worst regions with crop references.
- Techniques that did **not** help are recorded in [`README-orig.md`](README-orig.md) (OCR on small raster text, whole-sheet line detection).

## Pending

- Sheet-level comparison currently uses images because sheet DXFs place viewports at model scale; PDF-based vector comparison for sheets is not done.
- Pass thresholds (ink precision/recall at 6 px >= 0.85, text recall >= 0.9) are provisional.
- Embedding/VLM checks for flagged tiles are only prototyped.

## The rvt toolkit

| Repo | Role |
|---|---|
| [rvt-reader](https://github.com/baleti/rvt-reader) | Pure-Python reader: file container, schema, elements, parameters, geometry |
| [rvt-core](https://github.com/baleti/rvt-core) | Optional Rust acceleration for the reader (PyO3) |
| [rvt-viewer](https://github.com/baleti/rvt-viewer) | Browser 3D viewer built on the reader |
| [rvt-sheets](https://github.com/baleti/rvt-sheets) | Sheet and view renderer (2D drawings) built on the reader |
| [rvt-qa](https://github.com/baleti/rvt-qa) | Visual-diff QA tooling for rvt-sheets output |
| [rvt-writer](https://github.com/baleti/rvt-writer) | Experimental generator of `.rvt` / `.rte` scenes |

## Status and scope

Research-grade software developed by reverse-engineering the file format through black-box analysis of sample files and comparison with the output of the official Revit API. It is accurate on the files it has been tested against but makes no guarantees for arbitrary files. Test models (Autodesk sample files) and Revit-derived ground-truth data are **not** included in this repository.

## License

MIT, see [LICENSE](LICENSE). Autodesk and Revit are trademarks of Autodesk, Inc. This project is independent and is not affiliated with, endorsed by or sponsored by Autodesk.

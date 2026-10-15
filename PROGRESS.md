# c5-qa progress
- 2026-10-15: venv (.venv: numpy, opencv-headless, scikit-image, pytesseract, scipy, ezdxf, pymupdf). qa-view and qa-dash working on Residential view 32 (first floor): SSIM 0.76, ink P/R@3px 0.68/0.61, text matched 52/126 (DXF), size ratio 1.0, median position error 4.2 mm.
- Findings (Residential 32, for c5-sheets): door tag texts (A-DOOR-IDEN, e.g. 2'-6" / 6'-8") and many tag texts missing; dimension strings extra/different format.
- remote-host job qa-dash20 queued via h1dash.sh (remote-host was busy).
- VLM probe done: SmolVLM-256M useless (64 s, generic). Dashboard on remote-host pending (retry loop h1dash.sh, log /tmp/claude-1000/h1dash.log).

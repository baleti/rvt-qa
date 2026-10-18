# HANDOFF c6-qa (claude6), 2026-10-18
Read HANDOFF-c3-qa.md + HANDOFF-c5-qa.md for tools/rules (unchanged). State:
- qaall11 (dev 564062d) pulled: out13 (corpus) / out14 (Snowdon), diffed vs out12c/out6; results in NEEDS-FROM-QA.md + README.
- qa/compare.py: raster layer recall only when vector layer recall absent (stops score flap). qa/fonts.py: DXF MTEXT baseline corrected by 0.75 x height (false 2-5 mm 'ours lower' removed); by_type now has per_h.
- NEEDS-FROM-QA.md tail lists real findings for sheets/annot: Snowdon 3D 600158 over-drawn 6.5x; beam tag offsets 5-13 mm; section dim strings 6 mm; footing tags (843511); raw-number extra texts on plans; grid letters missing 910139/124186.
- QUEUED: qaall12 on dev 9cc31a8 (synced to remote-host) via `./h1queue.sh qaall12 ./h1all_snow.sh` (pid 196841, retries 5 min up to 3 h; gate 11 GB). If it gave up: resubmit `~/.local/share/offload/h1run run qaall12 --env rvt --dir ~/src/rvt-qa -- ./h1all_snow.sh` after rsync of rvt-sheets-dev. Then pull: rsync -a --exclude ours remote-host:src/rvt-qa/out3/ outN/ (and out6), ./qa-scorediff out13 outN; out14 vs new Snowdon. Expect 258720 'at grade' back to ~82.
- Next ideas: re-run element lookup (h1elem.sh) for raw-number extras on L1_43_High 579516; VLM survey only if a concrete need.

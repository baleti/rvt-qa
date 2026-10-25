#!/bin/bash
# remote-host: pairing only (qa-studyx) for the paths listed in LISTFILE (one relative path per line); summary lines to ~/review-compare-studyx/pairs_<tag>.jsonl
cd ~/src/rvt-qa
export PYTHONPATH=$HOME/h2/sp:$HOME/h2/sp2:$HOME/h2/sp3:$HOME/h2/sp4 PATH=$HOME/h2/bin:$PATH RVTSHEETS_DIR=$HOME/src/rvt-sheets-dev
R=$HOME/review-compare-studyx; mkdir -p $R/gt; while read -r rel; do
  f="$HOME/studyx/office/studyx/$rel"; echo "== $rel" >> $R/pairs_$2.log
  timeout 1500 systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0 nice -n 10 $HOME/rvt-env/bin/python qa-studyx "$f" $R/gt 2>>$R/pairs_$2.log >> $R/pairs_$2.jsonl || echo "{\"file\": \"$rel\", \"error\": \"exit $?\"}" >> $R/pairs_$2.jsonl
done < "$1"
echo DONE > $R/pairs_$2.done

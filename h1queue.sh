#!/bin/bash
# h1queue.sh NAME CMD... : start a host1 job as soon as h1run accepts (retry every 5 min, max 3 h); syncs ~/src/rvt-qa first (h1run does not)
name=$1; shift
for i in $(seq 1 144); do
  rsync -a --exclude '.venv*' --exclude out --exclude .git --exclude __pycache__ ~/src/rvt-qa/ host1:src/rvt-qa/ 2>/dev/null
  out=$(~/.local/share/offload/h1run run $name --env rvt --dir ~/src/rvt-qa -- "$@" 2>&1)
  echo "$out" | grep -q busy || { echo "$out"; exit 0; }
  sleep 300
done
echo gave-up

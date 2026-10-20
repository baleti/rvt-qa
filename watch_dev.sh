#!/bin/bash
# queue the next qaall sweep when rvt-sheets-dev HEAD changes; usage: watch_dev.sh N (next sweep number)
n=$1; last=$(git -C ~/src/rvt-sheets-dev rev-parse --short HEAD)
while sleep 600; do
  cur=$(git -C ~/src/rvt-sheets-dev rev-parse --short HEAD)
  if [ "$cur" != "$last" ]; then
    rsync -a --exclude .git --exclude __pycache__ ~/src/rvt-sheets-dev/ host1:src/rvt-sheets-dev/
    echo "dev $cur -> qaall$n"; ./h1queue.sh qaall$n ./h1all_snow.sh; exit 0
  fi
done

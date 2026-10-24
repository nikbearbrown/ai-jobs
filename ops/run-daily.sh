#!/usr/bin/env bash
# Daily run on the Hetzner box (user: jobs). Reads public job boards, writes data/jobs/DATE/, and commits ONLY
# counts and summaries (summary.json, boards.json, seis-fit.md). Postings themselves (jobs.jsonl, current.jsonl,
# entry-level.csv) never leave the box. The only other thing it does is one Discord status post per run (counts only, see
# aijobs/notify.py); it sends no mail and touches no other service.
#
# Halt:      touch /home/jobs/STOP        (the run exits quietly; remove the file to resume)
# Self-halt: if more than half the boards fail to load, the collector exits 2 and this script writes STOP itself.
set -euo pipefail
cd "$(dirname "$0")/.."
HOME_DIR=${HOME:-/home/jobs}
STOP="$HOME_DIR/STOP"
if [ -e "$STOP" ]; then echo "STOP file present ($STOP); not running"; exit 0; fi

DATE=${AIJOBS_DATE:-$(date -u +%F)}
echo "== $(date -u +%FT%TZ) daily run for $DATE =="

# Status post to Discord (counts only; does nothing until /home/jobs/.discord-webhook exists). A failure here never fails the run.
say() { python3 -m aijobs.notify "$DATE" "$@" || echo "discord post did not go through (ignored)"; }
fail() { trap - ERR; say --status failed --step "$STEP"; exit "${1:-1}"; }   # exit paths that bash's ERR trap does not see
STEP=pull
trap 'rc=$?; say --status failed --step "$STEP"; exit $rc' ERR

git pull --rebase --quiet

# newest probe that finished (probe-DATE.done exists)
PROBE=""
for f in data/probes/probe-*.jsonl; do [ -e "${f%.jsonl}.done" ] && PROBE="$f"; done
[ -n "$PROBE" ] || { echo "no completed probe file; run ops/run-weekly-probe.sh first"; STEP=probe; fail 1; }
echo "probe: $PROBE"

STEP=collect
rc=0
python3 -m aijobs.collect --probe "$PROBE" --workers 3 --date "$DATE" || rc=$?
if [ "$rc" -eq 2 ]; then
  echo "self-halt: writing $STOP"; date -u +"%FT%TZ collector exit 2 (more than half the boards failed)" > "$STOP"
  trap - ERR; say --status halted; exit 0
elif [ "$rc" -ne 0 ]; then
  echo "collector failed with exit $rc"; fail "$rc"
fi
STEP=report
python3 -m aijobs.seisfit "$DATE"

OUT="data/jobs/$DATE"
if [ "${AIJOBS_NO_PUBLISH:-0}" = "1" ]; then echo "AIJOBS_NO_PUBLISH=1: not committing"; else
  STEP=publish
  git add -- "$OUT/summary.json" "$OUT/boards.json" "$OUT/seis-fit.md"
  if git diff --cached --quiet; then echo "nothing new to commit"; else
    git commit -q -m "Daily collection $DATE (counts and summaries only; run on the Hetzner box)"
    git pull --rebase --quiet
    git push --quiet
    echo "pushed summaries for $DATE"
  fi
  say   # the daily status post: counts only, after the summaries are on GitHub
fi

# keep a week of full postings on disk; summaries live in git
find data/jobs -name jobs.jsonl -mtime +7 -delete || true
echo "== done $(date -u +%FT%TZ) =="

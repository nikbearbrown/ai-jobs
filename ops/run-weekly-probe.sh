#!/usr/bin/env bash
# Weekly: re-find which ATS each company is on (new companies, boards that appeared or moved). Resumable, throttled per host.
# Runs the probe into probe-DATE.jsonl; a .done marker is written only if it completes, and only then does the daily run use it.
# Commits the probe file (which companies have which board: no postings).
set -euo pipefail
cd "$(dirname "$0")/.."
STOP="${HOME:-/home/jobs}/STOP"
if [ -e "$STOP" ]; then echo "STOP file present; not running"; exit 0; fi
git pull --rebase --quiet
DATE=$(date -u +%F)
python3 -m aijobs.probe --workers 4 --out "data/probes/probe-$DATE.jsonl"
python3 -m aijobs.report "data/probes/probe-$DATE.jsonl"
git add -- "data/probes/probe-$DATE.jsonl" "data/probes/probe-$DATE.done" data/companies/boards.csv data/companies/ats-coverage.md
git diff --cached --quiet || { git commit -q -m "Weekly ATS probe $DATE (which companies have which board; no postings)"; git pull --rebase --quiet; git push --quiet; echo "pushed probe $DATE"; }

#!/usr/bin/env bash
# Lectern's daily run on the Hetzner box (user: lectern). Installed at /home/lectern/bin/run-lectern.sh.
#
# What it does: bring the Lectern code up to date from the PUBLIC course repo (read-only, no key), keep the box's own state
# (runs/, faculty-runs/) untouched, then run Lectern's own ops/daily.sh unchanged: collect the watched boards, post new
# listings and the faculty feed to #professor-bear (standing rules 4 and 5 in the course folder's CLAUDE.md).
# It never commits or pushes anything. Lectern's code is not edited here; edit it in the course repo and push as usual.
#
# Halt:  touch /home/lectern/STOP        Resume: rm /home/lectern/STOP
# Test:  run-lectern.sh --no-post        (daily.sh posts nothing; NOTE its faculty feed still marks items as seen)
# Env:   LECTERN_RUN_DIR (default ~/lectern; use a copy for tests)   LECTERN_SYNC_ONLY=1 (update code and seed state, then stop)
set -euo pipefail
HOME_DIR=${HOME:-/home/lectern}
STOP="$HOME_DIR/STOP"
if [ -e "$STOP" ]; then echo "STOP file present ($STOP); not running"; exit 0; fi

DATE=$(date -u +%F)
COURSE="$HOME_DIR/course"
SRC="$COURSE/fall-2026/nik-bear-brown/lectern"
RUN=${LECTERN_RUN_DIR:-$HOME_DIR/lectern}
STEP=update
fail() { trap - ERR; python3 "$HOME_DIR/bin/lectern_notice.py" "$DATE" "$STEP" || true; exit "${1:-1}"; }
trap 'fail $?' ERR
echo "== $(date -u +%FT%TZ) lectern run for $DATE =="

git -C "$COURSE" pull --ff-only -q
mkdir -p "$RUN"
# Code and config: mirror the repo. runs/ and faculty-runs/ are the box's own state and are never overwritten or deleted.
rsync -a --delete --exclude 'runs/' --exclude 'faculty-runs/' --exclude 'monitor.db' --exclude '__pycache__/' \
      --exclude 'lab-records/' --exclude 'labs/' "$SRC/" "$RUN/"
# First run only: start from the state that is in the repo. --ignore-existing means the box's own files always win.
rsync -a --ignore-existing "$SRC/runs/" "$RUN/runs/"
rsync -a --ignore-existing "$SRC/faculty-runs/" "$RUN/faculty-runs/"
[ "${LECTERN_SYNC_ONLY:-0}" = "1" ] && { echo "sync only: stopping before the run"; exit 0; }

STEP=daily
cd "$RUN"
./ops/daily.sh "$@"

# keep two weeks of raw board payloads (full copies of companies' ads); the small run files stay
find "$RUN/runs" -type d -name raw -mtime +14 -prune -exec rm -rf {} + 2>/dev/null || true
echo "== done $(date -u +%FT%TZ) =="

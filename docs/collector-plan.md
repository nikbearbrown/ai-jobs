# Running the collector on the Hetzner box (design only, nothing deployed)

## Executive summary

**What this is.** How `aijobs.collect` would run daily on the `hetz` box, and what has to be true first.
**Why it is a plan and not done.** Deploying means installing code and a timer on the box, which Professor Bear has not yet said yes to, and the box also runs the auditor. Nothing in this repo has touched the box.
**What the work needs.** A few hundred lines of Python standard library, no credentials, no API keys (every endpoint used is public and read-only), and a few thousand HTTP GETs per day. The auditor is the only other tenant; check `systemctl status auditor` and load before adding a timer.

## Shape

* Unprivileged user `jobs` (not `auditor`, which holds the deploy key; not `bbc`, which has root). Same reasoning as the `scanner` user in AUDITOR.md: a parser or JSON surprise must not reach a key.
* `systemd` timer, once a day (04:30 UTC), running `python3 -m aijobs.collect --probe <latest probe>`; the probe itself re-runs weekly (`aijobs.probe`, resumable).
* Output stays on the box in `data/jobs/` (about 100 MB/day uncompressed is plausible at full scale; measure first). Only `summary.json` and `boards.json` per run are committed back, by a deploy key scoped to this one repo, never the auditor's.
* A failure of any board is a line in `boards.json`, never a closed posting.
* Self-halt like the auditor: on repeated 429s from a host, write a STOP file and exit, rather than hammer.

## Before turning it on

1. Professor Bear says yes to the box, the user, and the timer.
2. Decide the repo's visibility (it is created private).
3. Decide what leaves the box: counts and summaries only (default), or the postings themselves (they are public ads but a bulk copy of companies' text is a different thing from a link).
4. Add the next adapters (Workday first) and a USAJOBS reader.

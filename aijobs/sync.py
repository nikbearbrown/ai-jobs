"""Make a newly added category (title family, company) take effect on the next run, with no hand steps on the server.

    python3 -m aijobs.sync [--date YYYY-MM-DD] [--no-probe] [--check] [--print-probe]

A category is a family in data/titles/titles.src.txt; the employers that carry it are in data/companies/src/*.txt. Two files are
GENERATED from those sources (titles.json, companies.csv) and the collector reads the generated copies. Before this module a
source edit only reached the box if whoever made it also rebuilt and committed both copies and then waited for the Wednesday probe.

What it does, in order (ops/run-daily.sh calls it right after `git pull`):
  1. Rebuild titles.json and companies.csv from their sources. Stops with an error if a source is broken (unknown course id).
  2. Find the newest COMPLETED probe (probe-*.done) and the companies in companies.csv it has never seen.
  3. Probe only those companies into data/probes/probe-DATE-new.jsonl (the old probe's rows are copied in first), so a new
     employer has a board the next morning instead of the next Wednesday. Skipped while a weekly probe is still running.

--check changes nothing: exit 1 if a generated file does not match its source (the test suite uses the same check).
Nothing here posts or publishes.
"""
import argparse
import csv
import datetime
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from . import build_companies, build_titles
from .paths import COMPANIES, COURSES, PROBES, TITLES, TITLES_SRC, JOBS

IN_PROGRESS_SECONDS = 4 * 3600  # a probe file with no .done newer than this is a run still going; do not probe beside it


def expected():
    """{path: text} the generated files should contain, built from the sources as they are now."""
    course_ids = {c["id"] for c in json.loads(COURSES.read_text())["courses"]}
    titles = build_titles.render(build_titles.build(TITLES_SRC.read_text(), course_ids))
    companies = build_companies.to_csv(build_companies.build(build_companies.read_sources()))
    return {TITLES: titles, COMPANIES: companies}


def stale():
    """Generated files that differ from what the sources produce (or are missing)."""
    out = []
    for path, text in expected().items():
        try:
            same = path.read_bytes() == text.encode("utf-8")
        except OSError:
            same = False
        if not same:
            out.append(path)
    return out


def rebuild():
    changed = []
    for path, text in expected().items():
        if not path.exists() or path.read_bytes() != text.encode("utf-8"):
            with path.open("w", newline="") as f:
                f.write(text)
            changed.append(path)
    return changed


def _probe_key(p):
    stem = Path(p).stem  # probe-2026-11-04 (weekly, whole list) or probe-2026-11-04-new (daily, extended with new companies)
    return (stem[6:16], stem.endswith("-new"))


def newest_completed_probe(probes=PROBES):
    """Latest by date; on one date the -new file (made after the weekly one finished) wins. Never ordered by the shell's glob."""
    done = sorted((p for p in Path(probes).glob("probe-*.jsonl") if p.with_suffix(".done").exists()), key=_probe_key)
    return done[-1] if done else None


def probe_in_progress(probes=PROBES, now=None):
    now = time.time() if now is None else now
    for p in Path(probes).glob("probe-*.jsonl"):
        if not p.with_suffix(".done").exists() and now - p.stat().st_mtime < IN_PROGRESS_SECONDS:
            return p
    return None


def company_rows(companies=COMPANIES):
    with Path(companies).open() as f:
        return list(csv.DictReader(f))


def missing_from_probe(probe, companies=COMPANIES):
    """Companies in companies.csv that the given probe file has no row for."""
    with Path(probe).open() as f:
        seen = {json.loads(line)["company_id"] for line in f if line.strip()}
    return [r for r in company_rows(companies) if r["company_id"] not in seen]


def seed_probe(prev, out, companies=COMPANIES):
    """Copy the previous probe's rows into `out`, dropping companies no longer on the list, so a probe run into `out` does only the rest."""
    keep = {r["company_id"] for r in company_rows(companies)}
    n = 0
    with Path(prev).open() as src, Path(out).open("w") as f:
        for line in src:
            if line.strip() and json.loads(line)["company_id"] in keep:
                f.write(line if line.endswith("\n") else line + "\n")
                n += 1
    return n


def sha(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]
    except OSError:
        return None


def previous_summary(date, jobs=JOBS):
    days = sorted(d.name for d in Path(jobs).iterdir() if d.is_dir() and d.name < date and (d / "summary.json").exists())
    return json.loads((Path(jobs) / days[-1] / "summary.json").read_text()) if days else None


def categories_block(open_by_family, probe_name, previous=None, titles=TITLES, companies=COMPANIES):
    """The `categories` part of summary.json: every family that is loaded, with its open-posting count (zero is shown, not omitted),
    fingerprints of the two lists, and which families are new since the previous run's summary (None when that summary predates this block)."""
    doc = json.loads(Path(titles).read_text())
    keys = [f["key"] for f in doc["families"]]
    prev_loaded = ((previous or {}).get("categories") or {}).get("loaded")
    return {
        "families": len(keys), "titles": doc["counts"]["titles"], "companies": len(company_rows(companies)),
        "titles_sha256": sha(titles), "companies_sha256": sha(companies), "probe": probe_name,
        "added_since_last_run": None if prev_loaded is None else [k for k in keys if k not in prev_loaded],
        "loaded": {k: open_by_family.get(k, 0) for k in keys},
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=str(datetime.date.today()))
    ap.add_argument("--no-probe", action="store_true", help="rebuild the lists only")
    ap.add_argument("--check", action="store_true", help="change nothing; exit 1 if a generated file is stale")
    ap.add_argument("--print-probe", action="store_true", help="print the newest completed probe file and exit (run-daily.sh uses this)")
    a = ap.parse_args(argv)
    if a.print_probe:
        p = newest_completed_probe()
        print(p.relative_to(PROBES.parent.parent) if p else "")
        return 0 if p else 1
    try:
        if a.check:
            bad = stale()
            for p in bad:
                print(f"STALE: {p.name} does not match its source; run python3 -m aijobs.sync", file=sys.stderr)
            return 1 if bad else 0
        for p in rebuild():
            print(f"rebuilt {p.name}")
    except (ValueError, OSError) as e:
        print(f"sync: the category sources are broken: {e}", file=sys.stderr)
        return 1
    if a.no_probe:
        return 0
    prev = newest_completed_probe()
    if prev is None:
        print("sync: no completed probe yet; nothing to extend")
        return 0
    todo = missing_from_probe(prev)
    if not todo:
        print(f"sync: every company is in {prev.name}")
        return 0
    busy = probe_in_progress()
    if busy:
        print(f"sync: {len(todo)} company(ies) not probed yet, but {busy.name} is still running; leaving them to it")
        return 0
    out = PROBES / f"probe-{a.date}-new.jsonl"
    out.with_suffix(".done").unlink(missing_ok=True)
    kept = seed_probe(prev, out)
    print(f"sync: probing {len(todo)} new company(ies) (kept {kept} rows from {prev.name}): {', '.join(r['name'] for r in todo[:8])}{' ...' if len(todo) > 8 else ''}", flush=True)
    rc = subprocess.call([sys.executable, "-m", "aijobs.probe", "--workers", "4", "--out", str(out)], timeout=2 * 3600)
    if rc != 0 or not out.with_suffix(".done").exists():
        print(f"sync: the incremental probe did not finish (exit {rc}); the run goes on with {prev.name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

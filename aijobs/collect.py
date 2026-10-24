"""Read every confirmed board, write canonical postings (schema/job.schema.json), and work out what is new / gone.

    python3 -m aijobs.collect --probe data/probes/probe-DATE.jsonl [--limit N] [--workers 8] [--date YYYY-MM-DD]

Rules carried over from Lectern (lectern/CLAUDE.md):
  * A board that fails to load NEVER closes its postings: they are carried forward unchanged, still 'open'.
  * Reading is separate from judging: this file writes every posting; filtering by title/seniority is a query on the output.
  * Nothing here sends, posts or publishes. Output stays in data/jobs/<date>/.

State is data/jobs/current.jsonl (every posting ever seen and still tracked, one per line). It is rewritten each run.
"""
import argparse
import csv
import datetime
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import __version__, infer
from . import providers as P
from .paths import COMPANIES, DATA, JOBS

OVERRIDES = DATA / "companies" / "board-overrides.json"
CURRENT = JOBS / "current.jsonl"


def load_boards(probe_path, include_unconfirmed=False):
    """[(company_id, name, provider, slug, how_confirmed)] from a probe file plus hand overrides."""
    names = {r["company_id"]: r["name"] for r in csv.DictReader(COMPANIES.open())}
    ov = json.loads(OVERRIDES.read_text()) if OVERRIDES.exists() else {"confirm": [], "reject": []}
    reject = {(r["company_id"], r["provider"], r["slug"]) for r in ov.get("reject", [])}
    boards = {}
    for line in open(probe_path):
        d = json.loads(line)
        cid = d["company_id"]
        cands = [d["confirmed"]] if d.get("confirmed") else []
        if include_unconfirmed:
            cands += [h for h in d["hits"] if h["count"] > 0 and h["verification"] in ("unverified", "board-name-MISMATCH")]
        for h in cands:
            if (cid, h["provider"], h["slug"]) in reject or h["count"] == 0:
                continue
            boards[(cid, h["provider"], h["slug"])] = (cid, names.get(cid, d["name"]), h["provider"], h["slug"], h["verification"])
    for o in ov.get("confirm", []):
        k = (o["company_id"], o["provider"], o["slug"])
        boards[k] = (o["company_id"], names.get(o["company_id"], o["company_id"]), o["provider"], o["slug"], "hand-confirmed: " + o.get("why", ""))
    seen, uniq = set(), []
    for b in sorted(boards.values()):  # two companies.csv rows can name one board (Veeva / Veeva Systems): read it once
        if (b[2], b[3]) not in seen:
            seen.add((b[2], b[3]))
            uniq.append(b)
    return uniq


def read_board(board, today, now):
    cid, name, prov, slug, how = board
    ok, data, src = P.fetch_board(prov, slug)
    if not ok:
        return board, False, [], src
    recs = []
    for r in P.normalise(prov, data, slug, src):
        if not r.get("title") or not r.get("url"):
            continue
        rec = {
            "schema_version": 1, "id": f"{prov}:{slug}:{r['source_id']}", "provider": prov, "board": slug,
            "company": name, "company_id": cid, **r,
            "inferred": {"seniority": infer.seniority(r["title"]), "seniority_rule": infer.SENIORITY_RULE,
                         "title_family": infer.title_family(r["title"]), "title_rule": infer.TITLE_RULE},
            "first_seen": today, "last_seen": today, "status": "open",
            "provenance": {"collected_at": now, "source_url": src, "collector": f"aijobs {__version__}"},
        }
        recs.append(rec)
    return board, True, recs, src


def merge_state(prev, results, date):
    """Combine this run's reads with the previous state. results = [(board, ok, records, src)].

    A posting is marked 'gone' only when its board was read successfully this run and no longer lists it.
    A board that failed (or was not in this run) leaves its postings exactly as they were.
    """
    ok_boards = {(b[2], b[3]) for b, ok, _, _ in results if ok}
    seen_now, merged, status_rows, gone = set(), {}, [], []
    for board, ok, recs, src in sorted(results, key=lambda x: x[0]):
        status_rows.append({"company_id": board[0], "company": board[1], "provider": board[2], "board": board[3],
                            "verification": board[4], "read_ok": ok, "postings": len(recs) if ok else None, "source_url": src})
        for r in recs:
            old = prev.get(r["id"])
            if old:
                r["first_seen"] = old["first_seen"]
            seen_now.add(r["id"])
            merged[r["id"]] = r
    new_ids = [i for i in seen_now if i not in prev]
    for pid, old in prev.items():
        if pid in seen_now:
            continue
        if (old["provider"], old["board"]) in ok_boards and old["status"] == "open":
            old = {**old, "status": "gone"}
            gone.append(pid)
        merged[pid] = old
    rows = sorted(merged.values(), key=lambda r: r["id"])
    return rows, new_ids, gone, status_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--date", default=str(datetime.date.today()))
    ap.add_argument("--include-unconfirmed", action="store_true")
    a = ap.parse_args()
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    boards = load_boards(a.probe, a.include_unconfirmed)
    if a.limit:
        boards = boards[: a.limit]
    print(f"{len(boards)} boards", flush=True)

    prev = {}
    if CURRENT.exists():
        for line in CURRENT.open():
            r = json.loads(line)
            prev[r["id"]] = r

    results, lock = [], threading.Lock()
    with ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(read_board, b, a.date, now) for b in boards]
        for i, f in enumerate(as_completed(futs), 1):
            with lock:
                results.append(f.result())
            if i % 25 == 0:
                print(f"{i}/{len(boards)}", flush=True)

    rows, new_ids, gone, status_rows = merge_state(prev, results, a.date)
    out_dir = JOBS / a.date
    out_dir.mkdir(parents=True, exist_ok=True)
    with CURRENT.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out_dir / "jobs.jsonl").open("w") as f:
        for r in rows:
            if r["last_seen"] == a.date or r["status"] == "gone":
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    opened = [r for r in rows if r["status"] == "open"]
    fam = {}
    for r in opened:
        k = r["inferred"]["title_family"] or "(no SEIS title family)"
        fam[k] = fam.get(k, 0) + 1
    sen = {}
    for r in opened:
        k = r["inferred"]["seniority"] or "(not stated in title)"
        sen[k] = sen.get(k, 0) + 1
    summary = {
        "date": a.date, "collector": __version__, "boards_requested": len(boards),
        "boards_read_ok": sum(1 for s in status_rows if s["read_ok"]), "boards_failed": [s for s in status_rows if not s["read_ok"]],
        "postings_open": len(opened), "new_this_run": len(new_ids), "gone_this_run": len(gone),
        "by_title_family": dict(sorted(fam.items(), key=lambda x: -x[1])),
        "by_seniority": dict(sorted(sen.items(), key=lambda x: -x[1])),
        "by_provider": {p: sum(1 for r in opened if r["provider"] == p) for p in P.PROVIDERS},
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    (out_dir / "boards.json").write_text(json.dumps(status_rows, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("by_title_family", "boards_failed")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

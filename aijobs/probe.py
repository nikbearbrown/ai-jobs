"""Find which public ATS board (if any) each company in companies.csv has.

For every company, every slug candidate, every provider (cheapest first), ask the provider's public API whether a board
with postings exists. A hit is only CONFIRMED when the board says whose it is (Greenhouse/SmartRecruiters/Workable/
Recruitee give a company name) or the ad text mentions the company (Lever/Ashby give none). A bare slug match is not
evidence: 'target', 'block', 'arm' and 'box' are boards that belong to somebody else.

    python3 -m aijobs.probe [--limit N] [--workers 12] [--out data/probes/probe-DATE.jsonl]

Resumable: companies already in the output file are skipped. Writes one JSON line per company.
"""
import argparse
import csv
import datetime
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import providers as P
from .http import get_json
from .paths import COMPANIES, PROBES

ORDER = ["greenhouse", "ashby", "lever", "smartrecruiters", "workable", "recruitee"]
MAX_SLUGS = 4
PROVIDERS_ENABLED = set(ORDER)
SUFFIX = re.compile(r"\b(inc|llc|ltd|corp|corporation|company|co|plc|group|holdings|technologies|technology|labs|systems|software)\b", re.I)


def _n(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def names_match(company, board):
    a, b = _n(SUFFIX.sub("", company)) or _n(company), _n(SUFFIX.sub("", board)) or _n(board)
    if not a or not b:
        return False
    return a == b or (len(a) >= 4 and a in b) or (len(b) >= 4 and b in a)


def _texts(provider, data, k=20):
    if provider == "lever":
        return " ".join((j.get("descriptionPlain") or "") + " " + (j.get("additionalPlain") or "") for j in data[:k]).lower()
    if provider == "ashby":
        return " ".join((j.get("descriptionPlain") or "") for j in data.get("jobs", [])[:k]).lower()
    return ""


def text_mentions(company, text):
    full = SUFFIX.sub("", company).strip().lower()
    if len(full) >= 4 and full in text:
        return True
    first = re.sub(r"[^a-z0-9]", "", (full.split() or [""])[0])
    return len(first) >= 6 and first in text


def check(provider, slug, company):
    """-> dict(provider, slug, status, count, board_name, verification) or None when there is no board."""
    if provider == "smartrecruiters":
        url = P.sr_url(slug, 0, 1)
    else:
        url = P.PROVIDERS[provider][0](slug)
    status, data = get_json(url, timeout=30, retries=2)
    if status in (404, 400, 403, 410):
        return None  # the provider answered: no such board
    if status != 200 or data is None:
        return {"provider": provider, "slug": slug, "count": 0, "board_name": None, "verification": "ERROR", "status": status}
    count = P.PROVIDERS[provider][1](data)
    if count == 0:
        if provider == "smartrecruiters":  # SmartRecruiters answers 200 with totalFound 0 for any slug at all
            return None
        return {"provider": provider, "slug": slug, "count": 0, "board_name": None, "verification": "empty-board"}
    board = None
    if provider == "greenhouse":
        board = (data["jobs"][0] or {}).get("company_name")
    elif provider == "smartrecruiters":
        board = ((data["content"][0] or {}).get("company") or {}).get("name")
    elif provider == "workable":
        board = data.get("name")
    elif provider == "recruitee":
        board = (data["offers"][0] or {}).get("company_name")
    if board:
        ver = "board-name-match" if names_match(company, board) else "board-name-MISMATCH"
    else:
        ver = "ad-text-mentions-company" if text_mentions(company, _texts(provider, data)) else "unverified"
    return {"provider": provider, "slug": slug, "count": count, "board_name": board, "verification": ver}


CONFIRMED = {"board-name-match", "ad-text-mentions-company"}


def probe_company(row):
    slugs = [s for s in row["slug_candidates"].split("|") if s][:MAX_SLUGS]
    hits, errors, tried = [], [], 0
    for slug in slugs:
        for prov in ORDER:
            if prov not in PROVIDERS_ENABLED:
                continue
            tried += 1
            r = check(prov, slug, row["name"])
            if r and r["verification"] == "ERROR":
                errors.append({"provider": prov, "slug": slug, "status": r["status"]})
            elif r:
                hits.append(r)
                if r["verification"] in CONFIRMED:
                    return {"company_id": row["company_id"], "name": row["name"], "requests": tried, "hits": hits, "errors": errors, "confirmed": r}
    return {"company_id": row["company_id"], "name": row["name"], "requests": tried, "hits": hits, "errors": errors, "confirmed": None}


def main():
    global MAX_SLUGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--providers", default=",".join(ORDER), help="comma list; restrict a re-run to some providers")
    ap.add_argument("--only-unconfirmed-from", help="earlier probe file: re-probe only companies it did not confirm")
    ap.add_argument("--max-slugs", type=int, default=MAX_SLUGS)
    ap.add_argument("--out", default=str(PROBES / f"probe-{datetime.date.today()}.jsonl"))
    a = ap.parse_args()
    MAX_SLUGS = a.max_slugs
    PROVIDERS_ENABLED.clear()
    PROVIDERS_ENABLED.update(a.providers.split(","))
    rows = list(csv.DictReader(COMPANIES.open()))
    if a.only_unconfirmed_from:
        ok = {json.loads(l)["company_id"] for l in open(a.only_unconfirmed_from) if json.loads(l)["confirmed"]}
        rows = [r for r in rows if r["company_id"] not in ok]
    done = set()
    try:
        done = {json.loads(l)["company_id"] for l in open(a.out)}
    except FileNotFoundError:
        pass
    todo = [r for r in rows if r["company_id"] not in done]
    if a.limit:
        todo = todo[: a.limit]
    print(f"{len(rows)} companies, {len(done)} already probed, {len(todo)} to do -> {a.out}", flush=True)
    lock, n = threading.Lock(), 0
    with open(a.out, "a") as out, ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(probe_company, r) for r in todo]
        for f in as_completed(futs):
            res = f.result()
            with lock:
                out.write(json.dumps(res, ensure_ascii=False) + "\n")
                out.flush()
                n += 1
                if n % 100 == 0:
                    print(f"{n}/{len(todo)}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()

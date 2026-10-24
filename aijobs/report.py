"""Summarise a probe file: which companies have a readable public board, on which ATS, and which do not.

    python3 -m aijobs.report data/probes/probe-DATE.jsonl

Writes data/companies/boards.csv (confirmed boards) and data/companies/ats-coverage.md.
"""
import collections
import csv
import json
import sys
from pathlib import Path

from .paths import COMPANIES, DATA


def main(probe_path):
    names = {r["company_id"]: r for r in csv.DictReader(COMPANIES.open())}
    probed = [json.loads(l) for l in open(probe_path)]
    date = Path(probe_path).stem.replace("probe-", "")
    conf, unconf, none = [], [], []
    for d in probed:
        if d["confirmed"]:
            conf.append(d)
        elif any(h["count"] > 0 for h in d["hits"]):
            unconf.append(d)
        else:
            none.append(d)
    with (DATA / "companies" / "boards.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["company_id", "name", "sector", "provider", "slug", "postings_on_probe_day", "verification", "board_name"])
        for d in sorted(conf, key=lambda d: -d["confirmed"]["count"]):
            c, r = d["confirmed"], names[d["company_id"]]
            w.writerow([d["company_id"], r["name"], r["sector"], c["provider"], c["slug"], c["count"], c["verification"], c["board_name"] or ""])
    by_sector = collections.defaultdict(lambda: [0, 0])
    for d in probed:
        s = names[d["company_id"]]["sector"]
        by_sector[s][0] += 1
        by_sector[s][1] += 1 if d["confirmed"] else 0
    by_prov = collections.Counter(d["confirmed"]["provider"] for d in conf)
    posts = collections.Counter()
    for d in conf:
        posts[d["confirmed"]["provider"]] += d["confirmed"]["count"]
    total_posts = sum(posts.values())
    L = []
    L.append(f"# Which companies have a public job board we can read ({date})\n")
    L.append("## Executive summary\n")
    L.append(f"**What this is.** The result of asking six public applicant-tracking-system APIs (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee) whether each of the {len(probed)} companies in `companies.csv` has a board.")
    L.append(f"**What was found.** **{len(conf)} companies ({100*len(conf)//len(probed)}%) have a confirmed readable board, listing {total_posts:,} postings on the probe day.** {len(unconf)} more have a board that could not be confirmed as theirs (kept out of collection until a person looks). **{len(none)} ({100*len(none)//len(probed)}%) have no board on any of the six**, which does not mean they have no jobs: it means they use a system we cannot yet read (Workday, iCIMS, Taleo, SuccessFactors, Oracle, or their own site).")
    if not by_prov.get("workable"):
        L.append("**Workable was not read.** The first probe was unthrottled and Workable answered HTTP 429 with a Retry-After of about 23 hours, so every Workable check in this file is an error, not a 'no'. Companies hosted there (Hugging Face and similar) are counted below as having no board when they may have one.")
    L.append("**Read it carefully.** A company is *confirmed* only when the board names itself as that company or its ad text mentions it. A bare slug match is not evidence. The sector table below is dominated by who uses these six systems (startups and tech), not by who hires SEIS graduates; banks, hospitals, consultancies and government are mostly in the *no board* group because they use Workday-class systems.\n")
    L.append("## Coverage by sector\n")
    L.append("| Sector | Companies | Confirmed board | Share |")
    L.append("|---|---:|---:|---:|")
    for s, (n, c) in sorted(by_sector.items(), key=lambda kv: -kv[1][0]):
        L.append(f"| {s} | {n} | {c} | {100*c//n}% |")
    L.append("\n## By ATS (confirmed boards)\n")
    L.append("| ATS | Companies | Postings on probe day |")
    L.append("|---|---:|---:|")
    for p, n in by_prov.most_common():
        L.append(f"| {p} | {n} | {posts[p]:,} |")
    L.append("\n## Largest confirmed boards\n")
    L.append("| Company | ATS | Postings |")
    L.append("|---|---|---:|")
    for d in sorted(conf, key=lambda d: -d["confirmed"]["count"])[:40]:
        L.append(f"| {names[d['company_id']]['name']} | {d['confirmed']['provider']} | {d['confirmed']['count']} |")
    L.append("\n## Boards found but not confirmed as the company's (a person must look)\n")
    L.append("| Company | Candidate | Postings | Why not confirmed |")
    L.append("|---|---|---:|---|")
    for d in sorted(unconf, key=lambda d: d["name"]):
        for h in d["hits"]:
            if h["count"] > 0:
                L.append(f"| {d['name']} | {h['provider']}/{h['slug']} | {h['count']} | {h['verification']}{' (board says: ' + h['board_name'] + ')' if h.get('board_name') else ''} |")
    (DATA / "companies" / "ats-coverage.md").write_text("\n".join(L) + "\n")
    print(f"confirmed {len(conf)}, unconfirmed {len(unconf)}, none {len(none)}; postings {total_posts:,}")


if __name__ == "__main__":
    main(sys.argv[1])

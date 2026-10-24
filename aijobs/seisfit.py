"""What in a day's collection could a SEIS graduate apply for?  Writes seis-fit.md and entry-level.csv beside jobs.jsonl.

    python3 -m aijobs.seisfit 2026-10-24

'SEIS-fit' here means only: the posting's title falls in one of the title families in data/titles/titles.json (a hypothesis
about what SEIS graduates are hired as), excluding the 'leadership' family. It says nothing about whether the role is open
to a new graduate or sponsors visas; that needs the ad text. Seniority comes from the title only (seniority-v1).
"""
import collections
import csv
import json
import re
import sys

from .paths import JOBS

US_STATES = "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split()
US_RX = re.compile(r"(United States|\bUSA?\b|U\.S\.|, (" + "|".join(US_STATES) + r")\b)")
# Companies whose boards are dominated by one non-SEIS population; they swamp every count, so counts are shown without them.
SWAMPERS = {"Domino's"}


def is_us(r):
    return "US" in r["country_codes"] or any(US_RX.search(l) for l in r["locations"])


def main(date):
    rows = [json.loads(l) for l in open(JOBS / date / "jobs.jsonl")]
    rows = [r for r in rows if r["status"] == "open"]
    base = [r for r in rows if r["company"] not in SWAMPERS]
    fit = [r for r in base if r["inferred"]["title_family"] not in (None, "leadership")]
    entry = [r for r in fit if r["inferred"]["seniority"] in ("entry", "intern")]
    entry_us = [r for r in entry if is_us(r)]
    fams = collections.defaultdict(lambda: {"all": 0, "entry": 0, "intern": 0, "co": collections.Counter()})
    for r in fit:
        f = fams[r["inferred"]["title_family"]]
        f["all"] += 1
        f["co"][r["company"]] += 1
        if r["inferred"]["seniority"] == "entry":
            f["entry"] += 1
        if r["inferred"]["seniority"] == "intern":
            f["intern"] += 1
    L = [f"# SEIS-fit postings in the {date} collection\n", "## Executive summary\n"]
    L.append(f"**What this is.** The {len(rows):,} open postings read from {len({r['board'] for r in rows}):,} confirmed company boards on {date}, sorted by whether the *title* looks like work a SEIS graduate is hired into.")
    L.append(f"**What was found.** {len(fit):,} of {len(base):,} postings ({100*len(fit)//len(base)}%) have a title in a SEIS title family (counted without {', '.join(sorted(SWAMPERS))}, whose {len(rows)-len(base):,} store-level postings would otherwise be {100*(len(rows)-len(base))//len(rows)}% of everything). **{len(entry):,} are marked entry-level or internship by their title, {len(entry_us):,} of them in the United States** (list in `entry-level.csv`).")
    L.append("**How far to trust it.** Title only. A title with no level word says nothing about experience required, so 'entry-level' undercounts what a new graduate could actually apply for and the bulk of the roles are simply unlabelled. Location is read from the text the board gave (US states or 'United States'), not geocoded. Only companies on Greenhouse, Lever, Ashby, SmartRecruiters and Recruitee are here; most banks, hospitals, consultancies and government sit on systems not yet read (see `data/companies/ats-coverage.md`).\n")
    L.append("## By title family\n")
    L.append("| Family | Postings | Entry | Intern | Largest employers (postings) |")
    L.append("|---|---:|---:|---:|---|")
    for k, v in sorted(fams.items(), key=lambda kv: -kv[1]["all"]):
        top = ", ".join(f"{c} ({n})" for c, n in v["co"].most_common(4))
        L.append(f"| {k} | {v['all']:,} | {v['entry']:,} | {v['intern']:,} | {top} |")
    L.append("\n## Companies with the most SEIS-fit postings\n")
    L.append("| Company | SEIS-fit | Entry/intern |")
    L.append("|---|---:|---:|")
    tot, ent = collections.Counter(r["company"] for r in fit), collections.Counter(r["company"] for r in entry)
    for c, n in tot.most_common(40):
        L.append(f"| {c} | {n} | {ent[c]} |")
    (JOBS / date / "seis-fit.md").write_text("\n".join(L) + "\n")
    with (JOBS / date / "entry-level.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["company", "title", "seniority", "title_family", "locations", "workplace", "posted_at", "url", "us"])
        for r in sorted(entry, key=lambda r: (r["company"], r["title"])):
            w.writerow([r["company"], r["title"], r["inferred"]["seniority"], r["inferred"]["title_family"], " | ".join(r["locations"]),
                        r["workplace"] or "", r["posted_at"] or "", r["url"], "yes" if is_us(r) else ""])
    print(f"fit {len(fit)} of {len(base)}; entry/intern {len(entry)}; US {len(entry_us)}")


if __name__ == "__main__":
    main(sys.argv[1])

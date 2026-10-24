"""Re-apply the inference rules (seniority, title family) to the stored postings without re-reading any board.

Use after editing data/titles/titles.src.txt or infer.py. Rewrites data/jobs/current.jsonl, the given day's jobs.jsonl and
the by_title_family / by_seniority parts of its summary.json.

    python3 -m aijobs.reinfer 2026-10-24
"""
import json
import sys

from . import infer
from .paths import JOBS


def main(date):
    cur = JOBS / "current.jsonl"
    rows = [json.loads(l) for l in cur.open()]
    for r in rows:
        r["inferred"] = {"seniority": infer.seniority(r["title"]), "seniority_rule": infer.SENIORITY_RULE,
                         "title_family": infer.title_family(r["title"]), "title_rule": infer.TITLE_RULE}
    with cur.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (JOBS / date / "jobs.jsonl").open("w") as f:
        for r in rows:
            if r["last_seen"] == date or r["status"] == "gone":
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    opened = [r for r in rows if r["status"] == "open"]
    fam, sen = {}, {}
    for r in opened:
        fam[r["inferred"]["title_family"] or "(no SEIS title family)"] = fam.get(r["inferred"]["title_family"] or "(no SEIS title family)", 0) + 1
        sen[r["inferred"]["seniority"] or "(not stated in title)"] = sen.get(r["inferred"]["seniority"] or "(not stated in title)", 0) + 1
    sp = JOBS / date / "summary.json"
    summ = json.loads(sp.read_text())
    summ["by_title_family"] = dict(sorted(fam.items(), key=lambda x: -x[1]))
    summ["by_seniority"] = dict(sorted(sen.items(), key=lambda x: -x[1]))
    sp.write_text(json.dumps(summ, indent=1) + "\n")
    print(len(opened), "open postings re-inferred")


if __name__ == "__main__":
    main(sys.argv[1])

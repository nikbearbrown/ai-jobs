"""data/companies/src/*.txt -> data/companies/companies.csv

One row per distinct company. Dedupe is on a normalised name (lower case, letters and digits only),
first file/segment that names a company keeps it; later mentions only add slug hints.
Products that are not employers are listed in EXCLUDE and dropped.
"""
import csv
import io
import re
import sys

from .paths import COMPANIES, COMPANIES_SRC

# Names that are products, projects or places rather than employers. Dropped, with the reason recorded here.
EXCLUDE = {
    "pivotal", "slack", "bitbucket", "firebase", "looker", "tableau", "power bi", "wave", "quickbooks",
    "scale nucleus", "overture maps", "milvus", "haystack", "workday student", "salesforce education",
    "salesforce commerce", "magento", "pi", "make", "continue", "wave", "ria", "jupyter", "wikimedia",
    "opencrowd", "lensa", "zillow offers", "hubspot developer", "twilio sendgrid", "zoom video",
    "wordpress automattic", "linkedin learning", "adobe sign", "dropbox sign", "workiva dummy",
    "cloudflare boston", "gitlab boston", "samsara boston", "toast boston", "digital ocean cambridge",
}


def norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s


def candidates(name, hints):
    """Slug guesses for the ATS probe. Ordered: hints first, then the name's natural forms."""
    base = re.sub(r"\b(inc|llc|ltd|corp|corporation|company|co|plc|group|holdings|technologies|labs)\b\.?", "", name, flags=re.I)
    forms = []
    for n in (name, base):
        n = n.strip()
        low = n.lower()
        forms += [
            re.sub(r"[^a-z0-9]", "", low),
            re.sub(r"[^a-z0-9]+", "-", low).strip("-"),
            re.sub(r"[^a-z0-9]+", "_", low).strip("_"),
        ]
    out, seen = [], set()
    for c in list(hints) + forms:
        if c and c not in seen and len(c) >= 2:
            seen.add(c)
            out.append(c)
    return out


FIELDS = ["company_id", "name", "sector", "segment", "hints", "slug_candidates", "source_file"]


def build(sources):
    """[(file name, text)] in the order they are read -> one row per distinct company (pure: no file is read or written)."""
    rows, index = [], {}
    for fname, text in sources:
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            seg, _, names = line.partition("|")
            seg = seg.strip()
            sector = seg.split("/")[0]
            for item in names.split(";"):
                item = item.strip()
                if not item:
                    continue
                name, _, hint = item.partition("=")
                name = name.strip()
                hints = [h.strip() for h in hint.split(",") if h.strip()]
                key = norm(name)
                if not key or name.lower() in EXCLUDE:
                    continue
                if key in index:
                    row = rows[index[key]]
                    for h in hints:
                        if h not in row["hints"]:
                            row["hints"].append(h)
                    continue
                index[key] = len(rows)
                rows.append({"company_id": slugify(name), "name": name, "sector": sector, "segment": seg,
                             "hints": hints, "source_file": fname})
    ids = {}
    for r in rows:  # make ids unique
        base, n = r["company_id"], 2
        while r["company_id"] in ids:
            r["company_id"] = f"{base}-{n}"
            n += 1
        ids[r["company_id"]] = True
        r["slug_candidates"] = "|".join(candidates(r["name"], r["hints"]))
        r["hints"] = "|".join(r["hints"])
    return rows


def to_csv(rows):
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def read_sources():
    return [(p.name, p.read_text()) for p in sorted(COMPANIES_SRC.glob("*.txt"))]


def main():
    rows = build(read_sources())
    with COMPANIES.open("w", newline="") as f:
        f.write(to_csv(rows))
    by = {}
    for r in rows:
        by[r["sector"]] = by.get(r["sector"], 0) + 1
    print(len(rows), "companies", by)


if __name__ == "__main__":
    sys.exit(main())

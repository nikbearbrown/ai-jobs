"""The six public job-board APIs, each reduced to the canonical record (schema/job.schema.json).

Every normaliser follows one rule: a field the board did not state is None, never guessed.
Descriptions are hashed, not stored (they are copies of the companies' ads).
"""
import hashlib
import re
from urllib.parse import quote

from .http import get_json


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None


def _str(v):
    return None if v in (None, "") else str(v)


_WORKPLACE = {"on-site": "onsite", "onsite": "onsite", "on site": "onsite", "in office": "onsite", "in-office": "onsite",
              "hybrid": "hybrid", "remote": "remote", "fully remote": "remote", "remote-first": "remote"}


def _workplace(v):
    return _WORKPLACE.get(str(v or "").strip().lower())


_EMPLOYMENT = {"fulltime": "full_time", "full-time": "full_time", "full time": "full_time", "permanent": "full_time",
               "parttime": "part_time", "part-time": "part_time", "contract": "contract", "contractor": "contract",
               "intern": "intern", "internship": "intern", "temporary": "temporary", "temp": "temporary"}


def _employment(v):
    if not v:
        return None
    k = str(v).strip().lower()
    if k in _EMPLOYMENT:
        return _EMPLOYMENT[k]
    for needle, val in (("intern", "intern"), ("part", "part_time"), ("full", "full_time"), ("contract", "contract"),
                        ("freelance", "contract"), ("temp", "temporary"), ("perm", "full_time")):
        if needle in k:
            return val
    return "other"


def _iso(v):
    """Recruitee writes '2026-10-15 09:31:36 UTC'; make it ISO 8601. Anything else passes through unchanged."""
    m = re.match(r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}) UTC$", v or "")
    return f"{m.group(1)}T{m.group(2)}Z" if m else v


def _iso_from_ms(ms):
    if not ms:
        return None
    import datetime
    return datetime.datetime.fromtimestamp(int(ms) / 1000, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---- Greenhouse ---------------------------------------------------------------------------
def gh_url(slug, content=False):
    """content=True adds departments, offices and the ad text (heavy). The probe does not ask for it; the collector does."""
    return f"https://boards-api.greenhouse.io/v1/boards/{quote(slug)}/jobs" + ("?content=true" if content else "")


def gh_count(d):
    return len(d.get("jobs", [])) if isinstance(d, dict) else 0


def gh_norm(d, slug, src):
    for j in d.get("jobs", []):
        wp = None
        for m in j.get("metadata") or []:
            if isinstance(m, dict) and re.search(r"location type|workplace|work type|remote", str(m.get("name", "")), re.I):
                wp = _workplace(m.get("value") if not isinstance(m.get("value"), list) else (m["value"] or [None])[0])
        loc = (j.get("location") or {}).get("name")
        depts = [x.get("name") for x in j.get("departments") or [] if isinstance(x, dict)]
        yield {
            "source_id": str(j["id"]), "title": j.get("title") or "", "url": j.get("absolute_url") or "",
            "apply_url": None, "locations": [s.strip() for s in re.split(r"\s*\|\s*|;\s*", loc) if s.strip()] if loc else [],
            "country_codes": [], "workplace": wp, "department": depts[0] if depts else None, "team": None,
            "employment_type": None, "posted_at": j.get("first_published"), "updated_at": j.get("updated_at"),
            "compensation": None, "description_sha256": _sha(j.get("content")),
        }


# ---- Lever --------------------------------------------------------------------------------
def lv_url(slug):
    return f"https://api.lever.co/v0/postings/{quote(slug)}?mode=json"


def lv_count(d):
    return len(d) if isinstance(d, list) else 0


def lv_norm(d, slug, src):
    for j in d:
        c = j.get("categories") or {}
        sal = j.get("salaryRange") or None
        comp = None
        if isinstance(sal, dict) and (sal.get("min") or sal.get("max")):
            comp = {"min": sal.get("min"), "max": sal.get("max"), "currency": sal.get("currency"),
                    "interval": {"per-year-salary": "year", "per-hour-wage": "hour", "per-month-salary": "month"}.get(sal.get("interval")),
                    "raw": None}
        locs = c.get("allLocations") or ([c["location"]] if c.get("location") else [])
        yield {
            "source_id": str(j["id"]), "title": j.get("text") or "", "url": j.get("hostedUrl") or "",
            "apply_url": j.get("applyUrl"), "locations": list(locs), "country_codes": [j["country"]] if j.get("country") else [],
            "workplace": _workplace(j.get("workplaceType")), "department": _str(c.get("department")), "team": _str(c.get("team")),
            "employment_type": _employment(c.get("commitment")), "posted_at": _iso_from_ms(j.get("createdAt")), "updated_at": None,
            "compensation": comp, "description_sha256": _sha(j.get("descriptionPlain")),
        }


# ---- Ashby --------------------------------------------------------------------------------
def ab_url(slug):
    return f"https://api.ashbyhq.com/posting-api/job-board/{quote(slug)}?includeCompensation=true"


def ab_count(d):
    return len(d.get("jobs", [])) if isinstance(d, dict) else 0


def ab_norm(d, slug, src):
    for j in d.get("jobs", []):
        if j.get("isListed") is False:
            continue
        locs = [j["location"]] if j.get("location") else []
        for s in j.get("secondaryLocations") or []:
            n = s.get("location") if isinstance(s, dict) else s
            if n:
                locs.append(n)
        wp = _workplace(j.get("workplaceType"))
        if wp is None and j.get("isRemote") is True:
            wp = "remote"
        comp = None
        c = j.get("compensation") or {}
        for comp_part in c.get("summaryComponents") or []:
            if isinstance(comp_part, dict) and comp_part.get("compensationType") == "Salary":
                comp = {"min": comp_part.get("minValue"), "max": comp_part.get("maxValue"), "currency": comp_part.get("currencyCode"),
                        "interval": {"1 YEAR": "year", "1 HOUR": "hour", "1 MONTH": "month"}.get(str(comp_part.get("interval", "")).upper()),
                        "raw": c.get("compensationTierSummary")}
                break
        yield {
            "source_id": str(j["id"]), "title": j.get("title") or "", "url": j.get("jobUrl") or "",
            "apply_url": j.get("applyUrl"), "locations": locs, "country_codes": [],
            "workplace": wp, "department": _str(j.get("department")), "team": _str(j.get("team")),
            "employment_type": _employment(j.get("employmentType")), "posted_at": j.get("publishedAt"), "updated_at": None,
            "compensation": comp, "description_sha256": _sha(j.get("descriptionPlain")),
        }


# ---- SmartRecruiters ----------------------------------------------------------------------
SR_PAGE = 100


def sr_url(slug, offset=0, limit=SR_PAGE):
    return f"https://api.smartrecruiters.com/v1/companies/{quote(slug)}/postings?limit={limit}&offset={offset}"


def sr_count(d):
    return int(d.get("totalFound", 0)) if isinstance(d, dict) else 0


def sr_norm(d, slug, src):
    for j in d.get("content", []):
        loc = j.get("location") or {}
        wp = "remote" if loc.get("remote") else ("hybrid" if loc.get("hybrid") else None)
        full = loc.get("fullLocation")
        yield {
            "source_id": str(j["id"]), "title": j.get("name") or "",
            "url": f"https://jobs.smartrecruiters.com/{quote(slug)}/{j['id']}", "apply_url": None,
            "locations": [full] if full else [], "country_codes": [loc["country"].upper()] if loc.get("country") else [],
            "workplace": wp, "department": _str((j.get("department") or {}).get("label")),
            "team": None, "employment_type": _employment((j.get("typeOfEmployment") or {}).get("label")),
            "posted_at": j.get("releasedDate"), "updated_at": None, "compensation": None, "description_sha256": None,
        }


# ---- Workable -----------------------------------------------------------------------------
def wk_url(slug):
    return f"https://apply.workable.com/api/v1/widget/accounts/{quote(slug)}"


def wk_count(d):
    return len(d.get("jobs", [])) if isinstance(d, dict) else 0


def wk_norm(d, slug, src):
    for j in d.get("jobs", []):
        locs, ccs = [], []
        for l in j.get("locations") or []:
            if l.get("hidden"):
                continue
            locs.append(", ".join(x for x in (l.get("city"), l.get("region"), l.get("country")) if x))
            if l.get("countryCode"):
                ccs.append(l["countryCode"])
        yield {
            "source_id": str(j.get("shortcode")), "title": j.get("title") or "", "url": j.get("url") or j.get("shortlink") or "",
            "apply_url": j.get("application_url"), "locations": locs, "country_codes": ccs,
            "workplace": "remote" if j.get("telecommuting") else None, "department": _str(j.get("department")), "team": None,
            "employment_type": _employment(j.get("employment_type")), "posted_at": j.get("published_on") or j.get("created_at"),
            "updated_at": None, "compensation": None, "description_sha256": _sha(j.get("description")),
        }


# ---- Recruitee ----------------------------------------------------------------------------
def rc_url(slug):
    return f"https://{quote(slug)}.recruitee.com/api/offers/"


def rc_count(d):
    return len(d.get("offers", [])) if isinstance(d, dict) else 0


def rc_norm(d, slug, src):
    for j in d.get("offers", []):
        if j.get("status") not in (None, "published"):
            continue
        wp = "remote" if j.get("remote") else ("hybrid" if j.get("hybrid") else ("onsite" if j.get("on_site") else None))
        locs = [j["location"]] if j.get("location") else []
        yield {
            "source_id": str(j.get("id")), "title": j.get("title") or "", "url": j.get("careers_url") or "",
            "apply_url": j.get("careers_apply_url"), "locations": locs,
            "country_codes": [j["country_code"].upper()] if j.get("country_code") else [],
            "workplace": wp, "department": _str(j.get("department")), "team": None,
            "employment_type": _employment(j.get("employment_type_code")), "posted_at": _iso(j.get("published_at") or j.get("created_at")),
            "updated_at": None, "compensation": None, "description_sha256": _sha(j.get("description")),
        }


PROVIDERS = {
    "greenhouse": (gh_url, gh_count, gh_norm),
    "lever": (lv_url, lv_count, lv_norm),
    "ashby": (ab_url, ab_count, ab_norm),
    "smartrecruiters": (sr_url, sr_count, sr_norm),
    "workable": (wk_url, wk_count, wk_norm),
    "recruitee": (rc_url, rc_count, rc_norm),
}


def probe(provider, slug):
    """(status, count). count > 0 means the board exists and lists postings; 0 with status 200 means an empty or unknown board."""
    url_fn, count_fn, _ = PROVIDERS[provider]
    status, data = get_json(url_fn(slug) if provider != "smartrecruiters" else sr_url(slug, 0, 1))
    return status, (count_fn(data) if data is not None else 0)


def fetch_board(provider, slug):
    """Read a whole board. Returns (ok, raw_records, source_url). A failure returns ok=False and never an empty-looking success."""
    url_fn, count_fn, _ = PROVIDERS[provider]
    if provider == "smartrecruiters":
        pages, offset, total = [], 0, None
        while total is None or offset < total:
            status, data = get_json(sr_url(slug, offset))
            if status != 200 or data is None:
                return False, None, sr_url(slug)
            total = sr_count(data)
            pages.append(data)
            if not data.get("content"):
                break
            offset += len(data["content"])
        merged = {"content": [x for p in pages for x in p.get("content", [])], "totalFound": total}
        return True, merged, sr_url(slug)
    url = gh_url(slug, content=True) if provider == "greenhouse" else url_fn(slug)
    status, data = get_json(url, timeout=60)
    if status != 200 or data is None:
        return False, None, url
    return True, data, url


def normalise(provider, data, slug, src):
    return PROVIDERS[provider][2](data, slug, src)

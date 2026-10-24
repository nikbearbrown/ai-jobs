"""No network. Run: python3 -m unittest discover -s tests -v   (jsonschema optional but used when installed)"""
import json
import unittest

from aijobs import collect, infer, providers as P
from aijobs.build_titles import parse, entry_variants
from aijobs.paths import SCHEMA

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

SCHEMA_DOC = json.loads(SCHEMA.read_text())


def canonical(provider, raw, slug="acme"):
    out = []
    for r in P.normalise(provider, raw, slug, "http://example/test"):
        rec = {"schema_version": 1, "id": f"{provider}:{slug}:{r['source_id']}", "provider": provider, "board": slug,
               "company": "Acme", "company_id": "acme", **r,
               "inferred": {"seniority": infer.seniority(r["title"]), "seniority_rule": infer.SENIORITY_RULE,
                            "title_family": infer.title_family(r["title"]), "title_rule": infer.TITLE_RULE},
               "first_seen": "2026-10-24", "last_seen": "2026-10-24", "status": "open",
               "provenance": {"collected_at": "2026-10-24T00:00:00Z", "source_url": "http://example/test", "collector": "test"}}
        out.append(rec)
    return out


FIXTURES = {
    "greenhouse": {"jobs": [{"id": 1, "title": "Data Engineer", "absolute_url": "https://x/1", "location": {"name": "Boston, MA | Remote"},
                             "first_published": "2026-10-01T00:00:00-04:00", "updated_at": "2026-10-02T00:00:00-04:00",
                             "metadata": [{"name": "Location Type", "value": "Hybrid"}], "departments": [{"name": "Data"}]}]},
    "lever": [{"id": "abc", "text": "Software Engineer I", "hostedUrl": "https://x/abc", "applyUrl": "https://x/abc/apply",
               "categories": {"team": "Platform", "department": "Eng", "location": "NYC", "commitment": "Full-time", "allLocations": ["NYC", "Remote"]},
               "createdAt": 1790000000000, "workplaceType": "remote", "descriptionPlain": "hi"}],
    "ashby": {"jobs": [{"id": "u1", "title": "ML Engineer", "jobUrl": "https://x/u1", "applyUrl": "https://x/u1/apply", "location": "SF",
                        "secondaryLocations": [{"location": "NYC"}], "isListed": True, "isRemote": True, "employmentType": "FullTime",
                        "publishedAt": "2026-10-01T00:00:00+00:00", "department": "Eng", "team": "ML"},
                       {"id": "u2", "title": "Hidden", "jobUrl": "https://x/u2", "isListed": False}]},
    "smartrecruiters": {"content": [{"id": "9", "name": "Data Analyst", "releasedDate": "2026-10-01T00:00:00Z",
                                     "location": {"fullLocation": "Austin, TX, United States", "country": "us", "remote": False, "hybrid": True},
                                     "department": {"label": "Data"}, "typeOfEmployment": {"label": "Full-time"}}], "totalFound": 1},
    "workable": {"jobs": [{"shortcode": "AB12", "title": "AI Engineer", "url": "https://x/AB12", "telecommuting": True, "published_on": "2026-10-01",
                           "employment_type": "Full-time", "locations": [{"city": "Paris", "region": "IdF", "country": "France", "countryCode": "FR", "hidden": False}]}]},
    "recruitee": {"offers": [{"id": 5, "title": "Research Engineer", "careers_url": "https://x/5", "city": "Amsterdam", "country_code": "nl",
                              "status": "published", "published_at": "2026-10-15 09:31:36 UTC", "employment_type_code": "fulltime_permanent", "hybrid": True}]},
}


class Providers(unittest.TestCase):
    def test_every_provider_normalises_to_the_schema(self):
        for prov, raw in FIXTURES.items():
            recs = canonical(prov, raw)
            self.assertGreaterEqual(len(recs), 1, prov)
            for r in recs:
                if jsonschema:
                    jsonschema.validate(r, SCHEMA_DOC)

    def test_unstated_fields_are_null_not_guessed(self):
        r = canonical("greenhouse", {"jobs": [{"id": 2, "title": "X", "absolute_url": "https://x/2"}]})[0]
        self.assertIsNone(r["workplace"])
        self.assertIsNone(r["employment_type"])
        self.assertIsNone(r["department"])

    def test_greenhouse_updated_at_is_not_posted_at(self):
        r = canonical("greenhouse", FIXTURES["greenhouse"])[0]
        self.assertEqual(r["posted_at"], "2026-10-01T00:00:00-04:00")
        self.assertEqual(r["updated_at"], "2026-10-02T00:00:00-04:00")
        self.assertEqual(r["workplace"], "hybrid")
        self.assertEqual(r["locations"], ["Boston, MA", "Remote"])

    def test_ashby_unlisted_is_skipped_and_remote_flag_used(self):
        recs = canonical("ashby", FIXTURES["ashby"])
        self.assertEqual([r["source_id"] for r in recs], ["u1"])
        self.assertEqual(recs[0]["workplace"], "remote")
        self.assertEqual(recs[0]["locations"], ["SF", "NYC"])

    def test_recruitee_date_and_employment(self):
        r = canonical("recruitee", FIXTURES["recruitee"])[0]
        self.assertEqual(r["posted_at"], "2026-10-15T09:31:36Z")
        self.assertEqual(r["employment_type"], "full_time")
        self.assertEqual(r["country_codes"], ["NL"])


class Infer(unittest.TestCase):
    def test_seniority(self):
        cases = {"Data Analyst Intern": "intern", "Associate Solutions Architect": "entry", "Software Engineer I": "entry",
                 "Senior Software Engineer": "senior", "Principal Engineer": "staff", "Director of Engineering": "director",
                 "Product Manager, AI": None, "Engineering Manager, Platform": "manager", "Machine Learning Engineer II": "mid",
                 "Account Executive": None}
        for t, want in cases.items():
            self.assertEqual(infer.seniority(t), want, t)

    def test_title_family_longest_match(self):
        self.assertEqual(infer.title_family("Senior Software Engineer, Infrastructure"), "software-engineering")
        self.assertEqual(infer.title_family("Forward Deployed Engineer (New Grad)"), "ai-engineering")
        self.assertIsNone(infer.title_family("Account Executive, AI Native"))


class Titles(unittest.TestCase):
    def test_parse_and_variants(self):
        fams = parse("## k | Label | c01 | y\nA B; C D\n# comment\nE F\n")
        self.assertEqual(fams[0]["titles"], ["A B", "C D", "E F"])
        self.assertIn("Junior A B", entry_variants("A B"))
        self.assertEqual(entry_variants("Senior A B"), [])


class Delta(unittest.TestCase):
    def rec(self, i, board="b1", status="open", first="2026-10-01"):
        return {"id": i, "provider": "greenhouse", "board": board, "status": status, "first_seen": first, "last_seen": first}

    def test_failed_board_never_closes_postings(self):
        prev = {"greenhouse:b1:1": self.rec("greenhouse:b1:1")}
        board = ("c", "C", "greenhouse", "b1", "board-name-match")
        rows, new, gone, _ = collect.merge_state(prev, [(board, False, [], "u")], "2026-10-24")
        self.assertEqual([r["status"] for r in rows], ["open"])
        self.assertEqual(gone, [])

    def test_successful_board_closes_missing_and_flags_new(self):
        prev = {"greenhouse:b1:1": self.rec("greenhouse:b1:1")}
        board = ("c", "C", "greenhouse", "b1", "board-name-match")
        fresh = [{**self.rec("greenhouse:b1:2"), "first_seen": "2026-10-24", "last_seen": "2026-10-24"}]
        rows, new, gone, _ = collect.merge_state(prev, [(board, True, fresh, "u")], "2026-10-24")
        self.assertEqual(new, ["greenhouse:b1:2"])
        self.assertEqual(gone, ["greenhouse:b1:1"])
        self.assertEqual({r["id"]: r["status"] for r in rows}, {"greenhouse:b1:1": "gone", "greenhouse:b1:2": "open"})

    def test_first_seen_survives(self):
        prev = {"greenhouse:b1:1": self.rec("greenhouse:b1:1", first="2026-09-01")}
        board = ("c", "C", "greenhouse", "b1", "x")
        again = [{**self.rec("greenhouse:b1:1"), "first_seen": "2026-10-24", "last_seen": "2026-10-24"}]
        rows, new, gone, _ = collect.merge_state(prev, [(board, True, again, "u")], "2026-10-24")
        self.assertEqual(rows[0]["first_seen"], "2026-09-01")
        self.assertEqual(new, [])


if __name__ == "__main__":
    unittest.main()

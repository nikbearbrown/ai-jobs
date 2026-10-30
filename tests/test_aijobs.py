"""No network. Run: python3 -m unittest discover -s tests -v   (jsonschema optional but used when installed)"""
import json
import unittest

from aijobs import collect, infer, notify, providers as P
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


SUMMARY = {"date": "2026-10-25", "boards_requested": 715, "boards_read_ok": 713, "boards_failed": [{"company": "X"}, {"company": "Y"}],
           "postings_open": 84600, "new_this_run": 412, "gone_this_run": 94, "first_run": False,
           "new_by_title_family": {"software-engineering": 70, "(no SEIS title family)": 240, "cloud-devops-sre": 31, "leadership": 9,
                                   "ai-engineering": 22, "analytics": 15, "security": 12, "ml-engineering": 8, "data-science": 5,
                                   "design-ux": 4, "research": 3, "robotics-cps": 2},
           "new_by_seniority": {"senior": 120, "entry": 14, "intern": 9}}


class Discord(unittest.TestCase):
    def test_daily_message_has_counts_and_no_postings(self):
        e = notify.build_ok(SUMMARY, {"software-engineering": "General software engineering"})
        text = e["title"] + e["description"] + e["footer"]
        self.assertIn("412 new", text)
        self.assertIn("General software engineering: 70", e["description"])
        self.assertIn("23 of the new postings", e["description"])         # 14 entry + 9 intern
        self.assertIn("of 412", e["description"])
        self.assertNotIn("leadership", e["description"])                    # not a SEIS-fit family
        self.assertIn("2 board(s) could not be read", e["description"])
        self.assertIn("more families", e["description"])                    # 10 families, top 8 shown
        notify.check_safe(text)

    def test_first_run_has_no_daily_figure(self):
        e = notify.build_ok({**SUMMARY, "first_run": True})
        self.assertIn("no daily figure", e["description"])
        self.assertNotIn("412 new", e["title"] + e["description"])

    def test_notices(self):
        self.assertIn("stopped itself", notify.build_notice("2026-10-25", "halted")["description"])
        self.assertIn("(step: collect)", notify.build_notice("2026-10-25", "failed", "collect")["description"])
        self.assertIn("test", notify.build_notice("2026-10-25", "test")["title"])

    def test_unsafe_text_is_refused(self):
        for bad in ("see /Users/bear/x", "mail bear@bearbrown.co", "https://discord.com/api/webhooks/1/abc", "at /home/jobs/STOP"):
            with self.assertRaises(notify.Unsafe):
                notify.to_payload({"title": "t", "description": bad, "footer": "f"})

    def test_payload_is_plain_text_so_it_shows_with_embeds_switched_off(self):
        p = notify.to_payload({"title": "T", "description": "body", "footer": "small", "url": "https://example.com/x"})
        self.assertNotIn("embeds", p)
        self.assertEqual(p["content"], "**T**\nbody\nhttps://example.com/x\n-# small")
        self.assertEqual(p["flags"], 4)                                   # SUPPRESS_EMBEDS: no link-preview card
        self.assertLessEqual(len(notify.to_payload({"title": "T", "description": "x" * 5000, "footer": "f"})["content"]), 2000)

    def test_payload_never_pings(self):
        p = notify.to_payload(notify.build_notice("2026-10-25", "failed"))
        self.assertEqual(p["allowed_mentions"], {"parse": []})

    def test_no_webhook_file_is_a_noop_and_loose_permissions_are_refused(self):
        import os, tempfile
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "hook")
            os.environ["AIJOBS_DISCORD_WEBHOOK_FILE"] = f
            self.assertIsNone(notify.read_webhook()[0])                         # missing file
            with open(f, "w") as fh:
                fh.write("https://discord.com/api/webhooks/1/abc\n")
            os.chmod(f, 0o644)
            url, why = notify.read_webhook()
            self.assertIsNone(url); self.assertIn("readable by group", why)
            os.chmod(f, 0o600)
            self.assertEqual(notify.read_webhook()[0], "https://discord.com/api/webhooks/1/abc")
            with open(f, "w") as fh:
                fh.write("https://example.com/not-discord\n")
            self.assertIsNone(notify.read_webhook()[0])
            del os.environ["AIJOBS_DISCORD_WEBHOOK_FILE"]


if __name__ == "__main__":
    unittest.main()

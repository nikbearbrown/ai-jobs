"""No network. A category added to the sources must reach the output without hand steps. Run: python3 -m unittest discover -s tests -v"""
import json
import os
import tempfile
import unittest
from pathlib import Path

from aijobs import build_titles, infer, notify, sync
from aijobs.paths import COURSES, TITLES_SRC

COURSE_IDS = {c["id"] for c in json.loads(COURSES.read_text())["courses"]}
NEW_FAMILY = "## game-engine-roles | Game engine roles | c07 | y\nUnity Gameplay Engineer; Unreal Gameplay Engineer\n"


def write(path, text):
    Path(path).write_text(text)
    return Path(path)


class GeneratedFilesAreCurrent(unittest.TestCase):
    def test_titles_json_and_companies_csv_match_their_sources(self):
        # Fails on the Mac when someone edits titles.src.txt or companies/src/*.txt and forgets to rebuild:
        # run python3 -m aijobs.sync, then commit the two generated files with the sources.
        self.assertEqual(sync.stale(), [])


class NewCategory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.titles = Path(self.tmp.name) / "titles.json"
        self.orig = infer.TITLES

    def tearDown(self):
        infer.TITLES = self.orig
        infer._title_index.cache_clear()

    def load(self, extra):
        doc = build_titles.build(TITLES_SRC.read_text() + "\n" + extra, COURSE_IDS)
        write(self.titles, build_titles.render(doc))
        infer.TITLES = self.titles
        infer._title_index.cache_clear()
        return doc

    def test_a_new_family_wins_its_longer_title_and_is_counted_even_at_zero(self):
        title = "Senior Unreal Gameplay Engineer"
        self.load("")
        self.assertEqual(infer.title_family(title), "gamedev-graphics")          # today: the shorter "Gameplay Engineer" claims it
        self.load(NEW_FAMILY)
        self.assertEqual(infer.title_family(title), "game-engine-roles")         # after: the longer title in the new family
        block = sync.categories_block({"gamedev-graphics": 5}, "probe-x.jsonl", titles=self.titles,
                                      companies=write(Path(self.tmp.name) / "c.csv", "company_id,name\nacme,Acme\n"))
        self.assertEqual(block["loaded"]["game-engine-roles"], 0)               # zero is shown, not omitted
        self.assertEqual(block["loaded"]["gamedev-graphics"], 5)
        self.assertEqual(block["families"], 28)

    def test_added_since_last_run(self):
        self.load(NEW_FAMILY)
        c = write(Path(self.tmp.name) / "c.csv", "company_id,name\nacme,Acme\n")
        yesterday = {"categories": {"loaded": {"gamedev-graphics": 5}}}
        added = sync.categories_block({}, "p", previous=yesterday, titles=self.titles, companies=c)["added_since_last_run"]
        self.assertIn("game-engine-roles", added)
        self.assertNotIn("gamedev-graphics", added)
        # a previous summary from before this block existed says nothing, so nothing is claimed
        self.assertIsNone(sync.categories_block({}, "p", previous={"date": "2026-10-28"}, titles=self.titles, companies=c)["added_since_last_run"])

    def test_broken_source_is_an_error_not_a_silent_skip(self):
        with self.assertRaises(ValueError):
            build_titles.build("## k | L | c99 | y\nA B\n", COURSE_IDS)


class NewCompanies(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)
        self.companies = write(self.d / "companies.csv", "company_id,name\nacme,Acme\nbolt,Bolt\nnew-studio,New Studio\n")
        self.probe = write(self.d / "probe-2026-10-28.jsonl",
                           json.dumps({"company_id": "acme", "name": "Acme", "confirmed": None}) + "\n"
                           + json.dumps({"company_id": "bolt", "name": "Bolt", "confirmed": None}) + "\n"
                           + json.dumps({"company_id": "gone-co", "name": "Gone Co", "confirmed": None}) + "\n")

    def test_only_the_company_no_probe_has_seen_is_missing(self):
        self.assertEqual([r["company_id"] for r in sync.missing_from_probe(self.probe, self.companies)], ["new-studio"])

    def test_seed_keeps_listed_companies_and_drops_removed_ones(self):
        out = self.d / "probe-2026-10-29-new.jsonl"
        self.assertEqual(sync.seed_probe(self.probe, out, self.companies), 2)
        ids = [json.loads(l)["company_id"] for l in out.read_text().splitlines()]
        self.assertEqual(ids, ["acme", "bolt"])                                  # gone-co dropped; new-studio is left for the probe to add

    def test_newest_completed_probe_ignores_unfinished_and_prefers_new_on_the_same_day(self):
        for name, done in [("probe-2026-10-28", True), ("probe-2026-11-04", True), ("probe-2026-11-04-new", True), ("probe-2026-11-05-new", False)]:
            write(self.d / f"{name}.jsonl", "")
            if done:
                write(self.d / f"{name}.done", "x\n")
        self.assertEqual(sync.newest_completed_probe(self.d).name, "probe-2026-11-04-new.jsonl")

    def test_unfinished_probe_blocks_a_second_one_only_while_recent(self):
        write(self.d / "probe-2026-11-04.jsonl", "")
        now = (self.d / "probe-2026-11-04.jsonl").stat().st_mtime
        self.assertIsNotNone(sync.probe_in_progress(self.d, now=now + 60))
        self.assertIsNone(sync.probe_in_progress(self.d, now=now + sync.IN_PROGRESS_SECONDS + 60))


class DiscordLine(unittest.TestCase):
    SUMMARY = {"date": "2026-10-29", "boards_requested": 715, "boards_read_ok": 715, "boards_failed": [], "postings_open": 85000,
               "new_this_run": 100, "gone_this_run": 90, "first_run": False, "new_by_title_family": {"gamedev-graphics": 4},
               "new_by_seniority": {"entry": 2}}

    def test_names_the_new_category_and_stays_safe(self):
        s = {**self.SUMMARY, "categories": {"added_since_last_run": ["game-engine-roles"]}}
        e = notify.build_ok(s, {"game-engine-roles": "Game engine roles"})
        self.assertIn("New categories loaded today: Game engine roles", e["description"])
        notify.check_safe(e["title"] + e["description"] + e["footer"])

    def test_silent_when_nothing_is_new_or_unknown(self):
        for cat in ({"added_since_last_run": []}, {"added_since_last_run": None}, None):
            s = {**self.SUMMARY, **({"categories": cat} if cat is not None else {})}
            self.assertNotIn("New categories", notify.build_ok(s, {})["description"])


if __name__ == "__main__":
    unittest.main()

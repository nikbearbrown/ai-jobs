# Adding a job category (game jobs, designer jobs, and so on)

## Executive summary

**What this is.** The three steps that make a new category show up in the daily output from the Hetzner box, and what each one changes.
**What a category is here.** A *title family* in `data/titles/titles.src.txt` (a label that the collector stamps on a posting whose title matches one of the family's titles), plus the *companies* in `data/companies/src/*.txt` whose boards the collector reads. The collector reads **every** posting on every confirmed board; a family only labels them. So a family with no employers on the list finds nothing, and an employer with no family is read but not counted under that category.
**What the box does by itself.** Every morning `ops/run-daily.sh` pulls `main`, runs `python3 -m aijobs.sync` (rebuilds `titles.json` and `companies.csv` from the sources, then probes only companies no probe has seen), collects, and commits `summary.json`. Nothing on the box needs to be edited when a category is added; the push to `main` is the signal.
**What still needs a person.** Writing the titles and companies (judgment), and pushing to `main` (the box runs whatever is on `main`, see `docs/collector-plan.md`). The titles are hypotheses, not verified openings.

## The three steps

1. **Edit the sources.**
   * A new family: add a block to `data/titles/titles.src.txt`: `## key | label | course ids | y` then titles separated by `;`. The course ids must exist in `data/courses.json` (the build stops with an error otherwise).
   * New employers: add names to a file in `data/companies/src/` (`Name=slug1,slug2` adds slug guesses).
   * Order matters: the first family that claims a title keeps it (case-insensitive), and a posting takes the family of the **longest** matching title inside its own title, so a specific title in a new family beats a shorter one in an old family.
   * Keep titles specific. A one-word title such as `Producer` or `Educator` matches anywhere inside a posting title (offline replay of the 2026-10-24 postings with a 202-title game list: 119 of its 160 matches came from the titles `producer`, `educator`, `development director` and `founder`, for example a pharma "National Manager, Oncology Nurse Educator" and a "Startup Founder").
2. **Rebuild and test on the Mac.**
   ```bash
   python3 -m aijobs.sync --no-probe     # rewrites titles.json and companies.csv from the sources
   python3 -m unittest discover -s tests # fails if a generated file does not match its source
   ```
   Commit the sources **and** the two generated files together.
3. **Push to `main`.** The next 04:30 UTC run (up to 10 minutes late) picks it up. To run it sooner, with Bear's say-so: `ssh hetz 'sudo systemctl start --no-block ai-jobs-daily.service'`.

## What you should see the next morning

* `data/jobs/DATE/summary.json` has a `categories` block: `loaded` lists **every** family with its open-posting count (a family with no postings shows `0` instead of being absent), `families`, `titles` and `companies` counts, a short hash of each generated list, the probe file used, and `added_since_last_run` (the families that were not in the previous summary; `null` when the previous summary predates this block).
* `by_title_family` and `seis-fit.md` show the family once it has at least one posting.
* The daily Discord status post gains one line: `New categories loaded today: <label>`.
* A new company is probed the same morning into `data/probes/probe-DATE-new.jsonl` (the previous probe's rows plus the new ones) and committed with the summaries. If it has a readable board, its postings are in that day's run. If it is on a system not read yet (Workday, iCIMS, its own site), it simply has no board; that is the "none" count in `ats-coverage.md`, not an error.

## What breaks, and how it shows

| Symptom | Cause | Where it shows |
|---|---|---|
| Daily run fails at step `sync` | A source is broken (for example an unknown course id) | Discord failure notice; journal line `sync: the category sources are broken` |
| `STALE: titles.json does not match its source` | Sources edited, generated files not rebuilt | `python3 -m aijobs.sync --check`, and the test suite |
| New family shows `0` for days | No listed employer posts a matching title, or the employers are not on a readable board | `categories.loaded` in `summary.json` |
| New company has no board | Not on Greenhouse, Lever, Ashby, SmartRecruiters or Recruitee, or the slug guess missed | `none` row for it in the newest probe file; add `Name=slug` hints |

## Not covered

* Nothing watches another repository. The course repository's lists (for example the CSYE 7270 `jobs/role-titles.json`, or Lectern's `keywords.json`) are separate; a category is not copied from them. Copying is a person (or a session) editing the sources above.
* Existing postings are re-classified on every run while they stay open on their board; a posting already marked `gone` keeps the family it had.

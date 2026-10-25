# ai-jobs

## Executive summary

**What this is.** A collector that reads companies' public job boards and writes every posting in one shape, so a SEIS (Software Engineering & Information Systems, Northeastern) graduate can search jobs across thousands of employers instead of one careers page at a time. This repo is the first slice: the list of **job titles** a SEIS graduate gets hired into, the list of **companies** that might hire one, which of those companies have a board we can read, and a first collection from the boards that answered.

**Why.** Lectern (Professor Bear's job search) watches 18 boards for a different purpose. The seis.jobs site has only fictional sample postings. This repo is meant to be the real data behind seis.jobs, and the thing the Hetzner box can run daily.

**What was found (2026-10-24).**
* **1,609 job titles in 27 families** ([data/titles/titles.json](data/titles/titles.json)), each family tied to the SEIS courses that teach it ([data/courses.json](data/courses.json), the 22 courses on seisai.site). Entry-level forms (Junior, Associate, New Grad, I, Intern) of the titles that take them add 11,966 more search strings.
* **2,574 companies** ([data/companies/companies.csv](data/companies/companies.csv)) across 13 sectors, written from general knowledge. **719 (28%) have a confirmed readable board** on Greenhouse, Lever, Ashby, SmartRecruiters or Recruitee ([boards.csv](data/companies/boards.csv)); **1,818 (71%) have none on those systems**, because they use Workday, iCIMS, Taleo, SuccessFactors or their own site, which are not read yet. Sector coverage is in [ats-coverage.md](data/companies/ats-coverage.md).
* **First collection: 84,282 open postings from 715 distinct boards, every board read successfully** ([summary](data/jobs/2026-10-24/summary.json)). Without Domino's store postings (24,833), 41% of postings have a title in a SEIS family; **1,891 are marked entry-level or internship by title, 1,079 of them in the US** ([entry-level.csv](data/jobs/2026-10-24/entry-level.csv), [seis-fit.md](data/jobs/2026-10-24/seis-fit.md)).
* A company's mention in the 112 SEIS student stories is a pointer, not a hire count: Amazon (21), LinkedIn (20), Google (9), Microsoft (8), Nokia (7), OpenAI (6), Snowflake (6), MongoDB (6) ([seis-story-mentions.json](data/companies/seis-story-mentions.json)).

**What is NOT done or NOT true yet.**
* **It now runs on the Hetzner box, but has done so for one test run only.** Deployed 2026-10-24 under an unprivileged `jobs` user with a daily timer (04:30 UTC) and a weekly probe (Wednesdays 03:00 UTC). The first run read all 715 boards in 1 min 56 s, 19 s of CPU, 642 MB peak, and got the same 84,282 postings as my Mac run. The first *scheduled* run (2026-10-25) and the first real push of summaries from the box have not happened yet; the push permission was tested with a throwaway branch. Details and how to stop it: [docs/collector-plan.md](docs/collector-plan.md).
* **Workable was not read.** My first probe hit it too hard and it answered HTTP 429 with a `Retry-After` of about 23 hours. The code now honours that and throttles; Workable-hosted companies (Hugging Face and the like) are missing from the counts until it is re-run after the block lifts. Not worked around.
* **The big regulated employers are mostly absent** (banks, hospitals, consultancies, government): they sit on systems with no adapter yet. Workday is the first one to build. LinkedIn, Indeed and Glassdoor are deliberately not used (their terms forbid scraping).
* **The company list is from memory.** Some names may be defunct, acquired or renamed (not checked); they would show as "no board". Existence of a name is not evidence of hiring.
* **Seniority and title family are read from the title alone**, by crude rules (`seniority-v1`, `title-ngram-v1`). Most postings carry no level word, so "entry-level" undercounts what a new graduate could apply for. Visa sponsorship, degree requirements and years of experience need the ad text, which is not read yet.
* The title list was extended once from titles seen on real boards (unmatched "Fullstack Engineer", "Deployed Engineer", "Solution Engineer" and similar); it will keep growing.

## What is in the repo

| Path | What |
|---|---|
| `schema/job.schema.json` | the canonical posting; unstated fields are `null`, our conclusions are under `inferred` with the rule that made them |
| `docs/canonical-form.md` | how each ATS maps to it (field table) and what is not covered |
| `docs/collector-plan.md` | how it runs on the Hetzner box, and how to stop or undo it |
| `ops/` | `run-daily.sh`, `run-weekly-probe.sh` and the four systemd units installed on the box |
| `data/courses.json` | the 22 SEIS AI courses, copied from seisai.site/courses |
| `data/titles/titles.src.txt` -> `titles.json` | the title list; edit the `.src.txt` |
| `data/companies/src/*.txt` -> `companies.csv` | the company list by segment; `Name=slug1,slug2` adds slug guesses |
| `data/probes/probe-DATE.jsonl` | which ATS each company is on, with how the board was confirmed |
| `data/companies/boards.csv`, `ats-coverage.md` | confirmed boards and the coverage report |
| `data/jobs/DATE/` | `summary.json`, `boards.json`, `seis-fit.md`, `entry-level.csv` (tracked); `jobs.jsonl` and `current.jsonl` (all postings, gitignored) |
| `research/` | possible papers, one folder each with a `paper-draft.md`; see `research/README.md` |
| `aijobs/` | the code: Python standard library only, no keys |

## Run it

```bash
python3 -m unittest discover -s tests            # 11 tests, no network
python3 -m aijobs.build_titles                   # titles.src.txt -> titles.json
python3 -m aijobs.build_companies                # src/*.txt -> companies.csv
python3 -m aijobs.probe --workers 12             # find each company's board (about 30 minutes; resumable; throttled per host)
python3 -m aijobs.report data/probes/probe-DATE.jsonl
python3 -m aijobs.collect --probe data/probes/probe-DATE.jsonl     # read every confirmed board (about 3 minutes)
python3 -m aijobs.seisfit DATE                   # SEIS-fit report + entry-level.csv
python3 -m aijobs.story_mentions /path/to/books/seis
```

## Rules this repo keeps

1. **A slug match is not a company match.** A board counts as the company's only when it names itself or its ads mention the company. 37 boards were found and not confirmed (for example xAI's Greenhouse board belongs to "SpaceXSI"); they are listed for a person and not collected.
2. **A board that fails to load never closes its postings.** `gone` only when the board was read and no longer lists the id (tested in `tests/test_aijobs.py`).
3. **Ad text is hashed, not stored.** It is a copy of the company's ad.
4. **A 429 is not a 404.** An error is recorded as an error, never as "no such board".
5. Nothing here posts, sends or publishes.

## Feed architecture and licensing

The offline [static feed v1 contract](docs/static-feed-v1.md) provides a full-state
exporter/validator, immutable date/run bundles, source-health and freshness metadata,
synthetic fixtures, local atomic acceptance and an importer checklist. It is not
connected to collection, hosting or seis.jobs yet. Run its examples only against
the synthetic fixtures until source rights and the production handoff are reviewed.

Original software is licensed under [MIT](LICENSE). Third-party employer and
O*NET data retain their own terms; see [DATA-PROVENANCE.md](DATA-PROVENANCE.md) for
attribution, pinned versions, checksums, coverage and modification requirements.
No claim of having the latest source data is made.

## Decisions waiting for Professor Bear

1. The repository is **public** (it was created private on 2026-10-24). The original software now has an MIT licence; third-party data rights remain separate, and `data/jobs/2026-10-24/entry-level.csv` (a list of 1,891 individual postings, committed from the first Mac run) is in the public tree although the box publishes only counts and summaries. Decide whether to keep that file; it has not been removed or relicensed.
2. Which adapter next: Workday (most banks, hospitals, consultancies), or USAJOBS (federal, has a documented free API)?
3. Review source/field rights and the static-feed importer checklist before connecting real postings to seis.jobs; only counts and summaries leave the box today.

# What a Public Job-Board Collector Can and Cannot See of the Market for Software Engineering and Information Systems Graduates

*Draft 0.1, 2026-10-24. Written by CRITIQ in silent mode from the ai-jobs repository's own outputs. Working title and authorship are [NEEDS HUMAN REVIEW]. Every number below is from `data/` in this repository unless marked otherwise.*

## Status box (read this first)

**What this is.** A data-and-measurement paper about the ai-jobs collector: how it finds which employers publish a readable job board, reads every posting into one canonical shape, and sorts titles into families tied to SEIS courses. It reports what the first single-day collection (2026-10-24) shows and, with equal weight, what it cannot show.

**Why it matters.** A program that wants to say "these are the jobs our graduates are hired into" needs a denominator. This measures how much of the market a public-API collector can see (about 28% of listed companies), how biased that slice is (toward technology employers), and how reliable the title-based labels are (untested against human labels).

**Headline numbers.** 2,574 companies listed; 719 (27.9%) have a confirmed readable board on one of five ATS systems; 715 distinct boards read successfully; 84,282 open postings; 41% of the 59,449 postings outside one outlier employer have a title in a SEIS title family; 1,891 postings are marked entry-level or internship by title, 1,079 of them in the United States.

**Biggest open problem.** The title list was extended once using unmatched titles from the same collection it is then scored on, so the 41% is partly in-sample. It needs a hand-labelled holdout before it is quoted (see section 6, finding 1).

## Abstract

We describe a collector for public applicant-tracking-system (ATS) job boards and evaluate what it covers. From a list of 2,574 employers compiled by hand and 1,609 job titles in 27 families tied to 22 SEIS AI courses, the collector probed five ATS providers and confirmed a readable board for 719 employers (27.9%); coverage ranged from 49% of AI companies to 8% of consulting firms and 9% of finance firms, because the probed systems are used mostly by technology employers. One day's collection returned 84,282 open postings from 715 boards. A rule-based classifier assigned 41% of postings (excluding one outlier employer that contributed 24,833 store-level postings) to a SEIS title family, and 1,891 postings carry an entry-level or internship marker in the title; most postings (about 62% of all) carry no level word, so title-based entry-level counts are a floor, not an estimate. We report the verification rule that stopped slug collisions from being counted as boards, a rate-limit incident that would have been misread as "no board", and the checks that remain to be done: human-labelled precision and recall for the title families, a second collection day for churn, and adapters for the systems that large regulated employers use.

## 1. Introduction

**Territory.** Programs that prepare students for software and data careers describe their outcomes with anecdotes, alumni stories and occasional surveys. Public job boards publish the demand side directly, in structured form, and several ATS vendors expose it through unauthenticated JSON endpoints intended for embedding on career pages.

**Niche.** Three things are unknown for a program like SEIS. (1) What share of its employers' postings can be read without scraping aggregators whose terms forbid it. (2) Whether a title taxonomy built from course content labels postings usefully. (3) How much the answer to (1) and (2) depends on sector.

**Contribution.** (1) A canonical posting schema with six provider adapters and explicit rules for unstated fields. (2) A measured coverage of a hand-compiled employer list. (3) A first, openly-flawed, title-based classification with its validity threats stated. (4) Operating rules for an unattended collector, including self-halt and "a failed board never closes a posting".

**Research questions.**
- **RQ1.** What fraction of listed employers publish a board readable through the probed ATS APIs, and how does this vary by sector?
- **RQ2.** What fraction of postings have a title in a SEIS title family, and what fraction of those carry an entry-level marker?
- **RQ3.** How accurate are the title-family and seniority rules against human labels?
- **RQ4.** How stable is the posting set from one day to the next (new, changed, gone)?

RQ3 and RQ4 are not answered in this draft.

## 2. Related work

[NEEDS HUMAN REVIEW: no literature search has been done for this draft. Candidates to locate and read, named from memory and not yet verified: research that uses job-posting data to measure skill demand and AI-related labour demand; work on coverage bias of online vacancy data relative to official vacancy statistics; ESCO and O\*NET documentation for occupation and skill classification.] Project-internal precedent: the Lectern job-search tool (a different purpose: teaching and education-product roles) found that keyword filters over job titles are vulnerable to false friends, such as "training" at an AI lab meaning model training; its audit found 25 of 27 postings with a teaching word in the title were of that kind (`lectern/config/title_families.json`, note on the ML_TRAINING family).

## 3. Data and methods

### 3.1 Employer and title lists
**Employers.** 2,574 names across 13 sectors, written from general knowledge on 2026-10-24 (AI 400, software 605, health 259, finance 227, data 174, consulting 159, media 149, retail 139, regional 109, energy 107, nonprofit 92, travel 81, hardware 73). The list is a convenience sample: it contains names that may be defunct or renamed (not checked) and cannot be treated as a census of SEIS employers.
**Titles.** 1,609 titles in 27 families, each linked to one or more of the 22 courses listed on seisai.site/courses. The mapping from family to course is editorial and unvalidated. After the first collection, titles seen on real boards but unmatched (for example "Fullstack Engineer", "Deployed Engineer", "Solution Engineer") were added to existing families.

### 3.2 Finding boards (the probe)
For each employer the probe tries up to four slug guesses against Greenhouse, Ashby, Lever, SmartRecruiters, Workable and Recruitee, in that order, and stops at the first confirmed hit. **A hit is confirmed only if the board names the company (Greenhouse, SmartRecruiters, Workable, Recruitee return a company name) or the ad text mentions it (Lever, Ashby return none).** A bare slug match is not evidence: for example xAI's Greenhouse board belongs to "SpaceXSI" and was held out. Boards with postings that could not be confirmed (37 employers) are listed for a person to review and are not collected.

### 3.3 Reading boards
Each confirmed board is read in full and normalised to the canonical schema (`schema/job.schema.json`). Rules: a field the board did not state is `null`; the board's facts and our inferences are stored separately; ad text is stored only as a SHA-256 hash; a board that fails to load never closes its postings (they are carried forward as open), and a posting is `gone` only when its board was read successfully and no longer lists it. Greenhouse's `first_published` is used as the posting date; `updated_at` is not.

### 3.4 Inference rules (both deliberately crude)
*Seniority* (`seniority-v1`): ordered regular expressions on the title only (intern, exec, director, entry, staff, senior, manager, mid); returns `null` when the title has no level word. *Title family* (`title-ngram-v1`): the longest title from the 1,609 found as a word sequence inside the posting title; the first family to claim a title keeps it.

### 3.5 Operation
The collector ran once on a Mac and then on the Hetzner server (unprivileged user, daily timer) and returned identical counts (84,282 postings, 715 boards) in 1 min 56 s with a 642 MB peak. The summaries, not the postings, are committed.

## 4. Results (single day, 2026-10-24)

### 4.1 Coverage of employers (RQ1)

| Sector | Employers | Confirmed board | Share |
|---|---:|---:|---:|
| software | 605 | 244 | 40% |
| ai | 400 | 196 | 49% |
| health | 259 | 40 | 15% |
| finance | 227 | 22 | 9% |
| data | 174 | 69 | 39% |
| consulting | 159 | 14 | 8% |
| media | 149 | 26 | 17% |
| retail | 139 | 31 | 22% |
| regional | 109 | 25 | 22% |
| energy | 107 | 14 | 13% |
| nonprofit | 92 | 11 | 11% |
| travel | 81 | 19 | 23% |
| hardware | 73 | 8 | 10% |
| **all** | **2,574** | **719** | **27.9%** |

Shares in the table are rounded down, as in `data/companies/ats-coverage.md`.

By ATS (employers; postings on the probe day): Greenhouse 391; 36,632. Ashby 191; 10,082. SmartRecruiters 74; 33,523. Lever 53; 4,874. Recruitee 10; 157. Workable 0: **Workable was not read.** An unthrottled first probe was rate-limited (HTTP 429, Retry-After about 23 h) and the failure had initially been recorded as "no board". Error handling now records such answers as errors. A 100-employer re-check of the four other providers on employers recorded as having no board found 0 new boards and 0 errors.

### 4.2 Postings and labels (RQ2)
84,282 open postings from 715 distinct boards (four of the 719 confirmed employer rows share a board with another row, for example Veeva and Veeva Systems). One employer, Domino's (SmartRecruiters), contributed 24,833 store-level postings; counts below exclude it (59,449 postings). **24,621 (41%) have a title in a SEIS family other than the leadership family.** The largest families: software-engineering 8,050; product-management 3,139; solutions-customer 2,373; cloud-devops-sre 1,963; early-career programme titles 1,145; ai-engineering 970; security 900; design-ux 794; analytics 743; evals-quality 716.

Seniority from titles (all 84,282): no level word 52,073 (about 62%); senior 15,721; staff 5,247; exec 3,760; director 3,271; **entry 1,584; intern 1,168**; mid 834; manager 624. Among SEIS-family postings outside the outlier, **1,891 are entry or intern, 1,079 in the US** (location read from US-state or "United States" text; not geocoded). Workplace type is stated for only a minority (outside the outlier: hybrid 6,822; onsite 5,600; remote 4,970; not stated 42,057).

### 4.3 Not yet measured
Precision and recall of the title and seniority rules (RQ3); day-to-day change (RQ4: the second run produced 0 new and 0 gone ten minutes after the first, which is a smoke test, not a churn estimate).

## 5. Discussion

The collector sees a large, readable slice of technology employers and very little of the regulated sectors that employ many graduates, so "41% of postings fit SEIS titles" describes the *visible* market. The sector gradient in 4.1 (49% of AI employers, 8% of consulting, 9% of finance) is the main finding about the instrument, not about the market. The entry-level count is a floor because most postings are unlabelled.

## 6. Threats to validity and CRITIQ self-review (silent mode)

1. **[CRITICAL] In-sample classification.** The title list was extended using unmatched titles from the same collection it is scored on. The 41% therefore overstates out-of-sample fit. *Fix (days, not months):* hand-label a random sample of postings (a few hundred, stratified by sector) before the next title edit, freeze the list, then report precision and recall on a collection day the list never saw.
2. **[CRITICAL] Convenience sample of employers.** 2,574 names from memory, tilted to technology. Do not report shares of "the market"; report shares of "listed employers with a readable board".
3. **[MAJOR] Title-only seniority** undercounts entry-level work and cannot see experience or degree requirements, visa sponsorship, or compensation. Reading ad text is a separate decision (copying companies' ads).
4. **[MAJOR] Ghost and duplicate postings.** One posting may appear on several boards or be a standing requisition; nothing here deduplicates across employers or estimates fill rate.
5. **[MAJOR] Single day.** Churn, seasonality and posting duration are unknown.
6. **[MINOR] Provider fields differ** (only some give department, workplace, employment type); comparisons across providers are biased by that.
7. **[MINOR] Rate-limit incident** documents a way the pipeline could have misreported coverage; keep it in Methods.

**What works.** Explicit "unknown" states; slug-collision verification; a failed board never closes a posting; identical results on two machines; summaries committed, postings not.

## 7. Ethics and data handling

Sources are public, unauthenticated, read-only endpoints designed for embedding. Aggregators whose terms forbid scraping (Indeed, LinkedIn, Glassdoor, ZipRecruiter) are not used. Requests are throttled per host and a long Retry-After is honoured. The collector stores titles, locations, links and ad hashes, not ad text, and commits only counts and summaries. [NEEDS HUMAN REVIEW: confirm the position on bulk copying of public ads before any dataset release.]

## Reproducibility

Everything is in the repository: `python3 -m aijobs.probe`, `aijobs.collect`, `aijobs.seisfit`; 11 tests; Python standard library only. Dated outputs: `data/probes/probe-2026-10-24.jsonl`, `data/jobs/2026-10-24/{summary,boards}.json`, `seis-fit.md`.

## Sources

ai-jobs `README.md`, `docs/canonical-form.md`, `docs/collector-plan.md`, `data/companies/ats-coverage.md`, `data/jobs/2026-10-24/`; Lectern `config/title_families.json`.

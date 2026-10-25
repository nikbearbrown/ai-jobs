# Canonical form: one posting, whichever board it came from

## Executive summary

**What this is.** The rules for turning six different job-board APIs into one record shape ([schema/job.schema.json](../schema/job.schema.json)).
**Why.** Greenhouse calls the title `title`, Lever calls it `text`, SmartRecruiters calls it `name`; Greenhouse has no employment type, Lever has no posted date except a millisecond `createdAt`. A search across companies is only possible if all of that is one shape first.
**What it found.** Every provider's public API was called live on 2026-10-24 (Anthropic/Greenhouse, Palantir/Lever, OpenAI/Ashby, Canva/SmartRecruiters, Hugging Face/Workable, bunq/Recruitee) and each normalises to a record that validates against the schema. Boards state much less than the schema allows: most fields are `null` for most providers, and that is recorded as `null`, never guessed.

## Rules

1. **Unstated is `null`.** `workplace` is set only where the board has a field for it (Lever `workplaceType`; Ashby `workplaceType`/`isRemote`; SmartRecruiters `location.remote/hybrid`; Workable `telecommuting`; Recruitee `remote/hybrid/on_site`; Greenhouse only when a `metadata` entry is named like "Location Type"). It is never inferred from the location text.
2. **Board facts and our conclusions are kept apart.** Everything under `inferred` (`seniority`, `title_family`) names the rule that made it (`seniority-v1`, `title-ngram-v1`). Change the rule, bump the name, never edit old records.
3. **`posted_at` is a publication date.** Greenhouse's `first_published` is `posted_at`; its `updated_at` is stored separately and is not a posting date.
4. **The ad text is hashed, not stored.** It is a copy of the company's ad. `description_sha256` lets us notice that an ad changed. The text, if ever needed, goes in `data/raw/`, which is gitignored.
5. **A board that fails to load never closes a posting** (Lectern's rule, learned the hard way). `status` goes `open` -> `gone` only when the board was read successfully and the id is no longer listed.
6. **A slug match is not a company match.** `target`, `block`, `arm`, `box` are somebody else's boards. A board counts as the company's only when it says so (a company name in the API) or its ads mention the company; otherwise it stays `unverified` and is not collected unless asked.

## Field map

| Canonical | Greenhouse | Lever | Ashby | SmartRecruiters | Workable | Recruitee |
|---|---|---|---|---|---|---|
| `source_id` | `id` | `id` | `id` | `id` | `shortcode` | `id` |
| `title` | `title` | `text` | `title` | `name` | `title` | `title` |
| `url` | `absolute_url` | `hostedUrl` | `jobUrl` | built from `id` | `url` | `careers_url` |
| `apply_url` | n/a | `applyUrl` | `applyUrl` | n/a | `application_url` | `careers_apply_url` |
| `locations` | `location.name` split on `\|` `;` | `categories.allLocations` | `location` + `secondaryLocations` | `location.fullLocation` | `locations[]` (non-hidden) | `location` |
| `country_codes` | n/a | `country` | n/a | `location.country` | `locations[].countryCode` | `country_code` |
| `workplace` | `metadata` "Location Type" only | `workplaceType` | `workplaceType`, else `isRemote` | `location.remote/hybrid` | `telecommuting` | `remote/hybrid/on_site` |
| `department` | `departments[0]` (needs `?content=true`) | `categories.department` | `department` | `department.label` | `department` | `department` |
| `team` | n/a | `categories.team` | `team` | n/a | n/a | n/a |
| `employment_type` | n/a | `categories.commitment` | `employmentType` | `typeOfEmployment.label` | `employment_type` | `employment_type_code` |
| `posted_at` | `first_published` | `createdAt` (ms) | `publishedAt` | `releasedDate` | `published_on` | `published_at` |
| `compensation` | n/a | `salaryRange` | `compensation.summaryComponents` | n/a | n/a | n/a |

## Not covered yet

* **Workday, iCIMS, Taleo, Oracle Recruiting, SuccessFactors, ADP, UKG, Jobvite, BambooHR, Paycom, Teamtailor, Personio, Breezy** and every company's own careers site. Large employers (banks, consultancies, hospitals, government, most of Fortune 500) mostly use these. They are the main reason the probe finds few boards in regulated sectors. Each needs its own adapter; Workday needs the tenant, pod and site name found from the careers page first. Lectern already has hand-built collectors for Google, Amazon, Microsoft and Meta (`lectern/collect/collectors/`).
* **Aggregators** (Indeed, LinkedIn, Glassdoor, ZipRecruiter) forbid scraping in their terms and are deliberately not used.
* **USAJOBS** (federal) has a documented public API with a free key. Not wired.

## Optional USAJOBS mapping

See [the adapter contract](usajobs-adapter.md) for the implemented field mapping,
public-search scope, required optional credentials and completeness rules. It is
synthetically tested only. Unlike a full employer board, absence from search does
not establish closure. The existing six-provider collection path is unchanged.

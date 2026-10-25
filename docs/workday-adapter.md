# Workday: optional public-career adapter, disabled pending source review

This is a synthetic-tested implementation of a conservative CXS payload contract.
**No employer API response was fetched or live-verified. No employer is enabled.**
It builds on the tested `feat/usajobs-adapter` branch and leaves the default probe,
collector, schedules, feed-v1 contract and deployment unchanged.

## Source evidence and the live blocker (2026-10-25)

The official [Workday careers page](https://www.workday.com/en-us/company/careers/overview.html)
links to [its public board](https://workday.wd5.myworkdayjobs.com/Workday/?source=Careers_Website).
That verifies this particular employer-to-board link, not a general tenant guessing
rule or permission to collect. No search of guessed tenants was performed.

[Workday site terms](https://www.workday.com/en-us/legal/site-terms.html), dated
2026-08-13, restrict automated extraction and applications interacting with its
covered sites without consent. Site-specific and supplemental terms need review.
The board robots URL could not be retrieved by the research tool; that is unknown,
not an allow decision. No CXS endpoint was requested, and no other host, account,
proxy or browser technique was used to evade the restriction.

There is no verified public CXS API specification in this task. The route/field
contract below remains an implementation hypothesis tested with invented data;
it is not represented as an official supported Workday API. Before using it on a
real employer, obtain a permitted source and record the exact endpoints and payload
shape actually served to its public careers UI. Do not probe for those endpoints.
A source that prohibits collection stays disabled; a public link alone is insufficient.

## Explicit configuration and review gate

`Config` requires exact `tenant`, `host`, `site`, `board_url`, `company`, and
`company_id`; there are no slug guesses, keyword searches or company-name fuzzy
matches. Only `<tenant>.wd<number>.myworkdayjobs.com` over HTTPS is supported.
The tenant must equal the host's first label. The public board path must be
`/<site>` or `/en-US/<site>`. Other locale, custom-domain and myworkdaysite variants
are unsupported until separately verified and tested.

`Review` records:

- Original employer careers page URL that links to the exact board.
- Observed board URL and observed jobs endpoint, which must match configuration.
- Applicable terms URL and that exact origin's robots URL.
- SHA-256 of retained review evidence, review date, and permission basis.
- Explicit `access_allowed=True` only after the source's restrictions permit it.

The default review is absent. A denied, missing, mismatched, future-dated or >30-day
old review fails before any request. These fields record an operator's evidence;
the code does not independently authenticate it, interpret terms or grant rights.
No production review/config is shipped. The synthetic test review is explicitly
fictional and its transport is mocked; never reuse it as an access decision.

`fetch(config, observed_at=<UTC ISO timestamp>)` is an explicit library call, not
an automatic probe. A transport can be injected for offline testing. No credentials,
cookies, login, CAPTCHA handling or alternate-host fallback are implemented.

## Supported protocol and defensive behavior

The proposed jobs endpoint is
`https://<host>/wday/cxs/<tenant>/<site>/jobs`, and it must exactly match the reviewed
observed endpoint. Listing requests POST `{appliedFacets: {}, searchText: "",
limit: <1..20>, offset: <accumulated count>}`. This POST only reads the public listing;
it does not submit an application. No filtered search is treated as the full board.

Each response must contain integer `total` and a `jobPostings` array. Totals must
remain stable, paths must be unique, and all pages must reconcile to the total.
Defaults cap a run at 100 pages/2,000 jobs; hitting a limit is an incomplete failure,
not a successful truncated board. No query partitioning works around those limits.

Each listing's `/job/...` externalPath is checked for unsafe URL components,
encoded traversal and controls before forming the same-origin detail URL beneath
`/wday/cxs/<tenant>/<site>`. Each detail must contain `jobPostingInfo` with a
`jobReqId` matching the path's final underscore suffix and an exact entry in the
listing's `bulletFields`. Listing/detail titles must match. If externalUrl is
provided, it must exactly match the configured public board plus that path. A
missing/mismatched identity, 404 detail, changing title, duplicate requisition,
malformed field or any failed page/detail rejects the **whole** result. Do not
silently skip a bad record and then close it from the prior state.

Canonical `provider` is `workday`, `board` is `<host>/<site>`, and `source_id` is
jobReqId, preserving identity across title/location URL changes. `company` and
`company_id` come from the explicitly verified config; a tenant slug itself is not
evidence of employer identity.

## Field mapping and unknowns

| Canonical field | Source/behavior |
|---|---|
| `title` | Detail title, checked against listing |
| `url` | Exact configured public board URL plus checked job path |
| `apply_url` | null; no invented application URL |
| `locations` | Detail location plus additionalLocations strings, deduplicated; never listing text such as “5 Locations” |
| `country_codes` | Exact supported country descriptor names (US/GB/CA); opaque country IDs are not ISO codes; other names stay unknown |
| `workplace` | Explicit recognized remoteType only, never location/title wording |
| `employment_type` | Explicit Full time/Part time variants only |
| `posted_at` | null: relative postedOn and unverified startDate meanings are not converted into publication dates |
| `department`, `team`, `compensation`, `updated_at` | null; no guess from job family, ad prose or relative dates |
| `description_sha256` | Hash of returned jobDescription; no ad body persisted or returned in canonical records |
| `inferred`, `provenance` | Existing inference rule versions; observation timestamp and exact safe detail endpoint |

These strict mappings intentionally reject or leave unknown unverified variants.
Additional locations may span countries; the country list includes only explicit
recognized descriptors, not a geocoded inventory. No language model extracts fields.

## Completeness, health and integration

Only successful unfiltered pagination **and all details** yields `complete=True`
and `closure_safe=True`. The pure `source_api.merge` helper may then mark missing
prior IDs from this exact board gone. An error returns zero new records and keeps
all previous state unchanged. Consumers must retain health/error/retry metadata
and mark carried state stale/unknown. An empty successful board is valid; production
promotion also needs an agreed anomalous-drop check. The upstream endpoint is not
a transactional snapshot, so stable counts cannot rule out every simultaneous edit.

Transport is the optional-source bounded, same-origin transport introduced for
USAJOBS: no redirects/retries, sequential request spacing, 8 MiB maximum response,
identity JSON only. 403/404/429 are failures, not an empty board. Retry-After seconds
or HTTP-date are honored without truncation; keep retry_at across restarts before
scheduling another call. No scheduler or collection job is installed here.

The canonical provider enum includes Workday. Frozen static feed v1 still rejects
both new providers. [Opt-in feed v2](static-feed-v2.md) supports already captured
results through local acceptance without changing v1 or activating collection.
No actual job data was committed. No source is automatically approved for public
redistribution by the MIT software license or this adapter.

Run `python3 -m unittest discover -s tests` for synthetic tests. Live verification
remains blocked on a permitted employer source, current terms/robots evidence and
verified CXS payloads/endpoints. Once available, use a bounded live check and retain
only allowed aggregate evidence in Git. Adapter availability does not establish
coverage of Workday employers, federal hiring or the labor market.

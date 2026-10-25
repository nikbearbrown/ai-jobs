# USAJOBS: optional search adapter

Implemented with synthetic offline tests; **not live-verified or enabled**. This
branch builds on `feat/static-feed-v1`. Existing unauthenticated adapters, probe
order, collector, scheduled tasks and deployment are unchanged.

## Official references checked 2026-10-25

- [Authentication](https://developer.usajobs.gov/guides/authentication): job searches
  require a registered API key, its registered email as User-Agent, and the fixed
  `data.usajobs.gov` Host header. Code-list access is a different, unauthenticated API.
- [Search API](https://developer.usajobs.gov/api-reference/get-api-search): response
  identities, organization, locations, schedules, publication date and remuneration.
- [Limits](https://developer.usajobs.gov/guides/rate-limiting): at most 500 rows/page
  and 10,000 rows/query. The adapter rejects totals at or above 10,000 because a
  saturated result cannot establish completeness. It does not partition queries
  to get around a limit.
- [Terms](https://developer.usajobs.gov/guides/terms-of-service): API access and
  public-data reuse are distinct; restrictions identified on particular content
  still apply. Attribute the source, retrieval date and official link, and make
  non-affiliation clear. No API account or terms acceptance was performed here.

## Explicit API/config contract

`aijobs.usajobs.Config(filters={}, page_size=500, max_pages=20)` accepts only
`Keyword`, `PositionTitle`, `JobCategoryCode`, `Organization`, `LocationName`,
`HiringPath`, and `RemoteIndicator` (strings). It forces `WhoMayApply=Public` and
`Fields=Min`. No rolling DatePosted filter, restricted Status/All access, URL override
or credential fields are accepted. The normalized query hashes to a stable board
scope; changing filters creates a different scope, not an employer rename.

Call `fetch(config, credentials, observed_at=<UTC ISO timestamp>)` explicitly.
`Credentials(email, api_key)` is an in-memory value with a redacted repr.
`credentials_from_environment()` reads `AIJOBS_USAJOBS_EMAIL` and
`AIJOBS_USAJOBS_API_KEY` only when explicitly called. It writes nothing, searches
no credential files and is never called by the existing collector. Do not put
credentials into JSON configs, source code, arguments, chat, logs or Git. No
persistent credential setup is included or authorized by this implementation.

Missing credentials return `complete=False`, `error=credentials_required`, no
records, and make no request. `Result` also provides provider, board, source URL,
retry timestamp and `closure_safe`. There is no CLI that silently reads secrets
or starts collection. The injected transport interface supports offline consumers
and tests; production defaults to the fixed HTTPS origin.

## Mapping and completeness

Control number `MatchedObjectId` is the stable source ID; announcement `PositionID`
is not used as identity. `company` comes from the response's agency name and
`company_id` stays null (no guessed company-list match). The official posting URL
must agree with the control number. Location strings are preserved. Explicit
alpha-2 codes and the exact source name United States map to country codes; other
country names remain unconverted. Only unambiguous schedule codes 1/2 map to
full/part-time. Permanent appointment does not mean full-time. PublicationStartDate
is posted_at; application deadlines are not posting dates. Currency, workplace,
team and updated_at remain unknown unless a future reviewed mapping establishes
them. Min response snippets are not hashed as though they were complete ad text.
Inference and provenance use the existing canonical structure/rule versions.

All pages must reconcile to one stable total, with unique control numbers and
valid canonical records. Short pages before the total, changed totals, duplicate
IDs, malformed payloads, page limits and HTTP failures discard the entire result.
Results are a public search slice, not all federal vacancies or employer coverage.
Offset/page search cannot guarantee a transactional upstream snapshot even when
counts reconcile.

A job disappearing from a search is not proof that it closed. USAJOBS results
therefore always have `closure_safe=False`. The pure `source_api.merge` helper
preserves missing prior rows as last-known state, even after a complete empty
search; failed reads preserve everything. A consumer must store source health and
observed IDs to display retained rows as stale/unknown. This is deliberately not
wired into `collect.merge_state`, which would otherwise close missing records.

Transport rejects redirects (so headers never follow another host), non-JSON,
compressed or >8 MiB responses, duplicate JSON keys and nonfinite values. Calls
are sequential with at least one second spacing; a run stops on the first error.
429/Retry-After accepts seconds or HTTP-date and blocks that origin across Transport instances in the process;
there are no automatic retries, alternate hosts or rate-limit workarounds. Retain
`retry_at` in the future scheduler across process restarts before any new attempt.
An unspecified/malformed 429 delay defaults to an hour. No scheduler is configured.

## Compatibility and next steps

Canonical provider vocabulary adds `usajobs`. The **frozen static feed v1 enum is
unchanged and rejects these rows**; a reviewed feed version is needed before site
integration. No real records or ad bodies are committed or published.

Tests: `python3 -m unittest discover -s tests` (offline).

Live verification is blocked by absence of separately approved API registration
and credential provisioning. No existing secrets were searched for or used.
After approval, securely provision credentials outside chat/Git, review the chosen
query, perform a bounded test, record counts/coverage only, and retain retry state.
This adapter's availability is not evidence of measured USAJOBS coverage.
